"""Create market_data_history table for daily snapshots.

Revision ID: 006
Revises: 005_conversations
Create Date: 2026-05-26
"""

from alembic import op
import sqlalchemy as sa

revision = "006_market_data_history"
down_revision = "005_conversations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "market_data_history",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("data_type", sa.String(50), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(50), server_default=""),
        sa.Column("change_pct", sa.Float(), nullable=True),
        sa.Column("source", sa.String(50), server_default="finnhub"),
        sa.Column("recorded_date", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_unique_constraint(
        "uq_market_history_ticker_type_unit_date",
        "market_data_history",
        ["ticker", "data_type", "unit", "recorded_date"],
    )
    op.create_index(
        "idx_market_history_ticker_date",
        "market_data_history",
        ["ticker", "recorded_date"],
    )


def downgrade() -> None:
    op.drop_index("idx_market_history_ticker_date", table_name="market_data_history")
    op.drop_constraint(
        "uq_market_history_ticker_type_unit_date",
        "market_data_history",
        type_="unique",
    )
    op.drop_table("market_data_history")
