import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.market import (
    DashboardSummary,
    EconomicIndicator,
    LatestInsight,
    MarketHistoryPoint,
    MarketHistoryResponse,
    MarketQuote,
)
from app.orm_models import MarketData

logger = logging.getLogger(__name__)

QUOTE_STALE_HOURS = 2
INDICATOR_STALE_HOURS = 48

INSIGHT_PREVIEW_LENGTH = 200


def _parse_timestamp(ts: str) -> Optional[datetime]:
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
        try:
            dt = datetime.strptime(ts, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def _is_stale(timestamp_str: str, threshold_hours: int) -> bool:
    dt = _parse_timestamp(timestamp_str)
    if dt is None:
        return True
    return datetime.now(timezone.utc) - dt > timedelta(hours=threshold_hours)


def get_quotes(db: Session, tickers: Optional[list[str]] = None) -> list[MarketQuote]:
    query = db.query(MarketData).filter(MarketData.data_type == "quote")
    if tickers:
        query = query.filter(MarketData.ticker.in_([t.upper() for t in tickers]))
    records = query.all()

    results = []
    for r in records:
        meta = json.loads(r.metadata_json) if r.metadata_json else {}
        results.append(
            MarketQuote(
                ticker=r.ticker,
                price=r.value,
                change_pct=r.change_pct,
                open=meta.get("open"),
                high=meta.get("high"),
                low=meta.get("low"),
                prev_close=meta.get("prev_close"),
                updated_at=r.timestamp,
                is_stale=_is_stale(r.timestamp, QUOTE_STALE_HOURS),
            )
        )
    return results


def get_economic_indicators(db: Session) -> list[EconomicIndicator]:
    records = (
        db.query(MarketData)
        .filter(MarketData.data_type == "economic_indicator")
        .all()
    )

    results = []
    for r in records:
        meta = json.loads(r.metadata_json) if r.metadata_json else {}
        results.append(
            EconomicIndicator(
                code=r.ticker,
                name=meta.get("name", r.ticker),
                value=r.value,
                unit=r.unit,
                updated_at=r.timestamp,
                is_stale=_is_stale(r.timestamp, INDICATOR_STALE_HOURS),
            )
        )
    return results


def get_dashboard_summary(db: Session) -> DashboardSummary:
    quotes = get_quotes(db)
    indicators = get_economic_indicators(db)

    all_timestamps = [q.updated_at for q in quotes] + [i.updated_at for i in indicators]
    last_updated = max(all_timestamps) if all_timestamps else None

    any_stale = any(q.is_stale for q in quotes) or any(i.is_stale for i in indicators)
    staleness_warning = None
    if not quotes and not indicators:
        staleness_warning = "No market data available. Data pipeline may not be running."
    elif any_stale:
        staleness_warning = "Some data may be delayed. Check data pipeline status."

    return DashboardSummary(
        quotes=quotes,
        indicators=indicators,
        last_updated=last_updated,
        staleness_warning=staleness_warning,
    )


def get_market_history(
    db: Session, ticker: str, data_type: str = "quote", days: int = 30
) -> MarketHistoryResponse:
    days = min(days, 365)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    rows = db.execute(
        text(
            """
            SELECT recorded_date, value, change_pct
            FROM market_data_history
            WHERE ticker = :ticker AND data_type = :data_type
              AND recorded_date >= :cutoff
            ORDER BY recorded_date ASC
            """
        ),
        {"ticker": ticker.upper(), "data_type": data_type, "cutoff": cutoff.date()},
    ).fetchall()

    points = [
        MarketHistoryPoint(
            date=str(row.recorded_date),
            value=row.value,
            change_pct=row.change_pct,
        )
        for row in rows
    ]

    return MarketHistoryResponse(
        ticker=ticker.upper(),
        data_type=data_type,
        points=points,
        total_points=len(points),
    )


def get_latest_insight(db: Session, user_id: str) -> Optional[LatestInsight]:
    row = db.execute(
        text(
            """
            SELECT cm.content, c.id AS conversation_id, cm.created_at
            FROM conversation_messages cm
            JOIN conversations c ON cm.conversation_id = c.id
            WHERE c.user_id = :uid AND c.deleted_at IS NULL AND cm.role = 'assistant'
            ORDER BY c.updated_at DESC, cm.seq DESC
            LIMIT 1
            """
        ),
        {"uid": user_id},
    ).fetchone()

    if row is None:
        return None

    content = row.content or ""
    preview = content[:INSIGHT_PREVIEW_LENGTH]
    has_more = len(content) > INSIGHT_PREVIEW_LENGTH
    if has_more:
        last_space = preview.rfind(" ")
        if last_space > INSIGHT_PREVIEW_LENGTH // 2:
            preview = preview[:last_space] + "..."
        else:
            preview += "..."

    return LatestInsight(
        preview=preview,
        conversation_id=str(row.conversation_id),
        created_at=row.created_at.isoformat() if hasattr(row.created_at, "isoformat") else str(row.created_at),
        has_more=has_more,
    )
