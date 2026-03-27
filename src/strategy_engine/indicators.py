"""Reusable indicator calculations over normalized candle data."""

from __future__ import annotations

from dataclasses import dataclass
import math
import statistics
from typing import Sequence

from market_data.contracts import Candle


Number = float | None


@dataclass(frozen=True)
class BollingerBands:
    upper: tuple[Number, ...]
    middle: tuple[Number, ...]
    lower: tuple[Number, ...]


@dataclass(frozen=True)
class MACDResult:
    line: tuple[float, ...]
    signal: tuple[float, ...]
    histogram: tuple[float, ...]


@dataclass(frozen=True)
class StochasticResult:
    k_percent: tuple[Number, ...]
    d_percent: tuple[Number, ...]


class IndicatorCalculator:
    @staticmethod
    def closes(candles: Sequence[Candle]) -> list[float]:
        return [c.close for c in candles]

    @staticmethod
    def highs(candles: Sequence[Candle]) -> list[float]:
        return [c.high for c in candles]

    @staticmethod
    def lows(candles: Sequence[Candle]) -> list[float]:
        return [c.low for c in candles]

    @staticmethod
    def volumes(candles: Sequence[Candle]) -> list[Number]:
        return [c.volume for c in candles]

    @staticmethod
    def sma(values: Sequence[float], period: int) -> list[Number]:
        if period <= 0:
            raise ValueError("period must be > 0")
        out: list[Number] = [None] * len(values)
        for i in range(period - 1, len(values)):
            window = values[i - period + 1 : i + 1]
            out[i] = statistics.fmean(window)
        return out

    @staticmethod
    def sma_optional(values: Sequence[Number], period: int) -> list[Number]:
        if period <= 0:
            raise ValueError("period must be > 0")
        out: list[Number] = [None] * len(values)
        for i in range(period - 1, len(values)):
            window = values[i - period + 1 : i + 1]
            if any(v is None for v in window):
                continue
            out[i] = statistics.fmean(v for v in window if v is not None)
        return out

    @staticmethod
    def ema(values: Sequence[float], period: int) -> list[float]:
        if period <= 0:
            raise ValueError("period must be > 0")
        if not values:
            return []
        alpha = 2.0 / (period + 1.0)
        out: list[float] = [values[0]]
        prev = values[0]
        for value in values[1:]:
            prev = (value * alpha) + (prev * (1.0 - alpha))
            out.append(prev)
        return out

    @staticmethod
    def rolling_std(values: Sequence[float], period: int) -> list[Number]:
        if period <= 1:
            raise ValueError("period must be > 1")
        out: list[Number] = [None] * len(values)
        for i in range(period - 1, len(values)):
            window = values[i - period + 1 : i + 1]
            out[i] = statistics.stdev(window) if len(window) > 1 else 0.0
        return out

    @staticmethod
    def rsi(values: Sequence[float], period: int = 14) -> list[Number]:
        if period <= 0:
            raise ValueError("period must be > 0")
        out: list[Number] = [None] * len(values)
        if len(values) < period + 1:
            return out

        for i in range(period, len(values)):
            gains: list[float] = []
            losses: list[float] = []
            for j in range(i - period + 1, i + 1):
                delta = values[j] - values[j - 1]
                if delta >= 0:
                    gains.append(delta)
                    losses.append(0.0)
                else:
                    gains.append(0.0)
                    losses.append(-delta)
            avg_gain = statistics.fmean(gains)
            avg_loss = statistics.fmean(losses)
            if avg_loss == 0:
                out[i] = 100.0
            else:
                rs = avg_gain / avg_loss
                out[i] = 100.0 - (100.0 / (1.0 + rs))
        return out

    @staticmethod
    def bollinger_bands(
        values: Sequence[float], period: int = 20, std_dev: float = 2.0
    ) -> BollingerBands:
        middle = IndicatorCalculator.sma(values, period)
        sigma = IndicatorCalculator.rolling_std(values, period) if len(values) >= 2 else []
        upper: list[Number] = [None] * len(values)
        lower: list[Number] = [None] * len(values)
        for i in range(len(values)):
            if i >= len(sigma):
                continue
            if middle[i] is None or sigma[i] is None:
                continue
            upper[i] = middle[i] + (sigma[i] * std_dev)
            lower[i] = middle[i] - (sigma[i] * std_dev)
        return BollingerBands(tuple(upper), tuple(middle), tuple(lower))

    @staticmethod
    def macd(
        values: Sequence[float],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> MACDResult:
        ema_fast = IndicatorCalculator.ema(values, fast_period)
        ema_slow = IndicatorCalculator.ema(values, slow_period)
        line = [f - s for f, s in zip(ema_fast, ema_slow, strict=False)]
        signal = IndicatorCalculator.ema(line, signal_period)
        histogram = [m - s for m, s in zip(line, signal, strict=False)]
        return MACDResult(tuple(line), tuple(signal), tuple(histogram))

    @staticmethod
    def stochastic(
        candles: Sequence[Candle], k_period: int = 14, d_period: int = 3
    ) -> StochasticResult:
        closes = IndicatorCalculator.closes(candles)
        highs = IndicatorCalculator.highs(candles)
        lows = IndicatorCalculator.lows(candles)

        k_values: list[Number] = [None] * len(candles)
        for i in range(k_period - 1, len(candles)):
            highest = max(highs[i - k_period + 1 : i + 1])
            lowest = min(lows[i - k_period + 1 : i + 1])
            denom = highest - lowest
            if denom == 0:
                k_values[i] = 50.0
            else:
                k_values[i] = 100.0 * ((closes[i] - lowest) / denom)
        d_values = IndicatorCalculator.sma_optional(k_values, d_period)
        return StochasticResult(tuple(k_values), tuple(d_values))

    @staticmethod
    def atr(candles: Sequence[Candle], period: int = 14) -> list[Number]:
        if not candles:
            return []
        tr_values: list[float] = []
        prev_close: float | None = None
        for candle in candles:
            if prev_close is None:
                tr = candle.high - candle.low
            else:
                tr = max(
                    candle.high - candle.low,
                    abs(candle.high - prev_close),
                    abs(candle.low - prev_close),
                )
            tr_values.append(tr)
            prev_close = candle.close
        return IndicatorCalculator.sma(tr_values, period)

    @staticmethod
    def adx(candles: Sequence[Candle], period: int = 14) -> list[Number]:
        n = len(candles)
        if n == 0:
            return []

        highs = IndicatorCalculator.highs(candles)
        lows = IndicatorCalculator.lows(candles)
        closes = IndicatorCalculator.closes(candles)

        tr_values: list[float] = [highs[0] - lows[0]]
        dm_plus: list[float] = [0.0]
        dm_minus: list[float] = [0.0]

        for i in range(1, n):
            up_move = highs[i] - highs[i - 1]
            down_move = lows[i - 1] - lows[i]
            dm_plus.append(up_move if up_move > down_move and up_move > 0 else 0.0)
            dm_minus.append(down_move if down_move > up_move and down_move > 0 else 0.0)

            tr_values.append(
                max(
                    highs[i] - lows[i],
                    abs(highs[i] - closes[i - 1]),
                    abs(lows[i] - closes[i - 1]),
                )
            )

        atr_values = IndicatorCalculator.sma(tr_values, period)
        dm_plus_smoothed = IndicatorCalculator.sma(dm_plus, period)
        dm_minus_smoothed = IndicatorCalculator.sma(dm_minus, period)

        di_plus: list[Number] = [None] * n
        di_minus: list[Number] = [None] * n
        dx: list[Number] = [None] * n

        for i in range(n):
            atr = atr_values[i]
            plus = dm_plus_smoothed[i]
            minus = dm_minus_smoothed[i]
            if atr is None or atr == 0 or plus is None or minus is None:
                continue
            di_plus[i] = 100.0 * (plus / atr)
            di_minus[i] = 100.0 * (minus / atr)
            denom = (di_plus[i] or 0.0) + (di_minus[i] or 0.0)
            if denom == 0:
                dx[i] = 0.0
            else:
                dx[i] = 100.0 * abs((di_plus[i] or 0.0) - (di_minus[i] or 0.0)) / denom

        return IndicatorCalculator.sma_optional(dx, period)

    @staticmethod
    def annualized_volatility(
        closes: Sequence[float], periods_per_year: int = 252
    ) -> float | None:
        if len(closes) < 3:
            return None
        returns: list[float] = []
        for i in range(1, len(closes)):
            prev = closes[i - 1]
            curr = closes[i]
            if prev == 0:
                continue
            returns.append((curr - prev) / prev)
        if len(returns) < 2:
            return None
        return statistics.stdev(returns) * math.sqrt(periods_per_year)

    @staticmethod
    def latest(values: Sequence[Number]) -> float | None:
        for value in reversed(values):
            if value is not None:
                return float(value)
        return None

    @staticmethod
    def tail_non_null(values: Sequence[Number], count: int) -> list[float]:
        out: list[float] = []
        for value in reversed(values):
            if value is None:
                continue
            out.append(float(value))
            if len(out) >= count:
                break
        out.reverse()
        return out
