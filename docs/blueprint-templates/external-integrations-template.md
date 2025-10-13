# External Service Integrations - Blueprint Template

**Section:** 13.0 External Service Integrations  
**References:** APFA architecture.md, security-best-practices.md

---

## 13.1 Overview

External integrations evolve from basic API calls (Phase 1) to production-grade resilience 
with circuit breakers and retries (Phase 2) to enterprise service mesh (Phase 3-5).

---

## 13.2 Phase 1: Basic Integration

```python
# Simple boto3 call (NO error handling)
bedrock = boto3.client('bedrock-agent-runtime', region_name=AWS_REGION)

def simulate_risk(input_data: str) -> str:
    response = bedrock.invoke_agent(
        agentId='loan-risk-agent',
        sessionId='session-123',
        inputText=input_data
    )
    return response['completion']
```

**Limitations:**
- ❌ No retry logic
- ❌ No timeout
- ❌ No circuit breaker
- ❌ Blocks on failure

---

## 13.3 Phase 2: Resilient Integration ← **DOCUMENTED**

### Circuit Breaker Pattern

**Reference:** `app/main.py` lines 102-126, [docs/architecture.md](../architecture.md)

```python
from tenacity import retry, stop_after_attempt, wait_exponential, circuit_breaker

@circuit_breaker(failure_threshold=5, recovery_timeout=60)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=4, max=10))
def simulate_risk(input_data: str) -> str:
    """AWS Bedrock with circuit breaker + retry."""
    try:
        response = bedrock.invoke_agent(
            agentId='loan-risk-agent',
            sessionId='session-123',
            inputText=input_data
        )
        return response['completion']
    except Exception as e:
        logger.error(f"Bedrock error: {e}")
        return "Error simulating risk."  # Graceful degradation
```

**Behavior:**
- Retry: 3 attempts with exponential backoff (4s, 8s, 10s)
- Circuit Breaker: After 5 failures → OPEN for 60s (fail fast)
- Timeout: 30s per request
- Fallback: Return error message (don't crash)

**Integrated Services:**
- AWS Bedrock (risk simulation)
- MinIO/S3 (object storage)
- Delta Lake (data lakehouse)
- Redis (caching, message broker)

---

### Connection Pooling

```python
from aiohttp import ClientSession, TCPConnector

# Async HTTP client with connection pooling
connector = TCPConnector(
    limit=100,              # Max 100 total connections
    limit_per_host=10,      # Max 10 per host
    ttl_dns_cache=300       # Cache DNS for 5 min
)
session = ClientSession(connector=connector)

# Reuse connections
async def call_external_api(url, data):
    async with session.post(url, json=data) as response:
        return await response.json()
```

**Performance:**
- Connection reuse (no SSL handshake overhead)
- DNS caching (reduce latency)
- Request pooling (efficient resource use)

---

## 13.4 Phase 3: Service Mesh

### Istio Resilience

```yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: bedrock-api
spec:
  host: bedrock.amazonaws.com
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 50
        maxRequestsPerConnection: 2
    outlierDetection:
      consecutiveErrors: 5
      interval: 30s
      baseEjectionTime: 60s
    loadBalancer:
      simple: LEAST_CONN
```

**Automatic:**
- Circuit breaking (5 errors → eject for 60s)
- Load balancing (least connections)
- Connection limits (prevent overload)
- Retry policies (automatic)

---

## 13.5 Summary

| Aspect | Phase 1 | Phase 2 ← DOCUMENTED | Phase 3 | Phase 4-5 |
|--------|---------|---------------------|---------|-----------|
| **Error Handling** | None ❌ | Circuit breaker ✅ | Service mesh | Advanced resilience |
| **Retries** | None | 3 attempts | Configurable | Adaptive |
| **Timeout** | None | 30s | Per-service | Dynamic |
| **Fallback** | Crash | Graceful degradation | Cached response | AI-powered fallback |
| **Monitoring** | None | Prometheus metrics | Distributed tracing | Full observability |

**Reference:** [docs/architecture.md](../architecture.md) section "Resilience & Performance"

