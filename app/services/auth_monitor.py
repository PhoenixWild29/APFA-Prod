"""
Authentication Monitoring Service

Provides real-time authentication metrics and security alerts
for administrative dashboards via Server-Sent Events.
"""
import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Global state for authentication metrics
auth_metrics = {
    "total_auth_attempts": 0,
    "successful_logins": 0,
    "failed_attempts": 0,
    "success_rate": 0.0,
    "active_sessions": 0,
    "last_updated": datetime.now(timezone.utc).isoformat(),
}

# Security alerts queue
auth_security_alerts = []


def update_auth_metrics(success: bool, failure_reason: str = None):
    """Update authentication metrics"""
    global auth_metrics
    
    auth_metrics["total_auth_attempts"] += 1
    
    if success:
        auth_metrics["successful_logins"] += 1
        auth_metrics["active_sessions"] += 1
    else:
        auth_metrics["failed_attempts"] += 1
        
        # Add security alert for failures
        if failure_reason:
            auth_security_alerts.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "failed_login",
                "reason": failure_reason,
                "severity": "medium"
            })
    
    # Calculate success rate
    total = auth_metrics["total_auth_attempts"]
    successful = auth_metrics["successful_logins"]
    auth_metrics["success_rate"] = (successful / total * 100) if total > 0 else 0.0
    auth_metrics["last_updated"] = datetime.now(timezone.utc).isoformat()


async def auth_event_stream():
    """Asynchronous generator for SSE authentication events"""
    logger.info("Starting auth monitoring SSE stream")
    
    try:
        while True:
            # Send metrics update
            event_data = {
                "metric_type": "auth_metrics",
                "value": auth_metrics.copy(),
                "trend": "stable",  # Could calculate trend from historical data
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            yield f"data: {json.dumps(event_data)}\n\n"
            
            # Send security alerts (if any)
            while auth_security_alerts:
                alert = auth_security_alerts.pop(0)
                alert_data = {
                    "metric_type": "security_alert",
                    "value": alert,
                    "timestamp": alert["timestamp"]
                }
                yield f"data: {json.dumps(alert_data)}\n\n"
            
            # Wait 1 second before next update
            await asyncio.sleep(1)
    
    except asyncio.CancelledError:
        logger.info("Auth SSE stream cancelled")
    except Exception as e:
        logger.error(f"Error in auth event stream: {e}")

