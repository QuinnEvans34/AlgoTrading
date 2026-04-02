"""Grounded asset-research orchestration."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from market_data import (
    AssetClass,
    BarInterval,
    HistoricalCandleRequest,
    Instrument,
    MarketDataAuthError,
    MarketDataRequestError,
    MarketDataService,
    UnsupportedInstrumentError,
)
from market_data.registry import MarketDataProviderRegistry
from persistence import (
    PersistenceUnavailableError,
    ResearchRunMetadataQuery,
    ResearchRunMetadataRepository,
    WorkflowPersistenceRepository,
)
from research import RunHistoryQuery, list_run_history

from .catalog import resolve_catalog_asset
from .errors import AssetResearchUnavailableError
from .models import (
    AssetResearchContext,
    AssetResearchMemoResult,
    AssetResearchMemoSection,
    AssetResearchQuestionResult,
    CatalogAssetRecord,
    GroundingDescriptor,
    MarketPriceSnapshot,
    RelatedRunNote,
    SavedConfigNote,
    StructuredForexMemoPayload,
    StructuredQuestionPayload,
    StructuredStockMemoPayload,
)
from .prompts import (
    build_memo_input,
    build_memo_instructions,
    build_question_input,
    build_question_instructions,
)
from .provider import AssetResearchProvider


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AssetResearchService:
    def __init__(
        self,
        *,
        provider: AssetResearchProvider | None,
        market_data_service: MarketDataService,
        provider_registry: MarketDataProviderRegistry,
        metadata_repository: ResearchRunMetadataRepository | None,
        workflow_repository: WorkflowPersistenceRepository | None,
        run_output_dir: Path,
        enabled: bool,
    ) -> None:
        self._provider = provider
        self._market_data_service = market_data_service
        self._provider_registry = provider_registry
        self._metadata_repository = metadata_repository
        self._workflow_repository = workflow_repository
        self._run_output_dir = run_output_dir
        self._enabled = enabled

    def generate_memo(
        self,
        *,
        asset_class: str,
        symbol: str,
    ) -> AssetResearchMemoResult:
        provider = self._require_provider()
        context = self._build_context(asset_class=asset_class, symbol=symbol)
        generated_at = _utcnow()
        if context.asset.asset_class == "stock":
            payload = StructuredStockMemoPayload.model_validate(
                provider.generate_json(
                    instructions=build_memo_instructions("stock"),
                    input_text=build_memo_input(context),
                    schema_name="stock_asset_research_memo",
                    schema=StructuredStockMemoPayload.model_json_schema(),
                )
            )
            sections = (
                AssetResearchMemoSection("Overview", payload.overview),
                AssetResearchMemoSection(
                    "Recent Price / Performance Context",
                    payload.recent_price_performance_context,
                ),
                AssetResearchMemoSection(
                    "Business / Profile Context",
                    payload.business_profile_context,
                ),
                AssetResearchMemoSection(
                    "Filing / Fundamental Highlights",
                    payload.filing_fundamental_highlights,
                ),
                AssetResearchMemoSection(
                    "Risks / Open Questions",
                    payload.risks_open_questions,
                ),
                AssetResearchMemoSection(
                    "Bottom-Line Takeaway",
                    payload.bottom_line_takeaway,
                ),
            )
        else:
            payload = StructuredForexMemoPayload.model_validate(
                provider.generate_json(
                    instructions=build_memo_instructions("forex"),
                    input_text=build_memo_input(context),
                    schema_name="forex_asset_research_memo",
                    schema=StructuredForexMemoPayload.model_json_schema(),
                )
            )
            sections = (
                AssetResearchMemoSection("Overview", payload.overview),
                AssetResearchMemoSection(
                    "Recent Price / Performance Context",
                    payload.recent_price_performance_context,
                ),
                AssetResearchMemoSection("Macro Context", payload.macro_context),
                AssetResearchMemoSection("Key Drivers", payload.key_drivers),
                AssetResearchMemoSection(
                    "Risks / Open Questions",
                    payload.risks_open_questions,
                ),
                AssetResearchMemoSection(
                    "Bottom-Line Takeaway",
                    payload.bottom_line_takeaway,
                ),
            )
        return AssetResearchMemoResult(
            asset_class=context.asset.asset_class,
            symbol=context.asset.symbol,
            name=context.asset.name,
            generated_at=generated_at,
            sections=sections,
            grounding=context.grounding,
            warnings=context.warnings,
        )

    def answer_question(
        self,
        *,
        asset_class: str,
        symbol: str,
        question: str,
    ) -> AssetResearchQuestionResult:
        provider = self._require_provider()
        context = self._build_context(asset_class=asset_class, symbol=symbol)
        payload = StructuredQuestionPayload.model_validate(
            provider.generate_json(
                instructions=build_question_instructions(context.asset.asset_class),
                input_text=build_question_input(context, question),
                schema_name="asset_research_answer",
                schema=StructuredQuestionPayload.model_json_schema(),
            )
        )
        return AssetResearchQuestionResult(
            asset_class=context.asset.asset_class,
            symbol=context.asset.symbol,
            name=context.asset.name,
            question=question,
            generated_at=_utcnow(),
            answer=payload.answer,
            grounding=context.grounding,
            warnings=context.warnings,
        )

    def _require_provider(self) -> AssetResearchProvider:
        if not self._enabled or self._provider is None:
            raise AssetResearchUnavailableError(
                "Grounded AI research is disabled or not configured."
            )
        return self._provider

    def _build_context(self, *, asset_class: str, symbol: str) -> AssetResearchContext:
        asset = resolve_catalog_asset(asset_class, symbol)
        saved_configs, saved_descriptor = self._load_saved_configs(asset)
        related_runs, runs_descriptor = self._load_related_runs(asset)
        market_price, market_descriptor, market_warning = self._load_market_price(asset)
        grounding = [
            GroundingDescriptor(
                source="catalog",
                status="used",
                detail="Using the shared curated asset catalog for profile and research context.",
            ),
            market_descriptor,
            saved_descriptor,
            runs_descriptor,
        ]
        warnings: list[str] = []
        if market_warning is not None:
            warnings.append(market_warning)
        if asset.asset_class == "stock":
            grounding.append(
                GroundingDescriptor(
                    source="filings_fundamentals_feed",
                    status="unavailable",
                    detail=(
                        "No live filings or fundamentals backend feed is wired yet; "
                        "those sections are limited to the curated catalog context."
                    ),
                )
            )
            warnings.append(
                "Live filings and fundamentals data are not currently wired, so those sections are narrowed to the curated catalog context."
            )
        else:
            grounding.append(
                GroundingDescriptor(
                    source="macro_feed",
                    status="unavailable",
                    detail=(
                        "No live macro backend feed is wired yet; macro sections are limited "
                        "to the curated pair metadata and available market context."
                    ),
                )
            )
            warnings.append(
                "Live macro data is not currently wired, so macro sections are narrowed to the curated pair context and available market data."
            )
        return AssetResearchContext(
            asset=asset,
            saved_configs=saved_configs,
            related_runs=related_runs,
            market_price=market_price,
            grounding=tuple(grounding),
            warnings=tuple(dict.fromkeys(warnings)),
        )

    def _load_saved_configs(
        self,
        asset: CatalogAssetRecord,
    ) -> tuple[tuple[SavedConfigNote, ...], GroundingDescriptor]:
        if self._workflow_repository is None:
            return (
                (),
                GroundingDescriptor(
                    source="saved_configs",
                    status="unavailable",
                    detail="Workflow persistence is unavailable, so no saved config context was loaded.",
                ),
            )
        try:
            records = self._workflow_repository.list_saved_configs(limit=100)
        except PersistenceUnavailableError:
            return (
                (),
                GroundingDescriptor(
                    source="saved_configs",
                    status="unavailable",
                    detail="Saved config persistence is temporarily unavailable.",
                ),
            )
        matching = tuple(
            SavedConfigNote(
                id=record.id,
                config_type=record.config_type,
                name=record.name,
                interval=record.interval,
                updated_at=record.updated_at,
            )
            for record in records
            if record.instrument_symbol.strip().upper() == asset.symbol
            and str(record.asset_class).strip().lower() == asset.asset_class
        )
        return (
            matching,
            GroundingDescriptor(
                source="saved_configs",
                status="used",
                detail=(
                    "No saved research configs matched this asset."
                    if not matching
                    else f"Loaded {len(matching)} saved research config templates for this asset."
                ),
            ),
        )

    def _load_related_runs(
        self,
        asset: CatalogAssetRecord,
    ) -> tuple[tuple[RelatedRunNote, ...], GroundingDescriptor]:
        exact_symbol = asset.symbol
        if self._metadata_repository is not None:
            try:
                result = self._metadata_repository.list_run_metadata(
                    ResearchRunMetadataQuery(
                        search=exact_symbol,
                        sort="started_desc",
                        limit=20,
                        offset=0,
                    )
                )
                notes = tuple(
                    RelatedRunNote(
                        run_id=record.run_id,
                        run_name=record.run_name,
                        workflow_type=record.workflow_type,
                        status=record.status,
                        interval=record.interval,
                        started_at=record.started_at,
                        has_strategy=record.has_strategy,
                        has_ml=record.has_ml,
                    )
                    for record in result.items
                    if record.instrument_symbol.strip().upper() == exact_symbol
                    and (record.asset_class or asset.asset_class) == asset.asset_class
                )
                return (
                    notes,
                    GroundingDescriptor(
                        source="recent_run_history",
                        status="used",
                        detail=(
                            "No saved runs matched this asset."
                            if not notes
                            else f"Loaded {len(notes)} recent saved runs for this asset from DB-primary history metadata."
                        ),
                    ),
                )
            except PersistenceUnavailableError:
                pass
        history = list_run_history(
            self._run_output_dir,
            RunHistoryQuery(search=exact_symbol, limit=20, offset=0, sort="started_desc"),
            metadata_repository=None,
        )
        notes = tuple(
            RelatedRunNote(
                run_id=record.run_id,
                run_name=record.run_name,
                workflow_type=record.workflow_type,
                status=record.status,
                interval=record.interval,
                started_at=record.started_at,
                has_strategy=record.has_strategy,
                has_ml=record.has_ml,
            )
            for record in history.items
            if record.instrument_symbol.strip().upper() == exact_symbol
            and (record.asset_class or asset.asset_class) == asset.asset_class
        )
        return (
            notes,
            GroundingDescriptor(
                source="recent_run_history",
                status="used",
                detail=(
                    "No saved runs matched this asset."
                    if not notes
                    else f"Loaded {len(notes)} recent saved runs for this asset from artifact-backed history."
                ),
            ),
        )

    def _load_market_price(
        self,
        asset: CatalogAssetRecord,
    ) -> tuple[MarketPriceSnapshot | None, GroundingDescriptor, str | None]:
        provider_names = self._provider_registry.available()
        if not provider_names:
            return (
                None,
                GroundingDescriptor(
                    source="market_data_preview",
                    status="unavailable",
                    detail="No market-data provider is currently registered for preview context.",
                ),
                "Market-data preview is unavailable because no provider is currently configured.",
            )
        end = _utcnow()
        start = end - timedelta(days=asset.performance_lookback_days)
        request = HistoricalCandleRequest(
            instrument=Instrument(
                symbol=asset.symbol,
                asset_class=AssetClass(asset.asset_class),
            ),
            interval=BarInterval(asset.preferred_interval),
            start=start,
            end=end,
        )
        for provider_name in provider_names:
            try:
                response = self._market_data_service.fetch_historical_candles(
                    provider_name,
                    request,
                )
            except (
                KeyError,
                UnsupportedInstrumentError,
                MarketDataAuthError,
                MarketDataRequestError,
                ValueError,
            ):
                continue
            candles = list(response.candles)
            if not candles:
                continue
            first = candles[0]
            last = candles[-1]
            snapshot = MarketPriceSnapshot(
                provider=response.provider,
                interval=response.interval.value,
                candle_count=len(candles),
                period_start=first.timestamp,
                period_end=last.timestamp,
                latest_close=last.close,
                net_change=last.close - first.close,
                net_change_pct=0.0
                if first.close == 0
                else ((last.close - first.close) / first.close) * 100.0,
                low=min(candle.low for candle in candles),
                high=max(candle.high for candle in candles),
            )
            return (
                snapshot,
                GroundingDescriptor(
                    source="market_data_preview",
                    status="used",
                    detail=(
                        f"Loaded {snapshot.candle_count} {snapshot.interval} candles from provider '{snapshot.provider}'."
                    ),
                ),
                None,
            )
        if asset.asset_class == "stock":
            warning = (
                "Provider-backed stock price preview is not currently available, so performance commentary is narrowed."
            )
        else:
            warning = (
                "Provider-backed FX price preview is not currently available, so the memo is narrowed to catalog and workflow context."
            )
        return (
            None,
            GroundingDescriptor(
                source="market_data_preview",
                status="unavailable",
                detail="No configured provider could supply a compatible historical preview for this asset.",
            ),
            warning,
        )
