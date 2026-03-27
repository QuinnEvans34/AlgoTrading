"""OANDA market data adapter using provider-neutral contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from ..contracts import (
    AssetClass,
    BarInterval,
    Candle,
    HistoricalCandleRequest,
    HistoricalCandleResponse,
    LiveQuoteRequest,
    Quote,
    ensure_utc,
)
from ..exceptions import (
    MarketDataAuthError,
    MarketDataRequestError,
    UnsupportedInstrumentError,
)
from ..retry import RetryPolicy, run_with_retry
from .base import MarketDataProvider


@dataclass(frozen=True)
class OandaConfig:
    api_token: str
    account_id: str | None = None
    environment: str = "practice"
    timeout_seconds: int = 15


class _RetryableHttpError(RuntimeError):
    """Internal marker for retryable HTTP statuses."""


class OandaMarketDataProvider(MarketDataProvider):
    _INTERVAL_TO_GRANULARITY = {
        BarInterval.M1: "M1",
        BarInterval.M5: "M5",
        BarInterval.M15: "M15",
        BarInterval.M30: "M30",
        BarInterval.H1: "H1",
        BarInterval.H4: "H4",
        BarInterval.D1: "D",
    }

    _CHUNK_BY_INTERVAL = {
        BarInterval.M1: timedelta(days=2),
        BarInterval.M5: timedelta(days=7),
        BarInterval.M15: timedelta(days=21),
        BarInterval.M30: timedelta(days=30),
        BarInterval.H1: timedelta(days=60),
        BarInterval.H4: timedelta(days=180),
        BarInterval.D1: timedelta(days=365),
    }

    _RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

    def __init__(
        self,
        config: OandaConfig,
        *,
        session: requests.Session | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self._config = config
        self._session = session or requests.Session()
        self._retry_policy = retry_policy or RetryPolicy(max_attempts=3)
        self._headers = {
            "Authorization": f"Bearer {config.api_token}",
            "Accept": "application/json",
        }
        if config.environment == "live":
            self._base_url = "https://api-fxtrade.oanda.com/v3"
        else:
            self._base_url = "https://api-fxpractice.oanda.com/v3"

    @property
    def name(self) -> str:
        return "oanda"

    def fetch_historical_candles(
        self, request: HistoricalCandleRequest
    ) -> HistoricalCandleResponse:
        if request.instrument.asset_class != AssetClass.FOREX:
            raise UnsupportedInstrumentError(
                "OANDA adapter currently supports forex instruments only"
            )

        start, end = request.validated_range()
        oanda_instrument = self._to_oanda_instrument(request.instrument.symbol)
        granularity = self._INTERVAL_TO_GRANULARITY[request.interval]

        all_candles: list[Candle] = []
        chunk_count = 0
        for chunk_start, chunk_end in self._iter_chunks(start, end, request.interval):
            chunk_count += 1
            chunk_candles = self._fetch_chunk_with_fallbacks(
                instrument=oanda_instrument,
                granularity=granularity,
                chunk_start=chunk_start,
                chunk_end=chunk_end,
            )
            all_candles.extend(chunk_candles)

        deduped = self._dedupe_sort_clip(all_candles, start, end, request.limit)
        return HistoricalCandleResponse(
            provider=self.name,
            instrument=request.instrument,
            interval=request.interval,
            candles=tuple(deduped),
            metadata={
                "provider_instrument": oanda_instrument,
                "requested_start": start.isoformat(),
                "requested_end": end.isoformat(),
                "chunk_count": chunk_count,
            },
        )

    def fetch_live_quote(self, request: LiveQuoteRequest) -> Quote:
        if request.instrument.asset_class != AssetClass.FOREX:
            raise UnsupportedInstrumentError(
                "OANDA adapter currently supports forex instruments only"
            )
        if not self._config.account_id:
            raise MarketDataRequestError(
                "OandaConfig.account_id is required to fetch live quotes"
            )

        oanda_instrument = self._to_oanda_instrument(request.instrument.symbol)
        payload = self._request_json(
            path=f"/accounts/{self._config.account_id}/pricing",
            params={"instruments": oanda_instrument},
        )

        prices = payload.get("prices", [])
        if not prices:
            raise MarketDataRequestError(
                f"OANDA returned no prices for {oanda_instrument}"
            )

        price = prices[0]
        timestamp = self._parse_oanda_time(price.get("time"))
        bid = self._first_level_price(price.get("bids"))
        ask = self._first_level_price(price.get("asks"))
        mid = self._calculate_mid(bid, ask)

        if mid is None:
            closeout_bid = self._to_float(price.get("closeoutBid"))
            closeout_ask = self._to_float(price.get("closeoutAsk"))
            mid = self._calculate_mid(closeout_bid, closeout_ask)

        return Quote(
            provider=self.name,
            instrument=request.instrument,
            timestamp=timestamp,
            bid=bid,
            ask=ask,
            mid=mid,
            last=mid,
            metadata={"provider_instrument": oanda_instrument},
        )

    def _fetch_chunk_with_fallbacks(
        self,
        *,
        instrument: str,
        granularity: str,
        chunk_start: datetime,
        chunk_end: datetime,
    ) -> list[Candle]:
        candles = self._fetch_range(
            instrument=instrument,
            granularity=granularity,
            from_time=chunk_start,
            to_time=chunk_end,
        )
        if candles:
            return self._clip_candles(candles, chunk_start, chunk_end)

        for count in (200, 500, 1000):
            payload = self._request_json(
                path=f"/instruments/{instrument}/candles",
                params={
                    "granularity": granularity,
                    "count": count,
                    "price": "M",
                    "to": self._format_oanda_time(chunk_end),
                },
            )
            fallback_candles = self._parse_candles(payload)
            clipped = self._clip_candles(fallback_candles, chunk_start, chunk_end)
            if clipped:
                return clipped

        for days in (1, 2):
            expanded = self._fetch_range(
                instrument=instrument,
                granularity=granularity,
                from_time=chunk_start - timedelta(days=days),
                to_time=chunk_end + timedelta(days=days),
            )
            clipped = self._clip_candles(expanded, chunk_start, chunk_end)
            if clipped:
                return clipped

        return []

    def _fetch_range(
        self,
        *,
        instrument: str,
        granularity: str,
        from_time: datetime,
        to_time: datetime,
    ) -> list[Candle]:
        payload = self._request_json(
            path=f"/instruments/{instrument}/candles",
            params={
                "from": self._format_oanda_time(from_time),
                "to": self._format_oanda_time(to_time),
                "granularity": granularity,
                "price": "M",
            },
        )
        return self._parse_candles(payload)

    def _request_json(self, *, path: str, params: dict[str, Any]) -> dict[str, Any]:
        url = f"{self._base_url}{path}"

        def operation() -> dict[str, Any]:
            try:
                response = self._session.get(
                    url,
                    headers=self._headers,
                    params=params,
                    timeout=self._config.timeout_seconds,
                )
            except requests.exceptions.RequestException as exc:
                raise _RetryableHttpError(str(exc)) from exc

            if response.status_code == 401:
                body = response.text[:500]
                raise MarketDataAuthError(f"OANDA auth failed: {body}")

            if response.status_code in self._RETRYABLE_STATUS_CODES:
                raise _RetryableHttpError(
                    f"OANDA retryable status={response.status_code}"
                )

            if response.status_code != 200:
                body = response.text[:500]
                raise MarketDataRequestError(
                    f"OANDA request failed status={response.status_code}, body={body}"
                )

            try:
                return response.json()
            except ValueError as exc:
                raise MarketDataRequestError(
                    "OANDA returned non-JSON response"
                ) from exc

        return run_with_retry(
            operation=operation,
            should_retry=lambda exc: isinstance(exc, _RetryableHttpError),
            policy=self._retry_policy,
        )

    @classmethod
    def _to_oanda_instrument(cls, symbol: str) -> str:
        normalized = symbol.strip().upper().replace("-", "/").replace("_", "/")
        if "/" in normalized:
            parts = normalized.split("/")
            if len(parts) == 2 and all(len(part) == 3 and part.isalpha() for part in parts):
                return f"{parts[0]}_{parts[1]}"
        if len(normalized) == 6 and normalized.isalpha():
            return f"{normalized[:3]}_{normalized[3:]}"
        raise UnsupportedInstrumentError(
            f"Unsupported forex symbol format for OANDA: {symbol}"
        )

    @classmethod
    def _parse_candles(cls, payload: dict[str, Any]) -> list[Candle]:
        parsed: list[Candle] = []
        for candle in payload.get("candles", []):
            mid = candle.get("mid")
            if not mid:
                continue
            timestamp = cls._parse_oanda_time(candle.get("time"))
            parsed.append(
                Candle(
                    timestamp=timestamp,
                    open=float(mid["o"]),
                    high=float(mid["h"]),
                    low=float(mid["l"]),
                    close=float(mid["c"]),
                    volume=float(candle.get("volume", 0)),
                )
            )
        return parsed

    @staticmethod
    def _parse_oanda_time(value: str | None) -> datetime:
        if not value:
            return datetime.now(timezone.utc)
        return ensure_utc(datetime.fromisoformat(value.replace("Z", "+00:00")))

    @staticmethod
    def _format_oanda_time(dt: datetime) -> str:
        return ensure_utc(dt).strftime("%Y-%m-%dT%H:%M:%SZ")

    @staticmethod
    def _clip_candles(
        candles: list[Candle], start: datetime, end: datetime
    ) -> list[Candle]:
        clipped = [c for c in candles if start <= c.timestamp <= end]
        return sorted(clipped, key=lambda c: c.timestamp)

    @staticmethod
    def _dedupe_sort_clip(
        candles: list[Candle],
        start: datetime,
        end: datetime,
        limit: int | None,
    ) -> list[Candle]:
        unique_by_ts = {c.timestamp: c for c in candles if start <= c.timestamp <= end}
        ordered = [unique_by_ts[ts] for ts in sorted(unique_by_ts.keys())]
        if limit is not None and limit > 0:
            return ordered[-limit:]
        return ordered

    @classmethod
    def _iter_chunks(
        cls, start: datetime, end: datetime, interval: BarInterval
    ) -> list[tuple[datetime, datetime]]:
        chunk_size = cls._CHUNK_BY_INTERVAL[interval]
        chunks: list[tuple[datetime, datetime]] = []
        cursor = start
        while cursor < end:
            next_end = min(cursor + chunk_size, end)
            chunks.append((cursor, next_end))
            cursor = next_end
        return chunks

    @staticmethod
    def _first_level_price(levels: Any) -> float | None:
        if not levels:
            return None
        first = levels[0]
        if not isinstance(first, dict):
            return None
        return OandaMarketDataProvider._to_float(first.get("price"))

    @staticmethod
    def _to_float(value: Any) -> float | None:
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _calculate_mid(bid: float | None, ask: float | None) -> float | None:
        if bid is None or ask is None:
            return None
        return (bid + ask) / 2.0
