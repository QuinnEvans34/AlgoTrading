"""SQLAlchemy ORM models for durable metadata persistence."""

from __future__ import annotations

from typing import Any
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for persistence models."""


class ResearchRunMetadataModel(Base):
    __tablename__ = "research_run_metadata"
    __table_args__ = (
        Index("ix_research_run_metadata_started_at", "started_at"),
        Index(
            "ix_research_run_metadata_workflow_started_at",
            "workflow_type",
            "started_at",
        ),
        Index(
            "ix_research_run_metadata_status_started_at",
            "status",
            "started_at",
        ),
        Index("ix_research_run_metadata_instrument_symbol", "instrument_symbol"),
    )

    run_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    run_name: Mapped[str] = mapped_column(String(255), nullable=False)
    workflow_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    instrument_symbol: Mapped[str] = mapped_column(String(64), nullable=False)
    asset_class: Mapped[str | None] = mapped_column(String(64), nullable=True)
    interval: Mapped[str | None] = mapped_column(String(32), nullable=True)
    candle_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    candle_source_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    has_strategy: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_ml: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    strategy_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    total_trades: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_return_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_net_pnl: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_drawdown_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    sharpe_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    ml_task_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ml_target_label: Mapped[str | None] = mapped_column(String(128), nullable=True)
    ml_best_model_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    ml_primary_metric_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    ml_best_validation_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    ml_best_test_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    ml_model_count_executed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ml_model_count_skipped: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ml_warning_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    summary_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    detail_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    manifest_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    metadata_schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    artifact_schema_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_source: Mapped[str] = mapped_column(String(64), nullable=False, default="dual_write")
    manifest_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    summary_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    detail_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    artifact_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SavedResearchConfigModel(Base):
    __tablename__ = "saved_research_configs"
    __table_args__ = (
        Index(
            "ix_saved_research_configs_type_updated_at",
            "config_type",
            "updated_at",
        ),
        Index(
            "ix_saved_research_configs_symbol",
            "instrument_symbol",
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    config_type: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    config_schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    instrument_symbol: Mapped[str] = mapped_column(String(64), nullable=False)
    asset_class: Mapped[str] = mapped_column(String(64), nullable=False)
    interval: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WatchlistItemModel(Base):
    __tablename__ = "watchlist_items"
    __table_args__ = (
        UniqueConstraint(
            "symbol",
            "asset_class",
            name="uq_watchlist_items_symbol_asset_class",
        ),
        Index("ix_watchlist_items_updated_at", "updated_at"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(64), nullable=False)
    asset_class: Mapped[str] = mapped_column(String(64), nullable=False)
    source_context: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RecentAssetModel(Base):
    __tablename__ = "recent_assets"
    __table_args__ = (
        UniqueConstraint(
            "symbol",
            "asset_class",
            name="uq_recent_assets_symbol_asset_class",
        ),
        Index("ix_recent_assets_last_used_at", "last_used_at"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(64), nullable=False)
    asset_class: Mapped[str] = mapped_column(String(64), nullable=False)
    source_context: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RecentCompareSetModel(Base):
    __tablename__ = "recent_compare_sets"
    __table_args__ = (
        UniqueConstraint(
            "fingerprint",
            name="uq_recent_compare_sets_fingerprint",
        ),
        Index("ix_recent_compare_sets_last_used_at", "last_used_at"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    fingerprint: Mapped[str] = mapped_column(String(128), nullable=False)
    compare_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    run_ids_json: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    last_used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
