"""Finnhub structured data connector for APFA.

Fetches market data (quotes, economic indicators, mortgage rates) and stores
in structured format. Does NOT embed raw numbers into FAISS.

Architecture (CoWork): Market data is served via agent tools (get_quote,
get_rate_trend), not RAG. Only derived textual summaries are embedded.

Refresh cadences:
- Quotes: 5-15 min (structured store only)
- Economic indicators: daily
- Recommendation trends: daily
- Fundamentals: daily/weekly
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from app.connectors.base import MarketDataRecord, NormalizedRecord, StructuredDataSource

logger = logging.getLogger(__name__)


class FinnhubConnector(StructuredDataSource):
    """Fetch market data from Finnhub and store in structured table.

    Produces derived textual summaries for RAG when generate_summaries()
    is called — these are the only artifacts that enter FAISS.
    """

    source_type = "finnhub"

    def __init__(self, api_key: str):
        self._api_key = api_key
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client

        import finnhub

        self._client = finnhub.Client(api_key=self._api_key)
        return self._client

    def fetch(
        self,
        tickers: list[str] | None = None,
        data_types: list[str] | None = None,
    ) -> list[MarketDataRecord]:
        """Fetch market data from Finnhub.

        Args:
            tickers: Stock/ETF symbols (e.g. ["AAPL", "SPY"]).
            data_types: Types to fetch: "quote", "fundamentals",
                        "economic_indicator", "recommendation".

        Returns:
            List of MarketDataRecord objects.
        """
        client = self._get_client()
        data_types = data_types or ["quote"]
        tickers = tickers or []
        now_iso = datetime.now(timezone.utc).isoformat()
        records: list[MarketDataRecord] = []

        for dtype in data_types:
            if dtype == "quote" and tickers:
                records.extend(self._fetch_quotes(client, tickers, now_iso))
            elif dtype == "economic_indicator":
                records.extend(
                    self._fetch_economic_indicators(client, now_iso)
                )
            elif dtype == "recommendation" and tickers:
                records.extend(
                    self._fetch_recommendations(client, tickers, now_iso)
                )
            elif dtype == "fundamentals" and tickers:
                records.extend(
                    self._fetch_fundamentals(client, tickers, now_iso)
                )

        logger.info(f"Fetched {len(records)} records from Finnhub")
        return records

    def _fetch_quotes(
        self, client, tickers: list[str], now_iso: str
    ) -> list[MarketDataRecord]:
        records = []
        for ticker in tickers:
            try:
                q = client.quote(ticker)
                records.append(
                    MarketDataRecord(
                        ticker=ticker,
                        data_type="quote",
                        value=q.get("c", 0),  # current price
                        unit="USD",
                        change_pct=q.get("dp", 0),  # % change
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
                logger.error(f"Finnhub quote failed for {ticker}: {e}")
        return records

    def _fetch_economic_indicators(
        self, client, now_iso: str
    ) -> list[MarketDataRecord]:
        """Fetch key economic indicators relevant to financial advising."""
        records = []
        # Mortgage rate indicators from FRED via Finnhub
        indicators = [
            ("MORTGAGE30US", "30-Year Fixed Mortgage Rate", "%"),
            ("MORTGAGE15US", "15-Year Fixed Mortgage Rate", "%"),
            ("FEDFUNDS", "Federal Funds Rate", "%"),
            ("UNRATE", "Unemployment Rate", "%"),
            ("CPIAUCSL", "Consumer Price Index", "index"),
        ]

        for code, name, unit in indicators:
            try:
                data = client.economic_data(code)
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
                logger.error(f"Finnhub economic indicator {code} failed: {e}")

        return records

    def _fetch_recommendations(
        self, client, tickers: list[str], now_iso: str
    ) -> list[MarketDataRecord]:
        records = []
        for ticker in tickers:
            try:
                recs = client.recommendation_trends(ticker)
                if recs:
                    latest = recs[0]
                    # Compute a net sentiment score
                    buy = latest.get("buy", 0) + latest.get("strongBuy", 0)
                    sell = latest.get("sell", 0) + latest.get("strongSell", 0)
                    hold = latest.get("hold", 0)
                    total = buy + sell + hold or 1
                    sentiment = (buy - sell) / total  # -1 to +1
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
                logger.error(f"Finnhub recommendations for {ticker}: {e}")
        return records

    def _fetch_fundamentals(
        self, client, tickers: list[str], now_iso: str
    ) -> list[MarketDataRecord]:
        records = []
        for ticker in tickers:
            try:
                metrics = client.company_basic_financials(ticker, "all")
                metric = metrics.get("metric", {})
                if metric:
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
                                    metadata_json=json.dumps(
                                        {"metric_name": key}
                                    ),
                                )
                            )
            except Exception as e:
                logger.error(f"Finnhub fundamentals for {ticker}: {e}")
        return records

    def store(self, records: list[MarketDataRecord], db_session) -> int:
        """Store market data records in Postgres.

        Uses the MarketData ORM model (to be created in orm_models.py).
        Upserts by (ticker, data_type) to keep latest values.
        """
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
                logger.error(
                    f"Failed to store {rec.ticker}/{rec.data_type}: {e}"
                )

        db_session.commit()
        return stored

    def generate_summaries(
        self, records: list[MarketDataRecord]
    ) -> list[NormalizedRecord]:
        """Generate natural language summaries from market data for RAG.

        Only economic indicators and recommendations get summaries —
        raw quotes are too ephemeral.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        summaries: list[NormalizedRecord] = []

        # Group by data type
        econ = [r for r in records if r.data_type == "economic_indicator"]
        recs = [r for r in records if r.data_type == "recommendation"]

        if econ:
            lines = []
            for r in econ:
                meta = json.loads(r.metadata_json) if r.metadata_json else {}
                name = meta.get("name", r.ticker)
                lines.append(f"{name}: {r.value}{r.unit}")

            summary_text = (
                f"Economic indicators as of {now_iso[:10]}: "
                + ". ".join(lines)
                + ". These indicators reflect current macroeconomic conditions "
                "relevant to lending, investment, and financial planning decisions."
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
                    text=summary_text,
                    ttl_hours=24,
                )
            )

        if recs:
            for r in recs:
                meta = json.loads(r.metadata_json) if r.metadata_json else {}
                buy = meta.get("buy", 0) + meta.get("strongBuy", 0)
                sell = meta.get("sell", 0) + meta.get("strongSell", 0)
                hold = meta.get("hold", 0)

                if r.value > 0.3:
                    stance = "bullish"
                elif r.value < -0.3:
                    stance = "bearish"
                else:
                    stance = "neutral"

                text = (
                    f"Analyst consensus on {r.ticker} as of {now_iso[:10]}: "
                    f"{stance} (buy: {buy}, hold: {hold}, sell: {sell}). "
                    f"Net sentiment score: {r.value:.2f}."
                )

                summaries.append(
                    NormalizedRecord(
                        external_id=f"finnhub:rec:{r.ticker}:{now_iso[:10]}",
                        source_type="finnhub",
                        source_url="https://finnhub.io",
                        title=f"Analyst Recommendations: {r.ticker}",
                        author="Finnhub",
                        published_at=now_iso,
                        fetched_at=now_iso,
                        freshness_class="daily",
                        content_kind="derived_summary",
                        text=text,
                        ttl_hours=24,
                        metadata_json=json.dumps({"stance": stance}),
                    )
                )

        return summaries
