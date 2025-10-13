"""
Knowledge base statistics schemas
"""
from pydantic import BaseModel, Field
from typing import Dict, List


class DocumentStatistics(BaseModel):
    """Document statistics"""
    total_documents: int = Field(..., description="Total document count")
    documents_by_type: Dict[str, int] = Field(..., description="Count by document type")
    documents_by_status: Dict[str, int] = Field(..., description="Count by processing status")
    average_file_size_mb: float = Field(..., description="Average file size in MB")


class ProcessingMetrics(BaseModel):
    """Processing performance metrics"""
    total_processing_time_hours: float = Field(..., description="Total processing time")
    average_processing_duration_seconds: float = Field(..., description="Average processing time")
    success_rate_percent: float = Field(..., description="Processing success rate")
    failure_rate_percent: float = Field(..., description="Processing failure rate")


class IndexPerformance(BaseModel):
    """Index performance data"""
    search_response_time_p95_ms: float = Field(..., description="P95 search response time")
    search_response_time_p99_ms: float = Field(..., description="P99 search response time")
    index_size_mb: float = Field(..., description="Index size in MB")
    vector_count: int = Field(..., description="Total vector count")
    similarity_search_accuracy_percent: float = Field(..., description="Search accuracy")


class StorageUtilization(BaseModel):
    """Storage utilization data"""
    total_storage_used_gb: float = Field(..., description="Total storage used in GB")
    storage_by_document_type: Dict[str, float] = Field(..., description="Storage by type in GB")
    storage_growth_trend_gb_per_day: float = Field(..., description="Daily growth rate")


class DailyAggregation(BaseModel):
    """Daily statistics aggregation"""
    date: str = Field(..., description="Aggregation date")
    documents_processed: int
    average_processing_time_seconds: float
    total_storage_gb: float


class KnowledgeBaseStatsResponse(BaseModel):
    """Complete knowledge base statistics response"""
    document_statistics: DocumentStatistics
    processing_metrics: ProcessingMetrics
    index_performance: IndexPerformance
    storage_utilization: StorageUtilization
    last_30_days_trend: List[DailyAggregation]
    data_freshness_timestamp: str = Field(..., description="Last update timestamp")
    cache_status: str = Field(..., description="Cache hit/miss status")

