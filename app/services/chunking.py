"""Structure-aware text chunking for the APFA data pipeline.

Splits text into semantically coherent chunks based on document type:
- Regulatory docs: split on section headers (Item, Section, Part boundaries)
- Prose/general: 300-500 token semantic windows with ~15% overlap
- YouTube transcripts: 60-90 second timestamp-aware windows
- Spreadsheets: sheet-level and table-level summaries

Never chunks across section boundaries. Chunks include positional metadata
(chunk_index, total_chunks) for provenance tracking.
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Chunk:
    text: str
    chunk_index: int
    total_chunks: int = 0  # set after all chunks are generated
    start_sec: Optional[float] = None  # YouTube transcripts only
    end_sec: Optional[float] = None


# ---------------------------------------------------------------------------
# Sentence splitting
# ---------------------------------------------------------------------------

_SENTENCE_RE = re.compile(
    r"(?<=[.!?])\s+(?=[A-Z])"  # period/excl/question + space + capital
    r"|(?<=\.)\s*\n"  # period + newline
)


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences. Falls back to newline splitting."""
    sentences = _SENTENCE_RE.split(text.strip())
    # Filter empty strings and whitespace-only
    return [s.strip() for s in sentences if s.strip()]


def _word_count(text: str) -> int:
    return len(text.split())


# ---------------------------------------------------------------------------
# Section header detection (regulatory documents)
# ---------------------------------------------------------------------------

_SECTION_HEADER_RE = re.compile(
    r"^(?:"
    r"(?:Section|SECTION|Item|ITEM|Part|PART|Article|ARTICLE)\s+\d+"  # Section 1, Item 2
    r"|(?:§\s*\d+)"  # §1234
    r"|(?:[IVXLCDM]+\.\s)"  # Roman numerals: IV. ...
    r"|(?:\d+\.\d+(?:\.\d+)*\s)"  # 1.2.3 numbering
    r"|(?:[A-Z][A-Z\s]{4,}$)"  # ALL CAPS line (likely a header)
    r")",
    re.MULTILINE,
)


def _split_on_sections(text: str) -> list[str]:
    """Split text at section headers. Returns sections including headers."""
    positions = [m.start() for m in _SECTION_HEADER_RE.finditer(text)]
    if not positions:
        return [text]

    # Add start if first section doesn't begin at 0
    if positions[0] != 0:
        positions.insert(0, 0)

    sections = []
    for i, start in enumerate(positions):
        end = positions[i + 1] if i + 1 < len(positions) else len(text)
        section = text[start:end].strip()
        if section:
            sections.append(section)
    return sections


# ---------------------------------------------------------------------------
# Core chunking strategies
# ---------------------------------------------------------------------------

def _chunk_by_token_window(
    text: str,
    min_tokens: int = 300,
    max_tokens: int = 500,
    overlap_fraction: float = 0.15,
) -> list[str]:
    """Semantic window chunking with overlap. Never splits mid-sentence."""
    sentences = _split_sentences(text)
    if not sentences:
        return [text] if text.strip() else []

    chunks: list[str] = []
    current_sentences: list[str] = []
    current_words = 0
    overlap_target = int(max_tokens * overlap_fraction)

    for sentence in sentences:
        sw = _word_count(sentence)

        # Single sentence exceeds max — split at word boundaries
        if sw > max_tokens:
            # Flush current buffer first
            if current_sentences:
                chunks.append(" ".join(current_sentences))
                current_sentences = []
                current_words = 0

            words = sentence.split()
            for i in range(0, len(words), max_tokens):
                chunk_words = words[i : i + max_tokens]
                chunks.append(" ".join(chunk_words))
            continue

        if current_words + sw > max_tokens and current_words >= min_tokens:
            # Flush current chunk
            chunks.append(" ".join(current_sentences))

            # Carry overlap: take trailing sentences up to overlap_target words
            overlap_sentences: list[str] = []
            overlap_words = 0
            for s in reversed(current_sentences):
                s_words = _word_count(s)
                if overlap_words + s_words > overlap_target:
                    break
                overlap_sentences.insert(0, s)
                overlap_words += s_words

            current_sentences = overlap_sentences
            current_words = overlap_words

        current_sentences.append(sentence)
        current_words += sw

    # Flush remaining
    if current_sentences:
        chunks.append(" ".join(current_sentences))

    return chunks


def chunk_regulatory(text: str) -> list[Chunk]:
    """Chunk regulatory documents: split on section headers first, then
    apply token-window chunking within each section."""
    sections = _split_on_sections(text)
    raw_chunks: list[str] = []
    for section in sections:
        if _word_count(section) <= 500:
            raw_chunks.append(section)
        else:
            raw_chunks.extend(_chunk_by_token_window(section))

    return [Chunk(text=c, chunk_index=i) for i, c in enumerate(raw_chunks)]


def chunk_prose(
    text: str,
    min_tokens: int = 300,
    max_tokens: int = 500,
) -> list[Chunk]:
    """Chunk general prose documents with semantic windows and overlap."""
    raw_chunks = _chunk_by_token_window(text, min_tokens, max_tokens)
    return [Chunk(text=c, chunk_index=i) for i, c in enumerate(raw_chunks)]


@dataclass
class TranscriptSegment:
    text: str
    start: float  # seconds
    duration: float


def chunk_transcript(
    segments: list[TranscriptSegment],
    min_seconds: float = 60.0,
    max_seconds: float = 90.0,
) -> list[Chunk]:
    """Chunk YouTube transcript segments by timestamp windows.

    Groups transcript segments into 60-90 second windows, preserving
    start_sec/end_sec for deep-linking ("Per CNBC at 4:23...").
    """
    if not segments:
        return []

    chunks: list[Chunk] = []
    window_texts: list[str] = []
    window_start = segments[0].start
    window_end = window_start

    for seg in segments:
        seg_end = seg.start + seg.duration
        window_duration = seg_end - window_start

        if window_duration > max_seconds and window_texts:
            chunks.append(
                Chunk(
                    text=" ".join(window_texts),
                    chunk_index=len(chunks),
                    start_sec=window_start,
                    end_sec=window_end,
                )
            )
            window_texts = []
            window_start = seg.start

        window_texts.append(seg.text)
        window_end = seg_end

    # Flush remaining
    if window_texts:
        # If too short, merge with previous chunk
        if chunks and (window_end - window_start) < min_seconds:
            prev = chunks[-1]
            chunks[-1] = Chunk(
                text=prev.text + " " + " ".join(window_texts),
                chunk_index=prev.chunk_index,
                start_sec=prev.start_sec,
                end_sec=window_end,
            )
        else:
            chunks.append(
                Chunk(
                    text=" ".join(window_texts),
                    chunk_index=len(chunks),
                    start_sec=window_start,
                    end_sec=window_end,
                )
            )

    # Set total_chunks
    for chunk in chunks:
        chunk.total_chunks = len(chunks)

    return chunks


def chunk_spreadsheet(
    sheet_name: str,
    headers: list[str],
    rows: list[list[str]],
    summary: str = "",
) -> list[Chunk]:
    """Chunk spreadsheet data: one summary chunk + one chunk per row group.

    Produces a sheet-level summary chunk, then groups rows into chunks of
    ~10 rows each with column headers repeated for context.
    """
    chunks: list[Chunk] = []

    # Sheet summary
    header_str = ", ".join(headers)
    summary_text = (
        f"Spreadsheet: {sheet_name}. Columns: {header_str}. "
        f"{len(rows)} rows total."
    )
    if summary:
        summary_text += f" {summary}"
    chunks.append(Chunk(text=summary_text, chunk_index=0))

    # Row groups (~10 rows per chunk)
    group_size = 10
    for i in range(0, len(rows), group_size):
        group = rows[i : i + group_size]
        row_texts = []
        for row in group:
            pairs = [
                f"{h}: {v}" for h, v in zip(headers, row) if v.strip()
            ]
            row_texts.append("; ".join(pairs))
        chunk_text = (
            f"{sheet_name} (rows {i + 1}-{i + len(group)}): "
            + " | ".join(row_texts)
        )
        chunks.append(Chunk(text=chunk_text, chunk_index=len(chunks)))

    for chunk in chunks:
        chunk.total_chunks = len(chunks)

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
    """Route to the appropriate chunking strategy based on content_kind.

    Args:
        text: The document text to chunk.
        content_kind: One of "doc_section", "transcript_segment",
                      "sheet_table", "regulation", "market_snapshot",
                      "derived_summary".
        transcript_segments: Required if content_kind is "transcript_segment".
        spreadsheet_data: Dict with keys "sheet_name", "headers", "rows",
                          and optional "summary". Required for "sheet_table".

    Returns:
        List of Chunk objects with positional metadata.
    """
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
        # Market snapshots and derived summaries are already short —
        # return as a single chunk
        return [Chunk(text=text, chunk_index=0, total_chunks=1)]

    # Default: prose chunking
    return chunk_prose(text)
