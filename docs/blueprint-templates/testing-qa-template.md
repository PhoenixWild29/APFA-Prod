# Testing & Quality Assurance - Blueprint Template

**Section:** 16.0 Testing & Quality Assurance  
**References:** Multiple APFA docs

---

## 16.1 Overview

Testing evolves from basic unit tests (Phase 1) to comprehensive QA automation (Phase 2) 
to continuous testing with chaos engineering (Phase 3-5).

---

## 16.2 Phase 1: Basic Testing

```python
# Unit tests
def test_embed_document():
    result = embedder.encode(["test doc"])
    assert result.shape == (1, 384)

# Manual integration tests
# No automation, no CI/CD
```

**Coverage:** ~60%  
**Automation:** None

---

## 16.3 Phase 2: Production Testing ← **DOCUMENTED**

### 16.3.1 Unit Tests

```python
# pytest with 90% coverage target
def test_celery_task_success():
    result = embed_document_batch.apply(args=[docs, "batch_001"])
    assert result.successful()
    assert result.get()[1] == len(docs)

def test_celery_task_retry():
    with patch('minio_client.put_object') as mock:
        mock.side_effect = [Exception("Fail"), None]
        result = embed_document_batch.apply(args=[docs, "retry_batch"])
        assert mock.call_count == 2  # Initial + 1 retry
```

### 16.3.2 Integration Tests

```python
def test_end_to_end_pipeline():
    # Trigger embedding job
    task = embed_all_documents.apply_async()
    result = task.get(timeout=300)
    
    # Verify index built
    assert result['status'] == 'success'
    assert result['total_documents'] == 10000
    
    # Verify index deployed
    response = requests.get('http://localhost:8000/admin/index/current')
    assert response.json()['vectors'] == 10000
```

### 16.3.3 Load Testing

```bash
# wrk load test
wrk -t10 -c100 -d60s -s payload.lua http://api/generate-advice

# Expected:
# P95 latency: <3s
# Throughput: >10 req/sec
# Error rate: <0.1%
```

### 16.3.4 Security Testing

```bash
# OWASP ZAP automated scan
docker run -t owasp/zap2docker-stable zap-baseline.py -t http://api

# Bandit (Python security)
bandit -r app/ -ll

# Safety (dependency vulnerabilities)
safety check
```

**Reference:** [docs/security-best-practices.md](../security-best-practices.md) section "Security Checklist"

---

## 16.4 Phase 3: Continuous Testing

### 16.4.1 Chaos Engineering

```python
# Chaos Monkey for Celery
def inject_worker_failure():
    # Kill random worker
    worker = random.choice(get_active_workers())
    kill_worker(worker)
    
    # Verify:
    # - Tasks automatically retried
    # - Other workers pick up load
    # - No user-facing errors

# Latency injection
def inject_latency():
    # Add 5s delay to Redis
    with patch('redis_client.get') as mock:
        mock.side_effect = lambda k: (time.sleep(5), real_get(k))
        # Verify circuit breaker opens
```

### 16.4.2 Synthetic Monitoring

```python
# Continuous production testing
@app.scheduled(interval='5min')
async def synthetic_test():
    # Generate test query
    response = await client.post('/generate-advice', json={'query': 'test loan $100,000'})
    
    # Assert SLA
    assert response.status_code == 200
    assert response.elapsed.total_seconds() < 3  # P95 <3s
    
    # Alert if failed
    if response.status_code != 200:
        send_alert("Synthetic test failed")
```

---

## 16.5 Summary

| Aspect | Phase 1 | Phase 2 ← DOCUMENTED | Phase 3 | Phase 4-5 |
|--------|---------|---------------------|---------|-----------|
| **Unit Tests** | Basic | 90% coverage | 95% coverage | AI-generated tests |
| **Integration** | Manual | Automated | Continuous | Contract testing |
| **Load Testing** | None | wrk (100K req) | Continuous | Global scale |
| **Security** | None | OWASP ZAP | Continuous | Automated pentesting |
| **Chaos** | None | None | Failure injection | Advanced chaos |

