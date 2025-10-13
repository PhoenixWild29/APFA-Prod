"""
User registration data models with comprehensive validation

Supports:
- Secure user registration with password validation
- Email verification workflow
- Real-time registration event tracking
- Security monitoring for registration attempts
"""
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator
from enum import Enum
import re


class RegistrationStatus(str, Enum):
    """Registration status types"""
    PENDING_VERIFICATION = "pending_verification"
    ACTIVE = "active"


class RegistrationEventType(str, Enum):
    """Registration event types"""
    REGISTRATION_ATTEMPT = "registration_attempt"
    EMAIL_VERIFICATION = "email_verification"
    ACCOUNT_ACTIVATION = "account_activation"


class RegistrationMessageType(str, Enum):
    """WebSocket message types for registration"""
    REGISTRATION_EVENT = "registration_event"
    VERIFICATION_STATUS = "verification_status"
    SECURITY_ALERT = "security_alert"


class UserRegistrationRequest(BaseModel):
    """
    User registration request data model with comprehensive validation
    
    Attributes:
        username: Unique username (3-50 characters, alphanumeric + _ -)
        email: Valid email address
        password: Password (8+ characters with complexity requirements)
        confirm_password: Password confirmation (must match password)
        first_name: User's first name (1-100 characters)
        last_name: User's last name (1-100 characters)
        terms_accepted: Terms and conditions acceptance (required True)
        marketing_consent: Marketing email consent (default False)
    
    Example:
        >>> request = UserRegistrationRequest(
        ...     username="john_doe",
        ...     email="john@example.com",
        ...     password="SecurePass123!",
        ...     confirm_password="SecurePass123!",
        ...     first_name="John",
        ...     last_name="Doe",
        ...     terms_accepted=True
        ... )
    """
    username: str = Field(
        ...,
        description="Unique username",
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$"
    )
    email: EmailStr = Field(
        ...,
        description="Valid email address"
    )
    password: str = Field(
        ...,
        description="Password (8+ chars with complexity)",
        min_length=8,
        max_length=128
    )
    confirm_password: str = Field(
        ...,
        description="Password confirmation",
        min_length=8,
        max_length=128
    )
    first_name: str = Field(
        ...,
        description="User's first name",
        min_length=1,
        max_length=100
    )
    last_name: str = Field(
        ...,
        description="User's last name",
        min_length=1,
        max_length=100
    )
    terms_accepted: bool = Field(
        ...,
        description="Terms and conditions acceptance (must be True)"
    )
    marketing_consent: bool = Field(
        default=False,
        description="Marketing email consent"
    )
    
    @field_validator('username')
    @classmethod
    def validate_username_format(cls, v: str) -> str:
        """Validate username format"""
        if v.startswith('-') or v.startswith('_'):
            raise ValueError("Username cannot start with - or _")
        if v.endswith('-') or v.endswith('_'):
            raise ValueError("Username cannot end with - or _")
        
        # Reserved usernames
        reserved = ['admin', 'root', 'system', 'administrator', 'moderator']
        if v.lower() in reserved:
            raise ValueError(f"Username '{v}' is reserved and cannot be used")
        
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Validate password strength with complexity requirements
        
        Requirements:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', v):
            raise ValueError("Password must contain at least one digit")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")
        
        # Check for common weak passwords
        weak_passwords = ['password', '12345678', 'qwerty123', 'admin123']
        if v.lower() in weak_passwords:
            raise ValueError("Password is too common. Please choose a stronger password")
        
        return v
    
    @field_validator('terms_accepted')
    @classmethod
    def validate_terms_accepted(cls, v: bool) -> bool:
        """Ensure terms are accepted"""
        if not v:
            raise ValueError("You must accept the terms and conditions to register")
        return v
    
    @model_validator(mode='after')
    def validate_password_confirmation(self):
        """Ensure password and confirm_password match"""
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "john.doe@example.com",
                "password": "SecurePass123!",
                "confirm_password": "SecurePass123!",
                "first_name": "John",
                "last_name": "Doe",
                "terms_accepted": True,
                "marketing_consent": False
            }
        }


class RegistrationResponse(BaseModel):
    """
    User registration response data model
    
    Attributes:
        user_id: Newly created user ID
        username: Registered username
        email: Registered email address
        registration_status: Status (pending_verification or active)
        verification_token_sent: Whether verification email was sent
        created_at: UTC timestamp of registration
        next_steps: List of actions user should take
    
    Example:
        >>> response = RegistrationResponse(
        ...     user_id="user_12345",
        ...     username="john_doe",
        ...     email="john@example.com",
        ...     registration_status="pending_verification",
        ...     verification_token_sent=True,
        ...     next_steps=["Check your email", "Click verification link"]
        ... )
    """
    user_id: str = Field(
        ...,
        description="Newly created user ID",
        min_length=1,
        max_length=255
    )
    username: str = Field(
        ...,
        description="Registered username",
        min_length=3,
        max_length=50
    )
    email: EmailStr = Field(
        ...,
        description="Registered email address"
    )
    registration_status: RegistrationStatus = Field(
        ...,
        description="Registration status"
    )
    verification_token_sent: bool = Field(
        ...,
        description="Whether verification email was sent"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of registration"
    )
    next_steps: List[str] = Field(
        ...,
        description="List of actions user should take",
        examples=[["Check your email for verification link", "Verify your email within 24 hours"]]
    )
    
    @field_validator('created_at')
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware"""
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_12345",
                "username": "john_doe",
                "email": "john.doe@example.com",
                "registration_status": "pending_verification",
                "verification_token_sent": True,
                "created_at": "2025-10-11T14:30:00Z",
                "next_steps": [
                    "Check your email inbox",
                    "Click the verification link",
                    "Complete email verification within 24 hours"
                ]
            }
        }


class RegistrationEvent(BaseModel):
    """
    Registration event data model for tracking registration lifecycle
    
    Attributes:
        event_type: Type of registration event
        user_id: Optional user ID (None for failed attempts)
        email: Email address from registration
        timestamp: UTC timestamp of event
        ip_address: IP address of registration attempt
        user_agent: Browser/client user agent
        success: Whether the event was successful
        validation_errors: List of validation errors if any
        security_flags: List of security markers
    
    Example:
        >>> event = RegistrationEvent(
        ...     event_type="registration_attempt",
        ...     email="john@example.com",
        ...     ip_address="192.168.1.1",
        ...     user_agent="Mozilla/5.0",
        ...     success=True
        ... )
    """
    event_type: RegistrationEventType = Field(
        ...,
        description="Type of registration event"
    )
    user_id: Optional[str] = Field(
        None,
        description="User ID (None for failed attempts)",
        max_length=255
    )
    email: EmailStr = Field(
        ...,
        description="Email address from registration"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of event"
    )
    ip_address: str = Field(
        ...,
        description="IP address of registration attempt",
        pattern=r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$|^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$"
    )
    user_agent: str = Field(
        ...,
        description="Browser/client user agent",
        max_length=500
    )
    success: bool = Field(
        ...,
        description="Whether the event was successful"
    )
    validation_errors: List[str] = Field(
        default_factory=list,
        description="List of validation errors if any",
        examples=[["Password too weak", "Email already registered"]]
    )
    security_flags: List[str] = Field(
        default_factory=list,
        description="Security markers for monitoring",
        examples=[["suspicious_ip", "vpn_detected", "disposable_email"]]
    )
    
    @field_validator('timestamp')
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware"""
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
                "event_type": "registration_attempt",
                "user_id": "user_12345",
                "email": "john.doe@example.com",
                "timestamp": "2025-10-11T14:30:00Z",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "success": True,
                "validation_errors": [],
                "security_flags": ["verified_email_domain"]
            }
        }


class WebSocketRegistrationMessage(BaseModel):
    """
    WebSocket message wrapper for registration events
    
    Attributes:
        message_type: Type of WebSocket message
        event_data: Registration event details
        admin_notification: Whether to notify administrators
        requires_review: Whether manual review is required
    
    Example:
        >>> message = WebSocketRegistrationMessage(
        ...     message_type="registration_event",
        ...     event_data=registration_event,
        ...     admin_notification=False,
        ...     requires_review=False
        ... )
    """
    message_type: RegistrationMessageType = Field(
        ...,
        description="Type of WebSocket message"
    )
    event_data: RegistrationEvent = Field(
        ...,
        description="Registration event details"
    )
    admin_notification: bool = Field(
        default=False,
        description="Whether to notify administrators"
    )
    requires_review: bool = Field(
        default=False,
        description="Whether manual review is required"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "message_type": "registration_event",
                "event_data": {
                    "event_type": "registration_attempt",
                    "user_id": "user_12345",
                    "email": "john@example.com",
                    "timestamp": "2025-10-11T14:30:00Z",
                    "ip_address": "192.168.1.100",
                    "user_agent": "Mozilla/5.0",
                    "success": True,
                    "validation_errors": [],
                    "security_flags": []
                },
                "admin_notification": False,
                "requires_review": False
            }
        }

