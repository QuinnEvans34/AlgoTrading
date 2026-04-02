"""Shared static asset catalog for product browsing and AI grounding."""

from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path

from .models import CatalogAssetRecord

_CATALOG_PATH = (
    Path(__file__).resolve().parents[2]
    / "frontend"
    / "src"
    / "lib"
    / "catalog"
    / "assetCatalog.json"
)


def _catalog_asset_from_payload(payload: dict, asset_class: str) -> CatalogAssetRecord:
    return CatalogAssetRecord(
        symbol=str(payload["symbol"]).upper(),
        asset_class=asset_class,  # type: ignore[arg-type]
        name=str(payload["name"]),
        headline=str(payload["headline"]),
        description=str(payload["description"]),
        tags=tuple(str(item) for item in payload.get("tags", [])),
        preferred_interval=str(payload["preferredInterval"]),
        performance_lookback_days=int(payload["performanceLookbackDays"]),
        profile_bullets=tuple(str(item) for item in payload.get("profileBullets", [])),
        performance_focus=tuple(str(item) for item in payload.get("performanceFocus", [])),
        ai_prompts=tuple(str(item) for item in payload.get("aiPrompts", [])),
        sector=None if payload.get("sector") is None else str(payload["sector"]),
        exchange=None if payload.get("exchange") is None else str(payload["exchange"]),
        filings_focus=tuple(str(item) for item in payload.get("filingsFocus", [])),
        region=None if payload.get("region") is None else str(payload["region"]),
        macro_drivers=tuple(str(item) for item in payload.get("macroDrivers", [])),
    )


@lru_cache(maxsize=1)
def load_catalog() -> tuple[CatalogAssetRecord, ...]:
    payload = json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))
    stocks = [
        _catalog_asset_from_payload(item, "stock")
        for item in payload.get("stocks", [])
        if isinstance(item, dict)
    ]
    forex = [
        _catalog_asset_from_payload(item, "forex")
        for item in payload.get("forex", [])
        if isinstance(item, dict)
    ]
    return tuple([*stocks, *forex])


def find_catalog_asset(asset_class: str, symbol: str) -> CatalogAssetRecord | None:
    normalized_symbol = symbol.strip().upper()
    for asset in load_catalog():
        if asset.asset_class == asset_class and asset.symbol == normalized_symbol:
            return asset
    return None


def build_fallback_catalog_asset(asset_class: str, symbol: str) -> CatalogAssetRecord:
    normalized_symbol = symbol.strip().upper()
    if asset_class == "forex":
        return CatalogAssetRecord(
            symbol=normalized_symbol,
            asset_class="forex",
            name=normalized_symbol.replace("_", " / "),
            headline="Uncatalogued FX pair opened directly from the product.",
            description=(
                "This asset is not yet part of the curated explorer catalog, but you can still "
                "launch research and use watchlist continuity."
            ),
            tags=("custom", "research"),
            preferred_interval="4h",
            performance_lookback_days=120,
            region="Custom FX",
            profile_bullets=(
                "Treat this page as a research launch surface rather than a full market profile.",
                "Use history and compare to inspect prior work on this pair.",
            ),
            performance_focus=(
                "Trend persistence on the chosen interval",
                "Range behavior in quiet sessions",
                "Response to macro catalysts",
            ),
            ai_prompts=(
                "Launch ML research using the existing saved-config workflow.",
                "Compare runs after you have at least two compatible saved results.",
            ),
            macro_drivers=(
                "Relative policy path",
                "Macro surprise flow",
                "Risk sentiment",
            ),
        )
    return CatalogAssetRecord(
        symbol=normalized_symbol,
        asset_class="stock",
        name=normalized_symbol,
        headline="Uncatalogued equity opened directly from the product.",
        description=(
            "This asset is not yet part of the curated stock explorer, but it still supports "
            "watchlist, history, and research handoff."
        ),
        tags=("custom", "research"),
        preferred_interval="1d",
        performance_lookback_days=180,
        sector="Custom Equity",
        exchange="Custom",
        profile_bullets=(
            "Use this page to route into Strategy Lab, ML Lab, and related run history.",
            "Add the asset to your watchlist if it should become part of your regular workflow.",
        ),
        filings_focus=(
            "Quarterly revenue and margin trend",
            "Management guidance changes",
            "Risk factors that affect the current thesis",
        ),
        performance_focus=(
            "Reaction to earnings and guidance",
            "Trend quality on the chosen interval",
            "Relative strength versus your watchlist",
        ),
        ai_prompts=(
            "Save a strategy template if you revisit this symbol frequently.",
            "Use compare once multiple runs exist for the same name.",
        ),
    )


def resolve_catalog_asset(asset_class: str, symbol: str) -> CatalogAssetRecord:
    return find_catalog_asset(asset_class, symbol) or build_fallback_catalog_asset(
        asset_class,
        symbol,
    )
