"""
Enhanced user login data models

Supports:
- Comprehensive login request validation
- Detailed login response with user profile and session metadata
- MFA support
- Device tracking
- Client metadata capture
"""
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field
from app.models.user_profile import UserProfile, SessionMetadata


class UserLoginRequest(BaseModel):
    """
    Enhanced user login request data model
    
    Attributes:
        username: Username for authentication (3-50 characters)
        password: User password (minimum 1 character)
        remember_me: Whether to extend session lifetime
        mfa_token: Optional MFA token for two-factor authentication
        device_fingerprint: Optional unique device identifier
        client_metadata: Optional client information (browser, OS, etc.)
    
    Example:
        >>> request = UserLoginRequest(
        ...     username="john_doe",
        ...     password="SecurePass123!",
        ...     remember_me=True,
        ...     device_fingerprint="fp_abc123"
        ... )
    """
    username: str = Field(
        ...,
        description="Username for authentication",
        min_length=3,
        max_length=50
    )
    password: str = Field(
        ...,
        description="User password",
        min_length=1
    )
    remember_me: bool = Field(
        default=False,
        description="Whether to extend session lifetime"
    )
    mfa_token: Optional[str] = Field(
        None,
        description="MFA token for two-factor authentication",
        min_length=6,
        max_length=10
    )
    device_fingerprint: Optional[str] = Field(
        None,
        description="Unique device identifier",
        max_length=255
    )
    client_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Client information (browser, OS, etc.)",
        examples=[{
            "browser": "Chrome",
            "browser_version": "118.0",
            "os": "Windows",
            "os_version": "10",
            "device_type": "desktop"
        }]
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "password": "SecurePass123!",
                "remember_me": True,
                "mfa_token": "123456",
                "device_fingerprint": "fp_abc123xyz",
                "client_metadata": {
                    "browser": "Chrome",
                    "browser_version": "118.0",
                    "os": "Windows",
                    "device_type": "desktop"
                }
            }
        }


class LoginResponse(BaseModel):
    """
    Enhanced login response data model
    
    Attributes:
        access_token: JWT access token
        refresh_token: JWT refresh token (for token renewal)
        token_type: Token type (default "bearer")
        expires_in: Token expiration time in seconds
        user_profile: User profile information
        session_metadata: Session tracking information
        requires_mfa: Whether MFA verification is required
        mfa_methods: Available MFA methods if required
    
    Example:
        >>> response = LoginResponse(
        ...     access_token="eyJhbGci...",
        ...     refresh_token="eyJhbGci...",
        ...     token_type="bearer",
        ...     expires_in=1800,
        ...     user_profile=user_profile,
        ...     session_metadata=session_metadata,
        ...     requires_mfa=False,
        ...     mfa_methods=[]
        ... )
    """
    access_token: str = Field(
        ...,
        description="JWT access token"
    )
    refresh_token: str = Field(
        ...,
        description="JWT refresh token"
    )
    token_type: str = Field(
        default="bearer",
        description="Token type"
    )
    expires_in: int = Field(
        ...,
        description="Token expiration time in seconds",
        gt=0
    )
    user_profile: UserProfile = Field(
        ...,
        description="User profile information"
    )
    session_metadata: SessionMetadata = Field(
        ...,
        description="Session tracking information"
    )
    requires_mfa: bool = Field(
        default=False,
        description="Whether MFA verification is required"
    )
    mfa_methods: List[str] = Field(
        default_factory=list,
        description="Available MFA methods if required",
        examples=[["totp", "sms", "email"]]
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "user_profile": {
                    "user_id": "user_12345",
                    "username": "john_doe",
                    "email": "john@example.com",
                    "role": "advisor",
                    "permissions": ["advice:generate", "advice:view_history"]
                },
                "session_metadata": {
                    "session_id": "550e8400-e29b-41d4-a716-446655440000",
                    "user_id": "user_12345",
                    "ip_address": "192.168.1.100",
                    "user_agent": "Mozilla/5.0",
                    "is_active": True,
                    "security_flags": ["verified", "trusted_device"]
                },
                "requires_mfa": False,
                "mfa_methods": []
            }
        }

