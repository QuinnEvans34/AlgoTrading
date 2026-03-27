import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from live_execution.attempt_log import LiveExecutionAttemptLog  # noqa: E402
from live_execution.contracts import LiveBrokerName  # noqa: E402
from live_execution.results import GuardCheckResult, LiveExecutionAttemptRecord, utcnow  # noqa: E402


class LiveExecutionAttemptLogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.path = Path(self.tempdir.name) / "live" / "attempts.jsonl"
        self.log = LiveExecutionAttemptLog(self.path)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _record(self, *, attempt_id: str, idempotency_key: str, accepted: bool):
        return LiveExecutionAttemptRecord(
            attempt_id=attempt_id,
            timestamp=utcnow(),
            broker_name=LiveBrokerName.NULL,
            idempotency_key=idempotency_key,
            request_summary={"symbol": "EUR_USD", "operator_note_present": False},
            guard_checks=(
                GuardCheckResult(
                    name="confirm_live_execution",
                    passed=accepted,
                    code=None if accepted else "manual_confirmation_required",
                    message="test",
                ),
            ),
            accepted=accepted,
            status="accepted" if accepted else "rejected",
            rejection_code=None if accepted else "manual_confirmation_required",
            rejection_message=None if accepted else "failed",
            external_order_id=None,
        )

    def test_append_and_list_recent(self) -> None:
        first = self._record(attempt_id="a1", idempotency_key="k1", accepted=False)
        second = self._record(attempt_id="a2", idempotency_key="k2", accepted=True)
        self.log.append(first)
        self.log.append(second)

        recent = self.log.list_recent(limit=10)
        self.assertEqual(len(recent), 2)
        self.assertEqual(recent[0].attempt_id, "a2")
        self.assertEqual(recent[1].attempt_id, "a1")
        self.assertEqual(recent[0].request_summary["symbol"], "EUR_USD")

    def test_has_idempotency_key(self) -> None:
        self.log.append(self._record(attempt_id="a1", idempotency_key="abc", accepted=False))
        self.assertTrue(self.log.has_idempotency_key("abc"))
        self.assertFalse(self.log.has_idempotency_key("xyz"))


if __name__ == "__main__":
    unittest.main()
