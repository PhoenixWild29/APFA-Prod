"""
Performance snapshot and system resource data models

Provides:
- Comprehensive performance snapshots
- System resource utilization tracking
- Historical trend analysis support
"""
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class SystemResourceMetrics(BaseModel):
    """
    System resource utilization metrics
    
    Tracks detailed system resource usage for capacity planning
    and performance optimization.
    
    Attributes:
        cpu_utilization_percent: CPU usage percentage
        memory_utilization_percent: Memory usage percentage
        disk_io_utilization_percent: Disk I/O usage percentage
        network_throughput_mbps: Network throughput in Mbps
        database_connections: Active database connections
        cache_memory_usage_mb: Cache memory usage in MB
    
    Example:
        >>> resources = SystemResourceMetrics(
        ...     cpu_utilization_percent=65.5,
        ...     memory_utilization_percent=42.0,
        ...     disk_io_utilization_percent=15.0,
        ...     network_throughput_mbps=125.5,
        ...     database_connections=25,
        ...     cache_memory_usage_mb=150.5
        ... )
    """
    cpu_utilization_percent: float = Field(
        ...,
        description="CPU usage percentage",
        ge=0.0,
        le=100.0
    )
    memory_utilization_percent: float = Field(
        ...,
        description="Memory usage percentage",
        ge=0.0,
        le=100.0
    )
    disk_io_utilization_percent: float = Field(
        ...,
        description="Disk I/O usage percentage",
        ge=0.0,
        le=100.0
    )
    network_throughput_mbps: float = Field(
        ...,
        description="Network throughput in Mbps",
        ge=0.0
    )
    database_connections: int = Field(
        ...,
        description="Active database connections",
        ge=0
    )
    cache_memory_usage_mb: float = Field(
        ...,
        description="Cache memory usage in MB",
        ge=0.0
    )
    
    @field_validator('network_throughput_mbps', 'cache_memory_usage_mb')
    @classmethod
    def validate_non_negative(cls, v: float) -> float:
        """Ensure non-negative values"""
        if v < 0:
            raise ValueError("Value must be non-negative")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "cpu_utilization_percent": 65.5,
                "memory_utilization_percent": 42.0,
                "disk_io_utilization_percent": 15.0,
                "network_throughput_mbps": 125.5,
                "database_connections": 25,
                "cache_memory_usage_mb": 150.5
            }
        }


class PerformanceSnapshot(BaseModel):
    """
    Comprehensive performance snapshot
    
    Captures complete system performance state at a point in time
    for historical analysis and trend monitoring.
    
    Attributes:
        timestamp: Snapshot timestamp
        request_count: Total requests processed
        response_time_p95_ms: 95th percentile response time
        response_time_p99_ms: 99th percentile response time
        error_rate_percent: Error rate percentage
        cache_hit_rate_percent: Cache hit rate percentage
        active_requests: Currently active requests
        system_resources: System resource metrics
    
    Example:
        >>> snapshot = PerformanceSnapshot(
        ...     timestamp=datetime.now(timezone.utc),
        ...     request_count=15420,
        ...     response_time_p95_ms=185.5,
        ...     response_time_p99_ms=350.0,
        ...     error_rate_percent=0.05,
        ...     cache_hit_rate_percent=75.0,
        ...     active_requests=12,
        ...     system_resources=resources
        ... )
    """
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Snapshot timestamp"
    )
    request_count: int = Field(
        ...,
        description="Total requests processed",
        ge=0
    )
    response_time_p95_ms: float = Field(
        ...,
        description="95th percentile response time",
        ge=0.0
    )
    response_time_p99_ms: float = Field(
        ...,
        description="99th percentile response time",
        ge=0.0
    )
    error_rate_percent: float = Field(
        ...,
        description="Error rate percentage",
        ge=0.0,
        le=100.0
    )
    cache_hit_rate_percent: float = Field(
        ...,
        description="Cache hit rate percentage",
        ge=0.0,
        le=100.0
    )
    active_requests: int = Field(
        ...,
        description="Currently active requests",
        ge=0
    )
    system_resources: SystemResourceMetrics = Field(
        ...,
        description="System resource metrics"
    )
    
    @field_validator('timestamp')
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware"""
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v
    
    @field_validator('response_time_p99_ms')
    @classmethod
    def validate_p99_greater_than_p95(cls, v: float, info) -> float:
        """Ensure P99 is >= P95"""
        p95 = info.data.get('response_time_p95_ms')
        if p95 is not None and v < p95:
            raise ValueError("P99 response time must be >= P95")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-10-12T10:00:00Z",
                "request_count": 15420,
                "response_time_p95_ms": 185.5,
                "response_time_p99_ms": 350.0,
                "error_rate_percent": 0.05,
                "cache_hit_rate_percent": 75.0,
                "active_requests": 12,
                "system_resources": {
                    "cpu_utilization_percent": 65.5,
                    "memory_utilization_percent": 42.0,
                    "disk_io_utilization_percent": 15.0,
                    "network_throughput_mbps": 125.5,
                    "database_connections": 25,
                    "cache_memory_usage_mb": 150.5
                }
            }
        }

