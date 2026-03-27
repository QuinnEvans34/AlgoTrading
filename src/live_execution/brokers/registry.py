"""Broker adapter resolution for live execution."""

from __future__ import annotations

from ..config import LiveExecutionSettings
from ..contracts import LiveBrokerName
from .base import LiveBrokerAdapter
from .null_broker import NullBrokerAdapter
from .oanda_stub import OandaStubBrokerAdapter, OandaStubConfig


def resolve_broker_name(name: str | LiveBrokerName | None) -> LiveBrokerName:
    if isinstance(name, LiveBrokerName):
        return name
    if name is None:
        return LiveBrokerName.NULL
    candidate = name.strip().lower()
    try:
        return LiveBrokerName(candidate)
    except ValueError:
        return LiveBrokerName.NULL


def create_broker_adapter(settings: LiveExecutionSettings) -> LiveBrokerAdapter:
    broker_name = resolve_broker_name(settings.broker_name)
    if broker_name == LiveBrokerName.OANDA_STUB:
        return OandaStubBrokerAdapter(
            OandaStubConfig(
                api_token=settings.oanda_api_token,
                account_id=settings.oanda_account_id,
                environment=settings.oanda_environment,
            )
        )
    return NullBrokerAdapter()

