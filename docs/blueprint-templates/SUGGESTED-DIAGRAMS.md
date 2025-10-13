# Suggested Diagrams for Blueprint

Add these 3 diagrams to your blueprint for maximum visual impact.

---

## Diagram 1: APFA System Architecture

**Where to add:** Section 2.0 (System Overview) or Section 0.0 (Backend General)

**Mermaid Code:**
```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[React Admin Dashboard<br/>- CeleryJobMonitor<br/>- BatchProcessingStatus<br/>- IndexManagement]
    end
    
    subgraph "API Layer"
        API[FastAPI Application<br/>:8000]
        WS[WebSocket Server<br/>Real-time Updates]
    end
    
    subgraph "AI/ML Pipeline"
        RAG[RAG Pipeline<br/>FAISS Index]
        LLM[LLM Service<br/>Llama-3-8B]
        EMB[Embedding Model<br/>all-MiniLM-L6-v2]
    end
    
    subgraph "Background Jobs"
        CELERY[Celery Workers<br/>4 workers<br/>4,000 docs/sec]
        BEAT[Celery Beat<br/>Scheduler]
        FLOWER[Flower<br/>:5555 Monitor]
    end
    
    subgraph "Data Layer"
        REDIS[(Redis<br/>Cache + Broker)]
        MINIO[(MinIO<br/>FAISS Indexes<br/>Models)]
        DELTA[(Delta Lake<br/>User Profiles)]
    end
    
    subgraph "Monitoring"
        PROM[Prometheus<br/>:9090]
        GRAF[Grafana<br/>:3000]
    end
    
    subgraph "External Services"
        BEDROCK[AWS Bedrock<br/>Risk Analysis]
    end
    
    UI -->|HTTPS| API
    UI -->|WSS| WS
    API --> RAG
    API --> LLM
    API --> CELERY
    API --> BEDROCK
    RAG --> EMB
    RAG --> MINIO
    CELERY --> REDIS
    CELERY --> MINIO
    CELERY --> DELTA
    BEAT --> CELERY
    API --> REDIS
    API --> PROM
    CELERY --> PROM
    PROM --> GRAF
    
    style API fill:#4A90E2
    style CELERY fill:#F5A623
    style RAG fill:#7ED321
    style REDIS fill:#D0021B
    style MINIO fill:#BD10E0
```

**ASCII Alternative (if Mermaid not supported):**
```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (React + Admin UI)                  │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS/WebSocket
┌────────────────────────────▼────────────────────────────────────┐
│                   FastAPI Application (:8000)                   │
│  • JWT Auth + RBAC         • Advice Generation                  │
│  • Admin APIs              • Real-time WebSocket                │
└─────┬──────────┬───────────┬──────────────┬─────────────────────┘
      │          │           │              │
      │    ┌─────▼─────┐ ┌───▼──────┐  ┌───▼──────────┐
      │    │  Redis    │ │  MinIO   │  │  Delta Lake  │
      │    │  Cache    │ │  FAISS   │  │  Profiles    │
      │    │  Broker   │ │  Models  │  │              │
      │    └─────┬─────┘ └──────────┘  └──────────────┘
      │          │
      │    ┌─────▼──────────────────────────────────────┐
      │    │        Celery Workers (4 workers)          │
      │    │  • Batch Embedding: 4,000 docs/sec         │
      │    │  • Index Building: <5s                     │
      │    │  • Hot-swap: 0ms downtime                  │
      │    └────────────────────────────────────────────┘
      │
┌─────▼──────────────┐     ┌──────────────────┐
│   RAG Pipeline     │────▶│  AWS Bedrock     │
│   FAISS + LLM      │     │  Risk Analysis   │
└────────────────────┘     └──────────────────┘
      │
      │
┌─────▼──────────────────────────────────┐
│     Monitoring (Prometheus + Grafana)  │
└────────────────────────────────────────┘
```

---

## Diagram 2: Celery Background Pipeline Flow

**Where to add:** Section 8.0 (Document Processing) or Section 11.0 (AI/ML Pipeline)

**Mermaid Code:**
```mermaid
graph LR
    A[Delta Lake<br/>100K profiles] --> B[Batch Creation<br/>100 batches<br/>1K docs each]
    B --> C{Celery Group<br/>Parallel Processing}
    C -->|Worker 1| D1[Embed Batch 1-25<br/>25K docs]
    C -->|Worker 2| D2[Embed Batch 26-50<br/>25K docs]
    C -->|Worker 3| D3[Embed Batch 51-75<br/>25K docs]
    C -->|Worker 4| D4[Embed Batch 76-100<br/>25K docs]
    D1 --> E[Upload to MinIO<br/>embeddings/*.npy]
    D2 --> E
    D3 --> E
    D4 --> E
    E --> F[Build FAISS Index<br/>IndexIVFFlat<br/>100K vectors]
    F --> G[Upload Index<br/>MinIO<br/>faiss_index_v42.bin]
    G --> H[Publish Redis<br/>Hot-swap Event<br/>channel: index_updates]
    H --> I[FastAPI Workers<br/>Load New Index<br/>0ms downtime]
    
    style C fill:#F5A623
    style F fill:#7ED321
    style I fill:#4A90E2
```

**ASCII Alternative:**
```
Phase 1: Ingestion
┌─────────────┐
│ Delta Lake  │  Load 100K profiles
│ 100K docs   │
└──────┬──────┘
       │
Phase 2: Batch Creation
       ▼
┌──────────────────┐
│  Split to Batches│  100 batches × 1,000 docs
└──────┬───────────┘
       │
Phase 3: Parallel Embedding (Celery Group)
       ▼
  ┌────┴────┬────────┬────────┐
  │         │        │        │
Worker 1  Worker 2  Worker 3  Worker 4
Batch 1-25 26-50   51-75     76-100
25K docs  25K docs 25K docs  25K docs
  │         │        │        │
  └────┬────┴────────┴────────┘
       │ Upload embeddings
       ▼
  ┌────────────┐
  │   MinIO    │  embeddings/*.npy
  └─────┬──────┘
        │
Phase 4: Index Building
        ▼
  ┌────────────────┐
  │ Build FAISS    │  IndexIVFFlat
  │ 100K vectors   │  <5s duration
  └────────┬───────┘
           │
Phase 5: Hot-swap Deployment
           ▼
  ┌────────────────┐
  │ Upload to MinIO│  faiss_index_v42.bin
  └────────┬───────┘
           │
           ▼
  ┌────────────────┐
  │ Redis Pub/Sub  │  channel: index_updates
  └────────┬───────┘
           │
           ▼
  ┌────────────────┐
  │ FastAPI Reload │  0ms downtime
  │ New Index      │  Hot-swap complete
  └────────────────┘

Performance:
• Throughput: 4,000 docs/sec (40x vs synchronous)
• Total Time: <60s for 100K docs
• Downtime: 0ms (hot-swap)
```

---

## Diagram 3: Phased Evolution Timeline

**Where to add:** Section 1.0 (Introduction) or Architecture Roadmap section

**Mermaid Code:**
```mermaid
graph LR
    P1[Phase 1: MVP<br/>In-memory<br/>10K docs<br/>Single host]
    P2[Phase 2: Production<br/>Celery + FAISS<br/>500K docs<br/>ECS/AKS/GKE]
    P3[Phase 3: Scale<br/>Multi-region<br/>10M docs<br/>Auto-scaling]
    P4[Phase 4-5: Enterprise<br/>Kafka + Airflow<br/>100M+ docs<br/>Global deployment]
    
    P1 -->|Trigger: 10K+ docs<br/>Latency: >10s<br/>Cost: ~$500/mo| P2
    P2 -->|Trigger: 500K+ docs<br/>Latency: >100ms<br/>Cost: ~$680/mo| P3
    P3 -->|Trigger: 10M+ docs<br/>Multi-region need<br/>Cost: ~$5K/mo| P4
    
    style P1 fill:#E8E8E8
    style P2 fill:#4A90E2
    style P3 fill:#F5A623
    style P4 fill:#7ED321
```

**ASCII Alternative:**
```
Phase 1          Phase 2           Phase 3           Phase 4-5
MVP              Production        Scale             Enterprise
─────────────────────────────────────────────────────────────────────
• In-memory      • Celery workers  • Multi-region    • Kafka streams
• Mock data      • FAISS IndexIVF  • Aurora RDS      • Airflow DAGs
• Docker         • Redis cache     • ElastiCache     • ML Platform
• 10K docs       • MinIO/S3        • Active-passive  • Redshift
• Single host    • ECS/AKS/GKE     • Auto-scaling    • Global CDN
• $500/mo        • $680/mo         • $5,000/mo       • $25,000/mo

Latency:         Latency:          Latency:          Latency:
10-100s          <100ms            <50ms             <10ms

Throughput:      Throughput:       Throughput:       Throughput:
100 docs/sec     4,000 docs/sec    10K+ docs/sec     100K+ docs/sec

Capacity:        Capacity:         Capacity:         Capacity:
10K docs         500K docs         10M docs          100M+ docs

    │                │                 │                 │
    │ Triggers:      │ Triggers:       │ Triggers:       │
    │ • >10K docs    │ • >500K vectors │ • >10M docs     │
    │ • Latency >10s │ • Latency >100ms│ • Global users  │
    │ • Need async   │ • Multi-AZ need │ • Compliance++  │
    ▼                ▼                 ▼                 ▼
```

---

## Diagram 4: RBAC Permission Model (Optional)

**Where to add:** Section 5.0 (RBAC) or Section 12.0 (User Authentication)

**Mermaid Code:**
```mermaid
graph TD
    subgraph "Roles"
        R1[User]
        R2[Financial Advisor]
        R3[Admin]
        R4[Super Admin]
    end
    
    subgraph "Permissions"
        P1[advice:generate]
        P2[advice:view_history]
        P3[metrics:view]
        P4[celery:view]
        P5[celery:manage]
        P6[index:manage]
        P7[users:manage]
        P8[audit:view]
    end
    
    R1 --> P1
    R1 --> P2
    R2 --> P1
    R2 --> P2
    R2 --> P3
    R3 --> P1
    R3 --> P4
    R3 --> P5
    R3 --> P6
    R4 --> P1
    R4 --> P2
    R4 --> P3
    R4 --> P4
    R4 --> P5
    R4 --> P6
    R4 --> P7
    R4 --> P8
    
    style R1 fill:#E8E8E8
    style R2 fill:#4A90E2
    style R3 fill:#F5A623
    style R4 fill:#D0021B
```

**Table Alternative:**
```
┌─────────────────┬──────────────────────────────────────────────────┐
│ Role            │ Permissions                                      │
├─────────────────┼──────────────────────────────────────────────────┤
│ User            │ • advice:generate                                │
│                 │ • advice:view_history                            │
├─────────────────┼──────────────────────────────────────────────────┤
│ Financial       │ • advice:generate                                │
│ Advisor         │ • advice:view_history                            │
│                 │ • metrics:view                                   │
├─────────────────┼──────────────────────────────────────────────────┤
│ Admin           │ • advice:generate                                │
│                 │ • celery:view                                    │
│                 │ • celery:manage                                  │
│                 │ • index:manage                                   │
├─────────────────┼──────────────────────────────────────────────────┤
│ Super Admin     │ • ALL PERMISSIONS                                │
│                 │ • users:manage                                   │
│                 │ • audit:view                                     │
└─────────────────┴──────────────────────────────────────────────────┘
```

---

## How to Add Diagrams

### Option 1: Mermaid (Recommended)
If your blueprint platform supports Mermaid:
1. Copy the Mermaid code block
2. Paste directly into markdown
3. It will render as a diagram automatically

### Option 2: ASCII Art
If Mermaid not supported:
1. Copy the ASCII alternative
2. Paste into a code block (```text)
3. Ensure monospace font for alignment

### Option 3: External Tool
Create diagrams with:
- **draw.io** (free, exports as PNG/SVG)
- **Lucidchart** (professional)
- **PlantUML** (text-based, like Mermaid)

---

## Impact Assessment

**Adding 2-3 of these diagrams will:**
- ✅ Increase visual appeal (breaks up text)
- ✅ Improve understanding (visual learners)
- ✅ Show communication skills (complex → simple)
- ✅ Demonstrate system thinking (holistic view)
- ✅ Make blueprint memorable (stands out)

**Recommended:**
1. ✅ Diagram 1 (System Architecture) - MUST HAVE
2. ✅ Diagram 2 (Celery Pipeline) - HIGH VALUE
3. ✅ Diagram 3 (Phased Evolution) - STRATEGIC VALUE
4. ⚠️ Diagram 4 (RBAC) - OPTIONAL (only if you want to emphasize security)

---

**Choose 2-3 diagrams and add to your blueprint for maximum impact!**

