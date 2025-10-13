"""
Alert management data models for system monitoring

Provides:
- Alert rule definitions
- Alert event tracking
- Escalation workflow support
- Diagnostic data capture
"""
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, field_validator


class AlertRule(BaseModel):
    """
    Alert rule definition
    
    Defines conditions and thresholds for triggering system alerts.
    
    Attributes:
        rule_id: Unique rule identifier
        name: Human-readable rule name
        condition: Alert condition expression
        threshold: Alert threshold value
        severity: Alert severity level
        enabled: Whether rule is active
        notification_channels: Notification delivery channels
        cooldown_seconds: Minimum time between alerts
    
    Example:
        >>> rule = AlertRule(
        ...     rule_id="cpu_high_alert",
        ...     name="High CPU Utilization",
        ...     condition="cpu_utilization_percent > threshold",
        ...     threshold=80.0,
        ...     severity="warning",
        ...     enabled=True,
        ...     notification_channels=["email", "slack"],
        ...     cooldown_seconds=300
        ... )
    """
    rule_id: str = Field(
        ...,
        description="Unique rule identifier",
        min_length=1,
        max_length=100
    )
    name: str = Field(
        ...,
        description="Human-readable rule name",
        min_length=1,
        max_length=255
    )
    condition: str = Field(
        ...,
        description="Alert condition expression",
        min_length=1
    )
    threshold: float = Field(
        ...,
        description="Alert threshold value"
    )
    severity: Literal['info', 'warning', 'critical'] = Field(
        ...,
        description="Alert severity level"
    )
    enabled: bool = Field(
        True,
        description="Whether rule is active"
    )
    notification_channels: List[str] = Field(
        default_factory=list,
        description="Notification delivery channels"
    )
    cooldown_seconds: int = Field(
        300,
        description="Minimum time between alerts (default 5 minutes)",
        ge=0
    )
    
    @field_validator('cooldown_seconds')
    @classmethod
    def validate_non_negative_cooldown(cls, v: int) -> int:
        """Ensure cooldown is non-negative"""
        if v < 0:
            raise ValueError("Cooldown must be non-negative")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "rule_id": "cpu_high_alert",
                "name": "High CPU Utilization",
                "condition": "cpu_utilization_percent > threshold",
                "threshold": 80.0,
                "severity": "warning",
                "enabled": True,
                "notification_channels": ["email", "slack", "pagerduty"],
                "cooldown_seconds": 300
            }
        }


class AlertEvent(BaseModel):
    """
    Alert event tracking
    
    Records alert occurrences with diagnostic data and
    escalation tracking.
    
    Attributes:
        alert_id: Unique alert identifier
        rule_id: Associated rule identifier
        triggered_at: Alert trigger timestamp
        resolved_at: Alert resolution timestamp (if resolved)
        severity: Alert severity level
        message: Alert message
        affected_components: List of affected system components
        diagnostic_data: Diagnostic information
        escalation_level: Current escalation level
    
    Example:
        >>> alert = AlertEvent(
        ...     alert_id="alert_12345",
        ...     rule_id="cpu_high_alert",
        ...     triggered_at=datetime.now(timezone.utc),
        ...     severity="warning",
        ...     message="CPU utilization exceeded 80%",
        ...     affected_components=["api_server"],
        ...     diagnostic_data={"cpu_percent": 85.0, "threshold": 80.0},
        ...     escalation_level=0
        ... )
    """
    alert_id: str = Field(
        ...,
        description="Unique alert identifier",
        min_length=1,
        max_length=100
    )
    rule_id: str = Field(
        ...,
        description="Associated rule identifier",
        min_length=1,
        max_length=100
    )
    triggered_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Alert trigger timestamp"
    )
    resolved_at: Optional[datetime] = Field(
        None,
        description="Alert resolution timestamp"
    )
    severity: Literal['info', 'warning', 'critical'] = Field(
        ...,
        description="Alert severity level"
    )
    message: str = Field(
        ...,
        description="Alert message",
        min_length=1
    )
    affected_components: List[str] = Field(
        default_factory=list,
        description="Affected system components"
    )
    diagnostic_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Diagnostic information"
    )
    escalation_level: int = Field(
        0,
        description="Current escalation level",
        ge=0
    )
    
    @field_validator('triggered_at', 'resolved_at')
    @classmethod
    def validate_timezone_aware(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure timestamps are timezone-aware"""
        if v and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v
    
    @field_validator('escalation_level')
    @classmethod
    def validate_non_negative_escalation(cls, v: int) -> int:
        """Ensure escalation level is non-negative"""
        if v < 0:
            raise ValueError("Escalation level must be non-negative")
        return v
    
    @field_validator('resolved_at')
    @classmethod
    def validate_resolution_after_trigger(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Ensure resolved_at is after triggered_at"""
        if v:
            triggered = info.data.get('triggered_at')
            if triggered and v < triggered:
                raise ValueError("resolved_at must be after triggered_at")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "alert_id": "alert_550e8400",
                "rule_id": "cpu_high_alert",
                "triggered_at": "2025-10-12T10:00:00Z",
                "resolved_at": None,
                "severity": "warning",
                "message": "CPU utilization exceeded 80% threshold",
                "affected_components": ["api_server", "worker_1"],
                "diagnostic_data": {
                    "cpu_percent": 85.0,
                    "threshold": 80.0,
                    "duration_seconds": 120
                },
                "escalation_level": 0
            }
        }

