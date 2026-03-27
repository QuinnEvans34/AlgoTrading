"""Core single-asset research backtesting simulation engine."""

from __future__ import annotations

from dataclasses import replace
from typing import Mapping

from market_data.contracts import BarInterval
from strategy_engine.contracts import StrategyInput
from strategy_engine.strategies.base import Strategy

from .contracts import (
    BacktestConfig,
    BacktestInput,
    BacktestResult,
    EquityPoint,
    ExecutionTiming,
    ExitReason,
    Position,
    PositionDirection,
    SignalEvent,
    SizingMode,
    Trade,
)
from .costs import (
    CommissionModel,
    FillModel,
    FixedBpsCommissionModel,
    FixedBpsSlippageModel,
    FixedBpsSpreadModel,
)
from .execution import (
    protective_levels,
    resolve_intrabar_risk_exit,
    should_flip_position,
    should_ignore_signal,
    target_position_direction,
)
from .metrics import build_summary


class BacktestSimulator:
    def __init__(
        self,
        *,
        fill_model: FillModel | None = None,
        commission_model: CommissionModel | None = None,
        bars_per_year: Mapping[BarInterval, int] | None = None,
    ) -> None:
        self._fill_model = fill_model or FillModel(
            spread_model=FixedBpsSpreadModel(half_spread_bps=0.0),
            slippage_model=FixedBpsSlippageModel(bps=0.0),
        )
        self._commission_model = commission_model or FixedBpsCommissionModel(bps=0.0)
        self._bars_per_year = dict(
            bars_per_year
            or {
                BarInterval.M1: 252 * 390,
                BarInterval.M5: 252 * 78,
                BarInterval.M15: 252 * 26,
                BarInterval.M30: 252 * 13,
                BarInterval.H1: 252 * 6,
                BarInterval.H4: 252 * 2,
                BarInterval.D1: 252,
            }
        )

    def run(
        self,
        *,
        backtest_input: BacktestInput,
        strategy: Strategy,
        config: BacktestConfig | None = None,
    ) -> BacktestResult:
        cfg = config or BacktestConfig()
        self._validate_config(cfg)
        candles = tuple(sorted(backtest_input.candles, key=lambda c: c.timestamp))
        if len(candles) < max(3, cfg.warmup_bars + 1):
            raise ValueError("Not enough candles for configured warmup and simulation")

        cash = cfg.initial_capital
        position: Position | None = None
        trades: list[Trade] = []
        equity_curve: list[EquityPoint] = []
        signal_events: list[SignalEvent] = []
        peak_equity = cfg.initial_capital
        diagnostics: dict[str, float | int] = {
            "strategy_evaluations": 0,
            "ignored_low_confidence_signals": 0,
            "ignored_short_signals": 0,
            "timed_exits": 0,
            "stop_loss_exits": 0,
            "take_profit_exits": 0,
            "signal_flip_exits": 0,
            "end_of_data_exits": 0,
        }

        for i, candle in enumerate(candles):
            if position is not None:
                position = replace(position, bars_held=position.bars_held + 1)

            if position is not None and cfg.risk_exits is not None:
                risk_exit = resolve_intrabar_risk_exit(
                    candle=candle,
                    position=position,
                    risk_exits=cfg.risk_exits,
                )
                if risk_exit is not None:
                    risk_reason, risk_raw_price = risk_exit
                    trade, cash = self._close_position(
                        backtest_input=backtest_input,
                        position=position,
                        cash=cash,
                        raw_price=risk_raw_price,
                        exit_time=candle.timestamp,
                        exit_signal=None,
                        reason=risk_reason,
                    )
                    trades.append(trade)
                    position = None
                    if risk_reason == ExitReason.STOP_LOSS:
                        diagnostics["stop_loss_exits"] += 1
                    elif risk_reason == ExitReason.TAKE_PROFIT:
                        diagnostics["take_profit_exits"] += 1

            unrealized = self._unrealized_pnl(position, mark_price=candle.close)
            equity = cash + unrealized
            if equity > peak_equity:
                peak_equity = equity
            drawdown_pct = ((peak_equity - equity) / peak_equity * 100.0) if peak_equity > 0 else 0.0
            equity_curve.append(
                EquityPoint(
                    timestamp=candle.timestamp,
                    equity=equity,
                    cash=cash,
                    unrealized_pnl=unrealized,
                    drawdown_pct=drawdown_pct,
                )
            )

            if i < cfg.warmup_bars or i >= (len(candles) - 1):
                continue

            next_candle = candles[i + 1]
            if (
                position is not None
                and cfg.max_bars_in_position is not None
                and position.bars_held >= cfg.max_bars_in_position
            ):
                trade, cash = self._close_position(
                    backtest_input=backtest_input,
                    position=position,
                    cash=cash,
                    raw_price=next_candle.open,
                    exit_time=next_candle.timestamp,
                    exit_signal=None,
                    reason=ExitReason.MAX_BARS_TIMEOUT,
                )
                trades.append(trade)
                position = None
                diagnostics["timed_exits"] += 1

            diagnostics["strategy_evaluations"] += 1
            evaluation = strategy.evaluate(
                StrategyInput(
                    instrument=backtest_input.instrument,
                    interval=backtest_input.interval,
                    candles=candles[: i + 1],
                )
            )

            if evaluation.signal is None:
                continue

            if evaluation.signal.confidence < cfg.min_signal_confidence:
                diagnostics["ignored_low_confidence_signals"] += 1
                continue

            signal_event = SignalEvent(
                timestamp=evaluation.signal.timestamp,
                direction=evaluation.signal.direction,
                confidence=evaluation.signal.confidence,
                score=evaluation.signal.score,
                rationale=evaluation.signal.rationale,
                metadata=evaluation.signal.metadata,
            )
            signal_events.append(signal_event)

            target_direction = target_position_direction(signal_event.direction)
            if target_direction == PositionDirection.SHORT and not cfg.allow_short:
                diagnostics["ignored_short_signals"] += 1
                continue

            if position is None:
                position, cash = self._open_position(
                    backtest_input=backtest_input,
                    direction=target_direction,
                    signal_event=signal_event,
                    cash=cash,
                    equity=equity,
                    raw_price=next_candle.open,
                    entry_time=next_candle.timestamp,
                    config=cfg,
                )
                continue

            if should_ignore_signal(position=position, target_direction=target_direction):
                continue

            can_flip = should_flip_position(
                position=position,
                target_direction=target_direction,
                allow_flip=cfg.allow_flip,
            )
            trade, cash = self._close_position(
                backtest_input=backtest_input,
                position=position,
                cash=cash,
                raw_price=next_candle.open,
                exit_time=next_candle.timestamp,
                exit_signal=signal_event,
                reason=ExitReason.SIGNAL_FLIP,
            )
            trades.append(trade)
            diagnostics["signal_flip_exits"] += 1
            position = None

            if can_flip:
                position, cash = self._open_position(
                    backtest_input=backtest_input,
                    direction=target_direction,
                    signal_event=signal_event,
                    cash=cash,
                    equity=cash,
                    raw_price=next_candle.open,
                    entry_time=next_candle.timestamp,
                    config=cfg,
                )

        if position is not None and cfg.close_position_on_end:
            last = candles[-1]
            trade, cash = self._close_position(
                backtest_input=backtest_input,
                position=position,
                cash=cash,
                raw_price=last.close,
                exit_time=last.timestamp,
                exit_signal=None,
                reason=ExitReason.END_OF_DATA,
            )
            trades.append(trade)
            diagnostics["end_of_data_exits"] += 1
            position = None
            final_equity = cash
            if final_equity > peak_equity:
                peak_equity = final_equity
            drawdown_pct = ((peak_equity - final_equity) / peak_equity * 100.0) if peak_equity > 0 else 0.0
            equity_curve.append(
                EquityPoint(
                    timestamp=last.timestamp,
                    equity=final_equity,
                    cash=cash,
                    unrealized_pnl=0.0,
                    drawdown_pct=drawdown_pct,
                )
            )

        summary = build_summary(
            initial_capital=cfg.initial_capital,
            trades=trades,
            equity_curve=equity_curve,
            bars_per_year=self._bars_per_year.get(backtest_input.interval, 252),
        )
        return BacktestResult(
            config=cfg,
            instrument=backtest_input.instrument,
            interval=backtest_input.interval,
            trades=tuple(trades),
            equity_curve=tuple(equity_curve),
            summary=summary,
            signal_events=tuple(signal_events),
            diagnostics=diagnostics,
        )

    @staticmethod
    def _unrealized_pnl(position: Position | None, *, mark_price: float) -> float:
        if position is None:
            return 0.0
        if position.direction == PositionDirection.LONG:
            return position.units * (mark_price - position.entry_price)
        return position.units * (position.entry_price - mark_price)

    def _open_position(
        self,
        *,
        backtest_input: BacktestInput,
        direction: PositionDirection,
        signal_event: SignalEvent,
        cash: float,
        equity: float,
        raw_price: float,
        entry_time,
        config: BacktestConfig,
    ) -> tuple[Position, float]:
        entry_price = self._fill_model.entry_fill_price(
            instrument=backtest_input.instrument,
            timestamp=entry_time,
            raw_price=raw_price,
            direction=direction,
        )

        if config.sizing_mode != SizingMode.FIXED_EQUITY_FRACTION:
            raise ValueError(f"Unsupported sizing mode: {config.sizing_mode}")
        notional_target = max(0.0, equity * config.position_notional_fraction)
        units = (notional_target / entry_price) if entry_price > 0 else 0.0
        entry_notional = units * entry_price
        entry_commission = self._commission_model.commission(
            instrument=backtest_input.instrument,
            timestamp=entry_time,
            notional=entry_notional,
        )
        next_cash = cash - entry_commission
        stop_loss_price, take_profit_price = protective_levels(
            entry_price=entry_price,
            direction=direction,
            risk_exits=config.risk_exits,
        )
        position = Position(
            direction=direction,
            entry_time=entry_time,
            entry_price=entry_price,
            units=units,
            entry_equity=equity,
            entry_commission=entry_commission,
            entry_signal=signal_event,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price,
            bars_held=0,
        )
        return position, next_cash

    def _close_position(
        self,
        *,
        backtest_input: BacktestInput,
        position: Position,
        cash: float,
        raw_price: float,
        exit_time,
        exit_signal: SignalEvent | None,
        reason: ExitReason,
    ) -> tuple[Trade, float]:
        exit_price = self._fill_model.exit_fill_price(
            instrument=backtest_input.instrument,
            timestamp=exit_time,
            raw_price=raw_price,
            direction=position.direction,
        )
        exit_notional = position.units * exit_price
        exit_commission = self._commission_model.commission(
            instrument=backtest_input.instrument,
            timestamp=exit_time,
            notional=exit_notional,
        )

        if position.direction == PositionDirection.LONG:
            gross_pnl = position.units * (exit_price - position.entry_price)
        else:
            gross_pnl = position.units * (position.entry_price - exit_price)
        net_pnl = gross_pnl - position.entry_commission - exit_commission
        next_cash = cash + gross_pnl - exit_commission

        entry_equity = position.entry_equity if position.entry_equity != 0 else 1.0
        return_pct = (net_pnl / entry_equity) * 100.0
        trade = Trade(
            instrument=backtest_input.instrument,
            direction=position.direction,
            entry_time=position.entry_time,
            exit_time=exit_time,
            entry_price=position.entry_price,
            exit_price=exit_price,
            units=position.units,
            gross_pnl=gross_pnl,
            net_pnl=net_pnl,
            return_pct=return_pct,
            bars_held=position.bars_held,
            exit_reason=reason,
            entry_commission=position.entry_commission,
            exit_commission=exit_commission,
            entry_signal=position.entry_signal,
            exit_signal=exit_signal,
            metadata={},
        )
        return trade, next_cash

    @staticmethod
    def _validate_config(config: BacktestConfig) -> None:
        if config.entry_timing != ExecutionTiming.NEXT_BAR_OPEN:
            raise ValueError(f"Unsupported entry timing: {config.entry_timing}")
        if config.signal_exit_timing != ExecutionTiming.NEXT_BAR_OPEN:
            raise ValueError(f"Unsupported signal exit timing: {config.signal_exit_timing}")
        if not (0.0 <= config.position_notional_fraction <= 1.0):
            raise ValueError("position_notional_fraction must be in [0, 1]")
        if config.warmup_bars < 0:
            raise ValueError("warmup_bars must be >= 0")
        if config.initial_capital <= 0:
            raise ValueError("initial_capital must be > 0")
