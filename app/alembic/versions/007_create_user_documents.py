"""create user_documents table

Revision ID: 007_user_documents
Revises: 006_market_data_history
Create Date: 2026-06-01 00:00:00.000000

Tracks per-user document uploads and their processing status.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "007_user_documents"
down_revision: Union[str, None] = "006_market_data_history"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_documents",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("processing_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("chunk_count", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("celery_task_id", sa.String(50), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name="fk_user_documents_user_id",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "processing_status IN ('pending', 'processing', 'completed', 'failed')",
            name="ck_user_documents_status",
        ),
    )
    op.create_index("idx_user_documents_user_id", "user_documents", ["user_id"])
    op.create_index("idx_user_documents_user_status", "user_documents", ["user_id", "processing_status"])


def downgrade() -> None:
    op.drop_table("user_documents")
