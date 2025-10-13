"""
Registration Monitoring Service

Provides real-time registration metrics and alerts for
administrative dashboards via Server-Sent Events.
"""
import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Global state for registration metrics (in production, use Redis)
registration_metrics = {
    "total_registrations": 0,
    "successful_registrations": 0,
    "failed_attempts": 0,
    "conversion_rate": 0.0,
    "last_updated": datetime.now(timezone.utc).isoformat(),
}

# Alert queues
validation_failure_alerts = []
security_alerts = []


def update_registration_metrics(success: bool, failure_reason: str = None):
    """
    Update registration metrics (called from registration endpoint)
    
    Args:
        success: Whether registration was successful
        failure_reason: Optional reason for failure
    """
    global registration_metrics
    
    registration_metrics["total_registrations"] += 1
    
    if success:
        registration_metrics["successful_registrations"] += 1
    else:
        registration_metrics["failed_attempts"] += 1
        
        # Add to validation failure alerts
        if failure_reason:
            validation_failure_alerts.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "reason": failure_reason,
                "type": "validation_failure"
            })
    
    # Calculate conversion rate
    total = registration_metrics["total_registrations"]
    successful = registration_metrics["successful_registrations"]
    registration_metrics["conversion_rate"] = (successful / total * 100) if total > 0 else 0.0
    registration_metrics["last_updated"] = datetime.now(timezone.utc).isoformat()


def add_security_alert(alert_type: str, details: Dict[str, Any]):
    """
    Add security alert for suspicious registration activity
    
    Args:
        alert_type: Type of security alert
        details: Alert details
    """
    security_alerts.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "alert_type": alert_type,
        "details": details,
        "severity": "high" if alert_type in ["potential_attack", "brute_force"] else "medium"
    })


async def registration_event_stream():
    """
    Asynchronous generator for Server-Sent Events
    
    Yields registration metrics and alerts every second
    for real-time administrative monitoring.
    """
    logger.info("Starting registration monitoring SSE stream")
    
    try:
        while True:
            # Prepare event data
            event_data = {
                "type": "metrics_update",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metrics": registration_metrics.copy(),
            }
            
            # Send metrics update
            yield f"data: {json.dumps(event_data)}\n\n"
            
            # Send validation failure alerts (if any)
            while validation_failure_alerts:
                alert = validation_failure_alerts.pop(0)
                alert_data = {
                    "type": "validation_failure",
                    "timestamp": alert["timestamp"],
                    "details": alert
                }
                yield f"data: {json.dumps(alert_data)}\n\n"
            
            # Send security alerts (if any)
            while security_alerts:
                alert = security_alerts.pop(0)
                alert_data = {
                    "type": "security_alert",
                    "timestamp": alert["timestamp"],
                    "details": alert
                }
                yield f"data: {json.dumps(alert_data)}\n\n"
            
            # Wait 1 second before next update
            await asyncio.sleep(1)
    
    except asyncio.CancelledError:
        logger.info("SSE stream cancelled (client disconnected)")
    except Exception as e:
        logger.error(f"Error in registration event stream: {e}")


def get_current_metrics() -> Dict[str, Any]:
    """Get current registration metrics snapshot"""
    return registration_metrics.copy()


def reset_metrics():
    """Reset metrics (for testing or periodic resets)"""
    global registration_metrics
    registration_metrics = {
        "total_registrations": 0,
        "successful_registrations": 0,
        "failed_attempts": 0,
        "conversion_rate": 0.0,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }

