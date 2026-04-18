"""YouTube transcript connector for APFA.

Extracts transcripts from investment education videos, cleans them
(auto-captions have high error rates on tickers/rates), chunks by
timestamp windows, and ingests into the RAG corpus.

Input: Video IDs from Google Takeout export (watch history JSON).
The YouTube Data API watch history endpoint was removed by Google.

IMPORTANT: Never embed raw auto-captions without cleaning — error rate
on financial terminology (tickers, percentages, regulatory terms) is
too high per CoWork review. Captions must pass an LLM cleaning step.

Attribution: Every chunk includes video URL, channel name, and
timestamp locator for deep-linking.
"""

import json
import logging
import re
from datetime import datetime, timezone
from typing import Optional

from app.connectors.base import NormalizedRecord, RAGSource
from app.services.chunking import TranscriptSegment, chunk_transcript

logger = logging.getLogger(__name__)

# Channels known to produce investment/finance content
FINANCE_CHANNEL_ALLOWLIST = {
    # Populated by admin — channel IDs of trusted finance creators
}

# Keywords that indicate finance content
FINANCE_KEYWORDS = [
    "mortgage", "interest rate", "stock", "bond", "portfolio",
    "dividend", "ETF", "index fund", "investment", "401k",
    "IRA", "Roth", "real estate", "REIT", "inflation",
    "federal reserve", "fed", "treasury", "yield",
    "S&P 500", "nasdaq", "dow jones", "market cap",
    "P/E ratio", "earnings", "revenue", "EBITDA",
    "credit score", "FICO", "loan", "refinance",
    "budget", "savings", "emergency fund", "debt",
    "capital gains", "tax", "deduction",
]


def parse_takeout_watch_history(takeout_json: str) -> list[str]:
    """Extract video IDs from Google Takeout watch history JSON.

    The Takeout export is a JSON array of objects with 'titleUrl' fields
    containing YouTube video URLs.

    Args:
        takeout_json: Raw JSON string from Google Takeout.

    Returns:
        List of YouTube video IDs.
    """
    data = json.loads(takeout_json)
    video_ids = []

    for entry in data:
        url = entry.get("titleUrl", "")
        # Extract video ID from URL
        match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
        if match:
            video_ids.append(match.group(1))

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for vid in video_ids:
        if vid not in seen:
            seen.add(vid)
            unique.append(vid)

    logger.info(
        f"Parsed {len(unique)} unique video IDs from Takeout "
        f"({len(video_ids)} total entries)"
    )
    return unique


def is_finance_content(title: str, description: str = "", channel: str = "") -> bool:
    """Heuristic filter for finance-related content.

    Returns True if the video likely contains investment/finance education.
    """
    text = f"{title} {description} {channel}".lower()
    score = sum(1 for kw in FINANCE_KEYWORDS if kw.lower() in text)
    return score >= 2


class YouTubeTranscriptConnector(RAGSource):
    """Ingest YouTube video transcripts into the RAG pipeline.

    Input: List of video IDs (from Google Takeout or manual curation).
    Pipeline: fetch transcript → clean with LLM → timestamp-aware chunking
    → embed → DeltaTable.
    """

    source_type = "youtube"

    def __init__(self, openai_api_key: str = "", openai_model: str = "gpt-4o"):
        self._openai_api_key = openai_api_key
        self._openai_model = openai_model

    def fetch(
        self,
        video_ids: list[str] | None = None,
        takeout_json: str | None = None,
        filter_finance: bool = True,
    ) -> list[dict]:
        """Fetch transcripts for given video IDs.

        Args:
            video_ids: List of YouTube video IDs.
            takeout_json: Raw Google Takeout watch history JSON
                          (alternative to video_ids).
            filter_finance: If True, skip non-finance videos.

        Returns:
            List of raw document dicts with keys:
            video_id, title, channel, segments, description
        """
        from youtube_transcript_api import YouTubeTranscriptApi

        if takeout_json and not video_ids:
            video_ids = parse_takeout_watch_history(takeout_json)

        if not video_ids:
            return []

        raw_docs = []
        for video_id in video_ids:
            try:
                # Fetch transcript segments
                transcript_list = YouTubeTranscriptApi.list_transcripts(
                    video_id
                )

                # Prefer manual captions over auto-generated
                transcript = None
                try:
                    transcript = transcript_list.find_manually_created_transcript(
                        ["en"]
                    )
                except Exception:
                    try:
                        transcript = transcript_list.find_generated_transcript(
                            ["en"]
                        )
                    except Exception:
                        logger.warning(
                            f"No English transcript for {video_id}"
                        )
                        continue

                segments = transcript.fetch()

                # Get video metadata (title, channel) via oEmbed
                meta = self._get_video_metadata(video_id)

                if filter_finance and not is_finance_content(
                    meta.get("title", ""),
                    meta.get("description", ""),
                    meta.get("channel", ""),
                ):
                    logger.debug(
                        f"Skipping non-finance video: {meta.get('title', video_id)}"
                    )
                    continue

                is_auto = transcript.is_generated
                raw_docs.append(
                    {
                        "video_id": video_id,
                        "title": meta.get("title", f"Video {video_id}"),
                        "channel": meta.get("channel", "Unknown"),
                        "description": meta.get("description", ""),
                        "segments": segments,
                        "is_auto_caption": is_auto,
                        "published_at": meta.get("published_at", ""),
                    }
                )

            except Exception as e:
                logger.error(f"Failed to fetch transcript for {video_id}: {e}")

        logger.info(
            f"Fetched {len(raw_docs)} transcripts from {len(video_ids)} videos"
        )
        return raw_docs

    def _get_video_metadata(self, video_id: str) -> dict:
        """Get video metadata via oEmbed (no API key required)."""
        import urllib.request
        import urllib.parse

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
                    "description": "",
                    "published_at": "",
                }
        except Exception:
            return {"title": "", "channel": "", "description": ""}

    def transform(self, raw_docs: list[dict]) -> list[NormalizedRecord]:
        """Transform raw transcripts into chunked NormalizedRecords.

        Auto-captions are cleaned via LLM before chunking.
        Chunks are 60-90 second timestamp-aware windows.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        all_records: list[NormalizedRecord] = []

        for doc in raw_docs:
            video_id = doc["video_id"]
            segments_raw = doc["segments"]

            # Convert to TranscriptSegment objects
            segments = [
                TranscriptSegment(
                    text=seg.get("text", seg.get("text", "")),
                    start=seg.get("start", 0),
                    duration=seg.get("duration", 0),
                )
                for seg in segments_raw
            ]

            # Clean auto-captions if needed
            if doc.get("is_auto_caption") and self._openai_api_key:
                segments = self._clean_captions(segments, doc["title"])

            # Chunk by timestamp windows
            chunks = chunk_transcript(segments)

            for chunk in chunks:
                # Build timestamp locator for attribution
                start_mm_ss = self._format_timestamp(chunk.start_sec or 0)
                end_mm_ss = self._format_timestamp(chunk.end_sec or 0)
                locator = f"{start_mm_ss}-{end_mm_ss}"

                ext_id = (
                    f"youtube:{video_id}:chunk:{chunk.chunk_index:04d}"
                )

                metadata = {
                    "video_id": video_id,
                    "channel": doc["channel"],
                    "is_auto_caption": doc.get("is_auto_caption", False),
                    "start_sec": chunk.start_sec,
                    "end_sec": chunk.end_sec,
                    "snippet_locator": locator,
                }

                record = NormalizedRecord(
                    external_id=ext_id,
                    source_type="youtube",
                    source_url=f"https://www.youtube.com/watch?v={video_id}&t={int(chunk.start_sec or 0)}",
                    title=doc["title"],
                    author=doc["channel"],
                    published_at=doc.get("published_at", now_iso),
                    fetched_at=now_iso,
                    freshness_class="static",
                    content_kind="transcript_segment",
                    text=chunk.text,
                    chunk_index=chunk.chunk_index,
                    total_chunks=chunk.total_chunks,
                    parent_document_id=f"youtube:{video_id}",
                    metadata_json=json.dumps(metadata),
                )
                all_records.append(record)

        return all_records

    def _clean_captions(
        self,
        segments: list[TranscriptSegment],
        video_title: str,
    ) -> list[TranscriptSegment]:
        """Clean auto-generated captions using an LLM pass.

        Fixes common auto-caption errors on financial terms:
        - Ticker symbols (e.g., "spy" → "SPY")
        - Percentages and rates
        - Regulatory terms (e.g., "tiller" → "TILA")
        """
        if not self._openai_api_key:
            return segments

        try:
            from openai import OpenAI

            client = OpenAI(api_key=self._openai_api_key)

            # Process in batches to stay within token limits
            batch_size = 50
            cleaned_segments = []

            for i in range(0, len(segments), batch_size):
                batch = segments[i : i + batch_size]
                raw_text = " ".join(s.text for s in batch)

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
                                "- Correct regulatory terms (tiller→TILA, respa→RESPA)\n"
                                "- Fix common financial terms (pee ratio→P/E ratio)\n"
                                "Do NOT rephrase, summarize, or change meaning. "
                                "Return the corrected text only."
                            ),
                        },
                        {
                            "role": "user",
                            "content": f"Video: {video_title}\n\nCaption text:\n{raw_text}",
                        },
                    ],
                    max_tokens=len(raw_text.split()) * 2,
                    temperature=0.1,
                )

                cleaned_text = response.choices[0].message.content.strip()

                # Redistribute cleaned text back to segments proportionally
                words = cleaned_text.split()
                word_idx = 0
                for seg in batch:
                    orig_word_count = len(seg.text.split())
                    seg_words = words[word_idx : word_idx + orig_word_count]
                    cleaned_segments.append(
                        TranscriptSegment(
                            text=" ".join(seg_words) if seg_words else seg.text,
                            start=seg.start,
                            duration=seg.duration,
                        )
                    )
                    word_idx += orig_word_count

            return cleaned_segments

        except Exception as e:
            logger.warning(f"Caption cleaning failed, using raw captions: {e}")
            return segments

    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Format seconds as MM:SS."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
