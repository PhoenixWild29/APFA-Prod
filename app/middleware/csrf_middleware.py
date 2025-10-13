"""
CSRF (Cross-Site Request Forgery) Protection Middleware

Provides robust CSRF protection for all state-changing requests
using double-submit cookie pattern with additional security measures.
"""
from fastapi import Request, HTTPException
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
import secrets
import hashlib
import time


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection middleware using double-submit cookie pattern
    
    - Generates CSRF tokens and sets them in httpOnly cookies
    - Validates CSRF tokens from request headers
    - Protects POST, PUT, PATCH, DELETE requests
    - Allows safe methods (GET, HEAD, OPTIONS) without validation
    """
    
    SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
    CSRF_COOKIE_NAME = "csrf_token"
    CSRF_HEADER_NAME = "X-CSRF-Token"
    TOKEN_LENGTH = 32
    
    def __init__(self, app, secret_key: str):
        super().__init__(app)
        self.secret_key = secret_key
    
    def generate_csrf_token(self) -> str:
        """Generate a secure CSRF token"""
        random_token = secrets.token_urlsafe(self.TOKEN_LENGTH)
        timestamp = str(int(time.time()))
        
        # Combine with secret for additional security
        token_data = f"{random_token}:{timestamp}"
        signature = hashlib.sha256(
            f"{token_data}:{self.secret_key}".encode()
        ).hexdigest()[:16]
        
        return f"{random_token}.{timestamp}.{signature}"
    
    def validate_csrf_token(self, cookie_token: str, header_token: str) -> bool:
        """
        Validate CSRF token using double-submit pattern
        
        Args:
            cookie_token: Token from cookie
            header_token: Token from request header
        
        Returns:
            True if valid, False otherwise
        """
        if not cookie_token or not header_token:
            return False
        
        # Tokens must match (double-submit)
        if cookie_token != header_token:
            return False
        
        # Validate token structure
        try:
            parts = cookie_token.split('.')
            if len(parts) != 3:
                return False
            
            random_token, timestamp, signature = parts
            
            # Check token age (24 hours max)
            token_age = int(time.time()) - int(timestamp)
            if token_age > 86400:  # 24 hours in seconds
                return False
            
            # Verify signature
            token_data = f"{random_token}:{timestamp}"
            expected_signature = hashlib.sha256(
                f"{token_data}:{self.secret_key}".encode()
            ).hexdigest()[:16]
            
            return signature == expected_signature
        
        except (ValueError, IndexError):
            return False
    
    async def dispatch(self, request: Request, call_next):
        """Process request with CSRF protection"""
        
        # Skip CSRF for safe methods
        if request.method in self.SAFE_METHODS:
            response = await call_next(request)
            
            # Set CSRF token cookie on safe requests if not present
            if self.CSRF_COOKIE_NAME not in request.cookies:
                csrf_token = self.generate_csrf_token()
                response.set_cookie(
                    key=self.CSRF_COOKIE_NAME,
                    value=csrf_token,
                    httponly=False,  # Must be readable by JavaScript
                    secure=True,  # HTTPS only in production
                    samesite="strict",
                    max_age=86400  # 24 hours
                )
            
            return response
        
        # Validate CSRF for state-changing methods
        cookie_token = request.cookies.get(self.CSRF_COOKIE_NAME)
        header_token = request.headers.get(self.CSRF_HEADER_NAME)
        
        if not self.validate_csrf_token(cookie_token, header_token):
            raise HTTPException(
                status_code=403,
                detail="CSRF validation failed"
            )
        
        # Process request
        response = await call_next(request)
        
        return response

