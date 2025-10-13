"""
Embedding storage data models for vector management

Provides structured models for:
- Embedding batch storage
- Individual vector representations
- Metadata tracking
- Version control
- MinIO storage integration
"""
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
import numpy as np


class EmbeddingBatch(BaseModel):
    """
    Embedding batch storage model
    
    Coordinates batch processing and index building with proper
    metadata tracking and data integrity verification.
    
    Attributes:
        batch_id: Unique batch identifier
        document_count: Number of documents in batch
        embedding_dimensions: Vector dimensionality (default 384)
        model_version: Embedding model version (default all-MiniLM-L6-v2)
        created_at: Creation timestamp
        minio_path: Path to batch file in MinIO
        checksum: Data integrity checksum (MD5/SHA256)
    
    Example:
        >>> batch = EmbeddingBatch(
        ...     batch_id="batch_12345",
        ...     document_count=1000,
        ...     minio_path="s3://apfa-embeddings/batch_12345.npy",
        ...     checksum="5d41402abc4b2a76b9719d911017c592"
        ... )
    """
    batch_id: str = Field(
        ...,
        description="Unique batch identifier",
        min_length=1,
        max_length=255
    )
    document_count: int = Field(
        ...,
        description="Number of documents in batch",
        ge=1,
        le=1000
    )
    embedding_dimensions: int = Field(
        384,
        description="Vector dimensionality (all-MiniLM-L6-v2)",
        ge=1
    )
    model_version: str = Field(
        "all-MiniLM-L6-v2",
        description="Embedding model version"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )
    minio_path: str = Field(
        ...,
        description="Path to batch file in MinIO",
        min_length=1
    )
    checksum: str = Field(
        ...,
        description="Data integrity checksum (MD5/SHA256)",
        min_length=32,
        max_length=128
    )
    
    @field_validator('created_at')
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware"""
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v
    
    @field_validator('embedding_dimensions')
    @classmethod
    def validate_standard_dimensions(cls, v: int) -> int:
        """Validate embedding dimensions"""
        standard_dims = [128, 256, 384, 512, 768, 1024, 1536]
        if v not in standard_dims:
            raise ValueError(
                f"Embedding dimension {v} is non-standard. "
                f"Expected one of: {standard_dims}"
            )
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "batch_id": "batch_20251011_001",
                "document_count": 1000,
                "embedding_dimensions": 384,
                "model_version": "all-MiniLM-L6-v2",
                "created_at": "2025-10-11T14:30:00Z",
                "minio_path": "s3://apfa-embeddings/batch_20251011_001.npy",
                "checksum": "5d41402abc4b2a76b9719d911017c592"
            }
        }


class VectorEmbedding(BaseModel):
    """
    Individual vector embedding model
    
    Represents a single document's embedding vector with
    normalization tracking and performance metrics.
    
    Attributes:
        document_id: Document identifier
        embedding: 384-dimensional embedding vector
        normalized: Whether vector is normalized (L2 norm = 1.0)
        model_version: Embedding model version
        processing_time_ms: Time taken to generate embedding
    
    Example:
        >>> embedding = VectorEmbedding(
        ...     document_id="doc_12345",
        ...     embedding=[0.123, 0.456, ...],  # 384 dimensions
        ...     normalized=True,
        ...     model_version="all-MiniLM-L6-v2",
        ...     processing_time_ms=2.5
        ... )
    """
    document_id: str = Field(
        ...,
        description="Document identifier",
        min_length=1,
        max_length=255
    )
    embedding: List[float] = Field(
        ...,
        description="384-dimensional embedding vector"
    )
    normalized: bool = Field(
        True,
        description="Whether vector is L2-normalized"
    )
    model_version: str = Field(
        "all-MiniLM-L6-v2",
        description="Embedding model version"
    )
    processing_time_ms: float = Field(
        ...,
        description="Time taken to generate embedding (ms)",
        ge=0.0
    )
    
    @field_validator('embedding')
    @classmethod
    def validate_embedding_dimensions(cls, v: List[float]) -> List[float]:
        """
        Validate embedding has exactly 384 dimensions
        
        Args:
            v: Embedding vector
        
        Returns:
            Validated embedding
        
        Raises:
            ValueError: If dimensions != 384
        """
        expected_dim = 384
        if len(v) != expected_dim:
            raise ValueError(
                f"Embedding must have {expected_dim} dimensions, got {len(v)}"
            )
        return v
    
    @field_validator('embedding')
    @classmethod
    def validate_normalization(cls, v: List[float], info) -> List[float]:
        """
        Validate that normalized embeddings have L2 norm ≈ 1.0
        
        Args:
            v: Embedding vector
            info: Validation context
        
        Returns:
            Validated embedding
        
        Raises:
            ValueError: If normalized=True but L2 norm != 1.0
        """
        normalized = info.data.get('normalized', True)
        
        if normalized:
            # Calculate L2 norm
            arr = np.array(v)
            l2_norm = np.linalg.norm(arr)
            
            # Check if approximately 1.0 (within tolerance)
            tolerance = 0.01
            if abs(l2_norm - 1.0) > tolerance:
                raise ValueError(
                    f"Embedding marked as normalized but L2 norm is {l2_norm:.4f}, "
                    f"expected 1.0 (±{tolerance})"
                )
        
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc_550e8400-e29b-41d4-a716-446655440000",
                "embedding": [0.0123] * 384,  # 384-dimensional vector
                "normalized": True,
                "model_version": "all-MiniLM-L6-v2",
                "processing_time_ms": 2.5
            }
        }

