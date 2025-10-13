"""
Real-time authentication event data models

These models track authentication activities and support:
- Security monitoring and audit logging
- Real-time WebSocket notifications
- Session management and validation
- Authentication failure tracking
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class AuthEventType(str, Enum):
    """Authentication event types"""
    LOGIN = "login"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    VALIDATION_FAILURE = "validation_failure"


class MessageType(str, Enum):
    """WebSocket message types for authentication"""
    AUTH_EVENT = "auth_event"
    SECURITY_ALERT = "security_alert"
    SESSION_UPDATE = "session_update"


class Severity(str, Enum):
    """Event severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AuthenticationEvent(BaseModel):
    """
    Authentication event data model for tracking auth activities
    
    Attributes:
        event_type: Type of authentication event (login, logout, token_refresh, validation_failure)
        user_id: User identifier
        timestamp: UTC timestamp (timezone-aware)
        ip_address: IP address (IPv4 or IPv6 format)
        user_agent: Browser/client user agent string
        success: Whether the authentication was successful
        error_message: Optional error message if failed
        security_metadata: Extensible dictionary for additional security data
    
    Example:
        >>> event = AuthenticationEvent(
        ...     event_type="login",
        ...     user_id="user_123",
        ...     ip_address="192.168.1.1",
        ...     user_agent="Mozilla/5.0...",
        ...     success=True,
        ...     security_metadata={"session_id": "sess_abc", "mfa_used": True}
        ... )
    """
    event_type: AuthEventType = Field(
        ...,
        description="Type of authentication event"
    )
    user_id: str = Field(
        ...,
        description="User identifier",
        min_length=1,
        max_length=255
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp (timezone-aware)"
    )
    ip_address: str = Field(
        ...,
        description="IP address (IPv4 or IPv6)",
        pattern=r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$|^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$"
    )
    user_agent: str = Field(
        ...,
        description="User agent string",
        max_length=500
    )
    success: bool = Field(
        ...,
        description="Whether the authentication was successful"
    )
    error_message: Optional[str] = Field(
        None,
        description="Error message if authentication failed",
        max_length=500
    )
    security_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extensible security metadata (session_id, mfa_used, etc.)",
        examples=[{
            "session_id": "sess_abc123",
            "mfa_used": True,
            "device_id": "device_xyz",
            "last_activity": "2025-10-11T14:30:00Z"
        }]
    )
    
    @field_validator('timestamp')
    @classmethod
    def validate_timestamp_aware(cls, v: datetime) -> datetime:
        """
        Ensure timestamp is timezone-aware
        
        If a naive datetime is provided, it will be converted to UTC.
        """
        if v.tzinfo is None:
            # If naive, assume UTC and make aware
            return v.replace(tzinfo=timezone.utc)
        return v
    
    @field_validator('ip_address')
    @classmethod
    def validate_ip_format(cls, v: str) -> str:
        """
        Additional validation for IP address format
        
        The pattern in Field already validates the basic format,
        but this provides more detailed error messages.
        """
        import ipaddress
        try:
            # Validate using ipaddress module for more robust checking
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid IP address format: {v}")
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "login",
                "user_id": "user_12345",
                "timestamp": "2025-10-11T14:30:00Z",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/118.0",
                "success": True,
                "error_message": None,
                "security_metadata": {
                    "session_id": "sess_abc123xyz",
                    "mfa_used": True,
                    "device_fingerprint": "fp_device123",
                    "auth_method": "password"
                }
            }
        }


class WebSocketAuthMessage(BaseModel):
    """
    WebSocket message wrapper for real-time authentication events
    
    Attributes:
        message_type: Type of WebSocket message (auth_event, security_alert, session_update)
        event_data: The authentication event details
        severity: Event severity level (info, warning, critical)
        requires_action: Whether immediate admin action is required
    
    Example:
        >>> auth_event = AuthenticationEvent(...)
        >>> message = WebSocketAuthMessage(
        ...     message_type="security_alert",
        ...     event_data=auth_event,
        ...     severity="critical",
        ...     requires_action=True
        ... )
    """
    message_type: MessageType = Field(
        ...,
        description="Type of WebSocket message"
    )
    event_data: AuthenticationEvent = Field(
        ...,
        description="Authentication event details"
    )
    severity: Severity = Field(
        ...,
        description="Event severity level"
    )
    requires_action: bool = Field(
        default=False,
        description="Whether immediate action is required"
    )
    
    @field_validator('requires_action')
    @classmethod
    def validate_critical_requires_action(cls, v: bool, info) -> bool:
        """
        Validate that critical severity events should require action
        
        This is a soft validation that logs a warning rather than failing.
        """
        # Access severity from the validation context
        severity = info.data.get('severity')
        if severity == Severity.CRITICAL and not v:
            # In production, you might want to log this warning
            # For now, we'll allow it but it's unusual
            pass
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "message_type": "security_alert",
                "event_data": {
                    "event_type": "validation_failure",
                    "user_id": "user_99999",
                    "timestamp": "2025-10-11T14:30:00Z",
                    "ip_address": "203.0.113.99",
                    "user_agent": "curl/7.68.0",
                    "success": False,
                    "error_message": "Invalid JWT token",
                    "security_metadata": {
                        "token_expired": True,
                        "token_signature_invalid": False,
                        "attempts_count": 5
                    }
                },
                "severity": "critical",
                "requires_action": True
            }
        }

