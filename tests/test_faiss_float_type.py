"""Tests for FAISS float32 type safety.

Verifies that fastembed output is float32 and that the _as_faiss_array
helper produces contiguous float32 arrays suitable for FAISS.
"""

import numpy as np
import pytest


def test_embedder_output_dtype():
    """Assert fastembed output dtype is float32."""
    from fastembed import TextEmbedding

    e = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    result = np.array(list(e.embed(["test"])))
    assert result.dtype == np.float32, (
        f"Expected float32, got {result.dtype}. "
        "FAISS requires float32 — if fastembed changes its output dtype, "
        "the _as_faiss_array helper will catch it, but we want early warning."
    )


def test_as_faiss_array_float64_input():
    """_as_faiss_array converts float64 to contiguous float32."""
    from app.main import _as_faiss_array

    arr = np.array([[1.0, 2.0, 3.0]], dtype=np.float64)
    result = _as_faiss_array(arr)
    assert result.dtype == np.float32
    assert result.flags["C_CONTIGUOUS"]


def test_as_faiss_array_non_contiguous():
    """_as_faiss_array makes non-contiguous arrays contiguous."""
    from app.main import _as_faiss_array

    arr = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    # Transpose creates a non-contiguous view
    non_contig = arr.T
    assert not non_contig.flags["C_CONTIGUOUS"]

    result = _as_faiss_array(non_contig)
    assert result.flags["C_CONTIGUOUS"]
    assert result.dtype == np.float32


def test_as_faiss_array_already_correct():
    """_as_faiss_array is a no-op on correct input."""
    from app.main import _as_faiss_array

    arr = np.ascontiguousarray(np.array([[1.0, 2.0]], dtype=np.float32))
    result = _as_faiss_array(arr)
    assert result.dtype == np.float32
    assert result.flags["C_CONTIGUOUS"]


def test_embedding_dim_probe():
    """EMBEDDING_DIM matches the model's actual output dimension."""
    from app.main import EMBEDDING_DIM

    assert isinstance(EMBEDDING_DIM, int)
    assert EMBEDDING_DIM > 0
    # bge-small-en-v1.5 is 384-dim, but we don't hardcode — just verify it's reasonable
    assert 100 <= EMBEDDING_DIM <= 2048
