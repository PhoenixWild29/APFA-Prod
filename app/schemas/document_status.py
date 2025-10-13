"""
Document processing status schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class PerformanceMetrics(BaseModel):
    """Document processing performance metrics"""
    processing_duration_seconds: float = Field(..., description="Total processing duration")
    file_size_processed_bytes: int = Field(..., description="File size processed")
    throughput_bytes_per_second: float = Field(..., description="Processing throughput")
    extraction_time_ms: Optional[float] = Field(None, description="Text extraction time")
    embedding_time_ms: Optional[float] = Field(None, description="Embedding generation time")
    indexing_time_ms: Optional[float] = Field(None, description="Index insertion time")


class ErrorDetails(BaseModel):
    """Error details for failed processing"""
    error_message: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    suggested_actions: list[str] = Field(..., description="Suggested corrective actions")
    failed_at_stage: str = Field(..., description="Stage where failure occurred")


class DocumentStatus(BaseModel):
    """Document processing status"""
    document_id: str = Field(..., description="Document identifier")
    processing_stage: Literal[
        'uploaded',
        'extracting',
        'embedding',
        'indexing',
        'completed',
        'failed'
    ] = Field(..., description="Current processing stage")
    progress_percentage: float = Field(..., ge=0, le=100, description="Progress percentage")
    estimated_completion_time: Optional[str] = Field(None, description="Estimated completion time")
    
    # Timestamps
    upload_time: str = Field(..., description="Upload timestamp")
    extraction_start: Optional[str] = Field(None, description="Extraction start time")
    embedding_start: Optional[str] = Field(None, description="Embedding start time")
    indexing_start: Optional[str] = Field(None, description="Indexing start time")
    completion_time: Optional[str] = Field(None, description="Completion timestamp")
    
    # Performance metrics
    performance_metrics: Optional[PerformanceMetrics] = Field(None, description="Performance metrics")
    
    # Error details (if failed)
    error_details: Optional[ErrorDetails] = Field(None, description="Error details if failed")
    
    # Additional metadata
    filename: str = Field(..., description="Original filename")
    file_size_bytes: int = Field(..., description="File size")
    content_type: str = Field(..., description="File content type")

