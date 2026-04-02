"""add transition hardening fields to research run metadata"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_research_run_metadata_transition_fields"
down_revision = "0001_research_run_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "research_run_metadata",
        sa.Column("artifact_fingerprint", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "research_run_metadata",
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("research_run_metadata", "last_synced_at")
    op.drop_column("research_run_metadata", "artifact_fingerprint")
