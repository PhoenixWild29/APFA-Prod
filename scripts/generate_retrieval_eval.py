#!/usr/bin/env python3
"""Generate a synthetic retrieval evaluation set from APFA seed documents.

Uses GPT-4o to generate query-doc pairs with gold labels for measuring
retrieval quality (MRR@5, Recall@5, NDCG@5). Queries use colloquial
phrasing from a "user who hasn't read the doc" persona to avoid
lexical echo bias (CoWork S1).

Usage:
    python scripts/generate_retrieval_eval.py \
        --output tests/eval_results/retrieval_eval_set.json \
        --questions-per-doc 3 \
        --model gpt-4o

Requires: OPENAI_API_KEY env var.
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are generating evaluation queries for a financial research retrieval system.
Your job is to create realistic questions that a retail investor or first-time
homebuyer would ask — someone who has NOT read the source document and uses
everyday language, not regulatory jargon.

Rules:
- Use colloquial, natural phrasing (how a real person would type into a search box)
- Avoid copying vocabulary directly from the source text
- Each question should be answerable from the given document chunk
- Include an "answer_span" — the key sentence(s) from the document that answer the question
- Rate difficulty: "easy" if the answer is stated directly, "hard" if it requires inference
- Generate 1-2 hard negative descriptions: topics that sound similar but are answered
  by a DIFFERENT document (use the provided document list for context)
"""

USER_PROMPT_TEMPLATE = """\
Generate {n} retrieval evaluation queries for this financial document.

SOURCE DOCUMENT:
  Filename: {filename}
  Category: {document_type}
  Source: {source}
  Content:
{content}

OTHER DOCUMENTS IN THE CORPUS (for hard negative selection):
{other_docs}

Return a JSON array where each element has:
- "query": a natural question a user would ask (colloquial, no jargon copying)
- "answer_span": the key 1-2 sentences from the document that answer the question
- "difficulty": "easy" or "hard"
- "hard_negatives": list of 1-2 filenames from the corpus that are topically similar
  but DON'T answer this specific question

Return ONLY the JSON array, no other text.
"""


def load_seed_documents() -> list[dict]:
    """Load seed documents from rag_data.py."""
    from app.seed.rag_data import DOCUMENTS
    return DOCUMENTS


def generate_queries_for_doc(
    client,
    doc: dict,
    all_docs: list[dict],
    n: int,
    model: str,
) -> list[dict]:
    """Generate n synthetic queries for a single document using GPT-4o."""
    other_docs_summary = "\n".join(
        f"  - {d['filename']} ({d['document_type']}): {d['profile'][:100]}..."
        for d in all_docs
        if d["filename"] != doc["filename"]
    )

    prompt = USER_PROMPT_TEMPLATE.format(
        n=n,
        filename=doc["filename"],
        document_type=doc["document_type"],
        source=doc["source"],
        content=doc["profile"],
        other_docs=other_docs_summary,
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    parsed = json.loads(raw)

    if isinstance(parsed, dict) and "queries" in parsed:
        queries = parsed["queries"]
    elif isinstance(parsed, dict) and "items" in parsed:
        queries = parsed["items"]
    elif isinstance(parsed, list):
        queries = parsed
    else:
        queries = list(parsed.values())[0] if parsed else []

    results = []
    for q in queries[:n]:
        results.append({
            "query": q.get("query", ""),
            "expected_source_doc": doc["filename"],
            "expected_document_type": doc["document_type"],
            "answer_span": q.get("answer_span", ""),
            "category": doc["document_type"],
            "difficulty": q.get("difficulty", "easy"),
            "hard_negative_docs": q.get("hard_negatives", []),
        })

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic retrieval eval set from APFA seed docs"
    )
    parser.add_argument(
        "--output",
        default="tests/eval_results/retrieval_eval_set.json",
    )
    parser.add_argument("--questions-per-doc", type=int, default=3)
    parser.add_argument("--model", default="gpt-4o")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="Seconds between API calls to avoid rate limits")
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        print("ERROR: OPENAI_API_KEY env var required")
        sys.exit(1)

    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    docs = load_seed_documents()
    print(f"Loaded {len(docs)} seed documents")
    print(f"Generating {args.questions_per_doc} queries per doc = ~{len(docs) * args.questions_per_doc} total")
    print(f"Model: {args.model}")
    print()

    all_queries = []
    for i, doc in enumerate(docs):
        print(f"  [{i+1}/{len(docs)}] {doc['filename']}...", end=" ", flush=True)
        try:
            queries = generate_queries_for_doc(
                client, doc, docs, args.questions_per_doc, args.model
            )
            all_queries.extend(queries)
            print(f"{len(queries)} queries")
        except Exception as e:
            print(f"ERROR: {e}")

        if i < len(docs) - 1:
            time.sleep(args.delay)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    eval_set = {
        "version": "1.0",
        "generated_with": args.model,
        "total_queries": len(all_queries),
        "source_docs": len(docs),
        "questions_per_doc": args.questions_per_doc,
        "queries": all_queries,
    }

    output_path.write_text(json.dumps(eval_set, indent=2))
    print(f"\nGenerated {len(all_queries)} queries -> {output_path}")
    print("Review the output and fix any bad questions before committing.")


if __name__ == "__main__":
    main()
