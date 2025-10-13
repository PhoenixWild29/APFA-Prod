"""
Agent testing and validation schemas
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class RetrieverTestRequest(BaseModel):
    """Retriever agent test request"""
    query_text: str = Field(..., min_length=10, max_length=500, description="Test query text")
    context_requirements: Dict[str, Any] = Field(
        default_factory=dict,
        description="Expected context requirements"
    )
    performance_benchmarks: Dict[str, float] = Field(
        default_factory=lambda: {"max_latency_ms": 100.0, "min_relevance_score": 0.7},
        description="Performance targets"
    )


class RetrievalQualityMetrics(BaseModel):
    """Retrieval quality assessment"""
    context_relevance_scores: List[float] = Field(..., description="Relevance scores (0-1)")
    avg_relevance_score: float = Field(..., ge=0.0, le=1.0, description="Average relevance")
    coverage_analysis: Dict[str, Any] = Field(..., description="Coverage metrics")
    precision: float = Field(..., ge=0.0, le=1.0, description="Retrieval precision")
    recall: float = Field(..., ge=0.0, le=1.0, description="Retrieval recall")
    f1_score: float = Field(..., ge=0.0, le=1.0, description="F1 score")


class PerformanceBenchmark(BaseModel):
    """Performance benchmark results"""
    retrieval_latency_ms: float = Field(..., description="Total retrieval latency")
    search_duration_ms: float = Field(..., description="FAISS search duration")
    scoring_time_ms: float = Field(..., description="Relevance scoring time")
    throughput_queries_per_second: float = Field(..., description="Throughput")
    meets_performance_target: bool = Field(..., description="Whether meets target")


class DiagnosticInfo(BaseModel):
    """Diagnostic information"""
    faiss_index_performance: Dict[str, Any] = Field(..., description="FAISS metrics")
    embedding_quality_indicators: Dict[str, float] = Field(..., description="Embedding quality")
    optimization_recommendations: List[str] = Field(..., description="Recommendations")


class RetrieverTestResult(BaseModel):
    """Retriever agent test results"""
    test_status: str = Field(..., description="Overall test status (pass/fail)")
    query_text: str = Field(..., description="Test query")
    
    # Validation results
    retrieval_accuracy: float = Field(..., ge=0.0, le=1.0, description="Retrieval accuracy")
    quality_metrics: RetrievalQualityMetrics = Field(..., description="Quality assessment")
    
    # Performance results
    performance_benchmark: PerformanceBenchmark = Field(..., description="Performance metrics")
    
    # Diagnostics
    diagnostic_info: DiagnosticInfo = Field(..., description="Diagnostic information")
    
    # Retrieved context
    retrieved_context: List[str] = Field(..., description="Retrieved document snippets")
    context_count: int = Field(..., description="Number of contexts retrieved")

