"""
FastAPI dependency injection functions

Provides reusable dependencies for authentication, authorization,
and request validation.

Auth paths:
- Human users: Authorization: Bearer <jwt> (access token in header only)
- Pipeline keys: Authorization: Bearer apfa_pipe_<token>
  Resolved via api_keys table → user row (type="service", role="pipeline")
- require_pipeline_or_admin: accepts either path for connector endpoints
- Refresh tokens: httpOnly cookie, scoped to /token/* (handled in main.py)
"""

import logging
import secrets
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request
from jose import JWTError, jwt

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pipeline API key prefix
# ---------------------------------------------------------------------------
PIPELINE_KEY_PREFIX = "apfa_pipe_"


async def get_current_user_hybrid(request: Request):
    """Authenticate the current user from the Authorization: Bearer header.

    Access tokens are in-memory only (never cookies). Refresh tokens are
    httpOnly cookies scoped to /token/* — they never reach general endpoints.

    Used by: require_role, require_permission, require_admin.
    """
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        from app.main import get_current_user

        return await get_current_user(token)

    raise HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_role(required_role: str):
    """
    Dependency to require specific user role.

    Args:
        required_role: Required role ('standard', 'advisor', 'admin')

    Returns:
        Dependency function that validates user role
    """

    async def role_checker(user: dict = Depends(get_current_user_hybrid)):
        user_role = user.get("role", "standard")

        # Role hierarchy: admin > advisor > standard
        role_hierarchy = {"admin": 3, "advisor": 2, "standard": 1}

        if role_hierarchy.get(user_role, 0) < role_hierarchy.get(required_role, 0):
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required role: {required_role}",
            )

        return user

    return role_checker


def require_permission(required_permission: str):
    """
    Dependency to require specific permission.

    Args:
        required_permission: Required permission string (e.g., 'admin:celery:manage')

    Returns:
        Dependency function that validates user permission
    """

    async def permission_checker(user: dict = Depends(get_current_user_hybrid)):
        user_permissions = user.get("permissions", [])

        if required_permission not in user_permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied. Required: {required_permission}",
            )

        return user

    return permission_checker


async def require_admin(user: dict = Depends(get_current_user_hybrid)):
    """
    Dependency to require admin role

    Returns:
        User dict if admin

    Raises:
        HTTPException: 403 if not admin
    """
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Administrator access required")
    return user


# ---------------------------------------------------------------------------
# Pipeline rate limiter (separate bucket from user traffic)
# ---------------------------------------------------------------------------

class _PipelineRateLimiter:
    """Token-bucket rate limiter for pipeline API keys.

    300 req/min per key (5 req/sec steady state).
    Burst: 60 tokens, refill 5/sec.
    Separate from user rate limiter — pipeline traffic can't starve users.
    """

    def __init__(self, burst: int = 60, refill_rate: float = 5.0):
        self._burst = burst
        self._refill_rate = refill_rate
        self._buckets: dict[int, tuple[float, float]] = {}  # key_id → (tokens, last_refill)

    def check(self, key_id: int) -> tuple[bool, dict]:
        """Return (allowed, headers). Headers include Retry-After on 429."""
        now = time.monotonic()
        tokens, last_refill = self._buckets.get(key_id, (float(self._burst), now))

        # Refill tokens
        elapsed = now - last_refill
        tokens = min(self._burst, tokens + elapsed * self._refill_rate)

        if tokens < 1.0:
            retry_after = (1.0 - tokens) / self._refill_rate
            return False, {"Retry-After": str(int(retry_after) + 1)}

        tokens -= 1.0
        self._buckets[key_id] = (tokens, now)
        return True, {}


pipeline_rate_limiter = _PipelineRateLimiter(
    burst=settings.pipeline_rate_limit_burst,
    refill_rate=settings.pipeline_rate_limit_refill,
)


# ---------------------------------------------------------------------------
# Pipeline key authentication
# ---------------------------------------------------------------------------

def _verify_pipeline_key(raw_key: str) -> tuple[dict, int]:
    """Verify an apfa_pipe_ key against the api_keys table.

    Returns (user_dict, key_id) or raises HTTPException.
    Uses secrets.compare_digest for constant-time comparison against
    bcrypt hash. NEVER logs the raw key value — only key_id.
    """
    import bcrypt as _bcrypt
    from app.database import SessionLocal
    from app.orm_models import ApiKey, User

    db = SessionLocal()
    try:
        # Scan active (non-revoked, non-expired) keys
        now = datetime.now(timezone.utc)
        active_keys = (
            db.query(ApiKey)
            .filter(ApiKey.revoked_at.is_(None))
            .filter(
                (ApiKey.expires_at.is_(None)) | (ApiKey.expires_at > now)
            )
            .all()
        )

        matched_key = None
        for api_key in active_keys:
            # bcrypt.checkpw is already constant-time
            if _bcrypt.checkpw(
                raw_key.encode("utf-8"),
                api_key.key_hash.encode("utf-8"),
            ):
                matched_key = api_key
                break

        if matched_key is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired pipeline key",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Update last_used_at
        matched_key.last_used_at = now
        db.commit()

        # Resolve the user
        user = db.query(User).filter(User.id == matched_key.user_id).first()
        if user is None or user.disabled:
            raise HTTPException(status_code=401, detail="Service account disabled")

        user_dict = user.to_dict()
        key_id = matched_key.id

        # Log key_id only — NEVER the raw key
        logger.info(f"Pipeline auth: key_id={key_id} user={user.username}")

        return user_dict, key_id

    finally:
        db.close()


async def require_pipeline_or_admin(request: Request):
    """Dual-path auth for pipeline connector endpoints.

    Path 1: Authorization: Bearer apfa_pipe_* → api_keys table lookup
    Path 2: Authorization: Bearer <jwt> → existing admin flow

    Sets request.state.auth_source ("pipeline" | "admin") and
    request.state.key_id (int | None) for audit logging.

    Enforces pipeline rate limiting on path 1.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        # No Bearer token — try header-based admin auth
        try:
            user = await get_current_user_hybrid(request)
            if user.get("role") != "admin":
                raise HTTPException(status_code=403, detail="Admin access required")
            request.state.auth_source = "admin"
            request.state.key_id = None
            return user
        except HTTPException:
            raise HTTPException(
                status_code=401,
                detail="Authorization required",
                headers={"WWW-Authenticate": "Bearer"},
            )

    token = auth_header[7:]  # strip "Bearer "

    # Path 1: Pipeline key (apfa_pipe_ prefix)
    if token.startswith(PIPELINE_KEY_PREFIX):
        user_dict, key_id = _verify_pipeline_key(token)

        # Enforce pipeline rate limit (separate bucket)
        allowed, headers = pipeline_rate_limiter.check(key_id)
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Pipeline rate limit exceeded",
                headers=headers,
            )

        request.state.auth_source = "pipeline"
        request.state.key_id = key_id
        return user_dict

    # Path 2: JWT (admin)
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    from app.main import get_user
    user = get_user(username=username)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    request.state.auth_source = "admin"
    request.state.key_id = None
    return user
