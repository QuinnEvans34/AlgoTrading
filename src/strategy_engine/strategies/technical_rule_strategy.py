"""Initial rule-based technical strategy extracted from donor concepts."""

from __future__ import annotations

from dataclasses import asdict
import statistics
from typing import Any

from market_data.contracts import Candle

from ..contracts import (
    SignalDirection,
    StrategyEvaluation,
    StrategyInput,
    StrategySignal,
)
from ..indicators import IndicatorCalculator
from ..parameters import TechnicalRuleParameterSet, TechnicalRuleThresholds
from .base import Strategy


class TechnicalRuleStrategy(Strategy):
    def __init__(
        self,
        parameter_set: TechnicalRuleParameterSet | None = None,
        *,
        strategy_name: str = "technical_rule_v1",
    ) -> None:
        self._name = strategy_name
        self._parameter_set = parameter_set or TechnicalRuleParameterSet.multi_asset_defaults()
        self._indicators = IndicatorCalculator()

    @property
    def name(self) -> str:
        return self._name

    def evaluate(self, strategy_input: StrategyInput) -> StrategyEvaluation:
        candles = sorted(strategy_input.candles, key=lambda c: c.timestamp)
        thresholds = self._parameter_set.resolve(strategy_input.instrument)

        if len(candles) < thresholds.min_candles:
            return StrategyEvaluation(
                strategy_name=self.name,
                instrument=strategy_input.instrument,
                interval=strategy_input.interval,
                candle_count=len(candles),
                signal=None,
                diagnostics={"status": "insufficient_candles", "min_required": thresholds.min_candles},
            )

        closes = self._indicators.closes(candles)
        rsi_series = self._indicators.rsi(closes, period=thresholds.rsi_period)
        rsi_latest = self._indicators.latest(rsi_series)
        if rsi_latest is None:
            return self._no_signal(
                strategy_input,
                candles,
                {"status": "indicator_unavailable", "indicator": "rsi"},
            )

        rsi_window = self._indicators.tail_non_null(rsi_series, thresholds.rsi_z_window)
        rsi_z = self._zscore(rsi_latest, rsi_window)

        ema_series = self._indicators.ema(closes, thresholds.ema_period)
        ema_latest = ema_series[-1] if ema_series else None
        if ema_latest is None:
            return self._no_signal(
                strategy_input,
                candles,
                {"status": "indicator_unavailable", "indicator": "ema"},
            )
        current_price = closes[-1]
        trend = "bullish" if current_price > ema_latest else "bearish"

        bands = self._indicators.bollinger_bands(
            closes,
            period=thresholds.bollinger_period,
            std_dev=thresholds.bollinger_std_dev,
        )
        upper = self._indicators.latest(bands.upper)
        lower = self._indicators.latest(bands.lower)
        if upper is None or lower is None or upper == lower:
            bb_position = 0.5
        else:
            bb_position = (current_price - lower) / (upper - lower)

        volatility = self._indicators.annualized_volatility(closes)
        if volatility is None or not (thresholds.volatility_min <= volatility <= thresholds.volatility_max):
            return self._no_signal(
                strategy_input,
                candles,
                {
                    "status": "volatility_filter",
                    "volatility": volatility,
                    "volatility_min": thresholds.volatility_min,
                    "volatility_max": thresholds.volatility_max,
                },
            )

        macd = self._indicators.macd(
            closes,
            fast_period=thresholds.macd_fast,
            slow_period=thresholds.macd_slow,
            signal_period=thresholds.macd_signal,
        )
        macd_hist = macd.histogram[-1] if macd.histogram else 0.0
        hist_window = list(macd.histogram[-thresholds.rsi_z_window :])
        hist_std = statistics.stdev(hist_window) if len(hist_window) > 1 else 0.0
        macd_noise_threshold = max(
            thresholds.macd_min_hist_abs,
            hist_std * thresholds.macd_noise_factor,
        )
        if abs(macd_hist) < macd_noise_threshold:
            return self._no_signal(
                strategy_input,
                candles,
                {
                    "status": "macd_noise_filter",
                    "macd_hist": macd_hist,
                    "macd_noise_threshold": macd_noise_threshold,
                },
            )

        stochastic = self._indicators.stochastic(
            candles,
            k_period=thresholds.stoch_k_period,
            d_period=thresholds.stoch_d_period,
        )
        stoch_k = self._indicators.latest(stochastic.k_percent)
        if stoch_k is None:
            return self._no_signal(
                strategy_input,
                candles,
                {"status": "indicator_unavailable", "indicator": "stochastic"},
            )
        stoch_k = max(0.0, min(100.0, stoch_k))

        adx_series = self._indicators.adx(candles, period=thresholds.adx_period)
        adx_value = self._indicators.latest(adx_series) or 0.0
        if adx_value < thresholds.adx_floor:
            return self._no_signal(
                strategy_input,
                candles,
                {"status": "adx_filter", "adx": adx_value, "adx_floor": thresholds.adx_floor},
            )

        if thresholds.volume_filter_enabled and self._fails_volume_filter(
            candles, ratio_floor=thresholds.volume_ratio_floor
        ):
            return self._no_signal(
                strategy_input,
                candles,
                {"status": "volume_filter", "volume_ratio_floor": thresholds.volume_ratio_floor},
            )

        fvg_hits = self._detect_recent_fvg(
            candles,
            lookback=thresholds.fvg_lookback_bars,
            min_gap_fraction=thresholds.fvg_min_gap_fraction,
        )
        has_recent_bullish_fvg = any(kind == "bullish" for kind in fvg_hits)
        has_recent_bearish_fvg = any(kind == "bearish" for kind in fvg_hits)

        indicators = {
            "price_close": current_price,
            "ema": ema_latest,
            "rsi": rsi_latest,
            "rsi_z": rsi_z,
            "macd_hist": macd_hist,
            "macd_noise_threshold": macd_noise_threshold,
            "stoch_k": stoch_k,
            "bb_position": bb_position,
            "adx": adx_value,
            "volatility_annualized": volatility,
        }

        buy_condition = (
            (rsi_z < -thresholds.rsi_z_threshold)
            and (macd_hist > macd_noise_threshold)
            and ((stoch_k < thresholds.stoch_lower) or has_recent_bullish_fvg)
            and (bb_position < thresholds.bollinger_midpoint or trend == "bullish")
        )
        sell_condition = (
            (rsi_z > thresholds.rsi_z_threshold)
            and (macd_hist < -macd_noise_threshold)
            and ((stoch_k > thresholds.stoch_upper) or has_recent_bearish_fvg)
            and (bb_position > thresholds.bollinger_midpoint or trend == "bearish")
        )

        if not buy_condition and not sell_condition:
            return StrategyEvaluation(
                strategy_name=self.name,
                instrument=strategy_input.instrument,
                interval=strategy_input.interval,
                candle_count=len(candles),
                signal=None,
                indicators=indicators,
                diagnostics={"status": "conditions_not_met", "trend": trend},
            )

        direction = SignalDirection.BUY if buy_condition else SignalDirection.SELL
        score, confidence = self._score_signal(
            direction=direction,
            rsi_z=rsi_z,
            macd_hist=macd_hist,
            macd_noise_threshold=max(macd_noise_threshold, 1e-12),
            stoch_k=stoch_k,
            adx=adx_value,
            thresholds=thresholds,
        )

        if confidence < thresholds.min_confidence:
            return StrategyEvaluation(
                strategy_name=self.name,
                instrument=strategy_input.instrument,
                interval=strategy_input.interval,
                candle_count=len(candles),
                signal=None,
                indicators=indicators,
                diagnostics={
                    "status": "confidence_below_threshold",
                    "confidence": confidence,
                    "min_confidence": thresholds.min_confidence,
                },
            )

        rationale = (
            f"rsi_z={rsi_z:.2f}",
            f"macd_hist={macd_hist:.6f}",
            f"stoch_k={stoch_k:.2f}",
            f"adx={adx_value:.2f}",
            f"trend={trend}",
        )
        signal = StrategySignal(
            strategy_name=self.name,
            instrument=strategy_input.instrument,
            interval=strategy_input.interval,
            timestamp=candles[-1].timestamp,
            direction=direction,
            confidence=confidence,
            score=score,
            rationale=rationale,
            indicators=indicators,
            metadata={
                "parameter_profile": asdict(thresholds),
                "fvg_hits_recent": tuple(fvg_hits),
            },
        )
        return StrategyEvaluation(
            strategy_name=self.name,
            instrument=strategy_input.instrument,
            interval=strategy_input.interval,
            candle_count=len(candles),
            signal=signal,
            indicators=indicators,
            diagnostics={"status": "signal_generated"},
        )

    def _no_signal(
        self,
        strategy_input: StrategyInput,
        candles: list[Candle],
        diagnostics: dict[str, Any],
    ) -> StrategyEvaluation:
        return StrategyEvaluation(
            strategy_name=self.name,
            instrument=strategy_input.instrument,
            interval=strategy_input.interval,
            candle_count=len(candles),
            signal=None,
            diagnostics=diagnostics,
        )

    @staticmethod
    def _zscore(value: float, series: list[float]) -> float:
        if not series:
            return 0.0
        if len(series) < 2:
            return 0.0
        mean = statistics.fmean(series)
        stdev = statistics.stdev(series)
        if stdev == 0:
            return 0.0
        return (value - mean) / stdev

    @staticmethod
    def _fails_volume_filter(candles: list[Candle], ratio_floor: float) -> bool:
        volumes = [c.volume for c in candles if c.volume is not None]
        if len(volumes) < 20:
            return False
        recent = volumes[-60:] if len(volumes) >= 60 else volumes
        avg = statistics.fmean(recent)
        med = statistics.median(volumes)
        if med <= 0:
            return False
        return avg < (ratio_floor * med)

    @staticmethod
    def _detect_recent_fvg(
        candles: list[Candle],
        *,
        lookback: int,
        min_gap_fraction: float,
    ) -> list[str]:
        detections: list[tuple[str, int]] = []
        for i in range(1, len(candles) - 1):
            prev_candle = candles[i - 1]
            next_candle = candles[i + 1]
            reference = max(abs(next_candle.close), 1e-12)

            if prev_candle.low > next_candle.high:
                gap = prev_candle.low - next_candle.high
                if (gap / reference) >= min_gap_fraction:
                    detections.append(("bearish", i))
            elif prev_candle.high < next_candle.low:
                gap = next_candle.low - prev_candle.high
                if (gap / reference) >= min_gap_fraction:
                    detections.append(("bullish", i))

        cutoff = len(candles) - lookback
        return [kind for kind, idx in detections if idx >= cutoff]

    @staticmethod
    def _score_signal(
        *,
        direction: SignalDirection,
        rsi_z: float,
        macd_hist: float,
        macd_noise_threshold: float,
        stoch_k: float,
        adx: float,
        thresholds: TechnicalRuleThresholds,
    ) -> tuple[float, float]:
        rsi_score = min(1.0, abs(rsi_z) / max(thresholds.rsi_z_threshold * 3.0, 1e-12))
        macd_score = min(1.0, abs(macd_hist) / max(macd_noise_threshold * 2.0, 1e-12))
        if direction == SignalDirection.BUY:
            stoch_score = min(1.0, max(0.0, (thresholds.stoch_lower - stoch_k) / max(thresholds.stoch_lower, 1e-12)))
        else:
            stoch_score = min(
                1.0,
                max(
                    0.0,
                    (stoch_k - thresholds.stoch_upper)
                    / max(100.0 - thresholds.stoch_upper, 1e-12),
                ),
            )
        adx_score = min(1.0, adx / 40.0)
        score = (0.5 * rsi_score) + (0.25 * macd_score) + (0.15 * stoch_score) + (0.1 * adx_score)
        confidence = min(
            thresholds.max_confidence,
            0.10 + (score * 0.80),
        )
        return score, confidence
