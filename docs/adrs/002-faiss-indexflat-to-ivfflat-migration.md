# ADR-002: FAISS IndexFlatIP to IndexIVFFlat Migration Strategy

**Status:** Accepted  
**Date:** 2025-10-11  
**Decision Makers:** Backend Team Lead, ML Engineer  
**Stakeholders:** Backend Team, SRE Team, Product Team

---

## Context

APFA uses FAISS for vector similarity search in the RAG (Retrieval-Augmented Generation) pipeline. Currently, we use **IndexFlatIP** (exhaustive inner product search) which provides:
- ✅ 100% search accuracy (exhaustive search)
- ✅ Simple implementation (no training required)
- ✅ Fast for small-to-medium datasets (<100K vectors)
- ❌ O(n) search complexity (scales linearly with vector count)
- ❌ Becomes slow at >500K vectors (>200ms search latency)

**Current State:**
- Vector count: ~50K
- Dimensions: 384 (all-MiniLM-L6-v2)
- P95 search latency: ~10ms
- Memory: ~77MB (50K × 384 × 4 bytes)

**Projected Growth:**
- Current growth: ~5K vectors/day
- Days to 500K: ~90 days (3 months)
- Days to 1M: ~190 days (6 months)

**Problem:**
At current growth rate, we will hit performance degradation within 3-6 months, requiring migration to a more scalable index type.

---

## Decision

**We will adopt a phased migration strategy:**

1. **Phase 1 (Current - 3 months):** Continue with IndexFlatIP up to 500K vectors
2. **Phase 2 (Month 4-12):** Migrate to IndexIVFFlat for 500K-10M vectors
3. **Phase 3 (Year 2+):** Evaluate IndexIVFPQ if exceeding 10M vectors

**Trigger for Phase 2 migration:** ANY of the following:
- Vector count >500K
- P95 search latency >200ms
- FAISS search time >20% of total request time
- Index memory >2GB (50% of container memory)

---

## Options Considered

### Option 1: IndexFlatIP (Current)

**Description:** Exhaustive search using inner product (cosine similarity with L2-normalized vectors).

**Pros:**
- ✅ **Perfect accuracy:** 100% recall (searches all vectors)
- ✅ **No training:** Index built instantly from vectors
- ✅ **Simple:** No hyperparameters to tune
- ✅ **Memory-efficient:** Stores only raw vectors
- ✅ **Fast for small datasets:** <100ms for <100K vectors

**Cons:**
- ❌ **Linear scaling:** O(n) search complexity
- ❌ **Slow for large datasets:** >500ms for 1M vectors
- ❌ **Not scalable:** Impractical beyond 1M vectors

**Performance:**

| Vector Count | Search Latency (P95) | Memory |
|-------------|---------------------|--------|
| 10K | 1ms | 15MB |
| 100K | 10ms | 150MB |
| **500K** | **50ms** | **768MB** |
| 1M | 100ms | 1.5GB |
| 10M | 1000ms (1s) | 15GB ❌ |

**Decision:** Keep for Phase 1 (<500K vectors)

---

### Option 2: IndexIVFFlat (Selected for Phase 2)

**Description:** Inverted file index with exhaustive search within clusters. Uses k-means clustering to partition vectors, then searches only relevant clusters.

**Pros:**
- ✅ **Scalable:** O(sqrt(n)) search complexity
- ✅ **Fast:** 10-50ms for 1M vectors
- ✅ **Tunable accuracy:** Adjust nprobe (clusters to search)
- ✅ **Memory-efficient:** Same memory as IndexFlatIP
- ✅ **Production-proven:** Used by Pinterest, Spotify

**Cons:**
- ⚠️ **Requires training:** Must train k-means on sample data
- ⚠️ **Accuracy trade-off:** 95-98% recall (vs 100%)
- ⚠️ **Hyperparameter tuning:** nlist (clusters), nprobe (search clusters)
- ❌ **Migration complexity:** Requires reindexing

**Performance:**

| Vector Count | nlist | nprobe | Search Latency (P95) | Recall | Memory |
|-------------|-------|--------|---------------------|--------|--------|
| 500K | 100 | 10 | 20ms | 98% | 768MB |
| 1M | 256 | 16 | 30ms | 97% | 1.5GB |
| 5M | 1024 | 32 | 50ms | 96% | 7.7GB |
| 10M | 2048 | 64 | 80ms | 95% | 15GB |

**Hyperparameter Guidelines:**
```python
# Rule of thumb for nlist (number of clusters)
nlist = int(4 * sqrt(vector_count))

# For 500K vectors: nlist = 4 * sqrt(500,000) = 2,828 (use 2,048 or 4,096)
# For 1M vectors: nlist = 4 * sqrt(1,000,000) = 4,000 (use 4,096)

# nprobe (clusters to search) controls accuracy/speed trade-off
nprobe = 10  # Fast, 95% recall
nprobe = 32  # Balanced, 97% recall
nprobe = 64  # Slow, 98% recall
```

**Decision:** Use for Phase 2 (500K-10M vectors)

---

### Option 3: IndexIVFPQ (Future - Phase 3)

**Description:** IVF with Product Quantization (lossy compression). Compresses vectors to reduce memory.

**Pros:**
- ✅ **Very scalable:** O(sqrt(n)) search complexity
- ✅ **Low memory:** 10-50x compression (1.5GB → 30-150MB for 1M vectors)
- ✅ **Fast:** 50-100ms for 10M vectors
- ✅ **Handles billions:** Used by Facebook, Google

**Cons:**
- ❌ **Accuracy loss:** 85-95% recall (lossy compression)
- ❌ **Complex:** Many hyperparameters (nlist, nprobe, m, nbits)
- ❌ **Requires training:** Must train both IVF and PQ
- ❌ **GPU recommended:** CPU performance poor at scale

**Performance:**

| Vector Count | Memory (PQ-compressed) | Search Latency (P95) | Recall |
|-------------|----------------------|---------------------|--------|
| 10M | 150MB (vs 15GB) | 80ms | 92% |
| 100M | 1.5GB (vs 150GB) | 200ms | 90% |
| 1B | 15GB (vs 1.5TB) | 500ms | 88% |

**Decision:** Evaluate only if exceeding 10M vectors (Year 2+)

---

### Option 4: HNSW (Not Selected)

**Description:** Hierarchical Navigable Small World graph-based index.

**Pros:**
- ✅ **Fast:** 1-10ms search latency
- ✅ **High accuracy:** 95-99% recall
- ✅ **No training:** Builds incrementally

**Cons:**
- ❌ **High memory:** 2-5x more than IndexFlatIP
- ❌ **Slow indexing:** 10-100x slower than IndexFlatIP
- ❌ **Not supported in FAISS:** Requires hnswlib or Annoy

**Decision:** Rejected due to high memory overhead and library switch

---

## Decision Rationale

### Why Phased Approach?

**Principle:** "Don't optimize prematurely, but be prepared."

1. **Phase 1 (IndexFlatIP) for 0-500K vectors:**
   - Current performance is excellent (<50ms search)
   - No complexity overhead
   - Allows focus on Celery implementation (P0 priority)
   - Migration trigger: Well-defined thresholds

2. **Phase 2 (IndexIVFFlat) for 500K-10M vectors:**
   - Proven at scale (Pinterest uses for 100M+ vectors)
   - Good accuracy/speed trade-off (97% recall, 30ms)
   - Migration procedure documented NOW (zero-downtime)

3. **Phase 3 (IndexIVFPQ) for 10M+ vectors:**
   - Cross that bridge when we come to it (likely Year 2+)
   - Requires GPU, different cost model
   - Re-evaluate based on actual usage patterns

### Why IndexIVFFlat over HNSW?

| Factor | IndexIVFFlat | HNSW | Winner |
|--------|-------------|------|--------|
| **Memory** | Same as Flat | 2-5x Flat | IVF |
| **Speed** | 30ms @ 1M | 5ms @ 1M | HNSW |
| **Accuracy** | 97% | 98% | HNSW |
| **Indexing** | Fast | Slow | IVF |
| **FAISS support** | Native | Limited | IVF |
| **Library** | FAISS (current) | hnswlib (new) | IVF |

**Decision:** Memory efficiency and FAISS compatibility outweigh HNSW's speed advantage.

---

## Migration Triggers (Phase 1 → Phase 2)

### Automatic Monitoring

**Prometheus Alerts:**

```yaml
# Alert 1: Vector count threshold
- alert: ApproachingMigrationThreshold
  expr: apfa_index_vector_count > 400000
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "FAISS approaching 500K vectors"
    description: "Current: {{ $value }}. Plan migration within 30 days."

# Alert 2: Search latency degradation
- alert: HighFAISSSearchLatency
  expr: histogram_quantile(0.95, rate(apfa_faiss_search_seconds_bucket[5m])) > 0.2
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "FAISS P95 latency >200ms"
    description: "Latency: {{ $value }}s. Migration recommended."

# Alert 3: FAISS bottleneck
- alert: FAISSBottleneck
  expr: (rate(apfa_faiss_search_seconds_sum[5m]) / rate(apfa_response_time_seconds_sum[5m])) > 0.20
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "FAISS taking >20% of request time"
    description: "{{ $value | humanizePercentage }}. Consider migration."
```

### Manual Triggers

**Capacity Planning Dashboard:**
- Grafana panel: "Days Until 500K Threshold"
- Formula: `(500000 - current_count) / (7d_growth_rate × 86400)`
- If <30 days: Start migration planning

---

## Migration Procedure (Zero-Downtime)

### Strategy: Blue-Green Index Deployment

**Timeline:** 4-6 hours (mostly automated)

**Steps:**

#### Step 1: Build New Index (Offline)
```python
# Duration: 10-30 minutes for 500K vectors

# 1. Load current embeddings
embeddings = load_all_embeddings_from_minio()

# 2. Train IVF index
nlist = 2048  # For 500K vectors
quantizer = faiss.IndexFlatIP(384)
index = faiss.IndexIVFFlat(quantizer, 384, nlist)

# 3. Train on sample (faster than full dataset)
sample = embeddings[np.random.choice(len(embeddings), 100000, replace=False)]
index.train(sample)

# 4. Add all vectors
index.add(embeddings)

# 5. Upload to MinIO
upload_index('indexes/faiss_ivfflat_v1.pkl', index)
```

#### Step 2: Validation (Staging)
```python
# Duration: 30 minutes

# 1. Load both indexes
flat_index = load_index('indexes/faiss_flat_v10.pkl')
ivf_index = load_index('indexes/faiss_ivfflat_v1.pkl')

# 2. Run comparison test
test_queries = load_test_queries(1000)

for query in test_queries:
    # Search both indexes
    flat_results = flat_index.search(query, k=5)
    ivf_results = ivf_index.search(query, k=5)
    
    # Calculate recall
    recall = len(set(flat_results[1][0]) & set(ivf_results[1][0])) / 5
    assert recall >= 0.95, f"Recall too low: {recall}"

# 3. Measure latency
assert ivf_latency < flat_latency, "IVF should be faster"
```

#### Step 3: Blue-Green Deploy (Production)
```python
# Duration: 5 minutes

# 1. Load new index on 1 instance (green)
instance_1.load_index('faiss_ivfflat_v1.pkl')

# 2. Route 10% traffic to green
load_balancer.route(green_weight=0.1, blue_weight=0.9)

# 3. Monitor for 15 minutes
# Check: Error rate, latency, recall (user feedback)

# 4. If OK, gradual rollout
# 10% → 50% → 100% over 30 minutes

# 5. Decommission blue index
# All instances now using IVF index
```

#### Step 4: Performance Validation
```promql
# Before migration (Flat)
histogram_quantile(0.95, rate(apfa_faiss_search_seconds_bucket[5m]))
# Expected: 50-100ms @ 500K vectors

# After migration (IVF)
histogram_quantile(0.95, rate(apfa_faiss_search_seconds_bucket[5m]))
# Expected: 20-30ms @ 500K vectors (faster!)

# Recall check (manual)
# Sample 100 queries, compare results with ground truth
# Expected: >95% recall
```

#### Step 5: Rollback Plan
```python
# If issues detected:
# 1. Route 100% traffic back to blue (Flat index)
# 2. Investigate IVF index quality
# 3. Retrain with different hyperparameters
# 4. Retry migration

# Rollback time: <2 minutes
```

---

## Hyperparameter Tuning Guidelines

### nlist (Number of Clusters)

**Formula:** `nlist = 4 * sqrt(vector_count)`

**Tuning:**
- **Too small** (nlist < sqrt(n)): Slow search, poor clustering
- **Too large** (nlist > 16 * sqrt(n)): High memory, slow training
- **Sweet spot:** 4-8 × sqrt(n)

**Examples:**
```python
500K vectors: nlist = 2048 or 4096
1M vectors:   nlist = 4096 or 8192
5M vectors:   nlist = 8192 or 16384
```

### nprobe (Clusters to Search)

**Trade-off:** Accuracy vs Speed

**Tuning:**
- **nprobe = 1:** Fastest, ~80% recall ❌
- **nprobe = 10:** Fast, ~95% recall ✅
- **nprobe = 32:** Balanced, ~97% recall ✅ (recommended)
- **nprobe = 64:** Slow, ~98% recall ⚠️
- **nprobe = nlist:** Equivalent to Flat (defeats purpose)

**Recommendation:** Start with nprobe = 32, adjust based on recall requirements

---

## Monitoring Post-Migration

### Key Metrics to Track

```python
# 1. Search latency (should improve)
apfa_faiss_search_seconds_bucket{index_type="ivfflat"}

# 2. Recall (maintain >95%)
apfa_faiss_recall_percent  # Custom metric (compare with ground truth)

# 3. Index size
apfa_index_memory_bytes{index_type="ivfflat"}

# 4. Training time
apfa_index_build_seconds{phase="training"}
```

### Success Criteria

| Metric | Before (Flat) | After (IVF) | Status |
|--------|--------------|-------------|--------|
| **P95 latency** | 50-100ms | <30ms | ✅ Faster |
| **Recall** | 100% | >95% | ✅ Acceptable |
| **Memory** | 768MB | ~800MB | ✅ Similar |
| **Index build time** | 5s | 30s (+ 10min training) | ⚠️ Slower (acceptable for offline) |

---

## Cost-Benefit Analysis

### Phase 1: IndexFlatIP (Current)

**Costs:**
- Simple implementation
- Zero migration cost

**Benefits:**
- Fast search for <500K vectors
- 100% accuracy

**ROI:** Excellent for current scale

---

### Phase 2: IndexIVFFlat Migration

**Costs:**
- **Engineering time:** 40 hours (1 week sprint)
  - Development: 16 hours
  - Testing: 16 hours
  - Migration: 8 hours
- **Risk:** 5% accuracy loss (100% → 95% recall)
- **Complexity:** Training step added to index build

**Benefits:**
- **10x scalability:** 500K → 5M vectors without degradation
- **2-3x faster search:** 50ms → 20ms at 500K vectors
- **Future-proof:** Supports 2-3 years of growth

**ROI:** Break-even at 500K vectors, highly positive thereafter

---

### Phase 3: IndexIVFPQ (Future)

**Costs:**
- **Engineering time:** 80 hours (2 week sprint)
- **Infrastructure:** GPU instance ($300/month)
- **Accuracy loss:** 100% → 85-90% recall
- **Complexity:** Multiple training stages

**Benefits:**
- **100x memory reduction:** 15GB → 150MB
- **Supports billions:** 10M → 1B+ vectors

**ROI:** Only justified if reaching 10M+ vectors (Year 2+)

---

## Risks and Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Recall drops below 95%** | Medium | High | Tune nprobe higher, validate in staging first |
| **Migration causes downtime** | Low | Critical | Blue-green deployment, tested rollback |
| **Training takes too long** | Low | Medium | Train on sample (10% of data), not full dataset |
| **IVF slower than expected** | Low | Medium | Tune nlist/nprobe, consider GPU acceleration |
| **Team lacks expertise** | High | Medium | Document procedure now, training session, external consultant if needed |

---

## Future Considerations

### When to Revisit (Phase 2 → Phase 3)

**Triggers for IndexIVFPQ:**
1. Vector count >10M
2. Index memory >10GB
3. GPU available in infrastructure
4. Accuracy requirements relaxed (<95% acceptable)

**Alternatives to Consider:**
1. **Sharding:** Multiple smaller IndexIVFFlat indexes
2. **Hybrid:** Flat index for recent data, IVF for historical
3. **External services:** Pinecone, Weaviate, Milvus

---

## References

- [FAISS Documentation: Choosing an Index](https://github.com/facebookresearch/faiss/wiki/Faiss-indexes)
- [FAISS Guidelines and Best Practices](https://github.com/facebookresearch/faiss/wiki/Guidelines-to-choose-an-index)
- [Pinterest: Manas - Scaling Vector Search](https://medium.com/pinterest-engineering/manas-a-high-performing-customized-search-system-cf189f6ca40f)
- [Spotify: Annoy vs FAISS Comparison](https://engineering.atspotify.com/2020/11/approximate-nearest-neighbor-search/)

---

## Implementation Checklist

### Phase 1: Preparation (Month 1-3)
- [x] Document migration procedure (this ADR)
- [ ] Add Prometheus metrics for migration triggers
- [ ] Create Grafana dashboard: "Days Until Migration"
- [ ] Set up alerts for 400K vector threshold
- [ ] Implement recall measurement (compare with ground truth)

### Phase 2: Migration (When Triggered)
- [ ] Create migration project plan (1 week sprint)
- [ ] Build IVF index in staging
- [ ] Validate recall >95%
- [ ] Execute blue-green migration
- [ ] Monitor for 1 week post-migration
- [ ] Document lessons learned

### Phase 3: Monitoring (Ongoing)
- [ ] Weekly review of vector count growth
- [ ] Monthly capacity planning
- [ ] Quarterly ADR review

---

**ADR Status:** Accepted  
**Implementation Status:** Phase 1 (Active)  
**Next Review:** When vector count >400K or 2025-12-31, whichever comes first

---

**Signatures:**

| Role | Name | Date |
|------|------|------|
| Backend Team Lead | | 2025-10-11 |
| ML Engineer | | 2025-10-11 |
| SRE Lead | | 2025-10-11 |

