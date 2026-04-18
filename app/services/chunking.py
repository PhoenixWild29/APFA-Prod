"""Structure-aware text chunking for the APFA data pipeline.

Four chunking strategies, each respecting content structure:

    sentence_aware_chunk(text, target_tokens, overlap_pct)
        General-purpose sentence-boundary chunker for prose text.

    section_aware_chunk(text, section_pattern, target_tokens)
        Splits Markdown/structured text on header boundaries, then
        sub-chunks oversized sections with sentence_aware_chunk.

    timestamp_chunk(segments, window_sec, overlap_sec)
        Groups transcript segments into fixed-duration windows with
        overlap. Never splits mid-segment. Returns start_sec/end_sec.

    spreadsheet_chunk(sheet_name, headers, rows)
        Summary chunk + batched row chunks with header context.

Token sizing uses ~4 chars/token approximation (GPT-family heuristic).
Adapted from Perplexity reference pipeline with APFA enhancements.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from app.services.pipeline_utils import approx_token_count


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Chunk:
    text: str
    chunk_index: int
    total_chunks: int = 0
    start_sec: Optional[float] = None
    end_sec: Optional[float] = None
    section_title: str = ""
    chunk_kind: str = ""  # "summary", "rows", "section", etc.
    token_count: int = 0

    def __post_init__(self):
        if not self.token_count:
            self.token_count = approx_token_count(self.text)


@dataclass
class TranscriptSegment:
    text: str
    start: float  # seconds
    duration: float


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_SENT_SPLIT = re.compile(
    r"(?<=[.!?])\s+(?=[A-Z\"'\(])"  # after terminal punctuation + space
    r"|(?<=\n)\s*(?=\n)"  # blank-line paragraph break
)


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences. Handles prose and paragraph breaks."""
    raw = _SENT_SPLIT.split(text.strip())
    out = [s.strip() for s in raw if s.strip()]
    return out or [text.strip()]


def _build_chunks_from_sentences(
    sentences: list[str],
    target_tokens: int,
    overlap_pct: float,
) -> list[str]:
    """Greedy sentence packer with overlap.

    Fills a window up to target_tokens, then starts a new window with
    overlap_pct of the previous window re-used for context continuity.
    """
    if not sentences:
        return []

    overlap_tokens = max(1, int(target_tokens * overlap_pct))
    chunks: list[str] = []
    current: list[str] = []
    current_tokens: int = 0

    i = 0
    while i < len(sentences):
        sent = sentences[i]
        sent_tok = approx_token_count(sent)

        if current_tokens + sent_tok > target_tokens and current:
            chunks.append(" ".join(current))

            # Build overlap: walk back from end until overlap_tokens filled
            overlap: list[str] = []
            overlap_total = 0
            for s in reversed(current):
                s_tok = approx_token_count(s)
                if overlap_total + s_tok > overlap_tokens:
                    break
                overlap.insert(0, s)
                overlap_total += s_tok

            current = overlap
            current_tokens = overlap_total
            continue  # re-process current sentence in new window

        current.append(sent)
        current_tokens += sent_tok
        i += 1

    if current:
        chunks.append(" ".join(current))

    return chunks


# ---------------------------------------------------------------------------
# Public API: Prose chunking
# ---------------------------------------------------------------------------

def sentence_aware_chunk(
    text: str,
    target_tokens: int = 400,
    overlap_pct: float = 0.15,
) -> list[dict[str, Any]]:
    """Split text into sentence-aligned chunks with overlap.

    Returns list of dicts with text, chunk_index, token_count.
    """
    text = text.strip()
    if not text:
        return []

    sentences = _split_sentences(text)
    raw_chunks = _build_chunks_from_sentences(sentences, target_tokens, overlap_pct)

    return [
        {
            "text": c,
            "chunk_index": idx,
            "token_count": approx_token_count(c),
        }
        for idx, c in enumerate(raw_chunks)
        if c.strip()
    ]


def chunk_prose(
    text: str,
    target_tokens: int = 400,
    overlap_pct: float = 0.15,
) -> list[Chunk]:
    """Chunk general prose documents. Returns Chunk objects."""
    raw = sentence_aware_chunk(text, target_tokens, overlap_pct)
    chunks = [
        Chunk(text=c["text"], chunk_index=c["chunk_index"])
        for c in raw
    ]
    for c in chunks:
        c.total_chunks = len(chunks)
    return chunks


# ---------------------------------------------------------------------------
# Public API: Section-aware chunking (regulatory / Markdown)
# ---------------------------------------------------------------------------

# Matches Markdown headers, regulatory section headers, and all-caps lines
_DEFAULT_SECTION_RE = (
    r"^(?:"
    r"#{1,3}\s"  # Markdown headers
    r"|(?:Section|SECTION|Item|ITEM|Part|PART|Article|ARTICLE)\s+\d+"
    r"|(?:§\s*\d+)"
    r"|(?:[IVXLCDM]+\.\s)"
    r"|(?:\d+\.\d+(?:\.\d+)*\s)"
    r")"
)


def section_aware_chunk(
    text: str,
    section_pattern: str = _DEFAULT_SECTION_RE,
    target_tokens: int = 400,
    overlap_pct: float = 0.15,
) -> list[dict[str, Any]]:
    """Split structured text on header boundaries, then sub-chunk.

    Returns list of dicts with text, section_title, chunk_index,
    section_chunk_index, token_count.
    """
    text = text.strip()
    if not text:
        return []

    header_re = re.compile(section_pattern, re.MULTILINE)
    lines = text.splitlines(keepends=True)

    # Group lines into sections
    sections: list[tuple[str, str]] = []
    current_header = ""
    current_body: list[str] = []

    for line in lines:
        if header_re.match(line):
            if current_body or current_header:
                sections.append((current_header, "".join(current_body)))
            current_header = line.strip()
            current_body = []
        else:
            current_body.append(line)

    if current_body or current_header:
        sections.append((current_header, "".join(current_body)))

    results: list[dict[str, Any]] = []
    global_idx = 0

    for header, body in sections:
        body = body.strip()
        section_text = (f"{header}\n\n{body}" if header else body).strip()
        if not section_text:
            continue

        if approx_token_count(section_text) <= target_tokens:
            results.append(
                {
                    "text": section_text,
                    "section_title": header,
                    "chunk_index": global_idx,
                    "section_chunk_index": 0,
                    "token_count": approx_token_count(section_text),
                }
            )
            global_idx += 1
        else:
            sub_chunks = sentence_aware_chunk(
                section_text, target_tokens, overlap_pct
            )
            for sub_idx, sc in enumerate(sub_chunks):
                results.append(
                    {
                        "text": sc["text"],
                        "section_title": header,
                        "chunk_index": global_idx,
                        "section_chunk_index": sub_idx,
                        "token_count": sc["token_count"],
                    }
                )
                global_idx += 1

    return results


def chunk_regulatory(text: str) -> list[Chunk]:
    """Chunk regulatory documents using section-aware splitting."""
    raw = section_aware_chunk(text)
    chunks = [
        Chunk(
            text=c["text"],
            chunk_index=c["chunk_index"],
            section_title=c.get("section_title", ""),
        )
        for c in raw
    ]
    for c in chunks:
        c.total_chunks = len(chunks)
    return chunks


# ---------------------------------------------------------------------------
# Public API: Timestamp-aware chunking (YouTube transcripts)
# ---------------------------------------------------------------------------

def timestamp_chunk(
    segments: list[dict[str, Any]] | list[TranscriptSegment],
    window_sec: float = 75.0,
    overlap_sec: float = 12.0,
) -> list[dict[str, Any]]:
    """Group transcript segments into fixed-duration windows with overlap.

    Never splits mid-segment. Each chunk includes start_sec/end_sec for
    deep-linking ("Per CNBC at 4:23...").

    Args:
        segments: Transcript segments with text, start, duration.
        window_sec: Target window duration in seconds (default 75).
        overlap_sec: Overlap between consecutive windows (default 12).

    Returns:
        List of dicts with text, start_sec, end_sec, chunk_index, token_count.
    """
    if not segments:
        return []

    # Normalize to dicts
    segs: list[dict[str, Any]] = []
    for s in segments:
        if isinstance(s, TranscriptSegment):
            segs.append({"text": s.text, "start": s.start, "duration": s.duration})
        else:
            segs.append(s)

    def seg_end(seg: dict[str, Any]) -> float:
        return float(seg.get("start", 0)) + float(seg.get("duration", 0))

    chunks: list[dict[str, Any]] = []
    chunk_idx = 0
    i = 0
    n = len(segs)

    while i < n:
        window_start = float(segs[i].get("start", 0))
        window_end_target = window_start + window_sec

        # Collect segments until we pass the target window end
        j = i
        while j < n and float(segs[j].get("start", 0)) < window_end_target:
            j += 1

        window_segs = segs[i:j]
        if not window_segs:
            i += 1
            continue

        text = " ".join(s.get("text", "").strip() for s in window_segs)
        actual_start = float(window_segs[0].get("start", 0))
        actual_end = seg_end(window_segs[-1])

        chunks.append(
            {
                "text": text.strip(),
                "start_sec": round(actual_start, 2),
                "end_sec": round(actual_end, 2),
                "chunk_index": chunk_idx,
                "token_count": approx_token_count(text),
            }
        )
        chunk_idx += 1

        # Advance: find first segment that starts after (window_end - overlap)
        overlap_boundary = window_end_target - overlap_sec
        next_i = j
        for k in range(i, j):
            if float(segs[k].get("start", 0)) >= overlap_boundary:
                next_i = k
                break

        # Guard against infinite loop
        if next_i <= i:
            next_i = i + 1
        i = next_i

    return chunks


def chunk_transcript(
    segments: list[TranscriptSegment] | list[dict[str, Any]],
    window_sec: float = 75.0,
    overlap_sec: float = 12.0,
) -> list[Chunk]:
    """Chunk transcript segments into Chunk objects with timestamps."""
    raw = timestamp_chunk(segments, window_sec, overlap_sec)
    chunks = [
        Chunk(
            text=c["text"],
            chunk_index=c["chunk_index"],
            start_sec=c["start_sec"],
            end_sec=c["end_sec"],
        )
        for c in raw
    ]
    for c in chunks:
        c.total_chunks = len(chunks)
    return chunks


# ---------------------------------------------------------------------------
# Public API: Spreadsheet chunking
# ---------------------------------------------------------------------------

def spreadsheet_chunk(
    sheet_name: str,
    headers: list[str],
    rows: list[list[Any]],
    max_rows_per_chunk: int = 30,
) -> list[dict[str, Any]]:
    """Convert one spreadsheet sheet into text chunks for RAG.

    Produces:
    1. A summary chunk (name, columns, row count, sample rows)
    2. Batched row chunks with header context repeated

    Returns list of dicts with text, chunk_index, chunk_kind,
    sheet_name, row_start, row_end, token_count.
    """
    results: list[dict[str, Any]] = []
    chunk_idx = 0

    # Summary chunk
    col_list = ", ".join(f'"{h}"' for h in headers)
    summary_text = (
        f"Sheet: {sheet_name}\n"
        f"Columns ({len(headers)}): {col_list}\n"
        f"Total rows: {len(rows)}\n"
    )
    if rows:
        summary_text += "\nSample rows:\n"
        for row in rows[:3]:
            pairs = "; ".join(
                f"{h}={v}"
                for h, v in zip(headers, row)
                if v not in (None, "", [])
            )
            summary_text += f"  {pairs}\n"

    results.append(
        {
            "text": summary_text.strip(),
            "chunk_index": chunk_idx,
            "chunk_kind": "summary",
            "sheet_name": sheet_name,
            "row_start": 0,
            "row_end": 0,
            "token_count": approx_token_count(summary_text),
        }
    )
    chunk_idx += 1

    # Row chunks
    header_line = "Columns: " + " | ".join(str(h) for h in headers)
    total_batches = math.ceil(len(rows) / max_rows_per_chunk) if rows else 0

    for batch_num in range(total_batches):
        start = batch_num * max_rows_per_chunk
        end = min(start + max_rows_per_chunk, len(rows))
        batch = rows[start:end]

        lines = [f"Sheet: {sheet_name}", header_line, ""]
        for row_idx, row in enumerate(batch, start=start):
            pairs = []
            for header, cell in zip(headers, row):
                cell_str = str(cell) if cell not in (None, "") else ""
                if cell_str:
                    pairs.append(f"{header}={cell_str}")
            lines.append(f"Row {row_idx + 1}: " + "; ".join(pairs))

        chunk_text = "\n".join(lines)
        results.append(
            {
                "text": chunk_text.strip(),
                "chunk_index": chunk_idx,
                "chunk_kind": "rows",
                "sheet_name": sheet_name,
                "row_start": start,
                "row_end": end,
                "token_count": approx_token_count(chunk_text),
            }
        )
        chunk_idx += 1

    return results


def chunk_spreadsheet(
    sheet_name: str,
    headers: list[str],
    rows: list[list[str]],
    summary: str = "",
) -> list[Chunk]:
    """Chunk spreadsheet data into Chunk objects."""
    raw = spreadsheet_chunk(sheet_name, headers, rows)
    chunks = [
        Chunk(
            text=c["text"],
            chunk_index=c["chunk_index"],
            chunk_kind=c["chunk_kind"],
        )
        for c in raw
    ]
    for c in chunks:
        c.total_chunks = len(chunks)
    return chunks


# ---------------------------------------------------------------------------
# Unified entry point
# ---------------------------------------------------------------------------

def chunk_text(
    text: str,
    content_kind: str = "doc_section",
    transcript_segments: list[TranscriptSegment] | None = None,
    spreadsheet_data: dict | None = None,
) -> list[Chunk]:
    """Route to the appropriate chunking strategy based on content_kind."""
    if content_kind == "transcript_segment":
        if transcript_segments is None:
            raise ValueError(
                "transcript_segments required for content_kind='transcript_segment'"
            )
        return chunk_transcript(transcript_segments)

    if content_kind == "sheet_table":
        if spreadsheet_data is None:
            raise ValueError(
                "spreadsheet_data required for content_kind='sheet_table'"
            )
        return chunk_spreadsheet(
            sheet_name=spreadsheet_data["sheet_name"],
            headers=spreadsheet_data["headers"],
            rows=spreadsheet_data["rows"],
            summary=spreadsheet_data.get("summary", ""),
        )

    if content_kind == "regulation":
        return chunk_regulatory(text)

    if content_kind in ("market_snapshot", "derived_summary"):
        return [Chunk(text=text, chunk_index=0, total_chunks=1)]

    return chunk_prose(text)
