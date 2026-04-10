"""create users table

Revision ID: 001_create_users
Revises:
Create Date: 2026-04-10 00:00:00.000000

APFA-013 — initial migration replacing fake_users_db with PostgreSQL persistence.
Matches app/orm_models.py User model exactly.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "001_create_users"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column(
            "disabled", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "role", sa.String(), nullable=False, server_default="standard"
        ),
        sa.Column(
            "permissions",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'::json"),
        ),
        sa.Column(
            "verified", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("verification_token", sa.String(), nullable=True),
        sa.Column("token_expiration", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("first_name", sa.String(), nullable=True),
        sa.Column("last_name", sa.String(), nullable=True),
        sa.Column(
            "marketing_consent",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "subscription_tier",
            sa.String(),
            nullable=False,
            server_default="free",
        ),
        sa.Column("stripe_customer_id", sa.String(), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(), nullable=True),
        sa.Column(
            "query_count_this_period",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "billing_period_start", sa.DateTime(timezone=True), nullable=True
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(
        "ix_users_username", "users", ["username"], unique=True
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index(
        "ix_users_stripe_customer_id", "users", ["stripe_customer_id"]
    )
    op.create_index(
        "idx_users_stripe_customer", "users", ["stripe_customer_id"]
    )


def downgrade() -> None:
    op.drop_index("idx_users_stripe_customer", table_name="users")
    op.drop_index("ix_users_stripe_customer_id", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
