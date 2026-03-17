# Contributing to APFA

Thank you for your interest in contributing to the AI-Powered Financial Advisor! This guide will help you get started.

## Prerequisites

- Python 3.11+
- Node.js 22+
- Docker & Docker Compose
- Git

## Getting Started

1. **Fork and clone** the repository:
   ```bash
   git clone https://github.com/<your-username>/APFA-Prod.git
   cd APFA-Prod
   ```

2. **Copy environment config**:
   ```bash
   cp .env.example .env
   ```

3. **Install dependencies**:
   ```bash
   # Backend
   pip install -r requirements.txt

   # Frontend
   npm ci
   ```

4. **Start services** (PostgreSQL, Redis, MinIO):
   ```bash
   docker compose up -d redis postgres minio
   ```

5. **Run the backend**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

6. **Run the frontend**:
   ```bash
   npm run dev
   ```

## Project Structure

```
APFA-Prod/
├── app/                # FastAPI backend
│   ├── main.py         # Application entry point
│   ├── config.py       # Settings (Pydantic)
│   ├── models/         # Database / data models
│   ├── schemas/        # Request/response schemas
│   ├── crud/           # CRUD operations
│   ├── api/            # API route modules
│   ├── services/       # Business logic
│   └── middleware/      # CSRF, auth middleware
├── src/                # React TypeScript frontend
│   ├── components/     # Reusable UI components
│   ├── pages/          # Route pages
│   ├── hooks/          # Custom React hooks
│   ├── services/       # API client layer
│   ├── store/          # Zustand state management
│   └── types/          # TypeScript definitions
├── tests/              # Python test suite
├── monitoring/         # Prometheus & Grafana configs
├── deploy/             # Deployment scripts
├── infra/              # Infrastructure-as-Code
└── docs/               # Technical documentation
```

## Code Style

### Python (Backend)
- Formatter: **Black** (line length 100)
- Linter: **Flake8** (max line 120)
- Security: **Bandit**
- Type checking: **mypy** (strict mode)

```bash
make format    # Auto-format with Black
make lint      # Run Flake8
make test      # Run pytest
```

### TypeScript (Frontend)
- Linter: **ESLint** with React + TypeScript plugins
- Formatter: **Prettier** with Tailwind CSS plugin
- Type checking: **tsc --noEmit**

```bash
npm run lint        # ESLint
npm run format      # Prettier
npm run type-check  # TypeScript
npm test            # Jest
```

## Making Changes

1. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Write tests** for new functionality.

3. **Ensure all checks pass**:
   ```bash
   make check   # Runs format check, lint, and tests
   npm run lint && npm test
   ```

4. **Commit** with a clear message:
   ```
   feat(component): add document upload drag-and-drop
   fix(api): handle expired JWT refresh tokens
   docs: update API endpoint documentation
   ```

5. **Push** and open a Pull Request against `main`.

## Pull Request Guidelines

- Keep PRs focused — one feature or fix per PR.
- Include a clear description of what changed and why.
- Reference related issues (e.g., "Closes #42").
- All CI checks must pass before merge.
- Request review from at least one maintainer.

## Architecture Notes

- **Backend**: FastAPI + LangChain/LangGraph for RAG pipeline, Celery for background jobs.
- **Frontend**: React 18 + TypeScript, Vite build, Zustand state, TanStack Query for data fetching.
- **Storage**: PostgreSQL (relational), Redis (cache/sessions), MinIO (object storage / documents).
- **Monitoring**: Prometheus metrics + Grafana dashboards.

## Questions?

Open an issue or reach out to the maintainers. We appreciate every contribution!
