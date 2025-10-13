"""
Knowledge base reindexing schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal


class ReindexOperationStatus(BaseModel):
    """Reindexing operation status"""
    operation_id: str = Field(..., description="Unique operation identifier")
    status: Literal['initiated', 'in-progress', 'completed', 'failed'] = Field(
        ...,
        description="Current operation status"
    )
    start_timestamp: str = Field(..., description="Operation start time")
    estimated_completion_time: Optional[str] = Field(None, description="Estimated completion time")
    completion_timestamp: Optional[str] = Field(None, description="Actual completion time")
    documents_processed: int = Field(0, description="Number of documents processed")
    total_documents: int = Field(0, description="Total documents to process")
    progress_percentage: float = Field(0.0, ge=0.0, le=100.0, description="Progress percentage")
    error_message: Optional[str] = Field(None, description="Error message if failed")

