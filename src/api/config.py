"""Compatibility API settings wrapper backed by centralized AppSettings."""

from __future__ import annotations

from dataclasses import dataclass

from config import (
    APIServerSettings,
    AppSettings,
    FeatureFlags,
    LiveSafetySettings,
    PaperTradingDefaults,
    ProviderSettings,
    StorageSettings,
)


@dataclass(frozen=True)
class APISettings:
    app_name: str = "capstone-research-api"
    api_prefix: str = "/api/v1"
    host: str = "127.0.0.1"
    port: int = 8000
    default_strict_failures: bool = True
    default_persist_summary: bool = False
    default_run_output_dir: str = "artifacts/research_runs"
    default_paper_trading_dir: str = "artifacts/paper_trading"
    paper_default_account_id: str = "paper-main"
    paper_default_base_currency: str = "USD"
    paper_default_initial_cash: float = 100_000.0
    paper_default_allow_short: bool = False
    paper_default_spread_bps: float = 0.0
    paper_default_slippage_bps: float = 0.0
    paper_default_commission_bps: float = 0.0
    paper_default_commission_fixed: float = 0.0
    live_execution_enabled: bool = False
    live_execution_allow_order_submission: bool = False
    live_execution_broker: str = "null"
    live_execution_request_timeout_seconds: int = 10
    live_execution_confirmation_phrase: str = "EXECUTE LIVE ORDER"
    live_execution_attempt_log_path: str = "artifacts/live_execution/attempts.jsonl"
    live_oanda_api_token: str | None = None
    live_oanda_account_id: str | None = None
    live_oanda_environment: str = "practice"
    cors_allowed_origins: tuple[str, ...] = (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    )
    enable_oanda_provider: bool = False
    oanda_api_token: str | None = None
    oanda_account_id: str | None = None
    oanda_environment: str = "practice"
    oanda_timeout_seconds: int = 15
    feature_research_api_enabled: bool = True
    feature_history_api_enabled: bool = True
    feature_compare_api_enabled: bool = True
    feature_paper_trading_enabled: bool = True
    feature_live_execution_status_enabled: bool = True
    feature_live_execution_submit_enabled: bool = False

    @classmethod
    def from_env(cls) -> "APISettings":
        return cls.from_app_settings(AppSettings.from_env())

    @classmethod
    def from_app_settings(cls, settings: AppSettings) -> "APISettings":
        return cls(
            app_name=settings.api.app_name,
            api_prefix=settings.api.api_prefix,
            host=settings.api.host,
            port=settings.api.port,
            default_strict_failures=settings.default_strict_failures,
            default_persist_summary=settings.default_persist_summary,
            default_run_output_dir=settings.storage.run_output_dir,
            default_paper_trading_dir=settings.storage.paper_trading_dir,
            paper_default_account_id=settings.paper_defaults.account_id,
            paper_default_base_currency=settings.paper_defaults.base_currency,
            paper_default_initial_cash=settings.paper_defaults.initial_cash,
            paper_default_allow_short=settings.paper_defaults.allow_short,
            paper_default_spread_bps=settings.paper_defaults.spread_bps,
            paper_default_slippage_bps=settings.paper_defaults.slippage_bps,
            paper_default_commission_bps=settings.paper_defaults.commission_bps,
            paper_default_commission_fixed=settings.paper_defaults.commission_fixed,
            live_execution_enabled=settings.live_safety.enabled,
            live_execution_allow_order_submission=(
                settings.live_safety.allow_order_submission
            ),
            live_execution_broker=settings.live_safety.broker_name,
            live_execution_request_timeout_seconds=(
                settings.live_safety.request_timeout_seconds
            ),
            live_execution_confirmation_phrase=settings.live_safety.confirmation_phrase,
            live_execution_attempt_log_path=settings.live_safety.attempt_log_path,
            live_oanda_api_token=settings.live_safety.oanda_api_token,
            live_oanda_account_id=settings.live_safety.oanda_account_id,
            live_oanda_environment=settings.live_safety.oanda_environment,
            cors_allowed_origins=settings.api.cors_allowed_origins,
            enable_oanda_provider=settings.provider_settings.enable_oanda_provider,
            oanda_api_token=settings.provider_settings.oanda_api_token,
            oanda_account_id=settings.provider_settings.oanda_account_id,
            oanda_environment=settings.provider_settings.oanda_environment,
            oanda_timeout_seconds=settings.provider_settings.oanda_timeout_seconds,
            feature_research_api_enabled=settings.feature_flags.research_api_enabled,
            feature_history_api_enabled=settings.feature_flags.history_api_enabled,
            feature_compare_api_enabled=settings.feature_flags.compare_api_enabled,
            feature_paper_trading_enabled=settings.feature_flags.paper_trading_enabled,
            feature_live_execution_status_enabled=(
                settings.feature_flags.live_execution_status_enabled
            ),
            feature_live_execution_submit_enabled=(
                settings.feature_flags.live_execution_submit_enabled
            ),
        )

    def to_app_settings(self) -> AppSettings:
        return AppSettings(
            api=APIServerSettings(
                app_name=self.app_name,
                api_prefix=self.api_prefix,
                host=self.host,
                port=self.port,
                cors_allowed_origins=self.cors_allowed_origins,
            ),
            storage=StorageSettings(
                run_output_dir=self.default_run_output_dir,
                paper_trading_dir=self.default_paper_trading_dir,
            ),
            paper_defaults=PaperTradingDefaults(
                account_id=self.paper_default_account_id,
                base_currency=self.paper_default_base_currency,
                initial_cash=self.paper_default_initial_cash,
                allow_short=self.paper_default_allow_short,
                spread_bps=self.paper_default_spread_bps,
                slippage_bps=self.paper_default_slippage_bps,
                commission_bps=self.paper_default_commission_bps,
                commission_fixed=self.paper_default_commission_fixed,
            ),
            live_safety=LiveSafetySettings(
                enabled=self.live_execution_enabled,
                allow_order_submission=self.live_execution_allow_order_submission,
                broker_name=self.live_execution_broker,
                request_timeout_seconds=self.live_execution_request_timeout_seconds,
                confirmation_phrase=self.live_execution_confirmation_phrase,
                attempt_log_path=self.live_execution_attempt_log_path,
                oanda_api_token=self.live_oanda_api_token,
                oanda_account_id=self.live_oanda_account_id,
                oanda_environment=self.live_oanda_environment,
            ),
            provider_settings=ProviderSettings(
                enable_oanda_provider=self.enable_oanda_provider,
                oanda_api_token=self.oanda_api_token,
                oanda_account_id=self.oanda_account_id,
                oanda_environment=self.oanda_environment,
                oanda_timeout_seconds=self.oanda_timeout_seconds,
            ),
            feature_flags=FeatureFlags(
                research_api_enabled=self.feature_research_api_enabled,
                history_api_enabled=self.feature_history_api_enabled,
                compare_api_enabled=self.feature_compare_api_enabled,
                paper_trading_enabled=self.feature_paper_trading_enabled,
                live_execution_status_enabled=self.feature_live_execution_status_enabled,
                live_execution_submit_enabled=self.feature_live_execution_submit_enabled,
            ),
            default_strict_failures=self.default_strict_failures,
            default_persist_summary=self.default_persist_summary,
        )
