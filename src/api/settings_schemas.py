"""Pydantic schemas for safe system settings/status endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StrictSettingsModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RuntimeStatusSchema(StrictSettingsModel):
    app_name: str
    api_prefix: str
    host: str
    port: int
    cors_allowed_origins: list[str]
    generated_at: datetime


class FeatureFlagsSchema(StrictSettingsModel):
    research_api_enabled: bool
    history_api_enabled: bool
    compare_api_enabled: bool
    paper_trading_enabled: bool
    live_execution_status_enabled: bool
    live_execution_submit_enabled: bool


class StorageStatusSchema(StrictSettingsModel):
    run_output_dir: str
    paper_trading_dir: str


class PaperDefaultsStatusSchema(StrictSettingsModel):
    account_id: str
    base_currency: str
    initial_cash: float
    allow_short: bool
    spread_bps: float
    slippage_bps: float
    commission_bps: float
    commission_fixed: float


class LiveSafetyStatusSchema(StrictSettingsModel):
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


class ProviderStatusSchema(StrictSettingsModel):
    oanda_market_data_enabled: bool
    oanda_market_data_configured: bool
    live_oanda_configured: bool


class SystemSettingsResponseSchema(StrictSettingsModel):
    runtime: RuntimeStatusSchema
    feature_flags: FeatureFlagsSchema
    storage: StorageStatusSchema
    paper_defaults: PaperDefaultsStatusSchema
    live_safety: LiveSafetyStatusSchema
    providers: ProviderStatusSchema
