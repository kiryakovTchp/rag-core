"""add unique index on meta->>'sha256'

Revision ID: 0002
Revises: 0001
Create Date: 2025-09-07
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Unique on JSONB meta->>'sha256' for idempotency; exclude nulls
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_documents_sha256
        ON documents ((meta->>'sha256'))
        WHERE (meta->>'sha256') IS NOT NULL;
        """
    )
    # Reinforce indexes (idempotent); create if they don't exist
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents (created_at);
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks (document_id);
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_documents_sha256;")
    # Keep other indexes

