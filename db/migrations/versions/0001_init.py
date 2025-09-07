"""init schema and pgvector

Revision ID: 0001
Revises: 
Create Date: 2025-09-07
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # documents table
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("filename", sa.String(length=512), nullable=False),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_documents_created_at", "documents", ["created_at"], unique=False)

    # chunks table
    op.create_table(
        "chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("page", sa.Integer(), nullable=True),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_index("idx_chunks_document_id", "chunks", ["document_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_chunks_document_id", table_name="chunks")
    op.drop_table("chunks")
    op.drop_index("idx_documents_created_at", table_name="documents")
    op.drop_table("documents")
    # do not drop extension

