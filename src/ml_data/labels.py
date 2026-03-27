"""Label generation utilities with explicit forward-horizon alignment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from market_data.contracts import Candle

from .contracts import DirectionLabelSpec, FutureReturnLabelSpec, LabelSpec


Number = float | int | None


@dataclass(frozen=True)
class LabelComputationResult:
    label_values: dict[str, list[Number]]
    max_horizon_bars: int


def _future_return(closes: Sequence[float], horizon_bars: int) -> list[float | None]:
    out: list[float | None] = [None] * len(closes)
    last_index = len(closes) - horizon_bars
    for i in range(0, last_index):
        base = closes[i]
        future = closes[i + horizon_bars]
        if base == 0:
            continue
        out[i] = (future / base) - 1.0
    return out


def _direction_label(
    future_returns: Sequence[float | None],
    *,
    threshold: float,
) -> list[int | None]:
    out: list[int | None] = [None] * len(future_returns)
    for i, value in enumerate(future_returns):
        if value is None:
            continue
        out[i] = 1 if value > threshold else 0
    return out


def compute_label_values(
    candles: Sequence[Candle],
    *,
    label_specs: Sequence[LabelSpec],
) -> LabelComputationResult:
    if len(label_specs) == 0:
        raise ValueError("At least one label spec is required")

    closes = [c.close for c in candles]
    labels: dict[str, list[Number]] = {}
    max_horizon = 0

    for spec in label_specs:
        if spec.horizon_bars <= 0:
            raise ValueError("label horizon_bars must be > 0")
        if spec.price_field != "close":
            raise ValueError("Only price_field='close' is supported in this phase")

        max_horizon = max(max_horizon, spec.horizon_bars)

        if isinstance(spec, FutureReturnLabelSpec):
            name = spec.resolved_name()
            labels[name] = _future_return(closes, spec.horizon_bars)
            continue

        if isinstance(spec, DirectionLabelSpec):
            name = spec.resolved_name()
            future_returns = _future_return(closes, spec.horizon_bars)
            labels[name] = _direction_label(future_returns, threshold=spec.threshold)
            continue

        raise ValueError(f"Unsupported label spec type: {type(spec)!r}")

    return LabelComputationResult(
        label_values=labels,
        max_horizon_bars=max_horizon,
    )

