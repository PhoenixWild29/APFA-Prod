"""
Document upload data models for metadata and status tracking

Supports:
- File metadata capture
- Upload status tracking
- Processing progress monitoring
- Error tracking and reporting
"""
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum
import uuid


class UploadState(str, Enum):
    """Upload processing states"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    VALIDATION_ERROR = "validation_error"


class DocumentMetadata(BaseModel):
    """
    Document upload metadata data model
    
    Captures essential metadata about uploaded files for tracking
    and correlation throughout the processing pipeline.
    
    Attributes:
        upload_session_id: Unique upload session identifier (UUID)
        file_name: Original filename
        file_type: File MIME type
        file_extension: File extension (e.g., ".pdf")
        file_size_bytes: File size in bytes
        upload_timestamp: UTC timestamp when uploaded
        uploaded_by_user_id: User ID who uploaded the file
        checksum: Optional file checksum (MD5/SHA256)
    
    Example:
        >>> metadata = DocumentMetadata(
        ...     file_name="financial_report.pdf",
        ...     file_type="application/pdf",
        ...     file_extension=".pdf",
        ...     file_size_bytes=1024000,
        ...     uploaded_by_user_id="user_123"
        ... )
    """
    upload_session_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique upload session identifier (UUID)",
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    )
    file_name: str = Field(
        ...,
        description="Original filename",
        min_length=1,
        max_length=255
    )
    file_type: str = Field(
        ...,
        description="File MIME type",
        max_length=100
    )
    file_extension: str = Field(
        ...,
        description="File extension (e.g., .pdf)",
        pattern=r"^\.[a-zA-Z0-9]+$",
        max_length=10
    )
    file_size_bytes: int = Field(
        ...,
        description="File size in bytes",
        ge=0
    )
    upload_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when uploaded"
    )
    uploaded_by_user_id: str = Field(
        ...,
        description="User ID who uploaded the file",
        min_length=1,
        max_length=255
    )
    checksum: Optional[str] = Field(
        None,
        description="File checksum (MD5 or SHA256)",
        max_length=128
    )
    
    @field_validator('upload_timestamp')
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware"""
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v
    
    @field_validator('upload_session_id')
    @classmethod
    def validate_uuid_format(cls, v: str) -> str:
        """Validate UUID format"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid UUID format: {v}")
    
    class Config:
        json_schema_extra = {
            "example": {
                "upload_session_id": "550e8400-e29b-41d4-a716-446655440000",
                "file_name": "financial_report_Q1_2025.pdf",
                "file_type": "application/pdf",
                "file_extension": ".pdf",
                "file_size_bytes": 1024000,
                "upload_timestamp": "2025-10-11T14:30:00Z",
                "uploaded_by_user_id": "user_12345",
                "checksum": "5d41402abc4b2a76b9719d911017c592"
            }
        }


class UploadStatus(BaseModel):
    """
    Upload status tracking data model
    
    Tracks the progression of document uploads from initial upload
    through processing completion or failure.
    
    Attributes:
        upload_session_id: Upload session identifier (matches DocumentMetadata)
        current_state: Current processing state
        progress_percentage: Processing progress (0.0-100.0)
        started_at: UTC timestamp when processing started
        completed_at: Optional timestamp when processing completed
        error_message: Optional error message if failed
        failure_reason: Optional detailed failure reason
        retry_count: Number of retry attempts
        last_state_change: Timestamp of last state change
    
    Example:
        >>> status = UploadStatus(
        ...     upload_session_id="550e8400-e29b-41d4-a716-446655440000",
        ...     current_state="processing",
        ...     progress_percentage=45.0
        ... )
    """
    upload_session_id: str = Field(
        ...,
        description="Upload session identifier (UUID)",
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    )
    current_state: UploadState = Field(
        ...,
        description="Current processing state"
    )
    progress_percentage: float = Field(
        default=0.0,
        description="Processing progress (0.0-100.0)",
        ge=0.0,
        le=100.0
    )
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when processing started"
    )
    completed_at: Optional[datetime] = Field(
        None,
        description="UTC timestamp when processing completed"
    )
    error_message: Optional[str] = Field(
        None,
        description="Error message if failed",
        max_length=1000
    )
    failure_reason: Optional[str] = Field(
        None,
        description="Detailed failure reason",
        max_length=2000
    )
    retry_count: int = Field(
        default=0,
        description="Number of retry attempts",
        ge=0
    )
    last_state_change: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of last state change"
    )
    
    @field_validator('started_at', 'completed_at', 'last_state_change')
    @classmethod
    def validate_timezone_aware(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure datetime fields are timezone-aware"""
        if v and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v
    
    @field_validator('upload_session_id')
    @classmethod
    def validate_uuid_format(cls, v: str) -> str:
        """Validate UUID format"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid UUID format: {v}")
    
    @field_validator('completed_at')
    @classmethod
    def validate_completed_after_started(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Ensure completion time is after start time"""
        if v:
            started_at = info.data.get('started_at')
            if started_at and v < started_at:
                raise ValueError("completed_at must be after started_at")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "upload_session_id": "550e8400-e29b-41d4-a716-446655440000",
                "current_state": "processing",
                "progress_percentage": 75.0,
                "started_at": "2025-10-11T14:30:00Z",
                "completed_at": None,
                "error_message": None,
                "failure_reason": None,
                "retry_count": 0,
                "last_state_change": "2025-10-11T14:32:30Z"
            }
        }

