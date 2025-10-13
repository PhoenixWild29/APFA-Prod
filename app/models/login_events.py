"""
Real-time login event data models for security monitoring and anomaly detection

These models track authentication activities and support:
- Security auditing
- Anomaly detection
- Real-time admin alerts
- Geographic tracking
- Risk assessment
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class LoginEventType(str, Enum):
    """Login event types for security tracking"""
    LOGIN_ATTEMPT = "login_attempt"
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    MFA_REQUIRED = "mfa_required"


class MessageType(str, Enum):
    """WebSocket message types for real-time notifications"""
    LOGIN_EVENT = "login_event"
    SECURITY_ALERT = "security_alert"
    ANOMALY_DETECTION = "anomaly_detection"


class LoginEvent(BaseModel):
    """
    Login event data model for tracking authentication activities
    
    Attributes:
        event_type: Type of login event (attempt, success, failure, mfa_required)
        user_id: Optional user identifier (None for failed attempts)
        username: Username attempting to log in
        timestamp: UTC timestamp of the event
        ip_address: IP address of the login attempt
        user_agent: Browser/client user agent string
        device_fingerprint: Optional unique device identifier
        success: Whether the login was successful
        failure_reason: Optional reason for login failure
        security_score: Risk score (0.0-1.0, higher = more suspicious)
        geographic_location: Optional location data (country, city, lat/lon)
    
    Example:
        >>> event = LoginEvent(
        ...     event_type="login_success",
        ...     username="admin",
        ...     timestamp=datetime.utcnow(),
        ...     ip_address="192.168.1.1",
        ...     user_agent="Mozilla/5.0...",
        ...     success=True,
        ...     security_score=0.1
        ... )
    """
    event_type: LoginEventType = Field(
        ...,
        description="Type of login event"
    )
    user_id: Optional[str] = Field(
        None,
        description="User ID (None for failed attempts)",
        min_length=1,
        max_length=255
    )
    username: str = Field(
        ...,
        description="Username attempting login",
        min_length=1,
        max_length=255
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp of event"
    )
    ip_address: str = Field(
        ...,
        description="IP address of login attempt",
        pattern=r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$|^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$"
    )
    user_agent: str = Field(
        ...,
        description="Browser/client user agent",
        max_length=500
    )
    device_fingerprint: Optional[str] = Field(
        None,
        description="Unique device identifier",
        max_length=255
    )
    success: bool = Field(
        ...,
        description="Whether login was successful"
    )
    failure_reason: Optional[str] = Field(
        None,
        description="Reason for login failure",
        max_length=500
    )
    security_score: float = Field(
        ...,
        description="Risk score (0.0-1.0, higher = riskier)",
        ge=0.0,
        le=1.0
    )
    geographic_location: Optional[Dict[str, Any]] = Field(
        None,
        description="Location data (country, city, coordinates)",
        examples=[{
            "country": "US",
            "city": "San Francisco",
            "latitude": 37.7749,
            "longitude": -122.4194
        }]
    )
    
    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v: datetime) -> datetime:
        """Ensure timestamp is not in the future"""
        if v > datetime.utcnow():
            raise ValueError("Timestamp cannot be in the future")
        return v
    
    @field_validator('security_score')
    @classmethod
    def validate_security_score(cls, v: float) -> float:
        """Ensure security score is within valid range"""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Security score must be between 0.0 and 1.0")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "login_success",
                "user_id": "user_12345",
                "username": "admin",
                "timestamp": "2025-10-11T14:30:00Z",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/118.0",
                "device_fingerprint": "fp_abc123xyz",
                "success": True,
                "failure_reason": None,
                "security_score": 0.15,
                "geographic_location": {
                    "country": "US",
                    "city": "New York",
                    "latitude": 40.7128,
                    "longitude": -74.0060
                }
            }
        }


class WebSocketLoginMessage(BaseModel):
    """
    WebSocket message wrapper for broadcasting login events in real-time
    
    Attributes:
        message_type: Type of message (login_event, security_alert, anomaly_detection)
        event_data: The login event data
        risk_assessment: Risk analysis details
        requires_admin_attention: Whether admin should be notified
    
    Example:
        >>> message = WebSocketLoginMessage(
        ...     message_type="security_alert",
        ...     event_data=login_event,
        ...     risk_assessment={"threat_level": "high", "reasons": ["suspicious_ip"]},
        ...     requires_admin_attention=True
        ... )
    """
    message_type: MessageType = Field(
        ...,
        description="Type of WebSocket message"
    )
    event_data: LoginEvent = Field(
        ...,
        description="Login event details"
    )
    risk_assessment: Dict[str, Any] = Field(
        default_factory=dict,
        description="Risk analysis details",
        examples=[{
            "threat_level": "medium",
            "reasons": ["new_device", "unusual_time"],
            "recommended_action": "require_mfa"
        }]
    )
    requires_admin_attention: bool = Field(
        default=False,
        description="Whether to alert administrators"
    )
    
    @field_validator('risk_assessment')
    @classmethod
    def validate_risk_assessment(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure risk_assessment contains expected keys (if provided)"""
        if v:
            # Optional validation: ensure common keys exist if dict is not empty
            expected_keys = {'threat_level', 'reasons', 'recommended_action'}
            if not any(key in v for key in expected_keys):
                # Warning: risk_assessment doesn't contain standard keys
                # Don't fail validation, just log warning
                pass
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "message_type": "security_alert",
                "event_data": {
                    "event_type": "login_failure",
                    "user_id": None,
                    "username": "admin",
                    "timestamp": "2025-10-11T14:30:00Z",
                    "ip_address": "203.0.113.45",
                    "user_agent": "curl/7.68.0",
                    "device_fingerprint": None,
                    "success": False,
                    "failure_reason": "Invalid password",
                    "security_score": 0.85,
                    "geographic_location": {
                        "country": "Unknown",
                        "city": "Unknown"
                    }
                },
                "risk_assessment": {
                    "threat_level": "high",
                    "reasons": ["suspicious_ip", "unusual_user_agent", "repeated_failures"],
                    "recommended_action": "block_ip"
                },
                "requires_admin_attention": True
            }
        }

