"""Finnhub structured data connector for APFA.

Fetches market data and emits both structured records (Postgres) and
derived text summaries (RAG). Data types:
- Market news (general + category-filtered)
- Company-specific news
- Analyst recommendation trends
- SEC filings metadata
- Economic indicators
- Stock quotes (structured only, never RAG)

Rate limit: Finnhub free tier allows 30 calls/sec. All API calls are
throttled via RateLimiter and retried with exponential backoff.

Architecture (CoWork): Market data is served via agent tools (get_quote,
get_rate_trend), not RAG. Only derived textual summaries are embedded.

Adapted from Perplexity reference pipeline.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from app.connectors.base import (
    MarketDataRecord,
    NormalizedRecord,
    StructuredDataSource,
)
from app.services.pipeline_utils import (
    RateLimiter,
    now_utc_iso,
    retry,
    sha256_text,
)

logger = logging.getLogger(__name__)

# Finnhub free tier: 30 calls/sec
_DEFAULT_CALLS_PER_SEC = 29.0

# News categories supported by Finnhub
VALID_NEWS_CATEGORIES = {"general", "forex", "crypto", "merger"}


def _epoch_to_iso(ts: Optional[int | float]) -> str:
    """Convert Unix epoch timestamp to ISO-8601 UTC string."""
    if not ts:
        return ""
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    except (ValueError, OSError, OverflowError):
        return ""


class FinnhubFetcher:
    """Wrapper around Finnhub client with rate limiting and retries."""

    def __init__(self, client, calls_per_sec: float = _DEFAULT_CALLS_PER_SEC):
        self._client = client
        self._limiter = RateLimiter(calls_per_second=calls_per_sec)

    def _call(self, fn, *args, **kwargs) -> Any:
        self._limiter.wait()
        return fn(*args, **kwargs)

    @retry(max_attempts=5, base_delay=2.0, max_delay=60.0, exceptions=(Exception,))
    def quote(self, symbol: str) -> dict:
        return self._call(self._client.quote, symbol) or {}

    @retry(max_attempts=5, base_delay=2.0, max_delay=60.0, exceptions=(Exception,))
    def market_news(self, category: str = "general") -> list[dict]:
        if category not in VALID_NEWS_CATEGORIES:
            category = "general"
        return self._call(self._client.general_news, category, min_id=0) or []

    @retry(max_attempts=5, base_delay=2.0, max_delay=60.0, exceptions=(Exception,))
    def company_news(self, symbol: str, from_date: str, to_date: str) -> list[dict]:
        return (
            self._call(
                self._client.company_news, symbol, _from=from_date, to=to_date
            )
            or []
        )

    @retry(max_attempts=5, base_delay=2.0, max_delay=60.0, exceptions=(Exception,))
    def recommendation_trends(self, symbol: str) -> list[dict]:
        return self._call(self._client.recommendation_trends, symbol) or []

    @retry(max_attempts=5, base_delay=2.0, max_delay=60.0, exceptions=(Exception,))
    def economic_data(self, code: str) -> list[dict]:
        try:
            return self._call(self._client.economic_data, code) or []
        except Exception as exc:
            logger.info("Economic data %s unavailable: %s", code, exc)
            return []

    @retry(max_attempts=5, base_delay=2.0, max_delay=60.0, exceptions=(Exception,))
    def sec_filings(
        self, symbol: str, form_type: str = "", from_date: str = "", to_date: str = ""
    ) -> list[dict]:
        kwargs: dict[str, Any] = {"symbol": symbol}
        if form_type:
            kwargs["form"] = form_type
        if from_date:
            kwargs["from_"] = from_date
        if to_date:
            kwargs["to"] = to_date
        try:
            return self._call(self._client.filings, **kwargs) or []
        except Exception as exc:
            logger.warning("SEC filings for %s failed: %s", symbol, exc)
            return []

    @retry(max_attempts=5, base_delay=2.0, max_delay=60.0, exceptions=(Exception,))
    def company_basic_financials(self, symbol: str) -> dict:
        return self._call(self._client.company_basic_financials, symbol, "all") or {}


class FinnhubConnector(StructuredDataSource):
    """Fetch market data from Finnhub. Store structured data in Postgres,
    generate derived text summaries for RAG."""

    source_type = "finnhub"

    def __init__(self, api_key: str):
        self._api_key = api_key
        self._fetcher: Optional[FinnhubFetcher] = None

    def _get_fetcher(self) -> FinnhubFetcher:
        if self._fetcher is None:
            import finnhub

            client = finnhub.Client(api_key=self._api_key)
            self._fetcher = FinnhubFetcher(client)
        return self._fetcher

    def fetch(
        self,
        tickers: list[str] | None = None,
        data_types: list[str] | None = None,
        news_categories: list[str] | None = None,
        **kwargs,
    ) -> list[MarketDataRecord]:
        """Fetch market data from Finnhub.

        Args:
            tickers: Stock/ETF symbols.
            data_types: Types to fetch: "quote", "economic_indicator",
                        "recommendation", "fundamentals".
            news_categories: News categories: "general", "forex", etc.
        """
        fetcher = self._get_fetcher()
        data_types = data_types or ["quote"]
        tickers = tickers or []
        now_iso = now_utc_iso()
        records: list[MarketDataRecord] = []

        for dtype in data_types:
            if dtype == "quote" and tickers:
                records.extend(self._fetch_quotes(fetcher, tickers, now_iso))
            elif dtype == "economic_indicator":
                records.extend(self._fetch_economic_indicators(fetcher, now_iso))
            elif dtype == "recommendation" and tickers:
                records.extend(self._fetch_recommendations(fetcher, tickers, now_iso))
            elif dtype == "fundamentals" and tickers:
                records.extend(self._fetch_fundamentals(fetcher, tickers, now_iso))

        # Store raw news/filings data for RAG summaries (handled in generate_summaries)
        self._last_news: list[dict] = []
        self._last_filings: dict[str, list[dict]] = {}

        if news_categories:
            for cat in news_categories:
                items = fetcher.market_news(category=cat)
                for item in items:
                    item["_category"] = cat
                self._last_news.extend(items)

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        for ticker in tickers:
            ticker = ticker.upper()
            # Company news
            cnews = fetcher.company_news(ticker, "2024-01-01", today)
            for item in cnews:
                item["_category"] = f"company:{ticker}"
            self._last_news.extend(cnews)

            # SEC filings
            filings = fetcher.sec_filings(ticker, from_date="2024-01-01", to_date=today)
            if filings:
                self._last_filings[ticker] = filings

        logger.info(f"Fetched {len(records)} structured records from Finnhub")
        return records

    def _fetch_quotes(
        self, fetcher: FinnhubFetcher, tickers: list[str], now_iso: str
    ) -> list[MarketDataRecord]:
        records = []
        for ticker in tickers:
            try:
                q = fetcher.quote(ticker)
                records.append(
                    MarketDataRecord(
                        ticker=ticker,
                        data_type="quote",
                        value=q.get("c", 0),
                        unit="USD",
                        change_pct=q.get("dp", 0),
                        timestamp=now_iso,
                        source="finnhub",
                        metadata_json=json.dumps(
                            {
                                "open": q.get("o"),
                                "high": q.get("h"),
                                "low": q.get("l"),
                                "prev_close": q.get("pc"),
                            }
                        ),
                    )
                )
            except Exception as e:
                logger.error(f"Quote failed for {ticker}: {e}")
        return records

    def _fetch_economic_indicators(
        self, fetcher: FinnhubFetcher, now_iso: str
    ) -> list[MarketDataRecord]:
        records = []
        indicators = [
            ("MORTGAGE30US", "30-Year Fixed Mortgage Rate", "%"),
            ("MORTGAGE15US", "15-Year Fixed Mortgage Rate", "%"),
            ("FEDFUNDS", "Federal Funds Rate", "%"),
            ("UNRATE", "Unemployment Rate", "%"),
            ("CPIAUCSL", "Consumer Price Index", "index"),
        ]
        for code, name, unit in indicators:
            try:
                data = fetcher.economic_data(code)
                if data and isinstance(data, list) and data:
                    latest = data[-1] if isinstance(data, list) else data
                    value = latest.get("value", 0) if isinstance(latest, dict) else 0
                    records.append(
                        MarketDataRecord(
                            ticker=code,
                            data_type="economic_indicator",
                            value=float(value),
                            unit=unit,
                            timestamp=now_iso,
                            source="finnhub",
                            metadata_json=json.dumps({"name": name}),
                        )
                    )
            except Exception as e:
                logger.error(f"Economic indicator {code} failed: {e}")
        return records

    def _fetch_recommendations(
        self, fetcher: FinnhubFetcher, tickers: list[str], now_iso: str
    ) -> list[MarketDataRecord]:
        records = []
        for ticker in tickers:
            try:
                recs = fetcher.recommendation_trends(ticker)
                if recs:
                    latest = recs[0]
                    buy = latest.get("buy", 0) + latest.get("strongBuy", 0)
                    sell = latest.get("sell", 0) + latest.get("strongSell", 0)
                    hold = latest.get("hold", 0)
                    total = buy + sell + hold or 1
                    sentiment = (buy - sell) / total
                    records.append(
                        MarketDataRecord(
                            ticker=ticker,
                            data_type="recommendation",
                            value=sentiment,
                            unit="sentiment_score",
                            timestamp=now_iso,
                            source="finnhub",
                            metadata_json=json.dumps(latest),
                        )
                    )
            except Exception as e:
                logger.error(f"Recommendations for {ticker}: {e}")
        return records

    def _fetch_fundamentals(
        self, fetcher: FinnhubFetcher, tickers: list[str], now_iso: str
    ) -> list[MarketDataRecord]:
        records = []
        for ticker in tickers:
            try:
                metrics = fetcher.company_basic_financials(ticker)
                metric = metrics.get("metric", {})
                for key in [
                    "peNormalizedAnnual",
                    "dividendYieldIndicatedAnnual",
                    "marketCapitalization",
                    "52WeekHigh",
                    "52WeekLow",
                ]:
                    val = metric.get(key)
                    if val is not None:
                        records.append(
                            MarketDataRecord(
                                ticker=ticker,
                                data_type="fundamental",
                                value=float(val),
                                unit=key,
                                timestamp=now_iso,
                                source="finnhub",
                                metadata_json=json.dumps({"metric_name": key}),
                            )
                        )
            except Exception as e:
                logger.error(f"Fundamentals for {ticker}: {e}")
        return records

    def store(self, records: list[MarketDataRecord], db_session) -> int:
        """Store market data in Postgres (upsert by ticker + data_type)."""
        from sqlalchemy import text

        stored = 0
        for rec in records:
            try:
                db_session.execute(
                    text(
                        """
                        INSERT INTO market_data
                            (ticker, data_type, value, unit, change_pct,
                             timestamp, source, metadata_json)
                        VALUES
                            (:ticker, :data_type, :value, :unit, :change_pct,
                             :timestamp, :source, :metadata_json)
                        ON CONFLICT (ticker, data_type) DO UPDATE SET
                            value = EXCLUDED.value,
                            change_pct = EXCLUDED.change_pct,
                            timestamp = EXCLUDED.timestamp,
                            metadata_json = EXCLUDED.metadata_json
                        """
                    ),
                    {
                        "ticker": rec.ticker,
                        "data_type": rec.data_type,
                        "value": rec.value,
                        "unit": rec.unit,
                        "change_pct": rec.change_pct,
                        "timestamp": rec.timestamp,
                        "source": rec.source,
                        "metadata_json": rec.metadata_json,
                    },
                )
                stored += 1
            except Exception as e:
                logger.error(f"Store failed {rec.ticker}/{rec.data_type}: {e}")
        db_session.commit()
        return stored

    def generate_summaries(
        self, records: list[MarketDataRecord]
    ) -> list[NormalizedRecord]:
        """Generate derived text summaries from market data + news + filings.

        Economic indicators and recommendations get summaries. Market news
        items become individual RAG records. SEC filings get per-filing records.
        """
        now_iso = now_utc_iso()
        summaries: list[NormalizedRecord] = []

        # Economic indicators summary
        econ = [r for r in records if r.data_type == "economic_indicator"]
        if econ:
            lines = []
            for r in econ:
                meta = json.loads(r.metadata_json) if r.metadata_json else {}
                name = meta.get("name", r.ticker)
                lines.append(f"{name}: {r.value}{r.unit}")

            text = (
                f"Economic indicators as of {now_iso[:10]}: "
                + ". ".join(lines)
                + ". These indicators reflect current macroeconomic conditions "
                "relevant to lending, investment, and financial planning."
            )
            summaries.append(
                NormalizedRecord(
                    external_id=f"finnhub:econ_summary:{now_iso[:10]}",
                    source_type="finnhub",
                    source_url="https://finnhub.io",
                    title="Daily Economic Indicators Summary",
                    author="Finnhub",
                    published_at=now_iso,
                    fetched_at=now_iso,
                    freshness_class="daily",
                    content_kind="derived_summary",
                    text=text,
                    ttl_hours=24,
                )
            )

        # Recommendation summaries (with percentage breakdowns)
        recs = [r for r in records if r.data_type == "recommendation"]
        for r in recs:
            meta = json.loads(r.metadata_json) if r.metadata_json else {}
            buy = meta.get("buy", 0) + meta.get("strongBuy", 0)
            sell = meta.get("sell", 0) + meta.get("strongSell", 0)
            hold = meta.get("hold", 0)
            total = buy + sell + hold or 1
            pct_bullish = round(100 * buy / total, 1)
            pct_bearish = round(100 * sell / total, 1)

            sentiment = "bullish" if pct_bullish > 50 else "bearish" if pct_bearish > 50 else "mixed"

            text = (
                f"Analyst Recommendation Trends for {r.ticker} — {now_iso[:10]}\n"
                f"Strong Buy: {meta.get('strongBuy', 0)} | Buy: {meta.get('buy', 0)} | "
                f"Hold: {hold} | Sell: {meta.get('sell', 0)} | Strong Sell: {meta.get('strongSell', 0)}\n"
                f"Total analysts: {total}\n"
                f"Bullish: {pct_bullish}% | Bearish: {pct_bearish}%\n"
                f"Overall sentiment: {sentiment}"
            )
            summaries.append(
                NormalizedRecord(
                    external_id=f"finnhub:rec:{r.ticker}:{now_iso[:10]}",
                    source_type="finnhub",
                    source_url=f"https://finnhub.io/api/v1/stock/recommendation?symbol={r.ticker}",
                    title=f"{r.ticker} Analyst Recommendations",
                    author="Finnhub",
                    published_at=now_iso,
                    fetched_at=now_iso,
                    freshness_class="daily",
                    content_kind="derived_summary",
                    text=text,
                    ttl_hours=24,
                    metadata_json=json.dumps({"stance": sentiment}),
                )
            )

        # Market news items → individual RAG records
        seen_ids: set[str] = set()
        for item in getattr(self, "_last_news", []):
            headline = item.get("headline", "")
            summary = item.get("summary", "")
            source = item.get("source", "")
            url = item.get("url", "")
            ts = item.get("datetime", 0)
            published = _epoch_to_iso(ts)
            category = item.get("_category", "general")
            item_id = str(item.get("id", sha256_text(headline + url)[:16]))
            ext_id = f"finnhub:news:{item_id}"

            if ext_id in seen_ids:
                continue
            seen_ids.add(ext_id)

            text = f"Headline: {headline}\n"
            if summary:
                text += f"Summary: {summary}\n"
            text += f"Source: {source}\nCategory: {category}\n"

            summaries.append(
                NormalizedRecord(
                    external_id=ext_id,
                    source_type="finnhub",
                    source_url=url or "https://finnhub.io",
                    title=headline,
                    author=source,
                    published_at=published,
                    fetched_at=now_iso,
                    freshness_class="daily",
                    content_kind="derived_summary",
                    text=text.strip(),
                    ttl_hours=48,
                )
            )

        # SEC filings → individual RAG records
        for symbol, filings in getattr(self, "_last_filings", {}).items():
            for filing in filings[:20]:  # cap at 20 per symbol
                form = filing.get("form", "")
                filed_date = filing.get("filedDate", "")
                acc = filing.get("accessionNumber", "")
                report_url = filing.get("reportUrl", "")
                desc = filing.get("description", "")

                text = (
                    f"SEC Filing — {symbol}\n"
                    f"Form: {form} | Filed: {filed_date}\n"
                )
                if desc:
                    text += f"Description: {desc}\n"

                published = f"{filed_date}T00:00:00Z" if filed_date else now_iso

                summaries.append(
                    NormalizedRecord(
                        external_id=f"finnhub:sec:{symbol}:{acc or filed_date}:{form}",
                        source_type="finnhub",
                        source_url=report_url or "https://finnhub.io",
                        title=f"{symbol} {form} Filing — {filed_date}",
                        author="SEC EDGAR",
                        published_at=published,
                        fetched_at=now_iso,
                        freshness_class="weekly",
                        content_kind="derived_summary",
                        text=text.strip(),
                        ttl_hours=168,  # 1 week
                    )
                )

        return summaries
