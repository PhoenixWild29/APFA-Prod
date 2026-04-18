"""YouTube transcript connector for APFA.

Accepts video IDs from Google Takeout export or manual curation, fetches
transcripts, cleans auto-caption errors (regex-based + optional LLM pass),
applies finance classification, detects stance per chunk, and emits
NormalizedRecord chunks with timestamp locators.

Key features from Perplexity reference:
- Full Takeout watch-history parser with date filtering and dedup
- Regex-based auto-caption corrections (40+ financial term patterns)
- Finance classification with confidence levels + needs_llm flag
- Stance detection (bullish/bearish/neutral/mixed) per chunk
- Rich channel allowlist for finance content creators
- Timestamp-aware semantic chunking with overlap

IMPORTANT: Never embed raw auto-captions without cleaning — error rate
on financial terminology is too high per CoWork review.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import parse_qs, urlparse

from app.connectors.base import NormalizedRecord, RAGSource
from app.services.chunking import timestamp_chunk
from app.services.pipeline_utils import (
    RateLimiter,
    detect_stance,
    now_utc_iso,
    parse_iso,
    retry,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Finance classification
# ---------------------------------------------------------------------------

DEFAULT_FINANCE_CHANNELS: set[str] = {
    "bloomberg television",
    "cnbc television",
    "cnbc",
    "yahoo finance",
    "motley fool",
    "the motley fool",
    "finviz",
    "investors.com",
    "tastytrade",
    "benzinga",
    "seeking alpha",
    "valuetainment",
    "andrei jikh",
    "meet kevin",
    "graham stephan",
    "mark meldrum",
    "new money",
    "patrick boyle",
    "plain bagel",
    "two cents",
    "wall street millennial",
    "whiteboard finance",
}

FINANCE_KEYWORDS = re.compile(
    r"\b(stock|stocks|etf|fund|bond|bonds|equity|equities|earnings|revenue|"
    r"eps|dividend|dividends|portfolio|option|options|futures|fed|federal\s+reserve|"
    r"interest\s+rate|inflation|gdp|recession|bull\s*market|bear\s*market|"
    r"s&p|nasdaq|dow\s+jones|russell|ticker|share|shares|ipo|spac|"
    r"valuation|p\/e|pe\s+ratio|market\s+cap|yield|coupon|cpi|ppi|"
    r"central\s+bank|ecb|fomc|quarter|annual\s+report|10-k|10-q|sec\s+filing|"
    r"crypto|bitcoin|ethereum|defi|blockchain|commodity|commodities|"
    r"oil|gold|silver|forex|currency|mortgage|loan|refinance|"
    r"reit|real\s+estate|401k|ira|roth)\b",
    re.IGNORECASE,
)

FINANCE_KEYWORD_MIN_MATCHES = 3


def classify_finance(
    channel_name: str,
    title: str,
    description: str = "",
    allowlist: set[str] | None = None,
) -> dict[str, Any]:
    """Classify a video as finance-related using allowlist + keywords.

    Returns dict with is_finance, confidence, classification_method, needs_llm.
    """
    al = {c.lower() for c in (allowlist or DEFAULT_FINANCE_CHANNELS)}

    if channel_name.lower() in al:
        return {
            "is_finance": True,
            "confidence": "high",
            "classification_method": "channel_allowlist",
            "needs_llm": False,
        }

    combined = f"{title} {description}"
    matches = FINANCE_KEYWORDS.findall(combined)
    count = len(matches)

    if count >= FINANCE_KEYWORD_MIN_MATCHES:
        confidence = "high" if count >= 8 else "medium"
        return {
            "is_finance": True,
            "confidence": confidence,
            "classification_method": f"keywords:{count}",
            "needs_llm": False,
        }
    elif count > 0:
        return {
            "is_finance": False,
            "confidence": "uncertain",
            "classification_method": f"keywords:{count}",
            "needs_llm": True,
        }
    return {
        "is_finance": False,
        "confidence": "low",
        "classification_method": "no_signals",
        "needs_llm": False,
    }


# ---------------------------------------------------------------------------
# Auto-caption corrections (regex-based, no LLM cost)
# ---------------------------------------------------------------------------

_CAPTION_CORRECTIONS: list[tuple[re.Pattern, str]] = [
    # Tickers
    (re.compile(r"\bapple\s+incorporated\b", re.I), "AAPL"),
    (re.compile(r"\bmicrosoft\s+corporation\b", re.I), "MSFT"),
    (re.compile(r"\bamazon\s+dot\s+com\b", re.I), "AMZN"),
    (re.compile(r"\btesla\s+incorporated\b", re.I), "TSLA"),
    (re.compile(r"\bgoogle\b(?!\s+(?:docs|drive|sheets|slides))", re.I), "GOOGL"),
    (re.compile(r"\bnvidia\s+corporation\b", re.I), "NVDA"),
    (re.compile(r"\bmeta\s+platforms\b", re.I), "META"),
    # Common mis-hearings
    (re.compile(r"\bear\b(?=\s+per\s+share)", re.I), "EPS"),
    (re.compile(r"\bearnings\s+per\s+share\b", re.I), "EPS"),
    (re.compile(r"\bprice\s+to\s+earnings\b", re.I), "P/E"),
    (re.compile(r"\bpee\s+ee\b", re.I), "P/E"),
    (re.compile(r"\besa?\s*pee\s*five\s*hundred\b", re.I), "S&P 500"),
    (re.compile(r"\bsnp\s+500\b", re.I), "S&P 500"),
    (re.compile(r"\bfed(?:eral)?\s+res(?:erve)?\b", re.I), "Federal Reserve"),
    (re.compile(r"\bfee[\s-]ock\b", re.I), "FOMC"),
    (re.compile(r"\bquantitative\s+ee[sz]ing\b", re.I), "quantitative easing"),
    (re.compile(r"\bq\s*e\b(?=\s)", re.I), "QE"),
    (re.compile(r"\bbasis\s+point[s]?\b", re.I), "bps"),
    (re.compile(r"\bhundredth(?:s)?\s+of\s+a\s+percent\b", re.I), "bps"),
    # Inflation metrics
    (re.compile(r"\bconsumer\s+price\s+index\b", re.I), "CPI"),
    (re.compile(r"\bproducer\s+price\s+index\b", re.I), "PPI"),
    (re.compile(r"\bgross\s+domestic\s+product\b", re.I), "GDP"),
    # Cryptocurrency
    (re.compile(r"\bbit\s+coin\b", re.I), "Bitcoin"),
    (re.compile(r"\beether\b", re.I), "Ether"),
    (re.compile(r"\bdee\s+fee\b", re.I), "DeFi"),
    # SEC filings
    (re.compile(r"\bten\s+kay\b", re.I), "10-K"),
    (re.compile(r"\bten\s+cue\b", re.I), "10-Q"),
    (re.compile(r"\beight\s+kay\b", re.I), "8-K"),
    # Regulatory
    (re.compile(r"\btiller\b", re.I), "TILA"),
    (re.compile(r"\brespa\b", re.I), "RESPA"),
    (re.compile(r"\becoa\b", re.I), "ECOA"),
]


def clean_transcript_text(text: str) -> str:
    """Apply regex corrections to auto-caption text for financial terms."""
    for pattern, replacement in _CAPTION_CORRECTIONS:
        text = pattern.sub(replacement, text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Takeout parser
# ---------------------------------------------------------------------------

_VIDEO_ID_RE = re.compile(r"[?&]v=([A-Za-z0-9_-]{11})")


@dataclass
class WatchEntry:
    """One watched video from Takeout history."""

    video_id: str
    title: str
    channel: str
    watched_at: str
    watch_count: int = 1
    video_url: str = field(default="")
    channel_url: str = field(default="")

    def __post_init__(self):
        if not self.video_url and self.video_id:
            self.video_url = f"https://www.youtube.com/watch?v={self.video_id}"


def parse_takeout_watch_history(
    takeout_json: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> list[WatchEntry]:
    """Parse Google Takeout watch-history.json into deduplicated WatchEntries.

    Handles the Takeout format:
    - titleUrl field contains YouTube video URL
    - subtitles[0].name contains channel name
    - time contains ISO-8601 watch timestamp
    - title has "Watched " prefix to strip

    Returns list sorted newest-watched first, with watch_count for repeats.
    """
    data = json.loads(takeout_json)
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON array, got {type(data).__name__}")

    seen: dict[str, dict] = {}
    skipped = 0

    for item in data:
        url = item.get("titleUrl", "")
        if not url:
            skipped += 1
            continue

        m = _VIDEO_ID_RE.search(url)
        if not m:
            try:
                parsed = urlparse(url)
                qs = parse_qs(parsed.query)
                ids = qs.get("v", [])
                video_id = ids[0] if ids else None
            except Exception:
                video_id = None
            if not video_id:
                skipped += 1
                continue
        else:
            video_id = m.group(1)

        # Parse watch time
        time_str = item.get("time", "")
        watched_dt = parse_iso(time_str)

        # Date filter
        if start_date and watched_dt and watched_dt < start_date:
            continue
        if end_date and watched_dt and watched_dt > end_date:
            continue

        # Channel metadata
        subtitles = item.get("subtitles", [])
        channel_name = ""
        channel_url = ""
        if subtitles and isinstance(subtitles, list):
            first = subtitles[0]
            channel_name = first.get("name", "")
            channel_url = first.get("url", "")

        title = re.sub(
            r"^Watched\s+", "", item.get("title", ""), count=1, flags=re.I
        ).strip()

        if video_id in seen:
            existing = seen[video_id]
            existing["count"] += 1
            if watched_dt and (
                existing["watched_dt"] is None
                or watched_dt > existing["watched_dt"]
            ):
                existing["watched_dt"] = watched_dt
                existing["watched_at_str"] = time_str
                if title:
                    existing["title"] = title
                if channel_name:
                    existing["channel"] = channel_name
        else:
            seen[video_id] = {
                "video_id": video_id,
                "title": title,
                "channel": channel_name,
                "channel_url": channel_url,
                "video_url": url,
                "watched_dt": watched_dt,
                "watched_at_str": time_str,
                "count": 1,
            }

    logger.info(
        f"Takeout: {len(data)} entries → {len(seen)} unique videos "
        f"(skipped {skipped})"
    )

    entries = []
    for d in sorted(
        seen.values(),
        key=lambda x: x["watched_dt"] or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    ):
        entries.append(
            WatchEntry(
                video_id=d["video_id"],
                title=d["title"],
                channel=d["channel"],
                watched_at=d["watched_at_str"],
                watch_count=d["count"],
                video_url=d["video_url"],
                channel_url=d.get("channel_url", ""),
            )
        )

    return entries


# ---------------------------------------------------------------------------
# Connector class
# ---------------------------------------------------------------------------

MIN_TRANSCRIPT_CHARS = 100


class YouTubeTranscriptConnector(RAGSource):
    """Ingest YouTube video transcripts into the RAG pipeline.

    Input: video IDs from Google Takeout export or manual curation.
    Pipeline: fetch transcript → clean captions (regex + optional LLM) →
    classify finance → timestamp-aware chunking → stance detection → embed.
    """

    source_type = "youtube"

    def __init__(
        self,
        openai_api_key: str = "",
        openai_model: str = "gpt-4o",
        finance_allowlist: set[str] | None = None,
    ):
        self._openai_api_key = openai_api_key
        self._openai_model = openai_model
        self._finance_allowlist = finance_allowlist

    def fetch(
        self,
        video_ids: list[str] | None = None,
        takeout_json: str | None = None,
        filter_finance: bool = True,
        **kwargs,
    ) -> list[dict]:
        """Fetch transcripts for video IDs.

        Args:
            video_ids: YouTube video IDs.
            takeout_json: Raw Google Takeout watch-history.json content.
            filter_finance: Skip non-finance videos if True.
        """
        from youtube_transcript_api import YouTubeTranscriptApi

        watch_entries: list[WatchEntry] = []

        if takeout_json and not video_ids:
            watch_entries = parse_takeout_watch_history(takeout_json)
            video_ids = [e.video_id for e in watch_entries]

        if not video_ids:
            return []

        # Build channel lookup from Takeout entries
        takeout_channels: dict[str, str] = {}
        for e in watch_entries:
            if e.video_id and e.channel:
                takeout_channels[e.video_id] = e.channel

        raw_docs = []
        for video_id in video_ids:
            try:
                # Fetch transcript (prefer manual over auto-generated)
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                transcript = None
                is_auto = False

                try:
                    transcript = transcript_list.find_manually_created_transcript(["en"])
                except Exception:
                    try:
                        transcript = transcript_list.find_generated_transcript(["en"])
                        is_auto = True
                    except Exception:
                        logger.info(f"No English transcript for {video_id}")
                        continue

                segments = transcript.fetch()

                # Skip very short transcripts
                full_text = " ".join(s.get("text", "") for s in segments)
                if len(full_text) < MIN_TRANSCRIPT_CHARS:
                    logger.info(f"Transcript too short for {video_id}")
                    continue

                # Get metadata via oEmbed (no API key needed)
                meta = self._get_video_metadata(video_id)
                channel = meta.get("channel", takeout_channels.get(video_id, ""))

                # Finance classification
                fc = classify_finance(
                    channel_name=channel,
                    title=meta.get("title", ""),
                    allowlist=self._finance_allowlist,
                )

                if filter_finance and not fc["is_finance"] and not fc["needs_llm"]:
                    logger.debug(f"Skipping non-finance: {meta.get('title', video_id)}")
                    continue

                raw_docs.append(
                    {
                        "video_id": video_id,
                        "title": meta.get("title", f"Video {video_id}"),
                        "channel": channel,
                        "segments": segments,
                        "is_auto_caption": is_auto,
                        "published_at": meta.get("published_at", ""),
                        "finance_classification": fc,
                    }
                )

            except Exception as e:
                logger.error(f"Failed transcript for {video_id}: {e}")

        logger.info(f"Fetched {len(raw_docs)}/{len(video_ids)} transcripts")
        return raw_docs

    def _get_video_metadata(self, video_id: str) -> dict:
        """Get video metadata via oEmbed (no API key required)."""
        import urllib.request

        url = (
            "https://www.youtube.com/oembed?"
            f"url=https://www.youtube.com/watch?v={video_id}&format=json"
        )
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read())
                return {
                    "title": data.get("title", ""),
                    "channel": data.get("author_name", ""),
                    "published_at": "",
                }
        except Exception:
            return {"title": "", "channel": ""}

    def transform(self, raw_docs: list[dict]) -> list[NormalizedRecord]:
        """Transform transcripts into chunked NormalizedRecords.

        Applies regex caption cleaning, timestamp chunking, and stance detection.
        """
        now_iso = now_utc_iso()
        all_records: list[NormalizedRecord] = []

        for doc in raw_docs:
            video_id = doc["video_id"]
            segments = doc["segments"]

            # Clean auto-captions with regex corrections (always, no cost)
            cleaned_segments = [
                {**seg, "text": clean_transcript_text(seg.get("text", ""))}
                for seg in segments
            ]

            # Optional LLM cleaning for auto-captions (expensive, only if configured)
            if (
                doc.get("is_auto_caption")
                and self._openai_api_key
            ):
                cleaned_segments = self._llm_clean_captions(
                    cleaned_segments, doc["title"]
                )

            # Timestamp-aware chunking with overlap
            chunks = timestamp_chunk(
                cleaned_segments, window_sec=75.0, overlap_sec=12.0
            )

            for chunk in chunks:
                chunk_text = chunk["text"]
                if not chunk_text.strip():
                    continue

                stance = detect_stance(chunk_text)
                start_sec = chunk["start_sec"]
                end_sec = chunk["end_sec"]
                idx = chunk["chunk_index"]

                start_fmt = self._format_timestamp(start_sec)
                end_fmt = self._format_timestamp(end_sec)

                metadata = {
                    "video_id": video_id,
                    "channel": doc["channel"],
                    "is_auto_caption": doc.get("is_auto_caption", False),
                    "start_sec": start_sec,
                    "end_sec": end_sec,
                    "snippet_locator": f"{start_fmt}-{end_fmt}",
                    "stance": stance,
                    "finance_classification": doc.get("finance_classification", {}),
                }

                record = NormalizedRecord(
                    external_id=f"youtube:{video_id}:{idx:04d}",
                    source_type="youtube",
                    source_url=f"https://www.youtube.com/watch?v={video_id}&t={int(start_sec)}s",
                    title=doc["title"],
                    author=doc["channel"],
                    published_at=doc.get("published_at", now_iso),
                    fetched_at=now_iso,
                    freshness_class="static",
                    content_kind="transcript_segment",
                    text=chunk_text,
                    chunk_index=idx,
                    total_chunks=len(chunks),
                    parent_document_id=f"youtube:{video_id}",
                    metadata_json=json.dumps(metadata),
                )
                all_records.append(record)

        return all_records

    def _llm_clean_captions(
        self,
        segments: list[dict[str, Any]],
        video_title: str,
    ) -> list[dict[str, Any]]:
        """Optional LLM pass for caption cleaning (expensive, use sparingly).

        The regex corrections handle most cases. This is a fallback for
        cases the regex can't catch.
        """
        if not self._openai_api_key:
            return segments

        try:
            from openai import OpenAI

            client = OpenAI(api_key=self._openai_api_key)

            batch_size = 50
            cleaned = []

            for i in range(0, len(segments), batch_size):
                batch = segments[i: i + batch_size]
                raw_text = " ".join(s.get("text", "") for s in batch)

                response = client.chat.completions.create(
                    model=self._openai_model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are correcting auto-generated YouTube captions "
                                "from a finance/investment video. Fix ONLY factual "
                                "errors in financial terminology:\n"
                                "- Capitalize ticker symbols (spy→SPY, qqq→QQQ)\n"
                                "- Fix percentage/rate values if clearly wrong\n"
                                "- Correct regulatory terms (tiller→TILA)\n"
                                "- Fix common terms (pee ratio→P/E ratio)\n"
                                "Do NOT rephrase, summarize, or change meaning. "
                                "Return corrected text only."
                            ),
                        },
                        {
                            "role": "user",
                            "content": f"Video: {video_title}\n\n{raw_text}",
                        },
                    ],
                    max_tokens=len(raw_text.split()) * 2,
                    temperature=0.1,
                )

                cleaned_text = response.choices[0].message.content.strip()
                words = cleaned_text.split()
                word_idx = 0

                for seg in batch:
                    orig_count = len(seg.get("text", "").split())
                    seg_words = words[word_idx: word_idx + orig_count]
                    cleaned.append(
                        {
                            **seg,
                            "text": " ".join(seg_words) if seg_words else seg.get("text", ""),
                        }
                    )
                    word_idx += orig_count

            return cleaned

        except Exception as e:
            logger.warning(f"LLM caption cleaning failed: {e}")
            return segments

    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
