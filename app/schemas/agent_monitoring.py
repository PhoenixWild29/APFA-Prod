"""
Agent monitoring schemas
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class RetrieverStatus(BaseModel):
    """Retriever agent status"""
    agent_name: str = Field("retriever_agent", description="Agent name")
    status: str = Field(..., description="Current status (active/idle/error)")
    
    # RAG retrieval performance
    rag_retrieval_performance: Dict[str, float] = Field(
        ...,
        description="RAG retrieval metrics"
    )
    
    # FAISS index utilization
    faiss_index_utilization: Dict[str, Any] = Field(
        ...,
        description="FAISS index statistics"
    )
    
    # Context quality
    context_quality_scores: Dict[str, float] = Field(
        ...,
        description="Context quality metrics"
    )
    
    # Retrieval success rates
    retrieval_success_rate_percent: float = Field(..., description="Retrieval success rate")
    
    # Diagnostics
    current_index_size: int = Field(..., description="Current FAISS index size")
    last_retrieval_timestamp: Optional[str] = Field(None, description="Last retrieval time")
    error_counts: Dict[str, int] = Field(..., description="Error counts by type")
    system_health: str = Field(..., description="Overall system health")


class RetrieverPerformance(BaseModel):
    """Retriever agent performance analysis"""
    agent_name: str = Field("retriever_agent", description="Agent name")
    
    # Latency metrics
    retrieval_latency_ms: Dict[str, float] = Field(
        ...,
        description="Latency measurements (avg, p50, p95, p99)"
    )
    
    # Context relevance
    context_relevance_scores: Dict[str, float] = Field(
        ...,
        description="Context relevance metrics (avg, min, max)"
    )
    
    # Index efficiency
    index_search_efficiency: Dict[str, float] = Field(
        ...,
        description="Index search efficiency metrics"
    )
    
    # Recommendations
    optimization_recommendations: List[str] = Field(
        ...,
        description="System optimization suggestions"
    )
    
    # Historical trends
    historical_trends: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Historical performance data"
    )
    
    # Baseline comparison
    baseline_comparison: Dict[str, float] = Field(
        ...,
        description="Performance vs baseline metrics"
    )

