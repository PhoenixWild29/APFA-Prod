/**
 * Custom React hooks for API calls with authentication
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from './apiClient';
import { queryKeys, mutationKeys } from './queryClient';
import { getAccessToken } from '../config/auth';
import { logError } from './errorHandling';

/**
 * Custom hook for GET requests
 * @param {string} endpoint - API endpoint
 * @param {object} options - Query options
 * @returns {object} React Query result
 */
export const useApi = (endpoint, options = {}) => {
  const token = getAccessToken();
  
  return useQuery({
    queryKey: options.queryKey || [endpoint, options.params],
    queryFn: async () => {
      const response = await apiClient.get(endpoint, {
        params: options.params,
      });
      return response.data;
    },
    enabled: !!token && options.enabled !== false,
    onError: (error) => {
      logError(error, { endpoint, type: 'query' });
      options.onError?.(error);
    },
    ...options,
  });
};

/**
 * Custom hook for POST/PUT/DELETE requests
 * @param {string} endpoint - API endpoint
 * @param {string} method - HTTP method (post, put, patch, delete)
 * @param {object} options - Mutation options
 * @returns {object} React Query mutation result
 */
export const useApiMutation = (endpoint, method = 'post', options = {}) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationKey: options.mutationKey,
    mutationFn: async (data) => {
      const response = await apiClient[method](endpoint, data);
      return response.data;
    },
    onSuccess: (data, variables, context) => {
      // Invalidate related queries
      if (options.invalidateQueries) {
        options.invalidateQueries.forEach((queryKey) => {
          queryClient.invalidateQueries({ queryKey });
        });
      }
      
      // Call custom onSuccess
      options.onSuccess?.(data, variables, context);
    },
    onError: (error, variables, context) => {
      logError(error, { endpoint, method, type: 'mutation' });
      
      // Call custom onError
      options.onError?.(error, variables, context);
    },
    ...options,
  });
};

// ============================================================================
// Authentication Hooks
// ============================================================================

/**
 * Login mutation hook
 * @returns {object} Mutation result
 */
export const useLogin = () => {
  return useApiMutation('/token', 'post', {
    mutationKey: mutationKeys.login,
    onSuccess: (data) => {
      // Token is handled by calling component
      console.log('Login successful');
    },
  });
};

/**
 * Get current user hook
 * @returns {object} Query result
 */
export const useCurrentUser = () => {
  return useApi('/me', {
    queryKey: queryKeys.currentUser,
    retry: false, // Don't retry if not authenticated
  });
};

// ============================================================================
// Advice Generation Hooks
// ============================================================================

/**
 * Generate advice mutation hook
 * @returns {object} Mutation result
 */
export const useGenerateAdvice = () => {
  return useApiMutation('/generate-advice', 'post', {
    mutationKey: mutationKeys.generateAdvice,
    invalidateQueries: [queryKeys.adviceHistory],
  });
};

/**
 * Get advice history hook
 * @param {object} filters - Filter parameters
 * @returns {object} Query result
 */
export const useAdviceHistory = (filters = {}) => {
  return useApi('/advice/history', {
    queryKey: [...queryKeys.adviceHistory, filters],
    params: filters,
  });
};

// ============================================================================
// Admin - Celery Hooks
// ============================================================================

/**
 * Get Celery tasks hook
 * @param {object} filters - Filter parameters
 * @returns {object} Query result
 */
export const useCeleryTasks = (filters = {}) => {
  return useApi('/admin/celery/tasks', {
    queryKey: queryKeys.celeryTasks(filters),
    params: filters,
    refetchInterval: 5000, // Refetch every 5 seconds
  });
};

/**
 * Get Celery task details hook
 * @param {string} taskId - Task ID
 * @returns {object} Query result
 */
export const useCeleryTask = (taskId) => {
  return useApi(`/admin/celery/tasks/${taskId}`, {
    queryKey: queryKeys.celeryTask(taskId),
    enabled: !!taskId,
    refetchInterval: 2000, // Refetch every 2 seconds for active tasks
  });
};

/**
 * Trigger embedding job mutation
 * @returns {object} Mutation result
 */
export const useTriggerEmbedding = () => {
  return useApiMutation('/admin/celery/jobs/embed-all', 'post', {
    mutationKey: mutationKeys.triggerEmbedding,
    invalidateQueries: [queryKeys.celeryTasks({})],
  });
};

/**
 * Build FAISS index mutation
 * @returns {object} Mutation result
 */
export const useBuildIndex = () => {
  return useApiMutation('/admin/celery/jobs/build-index', 'post', {
    mutationKey: mutationKeys.buildIndex,
    invalidateQueries: [queryKeys.celeryTasks({}), queryKeys.indexCurrent],
  });
};

// ============================================================================
// Admin - Index Hooks
// ============================================================================

/**
 * Get current index info hook
 * @returns {object} Query result
 */
export const useCurrentIndex = () => {
  return useApi('/admin/index/current', {
    queryKey: queryKeys.indexCurrent,
  });
};

/**
 * Get index history hook
 * @returns {object} Query result
 */
export const useIndexHistory = () => {
  return useApi('/admin/index/history', {
    queryKey: queryKeys.indexHistory,
  });
};

/**
 * Get index statistics hook
 * @returns {object} Query result
 */
export const useIndexStats = () => {
  return useApi('/admin/index/stats', {
    queryKey: queryKeys.indexStats,
    refetchInterval: 60000, // Refetch every minute
  });
};

/**
 * Hot-swap index mutation
 * @returns {object} Mutation result
 */
export const useHotSwapIndex = () => {
  return useApiMutation('/admin/index/hot-swap', 'post', {
    mutationKey: mutationKeys.hotSwapIndex,
    invalidateQueries: [queryKeys.indexCurrent, queryKeys.indexHistory],
  });
};

// ============================================================================
// Admin - Metrics Hooks
// ============================================================================

/**
 * Get system metrics hook
 * @returns {object} Query result
 */
export const useMetrics = () => {
  return useApi('/admin/metrics', {
    queryKey: queryKeys.metrics,
    refetchInterval: 10000, // Refetch every 10 seconds
  });
};

/**
 * Get metrics history hook
 * @param {string} timeRange - Time range (e.g., '1h', '24h', '7d')
 * @returns {object} Query result
 */
export const useMetricsHistory = (timeRange = '1h') => {
  return useApi('/admin/metrics/history', {
    queryKey: queryKeys.metricsHistory(timeRange),
    params: { range: timeRange },
  });
};

// ============================================================================
// Health Check Hook
// ============================================================================

/**
 * Health check hook
 * @returns {object} Query result
 */
export const useHealthCheck = () => {
  return useApi('/health', {
    queryKey: queryKeys.health,
    refetchInterval: 30000, // Refetch every 30 seconds
    retry: false, // Don't retry health checks
  });
};

