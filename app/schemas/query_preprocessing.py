"""
Query preprocessing schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class QueryPreprocessingRequest(BaseModel):
    """Query preprocessing request"""
    query: str = Field(..., min_length=1, max_length=1000, description="Raw query text")


class Entity(BaseModel):
    """Extracted financial entity"""
    entity_type: Literal['amount', 'rate', 'loan_type', 'time_period'] = Field(..., description="Entity type")
    value: str = Field(..., description="Extracted value")
    normalized_value: Optional[str] = Field(None, description="Normalized value")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence")


class ProcessingMetadata(BaseModel):
    """Query processing metadata"""
    original_length: int = Field(..., description="Original query length")
    normalized_length: int = Field(..., description="Normalized query length")
    entities_found: int = Field(..., description="Number of entities extracted")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


class PreprocessedQueryResponse(BaseModel):
    """Preprocessed query response"""
    original_query: str = Field(..., description="Original query text")
    normalized_query: str = Field(..., description="Normalized query text")
    extracted_entities: List[Entity] = Field(..., description="Extracted financial entities")
    user_intent_category: Literal[
        'loan_inquiry',
        'rate_comparison',
        'eligibility_check',
        'general_advice',
        'unknown'
    ] = Field(..., description="Inferred user intent")
    context_tags: List[str] = Field(..., description="Financial context tags")
    processing_metadata: ProcessingMetadata = Field(..., description="Processing metadata")

