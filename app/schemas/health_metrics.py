"""
Health check and detailed metrics schemas
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional


class ComponentHealthStatus(BaseModel):
    """Individual component health status"""
    component: str
    status: str  # 'healthy', 'degraded', 'unhealthy'
    latency_ms: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EnhancedHealthResponse(BaseModel):
    """Enhanced health check response"""
    overall_status: str  # 'healthy', 'degraded', 'unhealthy'
    timestamp: str
    components: List[ComponentHealthStatus]
    degraded_components: List[str]
    failed_components: List[str]


class DetailedMetricsResponse(BaseModel):
    """Detailed metrics response"""
    timestamp: str
    time_range: str
    
    # Timing breakdowns
    timing_breakdowns: Dict[str, Dict[str, float]] = Field(
        ...,
        description="Component timing breakdowns"
    )
    
    # Cache analysis
    cache_analysis: Dict[str, float] = Field(
        ...,
        description="Cache performance analysis"
    )
    
    # System resources
    system_resources: Dict[str, float] = Field(
        ...,
        description="System resource utilization"
    )
    
    # Performance trends
    performance_trends: Dict[str, List[float]] = Field(
        ...,
        description="Recent performance trends"
    )
    
    # Latency percentiles
    latency_percentiles: Dict[str, float] = Field(
        ...,
        description="Response time percentiles"
    )
    
    # Throughput metrics
    throughput: Dict[str, float] = Field(
        ...,
        description="System throughput metrics"
    )
    
    # Error rates
    error_rates: Dict[str, float] = Field(
        ...,
        description="Error rates by component"
    )

