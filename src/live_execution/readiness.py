"""Readiness snapshot helpers for guarded manual live execution."""

from __future__ import annotations

from .contracts import BrokerConnectionStatus
from .guards import build_readiness_checks
from .results import LiveReadinessSnapshot, utcnow


def build_readiness_snapshot(
    *,
    status: BrokerConnectionStatus,
    submit_feature_enabled: bool,
    confirmation_phrase: str,
) -> LiveReadinessSnapshot:
    checks = build_readiness_checks(
        status=status,
        submit_feature_enabled=submit_feature_enabled,
    )
    return LiveReadinessSnapshot(
        generated_at=utcnow(),
        broker_name=status.broker_name,
        enabled=status.enabled,
        submission_allowed=status.submission_allowed,
        configured=status.configured,
        state=status.state,
        message=status.message,
        manual_submission_ready=all(check.passed for check in checks),
        confirmation_phrase=confirmation_phrase,
        checks=checks,
    )
