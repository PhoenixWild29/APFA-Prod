/**
 * Error handling utilities for API calls
 */

/**
 * Custom error classes
 */
export class APIError extends Error {
  constructor(message, status, endpoint, data = null) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.endpoint = endpoint;
    this.data = data;
  }
}

export class CircuitBreakerError extends Error {
  constructor(endpoint) {
    super(`Circuit breaker open for ${endpoint}`);
    this.name = 'CircuitBreakerError';
    this.endpoint = endpoint;
  }
}

export class NetworkError extends Error {
  constructor(message = 'Network error occurred') {
    super(message);
    this.name = 'NetworkError';
  }
}

export class TimeoutError extends Error {
  constructor(endpoint, timeout) {
    super(`Request to ${endpoint} timed out after ${timeout}ms`);
    this.name = 'TimeoutError';
    this.endpoint = endpoint;
    this.timeout = timeout;
  }
}

/**
 * Format error message for user-friendly display
 * @param {Error} error - Error object
 * @returns {string} Formatted error message
 */
export const formatErrorMessage = (error) => {
  // Circuit breaker error
  if (error.code === 'CIRCUIT_BREAKER_OPEN' || error.name === 'CircuitBreakerError') {
    return 'Service temporarily unavailable. Please try again in a moment.';
  }
  
  // Timeout error
  if (error.code === 'ECONNABORTED' || error.name === 'TimeoutError') {
    return 'Request timed out. Please check your connection and try again.';
  }
  
  // Network error
  if (!error.response && error.request) {
    return 'Network error. Please check your internet connection.';
  }
  
  // Server responded with error status
  if (error.response) {
    const status = error.response.status;
    const detail = error.response.data?.detail || error.message;
    
    switch (status) {
      case 400:
        return `Invalid request: ${detail}`;
      case 401:
        return 'Authentication required. Please log in.';
      case 403:
        return "You don't have permission to perform this action.";
      case 404:
        return 'Resource not found.';
      case 429:
        return 'Too many requests. Please slow down and try again.';
      case 500:
        return 'Internal server error. Our team has been notified.';
      case 502:
        return 'Service temporarily unavailable. Please try again.';
      case 503:
        return 'Service unavailable. Please try again later.';
      case 504:
        return 'Gateway timeout. Please try again.';
      default:
        return detail || `Error ${status}: Something went wrong.`;
    }
  }
  
  // Generic error
  return error.message || 'An unexpected error occurred. Please try again.';
};

/**
 * Get error severity level
 * @param {Error} error - Error object
 * @returns {string} Severity level: 'info', 'warning', 'error', 'critical'
 */
export const getErrorSeverity = (error) => {
  if (error.code === 'CIRCUIT_BREAKER_OPEN') return 'warning';
  if (error.code === 'ECONNABORTED') return 'warning';
  
  if (error.response) {
    const status = error.response.status;
    
    if (status >= 400 && status < 500) return 'warning'; // Client errors
    if (status >= 500) return 'error'; // Server errors
  }
  
  if (!error.response && error.request) return 'error'; // Network errors
  
  return 'error';
};

/**
 * Log error for monitoring
 * @param {Error} error - Error object
 * @param {Object} context - Additional context
 */
export const logError = (error, context = {}) => {
  const errorInfo = {
    name: error.name,
    message: error.message,
    status: error.response?.status,
    endpoint: error.config?.url || error.endpoint,
    method: error.config?.method,
    data: error.response?.data,
    stack: error.stack,
    severity: getErrorSeverity(error),
    timestamp: new Date().toISOString(),
    ...context,
  };
  
  // Console logging (development)
  if (process.env.NODE_ENV === 'development') {
    console.group(`🚨 ${errorInfo.severity.toUpperCase()}: ${error.name}`);
    console.error('Message:', error.message);
    if (errorInfo.endpoint) console.error('Endpoint:', errorInfo.endpoint);
    if (errorInfo.status) console.error('Status:', errorInfo.status);
    if (errorInfo.data) console.error('Response:', errorInfo.data);
    console.groupEnd();
  }
  
  // Send to monitoring service in production
  if (process.env.NODE_ENV === 'production' && window.Sentry) {
    window.Sentry.captureException(error, {
      extra: errorInfo,
      level: errorInfo.severity,
    });
  }
  
  // Could also send to custom logging endpoint
  if (process.env.REACT_APP_LOGGING_ENDPOINT) {
    fetch(process.env.REACT_APP_LOGGING_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(errorInfo),
    }).catch(() => {
      // Silently fail if logging endpoint is down
    });
  }
};

/**
 * Check if error is retryable
 * @param {Error} error - Error object
 * @returns {boolean} True if error should be retried
 */
export const isRetryableError = (error) => {
  // Network errors are retryable
  if (!error.response && error.request) return true;
  
  // Server errors (5xx) are retryable
  if (error.response?.status >= 500) return true;
  
  // Rate limit errors (429) are retryable after delay
  if (error.response?.status === 429) return true;
  
  // Timeout errors are retryable
  if (error.code === 'ECONNABORTED') return true;
  
  // Circuit breaker errors should not be retried immediately
  if (error.code === 'CIRCUIT_BREAKER_OPEN') return false;
  
  // Client errors (4xx) are not retryable
  return false;
};

/**
 * Extract validation errors from API response
 * @param {Error} error - Error object
 * @returns {Object} Validation errors by field
 */
export const extractValidationErrors = (error) => {
  if (error.response?.status !== 400 && error.response?.status !== 422) {
    return {};
  }
  
  const data = error.response.data;
  
  // FastAPI validation error format
  if (data?.detail && Array.isArray(data.detail)) {
    return data.detail.reduce((acc, err) => {
      const field = err.loc?.join('.') || 'general';
      acc[field] = err.msg;
      return acc;
    }, {});
  }
  
  // Generic validation error format
  if (typeof data?.detail === 'object') {
    return data.detail;
  }
  
  return { general: data?.detail || 'Validation error' };
};

