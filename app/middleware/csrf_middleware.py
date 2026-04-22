"""
CSRF (Cross-Site Request Forgery) Protection Middleware

Layered protection model:
1. Safe methods (GET/HEAD/OPTIONS) bypass validation, set CSRF cookie
2. Path allowlist for pre-auth and token endpoints (login, register,
   refresh, revoke) and webhook endpoints (verified by signature elsewhere)
3. Header-auth bypass: requests with Bearer/X-API-Key and no session cookie
   are non-ambient — CORS preflight prevents cross-origin attacks from
   setting these headers, so CSRF is structurally impossible
4. Otherwise: double-submit cookie validation (cookie value must equal
   X-CSRF-Token header value)

Auth model (PR 1-3):
- Access tokens: in-memory only (Bearer header) — NOT ambient, no CSRF risk
- Refresh tokens: httpOnly cookie, path=/token, SameSite=Strict — ambient
  but scoped to /token/* which is in the exempt list, and further protected
  by Origin/Referer check in the endpoint itself

Combined with SameSite=Strict on the refresh cookie and Origin/Referer
validation, this provides defense-in-depth.
"""

import hashlib
import secrets
import time
from typing import Iterable, Optional

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

# The only ambient auth cookie is refresh_token (path=/token).
# Access tokens are in-memory Bearer headers — never cookies.
SESSION_COOKIE_NAMES = {"refresh_token"}

# Path prefixes that bypass CSRF entirely:
# - /token/*: refresh cookie is scoped here; protected by SameSite +
#   Origin/Referer check in the endpoint
# - Pre-auth: user has no session yet (register, password reset, verify)
# - Webhooks: external services authenticate via signature in the handler
DEFAULT_EXEMPT_PREFIXES = (
    "/token",           # /token, /token/oauth2, /token/refresh, /token/revoke
    "/register",        # /register, /register/resend, /register/verify
    "/password-reset",  # /password-reset/request, /password-reset/confirm
    "/verify",          # /verify-email, /verify/{token}
    "/generate-advice", # Bearer-only — Depends(get_current_user) validates JWT
    "/documents",       # Bearer-only — all document endpoints require JWT
    "/query",           # Bearer-only — query validation/preprocessing
    "/agents",          # Bearer-only — agent management
    "/admin",           # Bearer-only — require_admin dependency
    "/ingest",          # Bearer/API-key — pipeline auth
    "/users",           # Bearer-only — authenticated user endpoints
    "/logout",          # Bearer-only — session termination
    "/roles",           # Bearer-only — RBAC management
    "/permissions",     # Bearer-only — RBAC management
    "/retrieval",       # Bearer-only — SSE retrieval events
    "/metrics",         # Bearer-only or public — no ambient auth
    "/health",          # Public — no auth needed
    "/api/billing/webhook",  # Stripe — signature-verified in handler
    "/api/billing",     # Bearer-only — billing endpoints
    "/api/webhooks",    # future webhooks — convention: signature-verified
)


class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF protection using double-submit cookie pattern with bypass layers."""

    SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
    CSRF_COOKIE_NAME = "csrf_token"
    CSRF_HEADER_NAME = "X-CSRF-Token"
    TOKEN_LENGTH = 32

    def __init__(
        self,
        app,
        secret_key: str,
        exempt_prefixes: Optional[Iterable[str]] = None,
        cookie_secure: bool = True,
    ):
        super().__init__(app)
        self.secret_key = secret_key
        self.exempt_prefixes = tuple(exempt_prefixes) if exempt_prefixes else DEFAULT_EXEMPT_PREFIXES
        self.cookie_secure = cookie_secure

    def generate_csrf_token(self) -> str:
        """Generate a signed CSRF token: random.timestamp.signature."""
        random_token = secrets.token_urlsafe(self.TOKEN_LENGTH)
        timestamp = str(int(time.time()))
        token_data = f"{random_token}:{timestamp}"
        signature = hashlib.sha256(
            f"{token_data}:{self.secret_key}".encode()
        ).hexdigest()[:16]
        return f"{random_token}.{timestamp}.{signature}"

    def validate_csrf_token(self, cookie_token: str, header_token: str) -> bool:
        """Validate double-submit: cookie and header must match, signature must be valid."""
        if not cookie_token or not header_token:
            return False
        if cookie_token != header_token:
            return False
        try:
            parts = cookie_token.split(".")
            if len(parts) != 3:
                return False
            random_token, timestamp, signature = parts
            token_age = int(time.time()) - int(timestamp)
            if token_age > 86400:  # 24 hours
                return False
            token_data = f"{random_token}:{timestamp}"
            expected_signature = hashlib.sha256(
                f"{token_data}:{self.secret_key}".encode()
            ).hexdigest()[:16]
            return signature == expected_signature
        except (ValueError, IndexError):
            return False

    def _is_exempt_path(self, path: str) -> bool:
        """True if the path is in the CSRF exemption allowlist."""
        return any(path.startswith(prefix) for prefix in self.exempt_prefixes)

    def _has_header_auth(self, request: Request) -> bool:
        """True if the request authenticates via Bearer or API key (non-ambient)."""
        auth = request.headers.get("authorization", "").lower()
        return auth.startswith("bearer ") or "x-api-key" in request.headers

    def _has_session_cookie(self, request: Request) -> bool:
        """True if the request carries any known session cookie."""
        return any(name in request.cookies for name in SESSION_COOKIE_NAMES)

    async def dispatch(self, request: Request, call_next):
        # Layer 1: Safe methods bypass validation, set CSRF cookie if missing
        if request.method in self.SAFE_METHODS:
            response = await call_next(request)
            if self.CSRF_COOKIE_NAME not in request.cookies:
                csrf_token = self.generate_csrf_token()
                response.set_cookie(
                    key=self.CSRF_COOKIE_NAME,
                    value=csrf_token,
                    httponly=False,  # JS must read it for double-submit
                    secure=self.cookie_secure,
                    samesite="lax",
                    max_age=86400,
                )
            return response

        # Layer 2: Path allowlist — pre-auth and webhook endpoints
        if self._is_exempt_path(request.url.path):
            return await call_next(request)

        # Layer 3: Header-auth bypass — non-ambient credentials
        # Guard: only bypass when there's NO session cookie. If both Bearer
        # and cookie are present, the request is ambiguous and we enforce
        # CSRF to defend against a Bearer-padding attack.
        if self._has_header_auth(request) and not self._has_session_cookie(request):
            return await call_next(request)

        # Layer 4: Double-submit validation
        cookie_token = request.cookies.get(self.CSRF_COOKIE_NAME)
        header_token = request.headers.get(self.CSRF_HEADER_NAME)
        if not self.validate_csrf_token(cookie_token, header_token):
            raise HTTPException(status_code=403, detail="CSRF validation failed")

        return await call_next(request)
