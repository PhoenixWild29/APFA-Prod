"""
Metrics streaming schemas for SSE endpoints
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List


class AgentExecutionMetrics(BaseModel):
    """Agent execution time metrics"""
    retriever_avg_ms: float = Field(..., description="Retriever average execution time")
    analyzer_avg_ms: float = Field(..., description="Analyzer average execution time")
    orchestrator_avg_ms: float = Field(..., description="Orchestrator average execution time")
    total_executions: int = Field(..., description="Total agent executions")


class IndexPerformanceData(BaseModel):
    """FAISS index performance data"""
    search_latency_p50_ms: float = Field(..., description="P50 search latency")
    search_latency_p95_ms: float = Field(..., description="P95 search latency")
    memory_usage_mb: float = Field(..., description="Memory usage")
    throughput_qps: float = Field(..., description="Queries per second")
    vector_count: int = Field(..., description="Total vectors in index")


class CeleryTaskStatistics(BaseModel):
    """Celery task statistics"""
    active_tasks: int = Field(..., description="Active tasks")
    pending_tasks: int = Field(..., description="Pending tasks")
    completed_tasks: int = Field(..., description="Completed tasks")
    failed_tasks: int = Field(..., description="Failed tasks")
    avg_task_duration_ms: float = Field(..., description="Average task duration")


class MetricsStreamData(BaseModel):
    """Complete metrics stream data"""
    timestamp: str = Field(..., description="Metrics timestamp")
    agent_metrics: AgentExecutionMetrics = Field(..., description="Agent execution metrics")
    index_performance: IndexPerformanceData = Field(..., description="Index performance")
    celery_statistics: CeleryTaskStatistics = Field(..., description="Celery statistics")
    system_health: str = Field(..., description="Overall system health")

