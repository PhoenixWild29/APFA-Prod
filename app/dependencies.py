"""
FastAPI dependency injection functions

Provides reusable dependencies for authentication, authorization,
and request validation.
"""
from fastapi import Request, HTTPException, Depends, Cookie
from typing import Optional
from jose import JWTError, jwt
from app.config import settings
import logging

logger = logging.getLogger(__name__)


async def get_current_user_from_cookie(
    access_token: Optional[str] = Cookie(None, alias="access_token")
):
    """
    Get current user from httpOnly cookie token.
    
    This dependency extracts the JWT token from httpOnly cookies
    instead of the Authorization header, providing enhanced security.
    
    Args:
        access_token: JWT token from httpOnly cookie
    
    Returns:
        User dict if authenticated
    
    Raises:
        HTTPException: 401 if token is invalid or missing
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not access_token:
        raise credentials_exception
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            access_token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    
    except JWTError as e:
        logger.error(f"JWT validation error: {e}")
        raise credentials_exception
    
    # Import here to avoid circular imports
    from app.main import get_user
    
    user = get_user(username=username)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_user_from_header(
    authorization: Optional[str] = None
):
    """
    Get current user from Authorization header (legacy support).
    
    Args:
        authorization: Bearer token from Authorization header
    
    Returns:
        User dict if authenticated
    
    Raises:
        HTTPException: 401 if token is invalid or missing
    """
    from app.main import oauth2_scheme, get_current_user
    
    # Use existing header-based authentication
    return await get_current_user(authorization)


async def get_current_user_hybrid(
    request: Request,
    cookie_token: Optional[str] = Cookie(None, alias="access_token"),
    header_auth: Optional[str] = None
):
    """
    Hybrid authentication: Try cookie first, fall back to header.
    
    Supports both httpOnly cookie (preferred) and Authorization header
    (for backward compatibility and API clients).
    
    Args:
        request: FastAPI request object
        cookie_token: Token from httpOnly cookie
        header_auth: Token from Authorization header
    
    Returns:
        User dict if authenticated
    
    Raises:
        HTTPException: 401 if authentication fails
    """
    # Try cookie first (preferred)
    if cookie_token:
        try:
            return await get_current_user_from_cookie(cookie_token)
        except HTTPException:
            pass  # Fall through to header
    
    # Fall back to Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        from app.main import get_current_user
        return await get_current_user(token)
    
    # No valid authentication
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
                detail=f"Insufficient permissions. Required role: {required_role}"
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
                detail=f"Permission denied. Required: {required_permission}"
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
        raise HTTPException(
            status_code=403,
            detail="Administrator access required"
        )
    return user

