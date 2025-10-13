"""
FAISS index performance tracking and metadata models

Supports:
- FAISS index performance metrics tracking
- Hot-swap index management
- Memory usage monitoring
- Search latency tracking
- Index build performance
"""
from typing import Literal, Dict, Any, Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator, model_validator


class IndexPerformanceMetrics(BaseModel):
    """
    FAISS index performance metrics data model
    
    Tracks search latency, memory usage, and throughput for
    performance monitoring and optimization.
    
    Attributes:
        p95_search_latency_ms: 95th percentile search latency in milliseconds
        p99_search_latency_ms: 99th percentile search latency in milliseconds
        memory_usage_percent: Memory usage as percentage of available
        faiss_latency_percent_of_request: FAISS latency as % of total request time
        search_throughput_qps: Search throughput in queries per second
    
    Example:
        >>> metrics = IndexPerformanceMetrics(
        ...     p95_search_latency_ms=50.0,
        ...     p99_search_latency_ms=95.0,
        ...     memory_usage_percent=35.5,
        ...     faiss_latency_percent_of_request=25.0,
        ...     search_throughput_qps=1000.0
        ... )
    """
    p95_search_latency_ms: float = Field(
        ...,
        description="95th percentile search latency in milliseconds",
        ge=0.0
    )
    p99_search_latency_ms: float = Field(
        ...,
        description="99th percentile search latency in milliseconds",
        ge=0.0
    )
    memory_usage_percent: float = Field(
        ...,
        description="Memory usage as percentage of available",
        ge=0.0,
        le=100.0
    )
    faiss_latency_percent_of_request: float = Field(
        ...,
        description="FAISS latency as percentage of total request time",
        ge=0.0,
        le=100.0
    )
    search_throughput_qps: float = Field(
        ...,
        description="Search throughput in queries per second",
        ge=0.0
    )
    
    @field_validator('p95_search_latency_ms', 'p99_search_latency_ms')
    @classmethod
    def validate_non_negative_latency(cls, v: float) -> float:
        """Ensure latency values are non-negative"""
        if v < 0:
            raise ValueError("Latency must be non-negative")
        return v
    
    @field_validator('p99_search_latency_ms')
    @classmethod
    def validate_p99_greater_than_p95(cls, v: float, info) -> float:
        """Ensure P99 latency is >= P95 latency"""
        p95 = info.data.get('p95_search_latency_ms')
        if p95 is not None and v < p95:
            raise ValueError("P99 latency must be >= P95 latency")
        return v
    
    @field_validator('search_throughput_qps')
    @classmethod
    def validate_non_negative_throughput(cls, v: float) -> float:
        """Ensure throughput is non-negative"""
        if v < 0:
            raise ValueError("Throughput must be non-negative")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "p95_search_latency_ms": 50.0,
                "p99_search_latency_ms": 95.0,
                "memory_usage_percent": 35.5,
                "faiss_latency_percent_of_request": 25.0,
                "search_throughput_qps": 1000.0
            }
        }


class FAISSIndexMetadata(BaseModel):
    """
    FAISS index metadata data model
    
    Tracks index configuration, performance metrics, and hot-swap status
    for FAISS vector search indexes.
    
    Attributes:
        index_version: Index version identifier (e.g., "v42")
        index_type: FAISS index type
        vector_count: Number of vectors in index
        dimensions: Vector dimensionality
        memory_size_mb: Index memory size in megabytes
        build_time_seconds: Time taken to build index
        performance_metrics: Performance tracking metrics
        hot_swap_status: Current hot-swap status
    
    Example:
        >>> metadata = FAISSIndexMetadata(
        ...     index_version="v42",
        ...     index_type="IndexIVFFlat",
        ...     vector_count=500000,
        ...     dimensions=384,
        ...     memory_size_mb=750.0,
        ...     build_time_seconds=15.5,
        ...     performance_metrics=metrics,
        ...     hot_swap_status="active"
        ... )
    """
    index_version: str = Field(
        ...,
        description="Index version identifier",
        min_length=1,
        max_length=50
    )
    index_type: Literal['IndexFlatIP', 'IndexIVFFlat'] = Field(
        ...,
        description="FAISS index type"
    )
    vector_count: int = Field(
        ...,
        description="Number of vectors in index",
        ge=0
    )
    dimensions: int = Field(
        ...,
        description="Vector dimensionality",
        ge=1
    )
    memory_size_mb: float = Field(
        ...,
        description="Index memory size in megabytes",
        ge=0.0
    )
    build_time_seconds: float = Field(
        ...,
        description="Time taken to build index in seconds",
        ge=0.0
    )
    performance_metrics: IndexPerformanceMetrics = Field(
        ...,
        description="Performance tracking metrics"
    )
    hot_swap_status: str = Field(
        ...,
        description="Current hot-swap status",
        max_length=50
    )
    
    @field_validator('dimensions')
    @classmethod
    def validate_dimensions(cls, v: int) -> int:
        """Validate vector dimensions"""
        common_dimensions = [128, 256, 384, 512, 768, 1024, 1536]
        if v not in common_dimensions:
            # Warning but don't fail
            pass
        return v
    
    @field_validator('memory_size_mb', 'build_time_seconds')
    @classmethod
    def validate_non_negative(cls, v: float) -> float:
        """Ensure values are non-negative"""
        if v < 0:
            raise ValueError("Value must be non-negative")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "index_version": "v42",
                "index_type": "IndexIVFFlat",
                "vector_count": 500000,
                "dimensions": 384,
                "memory_size_mb": 750.5,
                "build_time_seconds": 15.75,
                "performance_metrics": {
                    "p95_search_latency_ms": 50.0,
                    "p99_search_latency_ms": 95.0,
                    "memory_usage_percent": 35.5,
                    "faiss_latency_percent_of_request": 25.0,
                    "search_throughput_qps": 1000.0
                },
                "hot_swap_status": "active"
            }
        }


class MigrationTriggers(BaseModel):
    """
    FAISS index migration trigger thresholds
    
    Defines thresholds for automatic migration from IndexFlatIP
    to IndexIVFFlat when scaling beyond 500K vectors.
    
    Attributes:
        vector_count_threshold: Trigger migration at this vector count (500K)
        p95_latency_threshold_ms: Trigger on P95 latency exceeding threshold
        memory_threshold_percent: Trigger on memory usage exceeding threshold
        faiss_latency_threshold_percent: Trigger on FAISS latency % exceeding threshold
        early_warning_vector_count: Early warning threshold (400K)
        early_warning_latency_ms: Early warning latency threshold
        growth_rate_projection_days: Days to project growth for proactive scaling
    
    Example:
        >>> triggers = MigrationTriggers()  # Uses all defaults
    """
    vector_count_threshold: int = Field(
        500000,
        description="Trigger migration at this vector count",
        ge=0
    )
    p95_latency_threshold_ms: float = Field(
        200.0,
        description="P95 latency threshold for migration",
        ge=0.0
    )
    memory_threshold_percent: float = Field(
        50.0,
        description="Memory usage threshold for migration",
        ge=0.0,
        le=100.0
    )
    faiss_latency_threshold_percent: float = Field(
        20.0,
        description="FAISS latency % threshold for migration",
        ge=0.0,
        le=100.0
    )
    early_warning_vector_count: int = Field(
        400000,
        description="Early warning vector count threshold",
        ge=0
    )
    early_warning_latency_ms: float = Field(
        100.0,
        description="Early warning latency threshold",
        ge=0.0
    )
    growth_rate_projection_days: int = Field(
        30,
        description="Days to project growth for proactive scaling",
        ge=1
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "vector_count_threshold": 500000,
                "p95_latency_threshold_ms": 200.0,
                "memory_threshold_percent": 50.0,
                "faiss_latency_threshold_percent": 20.0,
                "early_warning_vector_count": 400000,
                "early_warning_latency_ms": 100.0,
                "growth_rate_projection_days": 30
            }
        }


class EnhancedIndexPerformanceMetrics(BaseModel):
    """
    Enhanced FAISS index performance metrics with migration detection
    
    Automatically detects when migration is required based on thresholds.
    
    Attributes:
        p95_search_latency_ms: 95th percentile search latency
        p99_search_latency_ms: 99th percentile search latency
        memory_usage_percent: Memory usage percentage
        faiss_latency_percent_of_request: FAISS latency as % of request time
        requires_migration: Automatically set based on thresholds
        migration_reason: Reason for migration if required
    
    Example:
        >>> metrics = EnhancedIndexPerformanceMetrics(
        ...     p95_search_latency_ms=250.0,  # Exceeds threshold!
        ...     p99_search_latency_ms=300.0,
        ...     memory_usage_percent=40.0,
        ...     faiss_latency_percent_of_request=15.0
        ... )
        >>> assert metrics.requires_migration == True
    """
    p95_search_latency_ms: float = Field(..., ge=0.0)
    p99_search_latency_ms: float = Field(..., ge=0.0)
    memory_usage_percent: float = Field(..., ge=0.0, le=100.0)
    faiss_latency_percent_of_request: float = Field(..., ge=0.0, le=100.0)
    requires_migration: bool = Field(False, description="Migration required flag")
    migration_reason: Optional[str] = Field(None, description="Reason for migration")
    
    @model_validator(mode='after')
    def check_migration_triggers(self):
        """Check if any migration triggers are exceeded"""
        triggers = MigrationTriggers()
        reasons = []
        
        if self.p95_search_latency_ms > triggers.p95_latency_threshold_ms:
            reasons.append(
                f"P95 latency ({self.p95_search_latency_ms}ms) exceeds threshold ({triggers.p95_latency_threshold_ms}ms)"
            )
        
        if self.memory_usage_percent > triggers.memory_threshold_percent:
            reasons.append(
                f"Memory usage ({self.memory_usage_percent}%) exceeds threshold ({triggers.memory_threshold_percent}%)"
            )
        
        if self.faiss_latency_percent_of_request > triggers.faiss_latency_threshold_percent:
            reasons.append(
                f"FAISS latency % ({self.faiss_latency_percent_of_request}%) exceeds threshold ({triggers.faiss_latency_threshold_percent}%)"
            )
        
        if reasons:
            self.requires_migration = True
            self.migration_reason = "; ".join(reasons)
        
        return self


class FAISSIndex(BaseModel):
    """
    FAISS index model with versioning and migration support
    
    Comprehensive index representation with performance metrics
    and migration trigger monitoring.
    
    Attributes:
        version: Index version identifier
        index_type: FAISS index type (IndexFlatIP or IndexIVFFlat)
        vector_count: Number of vectors in index
        dimensions: Vector dimensionality (default 384)
        memory_size_mb: Index memory size in MB
        build_time_seconds: Time taken to build index
        minio_path: Path to index in MinIO storage
        performance_metrics: Performance metrics
        migration_triggers: Migration trigger thresholds
    
    Example:
        >>> index = FAISSIndex(
        ...     version="v42",
        ...     vector_count=450000,
        ...     minio_path="s3://bucket/indexes/v42"
        ... )
    """
    version: str = Field(..., description="Index version identifier")
    index_type: str = Field("IndexFlatIP", description="FAISS index type")
    vector_count: int = Field(..., description="Number of vectors", ge=0)
    dimensions: int = Field(384, description="Vector dimensionality", ge=1)
    memory_size_mb: float = Field(..., description="Index memory size in MB", ge=0.0)
    build_time_seconds: float = Field(..., description="Index build time", ge=0.0)
    minio_path: str = Field(..., description="Path to index in MinIO")
    performance_metrics: EnhancedIndexPerformanceMetrics = Field(
        ...,
        description="Performance metrics with migration detection"
    )
    migration_triggers: MigrationTriggers = Field(
        default_factory=MigrationTriggers,
        description="Migration trigger thresholds"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "version": "v42",
                "index_type": "IndexFlatIP",
                "vector_count": 450000,
                "dimensions": 384,
                "memory_size_mb": 750.5,
                "build_time_seconds": 45.2,
                "minio_path": "s3://apfa-indexes/v42/index.faiss",
                "performance_metrics": {
                    "p95_search_latency_ms": 75.0,
                    "p99_search_latency_ms": 120.0,
                    "memory_usage_percent": 45.0,
                    "faiss_latency_percent_of_request": 15.0,
                    "requires_migration": False,
                    "migration_reason": None
                },
                "migration_triggers": {
                    "vector_count_threshold": 500000,
                    "p95_latency_threshold_ms": 200.0,
                    "memory_threshold_percent": 50.0,
                    "faiss_latency_threshold_percent": 20.0
                }
            }
        }


class HotSwapStatus(BaseModel):
    """
    FAISS index hot-swap status
    
    Tracks the status of index hot-swap operations for
    zero-downtime deployments.
    
    Attributes:
        is_ready: Whether index is ready for hot-swap
        swap_in_progress: Whether swap is currently in progress
        estimated_completion_time: Optional completion time estimate
    
    Example:
        >>> status = HotSwapStatus(
        ...     is_ready=True,
        ...     swap_in_progress=False
        ... )
    """
    is_ready: bool = Field(..., description="Whether index is ready for hot-swap")
    swap_in_progress: bool = Field(..., description="Whether swap is in progress")
    estimated_completion_time: Optional[datetime] = Field(
        None,
        description="Estimated completion time"
    )
    
    @field_validator('estimated_completion_time')
    @classmethod
    def validate_timezone_aware(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure timestamp is timezone-aware"""
        if v and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v


class MigrationReadiness(BaseModel):
    """
    Index migration readiness assessment
    
    Evaluates readiness for migrating from IndexFlatIP to IndexIVFFlat.
    
    Attributes:
        can_migrate: Whether migration is possible
        blocking_issues: List of issues blocking migration
        readiness_score: Overall readiness score (0.0-1.0)
    
    Example:
        >>> readiness = MigrationReadiness(
        ...     can_migrate=True,
        ...     blocking_issues=[],
        ...     readiness_score=0.95
        ... )
    """
    can_migrate: bool = Field(..., description="Whether migration is possible")
    blocking_issues: List[str] = Field(
        default_factory=list,
        description="Issues blocking migration"
    )
    readiness_score: float = Field(
        ...,
        description="Readiness score (0.0-1.0)",
        ge=0.0,
        le=1.0
    )


class EnhancedIndexMetadata(BaseModel):
    """
    Enhanced FAISS index metadata with hot-swap and migration support
    
    Comprehensive metadata for index management and optimization.
    
    Attributes:
        index_version: Index version identifier
        vector_count: Number of vectors in index
        last_updated: Last update timestamp
        performance_characteristics: Performance metrics
        hot_swap_status: Hot-swap operation status
        migration_readiness: Migration readiness assessment
    
    Example:
        >>> metadata = EnhancedIndexMetadata(
        ...     index_version="v42",
        ...     vector_count=450000,
        ...     performance_characteristics=perf_metrics,
        ...     hot_swap_status=swap_status,
        ...     migration_readiness=readiness
        ... )
    """
    index_version: str = Field(..., description="Index version identifier")
    vector_count: int = Field(..., description="Number of vectors", ge=0)
    last_updated: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp"
    )
    performance_characteristics: IndexPerformanceMetrics = Field(
        ...,
        description="Performance metrics"
    )
    hot_swap_status: HotSwapStatus = Field(..., description="Hot-swap status")
    migration_readiness: MigrationReadiness = Field(..., description="Migration readiness")
    
    @field_validator('last_updated')
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware"""
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v


class RAGRetrievalResult(BaseModel):
    """
    RAG retrieval result model
    
    Captures retrieval results with performance tracking.
    
    Attributes:
        retrieved_documents: List of retrieved document snippets
        similarity_scores: Corresponding similarity scores
        retrieval_time_ms: Time taken for retrieval
        index_version: Index version used
        search_parameters: Search parameters used
        performance_metrics: Performance tracking metrics
    
    Example:
        >>> result = RAGRetrievalResult(
        ...     retrieved_documents=["doc1", "doc2", "doc3"],
        ...     similarity_scores=[0.92, 0.88, 0.85],
        ...     retrieval_time_ms=45.2,
        ...     index_version="v42",
        ...     search_parameters={"top_k": 5},
        ...     performance_metrics={"cache_hit": 0.0}
        ... )
    """
    retrieved_documents: List[str] = Field(..., description="Retrieved document snippets")
    similarity_scores: List[float] = Field(..., description="Similarity scores")
    retrieval_time_ms: float = Field(..., description="Retrieval time (ms)", ge=0.0)
    index_version: str = Field(..., description="Index version used")
    search_parameters: Dict[str, Any] = Field(..., description="Search parameters")
    performance_metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="Performance metrics"
    )
    
    @field_validator('similarity_scores')
    @classmethod
    def validate_scores_length(cls, v: List[float], info) -> List[float]:
        """Ensure similarity_scores matches retrieved_documents length"""
        documents = info.data.get('retrieved_documents', [])
        if len(v) != len(documents):
            raise ValueError(
                f"similarity_scores length ({len(v)}) must match "
                f"retrieved_documents length ({len(documents)})"
            )
        return v
    
    @field_validator('similarity_scores')
    @classmethod
    def validate_score_range(cls, v: List[float]) -> List[float]:
        """Ensure all scores are in valid range"""
        for score in v:
            if not 0.0 <= score <= 1.0:
                raise ValueError(f"Similarity score {score} must be between 0.0 and 1.0")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "retrieved_documents": [
                    "Federal lending guidelines require...",
                    "Mortgage rates are determined by...",
                    "Loan eligibility criteria include..."
                ],
                "similarity_scores": [0.92, 0.88, 0.85],
                "retrieval_time_ms": 45.2,
                "index_version": "v42",
                "search_parameters": {
                    "top_k": 5,
                    "similarity_threshold": 0.7
                },
                "performance_metrics": {
                    "cache_hit_rate": 0.75,
                    "faiss_latency_ms": 40.0
                }
            }
        }

