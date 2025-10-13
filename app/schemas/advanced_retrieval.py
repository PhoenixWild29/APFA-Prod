"""
Advanced document retrieval schemas
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class SemanticSearchQuery(BaseModel):
    """Semantic search query"""
    search_terms: List[str] = Field(..., min_length=1, description="Search terms")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Search filters")
    ranking_algorithm: str = Field("relevance", description="Ranking algorithm")
    top_k: int = Field(10, ge=1, le=100, description="Number of results")


class SemanticSearchResult(BaseModel):
    """Semantic search result"""
    document_id: str
    title: str
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    document_classification: str
    snippet: str
    metadata: Dict[str, Any]


class AuditTrailEntry(BaseModel):
    """Audit trail entry"""
    event_type: str = Field(..., description="Event type (access/modification/version)")
    timestamp: str = Field(..., description="Event timestamp")
    user_id: str = Field(..., description="User who triggered event")
    action: str = Field(..., description="Action performed")
    details: Dict[str, Any] = Field(default_factory=dict, description="Event details")


class AuditTrailResponse(BaseModel):
    """Audit trail response"""
    document_id: str
    version_history: List[Dict[str, Any]] = Field(..., description="Version history")
    access_logs: List[AuditTrailEntry] = Field(..., description="Access logs")
    modification_events: List[AuditTrailEntry] = Field(..., description="Modification events")
    total_accesses: int
    last_modified: Optional[str] = None

