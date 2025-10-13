"""
Performance tracking data models for response metrics and caching

Provides comprehensive tracking of:
- Response performance metrics
- Cache interactions
- Agent execution traces
- Multi-level caching statistics
"""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator


class AgentExecutionStep(BaseModel):
    """Individual agent execution step"""
    agent_name: str = Field(..., description="Agent name")
    started_at: datetime = Field(..., description="Step start time")
    completed_at: datetime = Field(..., description="Step completion time")
    duration_ms: float = Field(..., description="Step duration in milliseconds")
    status: Literal['success', 'failure', 'skipped'] = Field(..., description="Execution status")
    output_summary: Optional[str] = Field(None, description="Summary of agent output")


class ResponseMetrics(BaseModel):
    """
    Response performance metrics
    
    Tracks detailed timing breakdown across the loan advisory pipeline.
    
    Attributes:
        total_latency_ms: Total end-to-end response time
        rag_retrieval_ms: RAG retrieval duration
        llm_inference_ms: LLM inference duration
        cache_lookup_ms: Cache lookup duration
        agent_coordination_ms: Agent coordination overhead
        was_cached: Whether response was served from cache
        cache_hit_rate: Overall cache hit rate (0.0-1.0)
    
    Example:
        >>> metrics = ResponseMetrics(
        ...     total_latency_ms=185.5,
        ...     rag_retrieval_ms=45.2,
        ...     llm_inference_ms=125.0,
        ...     cache_lookup_ms=2.5,
        ...     agent_coordination_ms=12.8,
        ...     was_cached=False,
        ...     cache_hit_rate=0.75
        ... )
    """
    total_latency_ms: float = Field(
        ...,
        description="Total end-to-end response time (ms)",
        ge=0.0
    )
    rag_retrieval_ms: float = Field(
        ...,
        description="RAG retrieval duration (ms)",
        ge=0.0
    )
    llm_inference_ms: float = Field(
        ...,
        description="LLM inference duration (ms)",
        ge=0.0
    )
    cache_lookup_ms: float = Field(
        ...,
        description="Cache lookup duration (ms)",
        ge=0.0
    )
    agent_coordination_ms: float = Field(
        ...,
        description="Agent coordination overhead (ms)",
        ge=0.0
    )
    was_cached: bool = Field(
        ...,
        description="Whether response was served from cache"
    )
    cache_hit_rate: float = Field(
        ...,
        description="Overall cache hit rate (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_latency_ms": 185.5,
                "rag_retrieval_ms": 45.2,
                "llm_inference_ms": 125.0,
                "cache_lookup_ms": 2.5,
                "agent_coordination_ms": 12.8,
                "was_cached": False,
                "cache_hit_rate": 0.75
            }
        }


class CacheMetadata(BaseModel):
    """
    Cache metadata tracking
    
    Provides detailed information about cache entries and their lifecycle.
    
    Attributes:
        cache_key: Unique cache key
        cache_level: Cache level (memory/redis/miss)
        hit_rate: Cache hit rate for this key
        ttl_remaining_seconds: Time to live remaining
        cache_size_bytes: Size of cached entry
        last_accessed: Last access timestamp
    
    Example:
        >>> metadata = CacheMetadata(
        ...     cache_key="query_hash_abc123",
        ...     cache_level="memory",
        ...     hit_rate=0.85,
        ...     ttl_remaining_seconds=420,
        ...     cache_size_bytes=2048,
        ...     last_accessed=datetime.now(timezone.utc)
        ... )
    """
    cache_key: str = Field(
        ...,
        description="Unique cache key",
        min_length=1,
        max_length=255
    )
    cache_level: Literal['memory', 'redis', 'miss'] = Field(
        ...,
        description="Cache level"
    )
    hit_rate: float = Field(
        ...,
        description="Cache hit rate (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    ttl_remaining_seconds: int = Field(
        ...,
        description="Time to live remaining",
        ge=0
    )
    cache_size_bytes: int = Field(
        ...,
        description="Size of cached entry in bytes",
        ge=0
    )
    last_accessed: datetime = Field(
        ...,
        description="Last access timestamp"
    )
    
    @field_validator('last_accessed')
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware"""
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "cache_key": "query_hash_5d41402abc4b2a76b9719d911017c592",
                "cache_level": "memory",
                "hit_rate": 0.85,
                "ttl_remaining_seconds": 420,
                "cache_size_bytes": 2048,
                "last_accessed": "2025-10-12T10:00:00Z"
            }
        }


class CacheInteraction(BaseModel):
    """
    Cache interaction tracking
    
    Records individual cache operations for monitoring and debugging.
    
    Attributes:
        operation: Cache operation type
        cache_level: Cache level where operation occurred
        key: Cache key
        latency_ms: Operation latency
        data_size_bytes: Optional data size for set operations
        ttl_seconds: Optional TTL for set operations
    
    Example:
        >>> interaction = CacheInteraction(
        ...     operation="hit",
        ...     cache_level="memory",
        ...     key="query_abc123",
        ...     latency_ms=1.5
        ... )
    """
    operation: Literal['hit', 'miss', 'set', 'invalidate'] = Field(
        ...,
        description="Cache operation type"
    )
    cache_level: Literal['memory', 'redis'] = Field(
        ...,
        description="Cache level"
    )
    key: str = Field(
        ...,
        description="Cache key",
        min_length=1,
        max_length=255
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
    
    class Config:
        json_schema_extra = {
            "example": {
                "operation": "hit",
                "cache_level": "memory",
                "key": "query_hash_5d41402abc",
                "latency_ms": 1.5,
                "data_size_bytes": None,
                "ttl_seconds": None
            }
        }


class CachedAdviceResponse(BaseModel):
    """
    Cached advice response model
    
    Stores complete advice responses with performance tracking
    and agent execution traces for caching optimization.
    
    Attributes:
        query_hash: Hash of the query for cache key
        advice_content: Generated advice content
        generated_at: Generation timestamp
        cache_ttl_seconds: Cache time-to-live
        performance_metrics: Performance tracking metrics
        agent_execution_trace: Agent execution steps
    
    Example:
        >>> cached_response = CachedAdviceResponse(
        ...     query_hash="5d41402abc4b2a76b9719d911017c592",
        ...     advice_content="Your personalized loan advice...",
        ...     cache_ttl_seconds=600,
        ...     performance_metrics=metrics,
        ...     agent_execution_trace=[step1, step2, step3]
        ... )
    """
    query_hash: str = Field(
        ...,
        description="Hash of the query for cache key",
        min_length=32,
        max_length=128
    )
    advice_content: str = Field(
        ...,
        description="Generated advice content",
        min_length=1
    )
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Generation timestamp"
    )
    cache_ttl_seconds: int = Field(
        600,
        description="Cache time-to-live (default 10 minutes)",
        ge=0
    )
    performance_metrics: ResponseMetrics = Field(
        ...,
        description="Performance tracking metrics"
    )
    agent_execution_trace: List[AgentExecutionStep] = Field(
        ...,
        description="Agent execution steps"
    )
    
    @field_validator('generated_at')
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware"""
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "query_hash": "5d41402abc4b2a76b9719d911017c592",
                "advice_content": "Based on your query about mortgage rates...",
                "generated_at": "2025-10-12T10:00:00Z",
                "cache_ttl_seconds": 600,
                "performance_metrics": {
                    "total_latency_ms": 185.5,
                    "rag_retrieval_ms": 45.2,
                    "llm_inference_ms": 125.0,
                    "cache_lookup_ms": 2.5,
                    "agent_coordination_ms": 12.8,
                    "was_cached": False,
                    "cache_hit_rate": 0.75
                },
                "agent_execution_trace": []
            }
        }

