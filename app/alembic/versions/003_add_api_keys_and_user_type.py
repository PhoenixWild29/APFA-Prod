"""add api_keys table, pipeline_audit_log table, users.type column

Revision ID: 003_api_keys_audit
Revises: 002_market_data
Create Date: 2026-04-18 00:00:00.000000

Pipeline authentication infrastructure (CoWork design):
- users.type column: "human" | "service" (defaults to "human")
- api_keys table: machine-to-machine keys for pipeline auth
- pipeline_audit_log: write-once audit trail (GLBA 7-year retention)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "003_api_keys_audit"
down_revision: Union[str, None] = "002_market_data"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- users.type column ---
    op.add_column(
        "users",
        sa.Column(
            "type",
            sa.String(20),
            server_default="human",
            nullable=False,
        ),
    )

    # --- api_keys table ---
    op.create_table(
        "api_keys",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("key_hash", sa.String(128), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_api_keys_user_id"),
    )
    op.create_index("idx_api_keys_user_id", "api_keys", ["user_id"])
    op.create_index("idx_api_keys_key_hash", "api_keys", ["key_hash"])

    # --- pipeline_audit_log table ---
    # Write-once, never update. Retain >= 7 years (GLBA Safeguards Rule).
    op.create_table(
        "pipeline_audit_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("key_id", sa.Integer(), nullable=True),
        sa.Column("source_connector", sa.String(50), nullable=False),
        sa.Column("source_url", sa.Text(), server_default=""),
        sa.Column("content_hash", sa.String(64), server_default=""),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("parent_document_id", sa.String(200), server_default=""),
        sa.Column("chunk_count", sa.Integer(), server_default="0"),
        sa.Column("request_ip", sa.String(45), server_default=""),
        sa.Column("user_agent", sa.String(500), server_default=""),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("error_code", sa.String(50), server_default=""),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["key_id"], ["api_keys.id"], name="fk_audit_log_key_id"
        ),
    )
    op.create_index(
        "idx_audit_log_timestamp", "pipeline_audit_log", ["timestamp"]
    )
    op.create_index(
        "idx_audit_log_source", "pipeline_audit_log", ["source_connector"]
    )
    op.create_index(
        "idx_audit_log_key_id", "pipeline_audit_log", ["key_id"]
    )


def downgrade() -> None:
    op.drop_index("idx_audit_log_key_id", table_name="pipeline_audit_log")
    op.drop_index("idx_audit_log_source", table_name="pipeline_audit_log")
    op.drop_index("idx_audit_log_timestamp", table_name="pipeline_audit_log")
    op.drop_table("pipeline_audit_log")
    op.drop_index("idx_api_keys_key_hash", table_name="api_keys")
    op.drop_index("idx_api_keys_user_id", table_name="api_keys")
    op.drop_table("api_keys")
    op.drop_column("users", "type")
