"""Base broker adapter contract for live execution."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping

from ..contracts import (
    BrokerCapabilities,
    LiveBrokerName,
    LiveSubmitResult,
    LiveTradeIntent,
)


class LiveBrokerAdapter(ABC):
    @property
    @abstractmethod
    def broker_name(self) -> LiveBrokerName:
        """Return adapter broker name."""

    @property
    @abstractmethod
    def capabilities(self) -> BrokerCapabilities:
        """Return static broker capability description."""

    @abstractmethod
    def is_configured(self) -> bool:
        """Return whether required credentials/config are present."""

    @abstractmethod
    def configuration_message(self) -> str:
        """Return human-readable configuration status."""

    @abstractmethod
    def map_intent_to_payload(self, intent: LiveTradeIntent) -> Mapping[str, Any]:
        """Map generic intent to broker payload preview."""

    @abstractmethod
    def submit_intent(self, intent: LiveTradeIntent) -> LiveSubmitResult:
        """Attempt intent submission through broker adapter."""

