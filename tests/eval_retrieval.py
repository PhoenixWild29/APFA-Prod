#!/usr/bin/env python3
"""APFA Retrieval Quality Evaluation Harness

Measures RAG retrieval quality in isolation (no LLM calls) using a
synthetic eval set of query-doc pairs with gold labels.

Metrics:
  - MRR@k: Mean Reciprocal Rank (position of first relevant result)
  - Recall@k: Fraction of expected docs found in top-k
  - NDCG@k: Normalized Discounted Cumulative Gain
  - Span containment: Does the retrieved chunk contain the gold answer span?

Supports two gold label granularities (CoWork S2):
  - source_doc: coarse recall (any chunk from the right document)
  - answer_span: precision (retrieved chunk contains the answer text)

Reports bootstrap 95% confidence intervals (CoWork S3).

Usage:
    # Local mode (direct FAISS access, no HTTP)
    python tests/eval_retrieval.py \\
        --eval-set tests/eval_results/retrieval_eval_set.json \\
        --mode local --k 5

    # Compare two runs
    python tests/eval_retrieval.py \\
        --compare tests/eval_results/retrieval_run_A.json \\
                  tests/eval_results/retrieval_run_B.json
"""

import argparse
import json
import math
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))


# ---------------------------------------------------------------------------
# Retrieval metrics
# ---------------------------------------------------------------------------

def mrr_at_k(retrieved_docs: list[str], relevant_docs: set[str], k: int = 5) -> float:
    for i, doc in enumerate(retrieved_docs[:k]):
        if doc in relevant_docs:
            return 1.0 / (i + 1)
    return 0.0


def recall_at_k(retrieved_docs: list[str], relevant_docs: set[str], k: int = 5) -> float:
    if not relevant_docs:
        return 0.0
    hits = sum(1 for doc in retrieved_docs[:k] if doc in relevant_docs)
    return hits / len(relevant_docs)


def ndcg_at_k(retrieved_docs: list[str], relevant_docs: set[str], k: int = 5) -> float:
    dcg = sum(
        1.0 / math.log2(i + 2)
        for i, doc in enumerate(retrieved_docs[:k])
        if doc in relevant_docs
    )
    ideal_dcg = sum(1.0 / math.log2(i + 2) for i in range(min(k, len(relevant_docs))))
    return dcg / ideal_dcg if ideal_dcg > 0 else 0.0


def span_containment(retrieved_texts: list[str], answer_span: str, k: int = 5) -> float:
    """Check if any top-k retrieved chunk contains the gold answer span."""
    if not answer_span:
        return 0.0
    span_lower = answer_span.lower()
    for text in retrieved_texts[:k]:
        if span_lower in text.lower():
            return 1.0
    return 0.0


def bootstrap_ci(values: list[float], n_bootstrap: int = 1000, ci: float = 0.95) -> tuple[float, float]:
    """Bootstrap confidence interval for the mean."""
    if len(values) < 2:
        mean = np.mean(values) if values else 0.0
        return (float(mean), float(mean))
    rng = np.random.default_rng(42)
    means = []
    arr = np.array(values)
    for _ in range(n_bootstrap):
        sample = rng.choice(arr, size=len(arr), replace=True)
        means.append(np.mean(sample))
    alpha = (1 - ci) / 2
    lo = float(np.percentile(means, alpha * 100))
    hi = float(np.percentile(means, (1 - alpha) * 100))
    return (round(lo, 4), round(hi, 4))


# ---------------------------------------------------------------------------
# Local retrieval engine (direct FAISS access, no HTTP)
# ---------------------------------------------------------------------------

class LocalRetriever:
    """Load FAISS index and embedder directly for fast offline eval."""

    def __init__(self):
        import faiss
        from fastembed import TextEmbedding
        from app.config import settings
        from app.main import load_rag_index

        self.settings = settings
        self.embedder = TextEmbedding(model_name=settings.embedder_model)

        print("Loading FAISS index...", end=" ", flush=True)
        self.rag_df, self.faiss_index = load_rag_index()
        print(f"OK ({len(self.rag_df)} vectors)")

    def search(self, query: str, k: int = 20) -> list[dict]:
        """Search FAISS and return top-k results with metadata."""
        import faiss

        query_emb = np.array(list(self.embedder.embed([query])), dtype=np.float32)
        if query_emb.ndim == 1:
            query_emb = query_emb.reshape(1, -1)
        faiss.normalize_L2(query_emb)

        distances, indices = self.faiss_index.search(query_emb, k=min(k, len(self.rag_df)))

        results = []
        for rank in range(len(indices[0])):
            idx = indices[0][rank]
            if idx < 0 or idx >= len(self.rag_df):
                continue
            row = self.rag_df.iloc[idx]
            results.append({
                "rank": rank,
                "score": float(distances[0][rank]),
                "filename": str(row.get("filename", "")),
                "source_connector": str(row.get("source_connector", "")),
                "chunk_id": str(row.get("chunk_id", "")),
                "text": str(row.get("profile", "")),
                "document_type": str(row.get("document_type", "")),
            })
        return results


# ---------------------------------------------------------------------------
# Evaluation runner
# ---------------------------------------------------------------------------

def run_eval(
    retriever: LocalRetriever,
    eval_set: dict,
    k: int = 5,
    fetch_k: int = 20,
) -> dict:
    """Run retrieval eval on all queries in the eval set."""
    queries = eval_set["queries"]
    per_query_results = []

    mrr_values = []
    recall_values = []
    ndcg_values = []
    span_values = []
    latencies = []
    category_metrics: dict[str, dict[str, list]] = {}

    for i, q in enumerate(queries):
        query_text = q["query"]
        expected_doc = q["expected_source_doc"]
        answer_span = q.get("answer_span", "")
        category = q.get("category", "unknown")

        start = time.perf_counter()
        results = retriever.search(query_text, k=fetch_k)
        latency_ms = (time.perf_counter() - start) * 1000

        retrieved_docs = [r["filename"] for r in results[:k]]
        retrieved_texts = [r["text"] for r in results[:k]]

        relevant = {expected_doc}
        q_mrr = mrr_at_k(retrieved_docs, relevant, k)
        q_recall = recall_at_k(retrieved_docs, relevant, k)
        q_ndcg = ndcg_at_k(retrieved_docs, relevant, k)
        q_span = span_containment(retrieved_texts, answer_span, k)

        mrr_values.append(q_mrr)
        recall_values.append(q_recall)
        ndcg_values.append(q_ndcg)
        span_values.append(q_span)
        latencies.append(latency_ms)

        cat_bucket = category_metrics.setdefault(category, {
            "mrr": [], "recall": [], "ndcg": [], "span": [],
        })
        cat_bucket["mrr"].append(q_mrr)
        cat_bucket["recall"].append(q_recall)
        cat_bucket["ndcg"].append(q_ndcg)
        cat_bucket["span"].append(q_span)

        status = "HIT" if q_recall > 0 else "MISS"
        span_status = "SPAN" if q_span > 0 else "no-span"
        print(
            f"  [{i+1}/{len(queries)}] {status} {span_status} "
            f"mrr={q_mrr:.2f} | {query_text[:60]}..."
        )

        per_query_results.append({
            "query": query_text,
            "expected_source_doc": expected_doc,
            "category": category,
            "difficulty": q.get("difficulty", "unknown"),
            "retrieved_docs": retrieved_docs,
            "mrr": round(q_mrr, 4),
            "recall": round(q_recall, 4),
            "ndcg": round(q_ndcg, 4),
            "span_containment": round(q_span, 4),
            "latency_ms": round(latency_ms, 1),
        })

    # Aggregate metrics with bootstrap CIs
    aggregate = {
        "mrr_at_k": round(float(np.mean(mrr_values)), 4),
        "mrr_ci_95": bootstrap_ci(mrr_values),
        "recall_at_k": round(float(np.mean(recall_values)), 4),
        "recall_ci_95": bootstrap_ci(recall_values),
        "ndcg_at_k": round(float(np.mean(ndcg_values)), 4),
        "ndcg_ci_95": bootstrap_ci(ndcg_values),
        "span_containment": round(float(np.mean(span_values)), 4),
        "span_ci_95": bootstrap_ci(span_values),
        "avg_latency_ms": round(float(np.mean(latencies)), 1),
        "total_queries": len(queries),
        "k": k,
    }

    by_category = {}
    for cat, vals in category_metrics.items():
        by_category[cat] = {
            "count": len(vals["mrr"]),
            "mrr_at_k": round(float(np.mean(vals["mrr"])), 4),
            "recall_at_k": round(float(np.mean(vals["recall"])), 4),
            "ndcg_at_k": round(float(np.mean(vals["ndcg"])), 4),
            "span_containment": round(float(np.mean(vals["span"])), 4),
        }

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config": {
            "embedder_model": retriever.settings.embedder_model,
            "chunk_target_tokens": retriever.settings.chunk_target_tokens,
            "vector_count": len(retriever.rag_df),
            "k": k,
            "fetch_k": fetch_k,
            "reranker": None,
        },
        "aggregate": aggregate,
        "by_category": by_category,
        "per_query": per_query_results,
    }


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------

def compare_runs(file_a: str, file_b: str):
    """Compare two eval run results side by side."""
    a = json.loads(Path(file_a).read_text())
    b = json.loads(Path(file_b).read_text())

    print(f"{'Metric':<25s} {'Run A':>10s} {'Run B':>10s} {'Delta':>10s}")
    print("-" * 58)

    for metric in ["mrr_at_k", "recall_at_k", "ndcg_at_k", "span_containment"]:
        va = a["aggregate"].get(metric, 0)
        vb = b["aggregate"].get(metric, 0)
        delta = vb - va
        sign = "+" if delta >= 0 else ""
        print(f"  {metric:<23s} {va:>10.4f} {vb:>10.4f} {sign}{delta:>9.4f}")

        ci_key = f"{metric.replace('_at_k', '_ci_95').replace('_containment', '_ci_95')}"
        if ci_key in a["aggregate"] and ci_key in b["aggregate"]:
            ci_a = a["aggregate"][ci_key]
            ci_b = b["aggregate"][ci_key]
            overlap = ci_a[1] >= ci_b[0] and ci_b[1] >= ci_a[0]
            print(f"    {'CI 95%':<21s} [{ci_a[0]:.4f}, {ci_a[1]:.4f}]  [{ci_b[0]:.4f}, {ci_b[1]:.4f}]  {'OVERLAP' if overlap else 'SEPARATED'}")

    print()
    print(f"  Config A: tokens={a['config'].get('chunk_target_tokens', '?')}, vectors={a['config'].get('vector_count', '?')}, reranker={a['config'].get('reranker', 'none')}")
    print(f"  Config B: tokens={b['config'].get('chunk_target_tokens', '?')}, vectors={b['config'].get('vector_count', '?')}, reranker={b['config'].get('reranker', 'none')}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="APFA Retrieval Evaluation Harness")
    parser.add_argument("--eval-set", default="tests/eval_results/retrieval_eval_set.json")
    parser.add_argument("--output-dir", default="tests/eval_results")
    parser.add_argument("--mode", choices=["local"], default="local")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--fetch-k", type=int, default=20,
                        help="How many candidates to fetch from FAISS before truncating to k")
    parser.add_argument("--compare", nargs=2, metavar=("RUN_A", "RUN_B"),
                        help="Compare two result files instead of running eval")
    args = parser.parse_args()

    if args.compare:
        compare_runs(args.compare[0], args.compare[1])
        return

    eval_path = Path(args.eval_set)
    if not eval_path.exists():
        print(f"ERROR: Eval set not found: {eval_path}")
        print("Run scripts/generate_retrieval_eval.py first.")
        sys.exit(1)

    eval_set = json.loads(eval_path.read_text())
    print(f"APFA Retrieval Evaluation")
    print(f"  Eval set: {eval_path} ({eval_set['total_queries']} queries)")
    print(f"  k={args.k}, fetch_k={args.fetch_k}")
    print()

    retriever = LocalRetriever()
    print()
    print("Running retrieval eval:")
    report = run_eval(retriever, eval_set, k=args.k, fetch_k=args.fetch_k)

    # Summary
    agg = report["aggregate"]
    print()
    print(f"{'='*60}")
    print(f"RESULTS (k={args.k}, {agg['total_queries']} queries)")
    print(f"  MRR@{args.k}:            {agg['mrr_at_k']:.4f}  CI95={agg['mrr_ci_95']}")
    print(f"  Recall@{args.k}:         {agg['recall_at_k']:.4f}  CI95={agg['recall_ci_95']}")
    print(f"  NDCG@{args.k}:           {agg['ndcg_at_k']:.4f}  CI95={agg['ndcg_ci_95']}")
    print(f"  Span containment: {agg['span_containment']:.4f}  CI95={agg['span_ci_95']}")
    print(f"  Avg latency:      {agg['avg_latency_ms']:.1f}ms")
    print()
    for cat, cat_data in report["by_category"].items():
        print(
            f"  {cat:20s}: n={cat_data['count']:2d}  "
            f"MRR={cat_data['mrr_at_k']:.3f}  "
            f"R@{args.k}={cat_data['recall_at_k']:.3f}  "
            f"NDCG={cat_data['ndcg_at_k']:.3f}  "
            f"span={cat_data['span_containment']:.3f}"
        )
    print(f"{'='*60}")

    # Save
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"retrieval_{timestamp}.json"
    output_file.write_text(json.dumps(report, indent=2, default=str))
    print(f"\nResults saved to {output_file}")


if __name__ == "__main__":
    main()
