"""
Admin API endpoints for job management and monitoring
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone, timedelta

from app.schemas.job_management import (
    JobScheduleResponse,
    ScheduledJob,
    JobTriggerRequest,
    JobTriggerResponse,
    PipelinePerformanceMetrics,
    BottleneckAnalysis,
    RecentErrorsResponse,
    ErrorReport
)
from app.dependencies import require_admin
from app.tasks import celery_app

router = APIRouter(prefix="/admin", tags=["admin-jobs"])

# Valid job names
VALID_JOBS = [
    "embed_all_documents",
    "build_faiss_index",
    "cleanup_old_embeddings",
    "compute_index_stats"
]


@router.get("/jobs/schedule", response_model=JobScheduleResponse)
async def get_job_schedule(admin: dict = Depends(require_admin)):
    """
    Get Celery Beat scheduled jobs (admin only).
    
    Returns schedule information for all periodic tasks including
    index rebuilds, cleanup tasks, and statistics computation.
    
    Args:
        admin: Authenticated admin user
    
    Returns:
        Scheduled jobs with execution times
    
    Example:
        GET /admin/jobs/schedule
        
        Response:
            {
                "scheduled_jobs": [
                    {
                        "job_name": "hourly_index_rebuild",
                        "schedule": "0 * * * *",
                        "next_run": "2025-10-11T15:00:00Z",
                        "enabled": true
                    },
                    ...
                ],
                "total_jobs": 4
            }
    """
    # In production, query Celery Beat scheduler
    now = datetime.now(timezone.utc)
    
    scheduled_jobs = [
        ScheduledJob(
            job_name="hourly_index_rebuild",
            schedule="0 * * * *",
            last_run=(now - timedelta(hours=1)).isoformat(),
            next_run=(now + timedelta(hours=1)).isoformat(),
            enabled=True
        ),
        ScheduledJob(
            job_name="daily_cleanup",
            schedule="0 2 * * *",
            last_run=(now - timedelta(days=1)).isoformat(),
            next_run=(now + timedelta(days=1) - timedelta(hours=now.hour - 2)).isoformat(),
            enabled=True
        ),
        ScheduledJob(
            job_name="compute_statistics",
            schedule="*/30 * * * *",
            last_run=(now - timedelta(minutes=30)).isoformat(),
            next_run=(now + timedelta(minutes=30)).isoformat(),
            enabled=True
        ),
        ScheduledJob(
            job_name="embed_all_documents",
            schedule="manual",
            last_run=None,
            next_run="manual trigger only",
            enabled=True
        )
    ]
    
    return JobScheduleResponse(
        scheduled_jobs=scheduled_jobs,
        total_jobs=len(scheduled_jobs)
    )


@router.post("/jobs/trigger/{job_name}", response_model=JobTriggerResponse)
async def trigger_job(
    job_name: str,
    request: JobTriggerRequest,
    admin: dict = Depends(require_admin)
):
    """
    Manually trigger a scheduled job (admin only).
    
    Supports triggering document embedding, index building,
    cleanup, and statistics computation jobs.
    
    Args:
        job_name: Name of job to trigger
        request: Job parameters
        admin: Authenticated admin user
    
    Returns:
        Job trigger confirmation with task ID
    
    Raises:
        HTTPException: 400 if job name invalid
    
    Example:
        POST /admin/jobs/trigger/build_faiss_index
        {
            "job_parameters": {"index_type": "IndexIVFFlat"}
        }
    """
    if job_name not in VALID_JOBS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid job name. Valid jobs: {', '.join(VALID_JOBS)}"
        )
    
    # Trigger Celery task
    task = celery_app.send_task(
        job_name,
        kwargs=request.job_parameters,
        queue='admin_jobs'
    )
    
    return JobTriggerResponse(
        job_name=job_name,
        task_id=str(task.id),
        status="queued",
        message=f"Job '{job_name}' triggered successfully"
    )


@router.get("/performance/pipeline", response_model=PipelinePerformanceMetrics)
async def get_pipeline_performance(admin: dict = Depends(require_admin)):
    """
    Get comprehensive pipeline performance metrics (admin only).
    
    Returns throughput, latency, efficiency, and resource utilization
    metrics for the document processing pipeline.
    
    Args:
        admin: Authenticated admin user
    
    Returns:
        Pipeline performance metrics
    
    Example:
        GET /admin/performance/pipeline
        
        Response:
            {
                "batch_processing_throughput_docs_per_sec": 4250.0,
                "p95_batch_completion_time_seconds": 0.95,
                "worker_efficiency_percent": 87.5,
                "index_building_time_seconds": 45.2,
                "system_resource_utilization": {...},
                "total_documents_processed": 1000000,
                "failed_documents": 125
            }
    """
    # In production, query actual metrics from Prometheus/monitoring system
    return PipelinePerformanceMetrics(
        batch_processing_throughput_docs_per_sec=4250.0,
        p95_batch_completion_time_seconds=0.95,
        worker_efficiency_percent=87.5,
        index_building_time_seconds=45.2,
        system_resource_utilization={
            "cpu_percent": 65.0,
            "memory_percent": 42.0,
            "disk_io_percent": 30.0,
            "network_io_mbps": 125.0
        },
        total_documents_processed=1000000,
        failed_documents=125
    )


@router.get("/performance/bottlenecks", response_model=BottleneckAnalysis)
async def analyze_bottlenecks(admin: dict = Depends(require_admin)):
    """
    Analyze performance bottlenecks (admin only).
    
    Identifies constraints, optimization opportunities,
    and provides scaling recommendations.
    
    Args:
        admin: Authenticated admin user
    
    Returns:
        Bottleneck analysis with recommendations
    
    Example:
        GET /admin/performance/bottlenecks
        
        Response:
            {
                "identified_constraints": [
                    "Embedding generation CPU-bound",
                    "Index building memory-intensive"
                ],
                "optimization_opportunities": [...],
                "scaling_recommendations": [...]
            }
    """
    # In production, perform actual analysis of metrics
    return BottleneckAnalysis(
        identified_constraints=[
            "Embedding generation is CPU-bound at 85% utilization",
            "Index building requires 750MB+ memory per worker",
            "Redis connection pool approaching limit (90/100)"
        ],
        optimization_opportunities=[
            "Add 2 more worker nodes to increase parallelism",
            "Implement batch size optimization (currently fixed at 1000)",
            "Enable vector quantization to reduce memory footprint",
            "Migrate from IndexFlatIP to IndexIVFFlat above 500K vectors"
        ],
        scaling_recommendations=[
            "Scale workers horizontally: 4 → 6 workers (+50% throughput)",
            "Increase Redis connection pool: 100 → 200 connections",
            "Upgrade worker instance type for more CPU cores",
            "Implement index sharding for >1M vectors"
        ],
        current_utilization={
            "worker_capacity_percent": 85.0,
            "redis_connections_percent": 90.0,
            "memory_usage_percent": 42.0,
            "throughput_vs_target_percent": 85.0
        }
    )


@router.get("/errors/recent", response_model=RecentErrorsResponse)
async def get_recent_errors(admin: dict = Depends(require_admin)):
    """
    Get recent error reports (admin only).
    
    Provides detailed error information with categorization,
    timestamps, and recovery recommendations.
    
    Args:
        admin: Authenticated admin user
    
    Returns:
        Recent errors with recovery recommendations
    
    Example:
        GET /admin/errors/recent
        
        Response:
            {
                "errors": [...],
                "total_errors": 15,
                "error_rate_per_hour": 2.5,
                "most_common_category": "validation_error"
            }
    """
    # In production, query error logging system
    errors = [
        ErrorReport(
            error_id="err_001",
            timestamp=datetime.now(timezone.utc).isoformat(),
            error_category="validation_error",
            error_message="Invalid document format: PDF extraction failed",
            affected_component="text_extraction",
            recovery_recommendation="Retry with alternative PDF parser or skip document",
            occurrence_count=5
        ),
        ErrorReport(
            error_id="err_002",
            timestamp=(datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat(),
            error_category="embedding_error",
            error_message="Sentence transformer timeout after 30s",
            affected_component="embedding_generation",
            recovery_recommendation="Increase timeout threshold or reduce batch size",
            occurrence_count=3
        )
    ]
    
    return RecentErrorsResponse(
        errors=errors,
        total_errors=15,
        error_rate_per_hour=2.5,
        most_common_category="validation_error"
    )

