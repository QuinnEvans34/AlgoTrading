"""Route registration for the API layer."""

from .compare import router as compare_router
from .health import router as health_router
from .history import router as history_router
from .live_execution import router as live_execution_router
from .market_data import router as market_data_router
from .metadata import router as metadata_router
from .paper_trading import router as paper_trading_router
from .research import router as research_router
from .results import router as results_router
from .settings import router as settings_router

__all__ = [
    "health_router",
    "metadata_router",
    "market_data_router",
    "research_router",
    "results_router",
    "history_router",
    "compare_router",
    "paper_trading_router",
    "live_execution_router",
    "settings_router",
]
