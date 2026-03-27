"""Thin API service layer that composes existing backend subsystems."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backtesting import BacktestConfig, RiskExitConfig
from config import AppSettings, build_safe_system_settings_snapshot
from diagnostics import DiagnosticsConfig
from live_execution import (
    GuardCheckResult,
    LiveExecutionAdapterError,
    LiveExecutionAdapterTimeoutError,
    LiveExecutionDisabledError,
    LiveExecutionNotConfiguredError,
    LiveExecutionService,
    LiveExecutionUnsupportedCapabilityError,
    ManualLiveOrderRequest,
    LiveOrderSide,
    LiveOrderType,
    LiveTradeIntent,
)
from market_data import (
    Candle,
    HistoricalCandleRequest,
    Instrument,
    MarketDataAuthError,
    MarketDataRequestError,
    MarketDataService,
    MarketDataProviderRegistry,
    UnsupportedInstrumentError,
)
from ml_data import (
    DirectionLabelSpec,
    FeatureSpec,
    FutureReturnLabelSpec,
    MissingValuePolicy,
    MissingVolumePolicy,
    SplitSpec,
)
from modeling import ModelSpec, OptionalDependencyPolicy, TaskType, TrainingConfig
from paper_trading import (
    PaperAccountConfig,
    PaperOrderRequest,
    PaperOrderSide,
    PaperOrderType,
    PaperSignalDirection,
    PaperSignalIntent,
    PaperTradingService,
    PriceUpdate,
)
from research import (
    InlineCandleSource,
    MLWorkflowSpec,
    MarketDataFetchSource,
    ResearchRunConfig,
    ResearchRunRequest,
    ResearchRunner,
    ResearchWorkflowType,
    StrategyWorkflowSpec,
    compare_saved_runs,
    get_run_detail,
    get_run_manifest,
    get_run_summary,
    list_run_history,
)

from .config import APISettings
from .errors import APIError
from .history_schemas import (
    CompareRunsRequestSchema,
    CompareRunsResponseSchema,
    HistoryReadResponseSchema,
    RunHistoryItemSchema,
    RunHistoryListResponseSchema,
)
from .live_execution_schemas import (
    LiveExecutionAttemptsResponseSchema,
    LiveExecutionReadinessResponseSchema,
    LiveExecutionStatusResponseSchema,
    LiveIntentValidationResponseSchema,
    ManualLiveOrderRequestSchema,
    ManualLiveSubmitResponseSchema,
    LiveSubmitResponseSchema,
    LiveTradeIntentSchema,
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
from .serializers import (
    serialize_market_data_preview,
    serialize_paper_cancel_action,
    serialize_paper_order_action,
    serialize_paper_price_update,
    serialize_paper_state,
    serialize_run_detail_from_summary,
    serialize_run_summary,
    serialize_stored_run_detail,
    serialize_stored_run_summary,
)
from .schemas import (
    CapabilitiesResponseSchema,
    CandleSchema,
    DirectionLabelSpecSchema,
    FutureReturnLabelSpecSchema,
    HealthResponseSchema,
    HybridRunRequestSchema,
    InlineCandleSourceSchema,
    MarketDataFetchSourceSchema,
    MarketDataPreviewRequestSchema,
    MarketDataPreviewResponseSchema,
    MLRunRequestSchema,
    ModelSpecSchema,
    RunConfigSchema,
    RunDetailResponseSchema,
    RunSummaryResponseSchema,
    SplitSpecSchema,
    StoredRunSummaryListResponseSchema,
    StrategyRunRequestSchema,
)
from .settings_schemas import SystemSettingsResponseSchema


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
    ) -> None:
        self._settings = settings
        self._app_settings = app_settings
        self._research_runner = research_runner
        self._market_data_service = market_data_service
        self._provider_registry = provider_registry
        self._paper_trading_service = paper_trading_service
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
            workflows=[w.value for w in ResearchWorkflowType],
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

    def get_system_settings(self) -> SystemSettingsResponseSchema:
        snapshot = build_safe_system_settings_snapshot(self._app_settings)
        return SystemSettingsResponseSchema.model_validate(snapshot.to_dict())

    def preview_historical_data(
        self,
        request: MarketDataPreviewRequestSchema,
    ) -> MarketDataPreviewResponseSchema:
        try:
            response = self._market_data_service.fetch_historical_candles(
                provider_name=request.provider_name,
                request=HistoricalCandleRequest(
                    instrument=self._to_instrument(request.instrument),
                    interval=request.interval,
                    start=request.start,
                    end=request.end,
                    limit=request.limit,
                ),
            )
            return serialize_market_data_preview(response)
        except KeyError as exc:
            raise APIError(
                status_code=404,
                code="provider_not_found",
                message=f"Provider '{request.provider_name}' is not registered",
            ) from exc
        except UnsupportedInstrumentError as exc:
            raise APIError(
                status_code=400,
                code="unsupported_instrument",
                message=str(exc),
            ) from exc
        except MarketDataAuthError as exc:
            raise APIError(
                status_code=502,
                code="provider_auth_error",
                message=str(exc),
            ) from exc
        except MarketDataRequestError as exc:
            raise APIError(
                status_code=502,
                code="provider_request_error",
                message=str(exc),
            ) from exc

    def run_strategy(
        self,
        request: StrategyRunRequestSchema,
    ) -> RunSummaryResponseSchema:
        self._ensure_feature_enabled(
            "research_api_enabled",
            code="research_disabled",
            message="Research run endpoints are disabled by feature flag.",
        )
        run_request = ResearchRunRequest(
            workflow_type=ResearchWorkflowType.STRATEGY_RESEARCH,
            instrument=self._to_instrument(request.instrument),
            interval=request.interval,
            candle_source=self._to_candle_source(request.candle_source),
            strategy_spec=self._to_strategy_spec(request.strategy_spec),
            run_config=self._to_run_config(request.run_config),
        )
        artifact = self._research_runner.run(run_request)
        return serialize_run_summary(artifact)

    def run_ml(
        self,
        request: MLRunRequestSchema,
    ) -> RunSummaryResponseSchema:
        self._ensure_feature_enabled(
            "research_api_enabled",
            code="research_disabled",
            message="Research run endpoints are disabled by feature flag.",
        )
        run_request = ResearchRunRequest(
            workflow_type=ResearchWorkflowType.ML_RESEARCH,
            instrument=self._to_instrument(request.instrument),
            interval=request.interval,
            candle_source=self._to_candle_source(request.candle_source),
            ml_spec=self._to_ml_spec(request.ml_spec),
            run_config=self._to_run_config(request.run_config),
        )
        artifact = self._research_runner.run(run_request)
        return serialize_run_summary(artifact)

    def run_hybrid(
        self,
        request: HybridRunRequestSchema,
    ) -> RunSummaryResponseSchema:
        self._ensure_feature_enabled(
            "research_api_enabled",
            code="research_disabled",
            message="Research run endpoints are disabled by feature flag.",
        )
        run_request = ResearchRunRequest(
            workflow_type=ResearchWorkflowType.HYBRID_RESEARCH,
            instrument=self._to_instrument(request.instrument),
            interval=request.interval,
            candle_source=self._to_candle_source(request.candle_source),
            strategy_spec=self._to_strategy_spec(request.strategy_spec),
            ml_spec=self._to_ml_spec(request.ml_spec),
            run_config=self._to_run_config(request.run_config),
        )
        artifact = self._research_runner.run(run_request)
        return serialize_run_summary(artifact)

    def list_saved_run_summaries(self, *, limit: int = 50) -> StoredRunSummaryListResponseSchema:
        self._ensure_feature_enabled(
            "history_api_enabled",
            code="history_disabled",
            message="History and saved run endpoints are disabled by feature flag.",
        )
        history = self.list_history_runs(limit=limit, offset=0)
        items = []
        for run in history.items:
            items.append(
                {
                    "run_id": run.run_id,
                    "run_name": run.run_name,
                    "workflow_type": run.workflow_type,
                    "status": run.status,
                    "started_at": run.started_at,
                    "ended_at": run.ended_at,
                    "summary_path": f"{run.run_id}/summary.json",
                }
            )
        return StoredRunSummaryListResponseSchema.model_validate({"runs": items})

    def get_saved_run_summary(self, run_id: str) -> RunSummaryResponseSchema:
        self._ensure_feature_enabled(
            "history_api_enabled",
            code="history_disabled",
            message="History and saved run endpoints are disabled by feature flag.",
        )
        payload = self._history_summary_payload(run_id)
        return serialize_stored_run_summary(payload)

    def get_saved_run_detail(self, run_id: str) -> RunDetailResponseSchema:
        self._ensure_feature_enabled(
            "history_api_enabled",
            code="history_disabled",
            message="History and saved run endpoints are disabled by feature flag.",
        )
        try:
            detail_payload = get_run_detail(self._history_root, run_id)
            if "summary" in detail_payload:
                return serialize_stored_run_detail(detail_payload)
            return serialize_run_detail_from_summary(detail_payload)
        except ValueError as exc:
            raise APIError(
                status_code=400,
                code="invalid_run_id",
                message=str(exc),
            ) from exc
        except FileNotFoundError as exc:
            raise APIError(
                status_code=404,
                code="run_detail_not_found",
                message=str(exc),
            ) from exc
        except (OSError, TypeError, ValueError) as exc:
            raise APIError(
                status_code=500,
                code="run_detail_read_error",
                message=f"Failed to read detail for run_id '{run_id}'",
            ) from exc

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
        self._ensure_feature_enabled(
            "history_api_enabled",
            code="history_disabled",
            message="History and saved run endpoints are disabled by feature flag.",
        )
        from research import RunHistoryQuery

        result = list_run_history(
            self._history_root,
            RunHistoryQuery(
                workflow_type=workflow_type,
                status=status,
                search=search,
                started_after=started_after,
                started_before=started_before,
                limit=limit,
                offset=offset,
                sort=sort,
            ),
        )
        items = [
            RunHistoryItemSchema.model_validate(
                {
                    "run_id": record.run_id,
                    "run_name": record.run_name,
                    "workflow_type": record.workflow_type,
                    "status": record.status,
                    "started_at": record.started_at,
                    "ended_at": record.ended_at,
                    "duration_ms": record.duration_ms,
                    "instrument_symbol": record.instrument_symbol,
                    "asset_class": record.asset_class,
                    "interval": record.interval,
                    "has_strategy": record.has_strategy,
                    "has_ml": record.has_ml,
                    "summary_available": record.summary_available,
                    "detail_available": record.detail_available,
                    "updated_at": record.updated_at,
                }
            )
            for record in result.items
        ]
        return RunHistoryListResponseSchema(
            items=items,
            total=result.total,
            limit=result.limit,
            offset=result.offset,
            warnings=list(result.warnings),
        )

    def get_history_run(self, run_id: str) -> HistoryReadResponseSchema:
        self._ensure_feature_enabled(
            "history_api_enabled",
            code="history_disabled",
            message="History and saved run endpoints are disabled by feature flag.",
        )
        try:
            manifest_payload = get_run_manifest(self._history_root, run_id)
            summary_payload = get_run_summary(self._history_root, run_id)
            detail_payload = get_run_detail(self._history_root, run_id)
        except ValueError as exc:
            raise APIError(
                status_code=400,
                code="invalid_run_id",
                message=str(exc),
            ) from exc
        except FileNotFoundError as exc:
            raise APIError(
                status_code=404,
                code="run_not_found",
                message=str(exc),
            ) from exc
        except (OSError, TypeError, ValueError) as exc:
            raise APIError(
                status_code=500,
                code="run_read_error",
                message=f"Failed to load run artifacts for '{run_id}'",
            ) from exc
        detail = (
            serialize_stored_run_detail(detail_payload)
            if "summary" in detail_payload
            else serialize_run_detail_from_summary(summary_payload)
        )
        return HistoryReadResponseSchema.model_validate(
            {
                "manifest": manifest_payload,
                "summary": summary_payload,
                "detail": detail.model_dump(),
            }
        )

    def compare_runs(self, request: CompareRunsRequestSchema) -> CompareRunsResponseSchema:
        self._ensure_feature_enabled(
            "compare_api_enabled",
            code="compare_disabled",
            message="Run comparison endpoint is disabled by feature flag.",
        )
        try:
            result = compare_saved_runs(
                root_dir=self._history_root,
                run_ids=request.run_ids,
                mode=request.mode,
            )
        except ValueError as exc:
            raise APIError(
                status_code=400,
                code="compare_invalid",
                message=str(exc),
            ) from exc
        except FileNotFoundError as exc:
            raise APIError(
                status_code=404,
                code="run_not_found",
                message=str(exc),
            ) from exc
        except (OSError, TypeError, ValueError) as exc:
            raise APIError(
                status_code=500,
                code="compare_read_error",
                message="Failed to compare selected runs",
            ) from exc
        return CompareRunsResponseSchema.model_validate(
            {
                "mode": result.mode,
                "warnings": list(result.warnings),
                "cards": list(result.cards),
                "rows": list(result.rows),
            }
        )

    def get_live_execution_status(self) -> LiveExecutionStatusResponseSchema:
        self._ensure_feature_enabled(
            "live_execution_status_enabled",
            code="live_execution_status_disabled",
            message="Live execution status endpoints are disabled by feature flag.",
        )
        status = self._live_execution_service.get_status()
        return LiveExecutionStatusResponseSchema.model_validate(
            self._status_payload(status)
        )

    def get_live_execution_readiness(self) -> LiveExecutionReadinessResponseSchema:
        self._ensure_feature_enabled(
            "live_execution_status_enabled",
            code="live_execution_status_disabled",
            message="Live execution status endpoints are disabled by feature flag.",
        )
        snapshot = self._live_execution_service.get_readiness()
        return LiveExecutionReadinessResponseSchema.model_validate(
            {
                "generated_at": snapshot.generated_at,
                "broker_name": snapshot.broker_name.value,
                "enabled": snapshot.enabled,
                "submission_allowed": snapshot.submission_allowed,
                "configured": snapshot.configured,
                "state": snapshot.state.value,
                "message": snapshot.message,
                "manual_submission_ready": snapshot.manual_submission_ready,
                "confirmation_phrase": snapshot.confirmation_phrase,
                "checks": [
                    self._guard_check_payload(check) for check in snapshot.checks
                ],
            }
        )

    def validate_live_intent(
        self,
        request: LiveTradeIntentSchema,
    ) -> LiveIntentValidationResponseSchema:
        self._ensure_feature_enabled(
            "live_execution_status_enabled",
            code="live_execution_status_disabled",
            message="Live execution status endpoints are disabled by feature flag.",
        )
        intent = self._to_live_trade_intent(request)
        result = self._live_execution_service.validate_intent(intent)
        normalized = result.normalized_intent
        normalized_payload = None
        if normalized is not None:
            normalized_payload = {
                "instrument": {
                    "symbol": normalized.instrument.symbol,
                    "asset_class": normalized.instrument.asset_class.value,
                    "venue": normalized.instrument.venue,
                    "quote_currency": normalized.instrument.quote_currency,
                },
                "side": normalized.side.value,
                "order_type": normalized.order_type.value,
                "quantity": normalized.quantity,
                "limit_price": normalized.limit_price,
                "client_order_id": normalized.client_order_id,
                "metadata": dict(normalized.metadata),
            }
        return LiveIntentValidationResponseSchema.model_validate(
            {
                "accepted": result.accepted,
                "reasons": list(result.reasons),
                "normalized_intent": normalized_payload,
                "broker_payload_preview": (
                    None
                    if result.broker_payload_preview is None
                    else dict(result.broker_payload_preview)
                ),
            }
        )

    def submit_live_intent(
        self,
        request: LiveTradeIntentSchema,
    ) -> LiveSubmitResponseSchema:
        del request
        self._ensure_feature_enabled(
            "live_execution_status_enabled",
            code="live_execution_status_disabled",
            message="Live execution status endpoints are disabled by feature flag.",
        )
        self._ensure_feature_enabled(
            "live_execution_submit_enabled",
            code="live_execution_submit_disabled",
            message="Live execution submit endpoint is disabled by feature flag.",
        )
        raise APIError(
            status_code=409,
            code="live_execution_manual_required",
            message=(
                "Deprecated endpoint. Use /live-execution/manual-orders "
                "with manual confirmation fields."
            ),
        )

    def submit_manual_live_order(
        self,
        request: ManualLiveOrderRequestSchema,
    ) -> ManualLiveSubmitResponseSchema:
        self._ensure_feature_enabled(
            "live_execution_status_enabled",
            code="live_execution_status_disabled",
            message="Live execution status endpoints are disabled by feature flag.",
        )
        self._ensure_feature_enabled(
            "live_execution_submit_enabled",
            code="live_execution_submit_disabled",
            message="Live execution submit endpoint is disabled by feature flag.",
        )
        domain_request = ManualLiveOrderRequest(
            intent=self._to_live_trade_intent(request.intent),
            idempotency_key=request.idempotency_key,
            confirm_live_execution=request.confirm_live_execution,
            confirmation_text=request.confirmation_text,
            operator_id=request.operator_id,
            operator_note=request.operator_note,
        )
        result = self._live_execution_service.submit_manual_order(domain_request)
        return ManualLiveSubmitResponseSchema.model_validate(
            {
                "accepted": result.accepted,
                "status": result.status,
                "attempt_id": result.attempt_id,
                "broker_name": result.broker_name.value,
                "rejection_code": result.rejection_code,
                "rejection_message": result.rejection_message,
                "external_order_id": result.external_order_id,
                "broker_payload": (
                    None if result.broker_payload is None else dict(result.broker_payload)
                ),
                "guard_checks": [
                    self._guard_check_payload(check) for check in result.guard_checks
                ],
            }
        )

    def list_live_execution_attempts(
        self,
        limit: int = 25,
    ) -> LiveExecutionAttemptsResponseSchema:
        self._ensure_feature_enabled(
            "live_execution_status_enabled",
            code="live_execution_status_disabled",
            message="Live execution status endpoints are disabled by feature flag.",
        )
        attempts = self._live_execution_service.list_recent_attempts(limit=limit)
        return LiveExecutionAttemptsResponseSchema.model_validate(
            {
                "attempts": [
                    {
                        "attempt_id": attempt.attempt_id,
                        "timestamp": attempt.timestamp,
                        "broker_name": attempt.broker_name.value,
                        "idempotency_key": attempt.idempotency_key,
                        "request_summary": dict(attempt.request_summary),
                        "guard_checks": [
                            self._guard_check_payload(check)
                            for check in attempt.guard_checks
                        ],
                        "accepted": attempt.accepted,
                        "status": attempt.status,
                        "rejection_code": attempt.rejection_code,
                        "rejection_message": attempt.rejection_message,
                        "external_order_id": attempt.external_order_id,
                    }
                    for attempt in attempts
                ]
            }
        )

    def get_paper_state(self, *, fills_limit: int = 100) -> PaperStateResponseSchema:
        self._ensure_feature_enabled(
            "paper_trading_enabled",
            code="paper_trading_disabled",
            message="Paper trading endpoints are disabled by feature flag.",
        )
        snapshot = self._paper_trading_service.get_state(fills_limit=fills_limit)
        return serialize_paper_state(snapshot)

    def place_paper_order(
        self,
        request: PaperOrderRequestSchema,
    ) -> PaperOrderActionResponseSchema:
        self._ensure_feature_enabled(
            "paper_trading_enabled",
            code="paper_trading_disabled",
            message="Paper trading endpoints are disabled by feature flag.",
        )
        try:
            result = self._paper_trading_service.place_order(
                PaperOrderRequest(
                    instrument=self._to_instrument(request.instrument),
                    side=PaperOrderSide(request.side),
                    order_type=PaperOrderType(request.order_type),
                    quantity=request.quantity,
                    limit_price=request.limit_price,
                    reference_price=request.reference_price,
                    client_order_id=request.client_order_id,
                    metadata=dict(request.metadata),
                )
            )
            return serialize_paper_order_action(result)
        except ValueError as exc:
            raise APIError(
                status_code=400,
                code="paper_order_invalid",
                message=str(exc),
            ) from exc

    def cancel_paper_order(self, order_id: str) -> PaperCancelActionResponseSchema:
        self._ensure_feature_enabled(
            "paper_trading_enabled",
            code="paper_trading_disabled",
            message="Paper trading endpoints are disabled by feature flag.",
        )
        try:
            result = self._paper_trading_service.cancel_order(order_id)
            return serialize_paper_cancel_action(result)
        except KeyError as exc:
            raise APIError(
                status_code=404,
                code="paper_order_not_found",
                message=str(exc),
            ) from exc
        except ValueError as exc:
            raise APIError(
                status_code=400,
                code="paper_order_cancel_invalid",
                message=str(exc),
            ) from exc

    def process_paper_price_update(
        self,
        request: PriceUpdateRequestSchema,
    ) -> PaperPriceUpdateResponseSchema:
        self._ensure_feature_enabled(
            "paper_trading_enabled",
            code="paper_trading_disabled",
            message="Paper trading endpoints are disabled by feature flag.",
        )
        try:
            result = self._paper_trading_service.process_price_update(
                PriceUpdate(
                    instrument=self._to_instrument(request.instrument),
                    price=request.price,
                    timestamp=(
                        datetime.now(timezone.utc)
                        if request.timestamp is None
                        else request.timestamp
                    ),
                    source=request.source,
                )
            )
            return serialize_paper_price_update(result)
        except ValueError as exc:
            raise APIError(
                status_code=400,
                code="paper_price_invalid",
                message=str(exc),
            ) from exc

    def submit_paper_signal_intent(
        self,
        request: PaperSignalIntentRequestSchema,
    ) -> PaperOrderActionResponseSchema:
        self._ensure_feature_enabled(
            "paper_trading_enabled",
            code="paper_trading_disabled",
            message="Paper trading endpoints are disabled by feature flag.",
        )
        try:
            result = self._paper_trading_service.submit_signal_intent(
                PaperSignalIntent(
                    instrument=self._to_instrument(request.instrument),
                    direction=PaperSignalDirection(request.direction),
                    quantity=request.quantity,
                    reference_price=request.reference_price,
                    client_order_id=request.client_order_id,
                    metadata=dict(request.metadata),
                )
            )
            return serialize_paper_order_action(result)
        except ValueError as exc:
            raise APIError(
                status_code=400,
                code="paper_signal_invalid",
                message=str(exc),
            ) from exc

    def reset_paper_account(
        self,
        request: PaperResetRequestSchema,
    ) -> PaperStateResponseSchema:
        self._ensure_feature_enabled(
            "paper_trading_enabled",
            code="paper_trading_disabled",
            message="Paper trading endpoints are disabled by feature flag.",
        )
        config = PaperAccountConfig(
            account_id=request.account_id or self._settings.paper_default_account_id,
            base_currency=request.base_currency or self._settings.paper_default_base_currency,
            initial_cash=(
                self._settings.paper_default_initial_cash
                if request.initial_cash is None
                else request.initial_cash
            ),
            allow_short=(
                self._settings.paper_default_allow_short
                if request.allow_short is None
                else request.allow_short
            ),
            default_spread_bps=(
                self._settings.paper_default_spread_bps
                if request.default_spread_bps is None
                else request.default_spread_bps
            ),
            default_slippage_bps=(
                self._settings.paper_default_slippage_bps
                if request.default_slippage_bps is None
                else request.default_slippage_bps
            ),
            commission_bps=(
                self._settings.paper_default_commission_bps
                if request.commission_bps is None
                else request.commission_bps
            ),
            commission_fixed=(
                self._settings.paper_default_commission_fixed
                if request.commission_fixed is None
                else request.commission_fixed
            ),
        )
        snapshot = self._paper_trading_service.reset_account(config=config)
        return serialize_paper_state(snapshot)

    @property
    def _history_root(self) -> Path:
        return Path(self._settings.default_run_output_dir)

    def _history_summary_payload(self, run_id: str) -> dict[str, Any]:
        try:
            return get_run_summary(self._history_root, run_id)
        except ValueError as exc:
            raise APIError(
                status_code=400,
                code="invalid_run_id",
                message=str(exc),
            ) from exc
        except FileNotFoundError as exc:
            raise APIError(
                status_code=404,
                code="run_summary_not_found",
                message=str(exc),
            ) from exc
        except (OSError, TypeError, ValueError) as exc:
            raise APIError(
                status_code=500,
                code="run_summary_read_error",
                message=f"Failed to read summary for run_id '{run_id}'",
            ) from exc

    def _ensure_feature_enabled(self, flag_name: str, *, code: str, message: str) -> None:
        flags = self._app_settings.feature_flags
        if not getattr(flags, flag_name):
            raise APIError(
                status_code=403,
                code=code,
                message=message,
            )

    @staticmethod
    def _guard_check_payload(check: GuardCheckResult) -> dict[str, Any]:
        return {
            "name": check.name,
            "passed": check.passed,
            "code": check.code,
            "message": check.message,
        }

    @staticmethod
    def _status_payload(status) -> dict[str, Any]:  # noqa: ANN001
        return {
            "broker_name": status.broker_name.value,
            "configured": status.configured,
            "enabled": status.enabled,
            "submission_allowed": status.submission_allowed,
            "state": status.state.value,
            "message": status.message,
            "capabilities": {
                "supported_asset_classes": [
                    asset_class.value
                    for asset_class in status.capabilities.supported_asset_classes
                ],
                "supported_order_types": [
                    order_type.value
                    for order_type in status.capabilities.supported_order_types
                ],
                "supported_order_sides": [
                    side.value for side in status.capabilities.supported_order_sides
                ],
                "supports_short": status.capabilities.supports_short,
                "supports_cancel": status.capabilities.supports_cancel,
                "supports_submit": status.capabilities.supports_submit,
            },
        }

    @staticmethod
    def _to_live_trade_intent(schema: LiveTradeIntentSchema) -> LiveTradeIntent:
        return LiveTradeIntent(
            instrument=Instrument(
                symbol=schema.instrument.symbol,
                asset_class=schema.instrument.asset_class,
                venue=schema.instrument.venue,
                quote_currency=schema.instrument.quote_currency,
            ),
            side=LiveOrderSide(schema.side),
            order_type=LiveOrderType(schema.order_type),
            quantity=schema.quantity,
            limit_price=schema.limit_price,
            client_order_id=schema.client_order_id,
            metadata=dict(schema.metadata),
        )

    @staticmethod
    def _map_live_execution_error(exc: Exception) -> APIError:
        if isinstance(exc, LiveExecutionDisabledError):
            return APIError(
                status_code=409,
                code="live_execution_disabled",
                message=str(exc),
            )
        if isinstance(exc, LiveExecutionNotConfiguredError):
            return APIError(
                status_code=409,
                code="live_execution_not_configured",
                message=str(exc),
            )
        if isinstance(exc, LiveExecutionUnsupportedCapabilityError):
            return APIError(
                status_code=400,
                code="live_execution_unsupported",
                message=str(exc),
            )
        if isinstance(exc, LiveExecutionAdapterTimeoutError):
            return APIError(
                status_code=504,
                code="live_execution_timeout",
                message=str(exc),
            )
        return APIError(
            status_code=502,
            code="live_execution_adapter_error",
            message=str(exc),
        )

    @staticmethod
    def _to_instrument(schema) -> Instrument:  # noqa: ANN001
        return Instrument(
            symbol=schema.symbol,
            asset_class=schema.asset_class,
            venue=schema.venue,
            quote_currency=schema.quote_currency,
        )

    @staticmethod
    def _to_candle(candle: CandleSchema) -> Candle:
        return Candle(
            timestamp=candle.timestamp,
            open=candle.open,
            high=candle.high,
            low=candle.low,
            close=candle.close,
            volume=candle.volume,
        )

    def _to_candle_source(
        self,
        candle_source: InlineCandleSourceSchema | MarketDataFetchSourceSchema,
    ) -> InlineCandleSource | MarketDataFetchSource:
        if isinstance(candle_source, InlineCandleSourceSchema):
            return InlineCandleSource(
                candles=tuple(self._to_candle(c) for c in candle_source.candles)
            )
        return MarketDataFetchSource(
            provider_name=candle_source.provider_name,
            start=candle_source.start,
            end=candle_source.end,
            limit=candle_source.limit,
        )

    def _to_run_config(self, config: RunConfigSchema) -> ResearchRunConfig:
        persist_summary = config.persist_summary
        output_dir = config.output_dir
        if output_dir is None and persist_summary:
            output_dir = self._settings.default_run_output_dir
        return ResearchRunConfig(
            run_id=config.run_id,
            run_name=config.run_name,
            random_seed=config.random_seed,
            strict_failures=config.strict_failures,
            persist_summary=persist_summary,
            output_dir=output_dir,
            metadata=dict(config.metadata),
        )

    def _to_strategy_spec(self, schema) -> StrategyWorkflowSpec:  # noqa: ANN001
        return StrategyWorkflowSpec(
            strategy_id=schema.strategy_id,
            backtest_config=schema.backtest_config.to_domain(),
            diagnostics_config=(
                None
                if schema.diagnostics_config is None
                else schema.diagnostics_config.to_domain()
            ),
        )

    @staticmethod
    def _to_feature_spec(schema) -> FeatureSpec:  # noqa: ANN001
        return FeatureSpec(
            return_windows=schema.return_windows,
            log_return_windows=schema.log_return_windows,
            volatility_windows=schema.volatility_windows,
            momentum_windows=schema.momentum_windows,
            sma_windows=schema.sma_windows,
            sma_crossover_pairs=schema.sma_crossover_pairs,
            atr_windows=schema.atr_windows,
            zscore_windows=schema.zscore_windows,
            include_candle_structure=schema.include_candle_structure,
            include_volume_features=schema.include_volume_features,
            volume_zscore_windows=schema.volume_zscore_windows,
        )

    @staticmethod
    def _to_split_spec(schema: SplitSpecSchema | None) -> SplitSpec | None:
        if schema is None:
            return None
        return SplitSpec(
            train_fraction=schema.train_fraction,
            validation_fraction=schema.validation_fraction,
            test_fraction=schema.test_fraction,
            gap_bars=schema.gap_bars,
        )

    @staticmethod
    def _to_label_specs(label_specs: list[Any]) -> tuple[Any, ...]:
        out: list[Any] = []
        for label_spec in label_specs:
            if isinstance(label_spec, FutureReturnLabelSpecSchema):
                out.append(
                    FutureReturnLabelSpec(
                        horizon_bars=label_spec.horizon_bars,
                        name=label_spec.name,
                        price_field=label_spec.price_field,
                    )
                )
                continue
            if isinstance(label_spec, DirectionLabelSpecSchema):
                out.append(
                    DirectionLabelSpec(
                        horizon_bars=label_spec.horizon_bars,
                        threshold=label_spec.threshold,
                        name=label_spec.name,
                        price_field=label_spec.price_field,
                    )
                )
                continue
            raise ValueError(f"Unsupported label spec schema: {type(label_spec)!r}")
        return tuple(out)

    @staticmethod
    def _to_model_specs(model_specs: list[ModelSpecSchema]) -> tuple[ModelSpec, ...]:
        return tuple(
            ModelSpec(
                model_id=spec.model_id,
                family=spec.family,
                hyperparameters=spec.hyperparameters,
                requires_optional_dependency=spec.requires_optional_dependency,
            )
            for spec in model_specs
        )

    def _to_training_config(self, schema) -> TrainingConfig:  # noqa: ANN001
        return TrainingConfig(
            random_seed=schema.random_seed,
            optional_dependency_policy=OptionalDependencyPolicy(
                schema.optional_dependency_policy
            ),
            fallback_split_spec=SplitSpec(
                train_fraction=schema.fallback_split_spec.train_fraction,
                validation_fraction=schema.fallback_split_spec.validation_fraction,
                test_fraction=schema.fallback_split_spec.test_fraction,
                gap_bars=schema.fallback_split_spec.gap_bars,
            ),
            standardize_linear_models=schema.standardize_linear_models,
            minimum_train_rows=schema.minimum_train_rows,
        )

    def _to_ml_spec(self, schema) -> MLWorkflowSpec:  # noqa: ANN001
        return MLWorkflowSpec(
            feature_spec=self._to_feature_spec(schema.feature_spec),
            label_specs=self._to_label_specs(schema.label_specs),
            split_spec=self._to_split_spec(schema.split_spec),
            missing_volume_policy=MissingVolumePolicy(schema.missing_volume_policy),
            missing_value_policy=MissingValuePolicy(schema.missing_value_policy),
            task_type=TaskType(schema.task_type),
            target_label=schema.target_label,
            model_specs=self._to_model_specs(schema.model_specs),
            training_config=self._to_training_config(schema.training_config),
        )
