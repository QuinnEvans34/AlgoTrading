"""Result contracts for guarded manual live execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping

from .contracts import LiveBrokerName, LiveConnectionState


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class LiveRejectionCode(str, Enum):
    FEATURE_SUBMIT_DISABLED = "feature_submit_disabled"
    LIVE_DISABLED = "live_execution_disabled"
    SUBMISSION_DISABLED = "live_submission_disabled"
    BROKER_NOT_CONFIGURED = "broker_not_configured"
    BROKER_SUBMIT_UNSUPPORTED = "broker_submit_unsupported"
    CONFIRMATION_REQUIRED = "manual_confirmation_required"
    CONFIRMATION_TEXT_MISMATCH = "confirmation_text_mismatch"
    IDEMPOTENCY_DUPLICATE = "idempotency_key_duplicate"
    INTENT_VALIDATION_FAILED = "intent_validation_failed"
    ADAPTER_TIMEOUT = "adapter_timeout"
    ADAPTER_ERROR = "adapter_error"
    SUBMIT_REJECTED = "submit_rejected"


@dataclass(frozen=True)
class GuardCheckResult:
    name: str
    passed: bool
    code: str | None = None
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "code": self.code,
            "message": self.message,
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "GuardCheckResult":
        return GuardCheckResult(
            name=str(payload.get("name", "unknown")),
            passed=bool(payload.get("passed", False)),
            code=None if payload.get("code") is None else str(payload.get("code")),
            message=str(payload.get("message", "")),
        )


@dataclass(frozen=True)
class LiveReadinessSnapshot:
    generated_at: datetime
    broker_name: LiveBrokerName
    enabled: bool
    submission_allowed: bool
    configured: bool
    state: LiveConnectionState
    message: str
    manual_submission_ready: bool
    confirmation_phrase: str
    checks: tuple[GuardCheckResult, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ManualLiveSubmitResult:
    accepted: bool
    status: str
    attempt_id: str
    broker_name: LiveBrokerName
    rejection_code: str | None = None
    rejection_message: str | None = None
    external_order_id: str | None = None
    broker_payload: Mapping[str, Any] | None = None
    guard_checks: tuple[GuardCheckResult, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class LiveExecutionAttemptRecord:
    attempt_id: str
    timestamp: datetime
    broker_name: LiveBrokerName
    idempotency_key: str
    request_summary: Mapping[str, Any]
    guard_checks: tuple[GuardCheckResult, ...]
    accepted: bool
    status: str
    rejection_code: str | None = None
    rejection_message: str | None = None
    external_order_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempt_id": self.attempt_id,
            "timestamp": self.timestamp.isoformat(),
            "broker_name": self.broker_name.value,
            "idempotency_key": self.idempotency_key,
            "request_summary": dict(self.request_summary),
            "guard_checks": [check.to_dict() for check in self.guard_checks],
            "accepted": self.accepted,
            "status": self.status,
            "rejection_code": self.rejection_code,
            "rejection_message": self.rejection_message,
            "external_order_id": self.external_order_id,
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "LiveExecutionAttemptRecord":
        raw_timestamp = payload.get("timestamp")
        parsed_timestamp = utcnow()
        if isinstance(raw_timestamp, str):
            try:
                parsed_timestamp = datetime.fromisoformat(raw_timestamp)
            except ValueError:
                parsed_timestamp = utcnow()

        raw_broker_name = payload.get("broker_name")
        broker_name = LiveBrokerName.NULL
        if isinstance(raw_broker_name, str):
            try:
                broker_name = LiveBrokerName(raw_broker_name)
            except ValueError:
                broker_name = LiveBrokerName.NULL

        raw_checks = payload.get("guard_checks", [])
        checks: list[GuardCheckResult] = []
        if isinstance(raw_checks, list):
            for item in raw_checks:
                if isinstance(item, Mapping):
                    checks.append(GuardCheckResult.from_dict(item))

        raw_summary = payload.get("request_summary", {})
        request_summary: Mapping[str, Any] = (
            dict(raw_summary) if isinstance(raw_summary, Mapping) else {}
        )

        return LiveExecutionAttemptRecord(
            attempt_id=str(payload.get("attempt_id", "")),
            timestamp=parsed_timestamp,
            broker_name=broker_name,
            idempotency_key=str(payload.get("idempotency_key", "")),
            request_summary=request_summary,
            guard_checks=tuple(checks),
            accepted=bool(payload.get("accepted", False)),
            status=str(payload.get("status", "unknown")),
            rejection_code=(
                None
                if payload.get("rejection_code") is None
                else str(payload.get("rejection_code"))
            ),
            rejection_message=(
                None
                if payload.get("rejection_message") is None
                else str(payload.get("rejection_message"))
            ),
            external_order_id=(
                None
                if payload.get("external_order_id") is None
                else str(payload.get("external_order_id"))
            ),
        )
