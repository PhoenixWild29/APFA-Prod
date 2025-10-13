/**
 * Performance monitoring utilities using Web Vitals
 */
import { onCLS, onFID, onFCP, onLCP, onTTFB, Metric } from 'web-vitals';

/**
 * Report Web Vitals metrics
 */
export const reportWebVitals = (onPerfEntry?: (metric: Metric) => void) => {
  if (onPerfEntry && onPerfEntry instanceof Function) {
    onCLS(onPerfEntry);
    onFID(onPerfEntry);
    onFCP(onPerfEntry);
    onLCP(onPerfEntry);
    onTTFB(onPerfEntry);
  }
};

/**
 * Log performance metrics to console (development only)
 */
export const logWebVitals = () => {
  if (import.meta.env.DEV) {
    reportWebVitals((metric) => {
      console.info(`[Web Vitals] ${metric.name}:`, {
        value: metric.value,
        rating: metric.rating,
        delta: metric.delta,
      });
    });
  }
};

/**
 * Send performance metrics to analytics endpoint
 */
export const sendToAnalytics = (metric: Metric) => {
  // Send to analytics service (e.g., Google Analytics, custom endpoint)
  const body = JSON.stringify({
    name: metric.name,
    value: metric.value,
    rating: metric.rating,
    delta: metric.delta,
    id: metric.id,
    navigationType: metric.navigationType,
  });

  // Use `navigator.sendBeacon()` if available, falling back to `fetch()`.
  if (navigator.sendBeacon) {
    navigator.sendBeacon('/api/analytics', body);
  } else {
    fetch('/api/analytics', { body, method: 'POST', keepalive: true }).catch(console.error);
  }
};

/**
 * Performance thresholds for monitoring
 */
export const PERFORMANCE_THRESHOLDS = {
  // Largest Contentful Paint (LCP)
  LCP: {
    good: 2500,
    needsImprovement: 4000,
  },
  // First Input Delay (FID)
  FID: {
    good: 100,
    needsImprovement: 300,
  },
  // Cumulative Layout Shift (CLS)
  CLS: {
    good: 0.1,
    needsImprovement: 0.25,
  },
  // First Contentful Paint (FCP)
  FCP: {
    good: 1800,
    needsImprovement: 3000,
  },
  // Time to First Byte (TTFB)
  TTFB: {
    good: 800,
    needsImprovement: 1800,
  },
};

/**
 * Get performance rating based on thresholds
 */
export const getPerformanceRating = (
  metricName: string,
  value: number
): 'good' | 'needs-improvement' | 'poor' => {
  const threshold = PERFORMANCE_THRESHOLDS[metricName as keyof typeof PERFORMANCE_THRESHOLDS];

  if (!threshold) return 'good';

  if (value <= threshold.good) return 'good';
  if (value <= threshold.needsImprovement) return 'needs-improvement';
  return 'poor';
};

/**
 * Initialize performance monitoring
 */
export const initPerformanceMonitoring = () => {
  // Log in development
  if (import.meta.env.DEV) {
    logWebVitals();
  }

  // Send to analytics in production
  if (import.meta.env.PROD) {
    reportWebVitals(sendToAnalytics);
  }
};

