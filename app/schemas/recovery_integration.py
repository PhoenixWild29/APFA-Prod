"""
Recovery and integration monitoring schemas
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any


class RetryFailedRequest(BaseModel):
    """Request to retry failed documents"""
    failed_document_ids: List[str] = Field(..., description="Document IDs to retry")
    error_type_filter: List[str] = Field(
        default_factory=list,
        description="Filter by error types (empty = retry all)"
    )
    max_retry_attempts: int = Field(3, ge=1, le=10, description="Max retry attempts per document")


class RetryFailedResponse(BaseModel):
    """Response from retry failed operation"""
    retry_batch_id: str = Field(..., description="Retry batch identifier")
    total_documents: int = Field(..., description="Total documents to retry")
    queued_for_retry: int = Field(..., description="Documents queued for retry")
    skipped: int = Field(..., description="Documents skipped")
    task_ids: List[str] = Field(..., description="Celery task IDs")
    failure_analysis: Dict[str, Any] = Field(..., description="Failure analysis report")


class CeleryWorkerStatus(BaseModel):
    """Celery worker health status"""
    worker_name: str
    status: str
    active_tasks: int
    processed_tasks: int
    failed_tasks: int


class CeleryStatusResponse(BaseModel):
    """Celery integration status"""
    active_workers: int = Field(..., description="Number of active workers")
    queue_depths: Dict[str, int] = Field(..., description="Queue depths by queue name")
    task_execution_stats: Dict[str, Any] = Field(..., description="Task execution statistics")
    failed_task_count: int = Field(..., description="Failed task count (last 24h)")
    flower_dashboard_url: str = Field(..., description="Flower dashboard URL")
    workers: List[CeleryWorkerStatus] = Field(..., description="Individual worker status")
    response_time_ms: float = Field(..., description="Health check response time")
    error_rate_percent: float = Field(..., description="Error rate (last 24h)")
    availability_percent: float = Field(..., description="Availability (last 24h)")


class MinIOStatusResponse(BaseModel):
    """MinIO integration status"""
    connectivity_status: str = Field(..., description="Connection status")
    storage_utilization_percent: float = Field(..., description="Storage utilization")
    bucket_health_status: Dict[str, str] = Field(..., description="Health status per bucket")
    data_integrity_checks: Dict[str, bool] = Field(..., description="Data integrity results")
    available_storage_gb: float = Field(..., description="Available storage in GB")
    total_objects: int = Field(..., description="Total objects stored")
    response_time_ms: float = Field(..., description="Health check response time")
    error_rate_percent: float = Field(..., description="Error rate (last 24h)")
    availability_percent: float = Field(..., description="Availability (last 24h)")

