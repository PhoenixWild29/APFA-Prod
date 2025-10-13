/**
 * TanStack Query client configuration
 */
import { QueryClient } from '@tanstack/react-query';

/**
 * Default query configuration
 */
const defaultQueryConfig = {
  queries: {
    staleTime: 5 * 60 * 1000, // 5 minutes - data considered fresh
    cacheTime: 10 * 60 * 1000, // 10 minutes - cache retention
    refetchOnWindowFocus: true, // Refetch when user returns to tab
    refetchOnReconnect: true, // Refetch when connection restored
    refetchOnMount: true, // Refetch on component mount
    retry: 1, // Retry failed requests once (interceptor handles more)
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  },
  mutations: {
    retry: 1, // Retry failed mutations once
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  },
};

/**
 * Create and configure TanStack Query client
 */
export const queryClient = new QueryClient({
  defaultOptions: defaultQueryConfig,
});

/**
 * Query key factories for consistent key generation
 */
export const queryKeys = {
  // Health
  health: ['health'],
  
  // Authentication
  currentUser: ['auth', 'current-user'],
  
  // Advice
  advice: (query) => ['advice', query],
  adviceHistory: ['advice', 'history'],
  
  // Admin - Celery
  celeryTasks: (filters) => ['admin', 'celery', 'tasks', filters],
  celeryTask: (taskId) => ['admin', 'celery', 'task', taskId],
  celeryWorkers: ['admin', 'celery', 'workers'],
  celeryQueues: ['admin', 'celery', 'queues'],
  
  // Admin - Index
  indexCurrent: ['admin', 'index', 'current'],
  indexHistory: ['admin', 'index', 'history'],
  indexStats: ['admin', 'index', 'stats'],
  
  // Admin - Metrics
  metrics: ['admin', 'metrics'],
  metricsHistory: (timeRange) => ['admin', 'metrics', 'history', timeRange],
};

/**
 * Mutation key factories
 */
export const mutationKeys = {
  login: ['auth', 'login'],
  generateAdvice: ['advice', 'generate'],
  triggerEmbedding: ['admin', 'celery', 'embed'],
  buildIndex: ['admin', 'celery', 'build-index'],
  hotSwapIndex: ['admin', 'index', 'hot-swap'],
};

/**
 * Helper to invalidate related queries
 */
export const invalidateQueries = {
  allAdvice: () => queryClient.invalidateQueries({ queryKey: ['advice'] }),
  allCelery: () => queryClient.invalidateQueries({ queryKey: ['admin', 'celery'] }),
  allIndex: () => queryClient.invalidateQueries({ queryKey: ['admin', 'index'] }),
  allMetrics: () => queryClient.invalidateQueries({ queryKey: ['admin', 'metrics'] }),
};

export default queryClient;

