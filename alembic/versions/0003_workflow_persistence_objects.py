"""add workflow persistence tables"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0003_workflow_persistence_objects"
down_revision = "0002_research_run_metadata_transition_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "saved_research_configs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("config_type", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1024), nullable=True),
        sa.Column("config_schema_version", sa.Integer(), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("instrument_symbol", sa.String(length=64), nullable=False),
        sa.Column("asset_class", sa.String(length=64), nullable=False),
        sa.Column("interval", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_saved_research_configs_type_updated_at",
        "saved_research_configs",
        ["config_type", "updated_at"],
        unique=False,
    )
    op.create_index(
        "ix_saved_research_configs_symbol",
        "saved_research_configs",
        ["instrument_symbol"],
        unique=False,
    )

    op.create_table(
        "watchlist_items",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("symbol", sa.String(length=64), nullable=False),
        sa.Column("asset_class", sa.String(length=64), nullable=False),
        sa.Column("source_context", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "symbol",
            "asset_class",
            name="uq_watchlist_items_symbol_asset_class",
        ),
    )
    op.create_index(
        "ix_watchlist_items_updated_at",
        "watchlist_items",
        ["updated_at"],
        unique=False,
    )

    op.create_table(
        "recent_assets",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("symbol", sa.String(length=64), nullable=False),
        sa.Column("asset_class", sa.String(length=64), nullable=False),
        sa.Column("source_context", sa.String(length=128), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "symbol",
            "asset_class",
            name="uq_recent_assets_symbol_asset_class",
        ),
    )
    op.create_index(
        "ix_recent_assets_last_used_at",
        "recent_assets",
        ["last_used_at"],
        unique=False,
    )

    op.create_table(
        "recent_compare_sets",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("fingerprint", sa.String(length=128), nullable=False),
        sa.Column("compare_mode", sa.String(length=32), nullable=False),
        sa.Column("run_ids_json", sa.JSON(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "fingerprint",
            name="uq_recent_compare_sets_fingerprint",
        ),
    )
    op.create_index(
        "ix_recent_compare_sets_last_used_at",
        "recent_compare_sets",
        ["last_used_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_recent_compare_sets_last_used_at",
        table_name="recent_compare_sets",
    )
    op.drop_table("recent_compare_sets")
    op.drop_index(
        "ix_recent_assets_last_used_at",
        table_name="recent_assets",
    )
    op.drop_table("recent_assets")
    op.drop_index(
        "ix_watchlist_items_updated_at",
        table_name="watchlist_items",
    )
    op.drop_table("watchlist_items")
    op.drop_index(
        "ix_saved_research_configs_symbol",
        table_name="saved_research_configs",
    )
    op.drop_index(
        "ix_saved_research_configs_type_updated_at",
        table_name="saved_research_configs",
    )
    op.drop_table("saved_research_configs")
