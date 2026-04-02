"""Explicit prompt builders for grounded asset research."""

from __future__ import annotations

import json

from .models import AssetResearchContext

_COMMON_INSTRUCTIONS = """You are a grounded asset research assistant.
Use only the supplied context. Never invent filings, fundamentals, macro facts, prices, or company events.
If a requested area is not available in the context, say that the data is not currently wired and keep the section narrow.
Write concise research-memo prose, not chatbot filler.
Avoid hype, motivational language, and unsupported causal claims.
Do not mention any data outside the supplied context.
"""


def _context_payload(context: AssetResearchContext) -> dict[str, object]:
    asset = context.asset
    asset_payload: dict[str, object] = {
        "symbol": asset.symbol,
        "asset_class": asset.asset_class,
        "name": asset.name,
        "headline": asset.headline,
        "description": asset.description,
        "tags": list(asset.tags),
        "preferred_interval": asset.preferred_interval,
        "performance_lookback_days": asset.performance_lookback_days,
        "profile_bullets": list(asset.profile_bullets),
        "performance_focus": list(asset.performance_focus),
        "ai_prompts": list(asset.ai_prompts),
    }
    if asset.asset_class == "stock":
        asset_payload["sector"] = asset.sector
        asset_payload["exchange"] = asset.exchange
        asset_payload["filings_focus"] = list(asset.filings_focus)
    else:
        asset_payload["region"] = asset.region
        asset_payload["macro_drivers"] = list(asset.macro_drivers)

    payload: dict[str, object] = {
        "asset": asset_payload,
        "saved_configs": [
            {
                "id": item.id,
                "config_type": item.config_type,
                "name": item.name,
                "interval": item.interval,
                "updated_at": item.updated_at.isoformat(),
            }
            for item in context.saved_configs
        ],
        "related_runs": [
            {
                "run_id": item.run_id,
                "run_name": item.run_name,
                "workflow_type": item.workflow_type,
                "status": item.status,
                "interval": item.interval,
                "started_at": (
                    None if item.started_at is None else item.started_at.isoformat()
                ),
                "has_strategy": item.has_strategy,
                "has_ml": item.has_ml,
            }
            for item in context.related_runs
        ],
        "grounding": [
            {
                "source": item.source,
                "status": item.status,
                "detail": item.detail,
            }
            for item in context.grounding
        ],
        "warnings": list(context.warnings),
    }
    if context.market_price is None:
        payload["market_price"] = None
    else:
        payload["market_price"] = {
            "provider": context.market_price.provider,
            "interval": context.market_price.interval,
            "candle_count": context.market_price.candle_count,
            "period_start": context.market_price.period_start.isoformat(),
            "period_end": context.market_price.period_end.isoformat(),
            "latest_close": context.market_price.latest_close,
            "net_change": context.market_price.net_change,
            "net_change_pct": context.market_price.net_change_pct,
            "low": context.market_price.low,
            "high": context.market_price.high,
        }
    return payload


def build_memo_instructions(asset_class: str) -> str:
    if asset_class == "stock":
        return (
            f"{_COMMON_INSTRUCTIONS}\n"
            "Produce a stock research memo with these exact sections: "
            "Overview, Recent Price / Performance Context, Business / Profile Context, "
            "Filing / Fundamental Highlights, Risks / Open Questions, Bottom-Line Takeaway.\n"
            "If filings or fundamentals are unavailable, say so clearly in the Filing / Fundamental Highlights section."
        )
    return (
        f"{_COMMON_INSTRUCTIONS}\n"
        "Produce a forex research memo with these exact sections: "
        "Overview, Recent Price / Performance Context, Macro Context, Key Drivers, "
        "Risks / Open Questions, Bottom-Line Takeaway.\n"
        "If macro data is unavailable beyond the curated context, say so clearly in the Macro Context section."
    )


def build_question_instructions(asset_class: str) -> str:
    scope = "stock asset" if asset_class == "stock" else "forex pair"
    return (
        f"{_COMMON_INSTRUCTIONS}\n"
        f"Answer the user's question about the {scope} using only the supplied context.\n"
        "Answer directly in concise research prose. If context is insufficient for a claim, say so explicitly."
    )


def build_memo_input(context: AssetResearchContext) -> str:
    return json.dumps(_context_payload(context), indent=2, sort_keys=True)


def build_question_input(context: AssetResearchContext, question: str) -> str:
    payload = _context_payload(context)
    payload["question"] = question
    return json.dumps(payload, indent=2, sort_keys=True)
