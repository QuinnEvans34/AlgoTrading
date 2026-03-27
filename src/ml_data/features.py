"""Deterministic historical-only feature computations for ML datasets."""

from __future__ import annotations

from dataclasses import dataclass
import math
import statistics
from typing import Sequence

from market_data.contracts import Candle
from strategy_engine.indicators import IndicatorCalculator

from .contracts import FeatureSpec, MissingVolumePolicy


Number = float | None


@dataclass(frozen=True)
class FeatureComputationResult:
    feature_values: dict[str, list[Number]]
    max_lookback_bars: int
    skipped_features: tuple[str, ...]


def _ensure_positive_windows(values: Sequence[int], field_name: str) -> None:
    if any(v <= 0 for v in values):
        raise ValueError(f"{field_name} must contain only positive integers")


def _close_return(closes: Sequence[float], window: int) -> list[Number]:
    out: list[Number] = [None] * len(closes)
    for i in range(window, len(closes)):
        prev = closes[i - window]
        out[i] = ((closes[i] / prev) - 1.0) if prev != 0 else None
    return out


def _log_return(closes: Sequence[float], window: int) -> list[Number]:
    out: list[Number] = [None] * len(closes)
    for i in range(window, len(closes)):
        prev = closes[i - window]
        curr = closes[i]
        if prev <= 0 or curr <= 0:
            out[i] = None
            continue
        out[i] = math.log(curr / prev)
    return out


def _momentum(closes: Sequence[float], window: int) -> list[Number]:
    out: list[Number] = [None] * len(closes)
    for i in range(window, len(closes)):
        out[i] = closes[i] - closes[i - window]
    return out


def _rolling_volatility(one_bar_returns: Sequence[Number], window: int) -> list[Number]:
    out: list[Number] = [None] * len(one_bar_returns)
    for i in range(window, len(one_bar_returns)):
        values = one_bar_returns[i - window + 1 : i + 1]
        if any(v is None for v in values):
            continue
        safe_values = [float(v) for v in values if v is not None]
        if len(safe_values) < 2:
            continue
        out[i] = statistics.stdev(safe_values)
    return out


def _price_vs_sma(closes: Sequence[float], window: int) -> list[Number]:
    sma = IndicatorCalculator.sma(closes, window)
    out: list[Number] = [None] * len(closes)
    for i in range(len(closes)):
        if sma[i] is None or sma[i] == 0:
            continue
        out[i] = (closes[i] / float(sma[i])) - 1.0
    return out


def _sma_spread(closes: Sequence[float], fast: int, slow: int) -> list[Number]:
    fast_sma = IndicatorCalculator.sma(closes, fast)
    slow_sma = IndicatorCalculator.sma(closes, slow)
    out: list[Number] = [None] * len(closes)
    for i in range(len(closes)):
        if fast_sma[i] is None or slow_sma[i] is None or slow_sma[i] == 0:
            continue
        out[i] = (float(fast_sma[i]) / float(slow_sma[i])) - 1.0
    return out


def _rolling_zscore(values: Sequence[float], window: int) -> list[Number]:
    out: list[Number] = [None] * len(values)
    for i in range(window - 1, len(values)):
        window_values = values[i - window + 1 : i + 1]
        mean = statistics.fmean(window_values)
        if len(window_values) < 2:
            continue
        std = statistics.stdev(window_values)
        if std == 0:
            out[i] = 0.0
            continue
        out[i] = (values[i] - mean) / std
    return out


def _rolling_optional_zscore(values: Sequence[Number], window: int) -> list[Number]:
    out: list[Number] = [None] * len(values)
    for i in range(window - 1, len(values)):
        window_values = values[i - window + 1 : i + 1]
        if any(v is None for v in window_values):
            continue
        safe = [float(v) for v in window_values if v is not None]
        mean = statistics.fmean(safe)
        if len(safe) < 2:
            continue
        std = statistics.stdev(safe)
        if std == 0:
            out[i] = 0.0
            continue
        out[i] = (float(values[i]) - mean) / std if values[i] is not None else None
    return out


def _volume_change(volumes: Sequence[Number]) -> list[Number]:
    out: list[Number] = [None] * len(volumes)
    for i in range(1, len(volumes)):
        prev = volumes[i - 1]
        curr = volumes[i]
        if prev is None or curr is None or prev == 0:
            continue
        out[i] = (float(curr) / float(prev)) - 1.0
    return out


def _candle_structure_features(candles: Sequence[Candle]) -> dict[str, list[Number]]:
    body_ratio: list[Number] = [None] * len(candles)
    upper_wick_ratio: list[Number] = [None] * len(candles)
    lower_wick_ratio: list[Number] = [None] * len(candles)
    range_ratio: list[Number] = [None] * len(candles)

    for i, candle in enumerate(candles):
        bar_range = candle.high - candle.low
        if bar_range <= 0:
            body_ratio[i] = 0.0
            upper_wick_ratio[i] = 0.0
            lower_wick_ratio[i] = 0.0
            range_ratio[i] = 0.0
            continue
        body = candle.close - candle.open
        upper_wick = candle.high - max(candle.open, candle.close)
        lower_wick = min(candle.open, candle.close) - candle.low
        body_ratio[i] = body / bar_range
        upper_wick_ratio[i] = upper_wick / bar_range
        lower_wick_ratio[i] = lower_wick / bar_range
        range_ratio[i] = (bar_range / candle.close) if candle.close != 0 else None

    return {
        "candle_body_ratio": body_ratio,
        "candle_upper_wick_ratio": upper_wick_ratio,
        "candle_lower_wick_ratio": lower_wick_ratio,
        "candle_range_ratio": range_ratio,
    }


def _max_lookback(spec: FeatureSpec) -> int:
    lookbacks: list[int] = []
    lookbacks.extend(spec.return_windows)
    lookbacks.extend(spec.log_return_windows)
    lookbacks.extend(spec.volatility_windows)
    lookbacks.extend(spec.momentum_windows)
    lookbacks.extend(spec.sma_windows)
    lookbacks.extend(spec.atr_windows)
    lookbacks.extend(spec.zscore_windows)
    if spec.include_volume_features:
        lookbacks.extend(spec.volume_zscore_windows)
    for fast, slow in spec.sma_crossover_pairs:
        lookbacks.append(max(fast, slow))
    return max(lookbacks, default=1)


def compute_feature_values(
    candles: Sequence[Candle],
    *,
    spec: FeatureSpec,
    missing_volume_policy: MissingVolumePolicy,
) -> FeatureComputationResult:
    _ensure_positive_windows(spec.return_windows, "return_windows")
    _ensure_positive_windows(spec.log_return_windows, "log_return_windows")
    _ensure_positive_windows(spec.volatility_windows, "volatility_windows")
    _ensure_positive_windows(spec.momentum_windows, "momentum_windows")
    _ensure_positive_windows(spec.sma_windows, "sma_windows")
    _ensure_positive_windows(spec.atr_windows, "atr_windows")
    _ensure_positive_windows(spec.zscore_windows, "zscore_windows")
    _ensure_positive_windows(spec.volume_zscore_windows, "volume_zscore_windows")
    for fast, slow in spec.sma_crossover_pairs:
        if fast <= 0 or slow <= 0:
            raise ValueError("sma_crossover_pairs must contain only positive window sizes")

    closes = IndicatorCalculator.closes(candles)
    volumes = IndicatorCalculator.volumes(candles)
    one_bar_returns = _close_return(closes, 1)
    atr_default_window = spec.atr_windows[0] if spec.atr_windows else 14
    atr_values = IndicatorCalculator.atr(candles, period=atr_default_window)

    features: dict[str, list[Number]] = {}
    skipped_features: list[str] = []

    for window in spec.return_windows:
        features[f"return_{window}"] = _close_return(closes, window)
    for window in spec.log_return_windows:
        features[f"log_return_{window}"] = _log_return(closes, window)
    for window in spec.volatility_windows:
        features[f"volatility_{window}"] = _rolling_volatility(one_bar_returns, window)
    for window in spec.momentum_windows:
        features[f"momentum_{window}"] = _momentum(closes, window)
    for window in spec.sma_windows:
        features[f"price_vs_sma_{window}"] = _price_vs_sma(closes, window)
    for fast, slow in spec.sma_crossover_pairs:
        features[f"sma_spread_{fast}_{slow}"] = _sma_spread(closes, fast, slow)
    for window in spec.atr_windows:
        atr_values_for_window = (
            atr_values if window == atr_default_window else IndicatorCalculator.atr(candles, period=window)
        )
        out: list[Number] = [None] * len(closes)
        for i in range(len(closes)):
            if i >= len(atr_values_for_window):
                continue
            atr = atr_values_for_window[i]
            if atr is None or closes[i] == 0:
                continue
            out[i] = float(atr) / closes[i]
        features[f"atr_norm_{window}"] = out
    for window in spec.zscore_windows:
        features[f"close_zscore_{window}"] = _rolling_zscore(closes, window)

    if spec.include_candle_structure:
        features.update(_candle_structure_features(candles))

    has_missing_volume = any(volume is None for volume in volumes)
    if spec.include_volume_features:
        if missing_volume_policy == MissingVolumePolicy.REQUIRE_VOLUME and has_missing_volume:
            raise ValueError(
                "Volume features requested with REQUIRE_VOLUME policy, but candles contain missing volume"
            )
        if not has_missing_volume:
            features["volume_change_1"] = _volume_change(volumes)
            for window in spec.volume_zscore_windows:
                features[f"volume_zscore_{window}"] = _rolling_optional_zscore(volumes, window)
        else:
            skipped_features.extend(["volume_change_1"])
            skipped_features.extend(f"volume_zscore_{window}" for window in spec.volume_zscore_windows)

    return FeatureComputationResult(
        feature_values=features,
        max_lookback_bars=_max_lookback(spec),
        skipped_features=tuple(skipped_features),
    )
