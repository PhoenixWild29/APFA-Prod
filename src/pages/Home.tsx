import { useHealthCheck } from '@/api/useApi';
import LoadingIndicator from '@/components/LoadingIndicator';
import { Button } from '@/components/ui/button';
import { CheckCircle2, XCircle } from 'lucide-react';

export default function Home() {
  const { data: health, isLoading, error } = useHealthCheck();

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <section className="py-12 text-center">
        <h1 className="mb-4 text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
          AI-Powered Financial Advisory
        </h1>
        <p className="mx-auto mb-8 max-w-2xl text-lg text-muted-foreground">
          Get personalized loan recommendations powered by advanced multi-agent AI systems
        </p>
        <div className="flex justify-center gap-4">
          <Button size="lg">Get Started</Button>
          <Button size="lg" variant="outline">
            Learn More
          </Button>
        </div>
      </section>

      {/* API Status */}
      <section className="mx-auto max-w-md rounded-lg border bg-card p-6">
        <h2 className="mb-4 text-xl font-semibold">API Status</h2>

        {isLoading && <LoadingIndicator message="Checking API health..." size="small" />}

        {error && (
          <div className="flex items-center gap-2 text-destructive">
            <XCircle className="h-5 w-5" />
            <span>API Unavailable</span>
          </div>
        )}

        {health && (
          <div className="flex items-center gap-2 text-green-600">
            <CheckCircle2 className="h-5 w-5" />
            <span>API {health.status === 'healthy' ? 'Healthy' : 'Unknown'}</span>
          </div>
        )}
      </section>

      {/* Features */}
      <section className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <FeatureCard
          title="Multi-Agent AI"
          description="Advanced RAG and LLM-powered analysis for accurate recommendations"
        />
        <FeatureCard
          title="Real-Time Processing"
          description="Background job processing with Celery for fast, scalable operations"
        />
        <FeatureCard
          title="Security First"
          description="JWT authentication, RBAC, and comprehensive audit logging"
        />
      </section>
    </div>
  );
}

function FeatureCard({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-lg border bg-card p-6">
      <h3 className="mb-2 text-lg font-semibold">{title}</h3>
      <p className="text-sm text-muted-foreground">{description}</p>
    </div>
  );
}

