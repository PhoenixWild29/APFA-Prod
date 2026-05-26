"""Pydantic request/response schemas for conversation persistence."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)


class ConversationUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


class MessageFeedback(BaseModel):
    feedback: Optional[str] = Field(None, pattern=r"^(up|down)$")


class SourceSchema(BaseModel):
    document_id: str
    title: str
    section: Optional[str] = None
    excerpt: str
    relevance_score: float


class MessageSchema(BaseModel):
    id: str
    role: str
    content: str
    sources: Optional[list[SourceSchema]] = None
    follow_ups: Optional[list[str]] = None
    feedback: Optional[str] = None
    seq: int
    created_at: datetime


class ConversationSummary(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    preview: Optional[str] = None


class ConversationDetail(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[MessageSchema]
    total_messages: int
