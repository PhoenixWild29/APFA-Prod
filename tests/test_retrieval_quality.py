"""Deterministic retrieval quality gate for the committed seed corpus.

This test uses a small in-memory TF-IDF retriever so it can run in CI without
network access, credentials, or a production FAISS index. It imports the
shared retrieval metrics from eval_retrieval.py to keep gate measurements
consistent with the offline evaluation harness.
"""

import json
import math
import re
from collections import Counter
from pathlib import Path

import numpy as np

from eval_retrieval import (
    bootstrap_ci,
    mrr_at_k,
    ndcg_at_k,
    recall_at_k,
    span_containment,
)

PROJECT_ROOT = Path(__file__).parent.parent
EVAL_SET_PATH = PROJECT_ROOT / "tests" / "eval_results" / "retrieval_eval_set.json"
SEED_DOCS_DIR = PROJECT_ROOT / "tests" / "fixtures" / "retrieval_seeds"
K = 5
MIN_MRR_AT_5 = 0.70
MIN_RECALL_AT_5 = 0.80
MIN_NDCG_AT_5 = 0.70
MIN_SPAN_CONTAINMENT = 0.80


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class InMemoryTfidfRetriever:
    """A dependency-free cosine TF-IDF retriever for the committed seed corpus."""

    def __init__(self, documents: dict[str, str]):
        self.documents = documents
        tokenized_documents = {
            name: _tokenize(text) for name, text in sorted(documents.items())
        }
        document_frequency: Counter[str] = Counter()
        for tokens in tokenized_documents.values():
            document_frequency.update(set(tokens))

        document_count = len(tokenized_documents)
        self.idf = {
            token: math.log((1 + document_count) / (1 + frequency)) + 1
            for token, frequency in document_frequency.items()
        }
        self.vectors = {
            name: self._vectorize(tokens)
            for name, tokens in tokenized_documents.items()
        }

    def _vectorize(self, tokens: list[str]) -> dict[str, float]:
        if not tokens:
            return {}
        counts = Counter(tokens)
        total = len(tokens)
        return {
            token: (count / total) * self.idf[token]
            for token, count in counts.items()
            if token in self.idf
        }

    @staticmethod
    def _cosine(left: dict[str, float], right: dict[str, float]) -> float:
        if not left or not right:
            return 0.0
        dot_product = sum(
            weight * right.get(token, 0.0) for token, weight in left.items()
        )
        left_norm = math.sqrt(sum(weight * weight for weight in left.values()))
        right_norm = math.sqrt(sum(weight * weight for weight in right.values()))
        return (
            dot_product / (left_norm * right_norm) if left_norm and right_norm else 0.0
        )

    def search(self, query: str, k: int) -> list[dict[str, str | float]]:
        query_vector = self._vectorize(_tokenize(query))
        scored = [
            (self._cosine(query_vector, vector), name)
            for name, vector in self.vectors.items()
        ]
        scored.sort(key=lambda item: (-item[0], item[1]))
        return [
            {"filename": name, "text": self.documents[name], "score": score}
            for score, name in scored[:k]
        ]


def _load_seed_documents() -> dict[str, str]:
    return {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(SEED_DOCS_DIR.glob("*.md"))
    }


def test_retrieval_quality_gate():
    """Keep the seed-corpus retriever above conservative quality thresholds."""
    eval_set = json.loads(EVAL_SET_PATH.read_text(encoding="utf-8"))
    queries = eval_set["queries"]
    assert eval_set["total_queries"] == len(queries)
    assert len(queries) >= 10
    assert len({query["category"] for query in queries}) >= 3

    documents = _load_seed_documents()
    assert len(documents) >= K
    retriever = InMemoryTfidfRetriever(documents)

    mrr_values = []
    recall_values = []
    ndcg_values = []
    span_values = []
    for evaluation in queries:
        results = retriever.search(evaluation["query"], k=K)
        retrieved_docs = [str(result["filename"]) for result in results]
        retrieved_texts = [str(result["text"]) for result in results]
        relevant_docs = {evaluation["expected_source_doc"]}

        mrr_values.append(mrr_at_k(retrieved_docs, relevant_docs, k=K))
        recall_values.append(recall_at_k(retrieved_docs, relevant_docs, k=K))
        ndcg_values.append(ndcg_at_k(retrieved_docs, relevant_docs, k=K))
        span_values.append(
            span_containment(retrieved_texts, evaluation["answer_span"], k=K)
        )

    metrics = {
        "mrr_at_5": float(np.mean(mrr_values)),
        "recall_at_5": float(np.mean(recall_values)),
        "ndcg_at_5": float(np.mean(ndcg_values)),
        "span_containment": float(np.mean(span_values)),
    }
    mrr_ci = bootstrap_ci(mrr_values)
    recall_ci = bootstrap_ci(recall_values)
    ndcg_ci = bootstrap_ci(ndcg_values)
    span_ci = bootstrap_ci(span_values)
    report = (
        "Retrieval quality gate results: "
        f"MRR@5={metrics['mrr_at_5']:.3f} CI95={mrr_ci}; "
        f"Recall@5={metrics['recall_at_5']:.3f} CI95={recall_ci}; "
        f"NDCG@5={metrics['ndcg_at_5']:.3f} CI95={ndcg_ci}; "
        f"span={metrics['span_containment']:.3f} CI95={span_ci}"
    )

    assert metrics["mrr_at_5"] >= MIN_MRR_AT_5, report
    assert metrics["recall_at_5"] >= MIN_RECALL_AT_5, report
    assert metrics["ndcg_at_5"] >= MIN_NDCG_AT_5, report
    assert metrics["span_containment"] >= MIN_SPAN_CONTAINMENT, report
