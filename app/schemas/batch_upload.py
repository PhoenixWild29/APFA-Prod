"""
Batch document upload schemas

Provides request/response models for batch upload operations.
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class FileUploadResult(BaseModel):
    """Individual file upload result"""
    filename: str = Field(..., description="Original filename")
    upload_id: str = Field(..., description="Unique upload identifier")
    status: str = Field(..., description="Upload status")
    file_size_bytes: int = Field(..., description="File size in bytes")
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors")
    processing_task_id: Optional[str] = Field(None, description="Celery task ID")


class BatchUploadResponse(BaseModel):
    """Batch upload response"""
    batch_upload_id: str = Field(..., description="Unique batch identifier")
    total_files: int = Field(..., description="Total files in batch")
    accepted_files: int = Field(..., description="Number of accepted files")
    rejected_files: int = Field(..., description="Number of rejected files")
    completion_percentage: float = Field(..., description="Batch completion percentage")
    upload_results: List[FileUploadResult] = Field(..., description="Individual file results")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

