"""
Advanced JWT token management data models

Supports:
- Token refresh and renewal
- Token revocation and blacklisting
- Real-time token event tracking
- Token validation and security assessment
- Token metadata and audit trails
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class TokenTypeHint(str, Enum):
    """Token type hints for revocation"""
    ACCESS_TOKEN = "access_token"
    REFRESH_TOKEN = "refresh_token"


class TokenEventType(str, Enum):
    """Token lifecycle event types"""
    ISSUED = "issued"
    REFRESHED = "refreshed"
    REVOKED = "revoked"
    EXPIRED = "expired"
    VALIDATION_FAILED = "validation_failed"


class TokenType(str, Enum):
    """Token types"""
    ACCESS = "access"
    REFRESH = "refresh"


class TokenMessageType(str, Enum):
    """WebSocket message types for token events"""
    TOKEN_EVENT = "token_event"
    SECURITY_VIOLATION = "security_violation"
    EXPIRATION_WARNING = "expiration_warning"


class TokenRefreshRequest(BaseModel):
    """
    Token refresh request data model
    
    Attributes:
        refresh_token: JWT refresh token to exchange for new access token
        device_fingerprint: Optional unique device identifier
        client_metadata: Optional client information
    
    Example:
        >>> request = TokenRefreshRequest(
        ...     refresh_token="eyJhbGciOiJIUzI1NiIs...",
        ...     device_fingerprint="fp_abc123"
        ... )
    """
    refresh_token: str = Field(
        ...,
        description="JWT refresh token",
        min_length=1
    )
    device_fingerprint: Optional[str] = Field(
        None,
        description="Unique device identifier",
        max_length=255
    )
    client_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Client information (browser, OS, etc.)",
        examples=[{"browser": "Chrome", "os": "Windows"}]
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "device_fingerprint": "fp_abc123xyz",
                "client_metadata": {
                    "browser": "Chrome",
                    "browser_version": "118.0",
                    "os": "Windows"
                }
            }
        }


class TokenRefreshResponse(BaseModel):
    """
    Token refresh response data model
    
    Attributes:
        access_token: New JWT access token
        refresh_token: New JWT refresh token (rotated)
        token_type: Token type (default "bearer")
        expires_in: Access token expiration in seconds
        refresh_expires_in: Refresh token expiration in seconds
        token_metadata: Token metadata for tracking and audit
    
    Example:
        >>> response = TokenRefreshResponse(
        ...     access_token="eyJhbGci...",
        ...     refresh_token="eyJhbGci...",
        ...     expires_in=1800,
        ...     refresh_expires_in=604800,
        ...     token_metadata=token_metadata
        ... )
    """
    access_token: str = Field(
        ...,
        description="New JWT access token"
    )
    refresh_token: str = Field(
        ...,
        description="New JWT refresh token (rotated)"
    )
    token_type: str = Field(
        default="bearer",
        description="Token type"
    )
    expires_in: int = Field(
        ...,
        description="Access token expiration in seconds",
        gt=0
    )
    refresh_expires_in: int = Field(
        ...,
        description="Refresh token expiration in seconds",
        gt=0
    )
    token_metadata: 'TokenMetadata' = Field(
        ...,
        description="Token metadata for tracking"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIs...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
                "token_type": "bearer",
                "expires_in": 1800,
                "refresh_expires_in": 604800,
                "token_metadata": {
                    "token_id": "550e8400-e29b-41d4-a716-446655440000",
                    "issued_at": "2025-10-11T14:30:00Z",
                    "expires_at": "2025-10-11T15:00:00Z",
                    "issuer": "apfa-api",
                    "audience": ["apfa-frontend"],
                    "scopes": ["advice:generate"]
                }
            }
        }


class TokenRevocationRequest(BaseModel):
    """
    Token revocation request data model
    
    Attributes:
        token: Token to revoke (access or refresh token)
        token_type_hint: Hint about token type for optimization
        revoke_all_sessions: Whether to revoke all user sessions
    
    Example:
        >>> request = TokenRevocationRequest(
        ...     token="eyJhbGci...",
        ...     token_type_hint="access_token",
        ...     revoke_all_sessions=False
        ... )
    """
    token: str = Field(
        ...,
        description="Token to revoke",
        min_length=1
    )
    token_type_hint: TokenTypeHint = Field(
        ...,
        description="Hint about token type"
    )
    revoke_all_sessions: bool = Field(
        default=False,
        description="Whether to revoke all user sessions"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type_hint": "access_token",
                "revoke_all_sessions": False
            }
        }


class TokenEvent(BaseModel):
    """
    Token lifecycle event data model
    
    Attributes:
        event_type: Type of token event
        token_id: Unique token identifier (JTI)
        user_id: Associated user identifier
        timestamp: UTC timestamp of event (timezone-aware)
        ip_address: IP address of the event
        user_agent: User agent string
        token_type: Type of token (access or refresh)
        expiration_time: Token expiration time
        security_metadata: Additional security information
    
    Example:
        >>> event = TokenEvent(
        ...     event_type="issued",
        ...     token_id="550e8400-e29b-41d4-a716-446655440000",
        ...     user_id="user_123",
        ...     ip_address="192.168.1.1",
        ...     user_agent="Mozilla/5.0",
        ...     token_type="access",
        ...     expiration_time=datetime.now(timezone.utc) + timedelta(hours=1)
        ... )
    """
    event_type: TokenEventType = Field(
        ...,
        description="Type of token event"
    )
    token_id: str = Field(
        ...,
        description="Unique token identifier (JTI)",
        min_length=1,
        max_length=255
    )
    user_id: str = Field(
        ...,
        description="Associated user identifier",
        min_length=1,
        max_length=255
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of event"
    )
    ip_address: str = Field(
        ...,
        description="IP address of the event",
        pattern=r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$|^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$"
    )
    user_agent: str = Field(
        ...,
        description="User agent string",
        max_length=500
    )
    token_type: TokenType = Field(
        ...,
        description="Type of token (access or refresh)"
    )
    expiration_time: datetime = Field(
        ...,
        description="Token expiration time"
    )
    security_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional security information",
        examples=[{
            "scope": "full_access",
            "permissions": ["advice:generate"],
            "device_verified": True
        }]
    )
    
    @field_validator('timestamp', 'expiration_time')
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure datetime fields are timezone-aware"""
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v
    
    @field_validator('ip_address')
    @classmethod
    def validate_ip_format(cls, v: str) -> str:
        """Validate IP address format"""
        import ipaddress
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid IP address format: {v}")
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "issued",
                "token_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "user_12345",
                "timestamp": "2025-10-11T14:30:00Z",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0",
                "token_type": "access",
                "expiration_time": "2025-10-11T15:00:00Z",
                "security_metadata": {
                    "scope": "full_access",
                    "permissions": ["advice:generate", "advice:view_history"]
                }
            }
        }


class WebSocketTokenMessage(BaseModel):
    """
    WebSocket message wrapper for token events
    
    Attributes:
        message_type: Type of WebSocket message
        event_data: Token event details
        security_assessment: Security analysis of the event
        requires_action: Whether immediate action is needed
    
    Example:
        >>> message = WebSocketTokenMessage(
        ...     message_type="security_violation",
        ...     event_data=token_event,
        ...     security_assessment={"threat_level": "high"},
        ...     requires_action=True
        ... )
    """
    message_type: TokenMessageType = Field(
        ...,
        description="Type of WebSocket message"
    )
    event_data: TokenEvent = Field(
        ...,
        description="Token event details"
    )
    security_assessment: Dict[str, Any] = Field(
        default_factory=dict,
        description="Security analysis of the event",
        examples=[{
            "threat_level": "low",
            "risk_factors": [],
            "recommended_action": "none"
        }]
    )
    requires_action: bool = Field(
        default=False,
        description="Whether immediate action is needed"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "message_type": "expiration_warning",
                "event_data": {
                    "event_type": "expired",
                    "token_id": "550e8400-e29b-41d4-a716-446655440000",
                    "user_id": "user_12345",
                    "timestamp": "2025-10-11T15:00:00Z",
                    "ip_address": "192.168.1.100",
                    "user_agent": "Mozilla/5.0",
                    "token_type": "access",
                    "expiration_time": "2025-10-11T15:00:00Z"
                },
                "security_assessment": {
                    "threat_level": "info",
                    "recommended_action": "refresh_token"
                },
                "requires_action": False
            }
        }


class TokenMetadata(BaseModel):
    """
    Token metadata data model for tracking and audit
    
    Attributes:
        token_id: Unique token identifier (JTI)
        issued_at: Timestamp when token was issued
        expires_at: Timestamp when token expires
        issuer: Token issuer (e.g., "apfa-api")
        audience: List of intended token audiences
        scopes: List of granted scopes/permissions
        device_fingerprint: Optional device identifier
        ip_address: Optional IP address where token was issued
        security_level: Security level classification
    
    Example:
        >>> metadata = TokenMetadata(
        ...     token_id="550e8400-e29b-41d4-a716-446655440000",
        ...     issued_at=datetime.now(timezone.utc),
        ...     expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ...     issuer="apfa-api",
        ...     audience=["apfa-frontend"],
        ...     scopes=["advice:generate"]
        ... )
    """
    token_id: str = Field(
        ...,
        description="Unique token identifier (JTI)",
        min_length=1,
        max_length=255
    )
    issued_at: datetime = Field(
        ...,
        description="Timestamp when token was issued"
    )
    expires_at: datetime = Field(
        ...,
        description="Timestamp when token expires"
    )
    issuer: str = Field(
        ...,
        description="Token issuer (e.g., apfa-api)",
        max_length=255
    )
    audience: List[str] = Field(
        ...,
        description="List of intended token audiences",
        examples=[["apfa-frontend", "apfa-mobile"]]
    )
    scopes: List[str] = Field(
        ...,
        description="List of granted scopes/permissions",
        examples=[["advice:generate", "advice:view_history"]]
    )
    device_fingerprint: Optional[str] = Field(
        None,
        description="Device identifier where token was issued",
        max_length=255
    )
    ip_address: Optional[str] = Field(
        None,
        description="IP address where token was issued",
        pattern=r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$|^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$"
    )
    security_level: Optional[str] = Field(
        None,
        description="Security level classification",
        max_length=50
    )
    
    @field_validator('issued_at', 'expires_at')
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure datetime fields are timezone-aware"""
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v
    
    @field_validator('expires_at')
    @classmethod
    def validate_expires_after_issued(cls, v: datetime, info) -> datetime:
        """Ensure expiration is after issuance"""
        issued_at = info.data.get('issued_at')
        if issued_at and v <= issued_at:
            raise ValueError("Token expiration must be after issuance time")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "token_id": "550e8400-e29b-41d4-a716-446655440000",
                "issued_at": "2025-10-11T14:30:00Z",
                "expires_at": "2025-10-11T15:00:00Z",
                "issuer": "apfa-api",
                "audience": ["apfa-frontend", "apfa-mobile"],
                "scopes": ["advice:generate", "advice:view_history"],
                "device_fingerprint": "fp_abc123",
                "ip_address": "192.168.1.100",
                "security_level": "standard"
            }
        }


class TokenValidationResult(BaseModel):
    """
    Token validation result data model
    
    Attributes:
        is_valid: Whether the token is valid
        token_id: Token identifier (JTI)
        user_id: Optional user identifier if valid
        expiration_time: Optional token expiration time
        validation_errors: List of validation errors if invalid
        security_warnings: List of security warnings
        remaining_ttl_seconds: Optional remaining time-to-live in seconds
    
    Example:
        >>> result = TokenValidationResult(
        ...     is_valid=True,
        ...     token_id="550e8400-e29b-41d4-a716-446655440000",
        ...     user_id="user_123",
        ...     remaining_ttl_seconds=1500
        ... )
    """
    is_valid: bool = Field(
        ...,
        description="Whether the token is valid"
    )
    token_id: str = Field(
        ...,
        description="Token identifier (JTI)",
        min_length=1,
        max_length=255
    )
    user_id: Optional[str] = Field(
        None,
        description="User identifier if valid",
        max_length=255
    )
    expiration_time: Optional[datetime] = Field(
        None,
        description="Token expiration time"
    )
    validation_errors: List[str] = Field(
        default_factory=list,
        description="List of validation errors if invalid",
        examples=[["Token expired", "Invalid signature"]]
    )
    security_warnings: List[str] = Field(
        default_factory=list,
        description="List of security warnings",
        examples=[["Token expires soon", "Issued from new IP"]]
    )
    remaining_ttl_seconds: Optional[int] = Field(
        None,
        description="Remaining time-to-live in seconds",
        ge=0
    )
    
    @field_validator('expiration_time')
    @classmethod
    def validate_timezone_aware(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure datetime is timezone-aware"""
        if v and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_valid": True,
                "token_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "user_12345",
                "expiration_time": "2025-10-11T15:00:00Z",
                "validation_errors": [],
                "security_warnings": ["Token expires in 5 minutes"],
                "remaining_ttl_seconds": 300
            }
        }

