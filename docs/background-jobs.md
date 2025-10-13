# Background Job Architecture

**Version:** 1.0  
**Last Updated:** 2025-10-11  
**Owner:** Backend Team  
**Status:** Active

---

## Table of Contents

1. [Overview](#overview)
2. [Technology Stack](#technology-stack)
3. [Architecture Design](#architecture-design)
4. [Queue Design](#queue-design)
5. [Task Definitions](#task-definitions)
6. [Scheduled Jobs](#scheduled-jobs)
7. [Monitoring & Observability](#monitoring--observability)
8. [Operational Procedures](#operational-procedures)
9. [Troubleshooting](#troubleshooting)
10. [Performance Tuning](#performance-tuning)

---

## Overview

### Purpose

The APFA Background Job Architecture solves the **critical 10-100s bottleneck** in the document embedding pipeline by moving CPU-intensive tasks to asynchronous background workers. This enables:

- **100x performance improvement**: Reduced latency from 15s → 0.1s for pre-built indexes
- **Zero-downtime updates**: Hot-swap FAISS indexes without service interruption
- **Horizontal scalability**: Add workers to handle increased load
- **Scheduled maintenance**: Automated cleanup and statistics collection

### Problem Statement

**Before (Synchronous):**
```python
# Line 541 in app/main.py - BLOCKING
dt = await asyncio.to_thread(load_rag_index)  # 10-100s per request!

# Impact:
# - 10K vectors: 10s delay per request
# - 100K vectors: 100s delay (1.67 minutes)
# - 1M vectors: 1,000s delay (16.67 minutes) ❌
```

**After (Celery):**
```python
# Pre-built index loaded from MinIO in 100ms
rag_df, faiss_index = load_rag_index_from_minio()  # <100ms

# Impact:
# - All vector counts: <100ms startup
# - Index rebuilt hourly in background
# - Zero request blocking ✅
```

### Success Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Startup time** | 10-100s | <1s | 10-100x faster |
| **Per-request overhead** | 10-100s | <100ms | 100-1000x faster |
| **P95 latency (uncached)** | 15s | 3s | 5x faster |
| **Throughput (docs/sec)** | ~100 | 1,000-5,000 | 10-50x faster |
| **Index rebuild downtime** | 100% blocking | 0% (hot-swap) | Zero downtime |

---

## Technology Stack

### Celery

**Why Celery:**
- ✅ **Production-proven**: Used by Instagram, Airbnb, Pinterest
- ✅ **Advanced task routing**: Priority queues, task chaining, groups
- ✅ **Built-in monitoring**: Flower dashboard for real-time visibility
- ✅ **Flexible scheduling**: Celery Beat for cron-like jobs
- ✅ **Robust retries**: Exponential backoff, circuit breakers
- ✅ **Large community**: Extensive documentation and support

**vs RQ (Alternative Considered):**
- RQ: Simpler but lacks advanced routing and scheduling
- Decision documented in [ADR-001: Celery vs RQ](../adrs/001-celery-vs-rq.md)

### Redis

**Why Redis:**
- ✅ **Already integrated**: Used for caching (line 435 in main.py)
- ✅ **Fast in-memory broker**: Low latency message delivery
- ✅ **Dual-purpose**: Message broker + result backend + cache
- ✅ **Persistence options**: RDB snapshots or AOF for durability
- ✅ **Pub/Sub support**: For index hot-swap notifications

**Configuration:**
```yaml
# docker-compose.yml
redis:
  image: redis:7-alpine
  command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
  volumes:
    - redis_data:/data
  ports:
    - "6379:6379"
```

### Flower

**Purpose:** Real-time Celery task monitoring

**Features:**
- Task progress tracking
- Worker status and statistics
- Task history and logs
- Queue depth visualization
- Task revocation and retry

**Access:** http://localhost:5555

---

## Architecture Design

### Multi-Queue Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Redis (Message Broker)                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │ embedding        │  │ indexing         │  │ maintenance      │  │
│  │ (priority: 9)    │  │ (priority: 7)    │  │ (priority: 5)    │  │
│  │                  │  │                  │  │                  │  │
│  │ High-priority    │  │ Medium-priority  │  │ Low-priority     │  │
│  │ Critical path    │  │ Index ops        │  │ Housekeeping     │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
└───────────┬───────────────────┬────────────────────┬────────────────┘
            │                   │                    │
    ┌───────▼────────┐   ┌──────▼───────┐    ┌─────▼──────┐
    │ Worker Pool 1  │   │ Worker Pool 2│    │ Worker     │
    │ (embedding)    │   │ (indexing)   │    │ Pool 3     │
    │                │   │              │    │ (maint)    │
    │ Concurrency: 4 │   │ Concurrency:2│    │ Concur: 1  │
    │ CPU-intensive  │   │ I/O-bound    │    │ Scheduled  │
    │                │   │              │    │            │
    │ Tasks:         │   │ Tasks:       │    │ Tasks:     │
    │ • embed_batch  │   │ • build_idx  │    │ • cleanup  │
    │ • embed_all    │   │ • hot_swap   │    │ • stats    │
    └────────────────┘   └──────────────┘    └────────────┘
            │                   │                    │
            └───────────────────┴────────────────────┘
                                │
                          ┌─────▼──────┐
                          │   MinIO    │
                          │ (Storage)  │
                          │            │
                          │ • Batches  │
                          │ • Indexes  │
                          │ • Versions │
                          └────────────┘
```

### Data Flow: Embedding Pipeline

```
┌──────────────────────────────────────────────────────────────────┐
│  STEP 1: INGESTION                                               │
├──────────────────────────────────────────────────────────────────┤
│  Delta Lake → DataFrame → Document List                         │
│  Time: <1s for 100K documents                                    │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│  STEP 2: BATCH CREATION                                          │
├──────────────────────────────────────────────────────────────────┤
│  Split into batches (1,000 docs/batch)                          │
│  100K docs → 100 batches                                         │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│  STEP 3: PARALLEL EMBEDDING (Celery Group)                      │
├──────────────────────────────────────────────────────────────────┤
│  [Task 1]  [Task 2]  [Task 3]  ...  [Task 100]                 │
│     ↓         ↓         ↓               ↓                        │
│  Embed    Embed    Embed     ...    Embed                       │
│  1K docs  1K docs  1K docs          1K docs                     │
│     ↓         ↓         ↓               ↓                        │
│  MinIO    MinIO    MinIO     ...    MinIO                       │
│                                                                  │
│  Time: ~10s (parallel) vs 100s (sequential)                     │
│  Workers: 4 workers × 2.5 batches/sec = 10 batches/sec         │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│  STEP 4: INDEX BUILDING                                          │
├──────────────────────────────────────────────────────────────────┤
│  Load all batches → Concatenate → Build FAISS IndexFlatIP      │
│  Upload to MinIO: indexes/faiss_index_{version}.pkl            │
│  Time: <5s for 100K vectors                                     │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│  STEP 5: HOT-SWAP (Zero Downtime)                               │
├──────────────────────────────────────────────────────────────────┤
│  Publish event → Redis pub/sub → apfa:index:swap               │
│  FastAPI subscribes → Loads new index → Atomic swap            │
│  Time: <100ms                                                    │
│  Downtime: 0ms ✅                                                │
└──────────────────────────────────────────────────────────────────┘
```

---

## Queue Design

### Queue Priorities

Priority ensures critical tasks execute first when workers are busy.

| Queue | Priority | Purpose | Typical Tasks | Workers |
|-------|----------|---------|---------------|---------|
| **embedding** | 9 (highest) | Critical path embedding | embed_document_batch, embed_all_documents | 2-4 |
| **indexing** | 7 (medium) | Index building/swapping | build_faiss_index, hot_swap_index | 1-2 |
| **maintenance** | 5 (low) | Cleanup, stats | cleanup_old_embeddings, compute_index_stats | 1 |

### Queue Configuration

**File:** `app/celeryconfig.py`

```python
from kombu import Exchange, Queue

task_routes = {
    'app.tasks.embed_*': {'queue': 'embedding'},
    'app.tasks.build_faiss_index': {'queue': 'indexing'},
    'app.tasks.hot_swap_index': {'queue': 'indexing'},
    'app.tasks.cleanup_*': {'queue': 'maintenance'},
    'app.tasks.compute_*': {'queue': 'maintenance'}
}

task_queues = (
    Queue('embedding', Exchange('embedding'), routing_key='embedding', priority=9),
    Queue('indexing', Exchange('indexing'), routing_key='indexing', priority=7),
    Queue('maintenance', Exchange('maintenance'), routing_key='maintenance', priority=5),
)
```

### Worker Pool Configuration

**Embedding Workers (CPU-intensive):**
```bash
celery -A app.tasks worker \
  --loglevel=info \
  --queues=embedding \
  --concurrency=4 \
  --max-tasks-per-child=10 \
  --prefetch-multiplier=1
```

**Indexing Workers (I/O-bound):**
```bash
celery -A app.tasks worker \
  --loglevel=info \
  --queues=indexing \
  --concurrency=2 \
  --max-tasks-per-child=20 \
  --prefetch-multiplier=2
```

**Maintenance Workers (Low priority):**
```bash
celery -A app.tasks worker \
  --loglevel=info \
  --queues=maintenance \
  --concurrency=1 \
  --max-tasks-per-child=50 \
  --prefetch-multiplier=4
```

---

## Task Definitions

### Priority 1: Embedding Tasks (Critical Path)

#### `embed_document_batch(document_batch, batch_id)`

**Purpose:** Embed a batch of documents using Sentence-BERT.

**Parameters:**
- `document_batch` (List[str]): List of document texts (max 1,000)
- `batch_id` (str): Unique identifier for tracking

**Returns:** `(minio_path: str, embedding_count: int)`

**Configuration:**
```python
@app.task(
    bind=True,
    queue='embedding',
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
    reject_on_worker_lost=True
)
```

**Performance:**
- Target: <1s per batch (1,000 documents)
- Throughput: 1,000 docs/sec/worker on CPU
- Memory: ~500MB per worker

**Error Handling:**
- Automatic retry with exponential backoff (60s, 120s, 240s)
- Failed batches logged for manual intervention
- Prometheus metric: `celery_task_failure_total{task_name="embed_document_batch"}`

**Example Usage:**
```python
# Synchronous (blocking)
result = embed_document_batch.apply(args=[documents, "batch_001"])

# Asynchronous (recommended)
task = embed_document_batch.apply_async(args=[documents, "batch_001"])
result = task.get(timeout=30)  # Wait up to 30s
```

---

#### `embed_all_documents(delta_table_path=None)`

**Purpose:** Orchestrate embedding of all documents from Delta Lake.

**Parameters:**
- `delta_table_path` (str, optional): Override default Delta Lake path

**Returns:** `dict` with statistics (total_docs, total_time, docs_per_second)

**Configuration:**
```python
@app.task(queue='embedding')
```

**Workflow:**
```python
1. Load documents from Delta Lake
2. Split into batches (1,000 docs each)
3. Submit parallel embedding tasks using Celery group()
4. Wait for all tasks to complete (timeout: 1 hour)
5. Trigger index rebuild
6. Return statistics
```

**Performance:**
- Target: 100K documents in <60s
- Parallelism: N workers × throughput per worker
- 4 workers × 1,000 docs/sec = 4,000 docs/sec theoretical max

**Monitoring:**
```bash
# Check progress in Flower
http://localhost:5555/tasks

# Check Prometheus metrics
celery_task_execution_seconds{task_name="embed_all_documents"}
```

**Example Usage:**
```python
# Trigger from FastAPI endpoint (admin only)
@app.post("/admin/rebuild-embeddings")
async def trigger_embedding_rebuild(current_user: dict = Depends(get_admin_user)):
    task = embed_all_documents.apply_async()
    return {"task_id": task.id, "status": "submitted"}

# Trigger from CLI
celery -A app.tasks call app.tasks.embed_all_documents
```

---

### Priority 2: Indexing Tasks

#### `build_faiss_index(num_batches)`

**Purpose:** Build FAISS index from pre-computed embedding batches.

**Parameters:**
- `num_batches` (int): Number of embedding batches to load

**Returns:** `str` - Path to new index in MinIO

**Configuration:**
```python
@app.task(
    bind=True,
    queue='indexing',
    max_retries=2,
    default_retry_delay=120
)
```

**Workflow:**
```python
1. Load all embedding batches from MinIO
2. Concatenate into single numpy array
3. Build FAISS IndexFlatIP
4. Serialize index with pickle
5. Generate version hash (SHA256[:8])
6. Upload to MinIO: indexes/faiss_index_{hash}.pkl
7. Update "latest" pointer
8. Trigger hot-swap
```

**Performance:**
- Target: 100K vectors in <5s
- Memory: ~150MB for 100K vectors (384 dims)

**Error Handling:**
- Missing batches logged as warnings
- Corrupted batches skipped
- Index integrity validated before upload

---

#### `hot_swap_index(version_hash)`

**Purpose:** Atomically swap active FAISS index with zero downtime.

**Parameters:**
- `version_hash` (str): Version identifier of new index

**Returns:** `bool` - Success status

**Configuration:**
```python
@app.task(queue='indexing')
```

**Mechanism:**
```python
1. Publish event to Redis pub/sub channel: apfa:index:swap
2. FastAPI background thread listens on this channel
3. On event: Load new index from MinIO
4. Atomic swap: old_index → new_index (single assignment)
5. Old index garbage collected
```

**Downtime:** 0ms ✅

**Verification:**
```python
# Check current index version
curl http://localhost:8000/admin/index-version
# Response: {"version": "abc123", "vectors": 100000}
```

---

### Priority 3: Maintenance Tasks

#### `cleanup_old_embeddings(retention_days=7)`

**Purpose:** Delete old embedding batches and indexes.

**Schedule:** Daily at 2:00 AM

**Logic:**
```python
1. List objects in MinIO: embeddings/batches/
2. Filter objects older than retention_days
3. Delete filtered objects
4. Log deletion count
5. Update Prometheus counter
```

**Safety:**
- Always keeps current index + latest embeddings
- Requires manual override to delete <7 days old

---

#### `compute_index_stats()`

**Purpose:** Calculate and report index statistics for monitoring.

**Schedule:** Every 5 minutes

**Metrics Computed:**
```python
{
    'version': 'abc123',
    'vector_count': 100000,
    'dimensions': 384,
    'memory_mb': 153.6,
    'index_type': 'IndexFlatIP',
    'migration_urgency': 45.2  # Score 0-100
}
```

**Migration Urgency Algorithm:**
```python
vector_score = min(100, (vector_count / 500000) * 100)
memory_score = min(100, (memory_bytes / (2 * 1024**3)) * 100)
urgency = max(vector_score, memory_score)

# Interpretation:
# < 70: No action needed
# 70-90: Plan migration
# > 90: Migrate immediately
```

---

## Scheduled Jobs

### Celery Beat Configuration

**File:** `app/tasks.py` (bottom)

```python
app.conf.beat_schedule = {
    'rebuild-index-hourly': {
        'task': 'app.tasks.embed_all_documents',
        'schedule': crontab(minute=0),  # Every hour at :00
        'options': {'queue': 'embedding'}
    },
    'cleanup-daily': {
        'task': 'app.tasks.cleanup_old_embeddings',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        'options': {'queue': 'maintenance'}
    },
    'compute-stats-every-5min': {
        'task': 'app.tasks.compute_index_stats',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
        'options': {'queue': 'maintenance'}
    }
}
```

### Viewing Scheduled Tasks

**Flower Dashboard:**
```
http://localhost:5555/tasks/scheduled
```

**CLI:**
```bash
# List scheduled tasks
celery -A app.tasks inspect scheduled

# View beat status
celery -A app.tasks inspect active
```

---

## Monitoring & Observability

### Prometheus Metrics

**Task Execution:**
```
celery_task_execution_seconds_bucket{task_name="embed_document_batch", queue="embedding"}
celery_task_success_total{task_name="embed_all_documents"}
celery_task_failure_total{task_name="build_faiss_index", exception_type="ValueError"}
```

**Queue Depth:**
```
celery_queue_depth{queue_name="embedding"}
celery_queue_depth{queue_name="indexing"}
celery_queue_depth{queue_name="maintenance"}
```

**Custom Metrics:**
```
celery_embedding_batches_total
celery_faiss_index_version
```

### Flower Dashboard

**Key Views:**
1. **Tasks:** Real-time task status (PENDING, STARTED, SUCCESS, FAILURE)
2. **Workers:** Worker health, CPU, memory
3. **Monitor:** Live task stream
4. **Broker:** Redis connection status
5. **Tasks (History):** Completed task history

**Access:**
```
http://localhost:5555
```

### Grafana Dashboard

See [Observability Documentation](observability.md) for complete Grafana setup.

**Key Panels:**
- Embedding Batch Duration (P95/P99)
- Celery Queue Depth
- Task Success/Failure Rate
- Worker CPU/Memory Usage

---

## Operational Procedures

### Starting Workers

**Development:**
```bash
# Start all workers
docker-compose up -d celery_worker celery_beat flower

# View logs
docker-compose logs -f celery_worker
```

**Production (AWS ECS):**
```bash
# Deploy via CDK
cdk deploy APFACeleryStack

# Scale workers
aws ecs update-service --cluster apfa-cluster --service celery-embedding --desired-count 4
```

### Scaling Workers

**When to Scale UP:**
- Queue depth consistently >20 tasks
- Worker CPU utilization >90%
- Task wait time >5 seconds

**How to Scale:**
```bash
# Docker Compose
docker-compose up -d --scale celery_worker=4

# AWS ECS
aws ecs update-service --cluster apfa-cluster --service celery-embedding --desired-count 8
```

**When to Scale DOWN:**
- Queue depth consistently <5 tasks
- Worker CPU utilization <30%
- Off-peak hours (e.g., night)

### Draining Queues

**Graceful Shutdown:**
```bash
# Stop accepting new tasks
celery -A app.tasks control shutdown

# Wait for current tasks to finish (timeout: 5 min)
celery -A app.tasks inspect active

# Force shutdown if needed
docker-compose stop celery_worker
```

**Purging Queues (DANGEROUS):**
```bash
# Purge specific queue
celery -A app.tasks purge -Q embedding

# Confirm deletion
# This deletes ALL pending tasks!
```

### Manual Task Execution

**Trigger Embedding Rebuild:**
```bash
celery -A app.tasks call app.tasks.embed_all_documents
```

**Build Index Manually:**
```bash
celery -A app.tasks call app.tasks.build_faiss_index --args='[100]'
```

**Cleanup Old Files:**
```bash
celery -A app.tasks call app.tasks.cleanup_old_embeddings --kwargs='{"retention_days": 3}'
```

---

## Troubleshooting

### Common Issues

#### 1. Tasks Stuck in PENDING

**Symptoms:**
- Tasks appear in Flower but never start
- Queue depth increasing

**Causes:**
- Workers not running
- Workers not subscribed to correct queue
- Redis connection issue

**Solutions:**
```bash
# Check worker status
celery -A app.tasks inspect active

# Check registered workers
celery -A app.tasks inspect registered

# Restart workers
docker-compose restart celery_worker

# Check Redis connectivity
redis-cli -h localhost ping
# Expected: PONG
```

---

#### 2. High Task Failure Rate

**Symptoms:**
- `celery_task_failure_total` metric increasing
- Error logs in worker output

**Causes:**
- Bad input data (e.g., missing Delta Lake column)
- Resource exhaustion (OOM, disk full)
- External service unavailable (MinIO, AWS Bedrock)

**Solutions:**
```bash
# Check worker logs
docker-compose logs celery_worker | grep ERROR

# Check resource usage
docker stats celery_worker

# View failed tasks in Flower
http://localhost:5555/tasks?state=FAILURE

# Retry failed task manually
celery -A app.tasks call app.tasks.embed_document_batch --args='[["doc1", "doc2"], "batch_retry_001"]'
```

---

#### 3. Slow Embedding Performance

**Symptoms:**
- P95 latency >2s per batch
- Low throughput (<500 docs/sec)

**Causes:**
- Insufficient workers
- CPU throttling
- Large batch sizes
- Network latency to MinIO

**Solutions:**
```bash
# Scale workers
docker-compose up -d --scale celery_worker=8

# Check CPU limits
docker inspect celery_worker | grep -A 5 resources

# Tune batch size (in tasks.py)
embedder.encode(document_batch, batch_size=16)  # Reduce from 32

# Check MinIO latency
curl -w "@curl-format.txt" http://minio:9000/minio/health/live
```

---

#### 4. Index Hot-Swap Failed

**Symptoms:**
- FastAPI still using old index version
- No `apfa:index:swap` event received

**Causes:**
- Redis pub/sub listener thread not running
- Corrupted index file in MinIO
- FastAPI not subscribed to Redis channel

**Solutions:**
```bash
# Check FastAPI logs
docker-compose logs apfa | grep "index swap"

# Verify pub/sub channel
redis-cli
> PUBSUB CHANNELS apfa:*
# Expected: apfa:index:swap

# Manually trigger hot-swap
celery -A app.tasks call app.tasks.hot_swap_index --args='["abc123"]'

# Restart FastAPI to reinitialize listener
docker-compose restart apfa
```

---

#### 5. Queue Depth Alarm

**Symptoms:**
- `celery_queue_depth` >50 for >10 minutes
- Alert: "CeleryQueueBacklog"

**Causes:**
- Worker crash or shutdown
- Unexpected load spike
- Long-running tasks blocking queue

**Solutions:**
```bash
# Immediate: Scale workers
docker-compose up -d --scale celery_worker=8

# Check for stuck tasks
celery -A app.tasks inspect active

# Revoke long-running task (if stuck)
celery -A app.tasks control revoke <task-id> --terminate

# Check worker health
celery -A app.tasks inspect ping
```

---

## Performance Tuning

### Worker Concurrency

**CPU-bound tasks (embedding):**
```
concurrency = CPU_COUNT × 1
# Example: 4 CPUs → concurrency=4
```

**I/O-bound tasks (indexing):**
```
concurrency = CPU_COUNT × 2-4
# Example: 4 CPUs → concurrency=8-16
```

### Batch Size Tuning

**Embedding batch size:**
```python
# Small batches: Lower latency, higher overhead
batch_size = 100  # <1s, good for real-time

# Medium batches: Balanced (RECOMMENDED)
batch_size = 1000  # 1-2s, optimal for throughput

# Large batches: Higher throughput, higher latency
batch_size = 5000  # 5-10s, good for bulk processing
```

**Sentence-BERT encode batch_size:**
```python
# CPU
embedder.encode(docs, batch_size=16)  # Conservative

# GPU
embedder.encode(docs, batch_size=64)  # Utilize GPU memory
```

### Memory Management

**Worker memory limits:**
```yaml
# docker-compose.yml
celery_worker:
  deploy:
    resources:
      limits:
        memory: 2G  # Prevent OOM
      reservations:
        memory: 1G  # Guaranteed memory
```

**Task recycling:**
```python
# celeryconfig.py
worker_max_tasks_per_child = 10  # Restart worker after 10 tasks
# Prevents memory leaks from accumulating
```

### Redis Optimization

**Configuration:**
```
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru  # Evict least-recently-used keys
appendonly yes  # Persistence
save 900 1  # RDB snapshot every 15min if ≥1 key changed
```

**Connection pooling:**
```python
# celeryconfig.py
broker_pool_limit = 10  # Connection pool size
broker_connection_retry_on_startup = True
```

---

## Security Considerations

### Task Authorization

**Production:** Restrict task execution to admin users only.

```python
@app.post("/admin/trigger-rebuild")
async def trigger_rebuild(current_user: dict = Depends(get_admin_user)):
    # Only admins can trigger expensive tasks
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    task = embed_all_documents.apply_async()
    return {"task_id": task.id}
```

### Secrets Management

**Environment variables:**
```yaml
# docker-compose.yml
celery_worker:
  environment:
    - CELERY_BROKER_URL=${CELERY_BROKER_URL}  # redis://redis:6379/0
    - MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY}
    - MINIO_SECRET_KEY=${MINIO_SECRET_KEY}
```

**AWS Secrets Manager (Production):**
```python
import boto3

def get_secret(secret_name):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])
```

### Network Security

**Production:** Isolate Celery workers in private subnet.

```
┌─────────────────────────────────────┐
│         Public Subnet               │
│  ┌─────────┐     ┌─────────┐        │
│  │   ALB   │────▶│  FastAPI │       │
│  └─────────┘     └─────────┘        │
└───────────────────────┬─────────────┘
                        │
┌───────────────────────▼─────────────┐
│         Private Subnet              │
│  ┌─────────┐     ┌─────────┐        │
│  │  Redis  │────▶│ Celery  │        │
│  └─────────┘     │ Workers │        │
│                  └─────────┘        │
└─────────────────────────────────────┘
```

---

## References

- [Celery Official Documentation](https://docs.celeryproject.org/)
- [APFA Observability Guide](observability.md)
- [APFA Deployment Operations](deployment-operations.md)
- [ADR-001: Celery vs RQ](../adrs/001-celery-vs-rq.md)

---

## Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-11 | Backend Team | Initial documentation for Week 1 implementation |

---

**Need Help?**
- Slack: #apfa-backend
- On-call: PagerDuty rotation
- Runbook: [Incident Response](deployment-operations.md#incident-response)

