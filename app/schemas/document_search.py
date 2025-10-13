"""
Document search API schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date


class DocumentMetadata(BaseModel):
    """Document metadata"""
    document_id: str
    filename: str
    document_type: str
    source: str
    creation_date: str
    file_size_bytes: int


class SearchResult(BaseModel):
    """Individual search result"""
    document_id: str
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    document_metadata: DocumentMetadata
    snippet: Optional[str] = None


class DocumentSearchResponse(BaseModel):
    """Search results response"""
    query: str
    results: List[SearchResult]
    total_results: int
    page: int
    page_size: int
    search_time_ms: float


class SimilarDocumentsResponse(BaseModel):
    """Similar documents response"""
    document_id: str
    similar_documents: List[SearchResult]
    total_results: int
    similarity_threshold: float

