"""Execution fill and transaction cost abstractions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from market_data.contracts import Instrument

from .contracts import PositionDirection


class SpreadModel(ABC):
    @abstractmethod
    def half_spread_fraction(self, *, instrument: Instrument, timestamp: datetime) -> float:
        """Return half-spread as fraction of price (e.g., 0.0001 = 1 bps)."""


class SlippageModel(ABC):
    @abstractmethod
    def slippage_fraction(
        self,
        *,
        instrument: Instrument,
        timestamp: datetime,
        direction: PositionDirection,
        is_entry: bool,
    ) -> float:
        """Return slippage as fraction of price."""


class CommissionModel(ABC):
    @abstractmethod
    def commission(
        self,
        *,
        instrument: Instrument,
        timestamp: datetime,
        notional: float,
    ) -> float:
        """Return commission in account currency."""


@dataclass(frozen=True)
class FixedBpsSpreadModel(SpreadModel):
    half_spread_bps: float = 0.0

    def half_spread_fraction(self, *, instrument: Instrument, timestamp: datetime) -> float:
        return self.half_spread_bps / 10_000.0


@dataclass(frozen=True)
class FixedBpsSlippageModel(SlippageModel):
    bps: float = 0.0

    def slippage_fraction(
        self,
        *,
        instrument: Instrument,
        timestamp: datetime,
        direction: PositionDirection,
        is_entry: bool,
    ) -> float:
        return self.bps / 10_000.0


@dataclass(frozen=True)
class FixedBpsCommissionModel(CommissionModel):
    bps: float = 0.0

    def commission(
        self,
        *,
        instrument: Instrument,
        timestamp: datetime,
        notional: float,
    ) -> float:
        return abs(notional) * (self.bps / 10_000.0)


@dataclass(frozen=True)
class FixedFeeCommissionModel(CommissionModel):
    fee_per_fill: float = 0.0

    def commission(
        self,
        *,
        instrument: Instrument,
        timestamp: datetime,
        notional: float,
    ) -> float:
        _ = instrument, timestamp, notional
        return self.fee_per_fill


@dataclass(frozen=True)
class CompositeCommissionModel(CommissionModel):
    notional_bps: float = 0.0
    fixed_fee: float = 0.0

    def commission(
        self,
        *,
        instrument: Instrument,
        timestamp: datetime,
        notional: float,
    ) -> float:
        _ = instrument, timestamp
        return abs(notional) * (self.notional_bps / 10_000.0) + self.fixed_fee


@dataclass(frozen=True)
class FillModel:
    spread_model: SpreadModel
    slippage_model: SlippageModel

    def entry_fill_price(
        self,
        *,
        instrument: Instrument,
        timestamp: datetime,
        raw_price: float,
        direction: PositionDirection,
    ) -> float:
        friction = self._friction_fraction(
            instrument=instrument,
            timestamp=timestamp,
            direction=direction,
            is_entry=True,
        )
        if direction == PositionDirection.LONG:
            return raw_price * (1.0 + friction)
        return raw_price * (1.0 - friction)

    def exit_fill_price(
        self,
        *,
        instrument: Instrument,
        timestamp: datetime,
        raw_price: float,
        direction: PositionDirection,
    ) -> float:
        friction = self._friction_fraction(
            instrument=instrument,
            timestamp=timestamp,
            direction=direction,
            is_entry=False,
        )
        if direction == PositionDirection.LONG:
            return raw_price * (1.0 - friction)
        return raw_price * (1.0 + friction)

    def _friction_fraction(
        self,
        *,
        instrument: Instrument,
        timestamp: datetime,
        direction: PositionDirection,
        is_entry: bool,
    ) -> float:
        spread = self.spread_model.half_spread_fraction(
            instrument=instrument,
            timestamp=timestamp,
        )
        slippage = self.slippage_model.slippage_fraction(
            instrument=instrument,
            timestamp=timestamp,
            direction=direction,
            is_entry=is_entry,
        )
        return max(0.0, spread + slippage)
