"""Demo: guarded manual live execution flow with readiness and attempt logging."""

from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from live_execution import (  # noqa: E402
    LiveExecutionService,
    LiveExecutionSettings,
    LiveOrderSide,
    LiveOrderType,
    LiveTradeIntent,
    ManualLiveOrderRequest,
)
from live_execution.brokers.registry import create_broker_adapter  # noqa: E402
from market_data import AssetClass, Instrument  # noqa: E402


def main() -> None:
    with tempfile.TemporaryDirectory() as tempdir:
        settings = LiveExecutionSettings(
            enabled=False,
            allow_order_submission=False,
            submit_feature_enabled=True,
            status_feature_enabled=True,
            attempt_log_path=str(Path(tempdir) / "attempts.jsonl"),
            confirmation_phrase="EXECUTE LIVE ORDER",
        )
        service = LiveExecutionService(
            settings=settings,
            adapter=create_broker_adapter(settings),
        )

        readiness = service.get_readiness()
        print("Readiness")
        print("---------")
        print(
            f"broker={readiness.broker_name.value} state={readiness.state.value} "
            f"manual_ready={readiness.manual_submission_ready}"
        )
        print("checks:")
        for check in readiness.checks:
            print(f"  - {check.name}: {'PASS' if check.passed else 'FAIL'} ({check.code})")
        print()

        request = ManualLiveOrderRequest(
            intent=LiveTradeIntent(
                instrument=Instrument(symbol="EUR_USD", asset_class=AssetClass.FOREX),
                side=LiveOrderSide.BUY,
                order_type=LiveOrderType.MARKET,
                quantity=1000.0,
            ),
            idempotency_key="demo-idem-1",
            confirm_live_execution=True,
            confirmation_text="EXECUTE LIVE ORDER",
            operator_id="demo-operator",
            operator_note="manual test submit",
        )
        result = service.submit_manual_order(request)
        print("Manual Submit Result")
        print("--------------------")
        print(
            f"accepted={result.accepted} status={result.status} "
            f"rejection_code={result.rejection_code}"
        )
        print(f"rejection_message={result.rejection_message}")
        print()

        attempts = service.list_recent_attempts(limit=5)
        print("Recent Attempts")
        print("---------------")
        for attempt in attempts:
            print(
                f"{attempt.attempt_id} accepted={attempt.accepted} "
                f"rejection={attempt.rejection_code}"
            )


if __name__ == "__main__":
    main()
