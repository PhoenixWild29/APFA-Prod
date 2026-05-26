"""Conversation persistence service layer.

Centralizes all DB access for conversations. Every query filters by user_id
to enforce ownership isolation — no cross-user access is possible.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from app.orm_models import Conversation, ConversationMessage

logger = logging.getLogger(__name__)

MAX_MESSAGES_PER_CONVERSATION = 200


def get_owned_conversation(
    conversation_id: str, user_id: str, db: Session
) -> Conversation:
    conv = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
            Conversation.deleted_at.is_(None),
        )
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


def list_conversations(
    user_id: str, db: Session, limit: int = 50, offset: int = 0
) -> list[dict]:
    from sqlalchemy import case, literal_column

    subq = (
        db.query(
            ConversationMessage.conversation_id,
            sa_func.count(ConversationMessage.id).label("message_count"),
            sa_func.min(
                case(
                    (ConversationMessage.role == "user", ConversationMessage.content),
                    else_=None,
                )
            ).label("first_user_message"),
        )
        .group_by(ConversationMessage.conversation_id)
        .subquery()
    )

    rows = (
        db.query(Conversation, subq.c.message_count, subq.c.first_user_message)
        .outerjoin(subq, Conversation.id == subq.c.conversation_id)
        .filter(
            Conversation.user_id == user_id,
            Conversation.deleted_at.is_(None),
        )
        .order_by(Conversation.updated_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": str(conv.id),
            "title": conv.title,
            "created_at": conv.created_at,
            "updated_at": conv.updated_at,
            "message_count": msg_count or 0,
            "preview": (first_msg[:100] if first_msg else None),
        }
        for conv, msg_count, first_msg in rows
    ]


def create_conversation(
    user_id: str, db: Session, title: Optional[str] = None
) -> Conversation:
    conv = Conversation(
        user_id=user_id,
        title=title or "New conversation",
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def get_conversation_detail(
    conversation_id: str,
    user_id: str,
    db: Session,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    conv = get_owned_conversation(conversation_id, user_id, db)

    total = (
        db.query(sa_func.count(ConversationMessage.id))
        .filter(ConversationMessage.conversation_id == conv.id)
        .scalar()
    )

    messages = (
        db.query(ConversationMessage)
        .filter(ConversationMessage.conversation_id == conv.id)
        .order_by(ConversationMessage.seq.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "id": str(conv.id),
        "title": conv.title,
        "created_at": conv.created_at,
        "updated_at": conv.updated_at,
        "messages": [
            {
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "sources": m.sources,
                "follow_ups": m.follow_ups,
                "feedback": m.feedback,
                "seq": m.seq,
                "created_at": m.created_at,
            }
            for m in messages
        ],
        "total_messages": total,
    }


def update_conversation_title(
    conversation_id: str, user_id: str, title: str, db: Session
) -> Conversation:
    conv = get_owned_conversation(conversation_id, user_id, db)
    conv.title = title
    conv.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(conv)
    return conv


def delete_conversation(
    conversation_id: str, user_id: str, db: Session
) -> None:
    conv = get_owned_conversation(conversation_id, user_id, db)
    conv.deleted_at = datetime.now(timezone.utc)
    db.commit()


def update_message_feedback(
    conversation_id: str,
    message_id: str,
    user_id: str,
    feedback: Optional[str],
    db: Session,
) -> ConversationMessage:
    conv = get_owned_conversation(conversation_id, user_id, db)
    msg = (
        db.query(ConversationMessage)
        .filter(
            ConversationMessage.id == message_id,
            ConversationMessage.conversation_id == conv.id,
        )
        .first()
    )
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    msg.feedback = feedback
    db.commit()
    db.refresh(msg)
    return msg


def append_messages(
    conversation_id: str,
    user_id: str,
    user_content: str,
    assistant_content: str,
    db: Session,
    sources: Optional[list] = None,
    follow_ups: Optional[list] = None,
) -> tuple[ConversationMessage, ConversationMessage]:
    conv = get_owned_conversation(conversation_id, user_id, db)

    current_count = (
        db.query(sa_func.count(ConversationMessage.id))
        .filter(ConversationMessage.conversation_id == conv.id)
        .scalar()
    )
    if current_count >= MAX_MESSAGES_PER_CONVERSATION:
        raise HTTPException(
            status_code=422,
            detail=f"Conversation has reached the {MAX_MESSAGES_PER_CONVERSATION} message limit. Start a new conversation.",
        )

    max_seq = (
        db.query(sa_func.coalesce(sa_func.max(ConversationMessage.seq), 0))
        .filter(ConversationMessage.conversation_id == conv.id)
        .scalar()
    )

    user_msg = ConversationMessage(
        conversation_id=conv.id,
        role="user",
        content=user_content,
        seq=max_seq + 1,
    )
    assistant_msg = ConversationMessage(
        conversation_id=conv.id,
        role="assistant",
        content=assistant_content,
        sources=sources,
        follow_ups=follow_ups,
        seq=max_seq + 2,
    )

    db.add(user_msg)
    db.add(assistant_msg)
    conv.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user_msg)
    db.refresh(assistant_msg)

    return user_msg, assistant_msg
