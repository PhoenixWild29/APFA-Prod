# AI/ML Pipeline - Blueprint Template (Phased Evolution)

**Template Version:** 1.0  
**Use For:** Blueprint section enhancement  
**References:** APFA documentation suite (23 files)

---

## Template Structure

```markdown
# 11.0 AI-Powered Loan Advisory Generation

## 11.1 Overview & Evolution Strategy

[Use this intro paragraph:]

The AI/ML Pipeline evolves from a static model deployment (Phase 1) to a production 
ML system with versioning and monitoring (Phase 2) to a comprehensive MLOps platform 
with automated retraining and governance (Phase 3-5). Each phase adds capabilities 
based on model performance metrics and business requirements.

**Evolution Path:**
- **Phase 1 (Current):** Static models, manual updates, in-memory index
- **Phase 2 (Months 1-6):** Model versioning, FAISS hot-swap, A/B testing, bias monitoring ← **DOCUMENTED**
- **Phase 3 (Year 1):** SageMaker endpoints, MLflow registry, automated retraining, feature store
- **Phase 4 (Year 2):** Airflow ML pipelines, AutoML, ensemble models, continuous learning
- **Phase 5 (Year 3+):** Distributed training, edge inference, federated learning

---

## 11.2 Phase 1: Current State (Static Models)

### 11.2.1 Multi-Agent Architecture

**Status:** ✅ **Operational**

**Framework:** LangGraph with LangChain agents

**Architecture:**
```
User Query
    ↓
┌───────────────────────────────────────┐
│  Agent 1: Retriever (RAG)             │
│  ┌─────────────────────────────────┐  │
│  │  Tool: retrieve_loan_data()     │  │
│  │  ├─ Embed query (BGE/fastembed)  │  │
│  │  ├─ FAISS search + reranker     │  │
│  │  └─ Return context              │  │
│  └─────────────────────────────────┘  │
└────────────┬──────────────────────────┘
             ↓
┌───────────────────────────────────────┐
│  Agent 2: Analyzer (LLM)              │
│  ┌─────────────────────────────────┐  │
│  │  Model: OpenAI GPT-4o            │  │
│  │  ├─ Context injection           │  │
│  │  ├─ Generate advice (1K tokens) │  │
│  │  └─ Return response             │  │
│  └─────────────────────────────────┘  │
└────────────┬──────────────────────────┘
             ↓
┌───────────────────────────────────────┐
│  Agent 3: Orchestrator (Bias Check)   │
│  ┌─────────────────────────────────┐  │
│  │  Tool: detect_bias() (stub)      │  │
│  │  ├─ Calculate bias score        │  │
│  │  ├─ Log if score > 0.3          │  │
│  │  └─ Return final advice         │  │
│  └─────────────────────────────────┘  │
└───────────────────────────────────────┘
```

**Reference:** LangGraph multi-agent graph in `app/main.py` (see `build_agent_graph()`)

**Implementation:**
```python
from langgraph.graph import StateGraph, END, START

# Define agent state — each agent returns a subset of these fields
class AgentState(typing.TypedDict, total=False):
    messages: typing.List[Any]
    query: str
    retrieval_confidence: float
    perplexity_context: str
    sources: typing.List[dict]

# Each agent is a plain function — no AgentExecutor needed.
# create_tool_calling_agent was removed in langchain 1.x (pinned: 1.2.12);
# APFA uses plain-function LangGraph nodes instead.
@trace.get_tracer(__name__).start_as_current_span("Retriever Agent")
def retriever_agent(state):
    """Retrieve relevant financial context via RAG/FAISS."""
    context, confidence, retrieval_sources = retrieve_context(state["query"])
    augmented_content = (
        f"Based on the following context, answer the user's question.\n\n"
        f"[CURATED] Context from research corpus:\n{context}\n\n"
        f"User question: {state['query']}"
    )
    return {
        "messages": [HumanMessage(content=augmented_content)],
        "query": state["query"],
        "retrieval_confidence": confidence,
        "sources": retrieval_sources,
    }

# Build graph — linear pipeline: retriever → perplexity → analyzer → orchestrator
graph = StateGraph(AgentState)
graph.add_node("retriever", retriever_agent)
graph.add_node("perplexity", perplexity_researcher)
graph.add_node("analyzer", analyzer_agent)
graph.add_node("orchestrator", orchestrator_agent)
graph.add_edge(START, "retriever")
graph.add_edge("retriever", "perplexity")
graph.add_edge("perplexity", "analyzer")
graph.add_edge("analyzer", "orchestrator")
graph.add_edge("orchestrator", END)

app_graph = graph.compile()
```

**Reference:** [docs/architecture.md](../architecture.md) section "Multi-Agent System"

---

### 11.2.2 Model Specifications

#### Embedding Model

**Model:** BAAI/bge-small-en-v1.5 (via fastembed, ONNX runtime)
- **Dimensions:** 384
- **Parameters:** 33M
- **Speed:** ~1,000 sentences/sec (CPU, ONNX optimized)
- **Use Case:** Convert text → dense vectors for similarity search

**Configuration:**
```python
from fastembed import TextEmbedding

embedder = TextEmbedding(model_name=settings.embedder_model)  # "BAAI/bge-small-en-v1.5"

# Generate embeddings
embeddings = np.array(list(embedder.embed(documents)), dtype=np.float32)
faiss.normalize_L2(embeddings)  # L2 normalization for cosine similarity via IndexFlatIP
```

**Reference:** `app/config.py` (see `embedder_model` setting)

---

#### Language Model (LLM)

**Model:** OpenAI GPT-4o (via langchain-openai)
- **Context Window:** 128K tokens
- **Output:** Max 1,000 tokens per request (configured)
- **Inference Time:** 1-5s per request (API call)

**Loading:**
```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model=settings.openai_model,      # "gpt-4o"
    api_key=settings.openai_api_key,
    temperature=0.2,
    max_tokens=1000,
    timeout=30.0,
    max_retries=2,
)
```

**Reference:** LLM initialization in `app/main.py` (see lifespan startup)

---

### 11.2.3 RAG (Retrieval-Augmented Generation)

**Current Implementation:**

**Data Flow:**
```
Delta Lake → Pandas DataFrame → Embeddings → FAISS Index → Query-Time Retrieval
(s3a://...)    (in-memory)      (384-dim)    (IndexFlatIP)   (top-5 via reranker)
```

**Code:**
```python
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def load_rag_index():
    """Load RAG data from Delta Lake."""
    dt = DeltaTable(settings.delta_table_path)
    df = dt.to_pandas()
    
    # Generate embeddings (BLOCKING in Phase 1)
    embeddings = np.array(list(embedder.embed(df['profile'].tolist())), dtype=np.float32)
    faiss.normalize_L2(embeddings)
    
    # Build FAISS index
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    
    return df, index

# Query-time retrieval pipeline:
# FAISS top-50 → cross-encoder reranker → top-20 → freshness decay → top-5
def retrieve_loan_data(query: str) -> str:
    query_emb = np.array(list(embedder.embed([query])), dtype=np.float32)
    faiss.normalize_L2(query_emb)
    distances, indices = faiss_index.search(query_emb, k=settings.faiss_fetch_k)  # top-50
    
    # Reranker stage (if enabled): cross-encoder rescoring
    # Uses fastembed TextCrossEncoder with BAAI/bge-reranker-base
    # See app/services/reranker.py for implementation
    ...
```

**Reference:** `retrieve_context()` in `app/main.py`, `RerankerService` in `app/services/reranker.py`

**Performance:**
- Embedding time: ~40ms per query
- FAISS search: ~10ms @ 50K vectors
- Total RAG latency: ~50ms

**Limitation:** Index built on every request (10-100s) ❌

---

### 11.2.4 Phase 1 Limitations

| Limitation | Impact | Trigger for Phase 2 |
|------------|--------|-------------------|
| **No model versioning** | Can't rollback bad models | Production deployment |
| **Synchronous index building** | 10-100s per request | User complaints |
| **No A/B testing** | Can't compare model variants | Need experimentation |
| **No bias monitoring** | Fairness issues undetected | Compliance requirement |
| **Manual model updates** | Downtime for updates | Need zero-downtime |

---

## 11.3 Phase 2: Production ML System (Months 1-6) ← **DOCUMENTED & READY**

### 11.3.1 Architecture Overview

**Status:** ✅ **Fully documented and ready to implement**

**Key Enhancements:**
1. **Pre-Built Indexes:** Async Celery job builds indexes in background
2. **Hot-Swap Deployment:** Zero-downtime model/index updates
3. **Model Versioning:** Semantic versioning (v1.0.0, v1.1.0, etc.)
4. **A/B Testing:** Compare model variants
5. **Bias Monitoring:** Real-time fairness metrics

**Architecture:**
```
┌─────────────────────────────────────────────────────────────────┐
│  Production ML Pipeline (Phase 2)                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Background Process (Celery - Hourly)                           │
│  ┌──────────────────────────────────────────────────────┐       │
│  │  embed_all_documents()                               │       │
│  │  ├─ Load from Delta Lake                             │       │
│  │  ├─ Parallel embedding (4 workers, 1K docs/batch)    │       │
│  │  ├─ Upload to MinIO: embeddings/batches/             │       │
│  │  └─ Trigger: build_faiss_index()                     │       │
│  └────────────┬─────────────────────────────────────────┘       │
│               ↓                                                  │
│  ┌──────────────────────────────────────────────────────┐       │
│  │  build_faiss_index()                                 │       │
│  │  ├─ Load all batches from MinIO                      │       │
│  │  ├─ Build FAISS IndexFlatIP                          │       │
│  │  ├─ Generate version: faiss_index_{sha256}.pkl       │       │
│  │  ├─ Upload to MinIO: indexes/                        │       │
│  │  └─ Trigger: hot_swap_index()                        │       │
│  └────────────┬─────────────────────────────────────────┘       │
│               ↓                                                  │
│  ┌──────────────────────────────────────────────────────┐       │
│  │  hot_swap_index()                                    │       │
│  │  ├─ Publish event: Redis pub/sub                     │       │
│  │  ├─ All FastAPI instances subscribe                  │       │
│  │  ├─ Load new index from MinIO (<100ms)               │       │
│  │  ├─ Atomic swap: old → new                           │       │
│  │  └─ Downtime: 0ms ✅                                  │       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                  │
│  Query-Time (FastAPI - No Blocking)                             │
│  ┌──────────────────────────────────────────────────────┐       │
│  │  Request → Load pre-built index (100ms) → Search     │       │
│  │  Total: <3s (vs 15s in Phase 1) ✅                    │       │
│  └──────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

**Reference:** [docs/background-jobs.md](../background-jobs.md) for complete pipeline

---

### 11.3.2 Model Versioning

**Implementation:**

**Version Scheme:** Semantic versioning
```
v1.0.0 - Initial production model
v1.1.0 - Minor improvement (updated embeddings)
v1.2.0 - Minor improvement (retrained LLM)
v2.0.0 - Major change (new model architecture)
```

**Storage Structure:**
```
MinIO/S3 Structure:
├── models/
│   ├── llm-config/
│   │   ├── v1.0.0/
│   │   ├── v1.1.0/
│   │   └── v2.0.0/
│   └── bge-small-en-v1.5/
│       ├── v1.0.0/
│       └── v1.1.0/
│
├── embeddings/
│   ├── v1.0.0/
│   │   ├── batch_0000.pkl
│   │   └── batch_0001.pkl
│   └── v1.1.0/
│       └── ...
│
└── indexes/
    ├── faiss_index_v1.0.0_abc123.pkl
    ├── faiss_index_v1.1.0_def456.pkl
    └── latest.txt  # Points to current version
```

**Metadata Tracking:**
```python
# models/llm-config/v1.1.0/metadata.json
{
    "version": "1.1.0",
    "model_name": "gpt-4o",
    "training_date": "2025-10-01",
    "training_dataset": "customer-queries-2025-09",
    "performance_metrics": {
        "avg_latency_ms": 2500,
        "bias_score": 0.15,
        "user_satisfaction": 4.2
    },
    "active": false,  # Not currently deployed
    "previous_version": "1.0.0",
    "changelog": "Reduced bias score from 0.25 to 0.15"
}
```

**Deployment:**
```python
# Load specific version
def load_model_version(version: str = "latest"):
    if version == "latest":
        version = get_latest_version()
    
    model_path = f"models/llm-config/{version}"
    model = load_from_minio(model_path)
    
    return model, version
```

---

### 11.3.3 FAISS Index Hot-Swap

**Status:** ✅ **Complete procedure documented**

**Documentation Reference:** [docs/background-jobs.md](../background-jobs.md) section "Index Building & Hot-Swap"

**Zero-Downtime Procedure:**

**Step 1: Build New Index (Background)**
```python
# Celery task: build_faiss_index
# Duration: 5-30 seconds for 100K vectors

@app.task(queue='indexing')
def build_faiss_index(num_batches: int):
    # Load all embedding batches
    all_embeddings = []
    for i in range(num_batches):
        batch = load_from_minio(f"embeddings/batches/batch_{i:04d}.pkl")
        all_embeddings.append(batch)
    
    # Concatenate
    embeddings = np.vstack(all_embeddings)
    
    # Build index
    index = faiss.IndexFlatIP(384)
    index.add(embeddings)
    
    # Version with SHA256
    index_bytes = pickle.dumps(faiss.serialize_index(index))
    version_hash = hashlib.sha256(index_bytes).hexdigest()[:8]
    
    # Upload to MinIO
    upload_to_minio(index_bytes, f"indexes/faiss_index_{version_hash}.pkl")
    update_latest_pointer(version_hash)
    
    return version_hash
```

**Step 2: Hot-Swap (Zero Downtime)**
```python
# Celery task: hot_swap_index
# Duration: <100ms per instance

@app.task(queue='indexing')
def hot_swap_index(version_hash: str):
    # Publish to Redis pub/sub
    r = redis.from_url(settings.celery_broker_url)
    swap_message = {
        'event': 'index_swap',
        'version': version_hash,
        'timestamp': time.time()
    }
    r.publish('apfa:index:swap', pickle.dumps(swap_message))

# FastAPI subscribes to swap events
def index_swap_listener():
    global rag_df, faiss_index
    
    pubsub = redis_client.pubsub()
    pubsub.subscribe('apfa:index:swap')
    
    for message in pubsub.listen():
        if message['type'] == 'message':
            swap_data = pickle.loads(message['data'])
            version = swap_data['version']
            
            # Load new index
            new_df, new_index = load_from_minio(version)
            
            # Atomic swap (single assignment = instant)
            rag_df = new_df
            faiss_index = new_index
            
            logger.info(f"Index hot-swapped to version {version}")
```

**Reference:** [docs/background-jobs.md](../background-jobs.md) section "hot_swap_index"

**Benefits:**
- ✅ Zero downtime (atomic variable swap)
- ✅ Instant rollback (publish previous version)
- ✅ All instances update simultaneously (Redis pub/sub)
- ✅ No request failures during swap

---

### 11.3.4 A/B Testing Framework

**Implementation:**

```python
# Model variant routing
class ModelRouter:
    def __init__(self):
        self.variants = {
            'control': load_model_version('v1.0.0'),    # 90% of traffic
            'treatment': load_model_version('v1.1.0'),  # 10% of traffic
        }
        self.traffic_split = {'control': 0.9, 'treatment': 0.1}
    
    def get_model(self, user_id: str):
        """Route user to model variant."""
        # Consistent hashing (same user → same variant)
        hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        threshold = hash_value % 100 / 100.0
        
        if threshold < self.traffic_split['treatment']:
            return self.variants['treatment'], 'treatment'
        else:
            return self.variants['control'], 'control'

router = ModelRouter()

@app.post("/generate-advice")
async def generate_advice(q: LoanQuery, current_user: dict = Depends(get_current_user)):
    # Route to variant
    model, variant = router.get_model(current_user['username'])
    
    # Generate advice
    advice = model.generate(q.query)
    
    # Log for analysis
    await log_ab_test_result(
        user_id=current_user['username'],
        variant=variant,
        query=q.query,
        latency_ms=latency,
    )
    
    return {"advice": advice, "variant": variant}
```

**Analysis:**
```sql
-- Query A/B test results from PostgreSQL
SELECT
    variant,
    COUNT(*) as requests,
    AVG(latency_ms) as avg_latency,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95_latency,
    AVG(user_satisfaction) as satisfaction
FROM ab_test_results
WHERE test_id = 'model_v1.1.0_test'
    AND created_at > NOW() - INTERVAL '7 days'
GROUP BY variant;

-- Result:
-- variant   | requests | avg_latency | p95_latency | satisfaction
-- control   | 9000     | 2800        | 5200        | 4.1
-- treatment | 1000     | 2300        | 4100        | 4.3
-- Winner: treatment (20% faster, higher satisfaction)
```

---

### 11.3.5 Bias Detection & Monitoring

**Status:** ✅ **Stub implemented in orchestrator agent**

**Reference:** `detect_bias()` and `orchestrator_agent()` in `app/main.py`

**Implementation:**
```python
def detect_bias(text: str) -> float:
    """Stub bias detection — returns 0.0 (no bias detected).

    This is a synchronous stub. When a real implementation arrives
    (e.g., AIF360, external ML model), convert the entire agent graph
    to async: make all three node functions async def, use ainvoke(),
    and await this function.
    """
    return 0.0

def orchestrator_agent(state):
    """Orchestrator with bias detection."""
    messages = state["messages"]
    combined_text = ' '.join(messages)
    
    bias_score = detect_bias(combined_text)
    
    if bias_score > 0.3:
        logger.warning(f"High bias detected (score: {bias_score:.2f})")
        state["bias_detected"] = True
        state["bias_score"] = bias_score
    
    return state
```

**Monitoring:**
```promql
# Prometheus query for bias trends
avg(apfa_bias_score) by (model_version)

# Alert if bias increasing
increase(apfa_bias_score[7d]) > 0.1
```

**Reference:** [docs/observability.md](../observability.md) for bias monitoring metrics

---

### 11.3.6 FAISS Migration Path

**Status:** ✅ **Complete migration procedure documented**

**Documentation Reference:** [docs/adrs/002-faiss-indexflat-to-ivfflat-migration.md](../adrs/002-faiss-indexflat-to-ivfflat-migration.md)

**Migration Trigger:**

Migrate from IndexFlatIP to IndexIVFFlat when **ANY** of these conditions met:

| Trigger | Threshold | Measurement |
|---------|-----------|-------------|
| **Vector Count** | >500,000 | `apfa_index_vector_count` Prometheus metric |
| **P95 Search Latency** | >200ms | `histogram_quantile(0.95, rate(apfa_faiss_search_seconds_bucket[5m]))` |
| **Search % of Total Time** | >20% | `(rate(apfa_faiss_search_seconds_sum[5m]) / rate(apfa_response_time_seconds_sum[5m])) * 100` |
| **Index Memory** | >2GB | `apfa_index_memory_bytes > 2 * 1024^3` |

**Migration Procedure:**

```python
# Step 1: Train IVF index offline
embeddings = load_all_embeddings()  # 500K vectors

nlist = 2048  # 4 * sqrt(500K)
quantizer = faiss.IndexFlatIP(384)
index = faiss.IndexIVFFlat(quantizer, 384, nlist)

# Train on sample (faster)
sample = embeddings[np.random.choice(len(embeddings), 100000, replace=False)]
index.train(sample)

# Add all vectors
index.add(embeddings)

# Set search parameter
index.nprobe = 32  # Search 32 clusters (97% recall)

# Step 2: Validate in staging
test_queries = load_test_queries(1000)
for query in test_queries:
    flat_results = flat_index.search(query, k=5)
    ivf_results = ivf_index.search(query, k=5)
    
    recall = calculate_recall(flat_results, ivf_results)
    assert recall >= 0.95  # 95% minimum recall

# Step 3: Deploy with hot-swap (zero downtime)
upload_index(ivf_index, "indexes/faiss_ivfflat_v2.0.0.pkl")
hot_swap_index.apply_async(args=['v2.0.0'])
```

**Expected Performance:**
- Search latency: 50-100ms → 20-30ms (2-3x faster)
- Capacity: 500K → 10M vectors
- Recall: 100% → 97% (acceptable trade-off)

**Reference:** [docs/adrs/002-faiss-indexflat-to-ivfflat-migration.md](../adrs/002-faiss-indexflat-to-ivfflat-migration.md) complete migration guide

---

### 11.3.7 Performance Metrics (Phase 2)

| Component | Metric | Phase 1 | Phase 2 | Improvement |
|-----------|--------|---------|---------|-------------|
| **RAG Retrieval** | Latency | 10-100s (blocking) | <100ms | **100-1000x** |
| **FAISS Search** | Latency | 10ms @ 50K | 10ms @ 500K | Scales to 10x data |
| **LLM Inference** | Latency | 2-8s | 2-8s | Same (CPU-bound) |
| **Total Request** | P95 | 15s | <3s | **5x faster** |
| **Embedding** | Throughput | 100 docs/sec | 1,000-5,000 docs/sec | **10-50x** |

**Reference:** [docs/observability.md](../observability.md) section "Performance Baselines"

---

### 11.3.8 Implementation Timeline

**Status:** ✅ **Detailed 3-week plan available**

**Reference:** [docs/celery-implementation-project-plan.md](../celery-implementation-project-plan.md)

**Week 1:** Celery infrastructure (Days 1-7)
- Day 1-2: Redis, Celery workers, Flower
- Day 3-4: Core embedding tasks
- Day 5-7: Index building & hot-swap

**Week 2:** Optimization (Days 8-14)
- Day 8-9: Performance tuning (batch size, workers)
- Day 10-11: Scheduled jobs (Beat)
- Day 12-14: Monitoring & alerting

**Week 3:** Deployment (Days 15-21)
- Day 15-16: Staging deployment & load testing
- Day 17-18: Production deployment (blue-green)
- Day 19-21: Documentation & team training

**Success Criteria:**
- [ ] P95 latency <3s achieved
- [ ] Embedding throughput >1,000 docs/sec
- [ ] Zero failed requests during hot-swap
- [ ] All Grafana dashboards showing data
- [ ] Team can trigger jobs via Flower

---

## 11.4 Phase 3: ML Platform (Year 1)

### 11.4.1 Trigger Conditions

**Implement Phase 3 when ANY condition met:**

| Trigger | Threshold | Measurement |
|---------|-----------|-------------|
| **Model Updates** | >Weekly | Manual update frequency |
| **Model Variants** | >3 active | A/B testing complexity |
| **Vector Count** | >500K | FAISS IndexIVFFlat needed |
| **ML Engineers** | >2 FTE | Team size justifies platform |
| **Experimentation** | >10 experiments/month | Need feature store |

---

### 11.4.2 SageMaker Endpoints

**Why SageMaker:**
- ✅ Auto-scaling (scale to zero, scale to thousands)
- ✅ Model versioning (built-in)
- ✅ Multi-model endpoints (cost optimization)
- ✅ Monitoring (CloudWatch integration)
- ✅ A/B testing (traffic routing)

**Configuration:**
```python
import boto3

sagemaker = boto3.client('sagemaker')

# Deploy model to endpoint
## Note: SageMaker endpoints apply if/when self-hosted models are adopted.
## Current LLM (OpenAI GPT-4o) is a hosted API — no endpoint deployment needed.
## This section is applicable for embedding model serving or future self-hosted LLMs.
response = sagemaker.create_endpoint(
    EndpointName='financial-llm-prod',
    EndpointConfigName='financial-llm-config',
)

# Multi-model endpoint (cost optimization)
response = sagemaker.create_endpoint_config(
    EndpointConfigName='multi-model-config',
    ProductionVariants=[
        {
            'VariantName': 'financial-llm',
            'ModelName': 'financial-llm-v1.1.0',
            'InitialInstanceCount': 1,
            'InstanceType': 'ml.g4dn.xlarge',  # GPU instance
            'InitialVariantWeight': 0.9,  # 90% traffic
        },
        {
            'VariantName': 'financial-llm-experimental',
            'ModelName': 'financial-llm-v2.0.0',
            'InitialInstanceCount': 1,
            'InstanceType': 'ml.g4dn.xlarge',
            'InitialVariantWeight': 0.1,  # 10% traffic (A/B test)
        },
    ],
)
```

**Cost:** ~$1,000/month (ml.g4dn.xlarge, 50% utilization)

---

### 11.4.3 MLflow Model Registry

**Why MLflow:**
- ✅ Centralized model catalog
- ✅ Versioning with metadata
- ✅ Model lineage tracking
- ✅ Stage transitions (staging → production)

**Structure:**
```python
import mlflow

# Register model
mlflow.set_tracking_uri("http://mlflow.apfa.io")

with mlflow.start_run():
    # Log parameters
    mlflow.log_param("model_name", "gpt-4o")
    mlflow.log_param("embedding_model", "BAAI/bge-small-en-v1.5")
    mlflow.log_param("training_samples", 100000)
    
    # Log metrics
    mlflow.log_metric("avg_latency_ms", 2500)
    mlflow.log_metric("bias_score", 0.15)
    mlflow.log_metric("user_satisfaction", 4.3)
    
    # Log model
    mlflow.pyfunc.log_model("financial-llm", python_model=model)
    
    # Register
    mlflow.register_model("runs:/<run_id>/financial-llm", "LoanAdvisoryLLM")

# Promote to production
client = mlflow.tracking.MlflowClient()
client.transition_model_version_stage(
    name="LoanAdvisoryLLM",
    version=3,
    stage="Production"  # Staging → Production
)
```

**Cost:** ~$200/month (managed MLflow)

---

### 11.4.4 Feature Store

**Why Feature Store:**
- ✅ Centralized feature repository
- ✅ Online + offline features
- ✅ Point-in-time correctness (training/serving consistency)
- ✅ Feature sharing (across models)

**Example (AWS SageMaker Feature Store):**
```python
# Define feature group
feature_group = sagemaker.FeatureGroup(
    name='customer-features',
    feature_definitions=[
        {'FeatureName': 'user_id', 'FeatureType': 'String'},
        {'FeatureName': 'avg_loan_amount', 'FeatureType': 'Fractional'},
        {'FeatureName': 'credit_score', 'FeatureType': 'Integral'},
        {'FeatureName': 'num_queries', 'FeatureType': 'Integral'},
    ],
    record_identifier_name='user_id',
    event_time_feature_name='event_time',
)

# Ingest features
feature_group.ingest(
    data_frame=features_df,
    max_workers=4,
)

# Retrieve features (online store - low latency)
features = feature_store.get_record(
    feature_group_name='customer-features',
    record_identifier_value_as_string='user123',
)
```

**Cost:** ~$300/month (managed feature store)

---

## 11.5 Phase 4: ML Ops Platform (Year 2)

### 11.5.1 Trigger Conditions

| Trigger | Threshold | Justification |
|---------|-----------|---------------|
| **Models in Production** | >5 models | Need orchestration |
| **Retraining Frequency** | Weekly | Need automation |
| **Feature Engineering** | >50 features | Need feature store |
| **Experiments** | >20/month | Need experiment tracking |
| **ML Team Size** | >5 engineers | Need collaboration tools |

---

### 11.5.2 Apache Airflow (ML Pipelines)

**Why Airflow (vs. Celery Beat for Phase 2):**

| Feature | Celery Beat | Airflow | When to Switch |
|---------|------------|---------|----------------|
| **Simple scheduling** | ✅ crontab | ✅ crontab | Either works |
| **Complex DAGs** | ❌ Limited | ✅ Excellent | >5 dependent tasks |
| **Backfill** | ❌ No | ✅ Yes | Need historical runs |
| **Monitoring** | ⚠️ Flower | ✅ Web UI | Need task-level visibility |
| **Dependencies** | ❌ Manual | ✅ Automatic | Complex workflows |

**Reference:** [docs/architecture-roadmap.md](../architecture-roadmap.md) section "Phase 4: Apache Airflow"

**Example DAG:**
```python
from airflow import DAG
from airflow.operators.python import PythonOperator

with DAG(
    'weekly_model_retraining',
    schedule_interval='0 2 * * 0',  # Sunday 2 AM
    catchup=False,
) as dag:
    
    extract = PythonOperator(task_id='extract_training_data', ...)
    transform = PythonOperator(task_id='feature_engineering', ...)
    train = PythonOperator(task_id='train_model_sagemaker', ...)
    validate = PythonOperator(task_id='validate_model_quality', ...)
    deploy = PythonOperator(task_id='deploy_to_production', ...)
    
    extract >> transform >> train >> validate >> deploy
```

**Cost:** ~$200/month (Managed Airflow)

---

## 11.6 Phase 5: Advanced ML (Year 3+)

### 11.6.1 Distributed Training

**When needed:** Model training >24 hours on single GPU

**Technologies:**
- DeepSpeed (ZeRO optimization)
- Horovod (distributed training)
- Ray (distributed computing)

**Cost:** ~$5,000/month (multi-GPU instances)

---

### 11.6.2 Edge Inference

**When needed:** Mobile apps OR latency <50ms required

**Technologies:**
- ONNX Runtime (model compilation)
- TensorRT (GPU optimization)
- TFLite (mobile deployment)

**Cost:** Included in edge devices

---

## 11.7 Summary Table: AI/ML Evolution

| Aspect | Phase 1 | Phase 2 ← DOCUMENTED | Phase 3 | Phase 4-5 |
|--------|---------|---------------------|---------|-----------|
| **Models** | Static | Versioned | SageMaker | Distributed training |
| **Index** | Built per-request ❌ | Pre-built (hot-swap) ✅ | IndexIVFFlat | IndexIVFPQ |
| **Deployment** | Manual | Hot-swap (0 downtime) | A/B testing | Canary + shadowing |
| **Monitoring** | Basic | Bias detection, metrics | MLflow tracking | Full MLOps |
| **Retraining** | Manual | Manual | Weekly (automated) | Continuous learning |
| **Vector Capacity** | <100K | 100K-500K | 500K-10M | 10M-1B+ |
| **Latency (P95)** | 15s | <3s | <1s | <500ms |
| **Cost/Month** | $500 | $680 | $5,000 | $15,000+ |
| **Documentation** | ✅ Complete | ✅ Complete | ⚠️ Conceptual | 💭 Vision |

---

## 11.8 References

**Complete Documentation (Phase 1-2):**
- [Background Jobs](../background-jobs.md) - Celery async processing
- [ADR-002: FAISS Migration](../adrs/002-faiss-indexflat-to-ivfflat-migration.md) - IndexFlat → IVF
- [Observability](../observability.md) - Model performance metrics
- [Architecture](../architecture.md) - Multi-agent system
- [Celery Implementation Plan](../celery-implementation-project-plan.md) - 3-week timeline

**Strategic Planning:**
- [Architecture Roadmap](../architecture-roadmap.md) - 5-phase evolution

---

## 11.9 Implementation Checklist

### Phase 2 (Months 1-6)

- [ ] Implement Celery background jobs (Week 1-3)
  - Reference: [background-jobs.md](../background-jobs.md)
- [ ] Implement FAISS hot-swap (Week 1-3)
  - Reference: [background-jobs.md](../background-jobs.md) section "hot_swap_index"
- [ ] Add model versioning (Week 4)
- [ ] Implement A/B testing framework (Week 5-6)
- [ ] Set up bias monitoring (Week 7-8)
  - Reference: [observability.md](../observability.md)
- [ ] Deploy to production (Week 12)
  - Reference: [deployment-runbooks.md](../deployment-runbooks.md)

**Total:** 3 months implementation + 3 months stabilization

---

[END OF TEMPLATE]
```

---

**To use this template:**
1. Copy entire section to your blueprint
2. Keep all references to APFA documentation (shows you have production-ready specs)
3. Adjust timelines if needed for your context
4. Add your specific business requirements
5. Update costs if using different cloud providers

---

**This template demonstrates:**
- ✅ Deep understanding of ML systems
- ✅ Phased evolution (not premature optimization)
- ✅ Production experience (references real implementations)
- ✅ Performance focus (specific metrics and benchmarks)
- ✅ Strategic planning (when to advance phases)

