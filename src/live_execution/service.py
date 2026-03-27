"""Service boundary for broker-agnostic live execution."""

from __future__ import annotations

from pathlib import Path

from .attempt_log import LiveExecutionAttemptLog, generate_attempt_id
from .brokers.base import LiveBrokerAdapter
from .config import LiveExecutionSettings
from .contracts import (
    BrokerConnectionStatus,
    IntentValidationResult,
    LiveConnectionState,
    LiveSubmitResult,
    LiveTradeIntent,
)
from .exceptions import (
    LiveExecutionAdapterError,
    LiveExecutionAdapterTimeoutError,
    LiveExecutionDisabledError,
    LiveExecutionNotConfiguredError,
    LiveExecutionUnsupportedCapabilityError,
)
from .guards import build_manual_submission_checks, first_failed_check
from .readiness import build_readiness_snapshot
from .requests import ManualLiveOrderRequest
from .results import (
    GuardCheckResult,
    LiveExecutionAttemptRecord,
    LiveReadinessSnapshot,
    LiveRejectionCode,
    ManualLiveSubmitResult,
    utcnow,
)
from .validation import build_validation_result, summarize_validation_reasons


class LiveExecutionService:
    def __init__(
        self,
        *,
        settings: LiveExecutionSettings,
        adapter: LiveBrokerAdapter,
        attempt_log: LiveExecutionAttemptLog | None = None,
    ) -> None:
        self._settings = settings
        self._adapter = adapter
        self._attempt_log = attempt_log or LiveExecutionAttemptLog(
            Path(settings.attempt_log_path)
        )

    def get_status(self) -> BrokerConnectionStatus:
        configured = self._adapter.is_configured()
        if not self._settings.enabled:
            return BrokerConnectionStatus(
                broker_name=self._adapter.broker_name,
                enabled=False,
                submission_allowed=self._settings.allow_order_submission,
                configured=configured,
                state=LiveConnectionState.DISABLED,
                message="Live execution is disabled (LIVE_EXECUTION_ENABLED=false).",
                capabilities=self._adapter.capabilities,
            )
        if not configured:
            return BrokerConnectionStatus(
                broker_name=self._adapter.broker_name,
                enabled=True,
                submission_allowed=self._settings.allow_order_submission,
                configured=False,
                state=LiveConnectionState.NOT_CONFIGURED,
                message=self._adapter.configuration_message(),
                capabilities=self._adapter.capabilities,
            )
        if not self._settings.allow_order_submission:
            return BrokerConnectionStatus(
                broker_name=self._adapter.broker_name,
                enabled=True,
                submission_allowed=False,
                configured=True,
                state=LiveConnectionState.READY,
                message=(
                    "Broker configured. Submission remains blocked "
                    "(LIVE_EXECUTION_ALLOW_ORDER_SUBMISSION=false)."
                ),
                capabilities=self._adapter.capabilities,
            )
        return BrokerConnectionStatus(
            broker_name=self._adapter.broker_name,
            enabled=True,
            submission_allowed=True,
            configured=True,
            state=LiveConnectionState.READY,
            message="Live execution boundary is configured.",
                capabilities=self._adapter.capabilities,
            )

    def validate_intent(self, intent: LiveTradeIntent) -> IntentValidationResult:
        extra_reasons: list[str] = []
        if not self._settings.enabled:
            extra_reasons.append("live_execution_disabled")
        if not self._adapter.is_configured():
            extra_reasons.append("broker_not_configured")
        payload_preview = self._adapter.map_intent_to_payload(intent)
        return build_validation_result(
            intent=intent,
            capabilities=self._adapter.capabilities,
            broker_payload_preview=payload_preview,
            extra_reasons=tuple(extra_reasons),
        )

    def get_readiness(self) -> LiveReadinessSnapshot:
        status = self.get_status()
        return build_readiness_snapshot(
            status=status,
            submit_feature_enabled=self._settings.submit_feature_enabled,
            confirmation_phrase=self._settings.confirmation_phrase,
        )

    def list_recent_attempts(self, *, limit: int = 50) -> tuple[LiveExecutionAttemptRecord, ...]:
        return self._attempt_log.list_recent(limit=limit)

    def submit_manual_order(
        self,
        request: ManualLiveOrderRequest,
    ) -> ManualLiveSubmitResult:
        normalized_request = request.normalized()
        status = self.get_status()
        validation = self.validate_intent(normalized_request.intent)
        checks = build_manual_submission_checks(
            request=normalized_request,
            status=status,
            submit_feature_enabled=self._settings.submit_feature_enabled,
            confirmation_phrase=self._settings.confirmation_phrase,
            idempotency_key_seen=self._attempt_log.has_idempotency_key(
                normalized_request.idempotency_key
            ),
            intent_validation_reasons=validation.reasons,
        )

        attempt_id = generate_attempt_id()
        first_failure = first_failed_check(checks)
        if first_failure is not None:
            result = ManualLiveSubmitResult(
                accepted=False,
                status="rejected",
                attempt_id=attempt_id,
                broker_name=self._adapter.broker_name,
                rejection_code=first_failure.code,
                rejection_message=first_failure.message,
                guard_checks=checks,
            )
            self._append_attempt_record(
                request=normalized_request,
                result=result,
                checks=checks,
            )
            return result

        normalized_intent = validation.normalized_intent or normalized_request.intent
        try:
            adapter_result = self._submit_normalized_intent(normalized_intent)
        except LiveExecutionDisabledError as exc:
            result = ManualLiveSubmitResult(
                accepted=False,
                status="rejected",
                attempt_id=attempt_id,
                broker_name=self._adapter.broker_name,
                rejection_code=LiveRejectionCode.LIVE_DISABLED.value,
                rejection_message=str(exc),
                guard_checks=checks,
            )
            self._append_attempt_record(
                request=normalized_request,
                result=result,
                checks=checks,
            )
            return result
        except LiveExecutionNotConfiguredError as exc:
            result = ManualLiveSubmitResult(
                accepted=False,
                status="rejected",
                attempt_id=attempt_id,
                broker_name=self._adapter.broker_name,
                rejection_code=LiveRejectionCode.BROKER_NOT_CONFIGURED.value,
                rejection_message=str(exc),
                guard_checks=checks,
            )
            self._append_attempt_record(
                request=normalized_request,
                result=result,
                checks=checks,
            )
            return result
        except LiveExecutionUnsupportedCapabilityError as exc:
            result = ManualLiveSubmitResult(
                accepted=False,
                status="rejected",
                attempt_id=attempt_id,
                broker_name=self._adapter.broker_name,
                rejection_code=LiveRejectionCode.SUBMIT_REJECTED.value,
                rejection_message=str(exc),
                guard_checks=checks,
            )
            self._append_attempt_record(
                request=normalized_request,
                result=result,
                checks=checks,
            )
            return result
        except LiveExecutionAdapterTimeoutError as exc:
            result = ManualLiveSubmitResult(
                accepted=False,
                status="rejected",
                attempt_id=attempt_id,
                broker_name=self._adapter.broker_name,
                rejection_code=LiveRejectionCode.ADAPTER_TIMEOUT.value,
                rejection_message=str(exc),
                guard_checks=checks,
            )
            self._append_attempt_record(
                request=normalized_request,
                result=result,
                checks=checks,
            )
            return result
        except LiveExecutionAdapterError as exc:
            result = ManualLiveSubmitResult(
                accepted=False,
                status="rejected",
                attempt_id=attempt_id,
                broker_name=self._adapter.broker_name,
                rejection_code=LiveRejectionCode.ADAPTER_ERROR.value,
                rejection_message=str(exc),
                guard_checks=checks,
            )
            self._append_attempt_record(
                request=normalized_request,
                result=result,
                checks=checks,
            )
            return result

        result = ManualLiveSubmitResult(
            accepted=adapter_result.accepted,
            status=adapter_result.status,
            attempt_id=attempt_id,
            broker_name=self._adapter.broker_name,
            rejection_code=(
                None
                if adapter_result.accepted
                else LiveRejectionCode.SUBMIT_REJECTED.value
            ),
            rejection_message=adapter_result.reason,
            external_order_id=adapter_result.external_order_id,
            broker_payload=adapter_result.broker_payload,
            guard_checks=checks,
        )
        self._append_attempt_record(
            request=normalized_request,
            result=result,
            checks=checks,
        )
        return result

    def submit_intent(self, intent: LiveTradeIntent) -> LiveSubmitResult:
        if not self._settings.enabled:
            raise LiveExecutionDisabledError(
                "Submit rejected: live execution is disabled."
            )
        if not self._settings.allow_order_submission:
            raise LiveExecutionDisabledError(
                "Submit rejected: live order submission is disabled."
            )
        if not self._adapter.is_configured():
            raise LiveExecutionNotConfiguredError(self._adapter.configuration_message())

        validation = self.validate_intent(intent)
        if not validation.accepted:
            raise LiveExecutionUnsupportedCapabilityError(
                "Intent failed validation: "
                + summarize_validation_reasons(validation.reasons)
            )
        normalized = validation.normalized_intent
        if normalized is None:
            raise LiveExecutionAdapterError("Normalized intent was unexpectedly empty.")
        return self._submit_normalized_intent(normalized)

    def _submit_normalized_intent(self, intent: LiveTradeIntent) -> LiveSubmitResult:
        try:
            return self._adapter.submit_intent(intent)
        except TimeoutError as exc:
            raise LiveExecutionAdapterTimeoutError(
                f"Broker adapter timeout ({self._adapter.broker_name.value})."
            ) from exc
        except (
            LiveExecutionDisabledError,
            LiveExecutionNotConfiguredError,
            LiveExecutionUnsupportedCapabilityError,
            LiveExecutionAdapterTimeoutError,
            LiveExecutionAdapterError,
        ):
            raise
        except Exception as exc:  # pragma: no cover - defensive guardrail
            raise LiveExecutionAdapterError(
                f"Broker adapter failure ({self._adapter.broker_name.value})."
            ) from exc

    def _append_attempt_record(
        self,
        *,
        request: ManualLiveOrderRequest,
        result: ManualLiveSubmitResult,
        checks: tuple[GuardCheckResult, ...],
    ) -> None:
        summary = {
            "symbol": request.intent.instrument.symbol,
            "asset_class": request.intent.instrument.asset_class.value,
            "side": request.intent.side.value,
            "order_type": request.intent.order_type.value,
            "quantity": request.intent.quantity,
            "limit_price": request.intent.limit_price,
            "client_order_id": request.intent.client_order_id,
            "operator_id": request.operator_id,
            "operator_note_present": request.operator_note is not None,
            "confirmation_flag": request.confirm_live_execution,
        }
        record = LiveExecutionAttemptRecord(
            attempt_id=result.attempt_id,
            timestamp=utcnow(),
            broker_name=result.broker_name,
            idempotency_key=request.idempotency_key,
            request_summary=summary,
            guard_checks=tuple(checks),
            accepted=result.accepted,
            status=result.status,
            rejection_code=result.rejection_code,
            rejection_message=result.rejection_message,
            external_order_id=result.external_order_id,
        )
        self._attempt_log.append(record)
