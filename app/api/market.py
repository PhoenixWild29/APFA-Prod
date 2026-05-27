import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user_hybrid
from app.models.market import (
    DashboardSummary,
    LatestInsight,
    MarketHistoryResponse,
    MarketQuote,
    EconomicIndicator,
)
from app.services.market_service import (
    get_dashboard_summary,
    get_economic_indicators,
    get_latest_insight,
    get_market_history,
    get_quotes,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/market", tags=["market-data"])

ALLOWED_TICKERS = {"SPY", "QQQ", "DIA", "TLT"}
ALLOWED_HISTORY_DATA_TYPES = {"quote", "economic_indicator"}
MAX_HISTORY_DAYS = 365


@router.get("/quotes", response_model=list[MarketQuote])
async def list_quotes(
    request: Request,
    tickers: Optional[str] = Query(
        None,
        description="Comma-separated ticker symbols (e.g., SPY,QQQ). Omit for all.",
    ),
    current_user: dict = Depends(get_current_user_hybrid),
    db: Session = Depends(get_db),
):
    ticker_list = None
    if tickers:
        ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    return get_quotes(db, ticker_list)


@router.get("/economic-indicators", response_model=list[EconomicIndicator])
async def list_economic_indicators(
    request: Request,
    current_user: dict = Depends(get_current_user_hybrid),
    db: Session = Depends(get_db),
):
    return get_economic_indicators(db)


@router.get("/dashboard-summary", response_model=DashboardSummary)
async def dashboard_summary(
    request: Request,
    current_user: dict = Depends(get_current_user_hybrid),
    db: Session = Depends(get_db),
):
    return get_dashboard_summary(db)


@router.get("/history", response_model=MarketHistoryResponse)
async def market_history(
    request: Request,
    ticker: str = Query(..., description="Ticker symbol (e.g., SPY)"),
    data_type: str = Query("quote", description="Data type: quote or economic_indicator"),
    days: int = Query(30, ge=1, le=MAX_HISTORY_DAYS, description="Number of days of history"),
    current_user: dict = Depends(get_current_user_hybrid),
    db: Session = Depends(get_db),
):
    if data_type not in ALLOWED_HISTORY_DATA_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid data_type. Allowed: {', '.join(sorted(ALLOWED_HISTORY_DATA_TYPES))}",
        )
    return get_market_history(db, ticker, data_type, days)


@router.get("/latest-insight", response_model=Optional[LatestInsight])
async def latest_insight(
    request: Request,
    current_user: dict = Depends(get_current_user_hybrid),
    db: Session = Depends(get_db),
):
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found")
    return get_latest_insight(db, user_id)
