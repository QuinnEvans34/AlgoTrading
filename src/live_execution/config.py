"""Configuration contract for the live-execution boundary."""

from __future__ import annotations

from dataclasses import dataclass

from config import AppSettings

from .contracts import LiveBrokerName


def _parse_broker_name(raw: str | None) -> LiveBrokerName:
    if raw is None:
        return LiveBrokerName.NULL
    candidate = raw.strip().lower()
    try:
        return LiveBrokerName(candidate)
    except ValueError:
        return LiveBrokerName.NULL


@dataclass(frozen=True)
class LiveExecutionSettings:
    enabled: bool = False
    allow_order_submission: bool = False
    submit_feature_enabled: bool = False
    status_feature_enabled: bool = True
    broker_name: LiveBrokerName = LiveBrokerName.NULL
    request_timeout_seconds: int = 10
    confirmation_phrase: str = "EXECUTE LIVE ORDER"
    attempt_log_path: str = "artifacts/live_execution/attempts.jsonl"
    oanda_api_token: str | None = None
    oanda_account_id: str | None = None
    oanda_environment: str = "practice"

    @classmethod
    def from_app_settings(cls, app_settings: AppSettings) -> "LiveExecutionSettings":
        live = app_settings.live_safety
        return cls(
            enabled=live.enabled,
            allow_order_submission=live.allow_order_submission,
            submit_feature_enabled=app_settings.feature_flags.live_execution_submit_enabled,
            status_feature_enabled=app_settings.feature_flags.live_execution_status_enabled,
            broker_name=_parse_broker_name(live.broker_name),
            request_timeout_seconds=live.request_timeout_seconds,
            confirmation_phrase=live.confirmation_phrase,
            attempt_log_path=live.attempt_log_path,
            oanda_api_token=live.oanda_api_token,
            oanda_account_id=live.oanda_account_id,
            oanda_environment=live.oanda_environment,
        )

    @classmethod
    def from_env(cls) -> "LiveExecutionSettings":
        return cls.from_app_settings(AppSettings.from_env())
