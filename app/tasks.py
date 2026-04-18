"""
Celery background tasks for APFA

Handles:
- Document processing (text extraction, embedding generation)
- Data pipeline connector syncs (Google Drive, Finnhub, YouTube)
- FAISS index building and hot-swapping
- TTL-based chunk expiration
- Maintenance tasks
"""

import logging
from typing import List, Optional

from celery import Celery, Task
from celery.schedules import crontab
from celery.signals import worker_init

from app.config import settings

logger = logging.getLogger(__name__)

# Initialize Celery — broker/backend URLs come from settings so they honor
# CELERY_BROKER_URL / CELERY_RESULT_BACKEND env vars and fall back to Docker
# hostname "redis" by default (not localhost).
celery_app = Celery(
    "apfa",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    worker_prefetch_multiplier=1,
)

# ---------------------------------------------------------------------------
# Worker initialization — load embedder once per worker process
# ---------------------------------------------------------------------------

_worker_embedder = None


@worker_init.connect
def init_worker_embedder(**kwargs):
    """Load the ONNX embedding model once when the worker starts.

    bge-small-en-v1.5 is ~130MB in memory. Loading per-task would be
    wasteful on a 4 vCPU / 8GB RAM droplet.
    """
    global _worker_embedder
    from fastembed import TextEmbedding

    _worker_embedder = TextEmbedding(model_name=settings.embedder_model)
    logger.info(f"Worker embedder loaded: {settings.embedder_model}")


def _get_embedder():
    """Get the worker-level embedder, loading lazily if needed."""
    global _worker_embedder
    if _worker_embedder is None:
        from fastembed import TextEmbedding

        _worker_embedder = TextEmbedding(model_name=settings.embedder_model)
    return _worker_embedder


def _get_redis():
    """Get a sync Redis client for FAISS rebuild signaling."""
    import redis

    return redis.from_url(settings.redis_url)


# ---------------------------------------------------------------------------
# Document processing (upgraded from stub)
# ---------------------------------------------------------------------------


@celery_app.task(name="process_document", bind=True)
def process_document(self: Task, document_id: str, file_path: str, metadata: dict):
    """
    Process uploaded document: extract text, chunk, embed, store in DeltaTable.

    Args:
        document_id: Unique document identifier
        file_path: Path to uploaded file (S3 or local)
        metadata: Document metadata (filename, content_type, etc.)
    """
    logger.info(f"Processing document {document_id} from {file_path}")

    try:
        self.update_state(
            state="PROGRESS",
            meta={"current": 10, "total": 100, "status": "Extracting text..."},
        )

        # Step 1: Extract text based on content type
        content_type = metadata.get("content_type", "text/plain")
        extracted_text = _extract_text_from_file(file_path, content_type)

        if not extracted_text:
            return {
                "status": "failed",
                "document_id": document_id,
                "error": "Could not extract text from document",
            }

        self.update_state(
            state="PROGRESS",
            meta={"current": 30, "total": 100, "status": "Chunking..."},
        )

        # Step 2: Chunk the text
        from app.services.chunking import chunk_prose

        chunks = chunk_prose(extracted_text)

        self.update_state(
            state="PROGRESS",
            meta={"current": 50, "total": 100, "status": "Embedding and storing..."},
        )

        # Step 3: Build normalized records and ingest
        from datetime import datetime, timezone

        now_iso = datetime.now(timezone.utc).isoformat()
        chunk_dicts = []
        for chunk in chunks:
            chunk_dicts.append(
                {
                    "external_id": f"upload:{document_id}:chunk:{chunk.chunk_index:04d}",
                    "source_type": "manual",
                    "source_url": "",
                    "title": metadata.get("filename", ""),
                    "author": metadata.get("uploaded_by", ""),
                    "published_at": now_iso,
                    "fetched_at": now_iso,
                    "freshness_class": "static",
                    "content_kind": "doc_section",
                    "text": chunk.text,
                    "chunk_index": chunk.chunk_index,
                    "total_chunks": len(chunks),
                    "parent_document_id": document_id,
                    "metadata_json": "{}",
                }
            )

        from app.services.delta_writer import ingest_chunks

        embedder = _get_embedder()
        redis_client = _get_redis()
        stats = ingest_chunks(chunk_dicts, embedder, settings, redis_client)

        self.update_state(
            state="PROGRESS",
            meta={"current": 100, "total": 100, "status": "Complete"},
        )

        logger.info(f"Document {document_id} processed: {stats}")

        return {
            "status": "completed",
            "document_id": document_id,
            "chunks_created": len(chunks),
            "inserted": stats["inserted"],
            "skipped": stats["skipped"],
        }

    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")
        raise


def _extract_text_from_file(file_path: str, content_type: str) -> str:
    """Extract text from a file based on content type."""
    try:
        if content_type == "application/pdf":
            from pypdf import PdfReader

            reader = PdfReader(file_path)
            return "\n\n".join(
                page.extract_text() or "" for page in reader.pages
            )

        elif content_type in (
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ):
            from docx import Document

            doc = Document(file_path)
            return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())

        elif content_type.startswith("text/"):
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

        else:
            logger.warning(f"Unsupported content type: {content_type}")
            return ""

    except Exception as e:
        logger.error(f"Text extraction failed for {file_path}: {e}")
        return ""


# ---------------------------------------------------------------------------
# Google Drive connector task
# ---------------------------------------------------------------------------


@celery_app.task(name="sync_google_drive")
def sync_google_drive_task(
    folder_ids: List[str] = None,
    file_ids: List[str] = None,
):
    """Sync documents from Google Drive into the RAG pipeline."""
    if not settings.google_drive_credentials_path:
        return {"status": "error", "detail": "Google Drive credentials not configured"}

    from app.connectors.google_drive import GoogleDriveConnector

    connector = GoogleDriveConnector(settings.google_drive_credentials_path)
    embedder = _get_embedder()
    redis_client = _get_redis()

    return connector.sync(
        embedder=embedder,
        settings=settings,
        redis_client=redis_client,
        folder_ids=folder_ids or settings.google_drive_folder_ids,
        file_ids=file_ids,
    )


# ---------------------------------------------------------------------------
# Finnhub connector task
# ---------------------------------------------------------------------------


@celery_app.task(name="fetch_finnhub_data")
def fetch_finnhub_data_task(
    tickers: List[str] = None,
    data_types: List[str] = None,
):
    """Fetch market data from Finnhub and store in structured table."""
    if not settings.finnhub_api_key:
        return {"status": "error", "detail": "Finnhub API key not configured"}

    from app.connectors.finnhub_connector import FinnhubConnector
    from app.database import SessionLocal

    connector = FinnhubConnector(settings.finnhub_api_key)
    db = SessionLocal()
    embedder = _get_embedder()
    redis_client = _get_redis()

    try:
        return connector.sync(
            db_session=db,
            embedder=embedder,
            settings=settings,
            redis_client=redis_client,
            tickers=tickers or settings.finnhub_default_tickers,
            data_types=data_types or ["quote", "economic_indicator"],
        )
    finally:
        db.close()


# ---------------------------------------------------------------------------
# YouTube connector task
# ---------------------------------------------------------------------------


@celery_app.task(name="ingest_youtube")
def ingest_youtube_task(
    video_ids: List[str] = None,
    takeout_json: str = None,
    filter_finance: bool = True,
):
    """Ingest YouTube video transcripts into the RAG pipeline."""
    from app.connectors.youtube import YouTubeTranscriptConnector

    connector = YouTubeTranscriptConnector(
        openai_api_key=settings.openai_api_key,
        openai_model=settings.openai_model,
    )
    embedder = _get_embedder()
    redis_client = _get_redis()

    return connector.sync(
        embedder=embedder,
        settings=settings,
        redis_client=redis_client,
        video_ids=video_ids,
        takeout_json=takeout_json,
        filter_finance=filter_finance,
    )


# ---------------------------------------------------------------------------
# FAISS index management
# ---------------------------------------------------------------------------


@celery_app.task(name="rebuild_faiss_index")
def rebuild_faiss_index_task():
    """Trigger FAISS index rebuild by signaling the FastAPI process.

    The actual rebuild happens in the FastAPI process via load_rag_index().
    This task just sets the Redis flag; the FastAPI lifespan or admin
    endpoint picks it up.
    """
    redis_client = _get_redis()
    redis_client.set("faiss:rebuild_needed", "1")
    logger.info("FAISS rebuild signal set")
    return {"status": "rebuild_signaled"}


@celery_app.task(name="rebuild_faiss_if_needed")
def rebuild_faiss_if_needed():
    """Conditional FAISS rebuild — only if new data was ingested."""
    redis_client = _get_redis()
    needed = redis_client.get("faiss:rebuild_needed")
    if needed and needed.decode("utf-8") == "1":
        redis_client.set("faiss:rebuild_needed", "1")
        logger.info("FAISS rebuild needed — signal confirmed")
        return {"status": "rebuild_needed"}
    return {"status": "no_rebuild_needed"}


# ---------------------------------------------------------------------------
# TTL expiration
# ---------------------------------------------------------------------------


@celery_app.task(name="expire_stale_chunks")
def expire_stale_chunks_task():
    """Remove chunks past their TTL."""
    from app.services.delta_writer import expire_stale_chunks

    redis_client = _get_redis()
    expired = expire_stale_chunks(settings, redis_client)
    return {"expired": expired}


# ---------------------------------------------------------------------------
# Batch processing
# ---------------------------------------------------------------------------


@celery_app.task(name="batch_process_documents")
def batch_process_documents(batch_id: str, document_ids: List[str]):
    """Process batch of documents in parallel using Celery group."""
    from celery import group

    logger.info(f"Processing batch {batch_id} with {len(document_ids)} documents")

    # Create a group of process_document tasks
    job = group(
        process_document.s(doc_id, f"/tmp/{doc_id}", {"filename": doc_id})
        for doc_id in document_ids
    )
    result = job.apply_async()

    return {
        "batch_id": batch_id,
        "total_documents": len(document_ids),
        "group_id": str(result.id),
    }


# ---------------------------------------------------------------------------
# Periodic tasks (Celery Beat)
# ---------------------------------------------------------------------------


@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Configure periodic tasks for the data pipeline."""

    # Cleanup old files daily at 2 AM
    sender.add_periodic_task(
        crontab(hour=2, minute=0),
        cleanup_old_documents.s(),
        name="cleanup-old-documents",
    )

    # Expire TTL chunks daily at 3 AM
    sender.add_periodic_task(
        crontab(hour=3, minute=0),
        expire_stale_chunks_task.s(),
        name="expire-ttl-chunks",
    )

    # Conditional FAISS rebuild every 30 min
    if settings.faiss_auto_rebuild:
        sender.add_periodic_task(
            crontab(minute=f"*/{settings.faiss_rebuild_interval_minutes}"),
            rebuild_faiss_if_needed.s(),
            name="faiss-conditional-rebuild",
        )

    # Finnhub: hourly quotes + economic indicators
    if settings.finnhub_api_key:
        sender.add_periodic_task(
            crontab(minute=0),  # every hour
            fetch_finnhub_data_task.s(
                tickers=settings.finnhub_default_tickers,
                data_types=["quote"],
            ),
            name="finnhub-hourly-quotes",
        )
        sender.add_periodic_task(
            crontab(hour=6, minute=0),  # daily at 6 AM UTC
            fetch_finnhub_data_task.s(
                tickers=settings.finnhub_default_tickers,
                data_types=["economic_indicator", "recommendation", "fundamentals"],
            ),
            name="finnhub-daily-fundamentals",
        )

    # Google Drive: sync every 6 hours
    if settings.google_drive_credentials_path and settings.google_drive_folder_ids:
        sender.add_periodic_task(
            crontab(minute=0, hour="*/6"),
            sync_google_drive_task.s(
                folder_ids=settings.google_drive_folder_ids,
            ),
            name="google-drive-sync",
        )


@celery_app.task(name="cleanup_old_documents")
def cleanup_old_documents():
    """Clean up old documents from storage"""
    logger.info("Running document cleanup task")
    # TODO: Implement cleanup of temp files in /tmp
    return {"cleaned": 0}
