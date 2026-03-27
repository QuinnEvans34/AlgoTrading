"""Null broker adapter that fails closed for live submission."""

from __future__ import annotations

from typing import Any, Mapping

from market_data import AssetClass

from ..contracts import (
    BrokerCapabilities,
    LiveBrokerName,
    LiveSubmitResult,
    LiveTradeIntent,
)
from ..exceptions import LiveExecutionNotConfiguredError
from .base import LiveBrokerAdapter


class NullBrokerAdapter(LiveBrokerAdapter):
    @property
    def broker_name(self) -> LiveBrokerName:
        return LiveBrokerName.NULL

    @property
    def capabilities(self) -> BrokerCapabilities:
        return BrokerCapabilities(
            supported_asset_classes=(AssetClass.STOCK, AssetClass.FOREX),
            supported_order_types=(),
            supported_order_sides=(),
            supports_short=False,
            supports_cancel=False,
            supports_submit=False,
        )

    def is_configured(self) -> bool:
        return False

    def configuration_message(self) -> str:
        return "No live broker is configured. Null adapter is active."

    def map_intent_to_payload(self, intent: LiveTradeIntent) -> Mapping[str, Any]:
        return {
            "broker": self.broker_name.value,
            "status": "disabled",
            "intent": {
                "symbol": intent.instrument.symbol,
                "side": intent.side.value,
                "order_type": intent.order_type.value,
                "quantity": intent.quantity,
                "limit_price": intent.limit_price,
            },
        }

    def submit_intent(self, intent: LiveTradeIntent) -> LiveSubmitResult:
        raise LiveExecutionNotConfiguredError(
            "Null broker is active. Live submission is unavailable."
        )

