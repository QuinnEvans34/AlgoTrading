"""Feature flag model and environment loading."""

from __future__ import annotations

from dataclasses import dataclass

from .environment import env_bool


@dataclass(frozen=True)
class FeatureFlags:
    research_api_enabled: bool = True
    history_api_enabled: bool = True
    compare_api_enabled: bool = True
    paper_trading_enabled: bool = True
    live_execution_status_enabled: bool = True
    live_execution_submit_enabled: bool = False

    @classmethod
    def from_env(cls) -> "FeatureFlags":
        return cls(
            research_api_enabled=env_bool("FEATURE_RESEARCH_API_ENABLED", True),
            history_api_enabled=env_bool("FEATURE_HISTORY_API_ENABLED", True),
            compare_api_enabled=env_bool("FEATURE_COMPARE_API_ENABLED", True),
            paper_trading_enabled=env_bool("FEATURE_PAPER_TRADING_ENABLED", True),
            live_execution_status_enabled=env_bool(
                "FEATURE_LIVE_EXECUTION_STATUS_ENABLED",
                True,
            ),
            live_execution_submit_enabled=env_bool(
                "FEATURE_LIVE_EXECUTION_SUBMIT_ENABLED",
                False,
            ),
        )

