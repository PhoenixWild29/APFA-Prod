"""
Document batch validation data models

Provides input validation for document batches before
processing through the embedding pipeline.
"""
from typing import List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class ProcessingOptions(BaseModel):
    """
    Configurable processing parameters for document batches
    
    Attributes:
        normalize_vectors: Whether to normalize embedding vectors
        extract_metadata: Whether to extract document metadata
        enable_caching: Whether to enable result caching
        retry_on_failure: Whether to retry failed documents
        custom_options: Additional custom processing options
    
    Example:
        >>> options = ProcessingOptions(
        ...     normalize_vectors=True,
        ...     extract_metadata=True
        ... )
    """
    normalize_vectors: bool = Field(True, description="Normalize embedding vectors")
    extract_metadata: bool = Field(True, description="Extract document metadata")
    enable_caching: bool = Field(True, description="Enable result caching")
    retry_on_failure: bool = Field(True, description="Retry failed documents")
    custom_options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional custom options"
    )


class DocumentBatch(BaseModel):
    """
    Document batch validation model
    
    Ensures proper formatting, size limits, and content validation
    before processing through the embedding pipeline.
    
    Attributes:
        documents: List of document IDs or paths (1-1000)
        batch_size: Number of documents in batch (max 1000)
        priority: Processing priority 1-10 (default 9)
        processing_options: Configurable processing parameters
    
    Example:
        >>> batch = DocumentBatch(
        ...     documents=["doc_1", "doc_2", "doc_3"],
        ...     batch_size=1000,
        ...     priority=9
        ... )
    
    Raises:
        ValueError: If documents list contains empty/whitespace items
        ValueError: If batch_size exceeds 1000
        ValueError: If priority is outside 1-10 range
    """
    documents: List[str] = Field(
        ...,
        description="List of document IDs or paths",
        min_length=1,
        max_length=1000
    )
    batch_size: int = Field(
        1000,
        description="Number of documents in batch",
        ge=1,
        le=1000
    )
    priority: int = Field(
        9,
        description="Processing priority (1=lowest, 10=highest)",
        ge=1,
        le=10
    )
    processing_options: ProcessingOptions = Field(
        default_factory=ProcessingOptions,
        description="Configurable processing parameters"
    )
    
    @field_validator('documents')
    @classmethod
    def validate_documents_not_empty(cls, v: List[str]) -> List[str]:
        """
        Validate that documents list contains no empty or whitespace-only items
        
        Args:
            v: List of document IDs/paths
        
        Returns:
            Validated list
        
        Raises:
            ValueError: If any document is empty or whitespace-only
        """
        for idx, doc in enumerate(v):
            if not doc or not doc.strip():
                raise ValueError(
                    f"Empty documents not allowed (found at index {idx})"
                )
        return v
    
    @field_validator('batch_size')
    @classmethod
    def validate_batch_size_matches_documents(cls, v: int, info) -> int:
        """
        Validate that batch_size matches actual document count
        
        Args:
            v: Batch size value
            info: Validation context
        
        Returns:
            Validated batch size
        
        Raises:
            ValueError: If batch_size doesn't match document count
        """
        documents = info.data.get('documents', [])
        if documents and len(documents) != v:
            raise ValueError(
                f"batch_size ({v}) must match number of documents ({len(documents)})"
            )
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "documents": [
                    "doc_550e8400-e29b-41d4-a716-446655440000",
                    "doc_550e8400-e29b-41d4-a716-446655440001",
                    "doc_550e8400-e29b-41d4-a716-446655440002"
                ],
                "batch_size": 1000,
                "priority": 9,
                "processing_options": {
                    "normalize_vectors": True,
                    "extract_metadata": True,
                    "enable_caching": True,
                    "retry_on_failure": True,
                    "custom_options": {}
                }
            }
        }

