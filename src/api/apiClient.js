/**
 * Axios HTTP client with retry logic, circuit breaker, and authentication
 */
import axios from 'axios';
import { authConfig, getAccessToken, isTokenExpired, clearAccessToken } from '../config/auth';

// Circuit breaker configuration
export const CIRCUIT_BREAKER_CONFIG = {
  threshold: 5, // Number of failures before opening circuit
  timeout: 60000, // Time to wait before attempting half-open (ms)
  resetTimeout: 10000, // Time in half-open state before reset (ms)
};

// Retry configuration
export const RETRY_CONFIG = {
  maxRetries: 3,
  retryDelay: (attemptIndex) => Math.pow(2, attemptIndex) * 1000, // 1s, 2s, 4s
  retryableStatuses: [408, 429, 500, 502, 503, 504],
};

// Circuit breaker state management
const circuitBreaker = {
  failures: new Map(), // Map<endpoint, {count, lastFailure, state}>
  states: {
    CLOSED: 'CLOSED',     // Normal operation
    OPEN: 'OPEN',         // Circuit is open, rejecting requests
    HALF_OPEN: 'HALF_OPEN', // Testing if service recovered
  },
};

/**
 * Get circuit state for endpoint
 * @param {string} endpoint - API endpoint
 * @returns {string} Circuit state
 */
const getCircuitState = (endpoint) => {
  const state = circuitBreaker.failures.get(endpoint);
  if (!state) return circuitBreaker.states.CLOSED;
  
  const { count, lastFailure, state: currentState } = state;
  const now = Date.now();
  
  if (currentState === circuitBreaker.states.OPEN) {
    // Check if timeout elapsed
    if (now - lastFailure >= CIRCUIT_BREAKER_CONFIG.timeout) {
      // Transition to half-open
      circuitBreaker.failures.set(endpoint, {
        ...state,
        state: circuitBreaker.states.HALF_OPEN,
      });
      return circuitBreaker.states.HALF_OPEN;
    }
    return circuitBreaker.states.OPEN;
  }
  
  return currentState || circuitBreaker.states.CLOSED;
};

/**
 * Check if circuit is open for endpoint
 * @param {string} endpoint - API endpoint
 * @returns {boolean} True if circuit is open
 */
const isCircuitOpen = (endpoint) => {
  const state = getCircuitState(endpoint);
  return state === circuitBreaker.states.OPEN;
};

/**
 * Record failure for circuit breaker
 * @param {string} endpoint - API endpoint
 */
const recordFailure = (endpoint) => {
  const state = circuitBreaker.failures.get(endpoint) || {
    count: 0,
    lastFailure: 0,
    state: circuitBreaker.states.CLOSED,
  };
  
  state.count++;
  state.lastFailure = Date.now();
  
  // Open circuit if threshold exceeded
  if (state.count >= CIRCUIT_BREAKER_CONFIG.threshold) {
    state.state = circuitBreaker.states.OPEN;
    console.warn(`Circuit breaker OPEN for ${endpoint} after ${state.count} failures`);
  }
  
  circuitBreaker.failures.set(endpoint, state);
};

/**
 * Reset circuit breaker on success
 * @param {string} endpoint - API endpoint
 */
const resetCircuit = (endpoint) => {
  const state = circuitBreaker.failures.get(endpoint);
  
  if (state?.state === circuitBreaker.states.HALF_OPEN) {
    console.info(`Circuit breaker CLOSED for ${endpoint} - service recovered`);
  }
  
  circuitBreaker.failures.delete(endpoint);
};

/**
 * Create Axios instance with base configuration
 */
const apiClient = axios.create({
  baseURL: authConfig.apiEndpoint,
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request interceptor - Add authentication and check circuit breaker
 */
apiClient.interceptors.request.use(
  (config) => {
    // Check circuit breaker
    const endpoint = config.url || '';
    if (isCircuitOpen(endpoint)) {
      const error = new Error(`Circuit breaker open for ${endpoint}`);
      error.code = 'CIRCUIT_BREAKER_OPEN';
      return Promise.reject(error);
    }
    
    // Add authentication token
    const token = getAccessToken();
    if (token && !isTokenExpired(token)) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Add request metadata for tracking
    config.metadata = {
      startTime: Date.now(),
    };
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Response interceptor - Handle errors, retry, and update circuit breaker
 */
apiClient.interceptors.response.use(
  (response) => {
    // Reset circuit breaker on success
    resetCircuit(response.config.url);
    
    // Log response time
    if (response.config.metadata?.startTime) {
      const duration = Date.now() - response.config.metadata.startTime;
      if (duration > 3000) {
        console.warn(`Slow response from ${response.config.url}: ${duration}ms`);
      }
    }
    
    return response;
  },
  async (error) => {
    const config = error.config;
    
    // Handle circuit breaker errors
    if (error.code === 'CIRCUIT_BREAKER_OPEN') {
      return Promise.reject(error);
    }
    
    // Record failure for circuit breaker (only for server errors)
    if (error.response?.status >= 500) {
      recordFailure(config.url);
    }
    
    // Handle 401 Unauthorized - Token expired
    if (error.response?.status === 401) {
      console.warn('Authentication failed - clearing token');
      clearAccessToken();
      
      // Redirect to login (if not already on login page)
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
      
      return Promise.reject(error);
    }
    
    // Retry logic with exponential backoff
    const shouldRetry = 
      config &&
      RETRY_CONFIG.retryableStatuses.includes(error.response?.status) &&
      (!config.__retryCount || config.__retryCount < RETRY_CONFIG.maxRetries);
    
    if (shouldRetry) {
      config.__retryCount = (config.__retryCount || 0) + 1;
      
      const delay = RETRY_CONFIG.retryDelay(config.__retryCount - 1);
      
      console.info(
        `Retrying request to ${config.url} (attempt ${config.__retryCount}/${RETRY_CONFIG.maxRetries}) after ${delay}ms`
      );
      
      // Wait before retry
      await new Promise((resolve) => setTimeout(resolve, delay));
      
      // Retry request
      return apiClient(config);
    }
    
    // No more retries
    if (config.__retryCount >= RETRY_CONFIG.maxRetries) {
      console.error(`Max retries (${RETRY_CONFIG.maxRetries}) exceeded for ${config.url}`);
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;

