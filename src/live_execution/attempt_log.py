"""Local attempt logging for manual live execution operations."""

from __future__ import annotations

import json
from pathlib import Path
import uuid

from .results import LiveExecutionAttemptRecord


def generate_attempt_id() -> str:
    return f"live-attempt-{uuid.uuid4().hex[:12]}"


class LiveExecutionAttemptLog:
    def __init__(self, path: Path) -> None:
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    def append(self, record: LiveExecutionAttemptRecord) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        previous = ""
        if self._path.exists():
            previous = self._path.read_text(encoding="utf-8")
            if previous and not previous.endswith("\n"):
                previous += "\n"

        line = json.dumps(record.to_dict(), sort_keys=True)
        payload = previous + line + "\n"
        temp_path = self._path.with_name(f"{self._path.name}.tmp")
        temp_path.write_text(payload, encoding="utf-8")
        temp_path.replace(self._path)

    def list_recent(self, limit: int = 50) -> tuple[LiveExecutionAttemptRecord, ...]:
        if limit <= 0:
            return ()
        records = self._read_all()
        records.sort(key=lambda item: item.timestamp, reverse=True)
        return tuple(records[:limit])

    def has_idempotency_key(self, idempotency_key: str) -> bool:
        normalized = idempotency_key.strip()
        if normalized == "":
            return False
        for record in self._read_all():
            if record.idempotency_key == normalized:
                return True
        return False

    def _read_all(self) -> list[LiveExecutionAttemptRecord]:
        if not self._path.exists():
            return []
        records: list[LiveExecutionAttemptRecord] = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            item = line.strip()
            if not item:
                continue
            try:
                payload = json.loads(item)
            except json.JSONDecodeError:
                continue
            if not isinstance(payload, dict):
                continue
            try:
                record = LiveExecutionAttemptRecord.from_dict(payload)
            except Exception:
                continue
            if record.attempt_id:
                records.append(record)
        return records
