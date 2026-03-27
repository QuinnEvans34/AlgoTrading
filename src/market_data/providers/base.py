"""Provider interface contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..contracts import (
    HistoricalCandleRequest,
    HistoricalCandleResponse,
    LiveQuoteRequest,
    Quote,
)


class MarketDataProvider(ABC):
    """Provider boundary for market data adapters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Stable provider name (for logging/metadata/registry)."""

    @abstractmethod
    def fetch_historical_candles(
        self, request: HistoricalCandleRequest
    ) -> HistoricalCandleResponse:
        """Fetch normalized historical OHLCV candles."""

    @abstractmethod
    def fetch_live_quote(self, request: LiveQuoteRequest) -> Quote:
        """Fetch normalized latest quote for an instrument."""
