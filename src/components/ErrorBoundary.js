/**
 * React Error Boundary component for graceful error handling
 */
import React from 'react';
import { ErrorBoundary as ReactErrorBoundary } from 'react-error-boundary';
import { formatErrorMessage, logError } from '../api/errorHandling';

/**
 * Error fallback component
 * Displayed when an error is caught by the boundary
 */
function ErrorFallback({ error, resetErrorBoundary }) {
  React.useEffect(() => {
    // Log error when component mounts
    logError(error, { component: 'ErrorBoundary' });
  }, [error]);
  
  return (
    <div role="alert" style={styles.container}>
      <div style={styles.content}>
        <div style={styles.icon}>⚠️</div>
        <h2 style={styles.title}>Oops! Something went wrong</h2>
        <p style={styles.message}>{formatErrorMessage(error)}</p>
        
        {process.env.NODE_ENV === 'development' && error.stack && (
          <details style={styles.details}>
            <summary style={styles.summary}>Error details (dev only)</summary>
            <pre style={styles.stack}>{error.stack}</pre>
          </details>
        )}
        
        <div style={styles.actions}>
          <button onClick={resetErrorBoundary} style={styles.primaryButton}>
            Try again
          </button>
          <button
            onClick={() => (window.location.href = '/')}
            style={styles.secondaryButton}
          >
            Go to home
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * Main Error Boundary component
 * Wraps app or components to catch and handle errors gracefully
 */
export default function ErrorBoundary({ children, fallback }) {
  return (
    <ReactErrorBoundary
      FallbackComponent={fallback || ErrorFallback}
      onError={(error, errorInfo) => {
        // Log error with component stack
        logError(error, {
          componentStack: errorInfo.componentStack,
          boundary: 'ErrorBoundary',
        });
      }}
      onReset={() => {
        // Optional: Clear app state on reset
        // queryClient.clear();
      }}
    >
      {children}
    </ReactErrorBoundary>
  );
}

/**
 * Styles for error boundary UI
 */
const styles = {
  container: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '100vh',
    padding: '20px',
    backgroundColor: '#f5f5f5',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },
  content: {
    maxWidth: '600px',
    width: '100%',
    backgroundColor: 'white',
    borderRadius: '8px',
    padding: '40px',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
    textAlign: 'center',
  },
  icon: {
    fontSize: '48px',
    marginBottom: '20px',
  },
  title: {
    fontSize: '24px',
    fontWeight: 'bold',
    marginBottom: '16px',
    color: '#d32f2f',
  },
  message: {
    fontSize: '16px',
    marginBottom: '24px',
    color: '#666',
    lineHeight: '1.5',
  },
  details: {
    marginBottom: '24px',
    textAlign: 'left',
    backgroundColor: '#f5f5f5',
    borderRadius: '4px',
    padding: '16px',
  },
  summary: {
    cursor: 'pointer',
    fontWeight: 'bold',
    marginBottom: '8px',
    color: '#666',
  },
  stack: {
    fontSize: '12px',
    color: '#333',
    overflowX: 'auto',
    whiteSpace: 'pre-wrap',
    wordWrap: 'break-word',
  },
  actions: {
    display: 'flex',
    gap: '12px',
    justifyContent: 'center',
  },
  primaryButton: {
    padding: '12px 24px',
    fontSize: '16px',
    backgroundColor: '#1976d2',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontWeight: '500',
    transition: 'background-color 0.2s',
  },
  secondaryButton: {
    padding: '12px 24px',
    fontSize: '16px',
    backgroundColor: 'white',
    color: '#1976d2',
    border: '2px solid #1976d2',
    borderRadius: '4px',
    cursor: 'pointer',
    fontWeight: '500',
    transition: 'all 0.2s',
  },
};

