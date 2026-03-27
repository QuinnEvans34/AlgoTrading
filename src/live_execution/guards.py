"""Guard-chain checks for manual live execution."""

from __future__ import annotations

from .contracts import BrokerConnectionStatus
from .requests import ManualLiveOrderRequest
from .results import GuardCheckResult, LiveRejectionCode


def _passed(name: str, message: str) -> GuardCheckResult:
    return GuardCheckResult(name=name, passed=True, code=None, message=message)


def _failed(name: str, code: LiveRejectionCode, message: str) -> GuardCheckResult:
    return GuardCheckResult(
        name=name,
        passed=False,
        code=code.value,
        message=message,
    )


def build_readiness_checks(
    *,
    status: BrokerConnectionStatus,
    submit_feature_enabled: bool,
) -> tuple[GuardCheckResult, ...]:
    checks: list[GuardCheckResult] = []
    checks.append(
        _passed("feature_submit_enabled", "Submit feature flag enabled.")
        if submit_feature_enabled
        else _failed(
            "feature_submit_enabled",
            LiveRejectionCode.FEATURE_SUBMIT_DISABLED,
            "Live submit feature flag is disabled.",
        )
    )
    checks.append(
        _passed("live_execution_enabled", "Live execution is enabled.")
        if status.enabled
        else _failed(
            "live_execution_enabled",
            LiveRejectionCode.LIVE_DISABLED,
            "Live execution is disabled.",
        )
    )
    checks.append(
        _passed("submission_allowed", "Live order submission is allowed.")
        if status.submission_allowed
        else _failed(
            "submission_allowed",
            LiveRejectionCode.SUBMISSION_DISABLED,
            "Live order submission is disabled by safety settings.",
        )
    )
    checks.append(
        _passed("broker_configured", "Broker configuration is present.")
        if status.configured
        else _failed(
            "broker_configured",
            LiveRejectionCode.BROKER_NOT_CONFIGURED,
            status.message,
        )
    )
    checks.append(
        _passed("broker_supports_submit", "Broker adapter supports submission.")
        if status.capabilities.supports_submit
        else _failed(
            "broker_supports_submit",
            LiveRejectionCode.BROKER_SUBMIT_UNSUPPORTED,
            "Broker adapter does not support live submission in this phase.",
        )
    )
    return tuple(checks)


def build_manual_submission_checks(
    *,
    request: ManualLiveOrderRequest,
    status: BrokerConnectionStatus,
    submit_feature_enabled: bool,
    confirmation_phrase: str,
    idempotency_key_seen: bool,
    intent_validation_reasons: tuple[str, ...],
) -> tuple[GuardCheckResult, ...]:
    checks = list(
        build_readiness_checks(
            status=status,
            submit_feature_enabled=submit_feature_enabled,
        )
    )

    checks.append(
        _passed("confirm_live_execution", "Manual confirmation flag is set.")
        if request.confirm_live_execution
        else _failed(
            "confirm_live_execution",
            LiveRejectionCode.CONFIRMATION_REQUIRED,
            "Manual confirmation flag is required for live order submission.",
        )
    )

    checks.append(
        _passed("confirmation_text", "Confirmation phrase matched.")
        if request.confirmation_text == confirmation_phrase
        else _failed(
            "confirmation_text",
            LiveRejectionCode.CONFIRMATION_TEXT_MISMATCH,
            "Confirmation phrase does not match required value.",
        )
    )

    checks.append(
        _failed(
            "idempotency_key",
            LiveRejectionCode.IDEMPOTENCY_DUPLICATE,
            "Idempotency key was already used by a prior attempt.",
        )
        if idempotency_key_seen
        else _passed("idempotency_key", "Idempotency key is unique.")
    )

    checks.append(
        _passed("intent_validation", "Intent passes broker capability checks.")
        if not intent_validation_reasons
        else _failed(
            "intent_validation",
            LiveRejectionCode.INTENT_VALIDATION_FAILED,
            ", ".join(intent_validation_reasons),
        )
    )
    return tuple(checks)


def first_failed_check(
    checks: tuple[GuardCheckResult, ...],
) -> GuardCheckResult | None:
    for check in checks:
        if not check.passed:
            return check
    return None
