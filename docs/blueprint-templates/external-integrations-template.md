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
# NOTE: AWS Bedrock is initialized but not currently in use for risk simulation.
# LLM inference uses OpenAI GPT-4o via langchain_openai.ChatOpenAI.
# The boto3 bedrock-agent-runtime client exists in app/main.py but no
# production code calls invoke_agent(). Example retained for reference only.
bedrock = boto3.client('bedrock-agent-runtime', region_name=AWS_REGION)
```

**Limitations of Phase 1 pattern (no error handling):**
- ❌ No retry logic
- ❌ No timeout
- ❌ No circuit breaker
- ❌ Blocks on failure

---

## 13.3 Phase 2: Resilient Integration ← **DOCUMENTED**

### Circuit Breaker Pattern

**Reference:** `app/services/circuit_breaker.py`, usage in `app/connectors/finnhub_connector.py`

```python
from tenacity import retry, stop_after_attempt, wait_exponential
from app.services.circuit_breaker import get_breaker, CircuitBreakerOpen

# In-house circuit breaker (not a third-party library).
# See app/services/circuit_breaker.py for implementation.
_finnhub_breaker = get_breaker("finnhub", failure_threshold=5, recovery_timeout=60)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=4, max=10))
def fetch_market_data(ticker: str) -> dict:
    """Finnhub market data with circuit breaker + retry."""
    def _inner():
        return finnhub_client.quote(ticker)
    try:
        return _finnhub_breaker.call(_inner)
    except CircuitBreakerOpen:
        logger.warning("Finnhub circuit breaker OPEN — returning cached data")
        return get_cached_quote(ticker)
    except Exception as e:
        logger.error(f"Finnhub error: {e}")
        raise
```

**Behavior:**
- Retry: 3 attempts with exponential backoff (4s, 8s, 10s)
- Circuit Breaker: After 5 failures → OPEN for 60s (fail fast)
- Timeout: 30s per request
- Fallback: Return cached data or error message (don't crash)

**Integrated Services:**
- OpenAI GPT-4o (LLM inference via langchain_openai)
- MinIO/S3 (object storage)
- Delta Lake (data lakehouse)
- Redis (caching, message broker)
- Finnhub (market data)
- Perplexity (research augmentation)

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
# Example Istio resilience config for an external API (e.g., Finnhub, Perplexity).
# Bedrock is not currently in production use — LLM is OpenAI GPT-4o.
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: external-api
spec:
  host: api.example.com
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

