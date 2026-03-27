"""Safe runtime settings projection for API/frontend visibility."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from .app_settings import AppSettings


@dataclass(frozen=True)
class SafeProviderStatus:
    oanda_market_data_enabled: bool
    oanda_market_data_configured: bool
    live_oanda_configured: bool


@dataclass(frozen=True)
class SafeLiveSafetyStatus:
    enabled: bool
    allow_order_submission: bool
    submit_feature_enabled: bool
    effective_submission_enabled: bool
    broker_name: str
    request_timeout_seconds: int
    confirmation_phrase: str
    attempt_log_path: str
    credentials_configured: bool
    environment: str


@dataclass(frozen=True)
class SafePaperDefaultsStatus:
    account_id: str
    base_currency: str
    initial_cash: float
    allow_short: bool
    spread_bps: float
    slippage_bps: float
    commission_bps: float
    commission_fixed: float


@dataclass(frozen=True)
class SafeStorageStatus:
    run_output_dir: str
    paper_trading_dir: str


@dataclass(frozen=True)
class SafeRuntimeStatus:
    app_name: str
    api_prefix: str
    host: str
    port: int
    cors_allowed_origins: tuple[str, ...]
    generated_at: datetime


@dataclass(frozen=True)
class SafeSystemSettingsSnapshot:
    runtime: SafeRuntimeStatus
    feature_flags: dict[str, bool]
    storage: SafeStorageStatus
    paper_defaults: SafePaperDefaultsStatus
    live_safety: SafeLiveSafetyStatus
    providers: SafeProviderStatus

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["runtime"]["generated_at"] = self.runtime.generated_at.isoformat()
        return payload


def build_safe_system_settings_snapshot(app_settings: AppSettings) -> SafeSystemSettingsSnapshot:
    provider = app_settings.provider_settings
    live = app_settings.live_safety
    flags = app_settings.feature_flags
    live_credentials_configured = bool(live.oanda_api_token and live.oanda_account_id)
    return SafeSystemSettingsSnapshot(
        runtime=SafeRuntimeStatus(
            app_name=app_settings.api.app_name,
            api_prefix=app_settings.api.api_prefix,
            host=app_settings.api.host,
            port=app_settings.api.port,
            cors_allowed_origins=app_settings.api.cors_allowed_origins,
            generated_at=datetime.now(timezone.utc),
        ),
        feature_flags={
            "research_api_enabled": flags.research_api_enabled,
            "history_api_enabled": flags.history_api_enabled,
            "compare_api_enabled": flags.compare_api_enabled,
            "paper_trading_enabled": flags.paper_trading_enabled,
            "live_execution_status_enabled": flags.live_execution_status_enabled,
            "live_execution_submit_enabled": flags.live_execution_submit_enabled,
        },
        storage=SafeStorageStatus(
            run_output_dir=app_settings.storage.run_output_dir,
            paper_trading_dir=app_settings.storage.paper_trading_dir,
        ),
        paper_defaults=SafePaperDefaultsStatus(
            account_id=app_settings.paper_defaults.account_id,
            base_currency=app_settings.paper_defaults.base_currency,
            initial_cash=app_settings.paper_defaults.initial_cash,
            allow_short=app_settings.paper_defaults.allow_short,
            spread_bps=app_settings.paper_defaults.spread_bps,
            slippage_bps=app_settings.paper_defaults.slippage_bps,
            commission_bps=app_settings.paper_defaults.commission_bps,
            commission_fixed=app_settings.paper_defaults.commission_fixed,
        ),
        live_safety=SafeLiveSafetyStatus(
            enabled=live.enabled,
            allow_order_submission=live.allow_order_submission,
            submit_feature_enabled=flags.live_execution_submit_enabled,
            effective_submission_enabled=(
                live.enabled
                and live.allow_order_submission
                and flags.live_execution_submit_enabled
            ),
            broker_name=live.broker_name,
            request_timeout_seconds=live.request_timeout_seconds,
            confirmation_phrase=live.confirmation_phrase,
            attempt_log_path=live.attempt_log_path,
            credentials_configured=live_credentials_configured,
            environment=live.oanda_environment,
        ),
        providers=SafeProviderStatus(
            oanda_market_data_enabled=provider.enable_oanda_provider,
            oanda_market_data_configured=bool(provider.oanda_api_token),
            live_oanda_configured=live_credentials_configured,
        ),
    )
