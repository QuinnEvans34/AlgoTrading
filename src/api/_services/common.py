"""Shared helpers for internal API service collaborators."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from config import AppSettings
from live_execution import (
    GuardCheckResult,
    LiveExecutionAdapterTimeoutError,
    LiveExecutionDisabledError,
    LiveExecutionNotConfiguredError,
    LiveExecutionUnsupportedCapabilityError,
    LiveOrderSide,
    LiveOrderType,
    LiveTradeIntent,
)
from market_data import Instrument

from ..config import APISettings
from ..errors import APIError
from ..live_execution_schemas import LiveTradeIntentSchema


def ensure_feature_enabled(
    app_settings: AppSettings,
    flag_name: str,
    *,
    code: str,
    message: str,
) -> None:
    flags = app_settings.feature_flags
    if not getattr(flags, flag_name):
        raise APIError(
            status_code=403,
            code=code,
            message=message,
        )


def history_root(settings: APISettings) -> Path:
    return Path(settings.default_run_output_dir)


def guard_check_payload(check: GuardCheckResult) -> dict[str, Any]:
    return {
        "name": check.name,
        "passed": check.passed,
        "code": check.code,
        "message": check.message,
    }


def status_payload(status: Any) -> dict[str, Any]:
    return {
        "broker_name": status.broker_name.value,
        "configured": status.configured,
        "enabled": status.enabled,
        "submission_allowed": status.submission_allowed,
        "state": status.state.value,
        "message": status.message,
        "capabilities": {
            "supported_asset_classes": [
                asset_class.value for asset_class in status.capabilities.supported_asset_classes
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


def to_instrument(schema: Any) -> Instrument:
    return Instrument(
        symbol=schema.symbol,
        asset_class=schema.asset_class,
        venue=schema.venue,
        quote_currency=schema.quote_currency,
    )


def to_live_trade_intent(schema: LiveTradeIntentSchema) -> LiveTradeIntent:
    return LiveTradeIntent(
        instrument=Instrument(
            symbol=schema.instrument.symbol,
            asset_class=schema.instrument.asset_class,
            venue=schema.instrument.venue,
            quote_currency=schema.instrument.quote_currency,
        ),
        side=LiveOrderSide(schema.side),
        order_type=LiveOrderType(schema.order_type),
        quantity=schema.quantity,
        limit_price=schema.limit_price,
        client_order_id=schema.client_order_id,
        metadata=dict(schema.metadata),
    )


def map_live_execution_error(exc: Exception) -> APIError:
    if isinstance(exc, LiveExecutionDisabledError):
        return APIError(
            status_code=409,
            code="live_execution_disabled",
            message=str(exc),
        )
    if isinstance(exc, LiveExecutionNotConfiguredError):
        return APIError(
            status_code=409,
            code="live_execution_not_configured",
            message=str(exc),
        )
    if isinstance(exc, LiveExecutionUnsupportedCapabilityError):
        return APIError(
            status_code=400,
            code="live_execution_unsupported",
            message=str(exc),
        )
    if isinstance(exc, LiveExecutionAdapterTimeoutError):
        return APIError(
            status_code=504,
            code="live_execution_timeout",
            message=str(exc),
        )
    return APIError(
        status_code=502,
        code="live_execution_adapter_error",
        message=str(exc),
    )
