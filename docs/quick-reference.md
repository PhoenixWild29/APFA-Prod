# APFA Quick Reference Guide

**Version:** 1.0  
**Last Updated:** 2025-10-11

---

## 🚀 Common Commands

### Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f apfa

# Restart service
docker-compose restart apfa

# Stop all services
docker-compose down
```

### Celery Operations

```bash
# Check active tasks
celery -A app.tasks inspect active

# Check queue depth
celery -A app.tasks inspect reserved

# Trigger embedding job
celery -A app.tasks call app.tasks.embed_all_documents

# Revoke task
celery -A app.tasks control revoke <task-id> --terminate

# Purge queue (DANGEROUS)
celery -A app.tasks purge -Q embedding
```

### Monitoring

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Query metric
curl 'http://localhost:9090/api/v1/query?query=apfa_index_vector_count'

# Check Flower
curl http://localhost:5555/api/workers
```

---

## 📊 Key Metrics

### Performance Targets

| Metric | Target | Alert Threshold |
|--------|--------|----------------|
| P95 Latency (uncached) | <3s | >10s |
| P95 Latency (cached) | <500ms | >2s |
| Cache Hit Rate | >80% | <60% |
| Error Rate | <0.1% | >1% |
| FAISS Search (P95) | <50ms | >200ms |
| Embedding Batch (P95) | <1s | >2s |

### Migration Triggers

| Trigger | Threshold | Action |
|---------|-----------|--------|
| Vector Count | >400K | Plan migration |
| Vector Count | >500K | Migrate NOW |
| P95 Search Latency | >200ms | Consider migration |
| Index Memory | >2GB | Evaluate migration |

---

## 🔗 Quick Links

### Dashboards
- **Grafana:** http://localhost:3000 (admin/admin)
- **Prometheus:** http://localhost:9090
- **Flower:** http://localhost:5555
- **API Docs:** http://localhost:8000/docs

### Documentation
- **Master Index:** [docs/README.md](README.md)
- **Background Jobs:** [docs/background-jobs.md](background-jobs.md)
- **Observability:** [docs/observability.md](observability.md)
- **Project Plan:** [docs/celery-implementation-project-plan.md](celery-implementation-project-plan.md)

---

## 🆘 Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs apfa

# Common issues:
# - Missing .env file → Copy .env.example to .env
# - Port already in use → Change port in docker-compose.yml
# - Redis not ready → Wait 30 seconds and retry
```

### High Latency

```bash
# Check cache hit rate
curl http://localhost:9090/api/v1/query?query='rate(apfa_cache_hits_total[5m])/(rate(apfa_cache_hits_total[5m])+rate(apfa_cache_misses_total[5m]))'

# Check FAISS search latency
curl http://localhost:9090/api/v1/query?query='histogram_quantile(0.95,rate(apfa_faiss_search_seconds_bucket[5m]))'

# Check if embedding is blocking
# See background-jobs.md
```

### Celery Tasks Not Processing

```bash
# Check workers
celery -A app.tasks inspect ping

# Check Redis
redis-cli -h localhost ping

# Restart workers
docker-compose restart celery_worker
```

---

## 📞 Support Contacts

- **Slack:** #apfa-backend
- **Email:** apfa-team@company.com
- **On-Call:** PagerDuty APFA rotation
- **Docs:** https://docs.apfa.io

