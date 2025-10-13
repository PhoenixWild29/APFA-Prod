"""
Upload progress WebSocket message schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal


class UploadProgressMessage(BaseModel):
    """Real-time upload progress message"""
    upload_id: str = Field(..., description="Upload identifier")
    percentage_complete: float = Field(..., ge=0, le=100, description="Progress percentage")
    current_stage: Literal[
        'initializing',
        'uploading',
        'validating',
        'scanning',
        'processing',
        'completed',
        'failed'
    ] = Field(..., description="Current processing stage")
    estimated_completion_time: Optional[str] = Field(None, description="Estimated completion time")
    bytes_uploaded: int = Field(..., description="Bytes uploaded so far")
    total_bytes: int = Field(..., description="Total bytes to upload")
    upload_speed_mbps: float = Field(..., description="Upload speed in MB/s")
    status: str = Field(..., description="Status message")
    error_conditions: List[str] = Field(default_factory=list, description="Any error conditions")
    timestamp: str = Field(..., description="Message timestamp")

