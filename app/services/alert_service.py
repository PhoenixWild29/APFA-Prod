"""
Alert service for real-time notification management

Handles:
- Alert message queuing
- WebSocket broadcasting
- Message persistence for disconnected clients
"""
import json
from typing import List, Dict, Any
from datetime import datetime, timezone


class AlertService:
    """
    Alert notification service
    
    Manages alert publishing and delivery to WebSocket clients.
    """
    
    def __init__(self):
        self.alert_queue: List[Dict[str, Any]] = []
        self.max_queue_size = 1000
    
    async def publish_alert(self, alert_data: Dict[str, Any]):
        """
        Publish alert to all subscribed clients
        
        Args:
            alert_data: Alert message data
        """
        # Add to queue for disconnected clients
        self.alert_queue.append(alert_data)
        
        # Trim queue if too large
        if len(self.alert_queue) > self.max_queue_size:
            self.alert_queue = self.alert_queue[-self.max_queue_size:]
    
    def get_recent_alerts(self, count: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent alerts for newly connected clients
        
        Args:
            count: Number of recent alerts to retrieve
        
        Returns:
            List of recent alert messages
        """
        return self.alert_queue[-count:]
    
    def clear_old_alerts(self, before_timestamp: str):
        """
        Clear alerts older than specified timestamp
        
        Args:
            before_timestamp: ISO format timestamp
        """
        self.alert_queue = [
            alert for alert in self.alert_queue
            if alert.get('timestamp', '') >= before_timestamp
        ]


# Global alert service instance
alert_service = AlertService()

