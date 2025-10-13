# ADR-003: Multi-Queue Task Architecture Design

**Status:** Accepted  
**Date:** 2025-10-11  
**Decision Makers:** Backend Team Lead, Senior Backend Engineer  
**Stakeholders:** Backend Team, SRE Team

---

## Context

The APFA Celery implementation requires handling multiple types of background tasks with different priorities, resource requirements, and SLAs. We need to decide how to organize Celery queues and workers for optimal performance and operational clarity.

**Task Types:**

| Task Category | Examples | Priority | CPU/IO | Frequency |
|--------------|----------|----------|---------|-----------|
| **Embedding** | embed_document_batch, embed_all_documents | Critical | CPU-intensive | Hourly + on-demand |
| **Indexing** | build_faiss_index, hot_swap_index | High | I/O-bound | After embedding |
| **Maintenance** | cleanup_old_embeddings, compute_index_stats | Low | I/O-bound | Scheduled (daily, 5min) |

**Requirements:**
1. **Priority:** Critical tasks must not wait behind low-priority tasks
2. **Resource isolation:** CPU-intensive tasks shouldn't starve I/O tasks
3. **Scalability:** Ability to scale specific worker pools independently
4. **Monitoring:** Clear visibility into each queue's health
5. **Simplicity:** Not overly complex for operational team

---

## Decision

**We will implement a 3-queue architecture with priority-based routing:**

```
┌─────────────────────────────────────────────────────────────┐
│                     Redis (Message Broker)                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────┐  │
│  │ embedding        │  │ indexing         │  │maintenance│  │
│  │ (priority: 9)    │  │ (priority: 7)    │  │(priority:5│  │
│  │ CPU-intensive    │  │ I/O-bound        │  │I/O-bound  │  │
│  │ 2-4 workers      │  │ 1-2 workers      │  │1 worker   │  │
│  └──────────────────┘  └──────────────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Task Routing Rules:**
- `app.tasks.embed_*` → `embedding` queue
- `app.tasks.build_faiss_index`, `app.tasks.hot_swap_index` → `indexing` queue
- `app.tasks.cleanup_*`, `app.tasks.compute_*` → `maintenance` queue

---

## Options Considered

### Option 1: Single Queue (Rejected)

**Description:** All tasks in one queue, processed FIFO.

**Pros:**
- ✅ Simplest to implement
- ✅ Lowest operational complexity
- ✅ Easy to scale (add more workers)

**Cons:**
- ❌ **No prioritization:** Low-priority tasks can block critical tasks
- ❌ **Resource contention:** CPU and I/O tasks compete
- ❌ **Poor monitoring:** Can't isolate queue depth by task type
- ❌ **Scaling limitation:** Can't scale CPU vs I/O workers independently

**Example Problem:**
```
Queue: [embed_batch, embed_batch, cleanup, embed_batch, compute_stats]
         ↑ Critical task blocked by cleanup task
```

**Decision:** Rejected - doesn't meet priority requirement

---

### Option 2: Priority-Based Single Queue (Rejected)

**Description:** One queue with task priorities (1-10 scale).

**Pros:**
- ✅ Simple implementation
- ✅ Built-in Celery priority support

**Cons:**
- ❌ **Priority inversion:** High-priority task can still wait if workers busy
- ❌ **No resource isolation:** CPU and I/O tasks still compete
- ❌ **Monitoring limitations:** Can't see queue depth by task type
- ❌ **Scaling limitation:** Can't tune worker counts for task types

**Example:**
```python
embed_batch.apply_async(priority=9)
cleanup.apply_async(priority=1)

# Still issues:
# - If all 4 workers busy with cleanup (started first), embedding waits
# - Can't scale CPU workers without also scaling I/O workers
```

**Decision:** Rejected - doesn't provide sufficient isolation

---

### Option 3: Multi-Queue with Priority Routing (Selected)

**Description:** 3 separate queues with priority levels and task-type routing.

**Pros:**
- ✅ **True prioritization:** Critical queue always processed first
- ✅ **Resource isolation:** Separate worker pools for CPU vs I/O
- ✅ **Independent scaling:** Scale embedding workers without touching maintenance
- ✅ **Clear monitoring:** Queue depth by task category
- ✅ **Operational clarity:** Easy to understand queue purpose
- ✅ **Flexibility:** Can tune concurrency per queue

**Cons:**
- ⚠️ **Moderate complexity:** 3 queues to monitor vs 1
- ⚠️ **Configuration overhead:** Must define routing rules
- ⚠️ **Potential underutilization:** Workers dedicated to idle queues

**Implementation:**
```python
# celeryconfig.py
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

**Decision:** Selected - best balance of priority, isolation, and simplicity

---

### Option 4: Fine-Grained Queues (Rejected)

**Description:** 6+ queues with one queue per task type.

**Example:**
- `embed_batch` queue
- `embed_all` queue
- `build_index` queue
- `hot_swap` queue
- `cleanup` queue
- `stats` queue

**Pros:**
- ✅ **Maximum isolation:** Each task type completely separated
- ✅ **Precise scaling:** Scale individual task types

**Cons:**
- ❌ **Operational overhead:** Too many queues to monitor
- ❌ **Underutilization:** Many queues idle most of the time
- ❌ **Configuration complexity:** Many routing rules
- ❌ **Worker waste:** Too many dedicated worker pools

**Decision:** Rejected - unnecessary complexity for current scale

---

## Decision Rationale

### Why 3 Queues?

**Principle:** "As simple as possible, but no simpler."

**Grouping Logic:**

#### Queue 1: Embedding (Critical Path)
**Why grouped:**
- Both `embed_document_batch` and `embed_all_documents` are critical path
- Both are CPU-intensive (embedder.encode)
- Both have same SLA (<1s per batch)
- Both benefit from same worker tuning (concurrency=4)

**Why separate from others:**
- ⚠️ Must not be blocked by low-priority maintenance
- ⚠️ CPU-intensive vs I/O-bound (different worker tuning)
- ⚠️ Highest priority (mission-critical for user experience)

#### Queue 2: Indexing (High Priority)
**Why grouped:**
- Both `build_faiss_index` and `hot_swap_index` are index operations
- Both are I/O-bound (MinIO, Redis pub/sub)
- Both have medium frequency (hourly + on-demand)
- Both need low concurrency (1-2 workers)

**Why separate from others:**
- ⚠️ Different resource profile than embedding (I/O vs CPU)
- ⚠️ Lower priority than embedding (can wait a few seconds)
- ⚠️ Higher priority than maintenance (index availability critical)

#### Queue 3: Maintenance (Low Priority)
**Why grouped:**
- Both `cleanup` and `compute_stats` are housekeeping
- Both are I/O-bound (MinIO, index loading)
- Both have low priority (can be delayed)
- Both need minimal workers (1 worker sufficient)

**Why separate from others:**
- ⚠️ Must not block critical or high-priority tasks
- ⚠️ Can tolerate delays (not user-facing)
- ⚠️ Scheduled execution (predictable load)

---

### Worker Pool Sizing

**Embedding Pool: 2-4 workers**

**Reasoning:**
- CPU-intensive tasks (embedder.encode)
- Target: Saturate CPU cores without thrashing
- Formula: `workers = CPU_cores × 1` (for CPU-bound)
- 4-core machine → 4 workers

**Configuration:**
```bash
celery -A app.tasks worker \
  --queues=embedding \
  --concurrency=4 \
  --max-tasks-per-child=10 \
  --prefetch-multiplier=1
```

**Tuning:**
- `concurrency=4`: One worker per CPU core
- `max-tasks-per-child=10`: Restart after 10 tasks (prevent memory leaks)
- `prefetch-multiplier=1`: Fetch 1 task at a time (fair distribution)

---

**Indexing Pool: 1-2 workers**

**Reasoning:**
- I/O-bound tasks (MinIO, Redis, FAISS save/load)
- Low frequency (hourly or less)
- Can tolerate higher concurrency (I/O-bound)

**Configuration:**
```bash
celery -A app.tasks worker \
  --queues=indexing \
  --concurrency=2 \
  --max-tasks-per-child=20 \
  --prefetch-multiplier=2
```

**Tuning:**
- `concurrency=2`: Can handle multiple I/O tasks
- `prefetch-multiplier=2`: Fetch 2 tasks (higher throughput for I/O)

---

**Maintenance Pool: 1 worker**

**Reasoning:**
- Low priority, low frequency
- Minimal resource usage
- 1 worker sufficient for scheduled tasks

**Configuration:**
```bash
celery -A app.tasks worker \
  --queues=maintenance \
  --concurrency=1 \
  --max-tasks-per-child=50 \
  --prefetch-multiplier=4
```

**Tuning:**
- `concurrency=1`: Single worker for housekeeping
- `prefetch-multiplier=4`: Can queue multiple maintenance tasks

---

## Monitoring Strategy

### Queue-Specific Metrics

```python
# Prometheus metrics by queue
celery_queue_depth{queue_name="embedding"}
celery_queue_depth{queue_name="indexing"}
celery_queue_depth{queue_name="maintenance"}

celery_task_execution_seconds{queue="embedding"}
celery_task_execution_seconds{queue="indexing"}
celery_task_execution_seconds{queue="maintenance"}
```

### Grafana Dashboard

**Panel 1: Queue Depth by Queue**
```promql
# Shows backlog per queue
celery_queue_depth
```

**Panel 2: Task Execution Rate by Queue**
```promql
# Shows throughput per queue
rate(celery_task_success_total[5m]) by (queue)
```

**Panel 3: Worker Utilization by Queue**
```promql
# Shows active workers per queue
celery_worker_active_tasks{queue="embedding"}
```

---

## Scaling Strategy

### Horizontal Scaling (Add Workers)

**When to Scale UP:**

| Queue | Trigger | Action |
|-------|---------|--------|
| **embedding** | Depth >20 for >5 min | Add 2-4 workers |
| **indexing** | Depth >10 for >10 min | Add 1 worker |
| **maintenance** | Depth >50 for >30 min | Add 1 worker (rare) |

**How to Scale:**
```bash
# Docker Compose
docker-compose up -d --scale celery_worker=8

# AWS ECS
aws ecs update-service \
  --cluster apfa-cluster \
  --service celery-embedding \
  --desired-count 8
```

**When to Scale DOWN:**
```bash
# Trigger: Queue depth <5 for >30 minutes
# Action: Reduce by 50%
```

---

### Vertical Scaling (Resource Limits)

**CPU Allocation:**
```yaml
# docker-compose.yml
celery_worker_embedding:
  deploy:
    resources:
      limits:
        cpus: '4.0'  # 4 CPU cores
        memory: 2G
      reservations:
        cpus: '2.0'  # Minimum 2 cores
        memory: 1G
```

---

## Failure Scenarios

### Scenario 1: Embedding Queue Backlog

**Symptom:** `celery_queue_depth{queue="embedding"}` >50

**Cause:** Sudden spike in embedding requests (e.g., bulk data import)

**Resolution:**
1. **Immediate:** Scale workers (4 → 8)
2. **Short-term:** Batch requests more aggressively
3. **Long-term:** Add auto-scaling rules

**Prevention:**
- Alert at depth >20
- Auto-scaling policy

---

### Scenario 2: Worker Crash During Embedding

**Symptom:** Worker process exits, tasks stuck in "STARTED" state

**Celery Behavior:**
- With `acks_late=True`: Task re-queued automatically
- Task retried by another worker
- No data loss ✅

**Resolution:**
1. Worker auto-restarts (Docker restart policy)
2. Task completes on another worker
3. Monitor for repeated crashes (alert)

---

### Scenario 3: Queue Priority Inversion

**Symptom:** Critical embedding tasks waiting while maintenance runs

**Prevention:**
- Separate queues ensure this CANNOT happen
- Embedding workers NEVER process maintenance tasks

**If it happens anyway:**
- Indicates configuration error (tasks routed to wrong queue)
- Fix routing rules in `celeryconfig.py`

---

## Trade-offs

### Pros of Multi-Queue Design

1. **Isolation:** Critical tasks never blocked by low-priority
2. **Scalability:** Independent scaling per queue
3. **Monitoring:** Clear visibility into task categories
4. **Resource optimization:** CPU vs I/O worker tuning
5. **Operational clarity:** Queue purpose obvious

### Cons of Multi-Queue Design

1. **Complexity:** 3 queues vs 1 (moderate increase)
2. **Configuration:** Routing rules must be maintained
3. **Underutilization risk:** Idle workers if queue empty
4. **Monitoring overhead:** 3x more metrics to track

### Mitigation of Cons

1. **Complexity:** Documented in [background-jobs.md](../background-jobs.md)
2. **Configuration:** Routing rules centralized, rarely change
3. **Underutilization:** Workers are cheap, priority is valuable
4. **Monitoring:** Grafana dashboard consolidates all queues

---

## Future Considerations

### When to Add More Queues

**Trigger Conditions:**
1. **New task category** with unique resource profile (e.g., GPU tasks)
2. **SLA requirements** differ significantly within existing categories
3. **Scale issues** that can't be solved by worker scaling

**Example:** If we add real-time inference tasks:
- New queue: `realtime` (priority: 10, CPU+GPU)
- Separate from batch embedding

### When to Merge Queues

**Trigger Conditions:**
1. **Underutilization:** Two queues consistently idle
2. **Similar profiles:** Tasks have same resource needs and priority
3. **Operational burden:** Too many queues for team to manage

**Example:** If maintenance tasks become frequent:
- Merge `indexing` and `maintenance` into `non_critical`
- Simplify to 2 queues: `critical` (embedding) and `non_critical`

**Unlikely:** Current 3-queue design is optimal for 2-3 years

---

## Alternatives Considered (But Not Pursued)

### Dynamic Queue Creation

**Idea:** Create queues on-the-fly based on task metadata

**Rejected because:**
- Adds significant complexity
- Hard to monitor (unknown queue names)
- Overkill for current needs

### Task Priority Within Queue

**Idea:** Use Celery task priorities (1-10) within each queue

**Rejected because:**
- Queues already provide prioritization
- Task priorities add complexity
- Current design sufficient

### Dedicated Celery Beat Instance per Queue

**Idea:** Separate Beat instance for each queue's scheduled tasks

**Rejected because:**
- Single Beat instance can handle all scheduled tasks
- Adds unnecessary infrastructure
- Current design sufficient

---

## Implementation Checklist

### Phase 1: Configuration (Week 1, Day 1-2)
- [x] Define queue configuration in `celeryconfig.py`
- [x] Define task routing rules
- [x] Set queue priorities

### Phase 2: Worker Deployment (Week 1, Day 2-3)
- [ ] Deploy embedding workers (2-4 instances)
- [ ] Deploy indexing workers (1-2 instances)
- [ ] Deploy maintenance worker (1 instance)
- [ ] Verify workers connected to correct queues

### Phase 3: Monitoring (Week 2, Day 12-14)
- [ ] Add Prometheus metrics for queue depth
- [ ] Create Grafana dashboard with queue panels
- [ ] Set up alerts for queue backlog

### Phase 4: Validation (Week 3, Day 15-16)
- [ ] Load test each queue independently
- [ ] Verify priority: Embedding tasks never blocked
- [ ] Test worker scaling (add/remove workers)
- [ ] Document operational runbook

---

## References

- [Celery Routing Tasks](https://docs.celeryproject.org/en/stable/userguide/routing.html)
- [Celery Queues Documentation](https://docs.celeryproject.org/en/stable/getting-started/brokers/redis.html#configuration)
- [Kombu Queue Documentation](https://kombu.readthedocs.io/en/stable/reference/kombu.html#queue)
- [APFA Background Jobs Documentation](../background-jobs.md)

---

## Success Metrics (Post-Implementation)

### Week 4 Post-Launch

| Metric | Target | Actual |
|--------|--------|--------|
| **Embedding queue depth** | <10 tasks | TBD |
| **Indexing queue depth** | <5 tasks | TBD |
| **Maintenance queue depth** | <2 tasks | TBD |
| **Critical task blocking** | 0 occurrences | TBD |
| **Worker utilization** | 60-90% | TBD |

### Month 1 Post-Launch

| Metric | Target | Actual |
|--------|--------|--------|
| **Queue-based alerts** | <5 per week | TBD |
| **Worker scaling events** | <2 per week | TBD |
| **Task mis-routing incidents** | 0 | TBD |
| **Operational clarity** | 5/5 (team survey) | TBD |

---

**ADR Status:** Accepted  
**Implementation Status:** Week 1 (In Progress)  
**Next Review:** 2025-11-15 (post-implementation retrospective)

---

**Signatures:**

| Role | Name | Date |
|------|------|------|
| Backend Team Lead | | 2025-10-11 |
| Senior Backend Engineer | | 2025-10-11 |
| SRE Lead | | 2025-10-11 |

