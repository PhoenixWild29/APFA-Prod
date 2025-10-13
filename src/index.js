/**
 * React application entry point
 */
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// Optional: Initialize Sentry for error monitoring in production
if (process.env.NODE_ENV === 'production' && process.env.REACT_APP_SENTRY_DSN) {
  import('@sentry/react').then((Sentry) => {
    Sentry.init({
      dsn: process.env.REACT_APP_SENTRY_DSN,
      environment: process.env.REACT_APP_ENV || 'production',
      tracesSampleRate: 0.1, // 10% of transactions
      integrations: [
        new Sentry.BrowserTracing(),
        new Sentry.Replay({
          maskAllText: true,
          blockAllMedia: true,
        }),
      ],
      replaysSessionSampleRate: 0.1,
      replaysOnErrorSampleRate: 1.0,
    });
  }).catch((err) => {
    console.warn('Failed to initialize Sentry:', err);
  });
}

// Create root and render app
const root = ReactDOM.createRoot(document.getElementById('root'));

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Optional: Performance measuring
if (process.env.NODE_ENV === 'development') {
  // Web Vitals reporting
  import('web-vitals').then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
    const reportWebVitals = (metric) => {
      console.log(metric);
    };
    
    getCLS(reportWebVitals);
    getFID(reportWebVitals);
    getFCP(reportWebVitals);
    getLCP(reportWebVitals);
    getTTFB(reportWebVitals);
  }).catch(() => {
    // Silently fail if web-vitals not installed
  });
}

