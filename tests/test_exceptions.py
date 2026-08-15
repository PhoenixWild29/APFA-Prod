"""Unit tests for app/exceptions.py and the structured-exception wiring in main.

Covers:
- the exception class hierarchy and ToolExecutionError metadata
- retrieve_context raising RAGIndexUnavailableError / RAGRetrievalError
- the LLM-safe tool wrappers converting exceptions back to strings
- retriever_agent degrading gracefully (confidence 0.0) on RAG errors
- the /agents/retriever/test endpoint mapping RAG errors to HTTP 503/500
"""

import asyncio
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

import app.main as main
from app.exceptions import (
    APFAError,
    ExternalServiceError,
    LLMError,
    RAGError,
    RAGIndexUnavailableError,
    RAGRetrievalError,
    ToolExecutionError,
)
from app.schemas.agent_testing import RetrieverTestRequest


# --------------------------------------------------------------------------- #
# Hierarchy / attributes
# --------------------------------------------------------------------------- #

def test_rag_subclasses_are_rag_and_apfa_errors():
    assert issubclass(RAGIndexUnavailableError, RAGError)
    assert issubclass(RAGRetrievalError, RAGError)
    assert issubclass(RAGError, APFAError)
    assert issubclass(RAGIndexUnavailableError, APFAError)


def test_tool_execution_is_external_and_apfa_error():
    assert issubclass(ToolExecutionError, ExternalServiceError)
    assert issubclass(ExternalServiceError, APFAError)
    assert issubclass(ToolExecutionError, APFAError)


def test_llm_error_is_apfa_error():
    assert issubclass(LLMError, APFAError)


def test_except_rag_error_catches_new_subclasses():
    """Existing `except RAGError` handlers must keep catching the new subclasses."""
    with pytest.raises(RAGError):
        raise RAGIndexUnavailableError("no data")
    with pytest.raises(RAGError):
        raise RAGRetrievalError("boom")


def test_except_external_service_error_catches_tool_execution():
    with pytest.raises(ExternalServiceError):
        raise ToolExecutionError("get_market_quote", "Error retrieving quote for AAPL.")


def test_tool_execution_error_carries_metadata():
    original = ValueError("db down")
    err = ToolExecutionError(
        "get_market_quote", "Error retrieving quote for AAPL.", original
    )
    assert err.tool_name == "get_market_quote"
    assert err.detail == "Error retrieving quote for AAPL."
    assert err.original_error is original
    assert str(err) == "get_market_quote: Error retrieving quote for AAPL."


def test_tool_execution_error_original_defaults_to_none():
    err = ToolExecutionError("get_rate_trend", "Error retrieving trend for DGS10.")
    assert err.original_error is None


# --------------------------------------------------------------------------- #
# retrieve_context behavior
# --------------------------------------------------------------------------- #

def test_retrieve_context_raises_index_unavailable(monkeypatch):
    monkeypatch.setattr(main, "faiss_index", None, raising=False)
    monkeypatch.setattr(main, "rag_df", None, raising=False)
    with pytest.raises(RAGIndexUnavailableError):
        main.retrieve_context("what are current treasury yields")


def test_retrieve_context_raises_retrieval_error(monkeypatch):
    """Index present but the embedder fails at runtime -> RAGRetrievalError."""
    monkeypatch.setattr(main, "faiss_index", object(), raising=False)
    monkeypatch.setattr(main, "rag_df", [1], raising=False)
    bad_embedder = Mock()
    bad_embedder.embed.side_effect = RuntimeError("embedding failed")
    monkeypatch.setattr(main, "embedder", bad_embedder, raising=False)
    with pytest.raises(RAGRetrievalError):
        main.retrieve_context("what are current treasury yields")


# --------------------------------------------------------------------------- #
# tool functions + LLM-safe wrappers
# --------------------------------------------------------------------------- #

def test_get_market_quote_raises_tool_execution_error(monkeypatch):
    monkeypatch.setattr(main, "SessionLocal", Mock(side_effect=RuntimeError("db down")))
    with pytest.raises(ToolExecutionError) as ei:
        main.get_market_quote("AAPL")
    assert ei.value.tool_name == "get_market_quote"
    assert "AAPL" in ei.value.detail


def test_safe_get_market_quote_returns_detail_string(monkeypatch):
    monkeypatch.setattr(main, "SessionLocal", Mock(side_effect=RuntimeError("db down")))
    result = main._safe_get_market_quote("AAPL")
    assert isinstance(result, str)
    assert result == "Error retrieving quote for AAPL."


def test_safe_get_rate_trend_returns_detail_string(monkeypatch):
    monkeypatch.setattr(main, "SessionLocal", Mock(side_effect=RuntimeError("db down")))
    result = main._safe_get_rate_trend("DGS10")
    assert isinstance(result, str)
    assert result == "Error retrieving trend for DGS10."


def test_retrieve_context_text_only_returns_string_on_index_unavailable(monkeypatch):
    def _raise(_q):
        raise RAGIndexUnavailableError("no data")

    monkeypatch.setattr(main, "retrieve_context", _raise)
    result = main._retrieve_context_text_only("query text here")
    assert result == "RAG index not available — no data has been ingested yet."


# --------------------------------------------------------------------------- #
# retriever_agent graph node degradation
# --------------------------------------------------------------------------- #

def test_retriever_agent_degrades_on_index_unavailable(monkeypatch):
    def _raise(_q):
        raise RAGIndexUnavailableError("no data")

    monkeypatch.setattr(main, "retrieve_context", _raise)
    state = main.retriever_agent({"query": "what are current treasury yields"})
    assert state["retrieval_confidence"] == 0.0
    assert state["sources"] == []


def test_retriever_agent_degrades_on_retrieval_error(monkeypatch):
    def _raise(_q):
        raise RAGRetrievalError("boom")

    monkeypatch.setattr(main, "retrieve_context", _raise)
    state = main.retriever_agent({"query": "what are current treasury yields"})
    assert state["retrieval_confidence"] == 0.0
    assert state["sources"] == []


# --------------------------------------------------------------------------- #
# /agents/retriever/test endpoint error mapping. The coroutine is awaited
# directly (no TestClient) so auth/CSRF middleware can't interfere; the
# endpoint raises HTTPException, which is what we assert on.
# --------------------------------------------------------------------------- #

def test_retriever_test_endpoint_returns_503_when_index_unavailable(monkeypatch):
    def _raise(_q):
        raise RAGIndexUnavailableError("no data")

    monkeypatch.setattr(main, "retrieve_context", _raise)
    req = RetrieverTestRequest(query_text="what are current treasury yields")
    with pytest.raises(HTTPException) as ei:
        asyncio.run(main.test_retriever_agent(req))
    assert ei.value.status_code == 503


def test_retriever_test_endpoint_returns_500_on_retrieval_error(monkeypatch):
    def _raise(_q):
        raise RAGRetrievalError("boom")

    monkeypatch.setattr(main, "retrieve_context", _raise)
    req = RetrieverTestRequest(query_text="what are current treasury yields")
    with pytest.raises(HTTPException) as ei:
        asyncio.run(main.test_retriever_agent(req))
    assert ei.value.status_code == 500
