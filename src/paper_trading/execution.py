"""Execution and fill simulation rules for the paper trading sandbox."""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import PaperAccountConfig, PaperOrder, PaperOrderSide, PaperOrderType


@dataclass(frozen=True)
class FillComputation:
    fill_price: float
    spread_cost: float
    slippage_cost: float
    commission: float


def is_limit_marketable(order: PaperOrder, market_price: float) -> bool:
    if order.order_type != PaperOrderType.LIMIT:
        return False
    if order.limit_price is None:
        return False
    if order.side == PaperOrderSide.BUY:
        return market_price <= order.limit_price
    return market_price >= order.limit_price


def compute_market_fill(
    *,
    order: PaperOrder,
    base_price: float,
    config: PaperAccountConfig,
) -> FillComputation:
    if order.order_type != PaperOrderType.MARKET:
        raise ValueError("compute_market_fill expects a market order")
    if base_price <= 0:
        raise ValueError("base_price must be > 0")

    half_spread_fraction = max(0.0, config.default_spread_bps / 20_000.0)
    slippage_fraction = max(0.0, config.default_slippage_bps / 10_000.0)
    friction = half_spread_fraction + slippage_fraction

    if order.side == PaperOrderSide.BUY:
        fill_price = base_price * (1.0 + friction)
    else:
        fill_price = base_price * (1.0 - friction)

    notional = abs(order.quantity * fill_price)
    commission = _commission_from_notional(notional=notional, config=config)
    spread_cost = abs(order.quantity * base_price) * half_spread_fraction
    slippage_cost = abs(order.quantity * base_price) * slippage_fraction
    return FillComputation(
        fill_price=fill_price,
        spread_cost=spread_cost,
        slippage_cost=slippage_cost,
        commission=commission,
    )


def compute_limit_fill(
    *,
    order: PaperOrder,
    config: PaperAccountConfig,
) -> FillComputation:
    if order.order_type != PaperOrderType.LIMIT:
        raise ValueError("compute_limit_fill expects a limit order")
    if order.limit_price is None or order.limit_price <= 0:
        raise ValueError("limit order requires a positive limit_price")

    fill_price = order.limit_price
    notional = abs(order.quantity * fill_price)
    commission = _commission_from_notional(notional=notional, config=config)
    return FillComputation(
        fill_price=fill_price,
        spread_cost=0.0,
        slippage_cost=0.0,
        commission=commission,
    )


def _commission_from_notional(*, notional: float, config: PaperAccountConfig) -> float:
    bps_component = notional * max(0.0, config.commission_bps / 10_000.0)
    fixed_component = max(0.0, config.commission_fixed)
    return bps_component + fixed_component

