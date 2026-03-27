"""Provider-agnostic market data subsystem."""

from .contracts import (
    AssetClass,
    BarInterval,
    Candle,
    HistoricalCandleRequest,
    HistoricalCandleResponse,
    Instrument,
    LiveQuoteRequest,
    Quote,
)
from .exceptions import (
    MarketDataAuthError,
    MarketDataError,
    MarketDataRequestError,
    UnsupportedInstrumentError,
)
from .providers import MarketDataProvider, OandaMarketDataProvider
from .providers.oanda import OandaConfig
from .registry import MarketDataProviderRegistry
from .service import MarketDataService

__all__ = [
    "AssetClass",
    "BarInterval",
    "Candle",
    "HistoricalCandleRequest",
    "HistoricalCandleResponse",
    "Instrument",
    "LiveQuoteRequest",
    "Quote",
    "MarketDataAuthError",
    "MarketDataError",
    "MarketDataRequestError",
    "UnsupportedInstrumentError",
    "MarketDataProvider",
    "OandaConfig",
    "OandaMarketDataProvider",
    "MarketDataProviderRegistry",
    "MarketDataService",
]
