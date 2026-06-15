"""Structured exceptions for APFA application errors.

This module is intentionally dependency-free (it imports nothing from ``app``)
so it can be imported anywhere without risking a circular import.

Hierarchy::

    APFAError
    ├── RAGError
    │   ├── RAGIndexUnavailableError   (no data ingested yet — expected state)
    │   └── RAGRetrievalError          (runtime failure: FAISS/embedding/etc.)
    ├── LLMError
    └── ExternalServiceError
        └── ToolExecutionError         (a LangChain tool function failed)

Because ``RAGIndexUnavailableError`` and ``RAGRetrievalError`` subclass
``RAGError`` (and ``ToolExecutionError`` subclasses ``ExternalServiceError``),
existing ``except RAGError`` / ``except ExternalServiceError`` handlers keep
catching the new subclasses unchanged.
"""

from __future__ import annotations


class APFAError(Exception):
    """Base exception for all APFA application errors."""


class RAGError(APFAError):
    """Raised when RAG index operations fail."""


class RAGIndexUnavailableError(RAGError):
    """Raised when the FAISS index or rag_df is None (no data has been ingested)."""


class RAGRetrievalError(RAGError):
    """Raised when RAG retrieval fails at runtime (FAISS search, embedding, etc.)."""


class LLMError(APFAError):
    """Raised when LLM operations fail."""


class ExternalServiceError(APFAError):
    """Raised when external service calls fail."""


class ToolExecutionError(ExternalServiceError):
    """Raised when a LangChain tool function fails (market quote, indicator, trend).

    Carries structured metadata so callers can log or surface an informative,
    LLM-safe message:

    - ``tool_name``: the tool that failed (e.g. ``"get_market_quote"``)
    - ``detail``: a human/LLM-readable message (the string the tool used to return)
    - ``original_error``: the underlying exception, if any
    """

    def __init__(
        self,
        tool_name: str,
        detail: str,
        original_error: Exception | None = None,
    ):
        self.tool_name = tool_name
        self.detail = detail
        self.original_error = original_error
        super().__init__(f"{tool_name}: {detail}")
