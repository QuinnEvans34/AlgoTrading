"""FastAPI application entrypoint for backend research APIs."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import APISettings
from .dependencies import get_settings
from .errors import install_exception_handlers
from .routes import (
    compare_router,
    health_router,
    history_router,
    live_execution_router,
    market_data_router,
    metadata_router,
    paper_trading_router,
    research_router,
    results_router,
    settings_router,
)


def create_app(settings: APISettings | None = None) -> FastAPI:
    cfg = settings or APISettings.from_env()
    app = FastAPI(
        title=cfg.app_name,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(cfg.cors_allowed_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.dependency_overrides[get_settings] = lambda: cfg
    install_exception_handlers(app)
    app.include_router(health_router, prefix=cfg.api_prefix)
    app.include_router(metadata_router, prefix=cfg.api_prefix)
    app.include_router(market_data_router, prefix=cfg.api_prefix)
    app.include_router(research_router, prefix=cfg.api_prefix)
    app.include_router(results_router, prefix=cfg.api_prefix)
    app.include_router(history_router, prefix=cfg.api_prefix)
    app.include_router(compare_router, prefix=cfg.api_prefix)
    app.include_router(paper_trading_router, prefix=cfg.api_prefix)
    app.include_router(live_execution_router, prefix=cfg.api_prefix)
    app.include_router(settings_router, prefix=cfg.api_prefix)
    return app


app = create_app()
