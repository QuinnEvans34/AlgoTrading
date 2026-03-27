"""Capability helpers for live broker adapters."""

from __future__ import annotations

from ..contracts import BrokerCapabilities, LiveOrderSide, LiveOrderType, LiveTradeIntent


def unsupported_reasons(
    intent: LiveTradeIntent,
    capabilities: BrokerCapabilities,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if intent.instrument.asset_class not in capabilities.supported_asset_classes:
        reasons.append(
            f"unsupported_asset_class:{intent.instrument.asset_class.value}"
        )
    if intent.order_type not in capabilities.supported_order_types:
        reasons.append(f"unsupported_order_type:{intent.order_type.value}")
    if intent.side not in capabilities.supported_order_sides:
        reasons.append(f"unsupported_order_side:{intent.side.value}")
    # Conservative rule in this phase: if shorting is unsupported, reject sell intents.
    if intent.side == LiveOrderSide.SELL and not capabilities.supports_short:
        reasons.append("short_or_sell_not_supported")
    if intent.order_type == LiveOrderType.LIMIT and intent.limit_price is None:
        reasons.append("limit_price_required")
    if intent.order_type == LiveOrderType.MARKET and intent.limit_price is not None:
        reasons.append("limit_price_not_allowed_for_market_order")
    return tuple(reasons)

