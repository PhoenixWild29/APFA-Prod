"""
Query suggestions schemas
"""
from pydantic import BaseModel, Field
from typing import List, Literal


class Suggestion(BaseModel):
    """Query suggestion"""
    completed_query: str = Field(..., description="Completed query text")
    relevance_score: float = Field(..., ge=0.0, le=100.0, description="Relevance score (0-100)")
    suggestion_type: Literal['completion', 'terminology', 'related_topic'] = Field(
        ...,
        description="Type of suggestion"
    )
    explanation: str = Field(..., description="Explanation or definition")


class SuggestionsResponse(BaseModel):
    """Query suggestions response"""
    partial_query: str = Field(..., description="Original partial query")
    suggestions: List[Suggestion] = Field(..., description="Ranked suggestions (max 10)")
    total_suggestions: int = Field(..., description="Total suggestions generated")

