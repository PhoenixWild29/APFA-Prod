export default function About() {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="text-3xl font-bold">About APFA</h1>

      <div className="space-y-4 text-muted-foreground">
        <p>
          The Agentic Personalized Financial Advisor (APFA) is a production-ready AI system that
          leverages multi-agent architecture to provide intelligent loan advisory services.
        </p>

        <h2 className="text-xl font-semibold text-foreground">Technology Stack</h2>
        <ul className="list-inside list-disc space-y-2">
          <li>
            <strong>Frontend:</strong> React 18 + TypeScript + Vite + Tailwind CSS
          </li>
          <li>
            <strong>Backend:</strong> FastAPI + Python with multi-agent LangGraph
          </li>
          <li>
            <strong>AI/ML:</strong> RAG with FAISS, LLM (Llama-3-8B), Sentence Transformers
          </li>
          <li>
            <strong>Background Jobs:</strong> Celery with Redis message broker
          </li>
          <li>
            <strong>Data:</strong> Delta Lake for structured data, MinIO for object storage
          </li>
          <li>
            <strong>Monitoring:</strong> Prometheus + Grafana for observability
          </li>
        </ul>

        <h2 className="text-xl font-semibold text-foreground">Architecture</h2>
        <p>
          APFA uses a micro-frontend architecture with Webpack Module Federation, allowing
          independent deployment of different features while maintaining a unified user experience.
        </p>

        <h2 className="text-xl font-semibold text-foreground">Key Features</h2>
        <ul className="list-inside list-disc space-y-2">
          <li>Multi-agent AI system with retrieval-augmented generation (RAG)</li>
          <li>Asynchronous background job processing for scalability</li>
          <li>Hot-swappable FAISS indexes for zero-downtime updates</li>
          <li>Comprehensive security with JWT auth and RBAC</li>
          <li>Real-time monitoring and admin dashboards</li>
          <li>Responsive design supporting mobile to desktop (320px-1920px)</li>
        </ul>
      </div>
    </div>
  );
}

