"""Pure execution-rule helpers for bar-based simulation."""

from __future__ import annotations

from market_data.contracts import Candle
from strategy_engine.contracts import SignalDirection

from .contracts import ExitReason, IntrabarExitPolicy, Position, PositionDirection, RiskExitConfig


def target_position_direction(signal_direction: SignalDirection) -> PositionDirection:
    if signal_direction == SignalDirection.BUY:
        return PositionDirection.LONG
    return PositionDirection.SHORT


def should_ignore_signal(
    *,
    position: Position | None,
    target_direction: PositionDirection,
) -> bool:
    return position is not None and position.direction == target_direction


def should_flip_position(
    *,
    position: Position | None,
    target_direction: PositionDirection,
    allow_flip: bool,
) -> bool:
    return (
        position is not None
        and position.direction != target_direction
        and allow_flip
    )


def protective_levels(
    *,
    entry_price: float,
    direction: PositionDirection,
    risk_exits: RiskExitConfig | None,
) -> tuple[float | None, float | None]:
    if risk_exits is None:
        return None, None

    stop_loss_price: float | None = None
    take_profit_price: float | None = None

    if risk_exits.stop_loss_fraction is not None and risk_exits.stop_loss_fraction > 0:
        if direction == PositionDirection.LONG:
            stop_loss_price = entry_price * (1.0 - risk_exits.stop_loss_fraction)
        else:
            stop_loss_price = entry_price * (1.0 + risk_exits.stop_loss_fraction)

    if risk_exits.take_profit_fraction is not None and risk_exits.take_profit_fraction > 0:
        if direction == PositionDirection.LONG:
            take_profit_price = entry_price * (1.0 + risk_exits.take_profit_fraction)
        else:
            take_profit_price = entry_price * (1.0 - risk_exits.take_profit_fraction)

    return stop_loss_price, take_profit_price


def resolve_intrabar_risk_exit(
    *,
    candle: Candle,
    position: Position,
    risk_exits: RiskExitConfig | None,
) -> tuple[ExitReason, float] | None:
    if risk_exits is None:
        return None
    if position.stop_loss_price is None and position.take_profit_price is None:
        return None

    if risk_exits.intrabar_exit_policy != IntrabarExitPolicy.ADVERSE_FIRST:
        raise ValueError(f"Unsupported intrabar policy: {risk_exits.intrabar_exit_policy}")

    if position.direction == PositionDirection.LONG:
        stop_hit = (
            position.stop_loss_price is not None and candle.low <= position.stop_loss_price
        )
        take_hit = (
            position.take_profit_price is not None and candle.high >= position.take_profit_price
        )
        if not stop_hit and not take_hit:
            return None
        if stop_hit and take_hit:
            # Conservative: adverse move first.
            return ExitReason.STOP_LOSS, _long_stop_price(candle.open, position.stop_loss_price)
        if stop_hit:
            return ExitReason.STOP_LOSS, _long_stop_price(candle.open, position.stop_loss_price)
        return ExitReason.TAKE_PROFIT, _long_take_price(candle.open, position.take_profit_price)

    stop_hit = (
        position.stop_loss_price is not None and candle.high >= position.stop_loss_price
    )
    take_hit = (
        position.take_profit_price is not None and candle.low <= position.take_profit_price
    )
    if not stop_hit and not take_hit:
        return None
    if stop_hit and take_hit:
        return ExitReason.STOP_LOSS, _short_stop_price(candle.open, position.stop_loss_price)
    if stop_hit:
        return ExitReason.STOP_LOSS, _short_stop_price(candle.open, position.stop_loss_price)
    return ExitReason.TAKE_PROFIT, _short_take_price(candle.open, position.take_profit_price)


def _long_stop_price(bar_open: float, stop_price: float | None) -> float:
    if stop_price is None:
        raise ValueError("stop_price is required")
    # Gap through stop: fill at open.
    return bar_open if bar_open <= stop_price else stop_price


def _long_take_price(bar_open: float, take_price: float | None) -> float:
    if take_price is None:
        raise ValueError("take_price is required")
    # Gap through target: fill at open.
    return bar_open if bar_open >= take_price else take_price


def _short_stop_price(bar_open: float, stop_price: float | None) -> float:
    if stop_price is None:
        raise ValueError("stop_price is required")
    return bar_open if bar_open >= stop_price else stop_price


def _short_take_price(bar_open: float, take_price: float | None) -> float:
    if take_price is None:
        raise ValueError("take_price is required")
    return bar_open if bar_open <= take_price else take_price
