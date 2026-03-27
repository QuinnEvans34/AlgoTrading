"""Thin service wrapper for provider dispatch."""

from __future__ import annotations

from .contracts import (
    HistoricalCandleRequest,
    HistoricalCandleResponse,
    LiveQuoteRequest,
    Quote,
)
from .registry import MarketDataProviderRegistry


class MarketDataService:
    def __init__(self, registry: MarketDataProviderRegistry) -> None:
        self._registry = registry

    def fetch_historical_candles(
        self, provider_name: str, request: HistoricalCandleRequest
    ) -> HistoricalCandleResponse:
        provider = self._registry.get(provider_name)
        return provider.fetch_historical_candles(request)

    def fetch_live_quote(self, provider_name: str, request: LiveQuoteRequest) -> Quote:
        provider = self._registry.get(provider_name)
        return provider.fetch_live_quote(request)
