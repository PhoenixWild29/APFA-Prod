"""Shared utilities for the APFA data pipeline.

Provides rate limiting, approximate token counting, retry/backoff,
and state persistence — used across all connectors.

Adapted from Perplexity reference pipeline with APFA integration.
"""

import functools
import hashlib
import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


# ---------------------------------------------------------------------------
# Token counting (approximate — no tiktoken dependency)
# ---------------------------------------------------------------------------

def approx_token_count(text: str) -> int:
    """Fast approximation: ~4 chars per token (GPT-family heuristic).

    Good enough for chunk window sizing; avoids a tiktoken dependency.
    """
    return max(1, len(text) // 4)


# ---------------------------------------------------------------------------
# Retry / backoff decorator
# ---------------------------------------------------------------------------

def retry(
    max_attempts: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:
    """Exponential-backoff retry decorator.

    Usage::
        @retry(max_attempts=4, exceptions=(requests.HTTPError, TimeoutError))
        def call_api(): ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = base_delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    if attempt == max_attempts:
                        logger.error(
                            "Function %s failed after %d attempts: %s",
                            func.__name__,
                            max_attempts,
                            exc,
                        )
                        raise
                    logger.warning(
                        "Attempt %d/%d for %s failed (%s). Retrying in %.1fs…",
                        attempt,
                        max_attempts,
                        func.__name__,
                        exc,
                        delay,
                    )
                    time.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)

        return wrapper  # type: ignore[return-value]

    return decorator


# ---------------------------------------------------------------------------
# Rate limiter (token-bucket style)
# ---------------------------------------------------------------------------


class RateLimiter:
    """Simple token-bucket rate limiter for API call throttling.

    Example::
        limiter = RateLimiter(calls_per_second=30)
        for item in items:
            limiter.wait()
            api_call(item)
    """

    def __init__(self, calls_per_second: float) -> None:
        self.min_interval = 1.0 / calls_per_second
        self._last_call: float = 0.0

    def wait(self) -> None:
        """Block until the minimum interval since the last call has elapsed."""
        elapsed = time.monotonic() - self._last_call
        to_wait = self.min_interval - elapsed
        if to_wait > 0:
            time.sleep(to_wait)
        self._last_call = time.monotonic()


# ---------------------------------------------------------------------------
# ISO-8601 helpers
# ---------------------------------------------------------------------------

def now_utc_iso() -> str:
    """Return current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(s: str) -> datetime | None:
    """Parse an ISO-8601 string to a timezone-aware UTC datetime."""
    if not s:
        return None
    try:
        s_clean = s.replace("Z", "+00:00")
        return datetime.fromisoformat(s_clean).astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Content hashing
# ---------------------------------------------------------------------------

def sha256_text(text: str) -> str:
    """SHA-256 hex digest of UTF-8 encoded text."""
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


# ---------------------------------------------------------------------------
# Incremental state persistence
# ---------------------------------------------------------------------------

def load_state(state_path: str | Path) -> dict[str, Any]:
    """Load a JSON state file, returning {} if missing or corrupt."""
    p = Path(state_path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("State file %s is corrupt — starting fresh.", p)
        return {}


def save_state(state: dict[str, Any], state_path: str | Path) -> None:
    """Persist state to a JSON file atomically (write-then-rename)."""
    p = Path(state_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    tmp.replace(p)


# ---------------------------------------------------------------------------
# Stance detection (bullish / bearish / neutral)
# ---------------------------------------------------------------------------

_BULLISH_SIGNALS = re.compile(
    r"\b(bull(?:ish)?|upside|rally|breakout|buy|outperform|overweight|"
    r"uptrend|all[- ]time\s+high|ath|growth|surge|soar|skyrocket|"
    r"strong\s+buy|accumulate|upgrade)\b",
    re.IGNORECASE,
)
_BEARISH_SIGNALS = re.compile(
    r"\b(bear(?:ish)?|downside|sell[-\s]off|breakdown|sell|underperform|"
    r"underweight|downtrend|crash|collapse|plunge|decline|drop|dump|"
    r"strong\s+sell|distribution|downgrade|recession|stagflat)\b",
    re.IGNORECASE,
)


def detect_stance(text: str) -> str:
    """Classify the financial stance of a text chunk.

    Returns "bullish", "bearish", "neutral", or "mixed".
    """
    bull_count = len(_BULLISH_SIGNALS.findall(text))
    bear_count = len(_BEARISH_SIGNALS.findall(text))

    if bull_count == 0 and bear_count == 0:
        return "neutral"
    if bull_count > bear_count * 1.5:
        return "bullish"
    if bear_count > bull_count * 1.5:
        return "bearish"
    return "mixed"
