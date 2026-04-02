"""create research run metadata table"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_research_run_metadata"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "research_run_metadata",
        sa.Column("run_id", sa.String(length=255), nullable=False),
        sa.Column("run_name", sa.String(length=255), nullable=False),
        sa.Column("workflow_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("instrument_symbol", sa.String(length=64), nullable=False),
        sa.Column("asset_class", sa.String(length=64), nullable=True),
        sa.Column("interval", sa.String(length=32), nullable=True),
        sa.Column("candle_count", sa.Integer(), nullable=True),
        sa.Column("candle_source_type", sa.String(length=64), nullable=True),
        sa.Column("has_strategy", sa.Boolean(), nullable=False),
        sa.Column("has_ml", sa.Boolean(), nullable=False),
        sa.Column("strategy_id", sa.String(length=128), nullable=True),
        sa.Column("total_trades", sa.Integer(), nullable=True),
        sa.Column("total_return_pct", sa.Float(), nullable=True),
        sa.Column("total_net_pnl", sa.Float(), nullable=True),
        sa.Column("max_drawdown_pct", sa.Float(), nullable=True),
        sa.Column("sharpe_ratio", sa.Float(), nullable=True),
        sa.Column("ml_task_type", sa.String(length=64), nullable=True),
        sa.Column("ml_target_label", sa.String(length=128), nullable=True),
        sa.Column("ml_best_model_id", sa.String(length=128), nullable=True),
        sa.Column("ml_primary_metric_name", sa.String(length=128), nullable=True),
        sa.Column("ml_best_validation_value", sa.Float(), nullable=True),
        sa.Column("ml_best_test_value", sa.Float(), nullable=True),
        sa.Column("ml_model_count_executed", sa.Integer(), nullable=True),
        sa.Column("ml_model_count_skipped", sa.Integer(), nullable=True),
        sa.Column("ml_warning_count", sa.Integer(), nullable=True),
        sa.Column("summary_path", sa.String(length=1024), nullable=False),
        sa.Column("detail_path", sa.String(length=1024), nullable=True),
        sa.Column("manifest_path", sa.String(length=1024), nullable=True),
        sa.Column("metadata_schema_version", sa.Integer(), nullable=False),
        sa.Column("artifact_schema_version", sa.Integer(), nullable=True),
        sa.Column("metadata_source", sa.String(length=64), nullable=False),
        sa.Column("manifest_synthetic", sa.Boolean(), nullable=False),
        sa.Column("summary_available", sa.Boolean(), nullable=False),
        sa.Column("detail_available", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("run_id"),
    )
    op.create_index(
        "ix_research_run_metadata_started_at",
        "research_run_metadata",
        ["started_at"],
        unique=False,
    )
    op.create_index(
        "ix_research_run_metadata_workflow_started_at",
        "research_run_metadata",
        ["workflow_type", "started_at"],
        unique=False,
    )
    op.create_index(
        "ix_research_run_metadata_status_started_at",
        "research_run_metadata",
        ["status", "started_at"],
        unique=False,
    )
    op.create_index(
        "ix_research_run_metadata_instrument_symbol",
        "research_run_metadata",
        ["instrument_symbol"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_research_run_metadata_instrument_symbol",
        table_name="research_run_metadata",
    )
    op.drop_index(
        "ix_research_run_metadata_status_started_at",
        table_name="research_run_metadata",
    )
    op.drop_index(
        "ix_research_run_metadata_workflow_started_at",
        table_name="research_run_metadata",
    )
    op.drop_index(
        "ix_research_run_metadata_started_at",
        table_name="research_run_metadata",
    )
    op.drop_table("research_run_metadata")
