"""
Enhanced document and batch management data models

Supports:
- Document metadata and tracking
- Batch processing operations
- Progress monitoring and metrics
- Version control
- Security scanning results
"""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator


class Document(BaseModel):
    """
    Document data model for knowledge base management
    
    Attributes:
        document_id: Unique document identifier
        filename: Original filename
        content_type: MIME type of document
        file_size_bytes: File size in bytes
        upload_timestamp: UTC timestamp when uploaded
        processing_status: Current processing status
        extracted_text: Optional extracted text content
        embedding_vector: Optional embedding vector (384 dimensions)
        metadata: Additional document metadata
        security_scan_results: Security scanning results
        version: Document version number
    
    Example:
        >>> doc = Document(
        ...     document_id="doc_12345",
        ...     filename="financial_report.pdf",
        ...     content_type="application/pdf",
        ...     file_size_bytes=1024000,
        ...     processing_status="completed",
        ...     version=1
        ... )
    """
    document_id: str = Field(
        ...,
        description="Unique document identifier",
        min_length=1,
        max_length=255
    )
    filename: str = Field(
        ...,
        description="Original filename",
        min_length=1,
        max_length=255
    )
    content_type: str = Field(
        ...,
        description="MIME type of document",
        max_length=100
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
    processing_status: str = Field(
        ...,
        description="Current processing status",
        max_length=50
    )
    extracted_text: Optional[str] = Field(
        None,
        description="Extracted text content"
    )
    embedding_vector: Optional[List[float]] = Field(
        None,
        description="Embedding vector (typically 384 dimensions)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional document metadata",
        examples=[{
            "page_count": 10,
            "author": "John Doe",
            "created_date": "2025-01-01",
            "category": "financial_report"
        }]
    )
    security_scan_results: Dict[str, Any] = Field(
        default_factory=dict,
        description="Security scanning results",
        examples=[{
            "status": "clean",
            "scanned_at": "2025-10-11T14:30:00Z",
            "threats_found": 0,
            "scan_duration_ms": 150
        }]
    )
    version: int = Field(
        ...,
        description="Document version number",
        ge=1
    )
    
    @field_validator('upload_timestamp')
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware"""
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v
    
    @field_validator('embedding_vector')
    @classmethod
    def validate_embedding_dimension(cls, v: Optional[List[float]]) -> Optional[List[float]]:
        """Validate embedding vector dimension"""
        if v is not None:
            expected_dim = 384  # all-MiniLM-L6-v2 dimension
            if len(v) != expected_dim:
                raise ValueError(f"Embedding vector must have {expected_dim} dimensions, got {len(v)}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc_550e8400-e29b-41d4-a716-446655440000",
                "filename": "financial_report_2025_Q1.pdf",
                "content_type": "application/pdf",
                "file_size_bytes": 1024000,
                "upload_timestamp": "2025-10-11T14:30:00Z",
                "processing_status": "completed",
                "extracted_text": "Financial Report Q1 2025...",
                "embedding_vector": None,  # 384-dimensional vector omitted for brevity
                "metadata": {
                    "page_count": 25,
                    "author": "Finance Department",
                    "category": "quarterly_report"
                },
                "security_scan_results": {
                    "status": "clean",
                    "scanned_at": "2025-10-11T14:30:15Z",
                    "threats_found": 0
                },
                "version": 1
            }
        }


class BatchProgress(BaseModel):
    """
    Batch processing progress data model
    
    Attributes:
        documents_processed: Number of documents processed
        total_documents: Total documents in batch
        completion_percentage: Progress percentage (0.0-100.0)
        estimated_remaining_seconds: Estimated time remaining
        processing_rate_docs_per_second: Current processing throughput
        errors_count: Number of errors encountered
    
    Example:
        >>> progress = BatchProgress(
        ...     documents_processed=450,
        ...     total_documents=1000,
        ...     completion_percentage=45.0,
        ...     estimated_remaining_seconds=137,
        ...     processing_rate_docs_per_second=4000.0,
        ...     errors_count=5
        ... )
    """
    documents_processed: int = Field(
        ...,
        description="Number of documents processed",
        ge=0
    )
    total_documents: int = Field(
        ...,
        description="Total documents in batch",
        ge=0
    )
    completion_percentage: float = Field(
        ...,
        description="Progress percentage (0.0-100.0)",
        ge=0.0,
        le=100.0
    )
    estimated_remaining_seconds: int = Field(
        ...,
        description="Estimated time remaining in seconds",
        ge=0
    )
    processing_rate_docs_per_second: float = Field(
        ...,
        description="Current processing throughput",
        ge=0.0
    )
    errors_count: int = Field(
        ...,
        description="Number of errors encountered",
        ge=0
    )
    
    @field_validator('completion_percentage')
    @classmethod
    def validate_completion_percentage(cls, v: float, info) -> float:
        """Validate completion percentage matches processed/total ratio"""
        processed = info.data.get('documents_processed', 0)
        total = info.data.get('total_documents', 1)
        
        if total > 0:
            expected = (processed / total) * 100
            # Allow small floating-point discrepancies
            if abs(v - expected) > 0.1:
                raise ValueError(
                    f"Completion percentage {v}% doesn't match processed/total ratio ({expected:.1f}%)"
                )
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "documents_processed": 7500,
                "total_documents": 10000,
                "completion_percentage": 75.0,
                "estimated_remaining_seconds": 625,
                "processing_rate_docs_per_second": 4000.0,
                "errors_count": 12
            }
        }


class DocumentBatch(BaseModel):
    """
    Document batch data model for batch processing operations
    
    Attributes:
        batch_id: Unique batch identifier
        document_ids: List of document IDs in batch
        batch_size: Number of documents in batch
        created_at: UTC timestamp when batch was created
        status: Current batch status
        progress: Batch processing progress
        performance_metrics: Performance tracking metrics
    
    Example:
        >>> batch = DocumentBatch(
        ...     batch_id="batch_20251011_001",
        ...     document_ids=["doc_1", "doc_2", "doc_3"],
        ...     batch_size=1000,
        ...     status="processing",
        ...     progress=batch_progress
        ... )
    """
    batch_id: str = Field(
        ...,
        description="Unique batch identifier",
        min_length=1,
        max_length=255
    )
    document_ids: List[str] = Field(
        ...,
        description="List of document IDs in batch"
    )
    batch_size: int = Field(
        ...,
        description="Number of documents in batch",
        ge=1
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when batch was created"
    )
    status: Literal['queued', 'processing', 'completed', 'failed'] = Field(
        ...,
        description="Current batch status"
    )
    progress: BatchProgress = Field(
        ...,
        description="Batch processing progress"
    )
    performance_metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="Performance tracking metrics",
        examples=[{
            "avg_processing_time_ms": 250.0,
            "peak_throughput_docs_per_sec": 5000.0,
            "total_processing_time_seconds": 2500.0
        }]
    )
    
    @field_validator('created_at')
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware"""
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v
    
    @field_validator('batch_size')
    @classmethod
    def validate_batch_size_matches_ids(cls, v: int, info) -> int:
        """Ensure batch_size matches document_ids length"""
        document_ids = info.data.get('document_ids', [])
        if len(document_ids) != v:
            raise ValueError(
                f"batch_size ({v}) doesn't match document_ids length ({len(document_ids)})"
            )
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "batch_id": "batch_20251011_001",
                "document_ids": ["doc_1", "doc_2", "doc_3"],
                "batch_size": 3,
                "created_at": "2025-10-11T14:00:00Z",
                "status": "processing",
                "progress": {
                    "documents_processed": 2,
                    "total_documents": 3,
                    "completion_percentage": 66.7,
                    "estimated_remaining_seconds": 15,
                    "processing_rate_docs_per_second": 4000.0,
                    "errors_count": 0
                },
                "performance_metrics": {
                    "avg_processing_time_ms": 250.0,
                    "peak_throughput_docs_per_sec": 4500.0
                }
            }
        }

