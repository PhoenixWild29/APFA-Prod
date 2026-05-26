"""create conversations and conversation_messages tables

Revision ID: 005_conversations
Revises: 004_refresh_tokens
Create Date: 2026-05-26 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


revision: str = "005_conversations"
down_revision: Union[str, None] = "004_refresh_tokens"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("title", sa.String(200), nullable=False,
                  server_default="New conversation"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_conversations_user_id", "conversations", ["user_id"])
    op.create_index("idx_conversations_updated", "conversations",
                    ["user_id", sa.text("updated_at DESC")])

    op.create_table(
        "conversation_messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("conversation_id", UUID(as_uuid=True),
                  sa.ForeignKey("conversations.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("role", sa.String(10), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sources", JSONB(), nullable=True),
        sa.Column("follow_ups", JSONB(), nullable=True),
        sa.Column("feedback", sa.String(4), nullable=True),
        sa.Column("seq", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("role IN ('user', 'assistant')", name="ck_message_role"),
        sa.CheckConstraint("feedback IS NULL OR feedback IN ('up', 'down')",
                           name="ck_message_feedback"),
    )
    op.create_index("idx_messages_conversation_seq", "conversation_messages",
                    ["conversation_id", "seq"])


def downgrade() -> None:
    op.drop_index("idx_messages_conversation_seq",
                  table_name="conversation_messages")
    op.drop_table("conversation_messages")
    op.drop_index("idx_conversations_updated", table_name="conversations")
    op.drop_index("idx_conversations_user_id", table_name="conversations")
    op.drop_table("conversations")
