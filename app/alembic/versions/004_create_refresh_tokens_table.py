"""create refresh_tokens table for token rotation and family-based revocation

Revision ID: 004_refresh_tokens
Revises: 003_api_keys_audit
Create Date: 2026-04-20 00:00:00.000000

Token refresh design (Plan agent + CoWork approved):
- Opaque refresh tokens stored as SHA-256 hashes
- Token families track lineage from a single login
- Rotation: each refresh invalidates old token, issues new
- Grace window: rotated token accepted within ~10s (multi-tab safety)
- Theft detection: reuse outside grace window revokes entire family
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "004_refresh_tokens"
down_revision: Union[str, None] = "003_api_keys_audit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column(
            "user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("family_id", sa.String(36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "replaced_by_id",
            sa.Integer(),
            sa.ForeignKey("refresh_tokens.id"),
            nullable=True,
        ),
    )
    op.create_index("idx_refresh_tokens_hash", "refresh_tokens", ["token_hash"])
    op.create_index("idx_refresh_tokens_family", "refresh_tokens", ["family_id"])
    op.create_index("idx_refresh_tokens_user", "refresh_tokens", ["user_id"])


def downgrade() -> None:
    op.drop_index("idx_refresh_tokens_user", table_name="refresh_tokens")
    op.drop_index("idx_refresh_tokens_family", table_name="refresh_tokens")
    op.drop_index("idx_refresh_tokens_hash", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
