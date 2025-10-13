"""
Real-time document processing data models

Supports:
- Document processing event tracking
- WebSocket communication for real-time updates
- Progress monitoring and reporting
- Performance metrics tracking
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator


class DocumentProcessingEvent(BaseModel):
    """
    Document processing event data model
    
    Tracks document processing lifecycle events including upload,
    validation, extraction, embedding, and indexing.
    
    Attributes:
        event_type: Type of processing event
        document_id: Unique document identifier
        timestamp: UTC timestamp of event (timezone-aware)
        status: Current processing status
        progress_percentage: Processing progress (0.0-100.0)
        processing_time_ms: Optional processing duration in milliseconds
        error_message: Optional error message if failed
        metadata: Additional event-specific data
    
    Example:
        >>> event = DocumentProcessingEvent(
        ...     event_type="embedding",
        ...     document_id="doc_12345",
        ...     status="in_progress",
        ...     progress_percentage=45.0,
        ...     metadata={"batch_id": "batch_001", "worker_id": "worker_1"}
        ... )
    """
    event_type: Literal['upload', 'validation', 'extraction', 'embedding', 'indexing'] = Field(
        ...,
        description="Type of processing event"
    )
    document_id: str = Field(
        ...,
        description="Unique document identifier",
        min_length=1,
        max_length=255
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of event"
    )
    status: Literal['started', 'in_progress', 'completed', 'failed'] = Field(
        ...,
        description="Current processing status"
    )
    progress_percentage: float = Field(
        ...,
        description="Processing progress (0.0-100.0)",
        ge=0.0,
        le=100.0
    )
    processing_time_ms: Optional[float] = Field(
        None,
        description="Processing duration in milliseconds",
        ge=0.0
    )
    error_message: Optional[str] = Field(
        None,
        description="Error message if failed",
        max_length=1000
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional event-specific data",
        examples=[{
            "batch_id": "batch_001",
            "worker_id": "worker_1",
            "document_size_bytes": 1024000,
            "page_count": 10
        }]
    )
    
    @field_validator('timestamp')
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware"""
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v
    
    @field_validator('progress_percentage')
    @classmethod
    def validate_progress(cls, v: float) -> float:
        """Ensure progress is within valid range"""
        if not 0.0 <= v <= 100.0:
            raise ValueError("Progress must be between 0.0 and 100.0")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "embedding",
                "document_id": "doc_550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2025-10-11T14:30:00Z",
                "status": "in_progress",
                "progress_percentage": 45.5,
                "processing_time_ms": 1250.5,
                "error_message": None,
                "metadata": {
                    "batch_id": "batch_001",
                    "worker_id": "worker_1",
                    "embedding_model": "all-MiniLM-L6-v2",
                    "dimensions": 384
                }
            }
        }


class WebSocketDocumentMessage(BaseModel):
    """
    WebSocket message wrapper for document processing events
    
    Used for real-time communication of document processing status,
    batch updates, and index changes.
    
    Attributes:
        message_type: Type of WebSocket message
        document_id: Optional document identifier
        batch_id: Optional batch identifier
        event_data: Document processing event details
        performance_metrics: Performance tracking metrics
    
    Example:
        >>> message = WebSocketDocumentMessage(
        ...     message_type="processing_update",
        ...     document_id="doc_123",
        ...     event_data=processing_event,
        ...     performance_metrics={"throughput_docs_per_sec": 4000.0}
        ... )
    """
    message_type: Literal['processing_update', 'batch_status', 'index_update'] = Field(
        ...,
        description="Type of WebSocket message"
    )
    document_id: Optional[str] = Field(
        None,
        description="Document identifier",
        max_length=255
    )
    batch_id: Optional[str] = Field(
        None,
        description="Batch identifier",
        max_length=255
    )
    event_data: DocumentProcessingEvent = Field(
        ...,
        description="Document processing event details"
    )
    performance_metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="Performance tracking metrics",
        examples=[{
            "throughput_docs_per_sec": 4000.0,
            "avg_processing_time_ms": 250.0,
            "total_documents_processed": 10000,
            "cache_hit_rate": 0.85
        }]
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "message_type": "processing_update",
                "document_id": "doc_550e8400-e29b-41d4-a716-446655440000",
                "batch_id": "batch_20251011_001",
                "event_data": {
                    "event_type": "embedding",
                    "document_id": "doc_550e8400-e29b-41d4-a716-446655440000",
                    "timestamp": "2025-10-11T14:30:00Z",
                    "status": "completed",
                    "progress_percentage": 100.0,
                    "processing_time_ms": 1500.0,
                    "metadata": {
                        "batch_id": "batch_20251011_001",
                        "embedding_dimension": 384
                    }
                },
                "performance_metrics": {
                    "throughput_docs_per_sec": 4250.0,
                    "avg_processing_time_ms": 235.0,
                    "documents_in_batch": 1000
                }
            }
        }

