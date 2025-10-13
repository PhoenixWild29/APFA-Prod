"""
RBAC Event Tracking and Real-Time Messaging Models

Provides comprehensive auditing and real-time monitoring of RBAC activities.
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class RBACEventType(str, Enum):
    """RBAC event types"""
    ROLE_ASSIGNED = "role_assigned"
    PERMISSION_GRANTED = "permission_granted"
    ACCESS_DENIED = "access_denied"
    ROLE_MODIFIED = "role_modified"


class SecurityImpactLevel(str, Enum):
    """Security impact levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class WebSocketMessageType(str, Enum):
    """WebSocket message types for RBAC"""
    RBAC_EVENT = "rbac_event"
    ACCESS_VIOLATION = "access_violation"
    ROLE_CHANGE = "role_change"


class RBACEvent(BaseModel):
    """
    RBAC event data model for auditing and monitoring
    
    Tracks role assignments, permission changes, and access control
    decisions for security monitoring and compliance.
    
    Attributes:
        event_type: Type of RBAC event
        user_id: User identifier
        role_id: Optional role identifier
        permission_id: Optional permission identifier
        timestamp: Event timestamp
        performed_by: User ID who performed the action
        resource_accessed: Resource that was accessed
        action_attempted: Action that was attempted
        success: Whether the action was successful
        audit_metadata: Additional audit metadata
    
    Example:
        >>> event = RBACEvent(
        ...     event_type="role_assigned",
        ...     user_id="user_123",
        ...     role_id="role_advisor",
        ...     performed_by="admin_user",
        ...     resource_accessed="roles",
        ...     action_attempted="assign",
        ...     success=True
        ... )
    """
    event_type: RBACEventType = Field(
        ...,
        description="Type of RBAC event"
    )
    user_id: str = Field(
        ...,
        description="User identifier",
        min_length=1,
        max_length=255
    )
    role_id: Optional[str] = Field(
        None,
        description="Optional role identifier",
        max_length=255
    )
    permission_id: Optional[str] = Field(
        None,
        description="Optional permission identifier",
        max_length=255
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Event timestamp"
    )
    performed_by: str = Field(
        ...,
        description="User ID who performed the action",
        min_length=1,
        max_length=255
    )
    resource_accessed: str = Field(
        ...,
        description="Resource that was accessed",
        min_length=1,
        max_length=255
    )
    action_attempted: str = Field(
        ...,
        description="Action that was attempted",
        min_length=1,
        max_length=100
    )
    success: bool = Field(
        ...,
        description="Whether the action was successful"
    )
    audit_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional audit metadata",
        examples=[{
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0...",
            "session_id": "session_123",
            "failure_reason": "Insufficient permissions"
        }]
    )
    
    @field_validator('timestamp')
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware"""
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "role_assigned",
                "user_id": "user_550e8400-e29b-41d4-a716-446655440000",
                "role_id": "role_advisor",
                "permission_id": None,
                "timestamp": "2025-10-11T14:30:00Z",
                "performed_by": "admin_user",
                "resource_accessed": "roles",
                "action_attempted": "assign",
                "success": True,
                "audit_metadata": {
                    "ip_address": "192.168.1.100",
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "session_id": "session_12345",
                    "reason": "User promotion to advisor"
                }
            }
        }


class WebSocketRBACMessage(BaseModel):
    """
    WebSocket message wrapper for RBAC events
    
    Provides real-time monitoring of RBAC activities with
    security impact assessment and review flags.
    
    Attributes:
        message_type: Type of WebSocket message
        event_data: RBAC event details
        security_impact: Security impact level
        requires_review: Whether event requires manual review
    
    Example:
        >>> message = WebSocketRBACMessage(
        ...     message_type="rbac_event",
        ...     event_data=rbac_event,
        ...     security_impact="medium",
        ...     requires_review=False
        ... )
    """
    message_type: WebSocketMessageType = Field(
        ...,
        description="Type of WebSocket message"
    )
    event_data: RBACEvent = Field(
        ...,
        description="RBAC event details"
    )
    security_impact: SecurityImpactLevel = Field(
        ...,
        description="Security impact level"
    )
    requires_review: bool = Field(
        ...,
        description="Whether event requires manual review"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "message_type": "rbac_event",
                "event_data": {
                    "event_type": "role_assigned",
                    "user_id": "user_12345",
                    "role_id": "role_advisor",
                    "timestamp": "2025-10-11T14:30:00Z",
                    "performed_by": "admin_user",
                    "resource_accessed": "roles",
                    "action_attempted": "assign",
                    "success": True,
                    "audit_metadata": {"reason": "Promotion"}
                },
                "security_impact": "medium",
                "requires_review": False
            }
        }

