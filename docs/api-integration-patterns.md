# API Integration Patterns for Real-Time Monitoring

**Version:** 1.0  
**Last Updated:** 2025-10-11  
**Owner:** Full-Stack Team  
**Status:** Design Specification

---

## Table of Contents

1. [Overview](#overview)
2. [WebSocket Integration](#websocket-integration)
3. [HTTP Polling Strategies](#http-polling-strategies)
4. [Hybrid Approach](#hybrid-approach)
5. [Error Handling & Retry Logic](#error-handling--retry-logic)
6. [Rate Limiting & Backpressure](#rate-limiting--backpressure)
7. [Authentication & Security](#authentication--security)
8. [Backend API Endpoints](#backend-api-endpoints)
9. [Performance Optimization](#performance-optimization)
10. [Testing Strategies](#testing-strategies)

---

## Overview

### Communication Patterns

APFA admin dashboards require real-time updates for monitoring Celery tasks. We support two communication patterns with automatic fallback:

```
┌──────────────────────────────────────────────────────┐
│         Primary: WebSocket (Socket.IO)               │
│  ┌────────────────────────────────────────────────┐  │
│  │  Pros: Real-time, bi-directional, efficient   │  │
│  │  Cons: Firewall issues, connection overhead   │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────┬────────────────────────────────────┘
                   │
                   │ Fallback on failure
                   ↓
┌──────────────────────────────────────────────────────┐
│         Fallback: HTTP Polling (REST)                │
│  ┌────────────────────────────────────────────────┐  │
│  │  Pros: Universal, simple, firewall-friendly   │  │
│  │  Cons: Higher latency, server load            │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

### Decision Matrix

| Use Case | Pattern | Rationale |
|----------|---------|-----------|
| **Task status updates** | WebSocket → Polling | Real-time important, but can tolerate 5s delay |
| **Queue depth** | Polling (10s interval) | Less critical, reduce server load |
| **Worker health** | Polling (30s interval) | Infrequent changes |
| **Batch job progress** | WebSocket → Polling | Real-time UX, but fallback acceptable |
| **Manual actions** | HTTP POST | One-off requests, no streaming needed |

---

## WebSocket Integration

### Backend Implementation (FastAPI + Socket.IO)

#### 1. Socket.IO Server Setup

```python
# backend/app/websocket.py
from socketio import AsyncServer, ASGIApp
from fastapi import FastAPI
import asyncio
import logging

logger = logging.getLogger(__name__)

# Socket.IO server
sio = AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=['http://localhost:3000', 'https://admin.apfa.io'],
    logger=True,
    engineio_logger=True,
)

# Wrap with ASGI app
socket_app = ASGIApp(sio)

# Authentication middleware
@sio.event
async def connect(sid, environ, auth):
    """Handle client connection with JWT authentication."""
    try:
        # Verify JWT token
        token = auth.get('token')
        if not token:
            logger.warning(f"[WS] Connection rejected: No token (sid={sid})")
            return False
        
        # Validate token
        payload = verify_jwt_token(token)
        user_id = payload.get('sub')
        
        # Check admin role
        user = get_user(user_id)
        if user.get('role') != 'admin':
            logger.warning(f"[WS] Connection rejected: Not admin (sid={sid}, user={user_id})")
            return False
        
        # Store user info in session
        await sio.save_session(sid, {'user_id': user_id, 'role': 'admin'})
        
        logger.info(f"[WS] Client connected: sid={sid}, user={user_id}")
        return True
    
    except Exception as e:
        logger.error(f"[WS] Connection error: {e}")
        return False

@sio.event
async def disconnect(sid):
    """Handle client disconnection."""
    session = await sio.get_session(sid)
    user_id = session.get('user_id', 'unknown')
    logger.info(f"[WS] Client disconnected: sid={sid}, user={user_id}")

# Room management
@sio.event
async def subscribe(sid, data):
    """Subscribe to specific event streams."""
    room = data.get('room')  # e.g., 'celery:tasks', 'celery:queue:embedding'
    
    if room:
        sio.enter_room(sid, room)
        logger.info(f"[WS] Client {sid} subscribed to {room}")
        await sio.emit('subscribed', {'room': room}, room=sid)

@sio.event
async def unsubscribe(sid, data):
    """Unsubscribe from event streams."""
    room = data.get('room')
    
    if room:
        sio.leave_room(sid, room)
        logger.info(f"[WS] Client {sid} unsubscribed from {room}")
```

#### 2. Task Update Broadcasting

```python
# backend/app/tasks.py (Celery signals)
from celery.signals import task_prerun, task_postrun, task_failure
import asyncio

@task_postrun.connect
def broadcast_task_update(sender=None, task_id=None, task=None, **kwargs):
    """Broadcast task status to WebSocket clients."""
    # Get task details
    task_data = {
        'id': task_id,
        'name': task.name,
        'state': 'SUCCESS',
        'queue': task.request.delivery_info.get('routing_key'),
        'worker': task.request.hostname,
        'timestamp': datetime.utcnow().isoformat(),
        'runtime': kwargs.get('retval', {}).get('runtime'),
    }
    
    # Broadcast to all clients subscribed to 'celery:tasks'
    asyncio.create_task(sio.emit(
        'task_update',
        {'type': 'task_update', 'data': task_data},
        room='celery:tasks'
    ))

@task_failure.connect
def broadcast_task_failure(sender=None, task_id=None, exception=None, **kwargs):
    """Broadcast task failure."""
    task_data = {
        'id': task_id,
        'name': sender.name,
        'state': 'FAILURE',
        'exception': str(exception),
        'timestamp': datetime.utcnow().isoformat(),
    }
    
    asyncio.create_task(sio.emit(
        'task_update',
        {'type': 'task_update', 'data': task_data},
        room='celery:tasks'
    ))
```

#### 3. Batch Job Progress Broadcasting

```python
# backend/app/tasks.py
@app.task(queue='embedding')
def embed_all_documents(delta_table_path: str = None) -> dict:
    """Orchestrate embedding with progress updates."""
    total_batches = calculate_total_batches()
    
    for i, batch in enumerate(batches):
        # Process batch
        result = embed_document_batch.apply(args=[batch, f"batch_{i:04d}"])
        
        # Broadcast progress
        progress = {
            'jobId': 'embed_job_123',
            'totalBatches': total_batches,
            'completedBatches': i + 1,
            'progress': ((i + 1) / total_batches) * 100,
            'estimatedTimeRemaining': calculate_eta(i, total_batches, start_time),
        }
        
        asyncio.create_task(sio.emit(
            'batch_progress',
            {'type': 'batch_progress', 'data': progress},
            room='celery:batch_jobs'
        ))
```

#### 4. Mount Socket.IO in FastAPI

```python
# backend/app/main.py
from fastapi import FastAPI
from .websocket import socket_app, sio

app = FastAPI()

# Mount Socket.IO
app.mount('/ws', socket_app)

@app.on_event("startup")
async def startup():
    """Start background task for queue monitoring."""
    asyncio.create_task(broadcast_queue_stats())

async def broadcast_queue_stats():
    """Periodically broadcast queue statistics."""
    while True:
        try:
            # Get queue stats from Redis
            stats = get_queue_statistics()
            
            # Broadcast to subscribed clients
            await sio.emit(
                'queue_stats',
                {'type': 'queue_stats', 'data': stats},
                room='celery:queues'
            )
            
            await asyncio.sleep(5)  # Every 5 seconds
        except Exception as e:
            logger.error(f"Error broadcasting queue stats: {e}")
            await asyncio.sleep(10)
```

---

### Frontend Implementation (React + Socket.IO Client)

#### 1. WebSocket Service

```typescript
// frontend/src/api/websocket.ts
import { io, Socket } from 'socket.io-client';

export interface WebSocketOptions {
  autoConnect?: boolean;
  reconnect?: boolean;
  reconnectAttempts?: number;
  reconnectDelay?: number;
}

class WebSocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private callbacks: Map<string, Set<(data: any) => void>> = new Map();

  connect(endpoint: string, options?: WebSocketOptions): Socket {
    const {
      autoConnect = true,
      reconnect = true,
      reconnectAttempts = 5,
      reconnectDelay = 1000,
    } = options || {};

    this.maxReconnectAttempts = reconnectAttempts;
    this.reconnectDelay = reconnectDelay;

    // Get auth token
    const token = localStorage.getItem('authToken');
    if (!token) {
      throw new Error('No authentication token found');
    }

    // Create Socket.IO connection
    this.socket = io(`${process.env.REACT_APP_WS_URL}${endpoint}`, {
      auth: { token },
      autoConnect,
      reconnection: reconnect,
      reconnectionDelay: this.reconnectDelay,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: this.maxReconnectAttempts,
      transports: ['websocket', 'polling'], // Try WebSocket first, fallback to polling
    });

    // Event handlers
    this.socket.on('connect', () => {
      console.log(`[WebSocket] Connected to ${endpoint}`);
      this.reconnectAttempts = 0;
      this.emitToCallbacks('connection:success', { endpoint });
    });

    this.socket.on('disconnect', (reason) => {
      console.log(`[WebSocket] Disconnected: ${reason}`);
      this.emitToCallbacks('connection:lost', { reason });
    });

    this.socket.on('connect_error', (error) => {
      console.error(`[WebSocket] Connection error:`, error);
      this.reconnectAttempts++;

      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        console.error('[WebSocket] Max reconnection attempts reached. Falling back to HTTP polling.');
        this.emitToCallbacks('connection:failed', { error: error.message });
        this.fallbackToPolling();
      }
    });

    this.socket.on('error', (error) => {
      console.error('[WebSocket] Error:', error);
      this.emitToCallbacks('error', { error: error.message });
    });

    return this.socket;
  }

  subscribe(room: string) {
    if (this.socket && this.socket.connected) {
      this.socket.emit('subscribe', { room });
      console.log(`[WebSocket] Subscribed to room: ${room}`);
    }
  }

  unsubscribe(room: string) {
    if (this.socket && this.socket.connected) {
      this.socket.emit('unsubscribe', { room });
      console.log(`[WebSocket] Unsubscribed from room: ${room}`);
    }
  }

  on(event: string, callback: (data: any) => void) {
    if (!this.callbacks.has(event)) {
      this.callbacks.set(event, new Set());
    }
    this.callbacks.get(event)!.add(callback);

    // Also listen on socket if connected
    if (this.socket) {
      this.socket.on(event, callback);
    }
  }

  off(event: string, callback: (data: any) => void) {
    const callbacks = this.callbacks.get(event);
    if (callbacks) {
      callbacks.delete(callback);
    }

    if (this.socket) {
      this.socket.off(event, callback);
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.callbacks.clear();
  }

  private emitToCallbacks(event: string, data: any) {
    const callbacks = this.callbacks.get(event);
    if (callbacks) {
      callbacks.forEach(callback => callback(data));
    }
  }

  private fallbackToPolling() {
    // Emit fallback event that components can listen to
    window.dispatchEvent(new CustomEvent('websocket:fallback', {
      detail: { reason: 'Max reconnection attempts exceeded' },
    }));
  }

  get connected(): boolean {
    return this.socket?.connected || false;
  }
}

export const websocketService = new WebSocketService();
```

#### 2. React Hook for WebSocket

```typescript
// frontend/src/hooks/useWebSocket.ts
import { useEffect, useState, useCallback } from 'react';
import { websocketService } from '../api/websocket';

export interface UseWebSocketOptions {
  autoConnect?: boolean;
  room?: string;
  onMessage?: (data: any) => void;
  onError?: (error: any) => void;
}

export const useWebSocket = (
  endpoint: string,
  options: UseWebSocketOptions = {}
) => {
  const { autoConnect = true, room, onMessage, onError } = options;
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!autoConnect) return;

    try {
      // Connect to WebSocket
      websocketService.connect(endpoint, {
        autoConnect: true,
        reconnect: true,
      });

      // Subscribe to room if provided
      if (room) {
        websocketService.subscribe(room);
      }

      // Listen for connection events
      websocketService.on('connection:success', () => {
        setConnected(true);
        setError(null);
      });

      websocketService.on('connection:lost', () => {
        setConnected(false);
      });

      websocketService.on('connection:failed', (data) => {
        setConnected(false);
        setError(data.error);
        onError?.(data.error);
      });

      websocketService.on('error', (data) => {
        setError(data.error);
        onError?.(data.error);
      });

      // Listen for messages based on endpoint
      const messageEvents = ['task_update', 'batch_progress', 'queue_stats'];
      messageEvents.forEach(event => {
        websocketService.on(event, (data) => {
          setMessages((prev) => [...prev, data]);
          onMessage?.(data);
        });
      });

      return () => {
        if (room) {
          websocketService.unsubscribe(room);
        }
        websocketService.disconnect();
      };
    } catch (err) {
      console.error('WebSocket connection failed:', err);
      setError(err.message);
      onError?.(err);
    }
  }, [endpoint, autoConnect, room, onMessage, onError]);

  const sendMessage = useCallback((event: string, data: any) => {
    if (websocketService.connected) {
      websocketService.socket?.emit(event, data);
    } else {
      console.warn('[WebSocket] Cannot send message: Not connected');
    }
  }, []);

  return {
    connected,
    messages,
    error,
    sendMessage,
  };
};
```

---

## HTTP Polling Strategies

### 1. Simple Interval Polling

**Use Case:** Queue statistics, worker health (non-critical updates)

```typescript
// frontend/src/hooks/usePolling.ts
import { useEffect, useRef, useState } from 'react';

export interface UsePollingOptions {
  enabled?: boolean;
  immediate?: boolean;
  onError?: (error: Error) => void;
}

export const usePolling = <T>(
  fetchFn: () => Promise<T>,
  interval: number,
  options: UsePollingOptions = {}
) => {
  const { enabled = true, immediate = true, onError } = options;
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const savedFetchFn = useRef(fetchFn);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // Update fetch function ref
  useEffect(() => {
    savedFetchFn.current = fetchFn;
  }, [fetchFn]);

  useEffect(() => {
    if (!enabled) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      return;
    }

    const executeFetch = async () => {
      setLoading(true);
      try {
        const result = await savedFetchFn.current();
        setData(result);
        setError(null);
      } catch (err) {
        const error = err as Error;
        setError(error);
        onError?.(error);
      } finally {
        setLoading(false);
      }
    };

    // Execute immediately if requested
    if (immediate) {
      executeFetch();
    }

    // Set up interval
    intervalRef.current = setInterval(executeFetch, interval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [interval, enabled, immediate, onError]);

  return { data, loading, error };
};
```

**Usage Example:**

```typescript
// Fetch queue stats every 10 seconds
const { data: queueStats, loading } = usePolling(
  async () => {
    const response = await celeryAPI.getQueueStats();
    return response.data;
  },
  10000,
  { immediate: true }
);
```

---

### 2. Adaptive Polling (Smart Interval Adjustment)

**Use Case:** Task status (high activity = faster polling, low activity = slower)

```typescript
// frontend/src/hooks/useAdaptivePolling.ts
import { useEffect, useRef, useState, useCallback } from 'react';

export interface UseAdaptivePollingOptions {
  minInterval: number; // Minimum polling interval (fast polling)
  maxInterval: number; // Maximum polling interval (slow polling)
  backoffMultiplier?: number; // Increase interval by this factor
  activityThreshold?: number; // Changes needed to decrease interval
}

export const useAdaptivePolling = <T>(
  fetchFn: () => Promise<T>,
  options: UseAdaptivePollingOptions
) => {
  const {
    minInterval,
    maxInterval,
    backoffMultiplier = 2,
    activityThreshold = 5,
  } = options;

  const [data, setData] = useState<T | null>(null);
  const [currentInterval, setCurrentInterval] = useState(minInterval);
  const [changeCount, setChangeCount] = useState(0);
  const savedFetchFn = useRef(fetchFn);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const executeFetch = useCallback(async () => {
    try {
      const newData = await savedFetchFn.current();
      
      // Compare with previous data to detect changes
      const hasChanged = JSON.stringify(newData) !== JSON.stringify(data);
      
      if (hasChanged) {
        setChangeCount(prev => prev + 1);
        
        // High activity: decrease interval (speed up polling)
        if (changeCount >= activityThreshold && currentInterval > minInterval) {
          setCurrentInterval(Math.max(minInterval, currentInterval / backoffMultiplier));
        }
      } else {
        setChangeCount(0);
        
        // Low activity: increase interval (slow down polling)
        if (currentInterval < maxInterval) {
          setCurrentInterval(Math.min(maxInterval, currentInterval * backoffMultiplier));
        }
      }
      
      setData(newData);
    } catch (error) {
      console.error('Polling error:', error);
    }
  }, [data, changeCount, activityThreshold, currentInterval, minInterval, maxInterval, backoffMultiplier]);

  useEffect(() => {
    executeFetch(); // Initial fetch

    intervalRef.current = setInterval(executeFetch, currentInterval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [currentInterval, executeFetch]);

  return { data, currentInterval };
};
```

**Usage Example:**

```typescript
// Poll tasks: Fast when active (2s), slow when idle (30s)
const { data: tasks, currentInterval } = useAdaptivePolling(
  async () => await celeryAPI.getTasks(),
  {
    minInterval: 2000,   // 2 seconds when active
    maxInterval: 30000,  // 30 seconds when idle
    activityThreshold: 3,
  }
);
```

---

### 3. Long Polling

**Use Case:** Waiting for job completion

```typescript
// frontend/src/api/celery.api.ts
export const celeryAPI = {
  /**
   * Long polling: Wait for job completion (server holds connection)
   */
  waitForJobCompletion: async (jobId: string, timeout: number = 60000): Promise<any> => {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await axios.get(`/api/admin/celery/jobs/${jobId}/wait`, {
        signal: controller.signal,
        params: { timeout: timeout / 1000 }, // Send timeout in seconds
      });
      
      clearTimeout(timeoutId);
      return response.data;
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error.name === 'AbortError') {
        // Timeout: Retry with another long poll
        return celeryAPI.waitForJobCompletion(jobId, timeout);
      }
      
      throw error;
    }
  },
};
```

**Backend Long Polling Endpoint:**

```python
# backend/app/main.py
@app.get("/api/admin/celery/jobs/{job_id}/wait")
async def wait_for_job_completion(
    job_id: str,
    timeout: int = 60,
    current_user: dict = Depends(get_current_admin)
):
    """
    Long polling endpoint: Wait for job completion or timeout.
    Server holds connection until job done or timeout reached.
    """
    start_time = time.time()
    poll_interval = 1  # Check every 1 second
    
    while time.time() - start_time < timeout:
        job = get_job_status(job_id)
        
        if job['status'] in ['completed', 'failed']:
            return job
        
        await asyncio.sleep(poll_interval)
    
    # Timeout: Return current status
    return {'status': 'pending', 'message': 'Still running'}
```

---

## Hybrid Approach (WebSocket + Polling)

### Implementation Strategy

```typescript
// frontend/src/hooks/useCeleryTasks.ts
import { useState, useEffect } from 'react';
import { useWebSocket } from './useWebSocket';
import { usePolling } from './usePolling';
import { celeryAPI } from '../api/celery.api';

export const useCeleryTasks = () => {
  const [tasks, setTasks] = useState([]);
  const [usePollingMode, setUsePollingMode] = useState(false);

  // WebSocket (primary)
  const { connected, messages } = useWebSocket('/ws/celery/tasks', {
    autoConnect: !usePollingMode,
    room: 'celery:tasks',
  });

  // HTTP Polling (fallback)
  const { data: polledTasks } = usePolling(
    async () => {
      const response = await celeryAPI.getTasks();
      return response.data;
    },
    5000, // Poll every 5 seconds
    { enabled: usePollingMode || !connected }
  );

  // Switch to polling on WebSocket failure
  useEffect(() => {
    const handleFallback = () => {
      console.log('[Hybrid] Switching to HTTP polling mode');
      setUsePollingMode(true);
    };

    window.addEventListener('websocket:fallback', handleFallback);
    return () => window.removeEventListener('websocket:fallback', handleFallback);
  }, []);

  // Update tasks from WebSocket
  useEffect(() => {
    if (connected && messages.length > 0) {
      const latestMessage = messages[messages.length - 1];
      if (latestMessage.type === 'task_update') {
        setTasks((prev) => updateTaskInArray(prev, latestMessage.data));
      }
    }
  }, [connected, messages]);

  // Update tasks from polling
  useEffect() => {
    if (usePollingMode && polledTasks) {
      setTasks(polledTasks);
    }
  }, [usePollingMode, polledTasks]);

  return {
    tasks,
    connected: !usePollingMode && connected,
    mode: usePollingMode ? 'polling' : 'websocket',
  };
};
```

---

## Error Handling & Retry Logic

### 1. Exponential Backoff

```typescript
// frontend/src/utils/retry.ts
export interface RetryOptions {
  maxRetries: number;
  initialDelay: number;
  maxDelay: number;
  backoffMultiplier: number;
  shouldRetry?: (error: any) => boolean;
}

export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  options: RetryOptions
): Promise<T> {
  const {
    maxRetries,
    initialDelay,
    maxDelay,
    backoffMultiplier,
    shouldRetry = () => true,
  } = options;

  let attempt = 0;
  let delay = initialDelay;

  while (attempt < maxRetries) {
    try {
      return await fn();
    } catch (error) {
      attempt++;

      if (attempt >= maxRetries || !shouldRetry(error)) {
        throw error;
      }

      console.warn(`[Retry] Attempt ${attempt}/${maxRetries} failed. Retrying in ${delay}ms...`);
      
      await new Promise(resolve => setTimeout(resolve, delay));
      
      // Exponential backoff
      delay = Math.min(delay * backoffMultiplier, maxDelay);
    }
  }

  throw new Error('Max retries exceeded');
}
```

**Usage:**

```typescript
// Retry API call with exponential backoff
const tasks = await retryWithBackoff(
  async () => await celeryAPI.getTasks(),
  {
    maxRetries: 3,
    initialDelay: 1000,
    maxDelay: 10000,
    backoffMultiplier: 2,
    shouldRetry: (error) => error.response?.status >= 500, // Only retry server errors
  }
);
```

---

### 2. Circuit Breaker Pattern

```typescript
// frontend/src/utils/circuitBreaker.ts
enum CircuitState {
  CLOSED = 'CLOSED',   // Normal operation
  OPEN = 'OPEN',       // Failing, reject requests
  HALF_OPEN = 'HALF_OPEN', // Testing if recovered
}

export class CircuitBreaker {
  private state: CircuitState = CircuitState.CLOSED;
  private failureCount = 0;
  private successCount = 0;
  private nextAttempt: number = Date.now();

  constructor(
    private failureThreshold: number = 5,
    private successThreshold: number = 2,
    private timeout: number = 60000 // 1 minute
  ) {}

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === CircuitState.OPEN) {
      if (Date.now() < this.nextAttempt) {
        throw new Error('Circuit breaker is OPEN');
      }
      
      // Transition to HALF_OPEN
      this.state = CircuitState.HALF_OPEN;
      console.log('[CircuitBreaker] Transitioning to HALF_OPEN');
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess() {
    this.failureCount = 0;

    if (this.state === CircuitState.HALF_OPEN) {
      this.successCount++;
      
      if (this.successCount >= this.successThreshold) {
        this.state = CircuitState.CLOSED;
        this.successCount = 0;
        console.log('[CircuitBreaker] Circuit CLOSED');
      }
    }
  }

  private onFailure() {
    this.failureCount++;
    this.successCount = 0;

    if (this.failureCount >= this.failureThreshold) {
      this.state = CircuitState.OPEN;
      this.nextAttempt = Date.now() + this.timeout;
      console.log(`[CircuitBreaker] Circuit OPEN. Will retry after ${this.timeout}ms`);
    }
  }

  getState(): CircuitState {
    return this.state;
  }
}
```

**Usage:**

```typescript
const circuitBreaker = new CircuitBreaker(5, 2, 60000);

try {
  const tasks = await circuitBreaker.execute(async () => {
    return await celeryAPI.getTasks();
  });
} catch (error) {
  if (error.message === 'Circuit breaker is OPEN') {
    console.log('Service unavailable. Using cached data.');
    // Fall back to cached data or show error message
  }
}
```

---

## Rate Limiting & Backpressure

### Frontend Rate Limiting

```typescript
// frontend/src/utils/rateLimiter.ts
export class RateLimiter {
  private queue: Array<() => Promise<any>> = [];
  private processing = 0;

  constructor(
    private maxConcurrent: number = 5,
    private minInterval: number = 200 // ms between requests
  ) {}

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      this.queue.push(async () => {
        try {
          const result = await fn();
          resolve(result);
        } catch (error) {
          reject(error);
        }
      });

      this.processQueue();
    });
  }

  private async processQueue() {
    if (this.processing >= this.maxConcurrent || this.queue.length === 0) {
      return;
    }

    this.processing++;
    const fn = this.queue.shift()!;
    
    await fn();
    
    // Wait minimum interval before next request
    await new Promise(resolve => setTimeout(resolve, this.minInterval));
    
    this.processing--;
    this.processQueue();
  }
}
```

---

## Authentication & Security

### JWT Token Management

```typescript
// frontend/src/api/auth.ts
export class AuthService {
  private static TOKEN_KEY = 'authToken';
  private static REFRESH_THRESHOLD = 5 * 60 * 1000; // 5 minutes

  static getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  static setToken(token: string) {
    localStorage.setItem(this.TOKEN_KEY, token);
  }

  static clearToken() {
    localStorage.removeItem(this.TOKEN_KEY);
  }

  static isTokenExpiringSoon(): boolean {
    const token = this.getToken();
    if (!token) return true;

    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const expiresAt = payload.exp * 1000; // Convert to ms
      const now = Date.now();

      return expiresAt - now < this.REFRESH_THRESHOLD;
    } catch {
      return true;
    }
  }

  static async refreshTokenIfNeeded() {
    if (this.isTokenExpiringSoon()) {
      try {
        const response = await axios.post('/api/auth/refresh');
        this.setToken(response.data.access_token);
      } catch (error) {
        console.error('Token refresh failed:', error);
        this.clearToken();
        window.location.href = '/login';
      }
    }
  }
}
```

---

## Backend API Endpoints

### Celery Task Endpoints

```python
# backend/app/main.py

@app.get("/api/admin/celery/tasks")
async def get_celery_tasks(
    queue: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = 1000,
    current_user: dict = Depends(get_current_admin)
):
    """Get Celery task list with optional filters."""
    # Implementation
    pass

@app.post("/api/admin/celery/tasks/{task_id}/revoke")
async def revoke_task(
    task_id: str,
    terminate: bool = False,
    current_user: dict = Depends(get_current_admin)
):
    """Revoke a running task."""
    celery.control.revoke(task_id, terminate=terminate)
    return {"status": "revoked", "task_id": task_id}

@app.post("/api/admin/celery/jobs/embed-all")
async def trigger_embedding_job(
    current_user: dict = Depends(get_current_admin)
):
    """Trigger full document embedding job."""
    task = embed_all_documents.apply_async()
    return {"job_id": str(task.id), "status": "submitted"}

@app.get("/api/admin/celery/queues/stats")
async def get_queue_stats(current_user: dict = Depends(get_current_admin)):
    """Get queue depth and worker stats."""
    # Implementation
    pass

@app.get("/api/admin/celery/workers")
async def get_workers(current_user: dict = Depends(get_current_admin)):
    """Get worker status and health."""
    # Implementation
    pass
```

---

## Performance Optimization

### 1. Debouncing User Actions

```typescript
// frontend/src/hooks/useDebounce.ts
import { useEffect, useState } from 'react';

export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}
```

**Usage:**

```typescript
// Debounce search input
const [searchTerm, setSearchTerm] = useState('');
const debouncedSearchTerm = useDebounce(searchTerm, 500);

useEffect(() => {
  // Only trigger API call after 500ms of no typing
  if (debouncedSearchTerm) {
    searchTasks(debouncedSearchTerm);
  }
}, [debouncedSearchTerm]);
```

---

### 2. Request Batching

```typescript
// frontend/src/utils/batcher.ts
export class RequestBatcher {
  private queue: Array<{
    resolve: (value: any) => void;
    reject: (error: any) => void;
    data: any;
  }> = [];
  private timeout: NodeJS.Timeout | null = null;

  constructor(
    private batchFn: (items: any[]) => Promise<any[]>,
    private delay: number = 100,
    private maxBatchSize: number = 50
  ) {}

  async add(data: any): Promise<any> {
    return new Promise((resolve, reject) => {
      this.queue.push({ resolve, reject, data });

      if (this.queue.length >= this.maxBatchSize) {
        this.flush();
      } else if (!this.timeout) {
        this.timeout = setTimeout(() => this.flush(), this.delay);
      }
    });
  }

  private async flush() {
    if (this.timeout) {
      clearTimeout(this.timeout);
      this.timeout = null;
    }

    if (this.queue.length === 0) return;

    const batch = this.queue.splice(0, this.maxBatchSize);
    const items = batch.map(item => item.data);

    try {
      const results = await this.batchFn(items);
      batch.forEach((item, index) => {
        item.resolve(results[index]);
      });
    } catch (error) {
      batch.forEach(item => item.reject(error));
    }
  }
}
```

---

## Testing Strategies

### 1. WebSocket Mock

```typescript
// frontend/src/__tests__/mocks/websocket.mock.ts
import { Server } from 'mock-socket';

export class WebSocketMock {
  private server: Server;

  constructor(url: string) {
    this.server = new Server(url);
  }

  simulateMessage(event: string, data: any) {
    this.server.emit(event, data);
  }

  close() {
    this.server.close();
  }
}
```

### 2. Integration Test

```typescript
// frontend/src/__tests__/CeleryJobMonitor.integration.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { CeleryJobMonitor } from '../components/admin/CeleryJobMonitor';
import { WebSocketMock } from './mocks/websocket.mock';

describe('CeleryJobMonitor Integration', () => {
  let wsMock: WebSocketMock;

  beforeEach(() => {
    wsMock = new WebSocketMock('ws://localhost:8000/ws/celery/tasks');
  });

  afterEach(() => {
    wsMock.close();
  });

  it('updates task list on WebSocket message', async () => {
    render(<CeleryJobMonitor />);

    // Simulate WebSocket message
    wsMock.simulateMessage('task_update', {
      type: 'task_update',
      data: {
        id: 'task-123',
        name: 'embed_document_batch',
        state: 'SUCCESS',
      },
    });

    await waitFor(() => {
      expect(screen.getByText('task-123')).toBeInTheDocument();
      expect(screen.getByText('SUCCESS')).toBeInTheDocument();
    });
  });
});
```

---

**Document Status:** Complete - Ready for Implementation  
**Estimated Implementation Time:** Backend (1 week), Frontend (2 weeks)

---

**References:**
- [Socket.IO Documentation](https://socket.io/docs/)
- [Frontend Admin Dashboards](frontend-admin-dashboards.md)
- [Backend Background Jobs](background-jobs.md)

