"""Tests for the detect_bias stub function.

These tests lock in two invariants:
1. detect_bias returns a float (not a coroutine) — prevents async/sync
   mismatch regression (Fix 2c).
2. detect_bias is NOT a coroutine function — calling it from the
   synchronous LangGraph agent nodes must work without await.

When a real bias detection implementation replaces the stub, update
the expected return value but keep the iscoroutinefunction assertion
unless the entire agent graph is converted to async (see Fix Plan v4).
"""
import inspect


def test_detect_bias_returns_float():
    from app.main import detect_bias

    result = detect_bias("any query text about financial markets")
    assert isinstance(result, float), f"Expected float, got {type(result).__name__}"
    assert result == 0.0, f"Stub should return 0.0, got {result}"


def test_detect_bias_is_not_coroutine_function():
    from app.main import detect_bias

    assert not inspect.iscoroutinefunction(detect_bias), (
        "detect_bias must be synchronous (def, not async def). "
        "The LangGraph agent graph calls it from sync nodes without await. "
        "If you need async bias detection, convert the entire graph to async first."
    )


def test_detect_bias_handles_empty_string():
    from app.main import detect_bias

    result = detect_bias("")
    assert isinstance(result, float)
    # Value may change with real implementation — only type matters here


def test_detect_bias_handles_long_text():
    from app.main import detect_bias

    long_text = "investment portfolio diversification strategy " * 500
    result = detect_bias(long_text)
    assert isinstance(result, float)
    # Value may change with real implementation — only type matters here
