"""
Batch document processing schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class ProcessBatchRequest(BaseModel):
    """Request to process a batch of documents"""
    batch_size: int = Field(..., ge=1, le=1000, description="Number of documents to process (max 1000)")
    priority: int = Field(5, ge=1, le=10, description="Processing priority (1=lowest, 10=highest)")
    source_path: str = Field(..., description="Path to document source")
    processing_options: Dict[str, Any] = Field(default_factory=dict, description="Additional processing options")


class ProcessBatchResponse(BaseModel):
    """Response from batch processing request"""
    task_id: str = Field(..., description="Celery task ID")
    batch_id: str = Field(..., description="Unique batch identifier")
    estimated_completion_time: str = Field(..., description="Estimated completion time (ISO format)")
    status_endpoint: str = Field(..., description="URL to check batch status")
    status: str = Field(..., description="Initial batch status")


class BatchStatusResponse(BaseModel):
    """Real-time batch processing status"""
    batch_id: str = Field(..., description="Batch identifier")
    documents_processed: int = Field(..., description="Number of documents processed")
    total_documents: int = Field(..., description="Total documents in batch")
    completion_percentage: float = Field(..., description="Completion percentage")
    estimated_remaining_seconds: int = Field(..., description="Estimated time remaining")
    processing_rate_docs_per_second: float = Field(..., description="Processing throughput")
    average_embedding_time_ms: float = Field(..., description="Average embedding time")
    worker_utilization_percent: float = Field(..., description="Worker utilization")
    status: str = Field(..., description="Current batch status")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Processing errors")
    started_at: Optional[str] = Field(None, description="Start timestamp")
    completed_at: Optional[str] = Field(None, description="Completion timestamp")


class ProcessAllResponse(BaseModel):
    """Response from process-all request"""
    task_id: str = Field(..., description="Master task ID")
    total_batches: int = Field(..., description="Number of batches created")
    total_documents: int = Field(..., description="Total documents to process")
    estimated_completion_time: str = Field(..., description="Estimated completion time")
    status_endpoints: List[str] = Field(..., description="Status URLs for each batch")

