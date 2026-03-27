"""Disabled OANDA broker stub for live-execution boundary testing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from market_data import AssetClass

from ..contracts import (
    BrokerCapabilities,
    LiveBrokerName,
    LiveOrderSide,
    LiveOrderType,
    LiveSubmitResult,
    LiveTradeIntent,
)
from ..exceptions import (
    LiveExecutionNotConfiguredError,
    LiveExecutionUnsupportedCapabilityError,
)
from .base import LiveBrokerAdapter


@dataclass(frozen=True)
class OandaStubConfig:
    api_token: str | None = None
    account_id: str | None = None
    environment: str = "practice"

    @property
    def configured(self) -> bool:
        return bool(self.api_token and self.account_id)


class OandaStubBrokerAdapter(LiveBrokerAdapter):
    def __init__(self, config: OandaStubConfig) -> None:
        self._config = config

    @property
    def broker_name(self) -> LiveBrokerName:
        return LiveBrokerName.OANDA_STUB

    @property
    def capabilities(self) -> BrokerCapabilities:
        return BrokerCapabilities(
            supported_asset_classes=(AssetClass.FOREX,),
            supported_order_types=(LiveOrderType.MARKET, LiveOrderType.LIMIT),
            supported_order_sides=(LiveOrderSide.BUY, LiveOrderSide.SELL),
            supports_short=True,
            supports_cancel=True,
            supports_submit=False,
        )

    def is_configured(self) -> bool:
        return self._config.configured

    def configuration_message(self) -> str:
        if not self._config.configured:
            return (
                "OANDA stub is selected but credentials are not configured "
                "(LIVE_OANDA_API_TOKEN and LIVE_OANDA_ACCOUNT_ID)."
            )
        return (
            "OANDA stub is configured but remains submission-disabled in this phase."
        )

    def map_intent_to_payload(self, intent: LiveTradeIntent) -> Mapping[str, Any]:
        units = intent.quantity if intent.side == LiveOrderSide.BUY else -intent.quantity
        order: dict[str, Any] = {
            "instrument": intent.instrument.symbol,
            "units": str(int(units) if float(units).is_integer() else units),
            "type": intent.order_type.value.upper(),
            "positionFill": "DEFAULT",
        }
        if intent.order_type == LiveOrderType.LIMIT:
            order["price"] = str(intent.limit_price)
            order["timeInForce"] = "GTC"
        else:
            order["timeInForce"] = "FOK"
        if intent.client_order_id:
            order["clientExtensions"] = {"id": intent.client_order_id}
        return {
            "endpoint": f"/v3/accounts/{self._config.account_id}/orders",
            "environment": self._config.environment,
            "payload": {"order": order},
        }

    def submit_intent(self, intent: LiveTradeIntent) -> LiveSubmitResult:
        if not self._config.configured:
            raise LiveExecutionNotConfiguredError(self.configuration_message())
        raise LiveExecutionUnsupportedCapabilityError(
            "OANDA stub adapter does not submit real orders in this phase."
        )

