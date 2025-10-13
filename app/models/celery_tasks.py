"""
Celery task orchestration data models

Provides structured definitions for:
- Embedding batch processing tasks
- FAISS index building tasks
- Task status tracking
- Performance metrics
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class TaskStatusEnum(str, Enum):
    """Celery task status values"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"


class EmbeddingBatchTask(BaseModel):
    """
    Embedding batch processing task definition
    
    Processes 1,000 documents per batch with high priority
    in the 'embedding' queue.
    
    Attributes:
        task_id: Unique task identifier
        batch_id: Batch identifier
        document_ids: List of document IDs to process
        batch_size: Number of documents (default 1000)
        queue: Celery queue name (default 'embedding')
        priority: Task priority 1-10 (default 9)
        target_completion_seconds: Target completion time (default 1s)
        model_version: Embedding model version
        processing_options: Additional processing options
    
    Example:
        >>> task = EmbeddingBatchTask(
        ...     task_id="task_123",
        ...     batch_id="batch_456",
        ...     document_ids=["doc_1", "doc_2", ...],
        ...     batch_size=1000
        ... )
    """
    task_id: str = Field(..., description="Unique task identifier")
    batch_id: str = Field(..., description="Batch identifier")
    document_ids: List[str] = Field(..., description="Document IDs to process")
    batch_size: int = Field(1000, description="Number of documents per batch", ge=1, le=1000)
    queue: str = Field("embedding", description="Celery queue name")
    priority: int = Field(9, description="Task priority (1-10)", ge=1, le=10)
    target_completion_seconds: float = Field(1.0, description="Target completion time")
    model_version: str = Field("all-MiniLM-L6-v2", description="Embedding model version")
    processing_options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional processing options"
    )
    
    @field_validator('batch_size')
    @classmethod
    def validate_batch_size(cls, v: int, info) -> int:
        """Ensure batch size matches document count"""
        document_ids = info.data.get('document_ids', [])
        if document_ids and len(document_ids) != v:
            raise ValueError(f"Batch size ({v}) doesn't match document count ({len(document_ids)})")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task_550e8400-e29b-41d4-a716-446655440000",
                "batch_id": "batch_12345",
                "document_ids": ["doc_1", "doc_2", "doc_3"],
                "batch_size": 1000,
                "queue": "embedding",
                "priority": 9,
                "target_completion_seconds": 1.0,
                "model_version": "all-MiniLM-L6-v2",
                "processing_options": {"normalize": True}
            }
        }


class IndexBuildTask(BaseModel):
    """
    FAISS index building task definition
    
    Constructs FAISS indexes from embedding batches with support
    for scheduled rebuilds and on-demand generation.
    
    Attributes:
        task_id: Unique task identifier
        index_version: Index version identifier
        index_type: FAISS index type
        embedding_batch_paths: Paths to embedding batches
        queue: Celery queue name (default 'indexing')
        priority: Task priority 1-10 (default 7)
        scheduled_build: Whether this is a scheduled rebuild
        trigger_type: Build trigger type (scheduled/on-demand)
        optimization_options: Index optimization options
    
    Example:
        >>> task = IndexBuildTask(
        ...     task_id="task_789",
        ...     index_version="v42",
        ...     index_type="IndexIVFFlat",
        ...     embedding_batch_paths=["s3://bucket/batch1", ...]
        ... )
    """
    task_id: str = Field(..., description="Unique task identifier")
    index_version: str = Field(..., description="Index version identifier")
    index_type: str = Field("IndexFlatIP", description="FAISS index type")
    embedding_batch_paths: List[str] = Field(..., description="Paths to embedding batches")
    queue: str = Field("indexing", description="Celery queue name")
    priority: int = Field(7, description="Task priority (1-10)", ge=1, le=10)
    scheduled_build: bool = Field(False, description="Whether this is a scheduled rebuild")
    trigger_type: str = Field("on-demand", description="Build trigger type")
    optimization_options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Index optimization options"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task_550e8400-e29b-41d4-a716-446655440000",
                "index_version": "v42",
                "index_type": "IndexIVFFlat",
                "embedding_batch_paths": [
                    "s3://apfa-embeddings/batch_001.npy",
                    "s3://apfa-embeddings/batch_002.npy"
                ],
                "queue": "indexing",
                "priority": 7,
                "scheduled_build": False,
                "trigger_type": "on-demand",
                "optimization_options": {"normalize": True, "nlist": 100}
            }
        }


class TaskStatus(BaseModel):
    """
    Celery task status tracking
    
    Tracks lifecycle and performance of Celery jobs.
    
    Attributes:
        task_id: Celery task ID
        task_name: Task name
        queue: Queue where task is running
        priority: Task priority
        status: Current task status
        started_at: Start timestamp
        completed_at: Completion timestamp
        execution_time_seconds: Execution duration
        worker_id: Worker processing the task
        retry_count: Number of retries
        error_message: Error message if failed
        performance_metrics: Performance tracking metrics
    
    Example:
        >>> status = TaskStatus(
        ...     task_id="task_123",
        ...     task_name="embed_document_batch",
        ...     queue="embedding",
        ...     priority=9,
        ...     status="success"
        ... )
    """
    task_id: str = Field(..., description="Celery task ID")
    task_name: str = Field(..., description="Task name")
    queue: str = Field(..., description="Queue name")
    priority: int = Field(..., ge=1, le=10, description="Task priority")
    status: TaskStatusEnum = Field(..., description="Current task status")
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Start timestamp"
    )
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    execution_time_seconds: Optional[float] = Field(None, description="Execution duration", ge=0)
    worker_id: Optional[str] = Field(None, description="Worker ID")
    retry_count: int = Field(0, description="Number of retries", ge=0)
    error_message: Optional[str] = Field(None, description="Error message if failed")
    performance_metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Performance tracking metrics"
    )
    
    @field_validator('started_at', 'completed_at')
    @classmethod
    def validate_timezone_aware(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure timestamps are timezone-aware"""
        if v and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v
    
    @field_validator('completed_at')
    @classmethod
    def validate_completion_after_start(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Ensure completion is after start"""
        if v:
            started_at = info.data.get('started_at')
            if started_at and v < started_at:
                raise ValueError("completed_at must be after started_at")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task_550e8400-e29b-41d4-a716-446655440000",
                "task_name": "embed_document_batch",
                "queue": "embedding",
                "priority": 9,
                "status": "success",
                "started_at": "2025-10-11T14:30:00Z",
                "completed_at": "2025-10-11T14:30:02Z",
                "execution_time_seconds": 2.0,
                "worker_id": "worker_1",
                "retry_count": 0,
                "error_message": None,
                "performance_metrics": {
                    "documents_processed": 1000,
                    "throughput_docs_per_sec": 500.0,
                    "avg_embedding_time_ms": 2.0
                }
            }
        }

