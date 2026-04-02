"""Public API service facade composed from concern-specific collaborators."""

from __future__ import annotations

from datetime import datetime

from config import AppSettings
from live_execution import LiveExecutionService
from market_data import MarketDataProviderRegistry, MarketDataService
from paper_trading import PaperTradingService
from persistence import ResearchRunMetadataRepository, WorkflowPersistenceRepository
from research import ResearchRunner
from asset_research import AssetResearchService

from ._services.asset_research_service import AssetResearchAPIService
from ._services.history_service import HistoryAPIService
from ._services.live_service import LiveAPIService
from ._services.market_data_service import MarketDataAPIService
from ._services.metadata_service import MetadataAPIService
from ._services.paper_service import PaperAPIService
from ._services.research_service import ResearchAPIService
from ._services.settings_service import SettingsAPIService
from ._services.workflow_service import WorkflowAPIService
from .config import APISettings
from .asset_research_schemas import (
    AskAssetResearchQuestionRequestSchema,
    AskAssetResearchQuestionResponseSchema,
    GenerateAssetMemoRequestSchema,
    GenerateAssetMemoResponseSchema,
)
from .history_schemas import (
    CompareRunsRequestSchema,
    CompareRunsResponseSchema,
    HistoryReadResponseSchema,
    RunHistoryListResponseSchema,
)
from .live_execution_schemas import (
    LiveExecutionAttemptsResponseSchema,
    LiveExecutionReadinessResponseSchema,
    LiveExecutionStatusResponseSchema,
    LiveIntentValidationResponseSchema,
    LiveSubmitResponseSchema,
    LiveTradeIntentSchema,
    ManualLiveOrderRequestSchema,
    ManualLiveSubmitResponseSchema,
)
from .paper_trading_schemas import (
    PaperCancelActionResponseSchema,
    PaperOrderActionResponseSchema,
    PaperOrderRequestSchema,
    PaperPriceUpdateResponseSchema,
    PaperResetRequestSchema,
    PaperSignalIntentRequestSchema,
    PaperStateResponseSchema,
    PriceUpdateRequestSchema,
)
from .schemas import (
    CapabilitiesResponseSchema,
    HealthResponseSchema,
    HybridRunRequestSchema,
    MarketDataPreviewRequestSchema,
    MarketDataPreviewResponseSchema,
    MLRunRequestSchema,
    RunDetailResponseSchema,
    RunSummaryResponseSchema,
    StoredRunSummaryListResponseSchema,
    StrategyRunRequestSchema,
)
from .settings_schemas import SystemSettingsResponseSchema
from .workflow_schemas import (
    DeleteWorkflowObjectResponseSchema,
    RecentAssetListResponseSchema,
    RecentAssetResponseSchema,
    RecentAssetTouchSchema,
    RecentCompareSetListResponseSchema,
    RecentCompareSetResponseSchema,
    RecentCompareTouchSchema,
    SavedResearchConfigListResponseSchema,
    SavedResearchConfigResponseSchema,
    SavedResearchConfigWriteSchema,
    WatchlistItemResponseSchema,
    WatchlistItemWriteSchema,
    WatchlistResponseSchema,
)


class APIService:
    def __init__(
        self,
        *,
        settings: APISettings,
        app_settings: AppSettings,
        research_runner: ResearchRunner,
        market_data_service: MarketDataService,
        provider_registry: MarketDataProviderRegistry,
        paper_trading_service: PaperTradingService,
        live_execution_service: LiveExecutionService,
        asset_research_service: AssetResearchService,
        metadata_repository: ResearchRunMetadataRepository | None = None,
        workflow_repository: WorkflowPersistenceRepository | None = None,
    ) -> None:
        self._metadata = MetadataAPIService(
            settings=settings,
            app_settings=app_settings,
            provider_registry=provider_registry,
            live_execution_service=live_execution_service,
        )
        self._settings_service = SettingsAPIService(app_settings=app_settings)
        self._market_data = MarketDataAPIService(market_data_service=market_data_service)
        self._research = ResearchAPIService(
            settings=settings,
            app_settings=app_settings,
            research_runner=research_runner,
        )
        self._history = HistoryAPIService(
            settings=settings,
            app_settings=app_settings,
            metadata_repository=metadata_repository,
        )
        self._paper = PaperAPIService(
            settings=settings,
            app_settings=app_settings,
            paper_trading_service=paper_trading_service,
        )
        self._live = LiveAPIService(
            app_settings=app_settings,
            live_execution_service=live_execution_service,
        )
        self._workflow = WorkflowAPIService(
            workflow_repository=workflow_repository,
        )
        self._asset_research = AssetResearchAPIService(
            asset_research_service=asset_research_service,
        )

    def health(self) -> HealthResponseSchema:
        return self._metadata.health()

    def capabilities(self) -> CapabilitiesResponseSchema:
        return self._metadata.capabilities()

    def get_system_settings(self) -> SystemSettingsResponseSchema:
        return self._settings_service.get_system_settings()

    def preview_historical_data(
        self,
        request: MarketDataPreviewRequestSchema,
    ) -> MarketDataPreviewResponseSchema:
        return self._market_data.preview_historical_data(request)

    def run_strategy(
        self,
        request: StrategyRunRequestSchema,
    ) -> RunSummaryResponseSchema:
        return self._research.run_strategy(request)

    def run_ml(
        self,
        request: MLRunRequestSchema,
    ) -> RunSummaryResponseSchema:
        return self._research.run_ml(request)

    def run_hybrid(
        self,
        request: HybridRunRequestSchema,
    ) -> RunSummaryResponseSchema:
        return self._research.run_hybrid(request)

    def list_saved_run_summaries(self, *, limit: int = 50) -> StoredRunSummaryListResponseSchema:
        return self._history.list_saved_run_summaries(limit=limit)

    def get_saved_run_summary(self, run_id: str) -> RunSummaryResponseSchema:
        return self._history.get_saved_run_summary(run_id)

    def get_saved_run_detail(self, run_id: str) -> RunDetailResponseSchema:
        return self._history.get_saved_run_detail(run_id)

    def list_history_runs(
        self,
        *,
        workflow_type: str | None = None,
        status: str | None = None,
        search: str | None = None,
        started_after: datetime | None = None,
        started_before: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str = "started_desc",
    ) -> RunHistoryListResponseSchema:
        return self._history.list_history_runs(
            workflow_type=workflow_type,
            status=status,
            search=search,
            started_after=started_after,
            started_before=started_before,
            limit=limit,
            offset=offset,
            sort=sort,
        )

    def get_history_run(self, run_id: str) -> HistoryReadResponseSchema:
        return self._history.get_history_run(run_id)

    def compare_runs(self, request: CompareRunsRequestSchema) -> CompareRunsResponseSchema:
        return self._history.compare_runs(request)

    def list_saved_configs(
        self,
        *,
        config_type: str | None = None,
        limit: int = 100,
    ) -> SavedResearchConfigListResponseSchema:
        return self._workflow.list_saved_configs(config_type=config_type, limit=limit)

    def create_saved_config(
        self,
        request: SavedResearchConfigWriteSchema,
    ) -> SavedResearchConfigResponseSchema:
        return self._workflow.create_saved_config(request)

    def get_saved_config(self, config_id: str) -> SavedResearchConfigResponseSchema:
        return self._workflow.get_saved_config(config_id)

    def update_saved_config(
        self,
        config_id: str,
        request: SavedResearchConfigWriteSchema,
    ) -> SavedResearchConfigResponseSchema:
        return self._workflow.update_saved_config(config_id, request)

    def delete_saved_config(self, config_id: str) -> DeleteWorkflowObjectResponseSchema:
        return self._workflow.delete_saved_config(config_id)

    def list_watchlist(self, *, limit: int = 100) -> WatchlistResponseSchema:
        return self._workflow.list_watchlist(limit=limit)

    def add_watchlist_item(
        self,
        request: WatchlistItemWriteSchema,
    ) -> WatchlistItemResponseSchema:
        return self._workflow.add_watchlist_item(request)

    def delete_watchlist_item(
        self,
        *,
        asset_class: str,
        symbol: str,
    ) -> DeleteWorkflowObjectResponseSchema:
        return self._workflow.delete_watchlist_item(asset_class=asset_class, symbol=symbol)

    def list_recent_assets(self, *, limit: int = 20) -> RecentAssetListResponseSchema:
        return self._workflow.list_recent_assets(limit=limit)

    def touch_recent_asset(
        self,
        request: RecentAssetTouchSchema,
    ) -> RecentAssetResponseSchema:
        return self._workflow.touch_recent_asset(request)

    def list_recent_compares(
        self,
        *,
        limit: int = 20,
    ) -> RecentCompareSetListResponseSchema:
        return self._workflow.list_recent_compares(limit=limit)

    def touch_recent_compare(
        self,
        request: RecentCompareTouchSchema,
    ) -> RecentCompareSetResponseSchema:
        return self._workflow.touch_recent_compare(request)

    def generate_asset_research_memo(
        self,
        request: GenerateAssetMemoRequestSchema,
    ) -> GenerateAssetMemoResponseSchema:
        return self._asset_research.generate_memo(request)

    def answer_asset_research_question(
        self,
        request: AskAssetResearchQuestionRequestSchema,
    ) -> AskAssetResearchQuestionResponseSchema:
        return self._asset_research.answer_question(request)

    def get_live_execution_status(self) -> LiveExecutionStatusResponseSchema:
        return self._live.get_live_execution_status()

    def get_live_execution_readiness(self) -> LiveExecutionReadinessResponseSchema:
        return self._live.get_live_execution_readiness()

    def validate_live_intent(
        self,
        request: LiveTradeIntentSchema,
    ) -> LiveIntentValidationResponseSchema:
        return self._live.validate_live_intent(request)

    def submit_live_intent(
        self,
        request: LiveTradeIntentSchema,
    ) -> LiveSubmitResponseSchema:
        return self._live.submit_live_intent(request)

    def submit_manual_live_order(
        self,
        request: ManualLiveOrderRequestSchema,
    ) -> ManualLiveSubmitResponseSchema:
        return self._live.submit_manual_live_order(request)

    def list_live_execution_attempts(
        self,
        limit: int = 25,
    ) -> LiveExecutionAttemptsResponseSchema:
        return self._live.list_live_execution_attempts(limit=limit)

    def get_paper_state(self, *, fills_limit: int = 100) -> PaperStateResponseSchema:
        return self._paper.get_paper_state(fills_limit=fills_limit)

    def place_paper_order(
        self,
        request: PaperOrderRequestSchema,
    ) -> PaperOrderActionResponseSchema:
        return self._paper.place_paper_order(request)

    def cancel_paper_order(self, order_id: str) -> PaperCancelActionResponseSchema:
        return self._paper.cancel_paper_order(order_id)

    def process_paper_price_update(
        self,
        request: PriceUpdateRequestSchema,
    ) -> PaperPriceUpdateResponseSchema:
        return self._paper.process_paper_price_update(request)

    def submit_paper_signal_intent(
        self,
        request: PaperSignalIntentRequestSchema,
    ) -> PaperOrderActionResponseSchema:
        return self._paper.submit_paper_signal_intent(request)

    def reset_paper_account(
        self,
        request: PaperResetRequestSchema,
    ) -> PaperStateResponseSchema:
        return self._paper.reset_paper_account(request)
