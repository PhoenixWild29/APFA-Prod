# Document Processing Pipeline - Blueprint Template

**Section:** 8.0 Document Processing Pipeline  
**References:** APFA background-jobs.md, architecture-roadmap.md

---

## 8.1 Overview

Document processing evolves from synchronous blocking operations (Phase 1) to high-throughput 
async pipelines (Phase 2) to enterprise ETL orchestration (Phase 3-5).

---

## 8.2 Phase 1: Current (Synchronous Blocking)

### Architecture

```python
# BLOCKING - Runs on every request
def load_rag_index():
    # Load from Delta Lake
    dt = DeltaTable(settings.delta_table_path)
    df = dt.to_pandas()
    
    # Generate embeddings (BLOCKS 10-100s)
    embeddings = embedder.encode(df['profile'].tolist())
    faiss.normalize_L2(embeddings)
    
    # Build index
    index = faiss.IndexFlatIP(384)
    index.add(embeddings)
    
    return df, index

# Called on EVERY request
rag_df, faiss_index = load_rag_index()  # Blocks application startup
```

**Performance:**
- 10K documents: 10s blocking
- 100K documents: 100s blocking (unacceptable)
- Throughput: ~100 docs/sec

**Limitation:** Can't scale beyond 100K documents

---

## 8.3 Phase 2: Async Pipeline ← **DOCUMENTED & READY**

### 8.3.1 Celery Background Processing

**Status:** ✅ **Complete implementation guide**

**Reference:** [docs/background-jobs.md](../background-jobs.md)

```
Pipeline Flow:
┌─────────────────────────────────────────────────────────────┐
│  1. Ingestion (Delta Lake)                                  │
│     └─ Load profiles to DataFrame                           │
├─────────────────────────────────────────────────────────────┤
│  2. Batch Creation                                          │
│     └─ Split into 1,000 doc batches                         │
├─────────────────────────────────────────────────────────────┤
│  3. Parallel Embedding (Celery Group)                       │
│     ├─ Worker 1: Embed batch 1-25                           │
│     ├─ Worker 2: Embed batch 26-50                          │
│     ├─ Worker 3: Embed batch 51-75                          │
│     └─ Worker 4: Embed batch 76-100                         │
│     Performance: 4,000 docs/sec (40x improvement)           │
├─────────────────────────────────────────────────────────────┤
│  4. Index Building                                          │
│     └─ Concatenate batches → Build FAISS → Upload MinIO    │
├─────────────────────────────────────────────────────────────┤
│  5. Hot-Swap Deployment                                     │
│     └─ Zero-downtime index replacement                      │
└─────────────────────────────────────────────────────────────┘
```

**Tasks:**
- `embed_document_batch` - Process 1K docs in <1s
- `embed_all_documents` - Orchestrate 100K docs in <60s
- `build_faiss_index` - Build index in <5s
- `hot_swap_index` - Swap in <100ms, 0ms downtime

**Performance:**
- Throughput: 1,000-5,000 docs/sec (10-50x improvement)
- Latency: <100ms (vs 10-100s)
- Downtime: 0ms (vs 100% blocking)

**Reference:** [docs/celery-implementation-project-plan.md](../celery-implementation-project-plan.md) for implementation

---

## 8.4 Phase 3: ETL Orchestration

### Apache Airflow DAGs

```python
from airflow import DAG
from airflow.operators.python import PythonOperator

with DAG('document_processing_pipeline', schedule_interval='@hourly') as dag:
    
    extract = PythonOperator(task_id='extract_from_delta_lake', python_callable=extract_documents)
    validate = PythonOperator(task_id='validate_schema', python_callable=validate_documents)
    transform = PythonOperator(task_id='transform_clean', python_callable=clean_documents)
    embed = PythonOperator(task_id='embed_parallel', python_callable=trigger_celery_embedding)
    index = PythonOperator(task_id='build_index', python_callable=build_index)
    deploy = PythonOperator(task_id='deploy_index', python_callable=hot_swap)
    quality = PythonOperator(task_id='quality_check', python_callable=validate_quality)
    
    extract >> validate >> transform >> embed >> index >> deploy >> quality
```

**Capabilities:**
- Complex dependencies (DAG)
- Backfill (reprocess historical data)
- Retry logic (automatic)
- Monitoring (Airflow UI)

**Trigger:** >10 tasks with dependencies

**Reference:** [docs/architecture-roadmap.md](../architecture-roadmap.md) Phase 4

---

## 8.5 Phase 4-5: Data Governance

### Data Quality Validation

```python
from great_expectations import DataContext

context = DataContext()

# Validate document schema
suite = context.get_expectation_suite("document_validation")
batch = context.get_batch("documents_batch")

results = batch.validate(suite)

if not results.success:
    # Alert data team
    send_alert("Data quality check failed")
    # Block deployment
    raise DataQualityError(results.statistics)
```

### PII Detection

```python
from presidio_analyzer import AnalyzerEngine

analyzer = AnalyzerEngine()

def detect_pii(text):
    results = analyzer.analyze(
        text=text,
        entities=['SSN', 'CREDIT_CARD', 'PHONE_NUMBER', 'EMAIL'],
        language='en'
    )
    return results

# Anonymize before logging
safe_text = anonymize_pii(user_query)
logger.info(f"Processing: {safe_text}")
```

**Reference:** [docs/security-best-practices.md](../security-best-practices.md) section "Data Protection"

---

## 8.6 Summary

| Aspect | Phase 1 | Phase 2 ← DOCUMENTED | Phase 3 | Phase 4-5 |
|--------|---------|---------------------|---------|-----------|
| **Processing** | Synchronous ❌ | Async (Celery) ✅ | Airflow DAGs | Advanced ETL |
| **Throughput** | 100 docs/sec | 1,000-5,000 docs/sec | 10K+ docs/sec | 100K+ docs/sec |
| **Downtime** | 100% blocking | 0% (hot-swap) | 0% | 0% |
| **Quality** | None | Basic validation | Full validation | Automated governance |
| **PII** | No protection | Logging only | Detection | Auto-anonymization |

**Reference:** [docs/background-jobs.md](../background-jobs.md) complete guide

