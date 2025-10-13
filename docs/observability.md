# Observability & Monitoring

**Version:** 1.0  
**Last Updated:** 2025-10-11  
**Owner:** SRE Team  
**Status:** Active

---

## Table of Contents

1. [Overview](#overview)
2. [Monitoring Stack](#monitoring-stack)
3. [Key Metrics](#key-metrics)
4. [Grafana Dashboards](#grafana-dashboards)
5. [Alerting Rules](#alerting-rules)
6. [Alert Response Runbook](#alert-response-runbook)
7. [Performance Baselines](#performance-baselines)
8. [Log Aggregation](#log-aggregation)
9. [Tracing](#tracing)
10. [Capacity Planning](#capacity-planning)

---

## Overview

### Observability Pillars

APFA observability is built on three pillars:

1. **Metrics** (Prometheus + Grafana): Quantitative measurements over time
2. **Logs** (Structured logging): Event-based debugging information
3. **Traces** (OpenTelemetry): Distributed request tracing

### Goals

- **Real-time visibility**: Detect issues within 1 minute
- **Root cause analysis**: Diagnose problems in <5 minutes
- **Proactive alerting**: Warn before user impact
- **Performance tracking**: Validate optimization impact
- **Capacity planning**: Predict scaling needs 30 days ahead

---

## Monitoring Stack

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │  FastAPI │    │  Celery  │    │  Redis   │              │
│  │  (APFA)  │    │ Workers  │    │  Broker  │              │
│  └─────┬────┘    └────┬─────┘    └────┬─────┘              │
│        │ expose       │ expose        │ expose             │
│        │ :8000/metrics│ :8000/metrics │ :9121 (exporter)   │
└────────┼──────────────┼───────────────┼─────────────────────┘
         │              │               │
         │              │               │
┌────────▼──────────────▼───────────────▼─────────────────────┐
│                    Prometheus                                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Time-Series Database                                │   │
│  │  • Scrape interval: 15s                              │   │
│  │  │  Retention: 30 days                                │   │
│  │  • Query engine: PromQL                              │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         │ query
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                      Grafana                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Performance  │  │  Celery      │  │  Alerting    │      │
│  │  Dashboard   │  │  Dashboard   │  │  Dashboard   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────────────────────────────────────────┘
                         │
                         │ alert
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                   AlertManager                               │
│  Routes to: Slack, PagerDuty, Email                         │
└──────────────────────────────────────────────────────────────┘
```

### Component Versions

| Component | Version | Purpose |
|-----------|---------|---------|
| **Prometheus** | 2.45+ | Metrics collection & storage |
| **Grafana** | 10.0+ | Visualization & dashboards |
| **Flower** | 2.0+ | Celery task monitoring |
| **Redis Exporter** | 1.50+ | Redis metrics export |
| **AlertManager** | 0.26+ | Alert routing & grouping |
| **prometheus-client** | 0.19.0 | Python metrics library |

---

## Key Metrics

### Application Metrics (FastAPI)

#### Request Metrics

```python
# Counter: Total requests
apfa_requests_total{method="POST", endpoint="/generate-advice", status="200"}

# Histogram: Response time
apfa_response_time_seconds_bucket{endpoint="/generate-advice", le="1.0"}

# Gauge: Active requests
apfa_active_requests
```

**PromQL Queries:**

```promql
# Request rate (requests/sec)
rate(apfa_requests_total[5m])

# P95 latency
histogram_quantile(0.95, rate(apfa_response_time_seconds_bucket[5m]))

# Error rate
rate(apfa_requests_total{status=~"5.."}[5m]) / rate(apfa_requests_total[5m])
```

#### Cache Metrics

```python
# Cache hit rate
apfa_cache_hits_total
apfa_cache_misses_total

# Effective cache hit rate
rate(apfa_cache_hits_total[5m]) / (rate(apfa_cache_hits_total[5m]) + rate(apfa_cache_misses_total[5m]))
```

**Target:** Cache hit rate >80%

#### Error Metrics

```python
# Error counter by type
apfa_errors_total{type="rag"}      # RAG errors
apfa_errors_total{type="llm"}      # LLM errors
apfa_errors_total{type="external"} # External service errors
```

---

### Celery Metrics

#### Task Execution

```python
# Histogram: Task execution time
celery_task_execution_seconds_bucket{task_name="embed_document_batch", queue="embedding"}

# Counter: Task success/failure
celery_task_success_total{task_name="embed_all_documents"}
celery_task_failure_total{task_name="build_faiss_index", exception_type="ValueError"}
```

**PromQL Queries:**

```promql
# P95 task execution time
histogram_quantile(0.95, rate(celery_task_execution_seconds_bucket[5m]))

# Task failure rate
rate(celery_task_failure_total[5m]) / (rate(celery_task_success_total[5m]) + rate(celery_task_failure_total[5m]))
```

#### Queue Depth

```python
# Gauge: Pending tasks in queue
celery_queue_depth{queue_name="embedding"}
celery_queue_depth{queue_name="indexing"}
celery_queue_depth{queue_name="maintenance"}
```

**Thresholds:**
- **Normal:** <10 tasks
- **Warning:** 10-50 tasks
- **Critical:** >50 tasks

#### Custom Celery Metrics

```python
# Embedding performance
celery_embedding_batches_total        # Total batches processed
celery_embedding_batch_duration_seconds  # Time per batch

# Index versioning
celery_faiss_index_version            # Current index version (numeric hash)
```

---

### FAISS/RAG Metrics

#### Search Performance

```python
# Histogram: FAISS search latency
apfa_faiss_search_seconds_bucket{le="0.01"}   # <10ms
apfa_faiss_search_seconds_bucket{le="0.1"}    # <100ms
apfa_faiss_search_seconds_bucket{le="0.5"}    # <500ms
```

**PromQL:**

```promql
# P95 search latency (milliseconds)
histogram_quantile(0.95, rate(apfa_faiss_search_seconds_bucket[5m])) * 1000

# Search latency as % of total request time
rate(apfa_faiss_search_seconds_sum[5m]) / rate(apfa_response_time_seconds_sum[5m]) * 100
```

**Thresholds:**
- **Excellent:** <50ms (P95)
- **Good:** 50-100ms (P95)
- **Warning:** 100-200ms (P95)
- **Critical:** >200ms (P95) → Consider IndexIVFFlat migration

#### Index Characteristics

```python
# Gauge: Index size
apfa_index_vector_count              # Number of vectors
apfa_index_memory_bytes              # Memory usage

# Counter: Index operations
apfa_index_reload_total              # Number of hot-swaps
```

**PromQL:**

```promql
# Memory usage (MB)
apfa_index_memory_bytes / (1024 * 1024)

# Vectors added per day
increase(apfa_index_vector_count[1d])

# Days until 500K threshold
(500000 - apfa_index_vector_count) / (deriv(apfa_index_vector_count[7d]) * 86400)
```

---

### System Metrics

#### Resource Usage

```python
# CPU
rate(process_cpu_seconds_total{job="apfa"}[5m]) * 100

# Memory
process_resident_memory_bytes{job="apfa"} / (1024 * 1024)

# File descriptors
process_open_fds{job="apfa"}
```

#### Redis Metrics

```python
# Memory
redis_memory_used_bytes / redis_memory_max_bytes * 100

# Commands processed
rate(redis_commands_processed_total[5m])

# Cache hit rate
rate(redis_keyspace_hits_total[5m]) / (rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m]))
```

---

## Grafana Dashboards

### Dashboard 1: APFA Performance & Scaling

**File:** `monitoring/grafana-dashboards/apfa-performance.json`

**Sections:**

#### Row 1: Critical Path - Embedding Performance

**Panel 1.1: Embedding Batch Duration (P95/P99)**
```json
{
  "title": "Embedding Batch Duration",
  "type": "graph",
  "targets": [
    {
      "expr": "histogram_quantile(0.95, rate(celery_task_execution_seconds_bucket{task_name=~\".*embed.*\"}[5m]))",
      "legendFormat": "P95"
    },
    {
      "expr": "histogram_quantile(0.99, rate(celery_task_execution_seconds_bucket{task_name=~\".*embed.*\"}[5m]))",
      "legendFormat": "P99"
    }
  ],
  "yaxes": [{"format": "s", "label": "Duration"}],
  "alert": {
    "name": "SlowEmbeddingBatches",
    "conditions": [{"evaluator": {"params": [2.0], "type": "gt"}}],
    "message": "Embedding P95 >2s (target: <1s)"
  }
}
```

**Panel 1.2: Embedding Throughput**
```json
{
  "title": "Documents Embedded/sec",
  "type": "graph",
  "targets": [
    {"expr": "rate(celery_embedding_batches_total[5m]) * 1000"}
  ]
}
```

#### Row 2: Migration Triggers

**Panel 2.1: Vector Count vs Thresholds**
```json
{
  "title": "Vector Count & Migration Thresholds",
  "type": "graph",
  "targets": [
    {"expr": "apfa_index_vector_count", "legendFormat": "Current"},
    {"expr": "400000", "legendFormat": "Warning (400K)"},
    {"expr": "500000", "legendFormat": "Critical (500K)"}
  ],
  "thresholds": [
    {"value": 400000, "colorMode": "critical"},
    {"value": 500000, "colorMode": "custom", "fillColor": "rgba(255,0,0,0.3)"}
  ]
}
```

**Panel 2.2: FAISS Search Latency**
```json
{
  "title": "FAISS Search Latency (ms)",
  "type": "graph",
  "targets": [
    {"expr": "histogram_quantile(0.95, rate(apfa_faiss_search_seconds_bucket[5m])) * 1000"}
  ],
  "thresholds": [
    {"value": 100, "colorMode": "warning"},
    {"value": 200, "colorMode": "critical"}
  ]
}
```

#### Row 3: Request Performance

**Panel 3.1: Request Latency Breakdown**
```json
{
  "title": "Request Latency Components",
  "type": "graph",
  "targets": [
    {"expr": "histogram_quantile(0.95, rate(apfa_response_time_seconds_bucket[5m]))", "legendFormat": "Total (P95)"},
    {"expr": "histogram_quantile(0.95, rate(apfa_faiss_search_seconds_bucket[5m]))", "legendFormat": "FAISS"},
    {"expr": "avg(rate(celery_task_execution_seconds_sum{task_name=\"generate_loan_advice\"}[5m]))", "legendFormat": "LLM"}
  ]
}
```

#### Row 4: Cache Performance

**Panel 4.1: Cache Hit Rate** (Singlestat)
```json
{
  "title": "Cache Hit Rate",
  "type": "singlestat",
  "targets": [
    {"expr": "rate(apfa_cache_hits_total[5m]) / (rate(apfa_cache_hits_total[5m]) + rate(apfa_cache_misses_total[5m])) * 100"}
  ],
  "thresholds": "70,85",
  "colors": ["red", "yellow", "green"],
  "format": "percent"
}
```

**Panel 4.2: Effective Latency with Caching**
```json
{
  "title": "Effective Latency (Considering Cache)",
  "type": "graph",
  "targets": [
    {"expr": "(rate(apfa_cache_misses_total[5m]) * histogram_quantile(0.95, rate(apfa_response_time_seconds_bucket[5m]))) + (rate(apfa_cache_hits_total[5m]) * 0.5)"}
  ]
}
```

#### Row 5: Celery Workers

**Panel 5.1: Queue Depth**
```json
{
  "title": "Celery Queue Depth",
  "type": "graph",
  "targets": [
    {"expr": "celery_queue_depth{queue_name=\"embedding\"}", "legendFormat": "Embedding"},
    {"expr": "celery_queue_depth{queue_name=\"indexing\"}", "legendFormat": "Indexing"},
    {"expr": "celery_queue_depth{queue_name=\"maintenance\"}", "legendFormat": "Maintenance"}
  ]
}
```

**Panel 5.2: Task Success/Failure Rate**
```json
{
  "title": "Task Execution Rate",
  "type": "graph",
  "targets": [
    {"expr": "rate(celery_task_success_total[5m])", "legendFormat": "Success {{task_name}}"},
    {"expr": "rate(celery_task_failure_total[5m])", "legendFormat": "Failure {{task_name}}"}
  ]
}
```

#### Row 6: Migration Planning

**Panel 6.1: Days Until Migration** (Singlestat)
```json
{
  "title": "Days Until 500K Threshold",
  "type": "singlestat",
  "targets": [
    {"expr": "(500000 - apfa_index_vector_count) / (deriv(apfa_index_vector_count[7d]) * 86400)"}
  ],
  "thresholds": "7,30",
  "colors": ["red", "yellow", "green"],
  "format": "none",
  "postfix": " days"
}
```

**Panel 6.2: Migration Urgency Score** (Gauge)
```json
{
  "title": "Migration Urgency",
  "type": "gauge",
  "targets": [
    {"expr": "max(apfa_migration_urgency_score)"}
  ],
  "thresholds": [
    {"value": 0, "color": "green"},
    {"value": 70, "color": "yellow"},
    {"value": 90, "color": "red"}
  ],
  "min": 0,
  "max": 100
}
```

---

### Dashboard 2: Celery Worker Performance

**File:** `monitoring/grafana-dashboards/celery-workers.json`

**Panels:**

1. **Worker CPU Usage** - `rate(process_cpu_seconds_total{job="celery"}[5m]) * 100`
2. **Worker Memory Usage** - `process_resident_memory_bytes{job="celery"} / (1024*1024)`
3. **Task Execution Heatmap** - `rate(celery_task_execution_seconds_bucket[5m])`
4. **Active Workers** - `up{job="celery"}`
5. **Task Latency by Queue** - `histogram_quantile(0.95, rate(celery_task_execution_seconds_bucket[5m])) by (queue)`

---

### Dashboard 3: System Health

**File:** `monitoring/grafana-dashboards/system-health.json`

**Panels:**

1. **Service Availability** - `up{job=~"apfa|celery|redis"}`
2. **HTTP Status Codes** - `rate(apfa_requests_total[5m]) by (status)`
3. **Error Rate by Type** - `rate(apfa_errors_total[5m]) by (type)`
4. **Redis Memory Usage** - `redis_memory_used_bytes / redis_memory_max_bytes * 100`
5. **Container Restarts** - `changes(container_last_seen[1h])`

---

## Alerting Rules

### File: `monitoring/alerts.yml`

```yaml
groups:
  - name: apfa_scaling_alerts
    interval: 30s
    rules:
      
      # ============================================================
      # CRITICAL: Migration Thresholds
      # ============================================================
      
      - alert: CriticalMigrationRequired
        expr: apfa_index_vector_count > 500000
        for: 1m
        labels:
          severity: critical
          component: faiss
          team: backend
        annotations:
          summary: "FAISS must migrate to IndexIVFFlat NOW"
          description: "Vector count is {{ $value }}, exceeds 500K critical threshold. Migration required within 48 hours."
          runbook: "https://docs.apfa.io/scaling-migration.md#indexflatip-to-indexivfflat"
          dashboard: "https://grafana.apfa.io/d/performance"
      
      - alert: ApproachingMigrationThreshold
        expr: apfa_index_vector_count > 400000
        for: 5m
        labels:
          severity: warning
          component: faiss
          team: backend
        annotations:
          summary: "FAISS approaching migration threshold"
          description: "Vector count is {{ $value }}. Plan IndexIVFFlat migration within 7 days."
          runbook: "https://docs.apfa.io/scaling-migration.md#migration-planning"
      
      # ============================================================
      # CRITICAL: Performance Degradation
      # ============================================================
      
      - alert: HighFAISSSearchLatency
        expr: histogram_quantile(0.95, rate(apfa_faiss_search_seconds_bucket[5m])) > 0.2
        for: 5m
        labels:
          severity: warning
          component: faiss
          team: backend
        annotations:
          summary: "FAISS search latency degraded"
          description: "P95 search latency is {{ $value }}s (>200ms threshold). Consider IndexIVFFlat migration."
          dashboard: "https://grafana.apfa.io/d/performance?viewPanel=4"
      
      - alert: SlowRequestLatency
        expr: histogram_quantile(0.95, rate(apfa_response_time_seconds_bucket[5m])) > 10
        for: 3m
        labels:
          severity: critical
          component: api
          team: backend
        annotations:
          summary: "Request latency exceeds SLA"
          description: "P95 latency is {{ $value }}s (SLA: <10s). Immediate investigation required."
          runbook: "https://docs.apfa.io/troubleshooting.md#high-latency"
      
      # ============================================================
      # WARNING: Celery Performance
      # ============================================================
      
      - alert: SlowEmbeddingBatches
        expr: histogram_quantile(0.95, rate(celery_task_execution_seconds_bucket{task_name=~".*embed.*"}[5m])) > 2
        for: 3m
        labels:
          severity: warning
          component: celery
          team: backend
        annotations:
          summary: "Embedding batch processing slow"
          description: "P95 batch duration is {{ $value }}s (target: <1s). Check worker CPU and scale if needed."
          runbook: "https://docs.apfa.io/background-jobs.md#slow-embedding-performance"
      
      - alert: CeleryQueueBacklog
        expr: celery_queue_depth{queue_name="embedding"} > 50
        for: 10m
        labels:
          severity: warning
          component: celery
          team: backend
        annotations:
          summary: "Celery embedding queue backlog"
          description: "{{ $value }} tasks pending. Scale workers: docker-compose up -d --scale celery_worker=8"
          runbook: "https://docs.apfa.io/background-jobs.md#scaling-workers"
      
      - alert: HighTaskFailureRate
        expr: rate(celery_task_failure_total[5m]) / (rate(celery_task_success_total[5m]) + rate(celery_task_failure_total[5m])) > 0.05
        for: 5m
        labels:
          severity: warning
          component: celery
          team: backend
        annotations:
          summary: "High Celery task failure rate"
          description: "{{ $value | humanizePercentage }} of tasks failing. Check logs: docker-compose logs celery_worker"
      
      # ============================================================
      # CRITICAL: Service Health
      # ============================================================
      
      - alert: ServiceDown
        expr: up{job=~"apfa|celery|redis"} == 0
        for: 1m
        labels:
          severity: critical
          component: infrastructure
          team: sre
        annotations:
          summary: "{{ $labels.job }} service is down"
          description: "{{ $labels.job }} has been down for >1 minute. Check: docker-compose ps"
          runbook: "https://docs.apfa.io/deployment-operations.md#service-recovery"
      
      - alert: HighErrorRate
        expr: rate(apfa_requests_total{status=~"5.."}[5m]) / rate(apfa_requests_total[5m]) > 0.05
        for: 3m
        labels:
          severity: critical
          component: api
          team: backend
        annotations:
          summary: "High API error rate"
          description: "{{ $value | humanizePercentage }} of requests failing. Check logs for root cause."
          dashboard: "https://grafana.apfa.io/d/system-health?viewPanel=3"
      
      # ============================================================
      # WARNING: Resource Pressure
      # ============================================================
      
      - alert: HighMemoryUsage
        expr: (process_resident_memory_bytes / 4294967296) > 0.85
        for: 5m
        labels:
          severity: warning
          component: infrastructure
          team: sre
        annotations:
          summary: "{{ $labels.job }} high memory usage"
          description: "Memory usage is {{ $value | humanizePercentage }} of 4GB container limit."
      
      - alert: RedisMemoryPressure
        expr: (redis_memory_used_bytes / redis_memory_max_bytes) > 0.90
        for: 5m
        labels:
          severity: warning
          component: redis
          team: sre
        annotations:
          summary: "Redis approaching memory limit"
          description: "Redis memory usage: {{ $value | humanizePercentage }}. Consider increasing maxmemory."
      
      # ============================================================
      # INFO: Capacity Planning
      # ============================================================
      
      - alert: MigrationPlanning
        expr: (500000 - apfa_index_vector_count) / (deriv(apfa_index_vector_count[7d]) * 86400) < 30
        for: 1h
        labels:
          severity: info
          component: capacity
          team: backend
        annotations:
          summary: "Migration needed within 30 days"
          description: "At current growth rate, will reach 500K vectors in {{ $value }} days. Start migration planning."
          runbook: "https://docs.apfa.io/scaling-migration.md"
```

---

## Alert Response Runbook

### Alert: CriticalMigrationRequired

**Severity:** Critical  
**Trigger:** `apfa_index_vector_count > 500000`  
**SLA:** Respond within 1 hour, resolve within 48 hours

**Response Steps:**

1. **Acknowledge alert** in PagerDuty
2. **Assess urgency:**
   ```bash
   # Check current performance
   curl http://localhost:9090/api/v1/query?query=histogram_quantile(0.95,rate(apfa_faiss_search_seconds_bucket[5m]))
   
   # If P95 latency >500ms: IMMEDIATE action required
   # If P95 latency <200ms: Can delay 24-48 hours
   ```

3. **Execute migration:** Follow [Migration Procedure](scaling-migration.md#indexflatip-to-indexivfflat)

4. **Validate performance:**
   ```promql
   # Check P95 latency improved
   histogram_quantile(0.95, rate(apfa_faiss_search_seconds_bucket[5m]))
   # Target: <50ms (vs >200ms before)
   ```

5. **Post-incident review:** Document migration timeline and challenges

---

### Alert: SlowEmbeddingBatches

**Severity:** Warning  
**Trigger:** P95 embedding duration >2s  
**SLA:** Investigate within 30 minutes

**Response Steps:**

1. **Check current queue depth:**
   ```bash
   celery -A app.tasks inspect active
   ```

2. **Scale workers if backlog:**
   ```bash
   docker-compose up -d --scale celery_worker=8
   ```

3. **Check worker CPU:**
   ```bash
   docker stats celery_worker
   ```
   - If CPU >90%: Scale workers
   - If CPU <50%: Investigate task performance

4. **Check for large batches:**
   ```bash
   # View task args in Flower
   http://localhost:5555/tasks
   ```
   - If batches >2000 docs: Reduce batch size

5. **Monitor improvement:**
   ```promql
   histogram_quantile(0.95, rate(celery_task_execution_seconds_bucket{task_name=~".*embed.*"}[5m]))
   ```

---

### Alert: CeleryQueueBacklog

**Severity:** Warning  
**Trigger:** Queue depth >50 for >10 minutes  
**SLA:** Respond within 15 minutes

**Response Steps:**

1. **Immediate: Scale workers**
   ```bash
   docker-compose up -d --scale celery_worker=8
   ```

2. **Check for stuck tasks:**
   ```bash
   celery -A app.tasks inspect active
   ```
   - If tasks running >30 minutes: Investigate or revoke

3. **Check worker health:**
   ```bash
   celery -A app.tasks inspect ping
   ```
   - If workers not responding: Restart

4. **Monitor queue drain rate:**
   ```promql
   deriv(celery_queue_depth{queue_name="embedding"}[5m])
   ```
   - Target: Negative derivative (draining)

5. **Scale down after queue cleared:**
   ```bash
   docker-compose up -d --scale celery_worker=4
   ```

---

### Alert: HighFAISSSearchLatency

**Severity:** Warning  
**Trigger:** P95 search >200ms  
**SLA:** Investigate within 1 hour, plan migration within 7 days

**Response Steps:**

1. **Check vector count:**
   ```promql
   apfa_index_vector_count
   ```
   - If >400K: Migration likely needed

2. **Verify latency is FAISS-specific:**
   ```promql
   rate(apfa_faiss_search_seconds_sum[5m]) / rate(apfa_response_time_seconds_sum[5m]) * 100
   ```
   - If >20% of total time: FAISS is bottleneck

3. **Create migration ticket:**
   - Template: [Migration Plan Template](scaling-migration.md#migration-checklist)
   - Assign to: Backend team lead
   - Due date: 7 days from alert

4. **Monitor growth rate:**
   ```promql
   deriv(apfa_index_vector_count[7d]) * 86400
   ```
   - Estimate days until 500K critical threshold

5. **Interim optimization:**
   - Increase cache TTL (600s → 1200s)
   - Add more APFA replicas for load distribution

---

## Performance Baselines

### Before Celery Implementation (Baseline)

| Metric | Value | Measurement Date |
|--------|-------|-----------------|
| **Startup time (10K vectors)** | 10s | 2025-10-01 |
| **Startup time (100K vectors)** | 100s | 2025-10-01 |
| **P95 request latency (uncached)** | 15s | 2025-10-01 |
| **P99 request latency (uncached)** | 30s | 2025-10-01 |
| **Throughput (docs/sec)** | ~100 | 2025-10-01 |
| **Cache hit rate** | 65% | 2025-10-01 |
| **Error rate** | 0.5% | 2025-10-01 |

### After Celery Implementation (Target)

| Metric | Target | Actual | Delta |
|--------|--------|--------|-------|
| **Startup time** | <1s | TBD | TBD |
| **P95 request latency (uncached)** | <3s | TBD | TBD |
| **P99 request latency (uncached)** | <5s | TBD | TBD |
| **Throughput (docs/sec)** | 1,000-5,000 | TBD | TBD |
| **Cache hit rate** | >80% | TBD | TBD |
| **Error rate** | <0.1% | TBD | TBD |

**Update this table post-deployment (Week 3)**

---

## Log Aggregation

### Structured Logging Format

**Python (FastAPI/Celery):**
```python
import logging
import json

logger = logging.getLogger(__name__)

# Structured log format
log_data = {
    "timestamp": datetime.utcnow().isoformat(),
    "level": "INFO",
    "service": "apfa",
    "component": "embedding",
    "message": "Batch embedding completed",
    "metadata": {
        "batch_id": "batch_001",
        "doc_count": 1000,
        "duration_ms": 850,
        "worker_id": "celery@worker1"
    }
}
logger.info(json.dumps(log_data))
```

### Log Levels

| Level | Usage | Example |
|-------|-------|---------|
| **DEBUG** | Development troubleshooting | Variable values, detailed flow |
| **INFO** | Important events | Task started, index loaded, request completed |
| **WARNING** | Unexpected but handled | Cache miss, retry attempt, deprecated API |
| **ERROR** | Operation failed | Task failure, service unavailable |
| **CRITICAL** | System failure | Database down, all workers crashed |

### Log Queries (Future: ELK Stack)

**Find failed embedding tasks:**
```
service:celery AND component:embedding AND level:ERROR
```

**Find slow requests:**
```
service:apfa AND component:api AND metadata.duration_ms:>10000
```

---

## Tracing

### OpenTelemetry Integration (Future)

**Current Status:** Partial (decorators in place at line 174, 182, 188 of main.py)

**Planned Enhancement:**
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.jaeger import JaegerExporter

# Initialize tracer
tracer = trace.get_tracer(__name__)

@app.post("/generate-advice")
async def generate_advice(q: LoanQuery):
    with tracer.start_as_current_span("generate_advice") as span:
        span.set_attribute("query.length", len(q.query))
        span.set_attribute("user.id", current_user["username"])
        
        # RAG retrieval span
        with tracer.start_as_current_span("rag_retrieval"):
            context = retrieve_loan_data(q.query)
        
        # LLM inference span
        with tracer.start_as_current_span("llm_inference"):
            advice = llm.generate(context)
        
        return {"advice": advice}
```

**Visualization:** Jaeger UI at http://localhost:16686

---

## Capacity Planning

### Growth Projections

**Formula:**
```
future_vectors = current_vectors + (growth_rate × days)

where growth_rate = deriv(apfa_index_vector_count[7d]) × 86400
```

**Example:**
```promql
# Current: 250K vectors
# Growth: 5K vectors/day
# Days to 500K: (500K - 250K) / 5K = 50 days
# Migration deadline: Today + 50 days - 7 days buffer = 43 days
```

### Resource Projections

**Embedding Workers:**
```
required_workers = (documents_per_day / 86400) / (docs_per_second_per_worker)

# Example:
# 100K docs/day ÷ 86400 sec/day = 1.16 docs/sec sustained
# 1.16 docs/sec ÷ 1000 docs/sec/worker = 0.002 workers (1 worker sufficient)
# Peak load (5x): 0.002 × 5 = 0.01 workers (still 1 worker)
# Recommendation: 2 workers for redundancy
```

**Redis Memory:**
```
redis_memory = (cache_size × avg_result_size) + (queue_overhead)

# Example:
# 1000 cached results × 5KB/result = 5MB
# 100 queued tasks × 10KB/task = 1MB
# Total: 6MB (Redis maxmemory: 2GB is overkill but safe)
```

---

## References

- [Prometheus Query Examples](https://prometheus.io/docs/prometheus/latest/querying/examples/)
- [Grafana Dashboard Best Practices](https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/)
- [APFA Background Jobs](background-jobs.md)
- [APFA Deployment Operations](deployment-operations.md)

---

## Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-11 | SRE Team | Initial observability documentation |

---

**Need Help?**
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090
- Flower: http://localhost:5555
- Slack: #apfa-monitoring

