"""Admin API endpoints for data pipeline connectors.

All endpoints are admin-only (single-curator model).
Provides:
- POST /admin/ingest — normalized record ingestion
- POST /admin/connectors/google-drive/sync — trigger Drive sync
- POST /admin/connectors/finnhub/sync — trigger Finnhub sync
- POST /admin/connectors/youtube/ingest — trigger YouTube ingestion
- POST /admin/connectors/faiss/rebuild — trigger FAISS index rebuild
- GET  /admin/connectors/status/{task_id} — check task status
- GET  /admin/market-data/{ticker} — query structured market data
- DELETE /admin/ingest/source — delete by source_url (GDPR/CCPA)
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["data-pipeline"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class NormalizedRecordRequest(BaseModel):
    external_id: str
    source_type: str
    source_url: str = ""
    title: str = ""
    author: str = ""
    published_at: str = ""
    fetched_at: str = ""
    freshness_class: str = "static"
    content_kind: str = "doc_section"
    text: str
    chunk_index: int = 0
    total_chunks: int = 1
    parent_document_id: str = ""
    metadata_json: str = "{}"
    ttl_hours: Optional[int] = None


class IngestRequest(BaseModel):
    records: list[NormalizedRecordRequest] = Field(
        ..., min_length=1, max_length=500
    )


class IngestResponse(BaseModel):
    inserted: int
    skipped: int
    errors: int


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
    source_url: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/ingest", response_model=IngestResponse)
async def ingest_records(
    request: IngestRequest,
    _admin=Depends(require_admin),
):
    """Ingest normalized records directly into the RAG pipeline.

    Accepts up to 500 records per request. Each record is deduplicated
    by content_hash and external_id before embedding and storage.
    """
    from app.config import settings
    from app.main import embedder

    try:
        from app.services.delta_writer import ingest_chunks

        chunk_dicts = [r.model_dump() for r in request.records]
        stats = ingest_chunks(chunk_dicts, embedder, settings)
        return IngestResponse(**stats)
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connectors/google-drive/sync")
async def sync_google_drive(
    request: GoogleDriveSyncRequest,
    _admin=Depends(require_admin),
):
    """Trigger Google Drive sync (async via Celery)."""
    from app.tasks import sync_google_drive_task

    folder_ids = request.folder_ids
    if not folder_ids and not request.file_ids:
        from app.config import settings

        folder_ids = settings.google_drive_folder_ids
        if not folder_ids:
            raise HTTPException(
                status_code=400,
                detail="No folder_ids provided and no default configured",
            )

    task = sync_google_drive_task.delay(
        folder_ids=folder_ids,
        file_ids=request.file_ids,
    )
    return {"task_id": str(task.id), "status": "queued"}


@router.post("/connectors/finnhub/sync")
async def sync_finnhub(
    request: FinnhubSyncRequest,
    _admin=Depends(require_admin),
):
    """Trigger Finnhub data sync (async via Celery)."""
    from app.tasks import fetch_finnhub_data_task

    tickers = request.tickers
    if not tickers:
        from app.config import settings

        tickers = settings.finnhub_default_tickers

    task = fetch_finnhub_data_task.delay(
        tickers=tickers,
        data_types=request.data_types,
    )
    return {"task_id": str(task.id), "status": "queued"}


@router.post("/connectors/youtube/ingest")
async def ingest_youtube(
    request: YouTubeIngestRequest,
    _admin=Depends(require_admin),
):
    """Trigger YouTube transcript ingestion (async via Celery)."""
    from app.tasks import ingest_youtube_task

    if not request.video_ids and not request.takeout_json:
        raise HTTPException(
            status_code=400,
            detail="Provide video_ids or takeout_json",
        )

    task = ingest_youtube_task.delay(
        video_ids=request.video_ids,
        takeout_json=request.takeout_json,
        filter_finance=request.filter_finance,
    )
    return {"task_id": str(task.id), "status": "queued"}


@router.post("/connectors/faiss/rebuild")
async def rebuild_faiss(
    _admin=Depends(require_admin),
):
    """Trigger immediate FAISS index rebuild."""
    from app.tasks import rebuild_faiss_index_task

    task = rebuild_faiss_index_task.delay()
    return {"task_id": str(task.id), "status": "queued"}


@router.get("/connectors/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    _admin=Depends(require_admin),
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
    _admin=Depends(require_admin),
):
    """Query structured market data for a ticker.

    This is the admin endpoint. The LLM uses agent tools (get_quote, etc.)
    which call the same underlying data.
    """
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
    request: DeleteBySourceRequest,
    _admin=Depends(require_admin),
):
    """Delete all chunks from a source URL (GDPR/CCPA compliance)."""
    from app.config import settings
    from app.services.delta_writer import delete_by_source_url

    deleted = delete_by_source_url(request.source_url, settings)
    return {"deleted": deleted, "source_url": request.source_url}
