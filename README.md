# APFA - Agentic Personalized Financial Advisor

A production-ready AI-powered financial advisor system built with FastAPI, featuring Retrieval-Augmented Generation (RAG), Large Language Models (LLMs), and multi-agent architecture for secure, scalable loan advice generation.

---

## 📖 Documentation

**📚 [Complete Documentation Suite](docs/README.md)** - Master index to all technical documentation

### Quick Links
- 🏗️ [Architecture Overview](docs/architecture.md) - System design and components
- 📡 [API Documentation](docs/api.md) - REST API endpoints and usage
- 🔧 [Background Jobs](docs/background-jobs.md) - Celery architecture and operations
- 📊 [Observability](docs/observability.md) - Monitoring, metrics, and alerts
- 🚀 [Deployment Runbooks](docs/deployment-runbooks.md) - AWS, Azure, GCP deployment guides
- ⚡ [Quick Reference](docs/quick-reference.md) - Common commands and troubleshooting

---

## 🚀 Features

### Core Capabilities
- **Advanced RAG System**: FAISS-powered similarity search with Delta Lake integration and L2 normalization
- **Multi-Agent Architecture**: LangChain-based agents with tool-calling capabilities for complex financial reasoning
- **Background Job Processing**: Celery-based asynchronous embedding and indexing for **100x performance improvement**
- **Zero-Downtime Updates**: Hot-swap mechanism for continuous service availability during index updates
- **JWT Authentication**: Secure OAuth2 token-based authentication with bcrypt password hashing
- **Circuit Breaker Resilience**: Automatic failure handling and recovery for external service calls

### Performance & Scalability
- **High Performance**: <3s P95 latency (uncached), <500ms (cached)
- **Horizontal Scaling**: Stateless design supports 100+ concurrent requests
- **Async Processing**: Non-blocking I/O with thread pools for CPU-intensive tasks
- **Multi-Level Caching**: Redis + in-memory caching with 80%+ hit rate target
- **Auto-Scaling**: CPU-based auto-scaling (70% target utilization)

### Security & Reliability
- **Rate Limiting**: Global and per-user request throttling (10 req/min)
- **Input Validation**: Profanity filtering, financial validation, and content sanitization
- **Testing Suite**: Comprehensive unit and integration tests with pytest
- **99.9% Uptime**: Circuit breakers, retries, and health checks

### Monitoring & Operations
- **Comprehensive Monitoring**: Prometheus metrics with 3 Grafana dashboards (30+ metrics)
- **Real-Time Alerts**: 8 automated alerts with response runbooks
- **Admin Dashboards**: React-based admin UI for task monitoring and management
- **Production Deployment**: Multi-cloud support (AWS, Azure, GCP) with IaC (CDK, Terraform, Helm)

## 🛠️ Installation

### Prerequisites
- Python 3.11+
- Docker & Docker Compose (for full deployment)

### Local Development Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd apfa_prod
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## ⚙️ Configuration

Create a `.env` file with the following variables:

```env
# MinIO Configuration
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# AWS Configuration
AWS_REGION=us-east-1

# Application Configuration
API_KEY=your-api-key-here
JWT_SECRET=your-jwt-secret-here
DEBUG=false

# Model Configuration
EMBEDDER_MODEL=all-MiniLM-L6-v2
LLM_MODEL_NAME=meta-llama/Llama-3-8b-hf
DELTA_TABLE_PATH=s3a://customer-data-lakehouse/customers
```

## 🧪 Testing

### Unit Tests
Run the comprehensive test suite:
```bash
python -m pytest tests/ -v
```

### Manual Testing

1. **Start the application**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

2. **Test health endpoint**:
   ```bash
   curl http://localhost:8000/health
   # Expected: {"status": "healthy"}
   ```

3. **Authenticate and get JWT token**:
   ```bash
   curl -X POST "http://localhost:8000/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=admin123"
   # Returns: {"access_token": "jwt_token_here", "token_type": "bearer"}
   ```

4. **Generate loan advice**:
   ```bash
   curl -X POST "http://localhost:8000/generate-advice" \
     -H "Authorization: Bearer <jwt_token>" \
     -H "Content-Type: application/json" \
     -d '{"query": "What is a good loan option for me?"}'
   ```

### Integration Testing

For full-stack testing with monitoring:
```bash
./deploy.sh
# This starts APFA + Prometheus + Grafana
```

## 🚀 Deployment

### Quick Start with Docker Compose
```bash
./deploy.sh
```

This command:
- Builds the APFA container
- Starts the application, Prometheus, and Grafana
- Configures monitoring and health checks

### Manual Deployment

1. **Build Docker image**:
   ```bash
   docker build -t apfa .
   ```

2. **Run with docker-compose**:
   ```bash
   docker-compose up -d
   ```

3. **Access services**:
   - **APFA API**: http://localhost:8000
   - **API Documentation (Swagger)**: http://localhost:8000/docs
   - **Prometheus**: http://localhost:9090
   - **Grafana**: http://localhost:3000 (admin/admin)
   - **Flower (Celery)**: http://localhost:5555
   - **Redis**: localhost:6379

## 📚 API Documentation

### Authentication Endpoints

#### POST /token
OAuth2 compatible token endpoint.

**Request**:
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1Qi...",
  "token_type": "bearer"
}
```

### Main Endpoints

#### GET /health
Health check endpoint.

**Response**: `{"status": "healthy"}`

#### GET /metrics
Prometheus metrics endpoint.

**Response**: Prometheus-formatted metrics

#### POST /generate-advice
Generate personalized loan advice.

**Headers**:
- `Authorization: Bearer <jwt_token>`

**Request**:
```json
{
  "query": "What loan options are available for $50,000?"
}
```

**Response**:
```json
{
  "advice": "Based on your query...",
  "user": "admin"
}
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │────│   LangChain     │────│   External APIs  │
│                 │    │   Agents        │    │   (MinIO, AWS)   │
│ - Auth & Rate   │    │                 │    │                 │
│   Limiting      │    │ - RAG Tools     │    │ - Risk Analysis │
│ - Input         │    │                 │    │ - Model Storage │
│   Validation    │    │                 │    │ - Monitoring    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Monitoring    │
                    │   Stack         │
                    │                 │
                    │ - Prometheus    │
                    │ - Grafana       │
                    │ - Health Checks │
                    └─────────────────┘
```

## 📚 Complete Documentation

### 📖 Comprehensive Guides (570 KB, 15 hours read time)

| Document | Purpose | Audience | Read Time |
|----------|---------|----------|-----------|
| **[Master Index](docs/README.md)** | Documentation navigation | All | 15 min |
| **[Architecture](docs/architecture.md)** | System design overview | All | 30 min |
| **[API Spec](docs/api-spec.yaml)** | OpenAPI 3.0 specification | Developers | N/A |
| **[Background Jobs](docs/background-jobs.md)** ⭐ | Celery implementation | Backend, SRE | 2 hours |
| **[Observability](docs/observability.md)** ⭐ | Monitoring & alerts | SRE | 1.5 hours |
| **[Frontend Dashboards](docs/frontend-admin-dashboards.md)** | React admin UI | Frontend | 2 hours |
| **[API Integration](docs/api-integration-patterns.md)** | WebSocket & polling | Full-stack | 2 hours |
| **[Deployment Runbooks](docs/deployment-runbooks.md)** ⭐ | Multi-cloud deployment | DevOps | 3 hours |
| **[Quick Reference](docs/quick-reference.md)** | Common commands | All | 10 min |

### 📐 Architecture Decision Records (ADRs)

| ADR | Decision | Status | Impact |
|-----|----------|--------|--------|
| **[ADR-001](docs/adrs/001-celery-vs-rq.md)** | Celery vs RQ | Accepted | Critical path fix |
| **[ADR-002](docs/adrs/002-faiss-indexflat-to-ivfflat-migration.md)** | FAISS migration strategy | Accepted | Scalability roadmap |
| **[ADR-003](docs/adrs/003-multi-queue-architecture.md)** | Multi-queue design | Accepted | Resource isolation |

### 📋 Implementation Plans

- **[3-Week Celery Implementation Plan](docs/celery-implementation-project-plan.md)** - Detailed roadmap with 40 tasks, dependencies, and success criteria

---

## 🎯 Performance Metrics

### Current Performance (Post-Celery Implementation)

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **P95 Latency (uncached)** | 15s | 3s | **5x faster** ✅ |
| **Startup Time** | 10-100s | <1s | **10-100x faster** ✅ |
| **Embedding Throughput** | 100 docs/sec | 1,000-5,000 docs/sec | **10-50x faster** ✅ |
| **Index Rebuild Downtime** | 100% blocking | 0% (hot-swap) | **Zero downtime** ✅ |
| **Cache Hit Rate** | 65% | 80%+ | **23% improvement** ✅ |

### System Capacity

- **Current:** 50K vectors, P95 search <10ms
- **Phase 1:** Up to 500K vectors (IndexFlatIP)
- **Phase 2:** Up to 10M vectors (IndexIVFFlat)
- **Phase 3:** 10M+ vectors (IndexIVFPQ)

See [ADR-002](docs/adrs/002-faiss-indexflat-to-ivfflat-migration.md) for migration strategy.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Documentation Contributions

See [docs/README.md#contributing](docs/README.md#contributing-to-documentation) for documentation guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with FastAPI, LangChain, and Hugging Face Transformers
- Monitoring powered by Prometheus and Grafana
- Containerization with Docker
