"""Unit tests for chunking strategies with reduced chunk sizes.

Validates that the new defaults (128 tokens, 20% overlap) produce
smaller, more focused chunks suitable for financial Q&A retrieval.
"""

import pytest

from app.services.chunking import (
    Chunk,
    TranscriptSegment,
    chunk_prose,
    chunk_text,
    sentence_aware_chunk,
    section_aware_chunk,
    spreadsheet_chunk,
    timestamp_chunk,
)
from app.services.pipeline_utils import approx_token_count


# ---------------------------------------------------------------------------
# Sample financial prose (~600 tokens / ~2400 chars)
# ---------------------------------------------------------------------------

SAMPLE_FINANCIAL_TEXT = (
    "A mortgage is a loan used to purchase real estate, where the property "
    "serves as collateral. Fixed-rate mortgages maintain the same interest "
    "rate for the entire loan term, typically 15 or 30 years. "
    "Adjustable-rate mortgages start with a lower rate that changes after "
    "an initial fixed period. The debt-to-income ratio is a key factor "
    "lenders consider when evaluating mortgage applications. "
    "Most lenders prefer a DTI ratio below 43 percent. "
    "Private mortgage insurance is required when the down payment is less "
    "than 20 percent of the home's purchase price. "
    "PMI typically costs between 0.3 and 1.5 percent of the original loan "
    "amount per year. Once you reach 20 percent equity, you can request "
    "PMI removal. "
    "Closing costs typically range from 2 to 5 percent of the loan amount "
    "and include origination fees, appraisal fees, title insurance, and "
    "prepaid taxes and insurance. "
    "Points, also known as discount points, allow borrowers to pay upfront "
    "to reduce their interest rate. Each point costs 1 percent of the loan "
    "amount and typically reduces the rate by 0.25 percentage points. "
    "The break-even period for buying points depends on how long you plan "
    "to stay in the home. "
    "Refinancing replaces your existing mortgage with a new one, often to "
    "secure a lower interest rate or change the loan term. Cash-out "
    "refinancing lets you borrow against your home equity. "
    "Home equity lines of credit provide flexible borrowing against your "
    "home's value. HELOCs typically have variable interest rates and a "
    "draw period followed by a repayment period. "
    "Escrow accounts hold funds for property taxes and homeowners insurance. "
    "Lenders often require escrow accounts to ensure these obligations are "
    "paid on time. Monthly escrow payments are included in your mortgage "
    "payment alongside principal and interest."
)


# ---------------------------------------------------------------------------
# sentence_aware_chunk tests
# ---------------------------------------------------------------------------


class TestSentenceAwareChunk:
    def test_default_128_produces_multiple_chunks(self):
        chunks = sentence_aware_chunk(SAMPLE_FINANCIAL_TEXT)
        assert len(chunks) > 3, f"Expected >3 chunks at 128 tokens, got {len(chunks)}"

    def test_chunks_under_token_limit(self):
        chunks = sentence_aware_chunk(SAMPLE_FINANCIAL_TEXT)
        for c in chunks:
            assert c["token_count"] <= 180, (
                f"Chunk {c['chunk_index']} has {c['token_count']} tokens "
                f"(expected <=180 allowing sentence overshoot)"
            )

    def test_128_produces_more_chunks_than_400(self):
        small = sentence_aware_chunk(SAMPLE_FINANCIAL_TEXT, target_tokens=128)
        large = sentence_aware_chunk(SAMPLE_FINANCIAL_TEXT, target_tokens=400)
        assert len(small) > len(large), (
            f"128-token chunking ({len(small)}) should produce more "
            f"chunks than 400-token ({len(large)})"
        )

    def test_overlap_present(self):
        chunks = sentence_aware_chunk(SAMPLE_FINANCIAL_TEXT)
        if len(chunks) < 2:
            pytest.skip("Need at least 2 chunks to verify overlap")
        first_end = chunks[0]["text"].split(". ")[-1]
        second_start = chunks[1]["text"].split(". ")[0]
        assert first_end in chunks[1]["text"] or second_start in chunks[0]["text"], (
            "Expected overlap between adjacent chunks"
        )

    def test_empty_input(self):
        assert sentence_aware_chunk("") == []
        assert sentence_aware_chunk("   ") == []

    def test_short_input_single_chunk(self):
        short = "This is a short sentence."
        chunks = sentence_aware_chunk(short)
        assert len(chunks) == 1
        assert chunks[0]["text"] == short

    def test_custom_params(self):
        chunks = sentence_aware_chunk(
            SAMPLE_FINANCIAL_TEXT, target_tokens=256, overlap_pct=0.10
        )
        assert len(chunks) >= 2

    def test_chunk_indices_sequential(self):
        chunks = sentence_aware_chunk(SAMPLE_FINANCIAL_TEXT)
        for i, c in enumerate(chunks):
            assert c["chunk_index"] == i


# ---------------------------------------------------------------------------
# section_aware_chunk tests
# ---------------------------------------------------------------------------


SAMPLE_STRUCTURED_TEXT = """## Mortgage Basics

A mortgage is a loan used to purchase real estate. Fixed-rate mortgages maintain the same interest rate for the entire loan term, typically 15 or 30 years. Adjustable-rate mortgages start with a lower rate that changes after an initial fixed period.

## Down Payment Requirements

Most conventional loans require a minimum down payment of 3 to 5 percent. FHA loans require as little as 3.5 percent. VA loans may offer zero-down financing for eligible veterans.

## Insurance Requirements

Private mortgage insurance is required when the down payment is less than 20 percent. PMI typically costs between 0.3 and 1.5 percent of the original loan amount per year. Once you reach 20 percent equity you can request PMI removal.

## Closing Costs

Closing costs typically range from 2 to 5 percent of the loan amount. They include origination fees, appraisal fees, title insurance, and prepaid taxes and insurance. Some sellers may agree to pay a portion of closing costs as a concession.
"""


class TestSectionAwareChunk:
    def test_sections_detected(self):
        chunks = section_aware_chunk(SAMPLE_STRUCTURED_TEXT)
        assert len(chunks) >= 4, f"Expected >=4 sections, got {len(chunks)}"

    def test_section_titles_preserved(self):
        chunks = section_aware_chunk(SAMPLE_STRUCTURED_TEXT)
        titles = {c.get("section_title", "") for c in chunks}
        assert "## Mortgage Basics" in titles
        assert "## Closing Costs" in titles

    def test_small_sections_not_split(self):
        chunks = section_aware_chunk(SAMPLE_STRUCTURED_TEXT)
        for c in chunks:
            if c.get("section_title") == "## Down Payment Requirements":
                assert c["section_chunk_index"] == 0

    def test_uses_128_token_default(self):
        chunks = section_aware_chunk(SAMPLE_STRUCTURED_TEXT)
        for c in chunks:
            assert c["token_count"] <= 200


# ---------------------------------------------------------------------------
# timestamp_chunk tests
# ---------------------------------------------------------------------------


def _make_segments(count: int = 30, duration: float = 5.0) -> list[dict]:
    """Create synthetic transcript segments spaced evenly."""
    return [
        {
            "text": f"Segment {i} about financial planning and investing strategies.",
            "start": i * duration,
            "duration": duration,
        }
        for i in range(count)
    ]


class TestTimestampChunk:
    def test_default_60_sec_windows(self):
        segs = _make_segments(60, duration=3.0)
        chunks = timestamp_chunk(segs)
        assert len(chunks) >= 3

    def test_60_sec_produces_more_than_75(self):
        segs = _make_segments(60, duration=3.0)
        small = timestamp_chunk(segs, window_sec=60.0)
        large = timestamp_chunk(segs, window_sec=75.0)
        assert len(small) >= len(large)

    def test_timestamps_present(self):
        segs = _make_segments(30)
        chunks = timestamp_chunk(segs)
        for c in chunks:
            assert "start_sec" in c
            assert "end_sec" in c
            assert c["end_sec"] > c["start_sec"]

    def test_empty_segments(self):
        assert timestamp_chunk([]) == []

    def test_overlap_between_windows(self):
        segs = _make_segments(30, duration=5.0)
        chunks = timestamp_chunk(segs, window_sec=60.0, overlap_sec=10.0)
        if len(chunks) >= 2:
            assert chunks[1]["start_sec"] < chunks[0]["end_sec"], (
                "Expected overlap: second chunk should start before first ends"
            )


# ---------------------------------------------------------------------------
# spreadsheet_chunk tests
# ---------------------------------------------------------------------------


class TestSpreadsheetChunk:
    def test_default_20_rows(self):
        headers = ["Date", "Amount", "Category"]
        rows = [[f"2026-01-{i:02d}", f"{i*100}", "expense"] for i in range(1, 51)]
        chunks = spreadsheet_chunk("Expenses", headers, rows)
        summary_chunks = [c for c in chunks if c["chunk_kind"] == "summary"]
        row_chunks = [c for c in chunks if c["chunk_kind"] == "rows"]
        assert len(summary_chunks) == 1
        assert len(row_chunks) == 3  # 50 rows / 20 per chunk = 3 (ceil)

    def test_max_rows_respected(self):
        headers = ["A", "B"]
        rows = [["x", "y"] for _ in range(45)]
        chunks = spreadsheet_chunk("Test", headers, rows, max_rows_per_chunk=15)
        row_chunks = [c for c in chunks if c["chunk_kind"] == "rows"]
        assert len(row_chunks) == 3  # 45/15 = 3


# ---------------------------------------------------------------------------
# chunk_prose (Chunk objects) tests
# ---------------------------------------------------------------------------


class TestChunkProse:
    def test_returns_chunk_objects(self):
        chunks = chunk_prose(SAMPLE_FINANCIAL_TEXT)
        assert all(isinstance(c, Chunk) for c in chunks)

    def test_total_chunks_set(self):
        chunks = chunk_prose(SAMPLE_FINANCIAL_TEXT)
        for c in chunks:
            assert c.total_chunks == len(chunks)

    def test_128_default(self):
        chunks = chunk_prose(SAMPLE_FINANCIAL_TEXT)
        assert len(chunks) > 3


# ---------------------------------------------------------------------------
# chunk_text router tests
# ---------------------------------------------------------------------------


class TestChunkTextRouter:
    def test_prose_routing(self):
        chunks = chunk_text(SAMPLE_FINANCIAL_TEXT, content_kind="doc_section")
        assert len(chunks) > 3
        assert all(isinstance(c, Chunk) for c in chunks)

    def test_market_snapshot_single_chunk(self):
        chunks = chunk_text("SPY: 550.25", content_kind="market_snapshot")
        assert len(chunks) == 1

    def test_custom_target_tokens(self):
        small = chunk_text(
            SAMPLE_FINANCIAL_TEXT,
            content_kind="doc_section",
            target_tokens=64,
        )
        large = chunk_text(
            SAMPLE_FINANCIAL_TEXT,
            content_kind="doc_section",
            target_tokens=256,
        )
        assert len(small) > len(large)
