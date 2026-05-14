"""DeltaTable writer for the APFA data pipeline.

Handles:
- Appending new document chunks to the RAG DeltaTable via merge (idempotent)
- Explicit DELTA_SCHEMA enforcement (PyArrow typed writes)
- Content-hash dedup (skip chunks already in table with same hash)
- FAISS rebuild signaling via Redis
- Per-source audit logging
- Deletion by source_url (GDPR/CCPA compliance)
- TTL-based chunk expiration

All writes use DeltaTable.merge() keyed on chunk_id — retries never
create duplicates, updated content replaces old chunks.
"""

import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import pandas as pd
import pyarrow as pa

logger = logging.getLogger(__name__)


def _compute_content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _conform_df_to_schema(df: pd.DataFrame, schema: pa.Schema) -> pd.DataFrame:
    """Ensure DataFrame has exactly the columns in DELTA_SCHEMA, in order.

    - Adds missing columns with None
    - Removes extra columns (with a warning)
    - Reorders to match schema
    - Converts embedding_vector values to float32 lists
    """
    expected = [field.name for field in schema]

    # Warn on extra columns
    extra = set(df.columns) - set(expected)
    if extra:
        logger.warning(
            f"DataFrame has columns not in DELTA_SCHEMA (dropping): {extra}"
        )

    # Add missing columns
    for col in expected:
        if col not in df.columns:
            df[col] = None

    # Ensure embeddings are float32 before Arrow conversion
    if "embedding_vector" in df.columns:
        df["embedding_vector"] = df["embedding_vector"].apply(
            lambda v: np.asarray(v, dtype=np.float32).tolist()
            if v is not None
            else None
        )

    # Ensure int columns have proper types (Arrow rejects float for int fields)
    for col in ["file_size_bytes", "chunk_index", "total_chunks", "ttl_hours"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            # ttl_hours can be null
            if col != "ttl_hours":
                df[col] = df[col].fillna(0).astype("int64")

    return df[expected]


def _df_to_arrow(df: pd.DataFrame, schema: pa.Schema) -> pa.Table:
    """Convert DataFrame to Arrow Table with explicit schema.

    Raises clear error if types don't match.
    """
    conformed = _conform_df_to_schema(df.copy(), schema)
    try:
        return pa.Table.from_pandas(
            conformed, schema=schema, preserve_index=False
        )
    except (pa.ArrowInvalid, pa.ArrowTypeError) as e:
        # Identify which column caused the error
        for field in schema:
            col = field.name
            try:
                pa.array(conformed[col].tolist(), type=field.type)
            except Exception as col_err:
                logger.error(
                    f"Schema mismatch on column '{col}': "
                    f"expected {field.type}, got error: {col_err}"
                )
        raise ValueError(f"Arrow schema conversion failed: {e}") from e


def ingest_chunks(
    chunks: list[dict],
    embedder,
    settings,
    redis_client=None,
) -> dict:
    """Ingest a batch of normalized document chunks into the RAG DeltaTable.

    Uses DeltaTable.merge() keyed on chunk_id — idempotent, retries don't
    create duplicates, updated content replaces old chunks.

    Dedup: skips chunks whose content_hash already exists in the table.

    Args:
        chunks: List of normalized record dicts (must have "text" key).
        embedder: FastEmbed TextEmbedding instance.
        settings: App Settings instance.
        redis_client: Optional Redis client for FAISS rebuild signaling.

    Returns:
        Dict with ingestion stats: inserted, skipped, errors.
    """
    from app.connectors.base import get_delta_schema
    from app.storage import get_delta_storage_options

    if not chunks:
        return {"inserted": 0, "skipped": 0, "errors": 0}

    storage_opts = get_delta_storage_options()
    schema = get_delta_schema()
    stats = {"inserted": 0, "skipped": 0, "errors": 0}

    # Load existing content hashes for dedup — column-pruned read.
    # Only read content_hash and external_id columns, not the full table
    # (which includes embedding vectors, text, metadata — 100MB+ at scale).
    # Uses PyArrow directly for true column projection (not late-projection).
    existing_hashes: set[str] = set()
    existing_external_ids: set[str] = set()
    table_exists = False
    try:
        from deltalake import DeltaTable

        dt = DeltaTable(settings.delta_table_path, storage_options=storage_opts)
        table_exists = True
        # Column-pruned read via PyArrow — only touches the Parquet columns needed
        dedup_cols = []
        dt_col_names = [f.name for f in dt.schema().fields]
        if "content_hash" in dt_col_names:
            dedup_cols.append("content_hash")
        if "external_id" in dt_col_names:
            dedup_cols.append("external_id")
        if dedup_cols:
            dedup_table = dt.to_pyarrow_table(columns=dedup_cols)
            if "content_hash" in dedup_cols:
                existing_hashes = set(
                    v for v in dedup_table["content_hash"].to_pylist() if v is not None
                )
            if "external_id" in dedup_cols:
                existing_external_ids = set(
                    v for v in dedup_table["external_id"].to_pylist() if v is not None
                )
    except Exception:
        pass

    # Filter out duplicates
    new_chunks = []
    for chunk in chunks:
        content_hash = _compute_content_hash(chunk["text"])
        ext_id = chunk.get("external_id", "")

        if content_hash in existing_hashes:
            stats["skipped"] += 1
            continue
        if ext_id and ext_id in existing_external_ids:
            stats["skipped"] += 1
            continue

        chunk["_content_hash"] = content_hash
        new_chunks.append(chunk)

    if not new_chunks:
        logger.info(
            f"All {len(chunks)} chunks already exist — nothing to ingest"
        )
        return stats

    # Embed the new chunks in batches to cap ONNX peak memory.
    # Without batching, ONNX allocates one large activation tensor for all
    # chunks — 1500 chunks can spike to 400MB+ of working memory.
    EMBED_BATCH_SIZE = 64
    texts = [c["text"] for c in new_chunks]
    try:
        all_embeddings = []
        for batch_start in range(0, len(texts), EMBED_BATCH_SIZE):
            batch = texts[batch_start:batch_start + EMBED_BATCH_SIZE]
            batch_emb = np.array(list(embedder.embed(batch)), dtype=np.float32)
            all_embeddings.append(batch_emb)
        embeddings = np.concatenate(all_embeddings, axis=0) if all_embeddings else np.array([], dtype=np.float32)
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        stats["errors"] = len(new_chunks)
        return stats

    # Build DataFrame rows matching DELTA_SCHEMA
    now_iso = datetime.now(timezone.utc).isoformat()
    rows = []
    for i, chunk in enumerate(new_chunks):
        doc_id = chunk.get("parent_document_id") or str(uuid.uuid4())
        chunk_id = chunk.get("external_id") or str(uuid.uuid4())

        rows.append(
            {
                "document_id": doc_id,
                "chunk_id": chunk_id,
                "filename": chunk.get("title", ""),
                "document_type": chunk.get("content_kind", "doc_section"),
                "source": chunk.get("author", chunk.get("source_type", "")),
                "creation_date": chunk.get("published_at", now_iso)[:10],
                "file_size_bytes": len(chunk["text"].encode("utf-8")),
                "profile": chunk["text"],
                "embedding_vector": embeddings[i].tolist(),
                "embedding_model": settings.embedder_model,
                "content_hash": chunk["_content_hash"],
                "embedded_at": now_iso,
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

    # Convert to Arrow with explicit schema
    try:
        table = _df_to_arrow(df, schema)
    except ValueError as e:
        logger.error(f"Schema conversion failed: {e}")
        stats["errors"] = len(rows)
        return stats

    # Write: merge if table exists, overwrite if first write
    try:
        import deltalake

        if table_exists:
            # Merge keyed on chunk_id — idempotent upsert
            dt = deltalake.DeltaTable(
                settings.delta_table_path, storage_options=storage_opts
            )
            dt.merge(
                source=table,
                predicate="s.chunk_id = t.chunk_id",
                source_alias="s",
                target_alias="t",
            ).when_matched_update_all().when_not_matched_insert_all().execute()
        else:
            # First write — create the table with explicit schema
            deltalake.write_deltalake(
                settings.delta_table_path,
                table,
                mode="overwrite",
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
    from app.connectors.base import get_delta_schema
    from app.storage import get_delta_storage_options
    from deltalake import DeltaTable

    storage_opts = get_delta_storage_options()
    schema = get_delta_schema()

    try:
        dt = DeltaTable(settings.delta_table_path, storage_options=storage_opts)
        df = dt.to_pandas()

        if "source_url" not in df.columns:
            return 0

        mask = df["source_url"] == source_url
        delete_count = mask.sum()

        if delete_count == 0:
            return 0

        keep_df = df[~mask].copy()
        table = _df_to_arrow(keep_df, schema)

        import deltalake as dl

        dl.write_deltalake(
            settings.delta_table_path,
            table,
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
    from app.connectors.base import get_delta_schema
    from app.storage import get_delta_storage_options
    from deltalake import DeltaTable

    storage_opts = get_delta_storage_options()
    schema = get_delta_schema()

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
        table = _df_to_arrow(keep_df, schema)

        import deltalake as dl

        dl.write_deltalake(
            settings.delta_table_path,
            table,
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


def migrate_delta_schema(settings) -> bool:
    """One-time migration: add missing columns to an existing DeltaTable.

    The original seed script created the table with only 8 columns.
    The full schema (from get_delta_schema()) has 21 columns including
    embedding_vector, content_hash, embedding_model, etc. Without
    these columns, embedding cache never persists and every restart
    re-embeds the entire corpus from scratch.

    Safety:
    - Only ADDS columns, never removes or alters existing ones
    - Reads all rows, adds missing columns with null, overwrites
    - Logs pre/post version and row counts for audit trail
    - Idempotent: skips if schema already matches
    - Should run BEFORE load_rag_index() and BEFORE any connector writes

    Returns True if migration ran, False if skipped.
    """
    from app.connectors.base import get_delta_schema
    from app.storage import get_delta_storage_options
    from deltalake import DeltaTable
    import deltalake as dl

    storage_opts = get_delta_storage_options()

    try:
        dt = DeltaTable(settings.delta_table_path, storage_options=storage_opts)
    except Exception:
        logger.info("migration.skip: DeltaTable does not exist yet — will be created by seed")
        return False

    target_schema = get_delta_schema()
    current_col_names = set(c.name for c in dt.schema().fields)
    target_col_names = set(f.name for f in target_schema)

    missing = target_col_names - current_col_names
    extra = current_col_names - target_col_names

    if extra:
        # Safety: never silently drop columns
        logger.error(
            f"migration.abort: DeltaTable has columns not in target schema: {extra}. "
            "Refusing to migrate — manual intervention required."
        )
        return False

    if not missing:
        logger.info("migration.skip: schema_matches=true")
        return False

    # Migration needed
    pre_version = dt.version()
    df = dt.to_pandas()
    row_count = len(df)

    logger.info(
        f"migration.start: pre_version={pre_version} row_count={row_count} "
        f"current_columns={sorted(current_col_names)} "
        f"missing_columns={sorted(missing)}"
    )

    # Add missing columns with null defaults
    for col_name in missing:
        df[col_name] = None

    # Convert to Arrow with the full schema
    arrow_table = _df_to_arrow(df, target_schema)

    logger.info(f"migration.read: rows_read={len(df)}")

    # Overwrite with full schema. schema_mode="overwrite" is required
    # because the target table has fewer columns than the source —
    # without it, Delta refuses to write ("number of fields does not match").
    dl.write_deltalake(
        settings.delta_table_path,
        arrow_table,
        mode="overwrite",
        schema_mode="overwrite",
        storage_options=storage_opts,
    )

    # Verify
    dt_new = DeltaTable(settings.delta_table_path, storage_options=storage_opts)
    post_version = dt_new.version()
    post_row_count = len(dt_new.to_pandas())

    if post_row_count != row_count:
        logger.error(
            f"migration.ERROR: row count changed! pre={row_count} post={post_row_count}. "
            "Data may have been lost. Check Delta time-travel for recovery."
        )
    else:
        logger.info(
            f"migration.complete: post_version={post_version} rows={post_row_count} "
            f"added_columns={sorted(missing)}"
        )

    return True
