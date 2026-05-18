"""Perplexity batch research connector.

Runs a configurable research agenda against the Perplexity API,
producing RAG-ready documents with source citations. Each answer
is chunked, embedded, and written to the DeltaTable for retrieval.

This connector extends RAGSource — it uses the same sync pipeline
(fetch → transform → ingest) as Google Drive and YouTube.

Content filter: rejects research results that are primarily about
non-investment topics (mortgages, tax advice, insurance) to maintain
the investment-focused positioning from Fix 4.

Dry-run mode: set PERPLEXITY_DRY_RUN=true in .env to log what would
be ingested without writing to the corpus. Use for the first 2-3 days
to verify output quality before enabling writes.

Rollback: all Perplexity chunks use external_id prefix 'perplexity:'.
To remove all Perplexity content from the corpus:
    from app.services.delta_writer import delete_by_source_url
    # Or query DeltaTable directly:
    # DELETE FROM rag WHERE external_id LIKE 'perplexity:%'
"""
import hashlib
import logging
import re
from datetime import datetime, timezone

from app.connectors.base import NormalizedRecord, RAGSource
from app.services.perplexity_client import PerplexityClient

logger = logging.getLogger(__name__)

# Content filter — reject results primarily about non-investment topics.
# Comprehensive list matching the leak detector from Fix 4 + eval harness.
# Applied at DOCUMENT level (not per-chunk) to catch distributed references.
_NON_INVESTMENT_PATTERN = re.compile(
    r"\b("
    # Mortgage/loan
    r"mortgage rate|FHA loan|loan officer|DTI ratio|down payment|closing cost"
    r"|home loan|TILA|RESPA|ECOA|loan product|30.year fixed"
    r"|refinanc.* (your|my) (mortgage|loan)"
    # Tax advice (not just mentioning taxes)
    r"|you should (claim|deduct|file)|tax deduction|Schedule [A-Z]|Form 1040"
    r"|itemize your|claim this deduction|tax bracket"
    # Insurance advice
    r"|you need .* insurance|insurance coverage|policy premium|deductible amount"
    r"|umbrella policy|term life"
    # Lending
    r"|apply for a loan|loan application|credit score.*(for|to get) a (loan|mortgage)"
    r")\b",
    re.IGNORECASE,
)


def _passes_content_filter(text: str) -> tuple[bool, list[str]]:
    """Check if content is investment-focused (should be ingested).

    Applied at DOCUMENT level before chunking — catches distributed
    non-investment references that individual chunks might miss.

    Returns (passes, list_of_matched_patterns) for audit logging.
    """
    hits = _NON_INVESTMENT_PATTERN.findall(text)
    # Allow up to 2 incidental mentions. Reject if 3+ = primary topic.
    return len(hits) < 3, hits


class PerplexityResearchConnector(RAGSource):
    """Connector that runs a research agenda via the Perplexity API.

    Activation:
        1. Set PERPLEXITY_API_KEY in .env
        2. Set PERPLEXITY_DRY_RUN=false (default is true)
        3. Restart celery-worker + celery-beat
        4. Daily 5AM UTC schedule runs automatically

    Manual trigger:
        celery -A app.tasks call run_perplexity_research

    Rollback:
        All chunks have external_id starting with 'perplexity:'.
        Query DeltaTable to find and remove them.
    """

    source_type = "perplexity_research"
    INGEST_BATCH_SIZE = 20  # research results are small, larger batches OK

    def __init__(self, api_key: str, model: str = "sonar-pro", dry_run: bool = False):
        self._client = PerplexityClient(api_key=api_key, model=model)
        self._dry_run = dry_run

    def fetch(
        self,
        agenda: list[dict] | None = None,
        **kwargs,
    ) -> list[dict]:
        """Execute each research question and return raw results.

        Each question is independent — if one fails, the others continue.
        """
        from app.connectors.research_agenda import (
            DEFAULT_RESEARCH_AGENDA,
            RESEARCH_SYSTEM_PROMPT,
        )

        agenda = agenda or DEFAULT_RESEARCH_AGENDA
        results = []
        total_tokens = 0
        errors = 0

        for i, topic in enumerate(agenda):
            query = topic["query"]
            system_prompt = topic.get("system_prompt", RESEARCH_SYSTEM_PROMPT)

            try:
                logger.info(f"Perplexity research [{i+1}/{len(agenda)}]: {query[:60]}...")
                result = self._client.research(
                    query=query,
                    system_prompt=system_prompt,
                )

                tokens_used = result["tokens"]["prompt"] + result["tokens"]["completion"]
                total_tokens += tokens_used

                results.append({
                    "query": query,
                    "content": result["content"],
                    "citations": result["citations"],
                    "category": topic.get("category", "general"),
                    "freshness_class": topic.get("freshness_class", "daily"),
                    "ttl_hours": topic.get("ttl_hours", 48),
                    "latency_ms": result["latency_ms"],
                    "tokens": tokens_used,
                })

                logger.info(
                    f"  → {len(result['content'])} chars, "
                    f"{len(result['citations'])} citations, "
                    f"{result['latency_ms']}ms, {tokens_used} tokens"
                )

            except Exception as e:
                errors += 1
                logger.error(f"Perplexity research failed for '{query[:50]}': {e}")

        # Per-run summary log (operational visibility)
        logger.info(
            f"perplexity_run_summary: "
            f"questions_attempted={len(agenda)}, "
            f"questions_succeeded={len(results)}, "
            f"questions_failed={errors}, "
            f"total_tokens={total_tokens}"
        )

        return results

    def transform(self, raw_docs: list[dict]) -> list[NormalizedRecord]:
        """Convert research results to NormalizedRecords.

        Content filter is applied at DOCUMENT level (before chunking)
        to catch distributed non-investment references. Rejected content
        is logged for audit/quarantine.
        """
        from app.services.chunking import chunk_prose

        records = []
        now_iso = datetime.now(timezone.utc).isoformat()
        filtered_count = 0
        total_chunks = 0

        for doc in raw_docs:
            # Content filter at document level
            passes, filter_hits = _passes_content_filter(doc["content"])
            if not passes:
                filtered_count += 1
                logger.warning(
                    f"perplexity_filter_rejected: query='{doc['query'][:50]}' "
                    f"hits={filter_hits[:5]} "
                    f"content_preview='{doc['content'][:100]}...'"
                )
                continue

            # Log filter near-misses for monitoring
            if filter_hits:
                logger.info(
                    f"perplexity_filter_passed_with_hits: query='{doc['query'][:50]}' "
                    f"hits={filter_hits} (below threshold)"
                )

            # Chunk the research brief
            chunks = chunk_prose(doc["content"])

            # Deterministic external_id: hash of query + date
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            query_hash = hashlib.sha256(doc["query"].encode()).hexdigest()[:12]

            for chunk in chunks:
                chunk_text = chunk.text if hasattr(chunk, "text") else str(chunk)
                chunk_idx = chunk.chunk_index if hasattr(chunk, "chunk_index") else 0

                # Store citation URLs at chunk level for provenance
                citation_urls = doc.get("citations", [])

                import json as _json
                records.append(NormalizedRecord(
                    external_id=f"perplexity:{query_hash}:{date_str}:{chunk_idx}",
                    source_type="perplexity_research",
                    source_url=citation_urls[0] if citation_urls else "",
                    title=doc["query"],
                    author="perplexity",
                    published_at=now_iso,
                    fetched_at=now_iso,
                    freshness_class=doc["freshness_class"],
                    content_kind="research_brief",
                    text=chunk_text,
                    ttl_hours=doc.get("ttl_hours", 48),
                    metadata_json=_json.dumps({
                        "query": doc["query"],
                        "citations": citation_urls,
                        "category": doc["category"],
                        "source": "perplexity_api",
                    }),
                ))
                total_chunks += 1

        # Transform summary
        logger.info(
            f"perplexity_transform_summary: "
            f"docs_processed={len(raw_docs)}, "
            f"docs_filtered={filtered_count}, "
            f"chunks_produced={total_chunks}"
        )

        return records

    def sync(self, embedder, settings, redis_client=None, **kwargs) -> dict:
        """Override sync to support dry-run mode.

        In dry-run mode: fetches and transforms but doesn't write to
        DeltaTable. Logs what would have been ingested for verification.
        """
        if self._dry_run:
            logger.info("PERPLEXITY DRY RUN — fetching and transforming only, NOT writing to corpus")

            raw_docs = self.fetch(**kwargs)
            records = self.transform(raw_docs)

            logger.info(
                f"perplexity_dry_run_summary: "
                f"would_ingest={len(records)} chunks from {len(raw_docs)} questions. "
                f"Set PERPLEXITY_DRY_RUN=false to enable writes."
            )

            # Log a preview of what would be ingested
            for r in records[:3]:
                logger.info(
                    f"  dry_run_preview: id={r.external_id} "
                    f"title='{r.title[:50]}' "
                    f"text='{r.text[:100]}...' "
                    f"ttl={r.ttl_hours}h"
                )

            return {"inserted": 0, "skipped": 0, "errors": 0, "dry_run": True,
                    "would_ingest": len(records)}

        # Normal mode — delegate to base class batched sync
        return super().sync(embedder=embedder, settings=settings,
                           redis_client=redis_client, **kwargs)
