/**
 * Axios HTTP client with retry logic, circuit breaker, and authentication.
 * Migrated from .js to .ts; uses Vite env and in-memory token.
 */
import axios, { type AxiosRequestConfig, type InternalAxiosRequestConfig } from 'axios';
import { authConfig, getAccessToken, isTokenExpired, clearAccessToken } from '@/config/auth';

// Extend config with metadata
declare module 'axios' {
  interface InternalAxiosRequestConfig {
    metadata?: { startTime: number };
    __retryCount?: number;
  }
}

// ── Circuit breaker ────────────────────────────────────────────────
const CIRCUIT_BREAKER_CONFIG = {
  threshold: 5,
  timeout: 60_000,
};

type CircuitState = 'CLOSED' | 'OPEN' | 'HALF_OPEN';

interface CircuitEntry {
  count: number;
  lastFailure: number;
  state: CircuitState;
}

const circuits = new Map<string, CircuitEntry>();

function getCircuitState(endpoint: string): CircuitState {
  const entry = circuits.get(endpoint);
  if (!entry) return 'CLOSED';

  if (entry.state === 'OPEN' && Date.now() - entry.lastFailure >= CIRCUIT_BREAKER_CONFIG.timeout) {
    entry.state = 'HALF_OPEN';
    return 'HALF_OPEN';
  }
  return entry.state;
}

function recordFailure(endpoint: string) {
  const entry = circuits.get(endpoint) ?? { count: 0, lastFailure: 0, state: 'CLOSED' as CircuitState };
  entry.count++;
  entry.lastFailure = Date.now();
  if (entry.count >= CIRCUIT_BREAKER_CONFIG.threshold) {
    entry.state = 'OPEN';
  }
  circuits.set(endpoint, entry);
}

function resetCircuit(endpoint: string) {
  circuits.delete(endpoint);
}

// ── Retry config ───────────────────────────────────────────────────
const RETRY_CONFIG = {
  maxRetries: 3,
  retryDelay: (attempt: number) => Math.pow(2, attempt) * 1000,
  retryableStatuses: [408, 429, 500, 502, 503, 504],
};

// ── Axios instance ─────────────────────────────────────────────────
const apiClient = axios.create({
  baseURL: authConfig.apiEndpoint,
  timeout: 30_000,
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor
apiClient.interceptors.request.use((config) => {
  const endpoint = config.url || '';

  if (getCircuitState(endpoint) === 'OPEN') {
    return Promise.reject(Object.assign(new Error(`Circuit breaker open for ${endpoint}`), { code: 'CIRCUIT_BREAKER_OPEN' }));
  }

  const token = getAccessToken();
  if (token && !isTokenExpired(token)) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  config.metadata = { startTime: Date.now() };
  return config;
});

// Response interceptor — retry + circuit breaker + 401 handling
apiClient.interceptors.response.use(
  (response) => {
    resetCircuit(response.config.url || '');
    const start = response.config.metadata?.startTime;
    if (start && Date.now() - start > 3000) {
      console.warn(`Slow response from ${response.config.url}: ${Date.now() - start}ms`);
    }
    return response;
  },
  async (error) => {
    const config = error.config as InternalAxiosRequestConfig | undefined;
    if (!config) return Promise.reject(error);

    if (error.code === 'CIRCUIT_BREAKER_OPEN') {
      return Promise.reject(error);
    }

    if (error.response?.status >= 500) {
      recordFailure(config.url || '');
    }

    // 401 — clear token, redirect to auth
    if (error.response?.status === 401) {
      clearAccessToken();
      if (window.location.pathname !== '/auth') {
        window.location.href = '/auth';
      }
      return Promise.reject(error);
    }

    // Retry with exponential backoff
    const retryCount = config.__retryCount ?? 0;
    if (
      RETRY_CONFIG.retryableStatuses.includes(error.response?.status) &&
      retryCount < RETRY_CONFIG.maxRetries
    ) {
      config.__retryCount = retryCount + 1;
      const delay = RETRY_CONFIG.retryDelay(retryCount);
      await new Promise((r) => setTimeout(r, delay));
      return apiClient(config);
    }

    return Promise.reject(error);
  }
);

export default apiClient;
