"""
Enhanced user profile and session data models

These models support:
- Role-based access control (RBAC)
- User preferences and security settings
- Detailed session tracking
- Multi-session management
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, EmailStr, field_validator
from enum import Enum
import uuid


class UserRole(str, Enum):
    """User role types for RBAC"""
    STANDARD = "standard"
    ADVISOR = "advisor"
    ADMIN = "admin"


class UserProfile(BaseModel):
    """
    Enhanced user profile data model
    
    Supports role-based access control, user preferences, and security settings.
    
    Attributes:
        user_id: Unique user identifier
        username: Username for authentication
        email: User email address (validated)
        role: User role for RBAC (standard, advisor, admin)
        permissions: List of specific permissions granted to user
        created_at: UTC timestamp when user was created (timezone-aware)
        last_login: UTC timestamp of last login (timezone-aware, optional)
        security_settings: Extensible security configuration
        preferences: User preferences for personalization
    
    Example:
        >>> profile = UserProfile(
        ...     user_id="user_12345",
        ...     username="john_doe",
        ...     email="john@example.com",
        ...     role="advisor",
        ...     permissions=["view_reports", "generate_advice"],
        ...     security_settings={"mfa_enabled": True, "password_expires": 90}
        ... )
    """
    user_id: str = Field(
        ...,
        description="Unique user identifier",
        min_length=1,
        max_length=255
    )
    username: str = Field(
        ...,
        description="Username for authentication",
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$"
    )
    email: EmailStr = Field(
        ...,
        description="User email address (validated format)"
    )
    role: UserRole = Field(
        ...,
        description="User role for RBAC"
    )
    permissions: List[str] = Field(
        default_factory=list,
        description="Specific permissions granted to user",
        examples=[["view_reports", "generate_advice", "manage_users"]]
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when user was created"
    )
    last_login: Optional[datetime] = Field(
        None,
        description="UTC timestamp of last login"
    )
    security_settings: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extensible security configuration",
        examples=[{
            "mfa_enabled": True,
            "password_expires_days": 90,
            "allowed_ip_ranges": ["192.168.1.0/24"],
            "require_password_change": False
        }]
    )
    preferences: Dict[str, Any] = Field(
        default_factory=dict,
        description="User preferences for personalization",
        examples=[{
            "theme": "dark",
            "language": "en",
            "timezone": "America/New_York",
            "notifications_enabled": True,
            "dashboard_layout": "compact"
        }]
    )
    
    @field_validator('created_at', 'last_login')
    @classmethod
    def validate_timezone_aware(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure datetime fields are timezone-aware"""
        if v is None:
            return v
        if v.tzinfo is None:
            # If naive, assume UTC and make aware
            return v.replace(tzinfo=timezone.utc)
        return v
    
    @field_validator('username')
    @classmethod
    def validate_username_format(cls, v: str) -> str:
        """Additional username validation"""
        if v.startswith('-') or v.startswith('_'):
            raise ValueError("Username cannot start with - or _")
        if v.endswith('-') or v.endswith('_'):
            raise ValueError("Username cannot end with - or _")
        return v
    
    @field_validator('permissions')
    @classmethod
    def validate_permissions_unique(cls, v: List[str]) -> List[str]:
        """Ensure permissions list has no duplicates"""
        if len(v) != len(set(v)):
            # Remove duplicates while preserving order
            seen = set()
            unique_perms = []
            for perm in v:
                if perm not in seen:
                    seen.add(perm)
                    unique_perms.append(perm)
            return unique_perms
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_12345",
                "username": "john_doe",
                "email": "john.doe@example.com",
                "role": "advisor",
                "permissions": ["view_reports", "generate_advice", "manage_clients"],
                "created_at": "2025-10-11T14:30:00Z",
                "last_login": "2025-10-11T16:45:00Z",
                "security_settings": {
                    "mfa_enabled": True,
                    "password_expires_days": 90,
                    "session_timeout_minutes": 30,
                    "allowed_ip_ranges": []
                },
                "preferences": {
                    "theme": "dark",
                    "language": "en",
                    "timezone": "America/New_York",
                    "notifications_enabled": True
                }
            }
        }


class SessionMetadata(BaseModel):
    """
    Session metadata data model for tracking active sessions
    
    Supports multi-session management, security monitoring, and session lifecycle tracking.
    
    Attributes:
        session_id: Unique session identifier (UUID format)
        user_id: User identifier associated with this session
        created_at: UTC timestamp when session was created (timezone-aware)
        last_activity: UTC timestamp of last session activity (timezone-aware)
        ip_address: IP address of the session (IPv4 or IPv6)
        user_agent: Browser/client user agent string
        is_active: Whether session is currently active
        security_flags: List of security markers (e.g., "suspicious", "vpn_detected")
    
    Example:
        >>> session = SessionMetadata(
        ...     session_id="550e8400-e29b-41d4-a716-446655440000",
        ...     user_id="user_12345",
        ...     ip_address="192.168.1.100",
        ...     user_agent="Mozilla/5.0...",
        ...     is_active=True,
        ...     security_flags=["verified", "trusted_device"]
        ... )
    """
    session_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique session identifier (UUID format)",
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    )
    user_id: str = Field(
        ...,
        description="User identifier associated with this session",
        min_length=1,
        max_length=255
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when session was created"
    )
    last_activity: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of last session activity"
    )
    ip_address: str = Field(
        ...,
        description="IP address of the session (IPv4 or IPv6)",
        pattern=r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$|^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$"
    )
    user_agent: str = Field(
        ...,
        description="Browser/client user agent string",
        max_length=500
    )
    is_active: bool = Field(
        default=True,
        description="Whether session is currently active"
    )
    security_flags: List[str] = Field(
        default_factory=list,
        description="Security markers (e.g., suspicious, vpn_detected, trusted_device)",
        examples=[["verified", "trusted_device", "mfa_authenticated"]]
    )
    
    @field_validator('created_at', 'last_activity')
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure datetime fields are timezone-aware"""
        if v.tzinfo is None:
            # If naive, assume UTC and make aware
            return v.replace(tzinfo=timezone.utc)
        return v
    
    @field_validator('ip_address')
    @classmethod
    def validate_ip_format(cls, v: str) -> str:
        """Validate IP address format using ipaddress module"""
        import ipaddress
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid IP address format: {v}")
    
    @field_validator('session_id')
    @classmethod
    def validate_session_id_format(cls, v: str) -> str:
        """Validate session_id is a valid UUID format"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid UUID format for session_id: {v}")
    
    @field_validator('last_activity')
    @classmethod
    def validate_last_activity_not_future(cls, v: datetime) -> datetime:
        """Ensure last_activity is not in the future"""
        now = datetime.now(timezone.utc)
        if v > now:
            raise ValueError("last_activity cannot be in the future")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "user_12345",
                "created_at": "2025-10-11T14:30:00Z",
                "last_activity": "2025-10-11T16:45:00Z",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/118.0",
                "is_active": True,
                "security_flags": ["verified", "trusted_device", "mfa_authenticated"]
            }
        }

