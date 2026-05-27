from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MarketQuote(BaseModel):
    ticker: str
    price: float
    change_pct: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    prev_close: Optional[float] = None
    updated_at: str
    is_stale: bool = False


class EconomicIndicator(BaseModel):
    code: str
    name: str
    value: float
    unit: str
    updated_at: str
    is_stale: bool = False


class DashboardSummary(BaseModel):
    quotes: list[MarketQuote]
    indicators: list[EconomicIndicator]
    last_updated: Optional[str] = None
    staleness_warning: Optional[str] = None


class MarketHistoryPoint(BaseModel):
    date: str
    value: float
    change_pct: Optional[float] = None


class MarketHistoryResponse(BaseModel):
    ticker: str
    data_type: str
    points: list[MarketHistoryPoint]
    total_points: int


class LatestInsight(BaseModel):
    preview: str
    conversation_id: str
    created_at: str
    has_more: bool = False
