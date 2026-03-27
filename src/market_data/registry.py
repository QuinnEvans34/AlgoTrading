"""Simple provider registry to support plug-and-play adapters."""

from __future__ import annotations

from typing import Dict

from .providers.base import MarketDataProvider


class MarketDataProviderRegistry:
    def __init__(self) -> None:
        self._providers: Dict[str, MarketDataProvider] = {}

    def register(self, provider: MarketDataProvider) -> None:
        self._providers[provider.name] = provider

    def get(self, name: str) -> MarketDataProvider:
        return self._providers[name]

    def available(self) -> tuple[str, ...]:
        return tuple(sorted(self._providers.keys()))
