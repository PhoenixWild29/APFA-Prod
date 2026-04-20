"""Base connector classes for the APFA data pipeline.

RAGSource — for text documents that get chunked, embedded, and stored in the
RAG DeltaTable for FAISS retrieval. Examples: Google Drive docs, YouTube
transcript segments.

StructuredDataSource — for numeric/tabular data stored in a separate
structured store (Postgres or separate DeltaTable). NOT embedded into FAISS.
Served to the LLM via agent tools (get_quote, get_rate_trend). May generate
derived textual summaries that ARE ingested into RAG.

Architecture rationale (CoWork): embedding "$187.42, -0.3%, P/E 28.1" is
stale instantly, pollutes retrieval, and wastes context. The LLM should call
a tool for live data, not retrieve embedded numbers.

SECURITY: All connectors are scoped to admin account only (single-curator
model). Never extend connector sync to end users.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import pyarrow as pa

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# DELTA_SCHEMA — canonical PyArrow schema for the RAG DeltaTable
# ---------------------------------------------------------------------------

def build_delta_schema(embedding_dim: int) -> pa.Schema:
    """Build the canonical PyArrow schema for the RAG DeltaTable.

    The embedding_vector column uses fixed_size_list(float32, dim) to
    guarantee type safety — PyArrow will reject wrong-dimension writes.

    Args:
        embedding_dim: Embedding dimension (e.g. 384 for bge-small-en-v1.5).
                        Probed from the embedder at startup, never hardcoded.
    """
    return pa.schema([
        # Core RAG columns (backward-compatible with seed data)
        pa.field("document_id", pa.string()),
        pa.field("chunk_id", pa.string()),
        pa.field("filename", pa.string()),
        pa.field("document_type", pa.string()),
        pa.field("source", pa.string()),
        pa.field("creation_date", pa.string()),
        pa.field("file_size_bytes", pa.int64()),
        pa.field("profile", pa.string()),
        # Embedding cache columns
        pa.field("embedding_vector", pa.list_(pa.float32(), embedding_dim)),
        pa.field("embedding_model", pa.string()),
        pa.field("content_hash", pa.string()),
        pa.field("embedded_at", pa.string()),
        # Pipeline extension columns
        pa.field("external_id", pa.string()),
        pa.field("source_connector", pa.string()),
        pa.field("source_url", pa.string()),
        pa.field("parent_document_id", pa.string()),
        pa.field("chunk_index", pa.int64()),
        pa.field("total_chunks", pa.int64()),
        pa.field("ingested_at", pa.string()),
        pa.field("ttl_hours", pa.int64()),
        pa.field("freshness_class", pa.string()),
        pa.field("content_kind", pa.string()),
        pa.field("metadata_json", pa.string()),
    ])


# Module-level cache — populated lazily on first use
_DELTA_SCHEMA: Optional[pa.Schema] = None
_EMBEDDING_DIM: Optional[int] = None


def get_delta_schema() -> pa.Schema:
    """Get the canonical DELTA_SCHEMA, probing the embedder dimension if needed.

    Lazy initialization avoids circular imports (main.py → base.py → main.py).
    """
    global _DELTA_SCHEMA, _EMBEDDING_DIM
    if _DELTA_SCHEMA is not None:
        return _DELTA_SCHEMA

    # Try to import EMBEDDING_DIM from main.py (set at startup)
    try:
        from app.main import EMBEDDING_DIM
        _EMBEDDING_DIM = EMBEDDING_DIM
    except (ImportError, AttributeError):
        # Fallback: probe the embedder directly
        import numpy as np
        from fastembed import TextEmbedding
        from app.config import settings
        _embedder = TextEmbedding(model_name=settings.embedder_model)
        _probe = np.array(list(_embedder.embed(["probe"])), dtype=np.float32)
        _EMBEDDING_DIM = int(_probe.shape[1])
        del _embedder, _probe

    _DELTA_SCHEMA = build_delta_schema(_EMBEDDING_DIM)
    return _DELTA_SCHEMA


def get_embedding_dim() -> int:
    """Get the embedding dimension, initializing if needed."""
    global _EMBEDDING_DIM
    if _EMBEDDING_DIM is None:
        get_delta_schema()  # triggers probe
    return _EMBEDDING_DIM


@dataclass
class NormalizedRecord:
    """Normalized record schema for all documents entering APFA's pipeline.

    Every connector must produce records in this format before passing
    to delta_writer.ingest_chunks().
    """

    external_id: str  # e.g. "youtube:abc123:chunk:07"
    source_type: str  # youtube|google_drive|finnhub|mboum|manual
    source_url: str
    title: str
    author: str
    published_at: str  # ISO 8601
    fetched_at: str  # ISO 8601
    freshness_class: str  # realtime|hourly|daily|weekly|static
    content_kind: str  # transcript_segment|doc_section|sheet_table|etc.
    text: str  # the actual chunk text
    chunk_index: int = 0
    total_chunks: int = 1
    parent_document_id: str = ""
    metadata_json: str = "{}"
    ttl_hours: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "external_id": self.external_id,
            "source_type": self.source_type,
            "source_url": self.source_url,
            "title": self.title,
            "author": self.author,
            "published_at": self.published_at,
            "fetched_at": self.fetched_at,
            "freshness_class": self.freshness_class,
            "content_kind": self.content_kind,
            "text": self.text,
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "parent_document_id": self.parent_document_id,
            "metadata_json": self.metadata_json,
            "ttl_hours": self.ttl_hours,
        }


class RAGSource(ABC):
    """Base class for connectors that produce text for the RAG pipeline.

    Subclasses implement fetch() to retrieve raw content and transform()
    to produce NormalizedRecord chunks. The sync() method orchestrates
    the full pipeline: fetch → transform → chunk → embed → DeltaTable.
    """

    source_type: str = "manual"

    @abstractmethod
    def fetch(self, **kwargs) -> list[dict]:
        """Fetch raw content from the data source.

        Returns a list of raw document dicts (source-specific format).
        Each dict must at minimum contain 'text' and some identifier.
        """
        ...

    @abstractmethod
    def transform(self, raw_docs: list[dict]) -> list[NormalizedRecord]:
        """Transform raw documents into NormalizedRecord chunks.

        This is where structure-aware chunking happens. The connector
        knows its content structure best (regulatory sections, transcript
        timestamps, spreadsheet rows) and applies the right strategy.
        """
        ...

    def sync(self, embedder, settings, redis_client=None, **kwargs) -> dict:
        """Full sync pipeline: fetch → transform → ingest.

        Returns ingestion stats dict.
        """
        from app.services.delta_writer import ingest_chunks

        logger.info(f"Starting {self.source_type} sync")

        raw_docs = self.fetch(**kwargs)
        logger.info(f"Fetched {len(raw_docs)} raw documents")

        records = self.transform(raw_docs)
        logger.info(f"Transformed into {len(records)} chunks")

        chunk_dicts = [r.to_dict() for r in records]
        stats = ingest_chunks(chunk_dicts, embedder, settings, redis_client)

        logger.info(
            f"{self.source_type} sync complete: "
            f"inserted={stats['inserted']}, "
            f"skipped={stats['skipped']}, "
            f"errors={stats['errors']}"
        )
        return stats


@dataclass
class MarketDataRecord:
    """Record for structured market data (NOT embedded into FAISS).

    Stored in Postgres or a separate DeltaTable. Served to the LLM
    via agent tools.
    """

    ticker: str
    data_type: str  # quote|fundamental|economic_indicator|rate
    value: float
    unit: str = ""
    change_pct: Optional[float] = None
    timestamp: str = ""  # ISO 8601
    source: str = ""
    metadata_json: str = "{}"


class StructuredDataSource(ABC):
    """Base class for structured/numeric data connectors.

    These do NOT produce embeddings or go into FAISS. Data is stored
    in a structured table and served via agent tools (get_quote, etc.).

    Optionally generates derived textual summaries that ARE ingested
    into the RAG pipeline for natural language queries like
    "What's the trend in mortgage rates?"
    """

    source_type: str = "structured"

    @abstractmethod
    def fetch(self, **kwargs) -> list[MarketDataRecord]:
        """Fetch structured data from the source.

        Returns a list of MarketDataRecord objects.
        """
        ...

    @abstractmethod
    def store(self, records: list[MarketDataRecord], db_session) -> int:
        """Store records in the structured data table (Postgres).

        Returns count of records stored.
        """
        ...

    def generate_summaries(
        self, records: list[MarketDataRecord]
    ) -> list[NormalizedRecord]:
        """Generate derived textual summaries for RAG ingestion.

        Default implementation: no summaries. Override to produce
        natural language summaries of market data trends.

        Example output: "As of 2026-04-18, the 30-year fixed mortgage
        rate is 6.875%, down 0.125% from the previous day."
        """
        return []

    def sync(self, db_session, embedder=None, settings=None, redis_client=None, **kwargs) -> dict:
        """Full sync: fetch → store in structured table → optionally generate RAG summaries."""
        from app.services.delta_writer import ingest_chunks

        logger.info(f"Starting {self.source_type} structured sync")

        records = self.fetch(**kwargs)
        stored = self.store(records, db_session)
        logger.info(f"Stored {stored} structured records")

        stats = {"stored": stored, "summaries_ingested": 0}

        # Generate and ingest derived summaries if embedder is available
        if embedder and settings:
            summaries = self.generate_summaries(records)
            if summaries:
                chunk_dicts = [s.to_dict() for s in summaries]
                ingest_stats = ingest_chunks(
                    chunk_dicts, embedder, settings, redis_client
                )
                stats["summaries_ingested"] = ingest_stats["inserted"]
                logger.info(
                    f"Ingested {ingest_stats['inserted']} derived summaries"
                )

        return stats
