"""
Job management and monitoring schemas
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class ScheduledJob(BaseModel):
    """Scheduled job information"""
    job_name: str = Field(..., description="Job name")
    schedule: str = Field(..., description="Schedule (cron or interval)")
    last_run: Optional[str] = Field(None, description="Last execution time")
    next_run: str = Field(..., description="Next execution time")
    enabled: bool = Field(..., description="Whether job is enabled")


class JobScheduleResponse(BaseModel):
    """Celery Beat schedule response"""
    scheduled_jobs: List[ScheduledJob] = Field(..., description="List of scheduled jobs")
    total_jobs: int = Field(..., description="Total number of scheduled jobs")


class JobTriggerRequest(BaseModel):
    """Manual job trigger request"""
    job_parameters: Dict[str, Any] = Field(default_factory=dict, description="Job parameters")


class JobTriggerResponse(BaseModel):
    """Job trigger response"""
    job_name: str = Field(..., description="Job name")
    task_id: str = Field(..., description="Celery task ID")
    status: str = Field(..., description="Initial status")
    message: str = Field(..., description="Status message")


class PipelinePerformanceMetrics(BaseModel):
    """Pipeline performance metrics"""
    batch_processing_throughput_docs_per_sec: float = Field(..., description="Batch throughput")
    p95_batch_completion_time_seconds: float = Field(..., description="P95 batch time")
    worker_efficiency_percent: float = Field(..., description="Worker efficiency")
    index_building_time_seconds: float = Field(..., description="Index build time")
    system_resource_utilization: Dict[str, float] = Field(..., description="Resource utilization")
    total_documents_processed: int = Field(..., description="Total documents processed")
    failed_documents: int = Field(..., description="Failed document count")


class BottleneckAnalysis(BaseModel):
    """Performance bottleneck analysis"""
    identified_constraints: List[str] = Field(..., description="Identified constraints")
    optimization_opportunities: List[str] = Field(..., description="Optimization suggestions")
    scaling_recommendations: List[str] = Field(..., description="Scaling recommendations")
    current_utilization: Dict[str, float] = Field(..., description="Current utilization metrics")


class ErrorReport(BaseModel):
    """Error report entry"""
    error_id: str = Field(..., description="Error identifier")
    timestamp: str = Field(..., description="Error timestamp")
    error_category: str = Field(..., description="Error category")
    error_message: str = Field(..., description="Error message")
    affected_component: str = Field(..., description="Affected component")
    recovery_recommendation: str = Field(..., description="Recovery recommendation")
    occurrence_count: int = Field(..., description="Number of occurrences")


class RecentErrorsResponse(BaseModel):
    """Recent errors response"""
    errors: List[ErrorReport] = Field(..., description="Recent errors")
    total_errors: int = Field(..., description="Total error count")
    error_rate_per_hour: float = Field(..., description="Error rate")
    most_common_category: str = Field(..., description="Most common error category")

