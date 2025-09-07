"""rename indexes to match AC names

Revision ID: 0003
Revises: 0002
Create Date: 2025-09-07
"""

from __future__ import annotations

from alembic import op


revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Unique sha256: rename uq_documents_sha256 -> ux_documents_sha256
    op.execute(
        "ALTER INDEX IF EXISTS uq_documents_sha256 RENAME TO ux_documents_sha256;"
    )
    # created_at: idx_documents_created_at -> ix_documents_created_at
    op.execute(
        "ALTER INDEX IF EXISTS idx_documents_created_at RENAME TO ix_documents_created_at;"
    )
    # chunks fk: idx_chunks_document_id -> ix_chunks_document_id
    op.execute(
        "ALTER INDEX IF EXISTS idx_chunks_document_id RENAME TO ix_chunks_document_id;"
    )


def downgrade() -> None:
    op.execute(
        "ALTER INDEX IF EXISTS ux_documents_sha256 RENAME TO uq_documents_sha256;"
    )
    op.execute(
        "ALTER INDEX IF EXISTS ix_documents_created_at RENAME TO idx_documents_created_at;"
    )
    op.execute(
        "ALTER INDEX IF EXISTS ix_chunks_document_id RENAME TO idx_chunks_document_id;"
    )

