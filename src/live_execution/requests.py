"""Request contracts for manual live-order submission."""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import LiveTradeIntent


@dataclass(frozen=True)
class ManualLiveOrderRequest:
    intent: LiveTradeIntent
    idempotency_key: str
    confirm_live_execution: bool
    confirmation_text: str
    operator_id: str | None = None
    operator_note: str | None = None

    def normalized(self) -> "ManualLiveOrderRequest":
        return ManualLiveOrderRequest(
            intent=self.intent,
            idempotency_key=self.idempotency_key.strip(),
            confirm_live_execution=bool(self.confirm_live_execution),
            confirmation_text=self.confirmation_text.strip(),
            operator_id=(
                None
                if self.operator_id is None or self.operator_id.strip() == ""
                else self.operator_id.strip()
            ),
            operator_note=(
                None
                if self.operator_note is None or self.operator_note.strip() == ""
                else self.operator_note.strip()
            ),
        )
