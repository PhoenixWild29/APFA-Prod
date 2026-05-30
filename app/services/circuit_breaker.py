"""Circuit breaker for external API calls.

Prevents cascading failures when third-party services (Finnhub, Google,
Perplexity) are down. Wraps the retry-decorated public method — NOT the
inner _call() — so an open circuit short-circuits before any retry/backoff
and a fully-exhausted retry counts as exactly one breaker failure.

States:
    CLOSED  → normal operation; failures increment counter
    OPEN    → all calls fail immediately with CircuitBreakerOpen
    HALF_OPEN → one probe call allowed; success → CLOSED, failure → OPEN

Per-process state (not shared across Celery workers). Each FastAPI and
Celery worker process maintains its own breaker instances. The /health
endpoint only reports FastAPI-process breaker state. With N Celery
workers, the API can be hit up to N * failure_threshold times before
all workers trip.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Callable

logger = logging.getLogger(__name__)


class CircuitBreakerOpen(Exception):
    """Raised when a circuit breaker is open and calls are rejected."""

    def __init__(self, name: str, recovery_seconds: float):
        self.name = name
        self.recovery_seconds = recovery_seconds
        super().__init__(
            f"Circuit breaker '{name}' is OPEN — "
            f"retry after {recovery_seconds:.0f}s"
        )


class CircuitBreaker:
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        on_state_change: Callable[[str, str, str], Any] | None = None,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._on_state_change = on_state_change

        self._state = self.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float = 0.0
        self._lock = threading.Lock()

    @property
    def state(self) -> str:
        with self._lock:
            if self._state == self.OPEN:
                if time.monotonic() - self._last_failure_time >= self.recovery_timeout:
                    self._transition(self.HALF_OPEN)
            return self._state

    def call(self, fn: Callable, *args: Any, **kwargs: Any) -> Any:
        with self._lock:
            if self._state == self.OPEN:
                if time.monotonic() - self._last_failure_time >= self.recovery_timeout:
                    self._transition(self.HALF_OPEN)
                else:
                    raise CircuitBreakerOpen(self.name, self.recovery_timeout)

            if self._state == self.HALF_OPEN:
                pass  # allow the probe call through

        try:
            result = fn(*args, **kwargs)
        except Exception:
            self._record_failure()
            raise

        self._record_success()
        return result

    def _record_failure(self) -> None:
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()

            if self._state == self.HALF_OPEN:
                self._transition(self.OPEN)
            elif (
                self._state == self.CLOSED
                and self._failure_count >= self.failure_threshold
            ):
                self._transition(self.OPEN)

    def _record_success(self) -> None:
        with self._lock:
            self._success_count += 1
            if self._state == self.HALF_OPEN:
                self._failure_count = 0
                self._transition(self.CLOSED)

    def _transition(self, new_state: str) -> None:
        old_state = self._state
        self._state = new_state
        logger.warning(
            "Circuit breaker '%s': %s → %s (failures=%d)",
            self.name, old_state, new_state, self._failure_count,
        )
        if self._on_state_change:
            try:
                self._on_state_change(self.name, old_state, new_state)
            except Exception:
                logger.debug("on_state_change callback failed", exc_info=True)

    def reset(self) -> None:
        with self._lock:
            self._failure_count = 0
            self._state = self.CLOSED

    def stats(self) -> dict[str, Any]:
        with self._lock:
            return {
                "state": self._state,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "failure_threshold": self.failure_threshold,
                "recovery_timeout": self.recovery_timeout,
            }


# ---------------------------------------------------------------------------
# Module-level registry
# ---------------------------------------------------------------------------

_breakers: dict[str, CircuitBreaker] = {}
_registry_lock = threading.Lock()


def get_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    on_state_change: Callable[[str, str, str], Any] | None = None,
) -> CircuitBreaker:
    """Get or create a named circuit breaker."""
    with _registry_lock:
        if name not in _breakers:
            _breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                on_state_change=on_state_change,
            )
        return _breakers[name]


def get_all_breaker_states() -> dict[str, dict]:
    """Return all breaker states for the health endpoint."""
    with _registry_lock:
        return {name: breaker.stats() for name, breaker in _breakers.items()}
