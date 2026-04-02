"""Centralized runtime application settings."""

from __future__ import annotations

from dataclasses import dataclass

from .environment import env_bool, env_csv, env_float, env_int, env_path, env_str
from .feature_flags import FeatureFlags


@dataclass(frozen=True)
class APIServerSettings:
    app_name: str = "capstone-research-api"
    api_prefix: str = "/api/v1"
    host: str = "127.0.0.1"
    port: int = 8000
    cors_allowed_origins: tuple[str, ...] = (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    )


@dataclass(frozen=True)
class StorageSettings:
    run_output_dir: str = "artifacts/research_runs"
    paper_trading_dir: str = "artifacts/paper_trading"


@dataclass(frozen=True)
class DatabaseSettings:
    enabled: bool = False
    url: str | None = None
    echo: bool = False


@dataclass(frozen=True)
class PaperTradingDefaults:
    account_id: str = "paper-main"
    base_currency: str = "USD"
    initial_cash: float = 100_000.0
    allow_short: bool = False
    spread_bps: float = 0.0
    slippage_bps: float = 0.0
    commission_bps: float = 0.0
    commission_fixed: float = 0.0


@dataclass(frozen=True)
class LiveSafetySettings:
    enabled: bool = False
    allow_order_submission: bool = False
    broker_name: str = "null"
    request_timeout_seconds: int = 10
    confirmation_phrase: str = "EXECUTE LIVE ORDER"
    attempt_log_path: str = "artifacts/live_execution/attempts.jsonl"
    oanda_api_token: str | None = None
    oanda_account_id: str | None = None
    oanda_environment: str = "practice"


@dataclass(frozen=True)
class ProviderSettings:
    enable_oanda_provider: bool = False
    oanda_api_token: str | None = None
    oanda_account_id: str | None = None
    oanda_environment: str = "practice"
    oanda_timeout_seconds: int = 15


@dataclass(frozen=True)
class AIResearchSettings:
    enabled: bool = False
    openai_api_key: str | None = None
    openai_model: str | None = None
    openai_base_url: str | None = None
    timeout_seconds: int = 30


@dataclass(frozen=True)
class AppSettings:
    api: APIServerSettings = APIServerSettings()
    storage: StorageSettings = StorageSettings()
    database: DatabaseSettings = DatabaseSettings()
    paper_defaults: PaperTradingDefaults = PaperTradingDefaults()
    live_safety: LiveSafetySettings = LiveSafetySettings()
    provider_settings: ProviderSettings = ProviderSettings()
    ai_research: AIResearchSettings = AIResearchSettings()
    feature_flags: FeatureFlags = FeatureFlags()
    default_strict_failures: bool = True
    default_persist_summary: bool = False

    @classmethod
    def from_env(cls) -> "AppSettings":
        return cls(
            api=APIServerSettings(
                app_name=env_str("API_APP_NAME", "capstone-research-api"),
                api_prefix=env_str("API_PREFIX", "/api/v1"),
                host=env_str("API_HOST", "127.0.0.1"),
                port=env_int("API_PORT", 8000),
                cors_allowed_origins=env_csv(
                    "API_CORS_ALLOWED_ORIGINS",
                    ("http://localhost:5173", "http://127.0.0.1:5173"),
                ),
            ),
            storage=StorageSettings(
                run_output_dir=env_path(
                    "API_DEFAULT_RUN_OUTPUT_DIR",
                    "artifacts/research_runs",
                ),
                paper_trading_dir=env_path(
                    "API_DEFAULT_PAPER_TRADING_DIR",
                    "artifacts/paper_trading",
                ),
            ),
            database=DatabaseSettings(
                enabled=env_bool("DATABASE_ENABLED", False),
                url=env_str("DATABASE_URL", "") or None,
                echo=env_bool("DATABASE_ECHO", False),
            ),
            paper_defaults=PaperTradingDefaults(
                account_id=env_str("API_PAPER_DEFAULT_ACCOUNT_ID", "paper-main"),
                base_currency=env_str("API_PAPER_DEFAULT_BASE_CURRENCY", "USD"),
                initial_cash=env_float("API_PAPER_DEFAULT_INITIAL_CASH", 100_000.0),
                allow_short=env_bool("API_PAPER_DEFAULT_ALLOW_SHORT", False),
                spread_bps=env_float("API_PAPER_DEFAULT_SPREAD_BPS", 0.0),
                slippage_bps=env_float("API_PAPER_DEFAULT_SLIPPAGE_BPS", 0.0),
                commission_bps=env_float("API_PAPER_DEFAULT_COMMISSION_BPS", 0.0),
                commission_fixed=env_float("API_PAPER_DEFAULT_COMMISSION_FIXED", 0.0),
            ),
            live_safety=LiveSafetySettings(
                enabled=env_bool("LIVE_EXECUTION_ENABLED", False),
                allow_order_submission=env_bool(
                    "LIVE_EXECUTION_ALLOW_ORDER_SUBMISSION",
                    False,
                ),
                broker_name=env_str("LIVE_EXECUTION_BROKER", "null"),
                request_timeout_seconds=env_int(
                    "LIVE_EXECUTION_REQUEST_TIMEOUT_SECONDS",
                    10,
                ),
                confirmation_phrase=env_str(
                    "LIVE_EXECUTION_CONFIRMATION_PHRASE",
                    "EXECUTE LIVE ORDER",
                ),
                attempt_log_path=env_path(
                    "LIVE_EXECUTION_ATTEMPT_LOG_PATH",
                    "artifacts/live_execution/attempts.jsonl",
                ),
                oanda_api_token=env_str("LIVE_OANDA_API_TOKEN", "")
                or None,
                oanda_account_id=env_str("LIVE_OANDA_ACCOUNT_ID", "")
                or None,
                oanda_environment=env_str("LIVE_OANDA_ENVIRONMENT", "practice"),
            ),
            provider_settings=ProviderSettings(
                enable_oanda_provider=env_bool("API_ENABLE_OANDA_PROVIDER", False),
                oanda_api_token=env_str("OANDA_API_TOKEN", "") or None,
                oanda_account_id=env_str("OANDA_ACCOUNT_ID", "") or None,
                oanda_environment=env_str("OANDA_ENVIRONMENT", "practice"),
                oanda_timeout_seconds=env_int("OANDA_TIMEOUT_SECONDS", 15),
            ),
            ai_research=AIResearchSettings(
                enabled=env_bool("AI_RESEARCH_ENABLED", False),
                openai_api_key=env_str("OPENAI_API_KEY", "") or None,
                openai_model=env_str("OPENAI_MODEL", "") or None,
                openai_base_url=env_str("OPENAI_BASE_URL", "") or None,
                timeout_seconds=env_int("AI_RESEARCH_TIMEOUT_SECONDS", 30),
            ),
            feature_flags=FeatureFlags.from_env(),
            default_strict_failures=env_bool("API_DEFAULT_STRICT_FAILURES", True),
            default_persist_summary=env_bool("API_DEFAULT_PERSIST_SUMMARY", False),
        )
