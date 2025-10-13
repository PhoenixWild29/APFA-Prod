"""
Monitoring event schemas for real-time dashboards
"""
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class RegistrationMetrics(BaseModel):
    """Registration success rate metrics"""
    total_registrations: int = Field(..., description="Total registration attempts")
    successful_registrations: int = Field(..., description="Successful registrations")
    failed_attempts: int = Field(..., description="Failed registration attempts")
    conversion_rate: float = Field(..., description="Success conversion rate percentage")
    last_updated: str = Field(..., description="Last update timestamp")


class ValidationFailureAlert(BaseModel):
    """Validation failure alert"""
    timestamp: str = Field(..., description="Alert timestamp")
    reason: str = Field(..., description="Failure reason")
    type: str = Field(..., description="Alert type")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")


class SecurityAlert(BaseModel):
    """Security alert"""
    timestamp: str = Field(..., description="Alert timestamp")
    alert_type: str = Field(..., description="Type of security alert")
    severity: str = Field(..., description="Alert severity level")
    details: Dict[str, Any] = Field(..., description="Alert details")

