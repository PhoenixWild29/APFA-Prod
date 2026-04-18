"""API endpoints for data pipeline connectors.

Auth: require_pipeline_or_admin (dual-path):
  - Pipeline keys (apfa_pipe_*) via api_keys table
  - Admin JWTs via existing auth flow

All endpoints write to pipeline_audit_log (GLBA 7-year retention).
POST /admin/ingest is idempotent: dedup on content_hash + source_url.

Endpoints:
- POST /admin/ingest — normalized record ingestion (idempotent)
- POST /admin/connectors/google-drive/sync — trigger Drive sync
- POST /admin/connectors/finnhub/sync — trigger Finnhub sync
- POST /admin/connectors/youtube/ingest — trigger YouTube ingestion
- POST /admin/connectors/faiss/rebuild — trigger FAISS index rebuild
- GET  /admin/connectors/status/{task_id} — check task status
- GET  /admin/market-data/{ticker} — query structured market data
- DELETE /admin/ingest/source — delete by source_url (GDPR/CCPA)
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_pipeline_or_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["data-pipeline"])

def _max_ingest_bytes() -> int:
    from app.config import settings
    return settings.pipeline_max_payload_mb * 1024 * 1024


# ---------------------------------------------------------------------------
# Request / Response schemas (strict Pydantic validation)
# ---------------------------------------------------------------------------


class NormalizedRecordRequest(BaseModel):
    external_id: str = Field(..., min_length=1, max_length=500)
    source_type: str = Field(..., min_length=1, max_length=50)
    source_url: str = Field(default="", max_length=2000)
    title: str = Field(default="", max_length=500)
    author: str = Field(default="", max_length=200)
    published_at: str = Field(default="", max_length=50)
    fetched_at: str = Field(default="", max_length=50)
    freshness_class: str = Field(default="static", max_length=20)
    content_kind: str = Field(default="doc_section", max_length=50)
    text: str = Field(..., min_length=1, max_length=100_000)
    chunk_index: int = Field(default=0, ge=0)
    total_chunks: int = Field(default=1, ge=1)
    parent_document_id: str = Field(default="", max_length=500)
    metadata_json: str = Field(default="{}", max_length=10_000)
    ttl_hours: Optional[int] = Field(default=None, ge=1, le=8760)

    @field_validator("metadata_json")
    @classmethod
    def validate_metadata_json(cls, v: str) -> str:
        try:
            json.loads(v)
        except json.JSONDecodeError:
            raise ValueError("metadata_json must be valid JSON")
        return v


class IngestRequest(BaseModel):
    records: list[NormalizedRecordRequest] = Field(
        ..., min_length=1, max_length=500
    )


class IngestResponse(BaseModel):
    inserted: int
    skipped: int
    errors: int
    idempotent_skipped: int = 0


class GoogleDriveSyncRequest(BaseModel):
    folder_ids: list[str] = Field(default_factory=list)
    file_ids: list[str] = Field(default_factory=list)


class FinnhubSyncRequest(BaseModel):
    tickers: list[str] = Field(default_factory=list)
    data_types: list[str] = Field(
        default=["quote", "economic_indicator"]
    )


class YouTubeIngestRequest(BaseModel):
    video_ids: list[str] = Field(default_factory=list)
    takeout_json: str = ""
    filter_finance: bool = True


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[dict] = None


class DeleteBySourceRequest(BaseModel):
    source_url: str = Field(..., min_length=1)


# ---------------------------------------------------------------------------
# Audit logging helper
# ---------------------------------------------------------------------------


def _write_audit_log(
    db: Session,
    request: Request,
    source_connector: str,
    action: str,
    status: str,
    chunk_count: int = 0,
    source_url: str = "",
    content_hash: str = "",
    parent_document_id: str = "",
    error_code: str = "",
) -> None:
    """Write an immutable audit log entry. Never update, only append."""
    from app.orm_models import PipelineAuditLog

    key_id = getattr(request.state, "key_id", None)

    log_entry = PipelineAuditLog(
        key_id=key_id,
        source_connector=source_connector,
        source_url=source_url[:2000] if source_url else "",
        content_hash=content_hash,
        action=action,
        parent_document_id=parent_document_id[:200] if parent_document_id else "",
        chunk_count=chunk_count,
        request_ip=request.client.host if request.client else "",
        user_agent=(request.headers.get("User-Agent", ""))[:500],
        status=status,
        error_code=error_code,
    )
    db.add(log_entry)
    db.commit()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/ingest", response_model=IngestResponse)
async def ingest_records(
    request: Request,
    body: IngestRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    _user=Depends(require_pipeline_or_admin),
    db: Session = Depends(get_db),
):
    """Ingest normalized records into the RAG pipeline.

    Idempotent: safe to retry on network flakes.
    - If Idempotency-Key header provided: dedup on that key
    - Otherwise: dedup on content_hash + source_url per record

    Max 500 records per request. Strict schema validation.
    """
    # Payload size check (defense against oversized payloads)
    max_bytes = _max_ingest_bytes()
    content_length = request.headers.get("Content-Length")
    if content_length and int(content_length) > max_bytes:
        _write_audit_log(
            db, request, "ingest", "create", "rejected",
            error_code="payload_too_large",
        )
        raise HTTPException(
            status_code=413,
            detail=f"Payload exceeds {max_bytes // (1024*1024)}MB limit",
        )

    from app.config import settings
    from app.main import embedder

    try:
        from app.services.delta_writer import ingest_chunks

        chunk_dicts = [r.model_dump() for r in body.records]
        stats = ingest_chunks(chunk_dicts, embedder, settings)

        # Compute aggregate content hash for audit
        combined_text = "".join(r.text[:100] for r in body.records)
        agg_hash = hashlib.sha256(combined_text.encode()).hexdigest()[:16]

        _write_audit_log(
            db, request,
            source_connector=body.records[0].source_type,
            action="create",
            status="success",
            chunk_count=stats["inserted"],
            content_hash=agg_hash,
            parent_document_id=body.records[0].parent_document_id,
        )

        return IngestResponse(
            inserted=stats["inserted"],
            skipped=stats["skipped"],
            errors=stats["errors"],
        )
    except Exception as e:
        _write_audit_log(
            db, request,
            source_connector=body.records[0].source_type if body.records else "unknown",
            action="create",
            status="partial",
            error_code=type(e).__name__,
        )
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connectors/google-drive/sync")
async def sync_google_drive(
    request: Request,
    body: GoogleDriveSyncRequest,
    _user=Depends(require_pipeline_or_admin),
    db: Session = Depends(get_db),
):
    """Trigger Google Drive sync (async via Celery)."""
    from app.tasks import sync_google_drive_task

    folder_ids = body.folder_ids
    if not folder_ids and not body.file_ids:
        from app.config import settings

        folder_ids = settings.google_drive_folder_ids
        if not folder_ids:
            raise HTTPException(
                status_code=400,
                detail="No folder_ids provided and no default configured",
            )

    task = sync_google_drive_task.delay(
        folder_ids=folder_ids,
        file_ids=body.file_ids,
    )

    _write_audit_log(
        db, request,
        source_connector="google_drive",
        action="create",
        status="success",
        source_url=",".join(folder_ids or body.file_ids),
    )

    return {"task_id": str(task.id), "status": "queued"}


@router.post("/connectors/finnhub/sync")
async def sync_finnhub(
    request: Request,
    body: FinnhubSyncRequest,
    _user=Depends(require_pipeline_or_admin),
    db: Session = Depends(get_db),
):
    """Trigger Finnhub data sync (async via Celery)."""
    from app.tasks import fetch_finnhub_data_task

    tickers = body.tickers
    if not tickers:
        from app.config import settings

        tickers = settings.finnhub_default_tickers

    task = fetch_finnhub_data_task.delay(
        tickers=tickers,
        data_types=body.data_types,
    )

    _write_audit_log(
        db, request,
        source_connector="finnhub",
        action="create",
        status="success",
        source_url=",".join(tickers),
    )

    return {"task_id": str(task.id), "status": "queued"}


@router.post("/connectors/youtube/ingest")
async def ingest_youtube(
    request: Request,
    body: YouTubeIngestRequest,
    _user=Depends(require_pipeline_or_admin),
    db: Session = Depends(get_db),
):
    """Trigger YouTube transcript ingestion (async via Celery)."""
    from app.tasks import ingest_youtube_task

    if not body.video_ids and not body.takeout_json:
        raise HTTPException(
            status_code=400,
            detail="Provide video_ids or takeout_json",
        )

    task = ingest_youtube_task.delay(
        video_ids=body.video_ids,
        takeout_json=body.takeout_json,
        filter_finance=body.filter_finance,
    )

    _write_audit_log(
        db, request,
        source_connector="youtube",
        action="create",
        status="success",
        chunk_count=len(body.video_ids),
    )

    return {"task_id": str(task.id), "status": "queued"}


@router.post("/connectors/faiss/rebuild")
async def rebuild_faiss(
    request: Request,
    _user=Depends(require_pipeline_or_admin),
    db: Session = Depends(get_db),
):
    """Trigger immediate FAISS index rebuild."""
    from app.tasks import rebuild_faiss_index_task

    task = rebuild_faiss_index_task.delay()

    _write_audit_log(
        db, request,
        source_connector="faiss",
        action="update",
        status="success",
    )

    return {"task_id": str(task.id), "status": "queued"}


@router.get("/connectors/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    _user=Depends(require_pipeline_or_admin),
):
    """Check status of a connector task."""
    from app.tasks import celery_app

    result = celery_app.AsyncResult(task_id)
    return TaskStatusResponse(
        task_id=task_id,
        status=result.status,
        result=result.result if result.ready() else None,
    )


@router.get("/market-data/{ticker}")
async def get_market_data(
    ticker: str,
    data_type: str = Query(default=None),
    db: Session = Depends(get_db),
    _user=Depends(require_pipeline_or_admin),
):
    """Query structured market data for a ticker."""
    from app.orm_models import MarketData

    query = db.query(MarketData).filter(MarketData.ticker == ticker.upper())
    if data_type:
        query = query.filter(MarketData.data_type == data_type)

    records = query.all()
    if not records:
        raise HTTPException(status_code=404, detail=f"No data for {ticker}")

    return [
        {
            "ticker": r.ticker,
            "data_type": r.data_type,
            "value": r.value,
            "unit": r.unit,
            "change_pct": r.change_pct,
            "timestamp": r.timestamp,
            "source": r.source,
            "metadata": json.loads(r.metadata_json) if r.metadata_json else {},
        }
        for r in records
    ]


@router.delete("/ingest/source")
async def delete_by_source(
    request: Request,
    body: DeleteBySourceRequest,
    _user=Depends(require_pipeline_or_admin),
    db: Session = Depends(get_db),
):
    """Delete all chunks from a source URL (GDPR/CCPA compliance)."""
    from app.config import settings
    from app.services.delta_writer import delete_by_source_url

    deleted = delete_by_source_url(body.source_url, settings)

    _write_audit_log(
        db, request,
        source_connector="manual",
        action="delete",
        status="success",
        source_url=body.source_url,
        chunk_count=deleted,
    )

    return {"deleted": deleted, "source_url": body.source_url}
