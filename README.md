# APFA - Agentic Personalized Financial Advisor

A production-ready AI-powered financial advisor system built with FastAPI, featuring Retrieval-Augmented Generation (RAG), Large Language Models (LLMs), and multi-agent architecture for secure, scalable loan advice generation.

## 🚀 Features

- **Advanced RAG System**: FAISS-powered similarity search with Delta Lake integration and L2 normalization
- **Multi-Agent Architecture**: LangChain-based agents with tool-calling capabilities for complex financial reasoning
- **JWT Authentication**: Secure OAuth2 token-based authentication with bcrypt password hashing
- **Circuit Breaker Resilience**: Automatic failure handling and recovery for external service calls
- **Comprehensive Monitoring**: Prometheus metrics with Grafana dashboards for real-time observability
- **Async Performance**: Non-blocking processing with advanced caching (Redis + in-memory) and thread pools
- **Rate Limiting**: Global and per-user request throttling to prevent abuse
- **Input Validation**: Profanity filtering, financial validation, and content sanitization
- **Testing Suite**: Comprehensive unit and integration tests with pytest
- **Production Deployment**: Docker containerization with docker-compose, health checks, and automation scripts

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
   - APFA API: http://localhost:8000
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3000 (admin/admin)

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

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with FastAPI, LangChain, and Hugging Face Transformers
- Monitoring powered by Prometheus and Grafana
- Containerization with Docker
