import React from 'react';
import { ErrorBoundary as ReactErrorBoundary } from 'react-error-boundary';
import { Button } from '@/components/ui/button';

interface ErrorFallbackProps {
  error: Error;
  resetErrorBoundary: () => void;
}

function ErrorFallback({ error, resetErrorBoundary }: ErrorFallbackProps) {
  return (
    <div
      role="alert"
      className="flex min-h-screen items-center justify-center bg-background p-4"
    >
      <div className="w-full max-w-md rounded-lg border bg-card p-6 text-center shadow-lg">
        <div className="mb-4 text-6xl">⚠️</div>
        <h2 className="mb-4 text-2xl font-bold text-destructive">Oops! Something went wrong</h2>
        <p className="mb-6 text-muted-foreground">
          {error.message || 'An unexpected error occurred. Please try again.'}
        </p>

        {import.meta.env.DEV && error.stack && (
          <details className="mb-6 rounded bg-muted p-4 text-left">
            <summary className="cursor-pointer font-bold text-muted-foreground">
              Error details (dev only)
            </summary>
            <pre className="mt-2 overflow-x-auto text-xs">{error.stack}</pre>
          </details>
        )}

        <div className="flex gap-3">
          <Button onClick={resetErrorBoundary} className="flex-1">
            Try again
          </Button>
          <Button onClick={() => (window.location.href = '/')} variant="outline" className="flex-1">
            Go to home
          </Button>
        </div>
      </div>
    </div>
  );
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<ErrorFallbackProps>;
}

export default function ErrorBoundary({ children, fallback }: ErrorBoundaryProps) {
  return (
    <ReactErrorBoundary
      FallbackComponent={fallback || ErrorFallback}
      onError={(error, errorInfo) => {
        // Log error
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

