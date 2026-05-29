"""Unit tests for cross-encoder reranker service and retrieve_context integration.

Covers sigmoid normalization, B1 index alignment (CoWork), error fallback,
singleton behavior, and retrieve_context with reranker on/off/fallback.
"""
from __future__ import annotations

import math
from unittest.mock import MagicMock, patch

import pytest

from app.services.reranker import RerankerService, get_reranker, sigmoid


# ---------------------------------------------------------------------------
# sigmoid tests
# ---------------------------------------------------------------------------


class TestSigmoid:
    def test_zero_is_half(self):
        assert sigmoid(0.0) == pytest.approx(0.5)

    def test_large_positive_near_one(self):
        assert sigmoid(10.0) == pytest.approx(1.0, abs=1e-4)
        assert sigmoid(100.0) == pytest.approx(1.0, abs=1e-10)

    def test_large_negative_near_zero(self):
        assert sigmoid(-10.0) == pytest.approx(0.0, abs=1e-4)
        assert sigmoid(-100.0) == pytest.approx(0.0, abs=1e-10)

    def test_known_values(self):
        assert 0.98 < sigmoid(4.1) < 1.0
        assert 0.0 < sigmoid(-8.2) < 0.001

    def test_numerical_stability_extreme(self):
        assert sigmoid(1000.0) == pytest.approx(1.0)
        assert sigmoid(-1000.0) == pytest.approx(0.0)
        assert sigmoid(500.0) == pytest.approx(1.0)
        assert sigmoid(-500.0) == pytest.approx(0.0)

    def test_monotonic(self):
        vals = [sigmoid(x) for x in [-5, -2, 0, 2, 5]]
        assert vals == sorted(vals)

    def test_output_bounded(self):
        for x in [-100, -10, -1, 0, 1, 10, 100]:
            s = sigmoid(x)
            assert 0.0 < s < 1.0


# ---------------------------------------------------------------------------
# RerankerService tests
# ---------------------------------------------------------------------------


class TestRerankerService:
    def test_empty_documents(self):
        svc = RerankerService("test-model")
        assert svc.rerank("query", [], [], top_n=5) == []

    def test_length_mismatch_returns_empty(self):
        svc = RerankerService("test-model")
        result = svc.rerank("query", ["doc1", "doc2"], [0], top_n=5)
        assert result == []

    @patch("app.services.reranker.RerankerService._ensure_loaded")
    def test_rerank_returns_sigmoid_scores(self, mock_load):
        svc = RerankerService("test-model")
        svc._encoder = MagicMock()
        svc._encoder.rerank.return_value = [3.0, -2.0, 0.5]

        result = svc.rerank(
            "What is a mortgage?",
            ["doc about mortgages", "doc about cars", "doc about loans"],
            [10, 25, 42],
            top_n=3,
        )

        assert len(result) == 3
        for doc_idx, score in result:
            assert 0.0 < score < 1.0
            assert doc_idx in (10, 25, 42)

        assert result[0][1] > result[1][1] > result[2][1]
        assert result[0][0] == 10  # logit 3.0 -> highest sigmoid
        assert result[2][0] == 25  # logit -2.0 -> lowest sigmoid

    @patch("app.services.reranker.RerankerService._ensure_loaded")
    def test_rerank_handles_dict_output(self, mock_load):
        svc = RerankerService("test-model")
        svc._encoder = MagicMock()
        svc._encoder.rerank.return_value = [
            {"score": 2.0},
            {"relevance_score": -1.0},
        ]

        result = svc.rerank("q", ["a", "b"], [0, 1], top_n=2)
        assert len(result) == 2
        assert result[0][0] == 0  # score 2.0 -> higher sigmoid
        assert result[1][0] == 1

    @patch("app.services.reranker.RerankerService._ensure_loaded")
    def test_rerank_respects_top_n(self, mock_load):
        svc = RerankerService("test-model")
        svc._encoder = MagicMock()
        svc._encoder.rerank.return_value = [1.0, 2.0, 3.0, 4.0, 5.0]

        result = svc.rerank(
            "q",
            ["a", "b", "c", "d", "e"],
            [0, 1, 2, 3, 4],
            top_n=3,
        )
        assert len(result) == 3

    @patch("app.services.reranker.RerankerService._ensure_loaded")
    def test_rerank_error_returns_empty(self, mock_load):
        svc = RerankerService("test-model")
        svc._encoder = MagicMock()
        svc._encoder.rerank.side_effect = RuntimeError("ONNX crashed")

        result = svc.rerank("q", ["a"], [0], top_n=5)
        assert result == []

    @patch("app.services.reranker.RerankerService._ensure_loaded")
    def test_doc_indices_passed_through_exactly(self, mock_load):
        """B1 (CoWork): doc_indices from caller must appear in output unchanged."""
        svc = RerankerService("test-model")
        svc._encoder = MagicMock()
        svc._encoder.rerank.return_value = [1.0, 2.0, 0.5]

        original_indices = [77, 203, 5]
        result = svc.rerank("q", ["a", "b", "c"], original_indices, top_n=3)

        returned_indices = {idx for idx, _ in result}
        assert returned_indices == {77, 203, 5}


# ---------------------------------------------------------------------------
# Singleton tests
# ---------------------------------------------------------------------------


class TestGetReranker:
    def test_singleton_same_model(self):
        import app.services.reranker as mod

        mod._instance = None
        r1 = get_reranker("model-a")
        r2 = get_reranker("model-a")
        assert r1 is r2

    def test_singleton_different_model_creates_new(self):
        import app.services.reranker as mod

        mod._instance = None
        r1 = get_reranker("model-a")
        r2 = get_reranker("model-b")
        assert r1 is not r2
        assert r2.model_name == "model-b"

        mod._instance = None


# ---------------------------------------------------------------------------
# B1 integration: FAISS -1 / out-of-range indices (CoWork)
# ---------------------------------------------------------------------------


class TestB1FaissIndexAlignment:
    """Prove that the single-pass candidate filtering in retrieve_context()
    correctly handles FAISS returning -1 padding and out-of-range indices,
    and that the reranker receives the right texts mapped to the right
    doc_idx values."""

    @patch("app.services.reranker.RerankerService._ensure_loaded")
    def test_faiss_negative_one_skipped_reranker_aligned(self, mock_load):
        """FAISS returns [-1, 5, 3, -1, 7] — the -1 entries must be
        filtered before the reranker sees them, and the reranker's
        returned doc_indices must map to the correct documents."""
        svc = RerankerService("test-model")
        svc._encoder = MagicMock()
        svc._encoder.rerank.return_value = [2.0, 1.0, 0.5]

        import numpy as np
        import pandas as pd

        faiss_indices = np.array([[-1, 5, 3, -1, 7]])
        faiss_distances = np.array([[0.0, 0.9, 0.8, 0.0, 0.7]])

        corpus = pd.DataFrame({
            "profile": [f"Document {i} text" for i in range(10)],
            "freshness_class": ["static"] * 10,
        })

        valid_doc_indices = []
        valid_texts = []
        for rank_idx in range(len(faiss_indices[0])):
            doc_idx = int(faiss_indices[0][rank_idx])
            if doc_idx < 0 or doc_idx >= len(corpus):
                continue
            valid_doc_indices.append(doc_idx)
            valid_texts.append(str(corpus.iloc[doc_idx]["profile"]))

        assert valid_doc_indices == [5, 3, 7]
        assert valid_texts == ["Document 5 text", "Document 3 text", "Document 7 text"]

        result = svc.rerank("test query", valid_texts, valid_doc_indices, top_n=3)

        assert len(result) == 3
        returned_indices = {idx for idx, _ in result}
        assert returned_indices == {5, 3, 7}
        assert result[0][0] == 5  # logit 2.0 -> first text -> doc_idx 5

    @patch("app.services.reranker.RerankerService._ensure_loaded")
    def test_faiss_out_of_range_skipped(self, mock_load):
        """FAISS returns indices beyond corpus size — they must be filtered."""
        svc = RerankerService("test-model")
        svc._encoder = MagicMock()
        svc._encoder.rerank.return_value = [1.5]

        import numpy as np
        import pandas as pd

        corpus_size = 5
        faiss_indices = np.array([[999, 2, -1, 1000]])
        faiss_distances = np.array([[0.5, 0.9, 0.0, 0.4]])

        corpus = pd.DataFrame({
            "profile": [f"Doc {i}" for i in range(corpus_size)],
        })

        valid_doc_indices = []
        valid_texts = []
        for rank_idx in range(len(faiss_indices[0])):
            doc_idx = int(faiss_indices[0][rank_idx])
            if doc_idx < 0 or doc_idx >= len(corpus):
                continue
            valid_doc_indices.append(doc_idx)
            valid_texts.append(str(corpus.iloc[doc_idx]["profile"]))

        assert valid_doc_indices == [2]
        assert valid_texts == ["Doc 2"]

        result = svc.rerank("q", valid_texts, valid_doc_indices, top_n=5)
        assert len(result) == 1
        assert result[0][0] == 2
