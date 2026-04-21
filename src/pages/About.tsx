export default function About() {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="text-3xl font-bold">About APFA</h1>

      <div className="space-y-4 text-muted-foreground">
        <p>
          The AI-Powered Financial Advisor (APFA) is a production-ready research tool that
          leverages multi-agent architecture to provide intelligent investment research
          and financial analysis. It combines retrieval-augmented generation with real-time
          market data to help you make informed financial decisions.
        </p>

        <h2 className="text-xl font-semibold text-foreground">Technology Stack</h2>
        <ul className="list-inside list-disc space-y-2">
          <li>
            <strong>Frontend:</strong> React 19 + TypeScript + Vite + Tailwind CSS + shadcn/ui
          </li>
          <li>
            <strong>Backend:</strong> FastAPI + Python with multi-agent LangGraph orchestration
          </li>
          <li>
            <strong>AI/ML:</strong> OpenAI GPT-4o for LLM, FastEmbed/ONNX bge-small-en-v1.5 for embeddings, FAISS for vector search
          </li>
          <li>
            <strong>Data Pipeline:</strong> Celery workers with connectors for Google Drive, Finnhub, and YouTube
          </li>
          <li>
            <strong>Storage:</strong> PostgreSQL + Redis + Delta Lake + MinIO
          </li>
          <li>
            <strong>Infrastructure:</strong> Docker + Nginx + Let&apos;s Encrypt SSL on DigitalOcean
          </li>
        </ul>

        <h2 className="text-xl font-semibold text-foreground">How It Works</h2>
        <p>
          When you ask a question, APFA searches through a curated knowledge base of
          financial documents using semantic search, retrieves the most relevant passages,
          and generates a research-backed answer with cited sources. The system shows its
          work so you can verify the reasoning behind every recommendation.
        </p>

        <h2 className="text-xl font-semibold text-foreground">Key Features</h2>
        <ul className="list-inside list-disc space-y-2">
          <li>AI advisor with retrieval-augmented generation (RAG) and source citations</li>
          <li>Real-time market data integration via Finnhub</li>
          <li>Document upload and semantic search across your financial documents</li>
          <li>Investment dashboard with portfolio tracking and market indices</li>
          <li>Hot-swappable FAISS indexes for zero-downtime knowledge base updates</li>
          <li>Comprehensive security with JWT auth, token rotation, and RBAC</li>
        </ul>
      </div>
    </div>
  );
}
