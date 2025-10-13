"""
Document retrieval monitoring service

Provides real-time metrics for search performance and system health
"""
import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Global retrieval metrics
retrieval_metrics = {
    "total_searches": 0,
    "successful_searches": 0,
    "failed_searches": 0,
    "avg_search_latency_ms": 0.0,
    "p95_search_latency_ms": 0.0,
    "p99_search_latency_ms": 0.0,
    "cache_hit_rate": 0.0,
    "faiss_index_utilization": 0.0,
    "query_volume_per_minute": 0.0,
    "last_updated": datetime.now(timezone.utc).isoformat(),
}


def update_retrieval_metrics(
    search_latency_ms: float,
    cache_hit: bool,
    success: bool
):
    """Update retrieval performance metrics"""
    global retrieval_metrics
    
    retrieval_metrics["total_searches"] += 1
    
    if success:
        retrieval_metrics["successful_searches"] += 1
    else:
        retrieval_metrics["failed_searches"] += 1
    
    # Update latency (simple average for MVP)
    current_avg = retrieval_metrics["avg_search_latency_ms"]
    total = retrieval_metrics["total_searches"]
    retrieval_metrics["avg_search_latency_ms"] = (
        (current_avg * (total - 1) + search_latency_ms) / total
    )
    
    # Update cache hit rate
    if cache_hit:
        current_rate = retrieval_metrics["cache_hit_rate"]
        retrieval_metrics["cache_hit_rate"] = (
            (current_rate * (total - 1) + 100.0) / total
        )
    else:
        current_rate = retrieval_metrics["cache_hit_rate"]
        retrieval_metrics["cache_hit_rate"] = (
            current_rate * (total - 1) / total
        )
    
    retrieval_metrics["last_updated"] = datetime.now(timezone.utc).isoformat()


async def retrieval_event_stream():
    """SSE event stream for retrieval monitoring"""
    logger.info("Starting retrieval monitoring SSE stream")
    
    try:
        while True:
            # Prepare monitoring data
            event_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metric_type": "retrieval_performance",
                "metrics": retrieval_metrics.copy(),
                "optimization_recommendations": [
                    "Cache hit rate good" if retrieval_metrics["cache_hit_rate"] > 80 else "Consider increasing cache size",
                    "Search latency optimal" if retrieval_metrics["avg_search_latency_ms"] < 100 else "Review FAISS index optimization"
                ]
            }
            
            yield f"data: {json.dumps(event_data)}\n\n"
            
            await asyncio.sleep(1)  # 1-second intervals
    
    except asyncio.CancelledError:
        logger.info("Retrieval monitoring SSE stream cancelled")
    except Exception as e:
        logger.error(f"Error in retrieval event stream: {e}")

