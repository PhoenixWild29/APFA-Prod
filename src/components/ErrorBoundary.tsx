import { ErrorBoundary as ReactErrorBoundary, type FallbackProps } from 'react-error-boundary';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';

function ErrorFallback({ error, resetErrorBoundary }: FallbackProps) {
  // useNavigate works here because ErrorBoundary is rendered inside <Routes>
  // in App.tsx. If the router itself errors, the fallback gracefully degrades.
  let navigate: ReturnType<typeof useNavigate> | null = null;
  try {
    navigate = useNavigate();
  } catch {
    // Router context unavailable — degrade to resetErrorBoundary only
  }

  const handleReturnToAdvisor = () => {
    if (navigate) {
      resetErrorBoundary();
      navigate('/app/advisor', { replace: true });
    } else {
      resetErrorBoundary();
    }
  };

  const errObj = error instanceof Error ? error : new Error(String(error));

  return (
    <div
      role="alert"
      className="flex min-h-screen items-center justify-center bg-background p-4"
    >
      <div className="w-full max-w-md rounded-lg border bg-card p-6 text-center shadow-lg">
        <div className="mb-4 text-6xl">⚠️</div>
        <h2 className="mb-4 text-2xl font-bold text-destructive">Oops! Something went wrong</h2>
        <p className="mb-6 text-muted-foreground">
          {errObj.message || 'An unexpected error occurred. Please try again.'}
        </p>

        {import.meta.env.DEV && errObj.stack && (
          <details className="mb-6 rounded bg-muted p-4 text-left">
            <summary className="cursor-pointer font-bold text-muted-foreground">
              Error details (dev only)
            </summary>
            <pre className="mt-2 overflow-x-auto text-xs">{errObj.stack}</pre>
          </details>
        )}

        <div className="flex gap-3">
          <Button onClick={resetErrorBoundary} className="flex-1">
            Try again
          </Button>
          <Button onClick={handleReturnToAdvisor} variant="outline" className="flex-1">
            Return to advisor
          </Button>
        </div>
      </div>
    </div>
  );
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<FallbackProps>;
}

export default function ErrorBoundary({ children, fallback }: ErrorBoundaryProps) {
  return (
    <ReactErrorBoundary
      FallbackComponent={fallback || ErrorFallback}
      onError={(error, errorInfo) => {
        console.error('Error caught by boundary:', error, errorInfo);
      }}
      onReset={() => {
        // Optional: Clear app state on reset
      }}
    >
      {children}
    </ReactErrorBoundary>
  );
}
