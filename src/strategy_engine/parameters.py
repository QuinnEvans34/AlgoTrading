"""Strategy-specific parameter models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from market_data.contracts import AssetClass, Instrument


@dataclass(frozen=True)
class TechnicalRuleThresholds:
    min_candles: int = 60
    min_confidence: float = 0.25
    max_confidence: float = 0.95

    rsi_period: int = 14
    rsi_z_window: int = 50
    rsi_z_threshold: float = 0.8

    ema_period: int = 20
    bollinger_period: int = 20
    bollinger_std_dev: float = 2.0
    bollinger_midpoint: float = 0.5

    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    macd_noise_factor: float = 0.5
    macd_min_hist_abs: float = 0.0

    stoch_k_period: int = 14
    stoch_d_period: int = 3
    stoch_lower: float = 25.0
    stoch_upper: float = 75.0

    adx_period: int = 14
    adx_floor: float = 10.0

    volatility_min: float = 0.03
    volatility_max: float = 2.50

    fvg_lookback_bars: int = 10
    fvg_min_gap_fraction: float = 0.0002

    volume_filter_enabled: bool = True
    volume_ratio_floor: float = 0.25


@dataclass(frozen=True)
class TechnicalRuleParameterSet:
    default_thresholds: TechnicalRuleThresholds = field(
        default_factory=TechnicalRuleThresholds
    )
    by_asset_class: Mapping[AssetClass, TechnicalRuleThresholds] = field(
        default_factory=dict
    )
    by_symbol: Mapping[str, TechnicalRuleThresholds] = field(default_factory=dict)

    def resolve(self, instrument: Instrument) -> TechnicalRuleThresholds:
        symbol_key = instrument.symbol.upper()
        if symbol_key in self.by_symbol:
            return self.by_symbol[symbol_key]
        if instrument.asset_class in self.by_asset_class:
            return self.by_asset_class[instrument.asset_class]
        return self.default_thresholds

    @classmethod
    def multi_asset_defaults(cls) -> "TechnicalRuleParameterSet":
        stock = TechnicalRuleThresholds(
            volatility_min=0.05,
            volatility_max=3.00,
            adx_floor=12.0,
            fvg_min_gap_fraction=0.0010,
        )
        forex = TechnicalRuleThresholds(
            volatility_min=0.02,
            volatility_max=1.20,
            adx_floor=8.0,
            fvg_min_gap_fraction=0.00015,
        )
        return cls(
            default_thresholds=TechnicalRuleThresholds(),
            by_asset_class={
                AssetClass.STOCK: stock,
                AssetClass.FOREX: forex,
            },
        )
