"""
Cache management and performance optimization schemas
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any


class CacheWarmRequest(BaseModel):
    """Cache warming request"""
    queries: List[str] = Field(..., min_length=1, max_length=1000, description="Queries to warm")
    ttl_seconds: int = Field(600, ge=60, le=86400, description="Cache TTL (60s-24h)")
    priority: int = Field(5, ge=1, le=10, description="Warming priority (1-10)")


class CacheWarmResponse(BaseModel):
    """Cache warming response"""
    success_count: int = Field(..., description="Successfully warmed queries")
    failure_count: int = Field(..., description="Failed queries")
    estimated_cache_impact_mb: float = Field(..., description="Estimated cache size impact")
    warming_time_ms: float = Field(..., description="Total warming time")
    failed_queries: List[str] = Field(default_factory=list, description="List of failed queries")


class PerformanceBottleneck(BaseModel):
    """Performance bottleneck"""
    component: str
    severity: str
    current_value: float
    threshold: float
    recommendation: str


class PerformanceReport(BaseModel):
    """Performance analysis report"""
    time_range: str = Field(..., description="Analysis time range")
    bottlenecks: List[PerformanceBottleneck] = Field(..., description="Identified bottlenecks")
    optimization_recommendations: List[str] = Field(..., description="Optimization suggestions")
    resource_utilization_trends: Dict[str, List[float]] = Field(..., description="Resource trends")
    threshold_violations: List[Dict[str, Any]] = Field(..., description="Threshold violations")
    suggested_config_changes: Dict[str, Any] = Field(..., description="Configuration suggestions")

