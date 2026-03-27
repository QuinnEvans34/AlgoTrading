"""Validation for live trade intents against static broker capabilities."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping

from .brokers.capabilities import unsupported_reasons
from .contracts import BrokerCapabilities, IntentValidationResult, LiveTradeIntent


def normalize_intent(intent: LiveTradeIntent) -> LiveTradeIntent:
    metadata: Mapping[str, Any] = dict(intent.metadata)
    client_order_id = intent.client_order_id
    if client_order_id is not None:
        stripped = client_order_id.strip()
        client_order_id = stripped if stripped else None
    return replace(
        intent,
        client_order_id=client_order_id,
        metadata=metadata,
    )


def validate_intent_against_capabilities(
    intent: LiveTradeIntent,
    capabilities: BrokerCapabilities,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if intent.quantity <= 0:
        reasons.append("quantity_must_be_greater_than_zero")
    if intent.order_type.value == "limit" and (intent.limit_price is None or intent.limit_price <= 0):
        reasons.append("limit_price_must_be_greater_than_zero")
    reasons.extend(unsupported_reasons(intent, capabilities))
    deduped = sorted(set(reasons))
    return tuple(deduped)


def build_validation_result(
    *,
    intent: LiveTradeIntent,
    capabilities: BrokerCapabilities,
    broker_payload_preview: Mapping[str, Any] | None,
    extra_reasons: tuple[str, ...] = (),
) -> IntentValidationResult:
    normalized = normalize_intent(intent)
    reasons = list(validate_intent_against_capabilities(normalized, capabilities))
    reasons.extend(extra_reasons)
    unique = tuple(sorted(set(reasons)))
    return IntentValidationResult(
        accepted=not unique,
        reasons=unique,
        normalized_intent=normalized,
        broker_payload_preview=broker_payload_preview,
    )


def summarize_validation_reasons(reasons: tuple[str, ...]) -> str:
    if not reasons:
        return "Intent validation passed."
    return ", ".join(reasons)
