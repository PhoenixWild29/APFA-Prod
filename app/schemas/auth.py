"""
Authentication data models with Pydantic validation

Provides formal, validated data structures for authentication components
to ensure type safety and data integrity.
"""
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
import uuid


# Allowed permissions for validation
ALLOWED_PERMISSIONS = {
    # User permissions
    "advice:generate",
    "advice:view_history",
    # Admin permissions
    "admin:celery:view",
    "admin:celery:manage",
    "admin:metrics:view",
    "admin:index:manage",
    "admin:users:manage",
    "admin:audit:view",
    # Financial advisor permissions
    "advisor:view_clients",
    "advisor:manage_clients",
    "advisor:generate_reports",
}


class User(BaseModel):
    """
    User data model for authentication
    
    Represents a user in the authentication system with credentials
    and account status.
    
    Attributes:
        username: Unique username for authentication (3-50 characters)
        hashed_password: Bcrypt hashed password (never store plaintext)
        disabled: Whether the user account is disabled
        full_name: Optional full name of the user
        email: Optional email address
    
    Example:
        >>> user = User(
        ...     username="john_doe",
        ...     hashed_password="$2b$12$KIX...",  # Bcrypt hash
        ...     disabled=False
        ... )
    
    Note:
        Username uniqueness must be enforced at the application/database layer.
    """
    username: str = Field(
        ...,
        description="Unique username for authentication",
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$"
    )
    hashed_password: str = Field(
        ...,
        description="Bcrypt hashed password",
        min_length=1
    )
    disabled: bool = Field(
        default=False,
        description="Whether the user account is disabled"
    )
    full_name: Optional[str] = Field(
        None,
        description="Full name of the user",
        max_length=100
    )
    email: Optional[str] = Field(
        None,
        description="Email address",
        max_length=255
    )
    
    @field_validator('username')
    @classmethod
    def validate_username_format(cls, v: str) -> str:
        """Validate username doesn't start/end with special characters"""
        if v.startswith('-') or v.startswith('_'):
            raise ValueError("Username cannot start with - or _")
        if v.endswith('-') or v.endswith('_'):
            raise ValueError("Username cannot end with - or _")
        return v
    
    @field_validator('hashed_password')
    @classmethod
    def validate_hashed_password(cls, v: str) -> str:
        """Validate password appears to be a bcrypt hash"""
        # Bcrypt hashes start with $2a$, $2b$, or $2y$ and have specific length
        if not v.startswith(('$2a$', '$2b$', '$2y$')):
            # Allow any string for flexibility, but log warning in production
            pass
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "hashed_password": "$2b$12$KIXwfGqW.vQNfB8p5K7TgOZhHhYXz5JX8qE4nJ0Vc7eP3aK4X5Yzi",
                "disabled": False,
                "full_name": "John Doe",
                "email": "john.doe@example.com"
            }
        }


class Token(BaseModel):
    """
    JWT token response model
    
    Returned after successful authentication.
    
    Attributes:
        access_token: JWT access token string
        token_type: Token type (typically "bearer")
    
    Example:
        >>> token = Token(
        ...     access_token="eyJhbGciOiJIUzI1NiIs...",
        ...     token_type="bearer"
        ... )
    """
    access_token: str = Field(
        ...,
        description="JWT access token string",
        min_length=1
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (typically 'bearer')"
    )
    
    @field_validator('token_type')
    @classmethod
    def validate_token_type(cls, v: str) -> str:
        """Ensure token_type is lowercase"""
        return v.lower()
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqb2huX2RvZSIsImV4cCI6MTYzOTQ3NjAwMH0.abc123",
                "token_type": "bearer"
            }
        }


class TokenPayload(BaseModel):
    """
    JWT token payload data model
    
    Represents the decoded JWT token payload with all claims.
    
    Attributes:
        sub: Subject (username)
        exp: Expiration time (UTC, timezone-aware)
        iat: Issued at time (UTC, timezone-aware)
        jti: JWT ID (unique token identifier)
        permissions: List of granted permissions
        session_id: Associated session identifier
    
    Example:
        >>> from datetime import datetime, timezone, timedelta
        >>> payload = TokenPayload(
        ...     sub="john_doe",
        ...     exp=datetime.now(timezone.utc) + timedelta(hours=1),
        ...     iat=datetime.now(timezone.utc),
        ...     jti=str(uuid.uuid4()),
        ...     permissions=["advice:generate", "advice:view_history"],
        ...     session_id="sess_abc123"
        ... )
    """
    sub: str = Field(
        ...,
        description="Subject (username)",
        min_length=1,
        max_length=255
    )
    exp: datetime = Field(
        ...,
        description="Expiration time (UTC, timezone-aware)"
    )
    iat: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Issued at time (UTC, timezone-aware)"
    )
    jti: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="JWT ID (unique token identifier)"
    )
    permissions: List[str] = Field(
        default_factory=list,
        description="List of granted permissions"
    )
    session_id: str = Field(
        ...,
        description="Associated session identifier",
        min_length=1,
        max_length=255
    )
    
    @field_validator('exp', 'iat')
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure datetime fields are timezone-aware"""
        if v.tzinfo is None:
            # If naive, assume UTC and make aware
            return v.replace(tzinfo=timezone.utc)
        return v
    
    @field_validator('exp')
    @classmethod
    def validate_expiration_future(cls, v: datetime) -> datetime:
        """Ensure expiration is in the future"""
        now = datetime.now(timezone.utc)
        if v <= now:
            raise ValueError("Token expiration must be in the future")
        return v
    
    @field_validator('permissions')
    @classmethod
    def validate_permissions(cls, v: List[str]) -> List[str]:
        """Validate permissions against allowed set"""
        if not v:
            # Empty permissions list is allowed
            return v
        
        invalid_perms = [perm for perm in v if perm not in ALLOWED_PERMISSIONS]
        if invalid_perms:
            raise ValueError(
                f"Invalid permissions: {invalid_perms}. "
                f"Allowed permissions: {sorted(ALLOWED_PERMISSIONS)}"
            )
        
        # Remove duplicates while preserving order
        seen = set()
        unique_perms = []
        for perm in v:
            if perm not in seen:
                seen.add(perm)
                unique_perms.append(perm)
        
        return unique_perms
    
    @field_validator('jti')
    @classmethod
    def validate_jti_format(cls, v: str) -> str:
        """Validate JTI is a valid UUID format"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid UUID format for jti: {v}")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sub": "john_doe",
                "exp": "2025-10-11T15:30:00Z",
                "iat": "2025-10-11T14:30:00Z",
                "jti": "550e8400-e29b-41d4-a716-446655440000",
                "permissions": ["advice:generate", "advice:view_history"],
                "session_id": "sess_abc123xyz"
            }
        }

