"""Shared retry/backoff helpers for provider adapters."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Callable, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    initial_backoff_seconds: float = 1.0
    backoff_multiplier: float = 2.0


def run_with_retry(
    operation: Callable[[], T],
    should_retry: Callable[[Exception], bool],
    policy: RetryPolicy | None = None,
) -> T:
    """Run an operation with retry/backoff based on caller-defined policy."""
    retry_policy = policy or RetryPolicy()
    attempts = 0
    delay = retry_policy.initial_backoff_seconds

    while True:
        attempts += 1
        try:
            return operation()
        except Exception as exc:  # noqa: BLE001 - delegate to should_retry
            if attempts >= retry_policy.max_attempts or not should_retry(exc):
                raise
            time.sleep(delay)
            delay *= retry_policy.backoff_multiplier
