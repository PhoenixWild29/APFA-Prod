# Infrastructure & Deployment - Blueprint Template

**Section:** 17.0 Infrastructure & Deployment  
**References:** APFA deployment-runbooks.md

---

## 17.1 Overview

Infrastructure evolves from local Docker Compose (Phase 1) to production container orchestration 
(Phase 2) to multi-region enterprise infrastructure (Phase 3-5).

---

## 17.2 Phase 1: Docker Compose

**Current deployment:**

```yaml
services:
  apfa:
    build: .
    ports: ["8000:8000"]
  prometheus:
    image: prom/prometheus:latest
  grafana:
    image: grafana/grafana:latest
```

**Limitations:**
- Single host (no HA)
- Manual scaling
- No auto-healing
- Development only

---

## 17.3 Phase 2: Production Orchestration ← **DOCUMENTED & READY**

### 17.3.1 Multi-Cloud Options

**Reference:** [docs/deployment-runbooks.md](../deployment-runbooks.md) - Complete IaC for 3 clouds

**AWS (ECS Fargate + CDK):**
```python
# Complete 200-line CDK stack provided
apfa_service = ecs_patterns.ApplicationLoadBalancedFargateService(
    self, "APFA-Service",
    cluster=cluster,
    task_definition=apfa_task_definition,
    desired_count=4,
    auto_scale_task_count(min=4, max=16, target_cpu=70)
)
```

**Azure (AKS + Terraform):**
```hcl
# Complete 150-line Terraform config provided
resource "azurerm_kubernetes_cluster" "apfa" {
  default_node_pool {
    enable_auto_scaling = true
    min_count = 3
    max_count = 10
  }
}
```

**GCP (GKE + Helm):**
```yaml
# Complete Helm chart provided
autoscaling:
  enabled: true
  minReplicas: 4
  maxReplicas: 16
  targetCPUUtilizationPercentage: 70
```

**Cost:**
- AWS: ~$680/month
- Azure: ~$720/month
- GCP: ~$650/month

---

### 17.3.2 Zero-Downtime Deployment

**Blue-Green Strategy:**

```bash
# 1. Deploy green (new version)
# 2. Route 10% traffic → green
# 3. Monitor 15 min
# 4. Route 50% → green
# 5. Route 100% → green
# 6. Decommission blue
```

**Rollback:** <5 minutes (route back to blue)

**Reference:** [docs/deployment-runbooks.md](../deployment-runbooks.md) section "Zero-Downtime Deployment"

---

## 17.4 Phase 3: Multi-Region

### Active-Passive Failover

```
Primary: us-east-1 (handles all traffic)
Standby: us-west-2 (ready for failover)

Failover: <5 minutes (automatic)
RPO: <1 minute (Aurora cross-region replication)
```

### Active-Active Global

```
us-east-1 ──┐
            ├── Global Load Balancer (Route 53 geo-routing)
eu-west-1 ──┤
            ├── Users → nearest region (<100ms latency)
ap-south-1 ──┘
```

**Cost:** +$5,000/month (multi-region infrastructure)

---

## 17.5 Summary

| Aspect | Phase 1 | Phase 2 ← DOCUMENTED | Phase 3 | Phase 4-5 |
|--------|---------|---------------------|---------|-----------|
| **Orchestration** | Docker Compose | ECS/AKS/GKE | Kubernetes (full) | Multi-region K8s |
| **HA** | None | Auto-scaling | Multi-AZ | Multi-region |
| **Deployment** | Manual | Blue-green | Canary | GitOps |
| **IaC** | docker-compose.yml | CDK/Terraform/Helm | + Service mesh | + Policy-as-code |
| **Cost** | $500/mo | $680/mo | $5,000/mo | $25,000/mo |

**Reference:** [docs/deployment-runbooks.md](../deployment-runbooks.md) complete multi-cloud guide

