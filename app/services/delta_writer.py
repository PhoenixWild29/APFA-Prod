"""DeltaTable writer for the APFA data pipeline.

Handles:
- Appending new document chunks to the RAG DeltaTable
- Content-hash dedup (skip chunks already in table with same hash)
- FAISS rebuild signaling via Redis
- Per-source audit logging
- Deletion by source_url (GDPR/CCPA compliance)
"""

import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def _compute_content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _generate_external_id(
    source_type: str, source_id: str, chunk_index: int
) -> str:
    """Generate a deterministic external_id for dedup.

    Format: {source_type}:{source_id}:chunk:{chunk_index:04d}
    Example: youtube:dQw4w9WgXcQ:chunk:0007
    """
    return f"{source_type}:{source_id}:chunk:{chunk_index:04d}"


def ingest_chunks(
    chunks: list[dict],
    embedder,
    settings,
    redis_client=None,
) -> dict:
    """Ingest a batch of normalized document chunks into the RAG DeltaTable.

    Each chunk dict must conform to the normalized record schema:
        - external_id: str (unique across sources)
        - source_type: str (youtube|google_drive|finnhub|manual)
        - source_url: str
        - title: str
        - author: str
        - published_at: str (ISO 8601)
        - fetched_at: str (ISO 8601)
        - freshness_class: str (realtime|hourly|daily|weekly|static)
        - content_kind: str (transcript_segment|doc_section|etc.)
        - text: str (the actual chunk content)
        - chunk_index: int
        - total_chunks: int
        - metadata_json: str (JSON blob, connector-specific)
        - parent_document_id: str (groups chunks from same doc)

    Args:
        chunks: List of normalized record dicts.
        embedder: FastEmbed TextEmbedding instance.
        settings: App Settings instance.
        redis_client: Optional Redis client for FAISS rebuild signaling.

    Returns:
        Dict with ingestion stats: inserted, skipped (dedup), errors.
    """
    from app.storage import get_delta_storage_options

    if not chunks:
        return {"inserted": 0, "skipped": 0, "errors": 0}

    storage_opts = get_delta_storage_options()
    stats = {"inserted": 0, "skipped": 0, "errors": 0}

    # Load existing content hashes for dedup
    existing_hashes: set[str] = set()
    existing_external_ids: set[str] = set()
    try:
        from deltalake import DeltaTable

        dt = DeltaTable(settings.delta_table_path, storage_options=storage_opts)
        existing_df = dt.to_pandas()
        if "content_hash" in existing_df.columns:
            existing_hashes = set(
                existing_df["content_hash"].dropna().tolist()
            )
        if "external_id" in existing_df.columns:
            existing_external_ids = set(
                existing_df["external_id"].dropna().tolist()
            )
    except Exception:
        # Table doesn't exist yet or is empty — no dedup needed
        pass

    # Filter out duplicates
    new_chunks = []
    for chunk in chunks:
        content_hash = _compute_content_hash(chunk["text"])
        ext_id = chunk.get("external_id", "")

        if content_hash in existing_hashes:
            stats["skipped"] += 1
            logger.debug(f"Skipping duplicate chunk (hash): {ext_id}")
            continue
        if ext_id and ext_id in existing_external_ids:
            stats["skipped"] += 1
            logger.debug(f"Skipping duplicate chunk (external_id): {ext_id}")
            continue

        chunk["_content_hash"] = content_hash
        new_chunks.append(chunk)

    if not new_chunks:
        logger.info(
            f"All {len(chunks)} chunks already exist — nothing to ingest"
        )
        return stats

    # Embed the new chunks
    texts = [c["text"] for c in new_chunks]
    try:
        embeddings = np.array(list(embedder.embed(texts)))
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        stats["errors"] = len(new_chunks)
        return stats

    # Build DataFrame rows matching DeltaTable schema
    now_iso = datetime.now(timezone.utc).isoformat()
    rows = []
    for i, chunk in enumerate(new_chunks):
        doc_id = chunk.get("parent_document_id") or str(uuid.uuid4())
        chunk_id = chunk.get("external_id") or str(uuid.uuid4())

        rows.append(
            {
                # Core RAG columns (backward-compatible with seed data)
                "document_id": doc_id,
                "chunk_id": chunk_id,
                "filename": chunk.get("title", ""),
                "document_type": chunk.get("content_kind", "doc_section"),
                "source": chunk.get("author", chunk.get("source_type", "")),
                "creation_date": chunk.get("published_at", now_iso)[:10],
                "file_size_bytes": len(chunk["text"].encode("utf-8")),
                "profile": chunk["text"],
                # Embedding cache columns
                "embedding_vector": embeddings[i].tolist(),
                "embedding_model": settings.embedder_model,
                "content_hash": chunk["_content_hash"],
                "embedded_at": now_iso,
                # Pipeline extension columns
                "external_id": chunk.get("external_id", ""),
                "source_connector": chunk.get("source_type", "manual"),
                "source_url": chunk.get("source_url", ""),
                "parent_document_id": doc_id,
                "chunk_index": chunk.get("chunk_index", 0),
                "total_chunks": chunk.get("total_chunks", 1),
                "ingested_at": now_iso,
                "ttl_hours": chunk.get("ttl_hours"),
                "freshness_class": chunk.get("freshness_class", "static"),
                "content_kind": chunk.get("content_kind", "doc_section"),
                "metadata_json": chunk.get("metadata_json", "{}"),
            }
        )

    df = pd.DataFrame(rows)

    # Append to DeltaTable (schema_mode="merge" adds new columns gracefully)
    try:
        import deltalake

        deltalake.write_deltalake(
            settings.delta_table_path,
            df,
            mode="append",
            schema_mode="merge",
            storage_options=storage_opts,
        )
        stats["inserted"] = len(rows)
        logger.info(
            f"Ingested {len(rows)} chunks into DeltaTable "
            f"(source: {rows[0]['source_connector']})"
        )
    except Exception as e:
        logger.error(f"DeltaTable write failed: {e}")
        stats["errors"] = len(rows)
        return stats

    # Signal FAISS rebuild needed
    _signal_faiss_rebuild(redis_client)

    # Audit log
    for row in rows:
        logger.info(
            f"AUDIT ingest: source={row['source_connector']} "
            f"url={row['source_url'][:80]} "
            f"hash={row['content_hash'][:12]} "
            f"chunk_id={row['chunk_id'][:40]}"
        )

    return stats


def delete_by_source_url(
    source_url: str,
    settings,
    redis_client=None,
) -> int:
    """Delete all chunks from a specific source URL (GDPR/CCPA compliance).

    Returns the number of rows deleted.
    """
    from app.storage import get_delta_storage_options
    from deltalake import DeltaTable

    storage_opts = get_delta_storage_options()

    try:
        dt = DeltaTable(settings.delta_table_path, storage_options=storage_opts)
        df = dt.to_pandas()

        if "source_url" not in df.columns:
            return 0

        mask = df["source_url"] == source_url
        delete_count = mask.sum()

        if delete_count == 0:
            return 0

        # Keep everything except the matching rows
        keep_df = df[~mask].copy()

        import deltalake as dl

        dl.write_deltalake(
            settings.delta_table_path,
            keep_df,
            mode="overwrite",
            storage_options=storage_opts,
        )

        logger.info(
            f"AUDIT delete: source_url={source_url[:80]} "
            f"rows_deleted={delete_count}"
        )

        _signal_faiss_rebuild(redis_client)
        return delete_count

    except Exception as e:
        logger.error(f"Delete by source_url failed: {e}")
        raise


def expire_stale_chunks(settings, redis_client=None) -> int:
    """Remove chunks past their TTL (ttl_hours from ingested_at).

    Called by Celery Beat on a schedule. Returns count of expired rows.
    """
    from app.storage import get_delta_storage_options
    from deltalake import DeltaTable

    storage_opts = get_delta_storage_options()

    try:
        dt = DeltaTable(settings.delta_table_path, storage_options=storage_opts)
        df = dt.to_pandas()

        if "ttl_hours" not in df.columns or "ingested_at" not in df.columns:
            return 0

        now = datetime.now(timezone.utc)
        has_ttl = df["ttl_hours"].notna()

        if not has_ttl.any():
            return 0

        expired_mask = pd.Series(False, index=df.index)
        for idx in df[has_ttl].index:
            ingested = datetime.fromisoformat(df.at[idx, "ingested_at"])
            ttl = int(df.at[idx, "ttl_hours"])
            if now > ingested + pd.Timedelta(hours=ttl):
                expired_mask.at[idx] = True

        expire_count = expired_mask.sum()
        if expire_count == 0:
            return 0

        keep_df = df[~expired_mask].copy()

        import deltalake as dl

        dl.write_deltalake(
            settings.delta_table_path,
            keep_df,
            mode="overwrite",
            storage_options=storage_opts,
        )

        logger.info(f"Expired {expire_count} stale chunks (TTL exceeded)")
        _signal_faiss_rebuild(redis_client)
        return expire_count

    except Exception as e:
        logger.error(f"TTL expiration failed: {e}")
        return 0


def _signal_faiss_rebuild(redis_client=None) -> None:
    """Set Redis flag to signal FAISS index needs rebuilding."""
    if redis_client is None:
        return
    try:
        redis_client.set("faiss:rebuild_needed", "1")
        logger.debug("FAISS rebuild signal set")
    except Exception as e:
        logger.warning(f"Could not signal FAISS rebuild via Redis: {e}")
