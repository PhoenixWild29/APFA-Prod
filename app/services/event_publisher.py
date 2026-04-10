"""
Event Publisher Service

Publishes events to Redis Pub/Sub for real-time WebSocket broadcasting
"""

import json
import logging
from typing import Any, Dict, Optional

# aioredis 2.0.1 is archived/broken on Python 3.11+ (duplicate base class
# TimeoutError). Use redis.asyncio from redis-py via namespace alias — the
# API is identical so downstream code (from_url, publish, close) works
# unchanged.
import redis.asyncio as aioredis

from config import settings

logger = logging.getLogger(__name__)


class EventPublisher:
    """
    Publishes events to Redis Pub/Sub channels for WebSocket broadcasting
    """

    def __init__(self, redis_url: Optional[str] = None):
        # Default to the configured Redis URL from settings (which defaults
        # to the Docker hostname "redis", not localhost). Callers can still
        # override by passing an explicit URL.
        self.redis_url = redis_url or settings.redis_url
        self.redis_client = None

    async def connect(self):
        """Connect to Redis"""
        if not self.redis_client:
            self.redis_client = await aioredis.from_url(
                self.redis_url, decode_responses=True
            )
            logger.info("EventPublisher connected to Redis")

    async def publish(self, channel: str, event: Dict[str, Any]):
        """
        Publish event to Redis channel

        Args:
            channel: Redis channel name
            event: Event data (will be JSON-serialized)
        """
        if not self.redis_client:
            await self.connect()

        try:
            message = json.dumps(event)
            await self.redis_client.publish(channel, message)
            logger.debug(
                f"Published event to {channel}: {event.get('type', 'unknown')}"
            )
        except Exception as e:
            logger.error(f"Failed to publish event to {channel}: {e}")

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("EventPublisher disconnected from Redis")


# Global event publisher instance
event_publisher = EventPublisher()
