"""
FAISS index management schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal


class IndexOptimizationOptions(BaseModel):
    """Index optimization options"""
    normalize_vectors: bool = Field(True, description="Normalize vectors before indexing")
    memory_optimization: bool = Field(False, description="Enable memory optimization")
    validation_enabled: bool = Field(True, description="Enable validation checks")


class IndexBuildRequest(BaseModel):
    """Request to build FAISS index"""
    embedding_batch_paths: List[str] = Field(..., description="Paths to embedding batches")
    index_type: Literal['IndexFlatIP', 'IndexIVFFlat'] = Field('IndexFlatIP', description="FAISS index type")
    optimization_options: IndexOptimizationOptions = Field(default_factory=IndexOptimizationOptions)


class IndexBuildResponse(BaseModel):
    """Response from index build request"""
    task_id: str = Field(..., description="Celery task ID")
    index_version: str = Field(..., description="New index version")
    estimated_build_time_seconds: float = Field(..., description="Estimated build time")
    status_endpoint: str = Field(..., description="Status check endpoint")


class PerformanceMetrics(BaseModel):
    """Index performance metrics"""
    p95_search_latency_ms: float = Field(..., description="95th percentile search latency")
    p99_search_latency_ms: float = Field(..., description="99th percentile search latency")
    memory_usage_percent: float = Field(..., description="Memory usage percentage")
    search_throughput_qps: float = Field(..., description="Search queries per second")


class MigrationStatus(BaseModel):
    """Hot-swap migration status"""
    is_migrating: bool = Field(..., description="Whether migration is in progress")
    current_version: str = Field(..., description="Current index version")
    target_version: Optional[str] = Field(None, description="Target version for migration")
    traffic_percentage: float = Field(0.0, description="Traffic percentage on new index")
    migration_phase: str = Field("none", description="Current migration phase")


class IndexStatusResponse(BaseModel):
    """Current index status and metadata"""
    version: str = Field(..., description="Current index version")
    type: str = Field(..., description="Index type")
    vector_count: int = Field(..., description="Number of vectors")
    dimensions: int = Field(..., description="Vector dimensions")
    memory_size_mb: float = Field(..., description="Index memory size in MB")
    build_time_seconds: float = Field(..., description="Time taken to build index")
    performance_metrics: PerformanceMetrics
    migration_status: MigrationStatus
    migration_thresholds: Dict[str, Any] = Field(
        default_factory=dict,
        description="Migration trigger thresholds"
    )


class IndexHotSwapRequest(BaseModel):
    """Request for index hot-swap"""
    new_index_version: str = Field(..., description="Version of new index to swap")
    gradual_migration: bool = Field(True, description="Enable gradual traffic migration")
    rollback_on_regression: bool = Field(True, description="Auto-rollback on performance regression")
    latency_regression_threshold: float = Field(10.0, description="Max latency increase % before rollback")


class IndexHotSwapResponse(BaseModel):
    """Response from hot-swap request"""
    swap_id: str = Field(..., description="Hot-swap operation ID")
    status: str = Field(..., description="Swap operation status")
    current_phase: str = Field(..., description="Current phase of swap operation")
    validation_results: Dict[str, bool] = Field(..., description="Pre-deployment validation results")
    estimated_completion_seconds: float = Field(..., description="Estimated time to complete")

