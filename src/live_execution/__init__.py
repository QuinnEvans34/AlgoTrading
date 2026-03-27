"""Live-execution boundary contracts and broker adapter interfaces."""

from .config import LiveExecutionSettings
from .contracts import (
    BrokerCapabilities,
    BrokerConnectionStatus,
    IntentValidationResult,
    LiveAccountSnapshot,
    LiveBalanceSnapshot,
    LiveBrokerName,
    LiveConnectionState,
    LiveFillSnapshot,
    LiveOrderSide,
    LiveOrderSnapshot,
    LiveOrderType,
    LivePositionSnapshot,
    LiveSubmitResult,
    LiveTradeIntent,
)
from .exceptions import (
    LiveExecutionAdapterError,
    LiveExecutionAdapterTimeoutError,
    LiveExecutionDisabledError,
    LiveExecutionError,
    LiveExecutionNotConfiguredError,
    LiveExecutionUnsupportedCapabilityError,
)
from .requests import ManualLiveOrderRequest
from .results import (
    GuardCheckResult,
    LiveExecutionAttemptRecord,
    LiveReadinessSnapshot,
    LiveRejectionCode,
    ManualLiveSubmitResult,
)
from .service import LiveExecutionService

__all__ = [
    "LiveExecutionSettings",
    "LiveBrokerName",
    "LiveOrderType",
    "LiveOrderSide",
    "LiveConnectionState",
    "BrokerCapabilities",
    "BrokerConnectionStatus",
    "LiveTradeIntent",
    "IntentValidationResult",
    "LiveSubmitResult",
    "LiveBalanceSnapshot",
    "LivePositionSnapshot",
    "LiveOrderSnapshot",
    "LiveFillSnapshot",
    "LiveAccountSnapshot",
    "LiveExecutionError",
    "LiveExecutionDisabledError",
    "LiveExecutionNotConfiguredError",
    "LiveExecutionUnsupportedCapabilityError",
    "LiveExecutionAdapterTimeoutError",
    "LiveExecutionAdapterError",
    "LiveRejectionCode",
    "GuardCheckResult",
    "LiveReadinessSnapshot",
    "ManualLiveOrderRequest",
    "ManualLiveSubmitResult",
    "LiveExecutionAttemptRecord",
    "LiveExecutionService",
]
