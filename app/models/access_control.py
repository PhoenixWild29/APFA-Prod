"""
Access Control Request and Decision Models

Provides structured data models for handling access control
requests and decisions with audit trails.
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Literal
from pydantic import BaseModel, Field, field_validator, IPvAnyAddress


class AccessRequest(BaseModel):
    """
    Access control request data model
    
    Captures access requests with context and metadata for
    permission checks and security auditing.
    
    Attributes:
        user_id: User identifier making the request
        resource: Resource being accessed
        action: Action being attempted
        context: Request context (flexible key-value pairs)
        timestamp: Request timestamp
        ip_address: Client IP address
        user_agent: Client user agent string
    
    Example:
        >>> request = AccessRequest(
        ...     user_id="user_123",
        ...     resource="documents",
        ...     action="read",
        ...     context={"document_id": "doc_456", "department": "finance"},
        ...     ip_address="192.168.1.100",
        ...     user_agent="Mozilla/5.0..."
        ... )
    """
    user_id: str = Field(
        ...,
        description="User identifier making the request",
        min_length=1,
        max_length=255
    )
    resource: str = Field(
        ...,
        description="Resource being accessed",
        min_length=1,
        max_length=255
    )
    action: str = Field(
        ...,
        description="Action being attempted",
        min_length=1,
        max_length=100
    )
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Request context (flexible key-value pairs)",
        examples=[{
            "document_id": "doc_12345",
            "department": "finance",
            "sensitivity_level": "high",
            "request_source": "web_ui"
        }]
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Request timestamp"
    )
    ip_address: str = Field(
        ...,
        description="Client IP address",
        max_length=45  # IPv6 max length
    )
    user_agent: str = Field(
        ...,
        description="Client user agent string",
        max_length=500
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
                "user_id": "user_550e8400-e29b-41d4-a716-446655440000",
                "resource": "documents",
                "action": "read",
                "context": {
                    "document_id": "doc_12345",
                    "department": "financial_services",
                    "sensitivity_level": "high"
                },
                "timestamp": "2025-10-11T14:30:00Z",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        }


class AccessDecision(BaseModel):
    """
    Access control decision data model
    
    Records access control decisions with audit trails,
    applied policies, and reasoning.
    
    Attributes:
        request_id: Unique request identifier
        user_id: User identifier
        resource: Resource being accessed
        action: Action attempted
        decision: Access decision (allow or deny)
        reason: Reason for the decision
        applied_policies: List of policies applied
        timestamp: Decision timestamp
        decision_metadata: Additional decision metadata
    
    Example:
        >>> decision = AccessDecision(
        ...     request_id="req_123",
        ...     user_id="user_456",
        ...     resource="documents",
        ...     action="read",
        ...     decision="allow",
        ...     reason="User has required permissions",
        ...     applied_policies=["policy_doc_read", "policy_user_active"]
        ... )
    """
    request_id: str = Field(
        ...,
        description="Unique request identifier",
        min_length=1,
        max_length=255
    )
    user_id: str = Field(
        ...,
        description="User identifier",
        min_length=1,
        max_length=255
    )
    resource: str = Field(
        ...,
        description="Resource being accessed",
        min_length=1,
        max_length=255
    )
    action: str = Field(
        ...,
        description="Action attempted",
        min_length=1,
        max_length=100
    )
    decision: Literal['allow', 'deny'] = Field(
        ...,
        description="Access decision (allow or deny)"
    )
    reason: str = Field(
        ...,
        description="Reason for the decision",
        max_length=1000
    )
    applied_policies: List[str] = Field(
        default_factory=list,
        description="List of policies applied in decision"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Decision timestamp"
    )
    decision_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional decision metadata",
        examples=[{
            "evaluation_time_ms": 15,
            "cache_hit": False,
            "policy_version": "1.2.3",
            "decision_confidence": 1.0
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
                "request_id": "req_550e8400-e29b-41d4-a716-446655440000",
                "user_id": "user_12345",
                "resource": "documents",
                "action": "read",
                "decision": "allow",
                "reason": "User has 'documents:read' permission and document is in user's department",
                "applied_policies": [
                    "policy_rbac_check",
                    "policy_department_access",
                    "policy_user_active"
                ],
                "timestamp": "2025-10-11T14:30:00Z",
                "decision_metadata": {
                    "evaluation_time_ms": 12,
                    "cache_hit": False,
                    "policy_version": "2.1.0",
                    "decision_confidence": 1.0,
                    "risk_score": 0.1
                }
            }
        }

