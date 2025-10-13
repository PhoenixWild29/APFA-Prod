"""
Upload progress tracking service

Manages real-time progress updates for file uploads
"""
import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Set
from fastapi import WebSocket

# Active upload connections (upload_id -> set of websockets)
upload_connections: Dict[str, Set[WebSocket]] = {}


async def connect_upload_progress(upload_id: str, websocket: WebSocket):
    """
    Connect websocket to upload progress tracking
    
    Args:
        upload_id: Upload identifier
        websocket: WebSocket connection
    """
    await websocket.accept()
    
    if upload_id not in upload_connections:
        upload_connections[upload_id] = set()
    
    upload_connections[upload_id].add(websocket)


def disconnect_upload_progress(upload_id: str, websocket: WebSocket):
    """
    Disconnect websocket from upload progress
    
    Args:
        upload_id: Upload identifier
        websocket: WebSocket connection
    """
    if upload_id in upload_connections:
        upload_connections[upload_id].discard(websocket)
        
        # Clean up if no more connections
        if not upload_connections[upload_id]:
            del upload_connections[upload_id]


async def broadcast_upload_progress(upload_id: str, progress_data: dict):
    """
    Broadcast progress update to all connections for an upload
    
    Args:
        upload_id: Upload identifier
        progress_data: Progress update data
    """
    if upload_id not in upload_connections:
        return
    
    message = json.dumps(progress_data)
    disconnected = []
    
    for websocket in upload_connections[upload_id]:
        try:
            await websocket.send_text(message)
        except Exception as e:
            print(f"Error broadcasting to WebSocket: {e}")
            disconnected.append(websocket)
    
    # Remove disconnected websockets
    for ws in disconnected:
        disconnect_upload_progress(upload_id, ws)


async def simulate_upload_progress(upload_id: str, total_bytes: int):
    """
    Simulate upload progress updates (for testing)
    
    Args:
        upload_id: Upload identifier
        total_bytes: Total file size
    """
    stages = [
        ('initializing', 5),
        ('uploading', 40),
        ('validating', 60),
        ('scanning', 80),
        ('processing', 95),
        ('completed', 100)
    ]
    
    for stage, percentage in stages:
        progress_data = {
            "upload_id": upload_id,
            "percentage_complete": percentage,
            "current_stage": stage,
            "estimated_completion_time": None if stage == "completed" else "30s",
            "bytes_uploaded": int(total_bytes * percentage / 100),
            "total_bytes": total_bytes,
            "upload_speed_mbps": 5.0,
            "status": f"{stage.capitalize()} in progress...",
            "error_conditions": [],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await broadcast_upload_progress(upload_id, progress_data)
        
        if stage != "completed":
            await asyncio.sleep(2)  # Simulate processing time


def get_active_connections_count(upload_id: str) -> int:
    """Get number of active connections for an upload"""
    return len(upload_connections.get(upload_id, set()))

