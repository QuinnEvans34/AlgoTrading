"""Demo: live-execution boundary status, validation, and safe rejection."""

from __future__ import annotations

import json

from live_execution import (
    LiveExecutionDisabledError,
    LiveExecutionService,
    LiveExecutionSettings,
    LiveOrderSide,
    LiveOrderType,
    LiveTradeIntent,
)
from live_execution.brokers.registry import create_broker_adapter
from market_data import AssetClass, Instrument


def _status_payload(service: LiveExecutionService) -> dict:
    status = service.get_status()
    return {
        "broker_name": status.broker_name.value,
        "enabled": status.enabled,
        "submission_allowed": status.submission_allowed,
        "configured": status.configured,
        "state": status.state.value,
        "message": status.message,
        "capabilities": {
            "supported_asset_classes": [
                asset_class.value
                for asset_class in status.capabilities.supported_asset_classes
            ],
            "supported_order_types": [
                order_type.value for order_type in status.capabilities.supported_order_types
            ],
            "supported_order_sides": [
                side.value for side in status.capabilities.supported_order_sides
            ],
            "supports_short": status.capabilities.supports_short,
            "supports_cancel": status.capabilities.supports_cancel,
            "supports_submit": status.capabilities.supports_submit,
        },
    }


def main() -> None:
    settings = LiveExecutionSettings()
    service = LiveExecutionService(
        settings=settings,
        adapter=create_broker_adapter(settings),
    )

    print("Live execution status:")
    print(json.dumps(_status_payload(service), indent=2))

    intent = LiveTradeIntent(
        instrument=Instrument(symbol="EUR_USD", asset_class=AssetClass.FOREX),
        side=LiveOrderSide.BUY,
        order_type=LiveOrderType.MARKET,
        quantity=10_000.0,
        metadata={"source": "demo"},
    )
    validation = service.validate_intent(intent)
    print("\nValidation preview:")
    print(
        json.dumps(
            {
                "accepted": validation.accepted,
                "reasons": list(validation.reasons),
                "payload_preview": validation.broker_payload_preview,
            },
            indent=2,
            default=str,
        )
    )

    print("\nSubmit attempt:")
    try:
        result = service.submit_intent(intent)
        print(json.dumps({"accepted": result.accepted, "status": result.status}, indent=2))
    except LiveExecutionDisabledError as exc:
        print(f"Rejected as expected: {exc}")


if __name__ == "__main__":
    main()

