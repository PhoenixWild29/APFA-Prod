"""Cross-encoder reranker for RAG retrieval pipeline.

Uses fastembed TextCrossEncoder (ONNX backend) to re-score query-document
pairs. Raw logits are sigmoid-normalized to [0, 1] for compatibility with
the freshness decay multiplier (0.2-1.0).

B1 (CoWork): cross-encoder logits are unbounded — sigmoid normalization
is mandatory before freshness multiplication.
"""
from __future__ import annotations

import logging
import math
import threading
from typing import Optional

logger = logging.getLogger(__name__)

_instance: Optional[RerankerService] = None
_lock = threading.Lock()


def get_reranker(model_name: str, cache_dir: str | None = None) -> RerankerService:
    global _instance
    if _instance is not None and _instance.model_name == model_name:
        return _instance
    with _lock:
        if _instance is not None and _instance.model_name == model_name:
            return _instance
        _instance = RerankerService(model_name, cache_dir=cache_dir)
        return _instance


def sigmoid(x: float) -> float:
    """Numerically stable sigmoid: 1 / (1 + exp(-x))."""
    x = max(-500.0, min(500.0, x))
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    exp_x = math.exp(x)
    return exp_x / (1.0 + exp_x)


class RerankerService:
    def __init__(self, model_name: str = "BAAI/bge-reranker-base", cache_dir: str | None = None):
        self.model_name = model_name
        self._cache_dir = cache_dir
        self._encoder = None
        self._init_lock = threading.Lock()
        logger.info("RerankerService created (model=%s, not yet loaded)", model_name)

    def _ensure_loaded(self):
        if self._encoder is not None:
            return
        with self._init_lock:
            if self._encoder is not None:
                return
            from fastembed import TextCrossEncoder

            kwargs = {"model_name": self.model_name}
            if self._cache_dir:
                kwargs["cache_dir"] = self._cache_dir
            logger.info("Loading cross-encoder model: %s", self.model_name)
            self._encoder = TextCrossEncoder(**kwargs)
            logger.info("Cross-encoder model loaded: %s", self.model_name)

    def warmup(self):
        """Pre-load the model so the first real query doesn't pay init cost."""
        self._ensure_loaded()
        logger.info("Reranker warmup complete")

    def rerank(
        self,
        query: str,
        documents: list[str],
        doc_indices: list[int],
        top_n: int = 20,
    ) -> list[tuple[int, float]]:
        """Re-rank documents by cross-encoder relevance.

        Args:
            query: Search query.
            documents: Document texts (parallel with doc_indices).
            doc_indices: Original corpus index for each document — the
                caller's canonical ID. Returned as-is in results so the
                caller never needs to re-derive the mapping (B1 fix).
            top_n: How many top results to return.

        Returns:
            List of (doc_index, sigmoid_score) sorted descending.
            doc_index values come directly from the doc_indices arg.
            Returns [] on error — caller falls back to FAISS-only.
        """
        if not documents:
            return []

        if len(documents) != len(doc_indices):
            logger.error(
                "rerank: documents (%d) and doc_indices (%d) length mismatch",
                len(documents), len(doc_indices),
            )
            return []

        try:
            self._ensure_loaded()
            raw_scores = list(self._encoder.rerank(query, documents))

            scored = []
            for i, raw in enumerate(raw_scores):
                if isinstance(raw, dict):
                    logit = float(raw.get("score", raw.get("relevance_score", 0.0)))
                else:
                    logit = float(raw)
                scored.append((doc_indices[i], sigmoid(logit), logit))

            scored.sort(key=lambda x: x[1], reverse=True)
            top = scored[:top_n]

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    "Reranker scores for '%s': %s",
                    query[:50],
                    ", ".join(
                        f"doc{idx}(logit={lg:.2f}->sig={ns:.3f})"
                        for idx, ns, lg in top[:10]
                    ),
                )

            return [(idx, score) for idx, score, _ in top]

        except Exception as e:
            logger.error("Reranker failed (falling back to FAISS-only): %s", e)
            return []
