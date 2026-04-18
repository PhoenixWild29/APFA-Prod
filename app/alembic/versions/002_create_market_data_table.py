"""create market_data table

Revision ID: 002_market_data
Revises: 001_create_users
Create Date: 2026-04-18 00:00:00.000000

Data pipeline: structured market data store for Finnhub/Mboum connectors.
NOT embedded into FAISS — served via agent tools.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "002_market_data"
down_revision: Union[str, None] = "001_create_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "market_data",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("data_type", sa.String(50), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(50), server_default=""),
        sa.Column("change_pct", sa.Float(), nullable=True),
        sa.Column("timestamp", sa.String(50), nullable=False),
        sa.Column("source", sa.String(50), server_default="finnhub"),
        sa.Column("metadata_json", sa.Text(), server_default="{}"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticker", "data_type", name="uq_market_data_ticker_type"),
    )
    op.create_index("idx_market_data_ticker", "market_data", ["ticker"])
    op.create_index("idx_market_data_type", "market_data", ["data_type"])


def downgrade() -> None:
    op.drop_index("idx_market_data_type", table_name="market_data")
    op.drop_index("idx_market_data_ticker", table_name="market_data")
    op.drop_table("market_data")
