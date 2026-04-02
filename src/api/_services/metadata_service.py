"""Health and metadata API orchestration."""

from __future__ import annotations

from datetime import datetime, timezone

from config import AppSettings
from live_execution import LiveExecutionService
from market_data import MarketDataProviderRegistry
from paper_trading import PaperOrderSide, PaperOrderType
from research import ResearchWorkflowType

from ..config import APISettings
from ..schemas import CapabilitiesResponseSchema, HealthResponseSchema


class MetadataAPIService:
    def __init__(
        self,
        *,
        settings: APISettings,
        app_settings: AppSettings,
        provider_registry: MarketDataProviderRegistry,
        live_execution_service: LiveExecutionService,
    ) -> None:
        self._settings = settings
        self._app_settings = app_settings
        self._provider_registry = provider_registry
        self._live_execution_service = live_execution_service

    def health(self) -> HealthResponseSchema:
        return HealthResponseSchema(
            status="ok",
            service=self._settings.app_name,
            version="v1",
            timestamp=datetime.now(timezone.utc),
        )

    def capabilities(self) -> CapabilitiesResponseSchema:
        from market_data import AssetClass, BarInterval
        from modeling import ModelFamily
        from research.validation import SUPPORTED_STRATEGY_IDS

        flags = self._app_settings.feature_flags
        live_status = self._live_execution_service.get_status()
        return CapabilitiesResponseSchema(
            workflows=[workflow.value for workflow in ResearchWorkflowType],
            strategies=list(SUPPORTED_STRATEGY_IDS),
            providers=list(self._provider_registry.available()),
            intervals=[interval.value for interval in BarInterval],
            asset_classes=[asset_class.value for asset_class in AssetClass],
            model_families=[family.value for family in ModelFamily],
            feature_flags={
                "research_api_enabled": flags.research_api_enabled,
                "history_api_enabled": flags.history_api_enabled,
                "compare_api_enabled": flags.compare_api_enabled,
                "paper_trading_enabled": flags.paper_trading_enabled,
                "live_execution_status_enabled": flags.live_execution_status_enabled,
                "live_execution_submit_enabled": flags.live_execution_submit_enabled,
            },
            paper_trading={
                "supported_order_types": [PaperOrderType.MARKET.value, PaperOrderType.LIMIT.value],
                "supported_order_sides": [PaperOrderSide.BUY.value, PaperOrderSide.SELL.value],
                "supports_short": self._settings.paper_default_allow_short,
                "supports_signal_intents": True,
                "supported_asset_classes": [asset_class.value for asset_class in AssetClass],
            },
            live_execution={
                "broker_name": live_status.broker_name.value,
                "enabled": live_status.enabled,
                "submission_allowed": live_status.submission_allowed,
                "configured": live_status.configured,
                "state": live_status.state.value,
                "message": live_status.message,
                "supported_order_types": [
                    order_type.value for order_type in live_status.capabilities.supported_order_types
                ],
                "supported_order_sides": [
                    side.value for side in live_status.capabilities.supported_order_sides
                ],
                "supported_asset_classes": [
                    asset_class.value
                    for asset_class in live_status.capabilities.supported_asset_classes
                ],
                "supports_short": live_status.capabilities.supports_short,
                "supports_cancel": live_status.capabilities.supports_cancel,
                "supports_submit": live_status.capabilities.supports_submit,
            },
        )

