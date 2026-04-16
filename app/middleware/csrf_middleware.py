"""
CSRF (Cross-Site Request Forgery) Protection Middleware

Layered protection model:
1. Safe methods (GET/HEAD/OPTIONS) bypass validation, set CSRF cookie
2. Path allowlist for pre-auth endpoints (login, register, password reset,
   email verify) and webhook endpoints (verified by signature elsewhere)
3. Header-auth bypass: requests with Bearer/X-API-Key and no session cookie
   are non-ambient — CORS preflight prevents cross-origin attacks from
   setting these headers, so CSRF is structurally impossible
4. Otherwise: double-submit cookie validation (cookie value must equal
   X-CSRF-Token header value)

Combined with SameSite=Lax on cookies, this provides defense-in-depth
without breaking login or webhooks.
"""

import hashlib
import secrets
import time
from typing import Iterable, Optional

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

# Session cookie names — must match what /token/cookie endpoint sets.
# Drift here silently fails the header-auth bypass guard clause.
SESSION_COOKIE_NAMES = {"access_token", "refresh_token"}

# Path prefixes that bypass CSRF entirely:
# - Pre-auth: user has no session yet (login, register, password reset, verify)
# - Webhooks: external services authenticate via signature in the handler
DEFAULT_EXEMPT_PREFIXES = (
    "/token",           # /token, /token/oauth2, /token/cookie, /token/refresh
    "/register",        # /register, /register/resend, /register/verify
    "/password-reset",  # /password-reset/request, /password-reset/confirm
    "/verify",          # /verify-email, /verify/{token}
    "/api/billing/webhook",  # Stripe — signature-verified in handler
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
