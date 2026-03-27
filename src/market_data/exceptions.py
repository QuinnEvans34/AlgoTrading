"""Market data subsystem exception hierarchy."""


class MarketDataError(Exception):
    """Base class for market data errors."""


class MarketDataAuthError(MarketDataError):
    """Authentication/authorization failure from a provider."""


class MarketDataRequestError(MarketDataError):
    """Non-auth request failure from a provider."""


class UnsupportedInstrumentError(MarketDataError):
    """Instrument or asset class is not supported by this provider."""
