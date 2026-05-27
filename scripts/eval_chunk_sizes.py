#!/usr/bin/env python3
"""Chunk size A/B test orchestrator for APFA retrieval.

Re-chunks the seed corpus at different token sizes, rebuilds FAISS indexes
in-process, and runs the retrieval eval to compare MRR@5/Recall@5/NDCG@5
across chunk sizes.

Works entirely in local mode — no HTTP calls, no production state changes.
Uses a temporary DeltaTable path to avoid touching the real corpus.

Usage:
    python scripts/eval_chunk_sizes.py \\
        --eval-set tests/eval_results/retrieval_eval_set.json \\
        --sizes 128 192 256 \\
        --output-dir tests/eval_results

Requires: fastembed, faiss-cpu, numpy, pandas, pyarrow
"""

import argparse
import json
import math
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))


def build_index_at_chunk_size(
    chunk_size: int,
    overlap_pct: float = 0.20,
) -> tuple:
    """Chunk seed docs at given size, embed, build FAISS index.

    Returns (rag_df, faiss_index, vector_count) using only seed data.
    """
    import faiss
    import pandas as pd
    from fastembed import TextEmbedding

    from app.config import settings
    from app.seed.rag_data import DOCUMENTS
    from app.services.chunking import sentence_aware_chunk, section_aware_chunk
    from app.services.pipeline_utils import approx_token_count

    embedder = TextEmbedding(model_name=settings.embedder_model)

    all_chunks = []
    for doc in DOCUMENTS:
        text = doc["profile"]
        filename = doc["filename"]
        doc_type = doc["document_type"]

        if doc_type == "regulation":
            chunks = section_aware_chunk(
                text, target_tokens=chunk_size, overlap_pct=overlap_pct
            )
        else:
            chunks = sentence_aware_chunk(
                text, target_tokens=chunk_size, overlap_pct=overlap_pct
            )

        for chunk in chunks:
            all_chunks.append({
                "profile": chunk["text"],
                "filename": filename,
                "document_type": doc_type,
                "source": doc["source"],
                "chunk_id": f"{filename}:{chunk['chunk_index']:04d}",
                "source_connector": "seed",
                "freshness_class": "static",
            })

    texts = [c["profile"] for c in all_chunks]
    embeddings = np.array(list(embedder.embed(texts)), dtype=np.float32)
    faiss.normalize_L2(embeddings)

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    df = pd.DataFrame(all_chunks)

    return df, index, len(all_chunks)


def run_retrieval_eval(
    rag_df,
    faiss_index,
    eval_set: dict,
    embedder,
    k: int = 5,
) -> dict:
    """Run retrieval eval against a given FAISS index."""
    import faiss as faiss_lib

    from tests.eval_retrieval import (
        bootstrap_ci,
        mrr_at_k,
        ndcg_at_k,
        recall_at_k,
        span_containment,
    )

    queries = eval_set["queries"]
    mrr_vals, recall_vals, ndcg_vals, span_vals = [], [], [], []

    for q in queries:
        query_emb = np.array(list(embedder.embed([q["query"]])), dtype=np.float32)
        if query_emb.ndim == 1:
            query_emb = query_emb.reshape(1, -1)
        faiss_lib.normalize_L2(query_emb)

        fetch_k = min(20, len(rag_df))
        distances, indices = faiss_index.search(query_emb, k=fetch_k)

        retrieved_docs = []
        retrieved_texts = []
        for rank in range(len(indices[0])):
            idx = indices[0][rank]
            if 0 <= idx < len(rag_df):
                row = rag_df.iloc[idx]
                retrieved_docs.append(str(row.get("filename", "")))
                retrieved_texts.append(str(row.get("profile", "")))

        relevant = {q["expected_source_doc"]}
        mrr_vals.append(mrr_at_k(retrieved_docs, relevant, k))
        recall_vals.append(recall_at_k(retrieved_docs, relevant, k))
        ndcg_vals.append(ndcg_at_k(retrieved_docs, relevant, k))
        span_vals.append(span_containment(retrieved_texts, q.get("answer_span", ""), k))

    return {
        "mrr_at_k": round(float(np.mean(mrr_vals)), 4),
        "mrr_ci_95": bootstrap_ci(mrr_vals),
        "recall_at_k": round(float(np.mean(recall_vals)), 4),
        "recall_ci_95": bootstrap_ci(recall_vals),
        "ndcg_at_k": round(float(np.mean(ndcg_vals)), 4),
        "ndcg_ci_95": bootstrap_ci(ndcg_vals),
        "span_containment": round(float(np.mean(span_vals)), 4),
        "span_ci_95": bootstrap_ci(span_vals),
    }


def main():
    parser = argparse.ArgumentParser(description="Chunk size A/B test for APFA retrieval")
    parser.add_argument("--eval-set", default="tests/eval_results/retrieval_eval_set.json")
    parser.add_argument("--sizes", nargs="+", type=int, default=[128, 192, 256])
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--output-dir", default="tests/eval_results")
    args = parser.parse_args()

    eval_path = Path(args.eval_set)
    if not eval_path.exists():
        print(f"ERROR: Eval set not found: {eval_path}")
        print("Run scripts/generate_retrieval_eval.py first.")
        sys.exit(1)

    eval_set = json.loads(eval_path.read_text())
    print(f"Chunk Size A/B Test")
    print(f"  Eval set: {eval_path} ({eval_set['total_queries']} queries)")
    print(f"  Chunk sizes: {args.sizes}")
    print(f"  k={args.k}")
    print()

    from fastembed import TextEmbedding
    from app.config import settings
    embedder = TextEmbedding(model_name=settings.embedder_model)

    comparison = []

    for size in args.sizes:
        print(f"--- Chunk size: {size} tokens ---")
        print("  Building index...", end=" ", flush=True)
        start = time.perf_counter()
        rag_df, faiss_index, vec_count = build_index_at_chunk_size(size)
        build_time = time.perf_counter() - start
        print(f"{vec_count} vectors in {build_time:.1f}s")

        print("  Running eval...", end=" ", flush=True)
        start = time.perf_counter()
        metrics = run_retrieval_eval(rag_df, faiss_index, eval_set, embedder, k=args.k)
        eval_time = time.perf_counter() - start
        print(f"done in {eval_time:.1f}s")

        result = {
            "chunk_size": size,
            "vector_count": vec_count,
            **metrics,
        }
        comparison.append(result)

        print(
            f"  MRR@{args.k}={metrics['mrr_at_k']:.4f} "
            f"R@{args.k}={metrics['recall_at_k']:.4f} "
            f"NDCG@{args.k}={metrics['ndcg_at_k']:.4f} "
            f"span={metrics['span_containment']:.4f}"
        )
        print()

    # Determine winner by MRR (primary), then Recall (tiebreak)
    best = max(comparison, key=lambda x: (x["mrr_at_k"], x["recall_at_k"]))

    # Check if winner's CIs separate from runner-up
    sorted_by_mrr = sorted(comparison, key=lambda x: x["mrr_at_k"], reverse=True)
    if len(sorted_by_mrr) >= 2:
        top = sorted_by_mrr[0]
        second = sorted_by_mrr[1]
        top_ci = top["mrr_ci_95"]
        second_ci = second["mrr_ci_95"]
        cis_separated = top_ci[0] > second_ci[1]
        confidence = "HIGH (CIs separated)" if cis_separated else "LOW (CIs overlap — difference may be noise)"
    else:
        confidence = "N/A (single size tested)"

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "eval_set": str(eval_path),
        "k": args.k,
        "comparison": comparison,
        "winner": {
            "chunk_size": best["chunk_size"],
            "mrr_at_k": best["mrr_at_k"],
            "recall_at_k": best["recall_at_k"],
            "confidence": confidence,
        },
    }

    # Print summary
    print(f"{'='*60}")
    print(f"COMPARISON (k={args.k})")
    print(f"{'Size':>6s} {'Vectors':>8s} {'MRR@k':>8s} {'R@k':>8s} {'NDCG@k':>8s} {'Span':>8s}")
    for r in comparison:
        marker = " <-- BEST" if r["chunk_size"] == best["chunk_size"] else ""
        print(
            f"{r['chunk_size']:>6d} {r['vector_count']:>8d} "
            f"{r['mrr_at_k']:>8.4f} {r['recall_at_k']:>8.4f} "
            f"{r['ndcg_at_k']:>8.4f} {r['span_containment']:>8.4f}{marker}"
        )
    print(f"\nWinner: {best['chunk_size']} tokens — {confidence}")
    print(f"{'='*60}")

    # Save
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"chunk_ab_{timestamp}.json"
    output_file.write_text(json.dumps(report, indent=2, default=str))
    print(f"\nResults saved to {output_file}")


if __name__ == "__main__":
    main()
