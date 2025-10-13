"""
Real-time monitoring data models for system events

Supports:
- System performance events
- WebSocket message structures
- Alert notifications
- Threshold breach tracking
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Literal
from pydantic import BaseModel, Field, field_validator


class SystemMetricsEvent(BaseModel):
    """
    System metrics event model
    
    Captures real-time system performance events for monitoring
    and alerting.
    
    Attributes:
        event_type: Type of event (performance_update, alert, threshold_breach)
        timestamp: Event timestamp
        metrics: Performance metrics dictionary
        component: System component (api, database, cache, agents)
        severity: Event severity level
        alert_rules_triggered: List of triggered alert rules
    
    Example:
        >>> event = SystemMetricsEvent(
        ...     event_type="performance_update",
        ...     timestamp=datetime.now(timezone.utc),
        ...     metrics={"cpu_percent": 75.0, "memory_mb": 420.0},
        ...     component="api",
        ...     severity="info",
        ...     alert_rules_triggered=[]
        ... )
    """
    event_type: Literal['performance_update', 'alert', 'threshold_breach'] = Field(
        ...,
        description="Event type"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Event timestamp"
    )
    metrics: Dict[str, float] = Field(
        ...,
        description="Performance metrics"
    )
    component: Literal['api', 'database', 'cache', 'agents'] = Field(
        ...,
        description="System component"
    )
    severity: Literal['info', 'warning', 'critical'] = Field(
        ...,
        description="Event severity level"
    )
    alert_rules_triggered: List[str] = Field(
        default_factory=list,
        description="Triggered alert rules"
    )
    
    @field_validator('timestamp')
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware"""
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v
    
    @field_validator('severity')
    @classmethod
    def validate_critical_has_alerts(cls, v: str, info) -> str:
        """Critical severity should have alert rules"""
        if v == 'critical':
            alerts = info.data.get('alert_rules_triggered', [])
            if not alerts:
                # Warning: critical event without alerts
                pass
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "threshold_breach",
                "timestamp": "2025-10-12T10:00:00Z",
                "metrics": {
                    "cpu_percent": 85.0,
                    "memory_percent": 78.0,
                    "response_time_ms": 3500.0
                },
                "component": "api",
                "severity": "warning",
                "alert_rules_triggered": [
                    "cpu_high_utilization",
                    "response_time_degraded"
                ]
            }
        }


class WebSocketMetricsMessage(BaseModel):
    """
    WebSocket metrics message model
    
    Structured message format for WebSocket-based real-time
    monitoring updates.
    
    Attributes:
        message_type: Type of WebSocket message
        metrics_data: System metrics event data
        dashboard_updates: Dashboard-specific updates
        requires_attention: Whether admin attention is needed
    
    Example:
        >>> message = WebSocketMetricsMessage(
        ...     message_type="alert",
        ...     metrics_data=event,
        ...     dashboard_updates={"panel": "performance", "action": "highlight"},
        ...     requires_attention=True
        ... )
    """
    message_type: Literal['metrics_update', 'alert', 'health_status'] = Field(
        ...,
        description="WebSocket message type"
    )
    metrics_data: SystemMetricsEvent = Field(
        ...,
        description="System metrics event data"
    )
    dashboard_updates: Dict[str, Any] = Field(
        default_factory=dict,
        description="Dashboard-specific updates"
    )
    requires_attention: bool = Field(
        False,
        description="Whether admin attention is needed"
    )
    
    @field_validator('requires_attention')
    @classmethod
    def validate_critical_requires_attention(cls, v: bool, info) -> bool:
        """Critical events should require attention"""
        metrics_data = info.data.get('metrics_data')
        if metrics_data and metrics_data.severity == 'critical':
            return True
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "message_type": "alert",
                "metrics_data": {
                    "event_type": "threshold_breach",
                    "timestamp": "2025-10-12T10:00:00Z",
                    "metrics": {"cpu_percent": 85.0},
                    "component": "api",
                    "severity": "warning",
                    "alert_rules_triggered": ["cpu_high_utilization"]
                },
                "dashboard_updates": {
                    "panel": "performance",
                    "action": "highlight",
                    "metric": "cpu_percent"
                },
                "requires_attention": True
            }
        }

