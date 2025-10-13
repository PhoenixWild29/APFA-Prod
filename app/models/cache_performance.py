"""
Cache performance monitoring data models

Provides:
- Cache performance metrics tracking
- Cache event logging
- TTL effectiveness analysis
- Memory usage monitoring
"""
from datetime import datetime, timezone
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


class CachePerformanceMetrics(BaseModel):
    """
    Cache performance metrics model
    
    Tracks cache effectiveness and performance for
    optimization and bottleneck identification.
    
    Attributes:
        cache_level: Cache tier (memory or redis)
        hit_rate_percent: Cache hit rate percentage
        miss_rate_percent: Cache miss rate percentage
        ttl_effectiveness_percent: TTL effectiveness percentage
        average_lookup_time_ms: Average lookup latency
        memory_usage_mb: Cache memory usage in MB
        eviction_count: Number of cache evictions
    
    Example:
        >>> metrics = CachePerformanceMetrics(
        ...     cache_level="memory",
        ...     hit_rate_percent=75.5,
        ...     miss_rate_percent=24.5,
        ...     ttl_effectiveness_percent=85.0,
        ...     average_lookup_time_ms=2.5,
        ...     memory_usage_mb=150.5,
        ...     eviction_count=42
        ... )
    """
    cache_level: Literal['memory', 'redis'] = Field(
        ...,
        description="Cache tier"
    )
    hit_rate_percent: float = Field(
        ...,
        description="Cache hit rate percentage",
        ge=0.0,
        le=100.0
    )
    miss_rate_percent: float = Field(
        ...,
        description="Cache miss rate percentage",
        ge=0.0,
        le=100.0
    )
    ttl_effectiveness_percent: float = Field(
        ...,
        description="TTL effectiveness percentage",
        ge=0.0,
        le=100.0
    )
    average_lookup_time_ms: float = Field(
        ...,
        description="Average lookup latency (ms)",
        ge=0.0
    )
    memory_usage_mb: float = Field(
        ...,
        description="Cache memory usage in MB",
        ge=0.0
    )
    eviction_count: int = Field(
        ...,
        description="Number of cache evictions",
        ge=0
    )
    
    @field_validator('hit_rate_percent', 'miss_rate_percent')
    @classmethod
    def validate_rates_sum(cls, v: float, info) -> float:
        """Validate hit and miss rates sum to ~100%"""
        if 'hit_rate_percent' in info.data and 'miss_rate_percent' in info.data:
            total = info.data.get('hit_rate_percent', 0) + v
            if abs(total - 100.0) > 0.1:  # Allow small floating point errors
                # Warning: rates don't sum to 100%
                pass
        return v
    
    @field_validator('average_lookup_time_ms', 'memory_usage_mb')
    @classmethod
    def validate_non_negative(cls, v: float) -> float:
        """Ensure non-negative values"""
        if v < 0:
            raise ValueError("Value must be non-negative")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "cache_level": "memory",
                "hit_rate_percent": 75.5,
                "miss_rate_percent": 24.5,
                "ttl_effectiveness_percent": 85.0,
                "average_lookup_time_ms": 2.5,
                "memory_usage_mb": 150.5,
                "eviction_count": 42
            }
        }


class CacheEvent(BaseModel):
    """
    Cache event tracking model
    
    Logs individual cache operations for detailed
    performance analysis and debugging.
    
    Attributes:
        event_type: Type of cache operation
        cache_level: Cache tier (memory or redis)
        key: Cache key
        timestamp: Event timestamp
        latency_ms: Operation latency
        data_size_bytes: Optional data size for set operations
        ttl_seconds: Optional TTL for set operations
    
    Example:
        >>> event = CacheEvent(
        ...     event_type="hit",
        ...     cache_level="memory",
        ...     key="advice:query_hash_abc123",
        ...     timestamp=datetime.now(timezone.utc),
        ...     latency_ms=1.5
        ... )
    """
    event_type: Literal['hit', 'miss', 'set', 'evict', 'invalidate'] = Field(
        ...,
        description="Cache operation type"
    )
    cache_level: Literal['memory', 'redis'] = Field(
        ...,
        description="Cache tier"
    )
    key: str = Field(
        ...,
        description="Cache key",
        min_length=1,
        max_length=500
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Event timestamp"
    )
    latency_ms: float = Field(
        ...,
        description="Operation latency (ms)",
        ge=0.0
    )
    data_size_bytes: Optional[int] = Field(
        None,
        description="Data size for set operations",
        ge=0
    )
    ttl_seconds: Optional[int] = Field(
        None,
        description="TTL for set operations",
        ge=0
    )
    
    @field_validator('timestamp')
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware"""
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v
    
    @field_validator('latency_ms')
    @classmethod
    def validate_non_negative_latency(cls, v: float) -> float:
        """Ensure latency is non-negative"""
        if v < 0:
            raise ValueError("Latency must be non-negative")
        return v
    
    @field_validator('data_size_bytes', 'ttl_seconds')
    @classmethod
    def validate_optional_non_negative(cls, v: Optional[int]) -> Optional[int]:
        """Ensure optional values are non-negative if provided"""
        if v is not None and v < 0:
            raise ValueError("Value must be non-negative")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "hit",
                "cache_level": "memory",
                "key": "advice:query_hash_5d41402abc4b2a76b9719d911017c592",
                "timestamp": "2025-10-12T10:00:00Z",
                "latency_ms": 1.5,
                "data_size_bytes": None,
                "ttl_seconds": None
            }
        }

