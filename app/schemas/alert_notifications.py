"""
Alert notification schemas for WebSocket delivery
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Literal
from datetime import datetime


class AlertMessage(BaseModel):
    """
    Alert message for WebSocket delivery
    
    Structured notification for critical system events.
    
    Attributes:
        message_type: Type of alert message
        timestamp: Alert timestamp
        severity_level: Alert severity (critical, warning, info)
        affected_component: System component affected
        error_details: Detailed error information
        diagnostic_data: Additional diagnostic context
        escalation_required: Whether escalation is needed
    
    Example:
        >>> alert = AlertMessage(
        ...     message_type="performance_degradation",
        ...     severity_level="warning",
        ...     affected_component="llm_inference",
        ...     error_details={"message": "Response time exceeding threshold"},
        ...     diagnostic_data={"current_ms": 3500, "threshold_ms": 3000}
        ... )
    """
    message_type: Literal[
        'performance_degradation',
        'security_incident',
        'system_error',
        'circuit_breaker_state_change',
        'resource_exhaustion'
    ] = Field(..., description="Alert message type")
    
    timestamp: str = Field(
        ...,
        description="Alert timestamp (ISO format)"
    )
    
    severity_level: Literal['critical', 'warning', 'info'] = Field(
        ...,
        description="Alert severity level"
    )
    
    affected_component: str = Field(
        ...,
        description="System component affected"
    )
    
    error_details: Dict[str, Any] = Field(
        ...,
        description="Detailed error information"
    )
    
    diagnostic_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional diagnostic context"
    )
    
    escalation_required: bool = Field(
        False,
        description="Whether escalation is needed"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "message_type": "performance_degradation",
                "timestamp": "2025-10-12T10:00:00Z",
                "severity_level": "warning",
                "affected_component": "llm_inference",
                "error_details": {
                    "message": "Response time exceeding threshold",
                    "threshold_ms": 3000,
                    "current_ms": 3500
                },
                "diagnostic_data": {
                    "endpoint": "/generate-advice",
                    "user_count": 5,
                    "queue_depth": 12
                },
                "escalation_required": False
            }
        }

