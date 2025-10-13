"""
Query validation schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class QueryValidationRequest(BaseModel):
    """Query validation request"""
    query: str = Field(..., min_length=1, max_length=1000, description="Query text to validate")


class QueryValidationResponse(BaseModel):
    """Query validation response with detailed feedback"""
    is_valid: bool = Field(..., description="Overall validation status")
    profanity_detected: bool = Field(..., description="Whether profanity was detected")
    is_financially_relevant: bool = Field(..., description="Whether query is financially relevant")
    is_content_safe: bool = Field(..., description="Whether content is safe")
    is_properly_formatted: bool = Field(..., description="Whether query is properly formatted")
    
    # Scores and metrics
    financial_relevance_score: float = Field(..., ge=0.0, le=100.0, description="Financial relevance score (0-100)")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Validation confidence score")
    
    # Feedback
    validation_failures: List[str] = Field(default_factory=list, description="List of validation failures")
    suggested_improvements: List[str] = Field(default_factory=list, description="Suggested query improvements")
    explanatory_messages: List[str] = Field(default_factory=list, description="Detailed explanatory messages")
    
    # Metadata
    validation_time_ms: float = Field(..., description="Validation processing time")

