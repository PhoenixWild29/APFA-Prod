/**
 * Utilities for implementing optimistic updates with TanStack Query
 */
import { queryClient } from '../api/queryClient';

/**
 * Create optimistic mutation configuration
 * @param {string[]} queryKey - Query key to update
 * @param {Function} updateFn - Function to optimistically update cached data
 * @param {Function} mutationFn - Actual mutation function
 * @returns {object} Mutation configuration with optimistic updates
 */
export const createOptimisticMutation = (queryKey, updateFn, mutationFn) => {
  return {
    mutationFn,
    onMutate: async (newData) => {
      // Cancel outgoing refetches to avoid overwriting optimistic update
      await queryClient.cancelQueries({ queryKey });
      
      // Snapshot previous value for rollback
      const previousData = queryClient.getQueryData(queryKey);
      
      // Optimistically update cache
      queryClient.setQueryData(queryKey, (old) => {
        if (!old) return old;
        return updateFn(old, newData);
      });
      
      // Return context with snapshot for rollback
      return { previousData };
    },
    onError: (err, newData, context) => {
      // Rollback to previous data on error
      if (context?.previousData) {
        queryClient.setQueryData(queryKey, context.previousData);
      }
      
      console.error('Optimistic update failed, rolled back:', err);
    },
    onSettled: () => {
      // Always refetch after mutation to ensure cache is in sync
      queryClient.invalidateQueries({ queryKey });
    },
  };
};

/**
 * Optimistic update for adding item to list
 * @param {string[]} queryKey - Query key for list
 * @param {object} newItem - New item to add
 * @returns {object} Mutation configuration
 */
export const createOptimisticAdd = (queryKey, newItem) => {
  return createOptimisticMutation(
    queryKey,
    (oldList, item) => {
      // Add temporary ID and pending flag
      const optimisticItem = {
        ...item,
        id: `temp_${Date.now()}`,
        pending: true,
        createdAt: new Date().toISOString(),
      };
      
      // Prepend to list
      return [optimisticItem, ...(oldList || [])];
    },
    (data) => data // Mutation function provided by caller
  );
};

/**
 * Optimistic update for updating item in list
 * @param {string[]} queryKey - Query key for list
 * @param {string|number} itemId - ID of item to update
 * @param {object} updates - Updates to apply
 * @returns {object} Mutation configuration
 */
export const createOptimisticUpdate = (queryKey, itemId, updates) => {
  return createOptimisticMutation(
    queryKey,
    (oldList, updateData) => {
      if (!Array.isArray(oldList)) return oldList;
      
      return oldList.map((item) =>
        item.id === itemId
          ? { ...item, ...updateData, updatedAt: new Date().toISOString() }
          : item
      );
    },
    (data) => data // Mutation function provided by caller
  );
};

/**
 * Optimistic update for removing item from list
 * @param {string[]} queryKey - Query key for list
 * @param {string|number} itemId - ID of item to remove
 * @returns {object} Mutation configuration
 */
export const createOptimisticRemove = (queryKey, itemId) => {
  return createOptimisticMutation(
    queryKey,
    (oldList) => {
      if (!Array.isArray(oldList)) return oldList;
      
      return oldList.filter((item) => item.id !== itemId);
    },
    (data) => data // Mutation function provided by caller
  );
};

// ============================================================================
// Specific Optimistic Update Patterns
// ============================================================================

/**
 * Optimistic advice creation
 * Used when generating new financial advice
 */
export const optimisticAdviceCreation = (mutationFn) => {
  return createOptimisticMutation(
    ['advice', 'history'],
    (oldAdviceList, newAdviceQuery) => {
      const optimisticAdvice = {
        id: `temp_${Date.now()}`,
        query: newAdviceQuery.query,
        advice: 'Generating advice...', // Placeholder
        pending: true,
        createdAt: new Date().toISOString(),
        user: 'current_user', // Placeholder
      };
      
      return [optimisticAdvice, ...(oldAdviceList || [])];
    },
    mutationFn
  );
};

/**
 * Optimistic Celery task status update
 * Used when updating task status in admin UI
 */
export const optimisticTaskStatusUpdate = (taskId, mutationFn) => {
  return createOptimisticMutation(
    ['admin', 'celery', 'tasks', {}],
    (oldTasks, newStatus) => {
      if (!Array.isArray(oldTasks)) return oldTasks;
      
      return oldTasks.map((task) =>
        task.id === taskId
          ? { ...task, status: newStatus, updatedAt: new Date().toISOString() }
          : task
      );
    },
    mutationFn
  );
};

/**
 * Optimistic index hot-swap
 * Used when triggering FAISS index hot-swap
 */
export const optimisticIndexHotSwap = (newIndexVersion, mutationFn) => {
  return createOptimisticMutation(
    ['admin', 'index', 'current'],
    (oldIndex, newVersion) => {
      return {
        ...oldIndex,
        version: newVersion,
        status: 'swapping', // Temporary status
        updatedAt: new Date().toISOString(),
      };
    },
    mutationFn
  );
};

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Manually update query data (without mutation)
 * Useful for WebSocket updates or manual cache manipulation
 * @param {string[]} queryKey - Query key to update
 * @param {Function} updateFn - Function to update data
 */
export const manuallyUpdateQueryData = (queryKey, updateFn) => {
  queryClient.setQueryData(queryKey, (oldData) => {
    if (!oldData) return oldData;
    return updateFn(oldData);
  });
};

/**
 * Optimistically add item to sorted list
 * Maintains sort order by specified field
 * @param {string[]} queryKey - Query key for list
 * @param {object} newItem - New item to add
 * @param {string} sortField - Field to sort by (default: 'createdAt')
 * @param {string} sortOrder - Sort order: 'asc' or 'desc' (default: 'desc')
 */
export const optimisticAddToSortedList = (
  queryKey,
  newItem,
  sortField = 'createdAt',
  sortOrder = 'desc'
) => {
  return createOptimisticMutation(
    queryKey,
    (oldList, item) => {
      const optimisticItem = {
        ...item,
        id: `temp_${Date.now()}`,
        pending: true,
        [sortField]: new Date().toISOString(),
      };
      
      const newList = [...(oldList || []), optimisticItem];
      
      // Sort list
      newList.sort((a, b) => {
        const aVal = a[sortField];
        const bVal = b[sortField];
        
        if (sortOrder === 'asc') {
          return aVal > bVal ? 1 : -1;
        } else {
          return aVal < bVal ? 1 : -1;
        }
      });
      
      return newList;
    },
    (data) => data
  );
};

