"""
Document processing status service
"""
from typing import Optional
from datetime import datetime, timezone, timedelta
from app.schemas.document_status import DocumentStatus, PerformanceMetrics, ErrorDetails

# In-memory document status storage (in production, use database)
document_statuses = {
    "doc_example_123": {
        "document_id": "doc_example_123",
        "processing_stage": "completed",
        "progress_percentage": 100.0,
        "estimated_completion_time": None,
        "upload_time": "2025-10-11T14:00:00Z",
        "extraction_start": "2025-10-11T14:00:05Z",
        "embedding_start": "2025-10-11T14:00:15Z",
        "indexing_start": "2025-10-11T14:00:25Z",
        "completion_time": "2025-10-11T14:00:30Z",
        "performance_metrics": {
            "processing_duration_seconds": 30.0,
            "file_size_processed_bytes": 1024000,
            "throughput_bytes_per_second": 34133.0,
            "extraction_time_ms": 8500.0,
            "embedding_time_ms": 9200.0,
            "indexing_time_ms": 4800.0
        },
        "error_details": None,
        "filename": "financial_report.pdf",
        "file_size_bytes": 1024000,
        "content_type": "application/pdf"
    }
}


def get_document_status(document_id: str) -> Optional[DocumentStatus]:
    """
    Retrieve document processing status
    
    Args:
        document_id: Document identifier
    
    Returns:
        DocumentStatus or None if not found
    """
    status_data = document_statuses.get(document_id)
    
    if not status_data:
        return None
    
    return DocumentStatus(**status_data)


def update_document_status(
    document_id: str,
    stage: str,
    progress: float,
    **kwargs
):
    """
    Update document processing status
    
    Args:
        document_id: Document identifier
        stage: Processing stage
        progress: Progress percentage
        **kwargs: Additional status fields
    """
    if document_id not in document_statuses:
        document_statuses[document_id] = {
            "document_id": document_id,
            "processing_stage": stage,
            "progress_percentage": progress,
            "upload_time": datetime.now(timezone.utc).isoformat(),
            "filename": kwargs.get("filename", "unknown"),
            "file_size_bytes": kwargs.get("file_size_bytes", 0),
            "content_type": kwargs.get("content_type", "unknown")
        }
    else:
        document_statuses[document_id].update({
            "processing_stage": stage,
            "progress_percentage": progress,
            **kwargs
        })


def create_document_status(
    document_id: str,
    filename: str,
    file_size_bytes: int,
    content_type: str
):
    """
    Create initial document status
    
    Args:
        document_id: Document identifier
        filename: Original filename
        file_size_bytes: File size
        content_type: Content type
    """
    document_statuses[document_id] = {
        "document_id": document_id,
        "processing_stage": "uploaded",
        "progress_percentage": 0.0,
        "estimated_completion_time": (
            datetime.now(timezone.utc) + timedelta(seconds=30)
        ).isoformat(),
        "upload_time": datetime.now(timezone.utc).isoformat(),
        "extraction_start": None,
        "embedding_start": None,
        "indexing_start": None,
        "completion_time": None,
        "performance_metrics": None,
        "error_details": None,
        "filename": filename,
        "file_size_bytes": file_size_bytes,
        "content_type": content_type
    }

