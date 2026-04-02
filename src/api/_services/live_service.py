"""Live-execution boundary API orchestration."""

from __future__ import annotations

from config import AppSettings
from live_execution import LiveExecutionService, ManualLiveOrderRequest

from ..errors import APIError
from ..live_execution_schemas import (
    LiveExecutionAttemptsResponseSchema,
    LiveExecutionReadinessResponseSchema,
    LiveExecutionStatusResponseSchema,
    LiveIntentValidationResponseSchema,
    LiveSubmitResponseSchema,
    LiveTradeIntentSchema,
    ManualLiveOrderRequestSchema,
    ManualLiveSubmitResponseSchema,
)
from .common import (
    ensure_feature_enabled,
    guard_check_payload,
    status_payload,
    to_live_trade_intent,
)


class LiveAPIService:
    def __init__(
        self,
        *,
        app_settings: AppSettings,
        live_execution_service: LiveExecutionService,
    ) -> None:
        self._app_settings = app_settings
        self._live_execution_service = live_execution_service

    def get_live_execution_status(self) -> LiveExecutionStatusResponseSchema:
        ensure_feature_enabled(
            self._app_settings,
            "live_execution_status_enabled",
            code="live_execution_status_disabled",
            message="Live execution status endpoints are disabled by feature flag.",
        )
        status = self._live_execution_service.get_status()
        return LiveExecutionStatusResponseSchema.model_validate(status_payload(status))

    def get_live_execution_readiness(self) -> LiveExecutionReadinessResponseSchema:
        ensure_feature_enabled(
            self._app_settings,
            "live_execution_status_enabled",
            code="live_execution_status_disabled",
            message="Live execution status endpoints are disabled by feature flag.",
        )
        snapshot = self._live_execution_service.get_readiness()
        return LiveExecutionReadinessResponseSchema.model_validate(
            {
                "generated_at": snapshot.generated_at,
                "broker_name": snapshot.broker_name.value,
                "enabled": snapshot.enabled,
                "submission_allowed": snapshot.submission_allowed,
                "configured": snapshot.configured,
                "state": snapshot.state.value,
                "message": snapshot.message,
                "manual_submission_ready": snapshot.manual_submission_ready,
                "confirmation_phrase": snapshot.confirmation_phrase,
                "checks": [guard_check_payload(check) for check in snapshot.checks],
            }
        )

    def validate_live_intent(
        self,
        request: LiveTradeIntentSchema,
    ) -> LiveIntentValidationResponseSchema:
        ensure_feature_enabled(
            self._app_settings,
            "live_execution_status_enabled",
            code="live_execution_status_disabled",
            message="Live execution status endpoints are disabled by feature flag.",
        )
        intent = to_live_trade_intent(request)
        result = self._live_execution_service.validate_intent(intent)
        normalized = result.normalized_intent
        normalized_payload = None
        if normalized is not None:
            normalized_payload = {
                "instrument": {
                    "symbol": normalized.instrument.symbol,
                    "asset_class": normalized.instrument.asset_class.value,
                    "venue": normalized.instrument.venue,
                    "quote_currency": normalized.instrument.quote_currency,
                },
                "side": normalized.side.value,
                "order_type": normalized.order_type.value,
                "quantity": normalized.quantity,
                "limit_price": normalized.limit_price,
                "client_order_id": normalized.client_order_id,
                "metadata": dict(normalized.metadata),
            }
        return LiveIntentValidationResponseSchema.model_validate(
            {
                "accepted": result.accepted,
                "reasons": list(result.reasons),
                "normalized_intent": normalized_payload,
                "broker_payload_preview": (
                    None
                    if result.broker_payload_preview is None
                    else dict(result.broker_payload_preview)
                ),
            }
        )

    def submit_live_intent(
        self,
        request: LiveTradeIntentSchema,
    ) -> LiveSubmitResponseSchema:
        del request
        ensure_feature_enabled(
            self._app_settings,
            "live_execution_status_enabled",
            code="live_execution_status_disabled",
            message="Live execution status endpoints are disabled by feature flag.",
        )
        ensure_feature_enabled(
            self._app_settings,
            "live_execution_submit_enabled",
            code="live_execution_submit_disabled",
            message="Live execution submit endpoint is disabled by feature flag.",
        )
        raise APIError(
            status_code=409,
            code="live_execution_manual_required",
            message=(
                "Deprecated endpoint. Use /live-execution/manual-orders "
                "with manual confirmation fields."
            ),
        )

    def submit_manual_live_order(
        self,
        request: ManualLiveOrderRequestSchema,
    ) -> ManualLiveSubmitResponseSchema:
        ensure_feature_enabled(
            self._app_settings,
            "live_execution_status_enabled",
            code="live_execution_status_disabled",
            message="Live execution status endpoints are disabled by feature flag.",
        )
        ensure_feature_enabled(
            self._app_settings,
            "live_execution_submit_enabled",
            code="live_execution_submit_disabled",
            message="Live execution submit endpoint is disabled by feature flag.",
        )
        domain_request = ManualLiveOrderRequest(
            intent=to_live_trade_intent(request.intent),
            idempotency_key=request.idempotency_key,
            confirm_live_execution=request.confirm_live_execution,
            confirmation_text=request.confirmation_text,
            operator_id=request.operator_id,
            operator_note=request.operator_note,
        )
        result = self._live_execution_service.submit_manual_order(domain_request)
        return ManualLiveSubmitResponseSchema.model_validate(
            {
                "accepted": result.accepted,
                "status": result.status,
                "attempt_id": result.attempt_id,
                "broker_name": result.broker_name.value,
                "rejection_code": result.rejection_code,
                "rejection_message": result.rejection_message,
                "external_order_id": result.external_order_id,
                "broker_payload": (
                    None if result.broker_payload is None else dict(result.broker_payload)
                ),
                "guard_checks": [guard_check_payload(check) for check in result.guard_checks],
            }
        )

    def list_live_execution_attempts(
        self,
        limit: int = 25,
    ) -> LiveExecutionAttemptsResponseSchema:
        ensure_feature_enabled(
            self._app_settings,
            "live_execution_status_enabled",
            code="live_execution_status_disabled",
            message="Live execution status endpoints are disabled by feature flag.",
        )
        attempts = self._live_execution_service.list_recent_attempts(limit=limit)
        return LiveExecutionAttemptsResponseSchema.model_validate(
            {
                "attempts": [
                    {
                        "attempt_id": attempt.attempt_id,
                        "timestamp": attempt.timestamp,
                        "broker_name": attempt.broker_name.value,
                        "idempotency_key": attempt.idempotency_key,
                        "request_summary": dict(attempt.request_summary),
                        "guard_checks": [
                            guard_check_payload(check) for check in attempt.guard_checks
                        ],
                        "accepted": attempt.accepted,
                        "status": attempt.status,
                        "rejection_code": attempt.rejection_code,
                        "rejection_message": attempt.rejection_message,
                        "external_order_id": attempt.external_order_id,
                    }
                    for attempt in attempts
                ]
            }
        )
