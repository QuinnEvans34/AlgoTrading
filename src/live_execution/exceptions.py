"""Explicit exception types for live-execution boundary guardrails."""

from __future__ import annotations


class LiveExecutionError(RuntimeError):
    """Base class for live-execution boundary failures."""


class LiveExecutionDisabledError(LiveExecutionError):
    """Raised when live execution is disabled by configuration."""


class LiveExecutionNotConfiguredError(LiveExecutionError):
    """Raised when broker configuration is missing."""


class LiveExecutionUnsupportedCapabilityError(LiveExecutionError):
    """Raised when an intent is incompatible with broker capabilities."""


class LiveExecutionAdapterTimeoutError(LiveExecutionError):
    """Raised when an adapter operation times out."""


class LiveExecutionAdapterError(LiveExecutionError):
    """Raised for non-timeout adapter failures."""

