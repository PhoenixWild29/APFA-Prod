# Celery Implementation Project Plan

**Project Name:** APFA Batch Embedding Critical Path Fix  
**Duration:** 3 weeks (21 days)  
**Start Date:** 2025-10-14 (Monday)  
**End Date:** 2025-11-01 (Friday)  
**Project Lead:** Backend Team Lead  
**Priority:** P0 - Critical

---

## Executive Summary

### Problem Statement
Current synchronous embedding generation causes **10-100s request latency**, blocking user requests and preventing scaling beyond 100K vectors. This is a critical bottleneck affecting user experience and system scalability.

### Solution
Implement Celery-based asynchronous background job processing to pre-compute embeddings and enable hot-swap index updates with zero downtime.

### Expected Outcomes
- **100-1000x latency improvement**: 15s → 0.1s for pre-built index loads
- **Zero-downtime updates**: Hot-swap indexes without service interruption
- **Horizontal scalability**: Support for 1M+ vectors
- **Operational excellence**: Comprehensive monitoring and alerting

---

## Success Criteria

| Metric | Current | Target | How to Measure |
|--------|---------|--------|----------------|
| **P95 latency (uncached)** | 15s | <3s | Prometheus: `histogram_quantile(0.95, rate(apfa_response_time_seconds_bucket[5m]))` |
| **Startup blocking time** | 10-100s | <1s | Log analysis: Time from container start to first request |
| **Embedding throughput** | ~100 docs/sec | 1,000-5,000 docs/sec | Celery metric: `rate(celery_embedding_batches_total[5m]) * 1000` |
| **Index hot-swap downtime** | 100% | 0% | Zero failed requests during swap |
| **Error rate** | 0.5% | <0.1% | Prometheus: `rate(apfa_requests_total{status=~"5.."}[5m]) / rate(apfa_requests_total[5m])` |
| **Cache hit rate** | 65% | >80% | Prometheus: `rate(apfa_cache_hits_total[5m]) / (rate(apfa_cache_hits_total[5m]) + rate(apfa_cache_misses_total[5m]))` |

---

## Project Milestones

```
Week 1: Foundation & Infrastructure ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ├─ Day 1-2:  Infrastructure Setup      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ├─ Day 3-4:  Core Embedding Tasks      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  └─ Day 5-7:  Index Building & Hot-Swap ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%

Week 2: Optimization & Production Readiness ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ├─ Day 8-9:  Performance Optimization  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ├─ Day 10-11: Scheduled Jobs           ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  └─ Day 12-14: Monitoring & Alerting    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%

Week 3: Production Deployment ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ├─ Day 15-16: Staging & Testing        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ├─ Day 17-18: Production Deployment    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  └─ Day 19-21: Documentation & Training ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
```

---

## Week 1: Foundation & Infrastructure

### Day 1-2: Infrastructure Setup

#### Task 1.1: Add Redis to Docker Compose
**Owner:** DevOps Engineer  
**Effort:** 2 hours  
**Dependencies:** None

**Acceptance Criteria:**
- [ ] Redis service added to `docker-compose.yml`
- [ ] Redis configured with persistence (AOF enabled)
- [ ] Redis health check passing
- [ ] Redis accessible at `redis://redis:6379`

**Implementation:**
```yaml
# File: docker-compose.yml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
  command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 10s
    timeout: 5s
    retries: 3
  restart: unless-stopped
```

**Verification:**
```bash
docker-compose up -d redis
redis-cli -h localhost ping  # Expected: PONG
```

---

#### Task 1.2: Add Celery Worker Service
**Owner:** Backend Engineer  
**Effort:** 3 hours  
**Dependencies:** Task 1.1

**Acceptance Criteria:**
- [ ] Celery worker service added to `docker-compose.yml`
- [ ] Worker connects to Redis successfully
- [ ] Can execute test task
- [ ] Logs visible via `docker-compose logs`

**Implementation:**
```yaml
# File: docker-compose.yml
celery_worker:
  build: .
  command: celery -A app.tasks worker --loglevel=info --queues=embedding,indexing,maintenance --concurrency=4
  environment:
    - CELERY_BROKER_URL=redis://redis:6379/0
    - CELERY_RESULT_BACKEND=redis://redis:6379/0
    - MINIO_ENDPOINT=${MINIO_ENDPOINT}
    - MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY}
    - MINIO_SECRET_KEY=${MINIO_SECRET_KEY}
  depends_on:
    redis:
      condition: service_healthy
  volumes:
    - ./app:/app
  restart: unless-stopped
  deploy:
    replicas: 2
```

**Verification:**
```bash
docker-compose up -d celery_worker
celery -A app.tasks inspect ping
# Expected: celery@<hostname>: OK
```

---

#### Task 1.3: Add Celery Beat and Flower
**Owner:** Backend Engineer  
**Effort:** 2 hours  
**Dependencies:** Task 1.2

**Acceptance Criteria:**
- [ ] Celery Beat service added for scheduled tasks
- [ ] Flower dashboard accessible at http://localhost:5555
- [ ] Can view workers and tasks in Flower

**Implementation:**
```yaml
# docker-compose.yml
celery_beat:
  build: .
  command: celery -A app.tasks beat --loglevel=info
  environment:
    - CELERY_BROKER_URL=redis://redis:6379/0
  depends_on:
    - redis
  restart: unless-stopped

flower:
  build: .
  command: celery -A app.tasks flower --port=5555
  ports:
    - "5555:5555"
  environment:
    - CELERY_BROKER_URL=redis://redis:6379/0
  depends_on:
    - redis
  restart: unless-stopped
```

**Verification:**
```bash
curl http://localhost:5555/api/workers
# Expected: JSON with worker list
```

---

#### Task 1.4: Create Celery Configuration Files
**Owner:** Backend Engineer  
**Effort:** 2 hours  
**Dependencies:** None

**Acceptance Criteria:**
- [ ] `app/celeryconfig.py` created with queue definitions
- [ ] `app/tasks.py` skeleton created
- [ ] Configuration validated

**Files to Create:**
1. `app/celeryconfig.py` (see [background-jobs.md](background-jobs.md#queue-configuration))
2. `app/tasks.py` (initial structure)

**Verification:**
```bash
python -c "from app.celeryconfig import task_queues; print(task_queues)"
# Expected: Queue definitions printed
```

---

#### Task 1.5: Update requirements.txt
**Owner:** Backend Engineer  
**Effort:** 30 minutes  
**Dependencies:** None

**Acceptance Criteria:**
- [ ] Celery dependencies added
- [ ] `pip install -r requirements.txt` succeeds

**Changes:**
```txt
# Add to requirements.txt
celery[redis]==5.3.4
flower==2.0.1
redis==5.0.1
```

**Verification:**
```bash
pip install -r requirements.txt
python -c "import celery; print(celery.__version__)"
# Expected: 5.3.4
```

---

### Day 3-4: Core Embedding Tasks

#### Task 2.1: Implement embed_document_batch Task
**Owner:** Backend Engineer  
**Effort:** 6 hours  
**Dependencies:** Day 1-2 infrastructure

**Acceptance Criteria:**
- [ ] Task definition complete with retry logic
- [ ] Embeddings generated successfully
- [ ] Results uploaded to MinIO
- [ ] Prometheus metrics instrumented

**Implementation Checklist:**
- [ ] Task decorator configured (queue, retries, acks_late)
- [ ] Sentence-BERT encoding with batching
- [ ] L2 normalization applied
- [ ] Pickle serialization
- [ ] MinIO upload with error handling
- [ ] Unit tests written (80%+ coverage)

**Test Cases:**
```python
def test_embed_document_batch_success():
    # Test successful embedding of 1000 documents
    result = embed_document_batch.apply(args=[sample_docs, "test_batch"])
    assert result.successful()
    assert len(result.get()) == 2  # (path, count)

def test_embed_document_batch_retry():
    # Test retry on MinIO failure
    with patch('minio_client.put_object') as mock:
        mock.side_effect = [Exception("Connection error"), None]
        result = embed_document_batch.apply(args=[sample_docs, "retry_batch"])
        assert mock.call_count == 2  # Initial + 1 retry

def test_embed_document_batch_metrics():
    # Test Prometheus metrics incremented
    before = EMBEDDING_BATCH_COUNT._value.get()
    embed_document_batch.apply(args=[sample_docs, "metrics_batch"])
    after = EMBEDDING_BATCH_COUNT._value.get()
    assert after == before + 1
```

**Performance Target:**
- 1,000 documents in <1 second (CPU)
- Memory usage <500MB per worker

---

#### Task 2.2: Implement embed_all_documents Orchestrator
**Owner:** Backend Engineer  
**Effort:** 4 hours  
**Dependencies:** Task 2.1

**Acceptance Criteria:**
- [ ] Loads documents from Delta Lake
- [ ] Splits into batches
- [ ] Submits parallel Celery group
- [ ] Triggers index rebuild on completion
- [ ] Returns statistics

**Implementation Checklist:**
- [ ] Delta Lake connection and data validation
- [ ] Batch size configuration (default: 1000)
- [ ] Celery group() for parallel execution
- [ ] Timeout handling (1 hour)
- [ ] Statistics calculation
- [ ] Chain to build_faiss_index task

**Test Cases:**
```python
def test_embed_all_documents_small_dataset():
    # Test with 5K documents
    result = embed_all_documents.apply(args=["s3://test-data/profiles"])
    stats = result.get(timeout=60)
    assert stats['total_documents'] == 5000
    assert stats['status'] == 'success'

def test_embed_all_documents_parallel():
    # Verify parallel execution (not sequential)
    start = time.time()
    embed_all_documents.apply(args=["s3://test-data/10k-profiles"])
    duration = time.time() - start
    assert duration < 30  # Should be <30s with parallelism (vs 100s serial)
```

**Performance Target:**
- 10K documents: <10 seconds
- 100K documents: <60 seconds

---

#### Task 2.3: Create MinIO Bucket and Test Storage
**Owner:** DevOps Engineer  
**Effort:** 1 hour  
**Dependencies:** None

**Acceptance Criteria:**
- [ ] MinIO bucket `apfa-embeddings` created
- [ ] Directory structure established
- [ ] Permissions verified
- [ ] Lifecycle policies configured (optional)

**Commands:**
```bash
# Install MinIO client
brew install minio/stable/mc  # or appropriate package manager

# Configure alias
mc alias set local http://localhost:9000 minioadmin minioadmin

# Create bucket
mc mb local/apfa-embeddings

# Create directory structure
mc mb local/apfa-embeddings/batches
mc mb local/apfa-embeddings/indexes

# Test upload/download
echo "test" > test.txt
mc cp test.txt local/apfa-embeddings/batches/test.txt
mc cat local/apfa-embeddings/batches/test.txt
```

**Verification:**
```bash
mc ls local/apfa-embeddings/
# Expected: batches/ and indexes/ directories
```

---

### Day 5-7: Index Building & Hot-Swap

#### Task 3.1: Implement build_faiss_index Task
**Owner:** Backend Engineer  
**Effort:** 6 hours  
**Dependencies:** Task 2.1, 2.2

**Acceptance Criteria:**
- [ ] Loads all embedding batches from MinIO
- [ ] Builds FAISS IndexFlatIP
- [ ] Generates version hash (SHA256)
- [ ] Uploads to MinIO
- [ ] Updates "latest" pointer

**Implementation Checklist:**
- [ ] Batch loading with error handling
- [ ] NumPy concatenation
- [ ] FAISS index construction
- [ ] Index serialization (faiss.serialize_index + pickle)
- [ ] Version hashing
- [ ] Atomic "latest" pointer update
- [ ] Prometheus metric: INDEX_VERSION

**Test Cases:**
```python
def test_build_faiss_index_success():
    # Pre-create 10 embedding batches
    setup_test_embeddings(10)
    
    result = build_faiss_index.apply(args=[10])
    index_path = result.get()
    
    # Verify index exists in MinIO
    assert minio_client.stat_object('apfa-embeddings', index_path)
    
    # Verify "latest" pointer updated
    latest = minio_client.get_object('apfa-embeddings', 'indexes/latest.txt').read()
    assert latest in index_path

def test_build_faiss_index_missing_batch():
    # Test graceful handling of missing batch
    result = build_faiss_index.apply(args=[10])  # Only 9 batches exist
    index_path = result.get()
    # Should succeed with 9 batches, log warning
```

**Performance Target:**
- 100K vectors: <5 seconds
- Memory: ~200MB for 100K vectors

---

#### Task 3.2: Implement hot_swap_index Task
**Owner:** Backend Engineer  
**Effort:** 3 hours  
**Dependencies:** Task 3.1

**Acceptance Criteria:**
- [ ] Publishes event to Redis pub/sub
- [ ] Event payload includes version hash
- [ ] Returns success status

**Implementation Checklist:**
- [ ] Redis pub/sub client initialization
- [ ] Event serialization (pickle)
- [ ] Publish to `apfa:index:swap` channel
- [ ] Error handling for Redis unavailable

**Test Cases:**
```python
def test_hot_swap_index_publishes_event():
    with patch('redis.Redis.publish') as mock_publish:
        hot_swap_index.apply(args=['abc123'])
        assert mock_publish.called
        assert mock_publish.call_args[0][0] == 'apfa:index:swap'
```

---

#### Task 3.3: Update FastAPI to Load Pre-Built Index
**Owner:** Backend Engineer  
**Effort:** 6 hours  
**Dependencies:** Task 3.1

**Acceptance Criteria:**
- [ ] `load_rag_index_from_minio()` function implemented
- [ ] Loads index in <100ms
- [ ] Falls back to sync build if MinIO unavailable
- [ ] Logs index version on startup

**Implementation Checklist:**
- [ ] MinIO client integration
- [ ] Load "latest" pointer
- [ ] Download and deserialize index
- [ ] Load corresponding DataFrame
- [ ] Fallback to `load_rag_index()` on error
- [ ] Startup time measurement

**Changes to app/main.py:**
```python
# Replace line 99:
# rag_df, faiss_index = load_rag_index()

# With:
rag_df, faiss_index, index_version = load_rag_index_from_minio()
logger.info(f"Loaded FAISS index version {index_version} with {len(rag_df)} vectors")
```

**Test Cases:**
```python
def test_load_rag_index_from_minio_success():
    # Pre-create index in MinIO
    create_test_index()
    
    df, index, version = load_rag_index_from_minio()
    assert len(df) > 0
    assert index.ntotal == len(df)
    assert version is not None

def test_load_rag_index_from_minio_fallback():
    # Test fallback when MinIO unavailable
    with patch('minio_client.get_object') as mock:
        mock.side_effect = Exception("MinIO down")
        
        df, index = load_rag_index()  # Fallback
        assert len(df) > 0
```

**Performance Target:**
- Load time: <100ms for 100K vectors

---

#### Task 3.4: Implement Index Hot-Swap Listener
**Owner:** Backend Engineer  
**Effort:** 4 hours  
**Dependencies:** Task 3.2, 3.3

**Acceptance Criteria:**
- [ ] Background thread listens to Redis pub/sub
- [ ] On event, loads new index atomically
- [ ] No request failures during swap
- [ ] Logs swap completion

**Implementation Checklist:**
- [ ] Redis pub/sub subscription
- [ ] Message parsing
- [ ] Atomic index swap (global variable)
- [ ] Error handling
- [ ] Thread lifecycle management (start on app startup, stop on shutdown)

**Changes to app/main.py:**
```python
# Add after line 99
import threading

def index_swap_listener():
    """Background thread for hot-swapping indexes."""
    global rag_df, faiss_index
    
    r = redis.Redis.from_url("redis://localhost:6379")
    pubsub = r.pubsub()
    pubsub.subscribe('apfa:index:swap')
    
    for message in pubsub.listen():
        if message['type'] == 'message':
            swap_data = pickle.loads(message['data'])
            version = swap_data['version']
            
            logger.info(f"Hot-swapping to index version {version}")
            new_df, new_index, _ = load_rag_index_from_minio()
            
            # Atomic swap
            rag_df = new_df
            faiss_index = new_index
            
            logger.info(f"Index hot-swapped successfully")

# Start listener thread
swap_thread = threading.Thread(target=index_swap_listener, daemon=True)
swap_thread.start()
```

**Test Cases:**
```python
def test_hot_swap_no_request_failures():
    # Start load test
    load_test = start_background_load_test(duration=30)
    
    # Trigger hot-swap during load test
    time.sleep(5)
    hot_swap_index.apply_async(args=['new_version'])
    
    # Wait for completion
    time.sleep(10)
    load_test.stop()
    
    # Verify zero failures
    assert load_test.error_count == 0
```

---

## Week 2: Optimization & Production Readiness

### Day 8-9: Performance Optimization

#### Task 4.1: Batch Size Tuning
**Owner:** Backend Engineer  
**Effort:** 4 hours  
**Dependencies:** Week 1 complete

**Acceptance Criteria:**
- [ ] Test batch sizes: 100, 500, 1000, 2000, 5000
- [ ] Measure latency and throughput for each
- [ ] Select optimal batch size
- [ ] Document results

**Test Matrix:**

| Batch Size | P95 Latency | Throughput (docs/sec) | Memory (MB) | Recommendation |
|------------|-------------|----------------------|-------------|----------------|
| 100 | TBD | TBD | TBD | Too small |
| 500 | TBD | TBD | TBD | - |
| **1000** | **<1s** | **1000+** | **500** | **OPTIMAL** ✅ |
| 2000 | TBD | TBD | TBD | - |
| 5000 | TBD | TBD | TBD | Too large |

**Test Script:**
```python
import time
from app.tasks import embed_document_batch

def benchmark_batch_size(batch_size, docs):
    batches = [docs[i:i+batch_size] for i in range(0, len(docs), batch_size)]
    
    start = time.time()
    results = [embed_document_batch.apply(args=[batch, f"bench_{i}"]) for i, batch in enumerate(batches)]
    [r.get() for r in results]
    duration = time.time() - start
    
    throughput = len(docs) / duration
    print(f"Batch size {batch_size}: {throughput:.0f} docs/sec, {duration:.2f}s total")

# Run benchmark
docs = load_test_documents(10000)
for size in [100, 500, 1000, 2000, 5000]:
    benchmark_batch_size(size, docs)
```

---

#### Task 4.2: Worker Concurrency Tuning
**Owner:** DevOps Engineer  
**Effort:** 3 hours  
**Dependencies:** Task 4.1

**Acceptance Criteria:**
- [ ] Test concurrency: 1, 2, 4, 8, 16 workers
- [ ] Measure queue drain rate
- [ ] Identify optimal worker count
- [ ] Update docker-compose.yml

**Test Matrix:**

| Workers | Queue Drain Rate (tasks/sec) | CPU Usage (%) | Recommendation |
|---------|------------------------------|---------------|----------------|
| 1 | TBD | TBD | Baseline |
| 2 | TBD | TBD | - |
| **4** | **High** | **70-90%** | **OPTIMAL** ✅ |
| 8 | TBD | TBD | Diminishing returns |
| 16 | TBD | TBD | CPU contention |

**Test Command:**
```bash
# Submit 1000 tasks
for i in {1..1000}; do
  celery -A app.tasks call app.tasks.embed_document_batch --args='[["doc1"], "test_'$i'"]'
done

# Monitor drain rate
watch -n 1 'celery -A app.tasks inspect active | grep embedding | wc -l'
```

---

#### Task 4.3: Add Prometheus Metrics
**Owner:** Backend Engineer  
**Effort:** 3 hours  
**Dependencies:** None

**Acceptance Criteria:**
- [ ] All metrics defined in observability.md implemented
- [ ] Metrics exported on `/metrics` endpoint
- [ ] Verified in Prometheus

**Metrics to Add:**
```python
# app/main.py (after line 298)
EMBEDDING_BATCH_DURATION = Histogram(
    'celery_task_execution_seconds',
    'Task execution time',
    ['task_name', 'queue']
)
FAISS_SEARCH_DURATION = Histogram(
    'apfa_faiss_search_seconds',
    'FAISS search duration',
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.2, 0.5, 1.0]
)
INDEX_VECTOR_COUNT = Gauge('apfa_index_vector_count', 'Vector count')
INDEX_MEMORY_BYTES = Gauge('apfa_index_memory_bytes', 'Index memory')
```

**Instrumentation:**
```python
# In load_rag_index_from_minio()
INDEX_VECTOR_COUNT.set(len(df))
INDEX_MEMORY_BYTES.set(len(df) * 384 * 4)

# In retrieve_loan_data() (line 106)
search_start = time.time()
_, indices = faiss_index.search(query_emb, k=5)
FAISS_SEARCH_DURATION.observe(time.time() - search_start)
```

**Verification:**
```bash
curl http://localhost:8000/metrics | grep apfa_
```

---

### Day 10-11: Scheduled Jobs & Maintenance

#### Task 5.1: Configure Celery Beat Schedules
**Owner:** Backend Engineer  
**Effort:** 2 hours  
**Dependencies:** None

**Acceptance Criteria:**
- [ ] Beat schedule defined in tasks.py
- [ ] Schedules validated with `inspect scheduled`
- [ ] Logs confirm execution

**Implementation:**
```python
# app/tasks.py (bottom)
app.conf.beat_schedule = {
    'rebuild-index-hourly': {
        'task': 'app.tasks.embed_all_documents',
        'schedule': crontab(minute=0),
        'options': {'queue': 'embedding'}
    },
    'cleanup-daily': {
        'task': 'app.tasks.cleanup_old_embeddings',
        'schedule': crontab(hour=2, minute=0),
        'options': {'queue': 'maintenance'}
    },
    'compute-stats-every-5min': {
        'task': 'app.tasks.compute_index_stats',
        'schedule': crontab(minute='*/5'),
        'options': {'queue': 'maintenance'}
    }
}
```

**Verification:**
```bash
celery -A app.tasks inspect scheduled
# Expected: 3 scheduled tasks listed
```

---

#### Task 5.2: Implement cleanup_old_embeddings
**Owner:** Backend Engineer  
**Effort:** 3 hours  
**Dependencies:** None

**Acceptance Criteria:**
- [ ] Deletes files older than retention_days
- [ ] Preserves current index
- [ ] Logs deletion count
- [ ] Updates Prometheus counter

**Test Cases:**
```python
def test_cleanup_old_embeddings():
    # Create old and new files
    create_test_file('embeddings/batches/old.pkl', days_old=10)
    create_test_file('embeddings/batches/new.pkl', days_old=3)
    
    cleanup_old_embeddings.apply(args=[7])
    
    # Verify old deleted, new preserved
    assert not file_exists('old.pkl')
    assert file_exists('new.pkl')
```

---

#### Task 5.3: Implement compute_index_stats
**Owner:** Backend Engineer  
**Effort:** 3 hours  
**Dependencies:** None

**Acceptance Criteria:**
- [ ] Computes all stats in observability.md
- [ ] Updates Prometheus gauges
- [ ] Calculates migration urgency score
- [ ] Logs results

**Implementation:**
```python
@app.task(queue='maintenance')
def compute_index_stats():
    # Load current index
    version = get_current_version()
    index = load_index(version)
    
    # Compute stats
    stats = {
        'vector_count': index.ntotal,
        'memory_mb': (index.ntotal * 384 * 4) / (1024**2),
        'migration_urgency': calculate_migration_urgency(index.ntotal)
    }
    
    # Update metrics
    INDEX_VECTOR_COUNT.set(stats['vector_count'])
    INDEX_MEMORY_BYTES.set(stats['memory_mb'] * 1024**2)
    
    return stats
```

---

### Day 12-14: Monitoring & Alerting

#### Task 6.1: Create Grafana Dashboards
**Owner:** SRE Engineer  
**Effort:** 6 hours  
**Dependencies:** Task 4.3

**Acceptance Criteria:**
- [ ] APFA Performance dashboard imported
- [ ] Celery Workers dashboard imported
- [ ] All panels displaying data
- [ ] Dashboards shared with team

**Files to Create:**
- `monitoring/grafana-dashboards/apfa-performance.json` (See observability.md)
- `monitoring/grafana-dashboards/celery-workers.json`

**Import Command:**
```bash
curl -X POST http://admin:admin@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @monitoring/grafana-dashboards/apfa-performance.json
```

**Verification:**
- Navigate to http://localhost:3000/dashboards
- Verify 2 dashboards visible
- Check all panels loading data

---

#### Task 6.2: Configure Prometheus Alerting
**Owner:** SRE Engineer  
**Effort:** 4 hours  
**Dependencies:** Task 4.3

**Acceptance Criteria:**
- [ ] `monitoring/alerts.yml` created
- [ ] Alerts loaded in Prometheus
- [ ] Test alerts firing correctly

**File to Create:**
- `monitoring/alerts.yml` (See observability.md)

**Update Prometheus Config:**
```yaml
# monitoring/prometheus.yml
rule_files:
  - 'alerts.yml'
```

**Test Alerts:**
```bash
# Trigger SlowEmbeddingBatches alert
# (Temporarily reduce alert threshold to 0.1s for testing)

# Check alert status
curl http://localhost:9090/api/v1/alerts | jq
```

---

#### Task 6.3: Set Up AlertManager (Optional)
**Owner:** SRE Engineer  
**Effort:** 4 hours  
**Dependencies:** Task 6.2

**Acceptance Criteria:**
- [ ] AlertManager service added to docker-compose
- [ ] Slack/email integration configured
- [ ] Test alert received

**docker-compose.yml:**
```yaml
alertmanager:
  image: prom/alertmanager:latest
  ports:
    - "9093:9093"
  volumes:
    - ./monitoring/alertmanager.yml:/etc/alertmanager/alertmanager.yml
  restart: unless-stopped
```

**alertmanager.yml:**
```yaml
route:
  receiver: 'slack'
  group_wait: 30s
  group_interval: 5m

receivers:
  - name: 'slack'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/XXX'
        channel: '#apfa-alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ .CommonAnnotations.description }}'
```

---

## Week 3: Production Deployment

### Day 15-16: Staging Deployment & Testing

#### Task 7.1: Deploy to Staging Environment
**Owner:** DevOps Engineer  
**Effort:** 4 hours  
**Dependencies:** Week 2 complete

**Acceptance Criteria:**
- [ ] All services deployed to staging
- [ ] Health checks passing
- [ ] Monitoring dashboards accessible

**Deployment Steps:**
```bash
# 1. Set environment
export ENV=staging

# 2. Deploy services
docker-compose -f docker-compose.staging.yml up -d

# 3. Verify health
curl https://staging.apfa.io/health
curl https://staging.apfa.io/metrics

# 4. Check Flower
curl https://staging.apfa.io:5555/api/workers
```

---

#### Task 7.2: Load Testing
**Owner:** QA Engineer  
**Effort:** 6 hours  
**Dependencies:** Task 7.1

**Acceptance Criteria:**
- [ ] Load tests executed for 1K, 10K, 100K requests
- [ ] P95 latency <3s achieved
- [ ] Error rate <0.1%
- [ ] Results documented

**Load Test Script:**
```bash
# Install wrk
brew install wrk

# Create request payload
cat > payload.lua <<EOF
wrk.method = "POST"
wrk.body = '{"query": "What is the best loan for me?"}'
wrk.headers["Content-Type"] = "application/json"
wrk.headers["Authorization"] = "Bearer <JWT_TOKEN>"
EOF

# Run load test (10 threads, 100 connections, 60 seconds)
wrk -t10 -c100 -d60s -s payload.lua https://staging.apfa.io/generate-advice

# Expected results:
# Requests/sec: >10
# Latency avg: <3s
# Latency p95: <5s
# Errors: <0.1%
```

**Test Matrix:**

| Test | Threads | Connections | Duration | Expected RPS | Expected P95 |
|------|---------|-------------|----------|--------------|--------------|
| Light | 2 | 10 | 30s | >5 | <2s |
| Medium | 10 | 100 | 60s | >10 | <3s |
| Heavy | 20 | 500 | 120s | >20 | <5s |

---

#### Task 7.3: Failure Scenario Testing
**Owner:** QA Engineer  
**Effort:** 4 hours  
**Dependencies:** Task 7.1

**Acceptance Criteria:**
- [ ] Worker crash recovery tested
- [ ] Redis unavailable scenario tested
- [ ] MinIO unavailable scenario tested
- [ ] All failures handled gracefully

**Test Cases:**

1. **Worker Crash:**
   ```bash
   # Kill one worker
   docker kill <worker_container_id>
   
   # Verify:
   # - Tasks automatically retried
   # - Other workers pick up tasks
   # - No user-facing errors
   ```

2. **Redis Down:**
   ```bash
   # Stop Redis
   docker-compose stop redis
   
   # Verify:
   # - FastAPI falls back to in-memory cache
   # - No 500 errors
   # - Alert fired
   ```

3. **MinIO Down:**
   ```bash
   # Stop MinIO
   docker-compose stop minio
   
   # Verify:
   # - FastAPI falls back to sync index build
   # - Higher latency but no errors
   # - Alert fired
   ```

---

### Day 17-18: Production Deployment

#### Task 8.1: Pre-Deployment Checklist
**Owner:** Project Lead  
**Effort:** 2 hours  
**Dependencies:** Task 7.2, 7.3

**Checklist:**
- [ ] All success criteria met
- [ ] Load tests passed
- [ ] Failure scenarios tested
- [ ] Monitoring dashboards configured
- [ ] Alerts tested
- [ ] Documentation complete
- [ ] Team notified (maintenance window if needed)
- [ ] Rollback plan prepared

---

#### Task 8.2: Production Deployment
**Owner:** DevOps Engineer  
**Effort:** 4 hours  
**Dependencies:** Task 8.1

**Deployment Strategy:** Blue-Green

**Steps:**
```bash
# 1. Deploy new stack (green)
docker-compose -f docker-compose.prod.yml up -d --scale apfa_green=4

# 2. Trigger initial embedding job
celery -A app.tasks call app.tasks.embed_all_documents

# 3. Wait for index build (monitor in Flower)
# Expected: 10-15 minutes for 100K documents

# 4. Health check green stack
curl https://green.apfa.io/health

# 5. Switch traffic (load balancer)
# Route 10% → green, 90% → blue

# 6. Monitor for 30 minutes
# Check: Error rate, latency, logs

# 7. Gradually shift traffic
# 50% → green, 50% → blue (15 min)
# 100% → green (if no issues)

# 8. Decommission blue stack
docker-compose -f docker-compose.prod.yml down apfa_blue
```

**Rollback Plan:**
```bash
# If issues detected:
# 1. Route 100% traffic back to blue
# 2. Investigate logs
# 3. Fix issue in staging
# 4. Retry deployment
```

---

#### Task 8.3: Post-Deployment Validation
**Owner:** SRE Engineer  
**Effort:** 3 hours  
**Dependencies:** Task 8.2

**Validation Checklist:**
- [ ] All services healthy
- [ ] Metrics confirming latency improvement
- [ ] No errors in logs (past 1 hour)
- [ ] Cache hit rate >80%
- [ ] Celery workers processing tasks
- [ ] Beat scheduler running

**Validation Queries:**
```promql
# P95 latency (should be <3s)
histogram_quantile(0.95, rate(apfa_response_time_seconds_bucket[5m]))

# Error rate (should be <0.1%)
rate(apfa_requests_total{status=~"5.."}[5m]) / rate(apfa_requests_total[5m])

# Cache hit rate (should be >80%)
rate(apfa_cache_hits_total[5m]) / (rate(apfa_cache_hits_total[5m]) + rate(apfa_cache_misses_total[5m]))
```

---

#### Task 8.4: 24-Hour Monitoring
**Owner:** On-Call Engineer  
**Effort:** Passive (24 hours)  
**Dependencies:** Task 8.3

**Monitoring Plan:**
- Check dashboards every 2 hours
- Respond to any alerts within 15 minutes
- Log any anomalies
- Collect user feedback (if available)

**Escalation Path:**
- Issues detected → Notify project lead
- Critical issues → Initiate rollback
- Minor issues → Create bug tickets

---

### Day 19-21: Documentation & Training

#### Task 9.1: Create Architecture Decision Records
**Owner:** Backend Team Lead  
**Effort:** 4 hours  
**Dependencies:** None

**ADRs to Create:**
- [x] ADR-001: Celery vs RQ (see next section)
- [ ] ADR-002: IndexFlatIP vs IndexIVFFlat Migration Strategy
- [ ] ADR-003: Multi-Queue Architecture Design

---

#### Task 9.2: Update Documentation
**Owner:** Technical Writer  
**Effort:** 6 hours  
**Dependencies:** Project complete

**Documents to Create/Update:**
- [x] docs/background-jobs.md
- [x] docs/observability.md
- [ ] docs/architecture.md (add Celery section)
- [ ] README.md (update features and deployment)
- [ ] docs/deployment-operations.md

---

#### Task 9.3: Team Training Session
**Owner:** Project Lead  
**Effort:** 1 hour  
**Dependencies:** Task 9.2

**Training Agenda:**
1. **Overview (10 min):** Problem, solution, results
2. **Architecture (15 min):** Celery, queues, hot-swap
3. **Monitoring (15 min):** Dashboards, alerts, runbooks
4. **Hands-On (20 min):** Trigger task, view in Flower, check metrics

**Training Materials:**
- Slides: Architecture diagrams, before/after metrics
- Hands-on: Live demo in staging environment
- Reference: Links to documentation

**Attendance:** All backend engineers, SRE team

---

#### Task 9.4: Knowledge Base Update
**Owner:** Technical Writer  
**Effort:** 2 hours  
**Dependencies:** Task 9.2

**Updates:**
- Add FAQ section
- Create troubleshooting guide
- Link to monitoring dashboards
- Document common operations (scaling, debugging)

---

## Risk Management

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Redis failure in production** | Medium | High | Graceful fallback to in-memory cache, alert on-call |
| **Worker overload** | Medium | Medium | Auto-scaling alerts, queue depth monitoring |
| **Index corruption** | Low | High | Automatic rebuild from embeddings, version checksums |
| **Deployment failure** | Low | Critical | Blue-green deployment, tested rollback procedure |
| **Team knowledge gap** | High | Medium | Comprehensive docs, training session, runbooks |
| **Unexpected performance regression** | Medium | High | Extensive staging testing, gradual rollout, rollback plan |

---

## Dependencies

### External Dependencies
- **MinIO**: Must be running and accessible
- **Delta Lake**: Customer data must be available
- **AWS Bedrock**: For risk simulation (non-critical)

### Internal Dependencies
- **Docker**: Version 20.10+
- **Python**: 3.11+
- **Redis**: Version 7+
- **Prometheus**: Version 2.45+
- **Grafana**: Version 10.0+

---

## Communication Plan

### Stakeholders
- **Project Lead:** Daily standups, weekly status
- **Backend Team:** Daily updates in #apfa-backend Slack channel
- **SRE Team:** Deployment coordination, monitoring setup
- **Product Team:** Weekly progress, post-launch metrics

### Status Updates
- **Daily:** Slack channel updates on completed tasks
- **Weekly:** Email summary to stakeholders
- **Ad-hoc:** Immediate notification of blockers or risks

### Channels
- **Slack:** #apfa-backend (technical), #apfa-general (stakeholders)
- **Email:** apfa-team@company.com
- **Docs:** Confluence page with live task tracking

---

## Success Metrics (Post-Launch)

### Week 1 Post-Launch
- [ ] P95 latency <3s confirmed
- [ ] Zero production incidents
- [ ] Cache hit rate >80%
- [ ] Team comfortable with new system

### Month 1 Post-Launch
- [ ] 100x performance improvement sustained
- [ ] Zero hot-swap failures
- [ ] Scheduled jobs running reliably
- [ ] Monitoring dashboards used daily

### Month 3 Post-Launch
- [ ] Scale to 500K vectors without IndexIVFFlat migration
- [ ] <1 alert per week
- [ ] Team self-sufficient (no escalations)

---

## Project Tracking

**Tool:** JIRA  
**Board:** APFA-CELERY  
**Sprint Length:** 1 week

### Task Breakdown
- **Total Tasks:** 40
- **Epic 1 (Week 1):** 15 tasks
- **Epic 2 (Week 2):** 12 tasks
- **Epic 3 (Week 3):** 13 tasks

### Daily Standup Format
1. **What I completed yesterday**
2. **What I'm working on today**
3. **Any blockers**

---

## Appendices

### Appendix A: Testing Checklist

#### Unit Tests (80%+ Coverage)
- [ ] embed_document_batch
- [ ] embed_all_documents
- [ ] build_faiss_index
- [ ] hot_swap_index
- [ ] cleanup_old_embeddings
- [ ] compute_index_stats

#### Integration Tests
- [ ] End-to-end embedding pipeline
- [ ] Index hot-swap during load
- [ ] Failure recovery scenarios

#### Load Tests
- [ ] 1K concurrent requests
- [ ] 10K concurrent requests
- [ ] 100K concurrent requests

---

### Appendix B: Rollback Procedure

**Scenario:** Critical issue detected in production post-deployment

**Steps:**
1. **Stop accepting new traffic** (route to blue stack)
2. **Investigate logs** (5-10 minutes)
3. **Decision:** Fix forward or rollback
4. **If rollback:**
   - Revert FastAPI to sync index loading
   - Stop Celery workers
   - Restart APFA containers
   - Monitor for 30 minutes
5. **Post-mortem:** Document issue and prevention plan

**Time to Rollback:** <10 minutes

---

### Appendix C: Cost Analysis

**Infrastructure Costs (AWS):**

| Resource | Before | After | Delta |
|----------|--------|-------|-------|
| **ECS Fargate Tasks** | 4 tasks | 4 tasks (APFA) + 4 tasks (Celery) | +$150/month |
| **Redis ElastiCache** | None | 1 node (t3.small) | +$30/month |
| **MinIO (S3)** | 10GB | 20GB (embeddings + indexes) | +$0.50/month |
| **Total** | $500/month | $680/month | **+$180/month (36% increase)** |

**ROI:**
- Cost increase: $180/month
- Performance improvement: 100x latency reduction
- User experience: Significantly improved
- Scalability: Support 10x more users
- **Verdict:** Highly cost-effective

---

## Sign-Off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| **Project Lead** | | | |
| **Backend Team Lead** | | | |
| **SRE Lead** | | | |
| **Product Manager** | | | |

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-11  
**Next Review:** 2025-11-01 (post-deployment)

