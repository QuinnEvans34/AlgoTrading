"""Market-data preview API orchestration."""

from __future__ import annotations

from market_data import (
    HistoricalCandleRequest,
    MarketDataAuthError,
    MarketDataRequestError,
    MarketDataService,
    UnsupportedInstrumentError,
)

from ..errors import APIError
from ..schemas import MarketDataPreviewRequestSchema, MarketDataPreviewResponseSchema
from ..serializers import serialize_market_data_preview
from .common import to_instrument


class MarketDataAPIService:
    def __init__(self, *, market_data_service: MarketDataService) -> None:
        self._market_data_service = market_data_service

    def preview_historical_data(
        self,
        request: MarketDataPreviewRequestSchema,
    ) -> MarketDataPreviewResponseSchema:
        try:
            response = self._market_data_service.fetch_historical_candles(
                provider_name=request.provider_name,
                request=HistoricalCandleRequest(
                    instrument=to_instrument(request.instrument),
                    interval=request.interval,
                    start=request.start,
                    end=request.end,
                    limit=request.limit,
                ),
            )
            return serialize_market_data_preview(response)
        except KeyError as exc:
            raise APIError(
                status_code=404,
                code="provider_not_found",
                message=f"Provider '{request.provider_name}' is not registered",
            ) from exc
        except UnsupportedInstrumentError as exc:
            raise APIError(
                status_code=400,
                code="unsupported_instrument",
                message=str(exc),
            ) from exc
        except MarketDataAuthError as exc:
            raise APIError(
                status_code=502,
                code="provider_auth_error",
                message=str(exc),
            ) from exc
        except MarketDataRequestError as exc:
            raise APIError(
                status_code=502,
                code="provider_request_error",
                message=str(exc),
            ) from exc
