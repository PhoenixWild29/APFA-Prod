"""
Health check and detailed metrics schemas
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ComponentHealthStatus(BaseModel):
    """Individual component health status.

    Allowed status values:
      - "healthy"         — component was checked and is operational
      - "degraded"        — component is reachable but in a partially-working state
      - "unhealthy"       — component was checked and failed
      - "unknown"         — health check NOT performed / unable to determine
      - "not_configured"  — component intentionally disabled for this deployment
    """

    component: str
    status: str
    latency_ms: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EnhancedHealthResponse(BaseModel):
    """Enhanced health check response.

    The `overall_status` reflects ONLY components that were actually checked.
    "unknown" components are surfaced in `unknown_components` so callers can
    see at a glance that some checks were skipped, and "not_configured"
    components are surfaced in `not_configured_components` so callers can
    distinguish "intentionally disabled" from "we don't know".
    """

    overall_status: str  # 'healthy', 'degraded', 'unhealthy'
    timestamp: str
    components: List[ComponentHealthStatus]
    degraded_components: List[str]
    failed_components: List[str]
    unknown_components: List[str] = Field(default_factory=list)
    not_configured_components: List[str] = Field(default_factory=list)


class DetailedMetricsResponse(BaseModel):
    """Detailed metrics response"""

    timestamp: str
    time_range: str

    # Timing breakdowns
    timing_breakdowns: Dict[str, Dict[str, float]] = Field(
        ..., description="Component timing breakdowns"
    )

    # Cache analysis
    cache_analysis: Dict[str, float] = Field(
        ..., description="Cache performance analysis"
    )

    # System resources
    system_resources: Dict[str, float] = Field(
        ..., description="System resource utilization"
    )

    # Performance trends
    performance_trends: Dict[str, List[float]] = Field(
        ..., description="Recent performance trends"
    )

    # Latency percentiles
    latency_percentiles: Dict[str, float] = Field(
        ..., description="Response time percentiles"
    )

    # Throughput metrics
    throughput: Dict[str, float] = Field(..., description="System throughput metrics")

    # Error rates
    error_rates: Dict[str, float] = Field(..., description="Error rates by component")
