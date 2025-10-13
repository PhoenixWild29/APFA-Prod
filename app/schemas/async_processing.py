"""
Async processing and status tracking schemas
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, Literal
from datetime import datetime


class AdviceStatusResponse(BaseModel):
    """Advice generation status response"""
    request_id: str = Field(..., description="Unique request identifier")
    processing_status: Literal['queued', 'processing', 'completed', 'failed'] = Field(
        ...,
        description="Current processing status"
    )
    progress_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Processing progress (0-100%)"
    )
    estimated_completion_time: Optional[str] = Field(
        None,
        description="Estimated completion time (ISO format)"
    )
    current_processing_stage: str = Field(
        ...,
        description="Current processing stage"
    )
    stage_specific_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Stage-specific processing metadata"
    )
    created_at: str = Field(..., description="Request creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    result: Optional[Dict[str, Any]] = Field(None, description="Result if completed")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class AsyncAdviceRequest(BaseModel):
    """Async advice generation request response"""
    request_id: str = Field(..., description="Request tracking ID")
    status_url: str = Field(..., description="Status endpoint URL")
    estimated_duration_seconds: int = Field(..., description="Estimated duration")

