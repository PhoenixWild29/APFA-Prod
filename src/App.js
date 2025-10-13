/**
 * Main App component
 * Wraps application with providers and error boundary
 */
import React from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { queryClient } from './api/queryClient';
import ErrorBoundary from './components/ErrorBoundary';
import LoadingIndicator from './components/LoadingIndicator';
import { useHealthCheck } from './api/useApi';

/**
 * Main application component
 */
function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <div className="App" style={styles.app}>
          <header style={styles.header}>
            <h1 style={styles.title}>APFA - AI Financial Advisor</h1>
            <p style={styles.subtitle}>Agentic Personalized Financial Advisor</p>
          </header>
          
          <main style={styles.main}>
            <StatusCard />
            <InfoCard />
          </main>
          
          <footer style={styles.footer}>
            <p>© 2025 APFA - Powered by FastAPI + React</p>
          </footer>
        </div>
        
        {/* Dev tools (only in development) */}
        {process.env.NODE_ENV === 'development' && (
          <ReactQueryDevtools initialIsOpen={false} />
        )}
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

/**
 * Status card showing API health
 */
function StatusCard() {
  const { data, isLoading, error } = useHealthCheck();
  
  return (
    <div style={styles.card}>
      <h2 style={styles.cardTitle}>API Status</h2>
      
      {isLoading && (
        <LoadingIndicator message="Checking API health..." size="small" />
      )}
      
      {error && (
        <div style={styles.statusError}>
          <span style={styles.statusIcon}>❌</span>
          <span>API Unavailable</span>
        </div>
      )}
      
      {data && (
        <div style={styles.statusSuccess}>
          <span style={styles.statusIcon}>✅</span>
          <span>API {data.status === 'healthy' ? 'Healthy' : 'Unknown'}</span>
        </div>
      )}
    </div>
  );
}

/**
 * Info card showing features
 */
function InfoCard() {
  return (
    <div style={styles.card}>
      <h2 style={styles.cardTitle}>Frontend Integration Ready</h2>
      
      <div style={styles.features}>
        <Feature icon="✅" title="Authentication" description="JWT token management with auto-retry" />
        <Feature icon="✅" title="API Client" description="Axios with circuit breaker and exponential backoff" />
        <Feature icon="✅" title="State Management" description="TanStack Query with 5-min cache" />
        <Feature icon="✅" title="Error Handling" description="Error boundaries and user-friendly messages" />
        <Feature icon="✅" title="Optimistic Updates" description="Instant UI feedback for better UX" />
        <Feature icon="✅" title="Loading States" description="Multiple loading indicator variants" />
      </div>
      
      <div style={styles.nextSteps}>
        <h3 style={styles.nextStepsTitle}>Next Steps:</h3>
        <ol style={styles.nextStepsList}>
          <li>Implement login/authentication UI components</li>
          <li>Create advice generation form</li>
          <li>Build admin dashboards (Celery, Index, Metrics)</li>
          <li>Add WebSocket integration for real-time updates</li>
        </ol>
      </div>
    </div>
  );
}

/**
 * Feature item component
 */
function Feature({ icon, title, description }) {
  return (
    <div style={styles.feature}>
      <span style={styles.featureIcon}>{icon}</span>
      <div>
        <h4 style={styles.featureTitle}>{title}</h4>
        <p style={styles.featureDescription}>{description}</p>
      </div>
    </div>
  );
}

/**
 * Styles
 */
const styles = {
  app: {
    minHeight: '100vh',
    backgroundColor: '#f5f5f5',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },
  header: {
    backgroundColor: '#1976d2',
    color: 'white',
    padding: '32px 20px',
    textAlign: 'center',
  },
  title: {
    margin: 0,
    fontSize: '32px',
    fontWeight: 'bold',
  },
  subtitle: {
    margin: '8px 0 0 0',
    fontSize: '16px',
    opacity: 0.9,
  },
  main: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '40px 20px',
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
    gap: '24px',
  },
  card: {
    backgroundColor: 'white',
    borderRadius: '8px',
    padding: '24px',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
  },
  cardTitle: {
    margin: '0 0 20px 0',
    fontSize: '20px',
    fontWeight: '600',
    color: '#333',
  },
  statusSuccess: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '12px',
    backgroundColor: '#e8f5e9',
    borderRadius: '4px',
    color: '#2e7d32',
    fontWeight: '500',
  },
  statusError: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '12px',
    backgroundColor: '#ffebee',
    borderRadius: '4px',
    color: '#c62828',
    fontWeight: '500',
  },
  statusIcon: {
    fontSize: '20px',
  },
  features: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
    marginBottom: '24px',
  },
  feature: {
    display: 'flex',
    gap: '12px',
    alignItems: 'flex-start',
  },
  featureIcon: {
    fontSize: '20px',
    marginTop: '2px',
  },
  featureTitle: {
    margin: '0 0 4px 0',
    fontSize: '16px',
    fontWeight: '600',
    color: '#333',
  },
  featureDescription: {
    margin: 0,
    fontSize: '14px',
    color: '#666',
  },
  nextSteps: {
    borderTop: '1px solid #e0e0e0',
    paddingTop: '20px',
  },
  nextStepsTitle: {
    margin: '0 0 12px 0',
    fontSize: '16px',
    fontWeight: '600',
    color: '#333',
  },
  nextStepsList: {
    margin: 0,
    paddingLeft: '20px',
    fontSize: '14px',
    color: '#666',
    lineHeight: '1.8',
  },
  footer: {
    textAlign: 'center',
    padding: '20px',
    color: '#666',
    fontSize: '14px',
  },
};

export default App;

