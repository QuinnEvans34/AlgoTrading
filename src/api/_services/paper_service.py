"""Paper-trading API orchestration."""

from __future__ import annotations

from datetime import datetime, timezone

from config import AppSettings
from paper_trading import (
    PaperAccountConfig,
    PaperOrderRequest,
    PaperOrderSide,
    PaperOrderType,
    PaperSignalDirection,
    PaperSignalIntent,
    PaperTradingService,
    PriceUpdate,
)

from ..config import APISettings
from ..errors import APIError
from ..paper_trading_schemas import (
    PaperCancelActionResponseSchema,
    PaperOrderActionResponseSchema,
    PaperOrderRequestSchema,
    PaperPriceUpdateResponseSchema,
    PaperResetRequestSchema,
    PaperSignalIntentRequestSchema,
    PaperStateResponseSchema,
    PriceUpdateRequestSchema,
)
from ..serializers import (
    serialize_paper_cancel_action,
    serialize_paper_order_action,
    serialize_paper_price_update,
    serialize_paper_state,
)
from .common import ensure_feature_enabled, to_instrument


class PaperAPIService:
    def __init__(
        self,
        *,
        settings: APISettings,
        app_settings: AppSettings,
        paper_trading_service: PaperTradingService,
    ) -> None:
        self._settings = settings
        self._app_settings = app_settings
        self._paper_trading_service = paper_trading_service

    def get_paper_state(self, *, fills_limit: int = 100) -> PaperStateResponseSchema:
        ensure_feature_enabled(
            self._app_settings,
            "paper_trading_enabled",
            code="paper_trading_disabled",
            message="Paper trading endpoints are disabled by feature flag.",
        )
        snapshot = self._paper_trading_service.get_state(fills_limit=fills_limit)
        return serialize_paper_state(snapshot)

    def place_paper_order(
        self,
        request: PaperOrderRequestSchema,
    ) -> PaperOrderActionResponseSchema:
        ensure_feature_enabled(
            self._app_settings,
            "paper_trading_enabled",
            code="paper_trading_disabled",
            message="Paper trading endpoints are disabled by feature flag.",
        )
        try:
            result = self._paper_trading_service.place_order(
                PaperOrderRequest(
                    instrument=to_instrument(request.instrument),
                    side=PaperOrderSide(request.side),
                    order_type=PaperOrderType(request.order_type),
                    quantity=request.quantity,
                    limit_price=request.limit_price,
                    reference_price=request.reference_price,
                    client_order_id=request.client_order_id,
                    metadata=dict(request.metadata),
                )
            )
            return serialize_paper_order_action(result)
        except ValueError as exc:
            raise APIError(
                status_code=400,
                code="paper_order_invalid",
                message=str(exc),
            ) from exc

    def cancel_paper_order(self, order_id: str) -> PaperCancelActionResponseSchema:
        ensure_feature_enabled(
            self._app_settings,
            "paper_trading_enabled",
            code="paper_trading_disabled",
            message="Paper trading endpoints are disabled by feature flag.",
        )
        try:
            result = self._paper_trading_service.cancel_order(order_id)
            return serialize_paper_cancel_action(result)
        except KeyError as exc:
            raise APIError(
                status_code=404,
                code="paper_order_not_found",
                message=str(exc),
            ) from exc
        except ValueError as exc:
            raise APIError(
                status_code=400,
                code="paper_order_cancel_invalid",
                message=str(exc),
            ) from exc

    def process_paper_price_update(
        self,
        request: PriceUpdateRequestSchema,
    ) -> PaperPriceUpdateResponseSchema:
        ensure_feature_enabled(
            self._app_settings,
            "paper_trading_enabled",
            code="paper_trading_disabled",
            message="Paper trading endpoints are disabled by feature flag.",
        )
        try:
            result = self._paper_trading_service.process_price_update(
                PriceUpdate(
                    instrument=to_instrument(request.instrument),
                    price=request.price,
                    timestamp=(
                        datetime.now(timezone.utc)
                        if request.timestamp is None
                        else request.timestamp
                    ),
                    source=request.source,
                )
            )
            return serialize_paper_price_update(result)
        except ValueError as exc:
            raise APIError(
                status_code=400,
                code="paper_price_invalid",
                message=str(exc),
            ) from exc

    def submit_paper_signal_intent(
        self,
        request: PaperSignalIntentRequestSchema,
    ) -> PaperOrderActionResponseSchema:
        ensure_feature_enabled(
            self._app_settings,
            "paper_trading_enabled",
            code="paper_trading_disabled",
            message="Paper trading endpoints are disabled by feature flag.",
        )
        try:
            result = self._paper_trading_service.submit_signal_intent(
                PaperSignalIntent(
                    instrument=to_instrument(request.instrument),
                    direction=PaperSignalDirection(request.direction),
                    quantity=request.quantity,
                    reference_price=request.reference_price,
                    client_order_id=request.client_order_id,
                    metadata=dict(request.metadata),
                )
            )
            return serialize_paper_order_action(result)
        except ValueError as exc:
            raise APIError(
                status_code=400,
                code="paper_signal_invalid",
                message=str(exc),
            ) from exc

    def reset_paper_account(
        self,
        request: PaperResetRequestSchema,
    ) -> PaperStateResponseSchema:
        ensure_feature_enabled(
            self._app_settings,
            "paper_trading_enabled",
            code="paper_trading_disabled",
            message="Paper trading endpoints are disabled by feature flag.",
        )
        config = PaperAccountConfig(
            account_id=request.account_id or self._settings.paper_default_account_id,
            base_currency=request.base_currency or self._settings.paper_default_base_currency,
            initial_cash=(
                self._settings.paper_default_initial_cash
                if request.initial_cash is None
                else request.initial_cash
            ),
            allow_short=(
                self._settings.paper_default_allow_short
                if request.allow_short is None
                else request.allow_short
            ),
            default_spread_bps=(
                self._settings.paper_default_spread_bps
                if request.default_spread_bps is None
                else request.default_spread_bps
            ),
            default_slippage_bps=(
                self._settings.paper_default_slippage_bps
                if request.default_slippage_bps is None
                else request.default_slippage_bps
            ),
            commission_bps=(
                self._settings.paper_default_commission_bps
                if request.commission_bps is None
                else request.commission_bps
            ),
            commission_fixed=(
                self._settings.paper_default_commission_fixed
                if request.commission_fixed is None
                else request.commission_fixed
            ),
        )
        snapshot = self._paper_trading_service.reset_account(config=config)
        return serialize_paper_state(snapshot)
