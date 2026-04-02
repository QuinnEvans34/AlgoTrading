"""Dependency wiring for API routes."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from asset_research import (
    AssetResearchProvider,
    AssetResearchService,
    OpenAIResponsesAssetResearchProvider,
)
from config import AppSettings
from fastapi import Depends
from live_execution import LiveExecutionService, LiveExecutionSettings
from live_execution.brokers import create_broker_adapter
from market_data import (
    MarketDataProviderRegistry,
    MarketDataService,
    OandaConfig,
    OandaMarketDataProvider,
)
from paper_trading import PaperAccountConfig, PaperTradingService, PaperTradingStorage
from persistence import (
    DatabaseManager,
    ResearchRunMetadataRepository,
    SQLAlchemyResearchRunMetadataRepository,
    SQLAlchemyWorkflowPersistenceRepository,
    WorkflowPersistenceRepository,
    create_database_manager,
)
from research import ResearchRunner

from .config import APISettings
from .services import APIService


@lru_cache(maxsize=1)
def get_settings() -> APISettings:
    return APISettings.from_env()


def get_app_settings(
    settings: APISettings = Depends(get_settings),
) -> AppSettings:
    return settings.to_app_settings()


def get_provider_registry(
    app_settings: AppSettings = Depends(get_app_settings),
) -> MarketDataProviderRegistry:
    registry = MarketDataProviderRegistry()
    provider = app_settings.provider_settings
    if provider.enable_oanda_provider and provider.oanda_api_token:
        registry.register(
            OandaMarketDataProvider(
                OandaConfig(
                    api_token=provider.oanda_api_token,
                    account_id=provider.oanda_account_id,
                    environment=provider.oanda_environment,
                    timeout_seconds=provider.oanda_timeout_seconds,
                )
            )
        )
    return registry


def get_market_data_service(
    registry: MarketDataProviderRegistry = Depends(get_provider_registry),
) -> MarketDataService:
    return MarketDataService(registry)


@lru_cache(maxsize=4)
def _database_manager_for_settings(app_settings: AppSettings) -> DatabaseManager | None:
    return create_database_manager(app_settings.database)


def get_database_manager(
    app_settings: AppSettings = Depends(get_app_settings),
) -> DatabaseManager | None:
    return _database_manager_for_settings(app_settings)


def get_research_run_metadata_repository(
    manager: DatabaseManager | None = Depends(get_database_manager),
) -> ResearchRunMetadataRepository | None:
    if manager is None:
        return None
    return SQLAlchemyResearchRunMetadataRepository(
        session_factory=manager.session_factory
    )


def get_workflow_persistence_repository(
    manager: DatabaseManager | None = Depends(get_database_manager),
) -> WorkflowPersistenceRepository | None:
    if manager is None:
        return None
    return SQLAlchemyWorkflowPersistenceRepository(
        session_factory=manager.session_factory
    )


@lru_cache(maxsize=4)
def _asset_research_provider_for_settings(
    app_settings: AppSettings,
) -> AssetResearchProvider | None:
    ai_settings = app_settings.ai_research
    if not ai_settings.enabled:
        return None
    return OpenAIResponsesAssetResearchProvider(
        api_key=ai_settings.openai_api_key,
        model=ai_settings.openai_model,
        base_url=ai_settings.openai_base_url,
        timeout_seconds=ai_settings.timeout_seconds,
    )


def get_asset_research_provider(
    app_settings: AppSettings = Depends(get_app_settings),
) -> AssetResearchProvider | None:
    return _asset_research_provider_for_settings(app_settings)


def get_asset_research_service(
    app_settings: AppSettings = Depends(get_app_settings),
    market_data_service: MarketDataService = Depends(get_market_data_service),
    provider_registry: MarketDataProviderRegistry = Depends(get_provider_registry),
    metadata_repository: ResearchRunMetadataRepository | None = Depends(
        get_research_run_metadata_repository
    ),
    workflow_repository: WorkflowPersistenceRepository | None = Depends(
        get_workflow_persistence_repository
    ),
    provider: AssetResearchProvider | None = Depends(get_asset_research_provider),
) -> AssetResearchService:
    return AssetResearchService(
        provider=provider,
        market_data_service=market_data_service,
        provider_registry=provider_registry,
        metadata_repository=metadata_repository,
        workflow_repository=workflow_repository,
        run_output_dir=Path(app_settings.storage.run_output_dir),
        enabled=app_settings.ai_research.enabled,
    )


def get_research_runner(
    market_data_service: MarketDataService = Depends(get_market_data_service),
    metadata_repository: ResearchRunMetadataRepository | None = Depends(
        get_research_run_metadata_repository
    ),
) -> ResearchRunner:
    return ResearchRunner(
        market_data_service=market_data_service,
        metadata_repository=metadata_repository,
    )


def get_paper_trading_service(
    app_settings: AppSettings = Depends(get_app_settings),
) -> PaperTradingService:
    storage = PaperTradingStorage(Path(app_settings.storage.paper_trading_dir))
    paper = app_settings.paper_defaults
    default_config = PaperAccountConfig(
        account_id=paper.account_id,
        base_currency=paper.base_currency,
        initial_cash=paper.initial_cash,
        allow_short=paper.allow_short,
        default_spread_bps=paper.spread_bps,
        default_slippage_bps=paper.slippage_bps,
        commission_bps=paper.commission_bps,
        commission_fixed=paper.commission_fixed,
    )
    return PaperTradingService(storage=storage, default_config=default_config)


def get_live_execution_service(
    app_settings: AppSettings = Depends(get_app_settings),
) -> LiveExecutionService:
    live_settings = LiveExecutionSettings.from_app_settings(app_settings)
    adapter = create_broker_adapter(live_settings)
    return LiveExecutionService(settings=live_settings, adapter=adapter)


def get_api_service(
    settings: APISettings = Depends(get_settings),
    app_settings: AppSettings = Depends(get_app_settings),
    market_data_service: MarketDataService = Depends(get_market_data_service),
    provider_registry: MarketDataProviderRegistry = Depends(get_provider_registry),
    research_runner: ResearchRunner = Depends(get_research_runner),
    metadata_repository: ResearchRunMetadataRepository | None = Depends(
        get_research_run_metadata_repository
    ),
    workflow_repository: WorkflowPersistenceRepository | None = Depends(
        get_workflow_persistence_repository
    ),
    paper_trading_service: PaperTradingService = Depends(get_paper_trading_service),
    live_execution_service: LiveExecutionService = Depends(get_live_execution_service),
    asset_research_service: AssetResearchService = Depends(get_asset_research_service),
) -> APIService:
    return APIService(
        settings=settings,
        app_settings=app_settings,
        research_runner=research_runner,
        market_data_service=market_data_service,
        provider_registry=provider_registry,
        paper_trading_service=paper_trading_service,
        live_execution_service=live_execution_service,
        asset_research_service=asset_research_service,
        metadata_repository=metadata_repository,
        workflow_repository=workflow_repository,
    )
