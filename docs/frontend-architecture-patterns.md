# Frontend Architecture Patterns - Advanced Patterns

**Version:** 1.0  
**Last Updated:** 2025-10-11  
**Owner:** Frontend Architecture Team  
**Status:** Design Specification

---

## Table of Contents

1. [Overview](#overview)
2. [Micro-Frontend Architecture](#micro-frontend-architecture)
3. [Component Composition Strategies](#component-composition-strategies)
4. [Advanced State Management](#advanced-state-management)
5. [Performance Optimization Patterns](#performance-optimization-patterns)
6. [Code Splitting & Lazy Loading](#code-splitting--lazy-loading)
7. [Testing Strategies](#testing-strategies)
8. [Build & Deployment](#build--deployment)

---

## Overview

### Why Advanced Patterns for APFA Admin Dashboard?

The APFA admin dashboard has unique requirements:

| Requirement | Challenge | Pattern Needed |
|------------|-----------|----------------|
| **Multiple dashboards** | CeleryJobMonitor, BatchStatus, IndexMgmt, QueueMonitor, WorkerDashboard | Micro-frontends |
| **Real-time updates** | 1000+ concurrent tasks, WebSocket streams | Optimistic UI, Virtual scrolling |
| **Complex state** | Task state, worker state, queue state, cache | Normalized Redux, Entity adapters |
| **Large datasets** | 10K+ tasks, 100+ workers | Virtualization, Pagination |
| **Team scaling** | Multiple teams (Celery, FAISS, Monitoring) | Module federation |

**Decision:** Implement **modular monolith** (single SPA) with **micro-frontend patterns** for future extraction.

---

## Micro-Frontend Architecture

### Architecture Decision: Module Federation

**Pattern:** Webpack 5 Module Federation for runtime integration

**Why Module Federation over alternatives:**

| Approach | Pros | Cons | Verdict |
|----------|------|------|---------|
| **Monolith SPA** | Simple, shared state | Hard to scale teams | ❌ Current pain point |
| **iFrame composition** | Full isolation | No shared state, poor UX | ❌ Rejected |
| **Web Components** | Standard, reusable | Limited framework support | ⚠️ Future |
| **Module Federation** | Runtime integration, shared deps | Webpack 5 required | ✅ **Selected** |

### Module Federation Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Shell Application (Host)                      │
│  ┌────────────────────────────────────────────────────────┐     │
│  │  App.tsx (Main Router)                                 │     │
│  │  ├─ Layout (Header, Sidebar, Footer)                   │     │
│  │  ├─ Authentication (JWT)                               │     │
│  │  └─ Global State (Redux Store)                         │     │
│  └────────────────────────────────────────────────────────┘     │
│                           │                                      │
│         ┌─────────────────┼─────────────────┬──────────────┐    │
│         │                 │                 │              │    │
│  ┌──────▼──────┐   ┌──────▼──────┐   ┌─────▼─────┐  ┌────▼───┐│
│  │ Celery      │   │ Index       │   │ Queue     │  │Worker  ││
│  │ Module      │   │ Module      │   │ Module    │  │Module  ││
│  │ (Remote)    │   │ (Remote)    │   │ (Remote)  │  │(Remote)││
│  │             │   │             │   │           │  │        ││
│  │ • JobMonitor│   │ • Management│   │ • Monitor │  │• Health││
│  │ • BatchStat │   │ • Migration │   │ • Depth   │  │• Stats ││
│  └─────────────┘   └─────────────┘   └───────────┘  └────────┘│
└─────────────────────────────────────────────────────────────────┘

Shared Dependencies (Singleton):
├─ React 18.2
├─ Redux Toolkit 1.9
├─ Material-UI 5.14
└─ Socket.IO Client 4.5
```

### Implementation: webpack.config.js (Host)

```javascript
// frontend/webpack.config.js
const ModuleFederationPlugin = require('webpack/lib/container/ModuleFederationPlugin');
const { dependencies } = require('./package.json');

module.exports = {
  // ... other config
  
  plugins: [
    new ModuleFederationPlugin({
      name: 'host',
      filename: 'remoteEntry.js',
      
      // Expose nothing (host only consumes)
      exposes: {},
      
      // Consume remote modules
      remotes: {
        celeryModule: 'celeryModule@http://localhost:3001/remoteEntry.js',
        indexModule: 'indexModule@http://localhost:3002/remoteEntry.js',
        queueModule: 'queueModule@http://localhost:3003/remoteEntry.js',
        workerModule: 'workerModule@http://localhost:3004/remoteEntry.js',
      },
      
      // Share dependencies (singletons)
      shared: {
        react: {
          singleton: true,
          requiredVersion: dependencies.react,
          eager: true,
        },
        'react-dom': {
          singleton: true,
          requiredVersion: dependencies['react-dom'],
          eager: true,
        },
        '@reduxjs/toolkit': {
          singleton: true,
          requiredVersion: dependencies['@reduxjs/toolkit'],
        },
        '@mui/material': {
          singleton: true,
          requiredVersion: dependencies['@mui/material'],
        },
        'socket.io-client': {
          singleton: true,
          requiredVersion: dependencies['socket.io-client'],
        },
      },
    }),
  ],
};
```

### Implementation: webpack.config.js (Remote - Celery Module)

```javascript
// frontend-celery-module/webpack.config.js
const ModuleFederationPlugin = require('webpack/lib/container/ModuleFederationPlugin');

module.exports = {
  // ... other config
  
  plugins: [
    new ModuleFederationPlugin({
      name: 'celeryModule',
      filename: 'remoteEntry.js',
      
      // Expose components
      exposes: {
        './CeleryJobMonitor': './src/components/CeleryJobMonitor',
        './BatchProcessingStatus': './src/components/BatchProcessingStatus',
      },
      
      // Share dependencies with host
      shared: {
        react: { singleton: true },
        'react-dom': { singleton: true },
        '@reduxjs/toolkit': { singleton: true },
        '@mui/material': { singleton: true },
      },
    }),
  ],
  
  devServer: {
    port: 3001,
    headers: {
      'Access-Control-Allow-Origin': '*',
    },
  },
};
```

### Usage in Host Application

```typescript
// frontend/src/App.tsx
import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { CircularProgress } from '@mui/material';

// Lazy load remote modules
const CeleryJobMonitor = lazy(() => import('celeryModule/CeleryJobMonitor'));
const BatchProcessingStatus = lazy(() => import('celeryModule/BatchProcessingStatus'));
const IndexManagement = lazy(() => import('indexModule/IndexManagement'));
const QueueMonitor = lazy(() => import('queueModule/QueueMonitor'));
const WorkerDashboard = lazy(() => import('workerModule/WorkerDashboard'));

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/admin" element={<AdminLayout />}>
          <Route
            path="celery/tasks"
            element={
              <Suspense fallback={<CircularProgress />}>
                <CeleryJobMonitor />
              </Suspense>
            }
          />
          <Route
            path="celery/batches"
            element={
              <Suspense fallback={<CircularProgress />}>
                <BatchProcessingStatus />
              </Suspense>
            }
          />
          <Route
            path="index"
            element={
              <Suspense fallback={<CircularProgress />}>
                <IndexManagement />
              </Suspense>
            }
          />
          <Route
            path="queues"
            element={
              <Suspense fallback={<CircularProgress />}>
                <QueueMonitor />
              </Suspense>
            }
          />
          <Route
            path="workers"
            element={
              <Suspense fallback={<CircularProgress />}>
                <WorkerDashboard />
              </Suspense>
            }
          />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
```

---

## Component Composition Strategies

### Pattern 1: Compound Components

**Use Case:** CeleryJobMonitor with flexible filtering

```typescript
// src/components/admin/CeleryJobMonitor/CeleryJobMonitor.tsx
import React, { createContext, useContext } from 'react';

// Context for compound components
const CeleryJobMonitorContext = createContext(null);

// Main component
export const CeleryJobMonitor = ({ children, ...props }) => {
  const [filters, setFilters] = useState({});
  const [tasks, setTasks] = useState([]);
  
  const value = {
    filters,
    setFilters,
    tasks,
    setTasks,
  };
  
  return (
    <CeleryJobMonitorContext.Provider value={value}>
      <Card>
        {children}
      </Card>
    </CeleryJobMonitorContext.Provider>
  );
};

// Sub-components
CeleryJobMonitor.Header = function Header({ children }) {
  return <CardHeader>{children}</CardHeader>;
};

CeleryJobMonitor.Filters = function Filters() {
  const { filters, setFilters } = useContext(CeleryJobMonitorContext);
  
  return (
    <Box display="flex" gap={2}>
      <QueueFilter value={filters.queue} onChange={(q) => setFilters({ ...filters, queue: q })} />
      <StateFilter value={filters.state} onChange={(s) => setFilters({ ...filters, state: s })} />
    </Box>
  );
};

CeleryJobMonitor.TaskList = function TaskList() {
  const { tasks, filters } = useContext(CeleryJobMonitorContext);
  const filteredTasks = applyFilters(tasks, filters);
  
  return <AgGridReact rowData={filteredTasks} />;
};

CeleryJobMonitor.Actions = function Actions() {
  const { tasks } = useContext(CeleryJobMonitorContext);
  
  return (
    <Box>
      <Button onClick={handleRevoke}>Revoke Selected</Button>
      <Button onClick={handleRefresh}>Refresh</Button>
    </Box>
  );
};
```

**Usage (Flexible Composition):**

```typescript
// Option 1: Full-featured
<CeleryJobMonitor>
  <CeleryJobMonitor.Header>
    <CeleryJobMonitor.Filters />
  </CeleryJobMonitor.Header>
  <CeleryJobMonitor.TaskList />
  <CeleryJobMonitor.Actions />
</CeleryJobMonitor>

// Option 2: Minimal (no filters)
<CeleryJobMonitor>
  <CeleryJobMonitor.TaskList />
</CeleryJobMonitor>

// Option 3: Custom layout
<CeleryJobMonitor>
  <Grid container>
    <Grid item xs={8}>
      <CeleryJobMonitor.TaskList />
    </Grid>
    <Grid item xs={4}>
      <CeleryJobMonitor.Filters />
      <CeleryJobMonitor.Actions />
    </Grid>
  </Grid>
</CeleryJobMonitor>
```

---

### Pattern 2: Render Props

**Use Case:** BatchProcessingStatus with customizable rendering

```typescript
// src/components/admin/BatchProcessingStatus/BatchProcessingStatus.tsx
interface BatchProcessingStatusProps {
  jobId?: string;
  renderProgress?: (progress: number, job: BatchJob) => React.ReactNode;
  renderStats?: (stats: JobStats) => React.ReactNode;
  renderErrors?: (errors: string[]) => React.ReactNode;
}

export const BatchProcessingStatus: React.FC<BatchProcessingStatusProps> = ({
  jobId,
  renderProgress,
  renderStats,
  renderErrors,
}) => {
  const { job, loading } = useBatchJob(jobId);
  
  if (loading) return <CircularProgress />;
  if (!job) return <Alert severity="warning">No job found</Alert>;
  
  const progress = (job.completedBatches / job.totalBatches) * 100;
  
  return (
    <Card>
      <CardContent>
        {/* Default or custom progress rendering */}
        {renderProgress ? (
          renderProgress(progress, job)
        ) : (
          <DefaultProgressBar progress={progress} />
        )}
        
        {/* Default or custom stats rendering */}
        {renderStats ? (
          renderStats({
            completed: job.completedBatches,
            failed: job.failedBatches,
            throughput: job.throughput,
          })
        ) : (
          <DefaultStatsGrid stats={job} />
        )}
        
        {/* Default or custom error rendering */}
        {job.errors && job.errors.length > 0 && (
          renderErrors ? (
            renderErrors(job.errors)
          ) : (
            <DefaultErrorList errors={job.errors} />
          )
        )}
      </CardContent>
    </Card>
  );
};
```

**Usage (Custom Rendering):**

```typescript
<BatchProcessingStatus
  jobId="embed_job_123"
  renderProgress={(progress, job) => (
    <Box>
      <Typography variant="h4">{progress.toFixed(1)}%</Typography>
      <LinearProgress variant="determinate" value={progress} />
      <Typography variant="caption">
        {job.completedBatches} / {job.totalBatches} batches
      </Typography>
    </Box>
  )}
  renderStats={(stats) => (
    <Grid container spacing={2}>
      <Grid item xs={4}>
        <Metric label="Completed" value={stats.completed} color="success" />
      </Grid>
      <Grid item xs={4}>
        <Metric label="Failed" value={stats.failed} color="error" />
      </Grid>
      <Grid item xs={4}>
        <Metric label="Throughput" value={`${stats.throughput} docs/s`} />
      </Grid>
    </Grid>
  )}
/>
```

---

### Pattern 3: Higher-Order Components (HOC)

**Use Case:** Add real-time updates to any component

```typescript
// src/hocs/withRealTimeUpdates.tsx
import React, { ComponentType } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';

export interface WithRealTimeUpdatesProps {
  realtimeData?: any;
  connected?: boolean;
}

export function withRealTimeUpdates<P extends object>(
  WrappedComponent: ComponentType<P & WithRealTimeUpdatesProps>,
  config: {
    endpoint: string;
    room?: string;
    dataTransform?: (message: any) => any;
  }
) {
  return function WithRealTimeUpdatesWrapper(props: P) {
    const { connected, messages } = useWebSocket(config.endpoint, {
      room: config.room,
    });
    
    // Transform latest message
    const realtimeData = messages.length > 0
      ? config.dataTransform?.(messages[messages.length - 1]) || messages[messages.length - 1]
      : null;
    
    return (
      <WrappedComponent
        {...props}
        realtimeData={realtimeData}
        connected={connected}
      />
    );
  };
}
```

**Usage:**

```typescript
// Original component
const TaskListBase: React.FC<TaskListProps & WithRealTimeUpdatesProps> = ({
  realtimeData,
  connected,
  ...props
}) => {
  const [tasks, setTasks] = useState([]);
  
  // Update tasks when real-time data arrives
  useEffect(() => {
    if (realtimeData && realtimeData.type === 'task_update') {
      setTasks(prev => updateTaskInArray(prev, realtimeData.data));
    }
  }, [realtimeData]);
  
  return (
    <div>
      {connected && <Chip label="Live" color="success" />}
      <TaskTable tasks={tasks} />
    </div>
  );
};

// Enhanced with real-time updates
export const TaskList = withRealTimeUpdates(TaskListBase, {
  endpoint: '/ws/celery/tasks',
  room: 'celery:tasks',
  dataTransform: (msg) => msg.data,
});
```

---

### Pattern 4: Container/Presenter Pattern

**Use Case:** Separate business logic from presentation

```typescript
// Container (Business Logic)
// src/containers/CeleryJobMonitorContainer.tsx
import React from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useCeleryTasks } from '../hooks/useCeleryTasks';
import { CeleryJobMonitorPresenter } from '../components/CeleryJobMonitorPresenter';
import { revokeTask, fetchCeleryTasks } from '../store/slices/celerySlice';

export const CeleryJobMonitorContainer: React.FC = () => {
  const dispatch = useDispatch();
  const { tasks, connected, mode } = useCeleryTasks();
  const { filters } = useSelector((state: RootState) => state.celery);
  
  // Business logic
  const handleRevoke = async (taskId: string) => {
    if (window.confirm('Revoke this task?')) {
      await dispatch(revokeTask(taskId));
    }
  };
  
  const handleRefresh = () => {
    dispatch(fetchCeleryTasks());
  };
  
  const handleFilterChange = (newFilters: any) => {
    dispatch(updateFilters(newFilters));
  };
  
  // Filter tasks
  const filteredTasks = tasks.filter(task => {
    if (filters.queue && task.queue !== filters.queue) return false;
    if (filters.state && task.state !== filters.state) return false;
    return true;
  });
  
  // Pass everything to presenter
  return (
    <CeleryJobMonitorPresenter
      tasks={filteredTasks}
      connected={connected}
      mode={mode}
      filters={filters}
      onRevoke={handleRevoke}
      onRefresh={handleRefresh}
      onFilterChange={handleFilterChange}
    />
  );
};
```

```typescript
// Presenter (Pure UI)
// src/components/CeleryJobMonitorPresenter.tsx
import React from 'react';
import { Card, CardHeader, CardContent } from '@mui/material';
import { AgGridReact } from 'ag-grid-react';

export interface CeleryJobMonitorPresenterProps {
  tasks: CeleryTask[];
  connected: boolean;
  mode: 'websocket' | 'polling';
  filters: any;
  onRevoke: (taskId: string) => void;
  onRefresh: () => void;
  onFilterChange: (filters: any) => void;
}

export const CeleryJobMonitorPresenter: React.FC<CeleryJobMonitorPresenterProps> = ({
  tasks,
  connected,
  mode,
  filters,
  onRevoke,
  onRefresh,
  onFilterChange,
}) => {
  // Pure presentation logic (no API calls, no state management)
  return (
    <Card>
      <CardHeader
        title="Celery Task Monitor"
        subheader={
          <ConnectionIndicator connected={connected} mode={mode} />
        }
        action={
          <RefreshButton onClick={onRefresh} />
        }
      />
      <CardContent>
        <FilterControls filters={filters} onChange={onFilterChange} />
        <TaskGrid tasks={tasks} onRevoke={onRevoke} />
      </CardContent>
    </Card>
  );
};
```

**Benefits:**
- ✅ Easy to test (presenter is pure UI, no dependencies)
- ✅ Reusable (presenter can be used with different data sources)
- ✅ Maintainable (separation of concerns)

---

## Advanced State Management

### Pattern 1: Normalized Redux State

**Problem:** Tasks, jobs, workers have relationships. Nested state is hard to update.

**Solution:** Normalize with Entity Adapters

```typescript
// src/store/slices/celerySlice.ts
import { createSlice, createEntityAdapter, PayloadAction } from '@reduxjs/toolkit';
import type { CeleryTask, BatchJob, CeleryWorker } from '../../types/celery.types';

// Entity adapters for normalized state
const tasksAdapter = createEntityAdapter<CeleryTask>({
  selectId: (task) => task.id,
  sortComparer: (a, b) => b.timestamp.localeCompare(a.timestamp), // Most recent first
});

const jobsAdapter = createEntityAdapter<BatchJob>({
  selectId: (job) => job.jobId,
});

const workersAdapter = createEntityAdapter<CeleryWorker>({
  selectId: (worker) => worker.name,
});

// Normalized state structure
interface CeleryState {
  tasks: ReturnType<typeof tasksAdapter.getInitialState>;
  jobs: ReturnType<typeof jobsAdapter.getInitialState>;
  workers: ReturnType<typeof workersAdapter.getInitialState>;
  filters: {
    queue?: string;
    state?: string;
    worker?: string;
  };
  ui: {
    loading: boolean;
    error: string | null;
  };
}

const initialState: CeleryState = {
  tasks: tasksAdapter.getInitialState(),
  jobs: jobsAdapter.getInitialState(),
  workers: workersAdapter.getInitialState(),
  filters: {},
  ui: {
    loading: false,
    error: null,
  },
};

const celerySlice = createSlice({
  name: 'celery',
  initialState,
  reducers: {
    // Tasks
    taskAdded: (state, action: PayloadAction<CeleryTask>) => {
      tasksAdapter.addOne(state.tasks, action.payload);
    },
    taskUpdated: (state, action: PayloadAction<CeleryTask>) => {
      tasksAdapter.upsertOne(state.tasks, action.payload);
    },
    taskRemoved: (state, action: PayloadAction<string>) => {
      tasksAdapter.removeOne(state.tasks, action.payload);
    },
    tasksReceived: (state, action: PayloadAction<CeleryTask[]>) => {
      tasksAdapter.setAll(state.tasks, action.payload);
    },
    
    // Jobs
    jobUpdated: (state, action: PayloadAction<BatchJob>) => {
      jobsAdapter.upsertOne(state.jobs, action.payload);
    },
    
    // Workers
    workersReceived: (state, action: PayloadAction<CeleryWorker[]>) => {
      workersAdapter.setAll(state.workers, action.payload);
    },
    
    // Filters
    filtersUpdated: (state, action: PayloadAction<any>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
  },
});

// Selectors (Memoized with reselect)
export const {
  selectAll: selectAllTasks,
  selectById: selectTaskById,
  selectIds: selectTaskIds,
} = tasksAdapter.getSelectors((state: RootState) => state.celery.tasks);

export const selectFilteredTasks = createSelector(
  [selectAllTasks, (state: RootState) => state.celery.filters],
  (tasks, filters) => {
    return tasks.filter(task => {
      if (filters.queue && task.queue !== filters.queue) return false;
      if (filters.state && task.state !== filters.state) return false;
      if (filters.worker && task.worker !== filters.worker) return false;
      return true;
    });
  }
);

export const selectTasksByQueue = createSelector(
  [selectAllTasks, (state: RootState, queue: string) => queue],
  (tasks, queue) => tasks.filter(task => task.queue === queue)
);
```

**Benefits:**
- ✅ **O(1) lookups:** `selectTaskById` is instant (hash map)
- ✅ **Efficient updates:** Update one task without copying entire array
- ✅ **Memoized selectors:** Re-compute only when dependencies change
- ✅ **Normalized structure:** No nested data, easier to update

---

### Pattern 2: Redux Toolkit Query (RTK Query)

**Use Case:** Cache API responses with automatic invalidation

```typescript
// src/store/api/celeryApi.ts
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type { CeleryTask, BatchJob } from '../../types/celery.types';

export const celeryApi = createApi({
  reducerPath: 'celeryApi',
  baseQuery: fetchBaseQuery({
    baseUrl: process.env.REACT_APP_API_URL,
    prepareHeaders: (headers) => {
      const token = localStorage.getItem('authToken');
      if (token) {
        headers.set('Authorization', `Bearer ${token}`);
      }
      return headers;
    },
  }),
  
  tagTypes: ['Task', 'Job', 'Worker', 'Queue'],
  
  endpoints: (builder) => ({
    // Queries (GET)
    getTasks: builder.query<CeleryTask[], { queue?: string; state?: string }>({
      query: (params) => ({
        url: '/api/admin/celery/tasks',
        params,
      }),
      providesTags: (result) =>
        result
          ? [...result.map(({ id }) => ({ type: 'Task' as const, id })), 'Task']
          : ['Task'],
      // Polling: Refetch every 5 seconds
      pollingInterval: 5000,
    }),
    
    getJob: builder.query<BatchJob, string>({
      query: (jobId) => `/api/admin/celery/jobs/${jobId}`,
      providesTags: (result, error, jobId) => [{ type: 'Job', id: jobId }],
    }),
    
    getWorkers: builder.query<CeleryWorker[], void>({
      query: () => '/api/admin/celery/workers',
      providesTags: ['Worker'],
      pollingInterval: 10000, // Poll every 10 seconds
    }),
    
    // Mutations (POST/DELETE)
    revokeTask: builder.mutation<void, string>({
      query: (taskId) => ({
        url: `/api/admin/celery/tasks/${taskId}/revoke`,
        method: 'POST',
      }),
      // Invalidate task cache to refetch
      invalidatesTags: (result, error, taskId) => [{ type: 'Task', id: taskId }],
    }),
    
    triggerEmbeddingJob: builder.mutation<{ job_id: string }, void>({
      query: () => ({
        url: '/api/admin/celery/jobs/embed-all',
        method: 'POST',
      }),
      // Invalidate jobs to show new job
      invalidatesTags: ['Job'],
    }),
    
    rebuildIndex: builder.mutation<void, void>({
      query: () => ({
        url: '/api/admin/index/rebuild',
        method: 'POST',
      }),
      invalidatesTags: ['Job'],
    }),
  }),
});

// Auto-generated hooks
export const {
  useGetTasksQuery,
  useGetJobQuery,
  useGetWorkersQuery,
  useRevokeTaskMutation,
  useTriggerEmbeddingJobMutation,
  useRebuildIndexMutation,
} = celeryApi;
```

**Usage (Automatic Caching & Polling):**

```typescript
// Component automatically subscribes to polling
const CeleryJobMonitor: React.FC = () => {
  // RTK Query handles: fetching, caching, polling, error handling
  const { data: tasks, isLoading, error, refetch } = useGetTasksQuery(
    { queue: 'embedding' },
    {
      pollingInterval: 5000, // Poll every 5s
      refetchOnMountOrArgChange: true,
    }
  );
  
  const [revokeTask] = useRevokeTaskMutation();
  
  const handleRevoke = async (taskId: string) => {
    await revokeTask(taskId);
    // Cache automatically invalidated, refetches tasks
  };
  
  if (isLoading) return <CircularProgress />;
  if (error) return <Alert severity="error">{error}</Alert>;
  
  return <TaskGrid tasks={tasks} onRevoke={handleRevoke} />;
};
```

**Benefits:**
- ✅ **Automatic caching:** No manual cache management
- ✅ **Auto-polling:** Built-in with configurable interval
- ✅ **Optimistic updates:** UI updates before server confirms
- ✅ **Invalidation:** Auto-refetch when data changes
- ✅ **Loading states:** Automatic loading/error handling
- ✅ **De-duplication:** Multiple components share same request

---

### Pattern 3: Optimistic Updates

**Use Case:** Instant UI feedback before server confirmation

```typescript
// src/store/slices/celerySlice.ts (with optimistic updates)
const celerySlice = createSlice({
  name: 'celery',
  initialState,
  reducers: {
    // Optimistic revoke
    taskRevokedOptimistic: (state, action: PayloadAction<string>) => {
      const task = state.tasks.entities[action.payload];
      if (task) {
        task.state = 'REVOKED'; // Instant UI update
        task._optimistic = true; // Mark as optimistic
      }
    },
    
    // Confirmed revoke
    taskRevokedConfirmed: (state, action: PayloadAction<string>) => {
      const task = state.tasks.entities[action.payload];
      if (task) {
        delete task._optimistic; // Remove optimistic flag
      }
    },
    
    // Rollback if failed
    taskRevokeRolledBack: (state, action: PayloadAction<string>) => {
      const task = state.tasks.entities[action.payload];
      if (task) {
        task.state = 'STARTED'; // Revert to previous state
        delete task._optimistic;
      }
    },
  },
});

// Thunk with optimistic update
export const revokeTaskOptimistic = createAsyncThunk(
  'celery/revokeTaskOptimistic',
  async (taskId: string, { dispatch }) => {
    // 1. Optimistic update (instant UI)
    dispatch(taskRevokedOptimistic(taskId));
    
    try {
      // 2. Server request
      await celeryAPI.revokeTask(taskId);
      
      // 3. Confirm (server succeeded)
      dispatch(taskRevokedConfirmed(taskId));
    } catch (error) {
      // 4. Rollback (server failed)
      dispatch(taskRevokeRolledBack(taskId));
      throw error;
    }
  }
);
```

**Usage:**

```typescript
const handleRevoke = async (taskId: string) => {
  try {
    await dispatch(revokeTaskOptimistic(taskId));
    // UI already updated, just show success
    toast.success('Task revoked');
  } catch (error) {
    // UI already rolled back, just show error
    toast.error('Failed to revoke task');
  }
};
```

---

## Performance Optimization Patterns

### Pattern 1: Virtual Scrolling (Large Task Lists)

**Use Case:** Render 10,000+ tasks without lag

```typescript
// src/components/admin/CeleryJobMonitor/VirtualTaskList.tsx
import React from 'react';
import { FixedSizeList } from 'react-window';
import AutoSizer from 'react-virtualized-auto-sizer';

interface VirtualTaskListProps {
  tasks: CeleryTask[];
  onTaskClick?: (task: CeleryTask) => void;
}

const TaskRow: React.FC<{ index: number; style: any; data: any }> = ({
  index,
  style,
  data,
}) => {
  const { tasks, onTaskClick } = data;
  const task = tasks[index];
  
  return (
    <div style={style} onClick={() => onTaskClick?.(task)}>
      <Box display="flex" gap={2} p={1} borderBottom="1px solid #eee">
        <Chip label={task.state} size="small" />
        <Typography variant="body2">{task.name}</Typography>
        <Typography variant="caption" color="textSecondary">
          {task.worker}
        </Typography>
      </Box>
    </div>
  );
};

export const VirtualTaskList: React.FC<VirtualTaskListProps> = ({
  tasks,
  onTaskClick,
}) => {
  return (
    <AutoSizer>
      {({ height, width }) => (
        <FixedSizeList
          height={height}
          width={width}
          itemCount={tasks.length}
          itemSize={60}
          itemData={{ tasks, onTaskClick }}
        >
          {TaskRow}
        </FixedSizeList>
      )}
    </AutoSizer>
  );
};
```

**Performance:**
- **Before:** Render 10K rows = 10K DOM nodes = 5s render time, laggy scrolling
- **After:** Render 10-20 visible rows = 50ms render time, smooth 60fps scrolling

---

### Pattern 2: Memoization & useMemo

```typescript
// Expensive computation: Filter and sort 10K tasks
const CeleryJobMonitor: React.FC = () => {
  const tasks = useSelector(selectAllTasks); // 10,000 tasks
  const filters = useSelector(state => state.celery.filters);
  
  // WITHOUT memoization (BAD):
  // Recomputes on every render (even unrelated state changes)
  const filteredTasks = tasks
    .filter(task => matchesFilters(task, filters))
    .sort((a, b) => b.timestamp - a.timestamp);
  
  // WITH memoization (GOOD):
  // Only recomputes when tasks or filters change
  const filteredTasks = useMemo(() => {
    return tasks
      .filter(task => matchesFilters(task, filters))
      .sort((a, b) => b.timestamp - a.timestamp);
  }, [tasks, filters]);
  
  return <TaskGrid tasks={filteredTasks} />;
};
```

---

### Pattern 3: React.memo for Component Memoization

```typescript
// Prevent unnecessary re-renders of child components
import React, { memo } from 'react';

interface TaskRowProps {
  task: CeleryTask;
  onRevoke: (id: string) => void;
}

// Component only re-renders if task or onRevoke changes
export const TaskRow = memo<TaskRowProps>(({ task, onRevoke }) => {
  return (
    <TableRow>
      <TableCell>{task.name}</TableCell>
      <TableCell><Chip label={task.state} /></TableCell>
      <TableCell>
        <IconButton onClick={() => onRevoke(task.id)}>
          <StopIcon />
        </IconButton>
      </TableCell>
    </TableRow>
  );
}, (prevProps, nextProps) => {
  // Custom comparison: Only re-render if task state changed
  return (
    prevProps.task.id === nextProps.task.id &&
    prevProps.task.state === nextProps.task.state
  );
});
```

---

### Pattern 4: useCallback for Stable References

```typescript
// Prevent child re-renders due to function reference changes
const CeleryJobMonitor: React.FC = () => {
  const dispatch = useDispatch();
  
  // WITHOUT useCallback (BAD):
  // New function created every render → child re-renders
  const handleRevoke = (taskId: string) => {
    dispatch(revokeTask(taskId));
  };
  
  // WITH useCallback (GOOD):
  // Same function reference → child skips re-render
  const handleRevoke = useCallback((taskId: string) => {
    dispatch(revokeTask(taskId));
  }, [dispatch]);
  
  return <TaskGrid tasks={tasks} onRevoke={handleRevoke} />;
};
```

---

## Code Splitting & Lazy Loading

### Route-Based Code Splitting

```typescript
// src/App.tsx
import React, { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';

// Lazy load admin routes
const CeleryJobMonitor = lazy(() => import('./components/admin/CeleryJobMonitor'));
const BatchProcessingStatus = lazy(() => import('./components/admin/BatchProcessingStatus'));
const IndexManagement = lazy(() => import('./components/admin/IndexManagement'));
const QueueMonitor = lazy(() => import('./components/admin/QueueMonitor'));
const WorkerDashboard = lazy(() => import('./components/admin/WorkerDashboard'));

// Loading fallback
const AdminLoadingFallback = () => (
  <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
    <CircularProgress />
    <Typography variant="body1" ml={2}>Loading admin dashboard...</Typography>
  </Box>
);

function App() {
  return (
    <Routes>
      <Route path="/admin" element={<AdminLayout />}>
        <Route
          path="celery/tasks"
          element={
            <Suspense fallback={<AdminLoadingFallback />}>
              <CeleryJobMonitor />
            </Suspense>
          }
        />
        {/* Other routes */}
      </Route>
    </Routes>
  );
}
```

**Bundle Analysis:**
```bash
# Analyze bundle size
npm run build -- --stats

# Visualize with webpack-bundle-analyzer
npx webpack-bundle-analyzer build/stats.json
```

**Expected Bundles:**
- **main.js:** Core React + routing (~200 KB gzipped)
- **celery.chunk.js:** CeleryJobMonitor component (~50 KB)
- **index.chunk.js:** IndexManagement component (~30 KB)
- **vendors.chunk.js:** AG-Grid, Recharts (~150 KB)

**Load Time:**
- **Initial:** main.js only (~200 KB) = <1s on 3G
- **Admin route:** main.js + celery.chunk.js = <2s total
- **Other routes:** Loaded on-demand

---

### Component-Level Code Splitting

```typescript
// Lazy load heavy dependencies
const AGGrid = lazy(() => import('ag-grid-react').then(module => ({
  default: module.AgGridReact
})));

const Recharts = lazy(() => import('recharts').then(module => ({
  default: module.LineChart
})));

// Use in component
const CeleryJobMonitor: React.FC = () => {
  const [showChart, setShowChart] = useState(false);
  
  return (
    <Card>
      <CardContent>
        {/* Always loaded */}
        <Button onClick={() => setShowChart(true)}>Show Chart</Button>
        
        {/* Loaded only when needed */}
        {showChart && (
          <Suspense fallback={<CircularProgress />}>
            <Recharts data={chartData} />
          </Suspense>
        )}
      </CardContent>
    </Card>
  );
};
```

---

## Testing Strategies

### Pattern 1: Component Testing with React Testing Library

```typescript
// src/components/admin/CeleryJobMonitor/CeleryJobMonitor.test.tsx
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { CeleryJobMonitor } from './CeleryJobMonitor';
import celeryReducer from '../../../store/slices/celerySlice';

// Mock WebSocket
jest.mock('../../../hooks/useWebSocket', () => ({
  useWebSocket: () => ({
    connected: true,
    messages: [],
  }),
}));

describe('CeleryJobMonitor', () => {
  let store;
  
  beforeEach(() => {
    store = configureStore({
      reducer: { celery: celeryReducer },
      preloadedState: {
        celery: {
          tasks: {
            ids: ['task-1', 'task-2'],
            entities: {
              'task-1': { id: 'task-1', name: 'embed_batch', state: 'SUCCESS' },
              'task-2': { id: 'task-2', name: 'build_index', state: 'STARTED' },
            },
          },
        },
      },
    });
  });
  
  it('renders task list', async () => {
    render(
      <Provider store={store}>
        <CeleryJobMonitor />
      </Provider>
    );
    
    await waitFor(() => {
      expect(screen.getByText('embed_batch')).toBeInTheDocument();
      expect(screen.getByText('build_index')).toBeInTheDocument();
    });
  });
  
  it('filters tasks by queue', async () => {
    render(
      <Provider store={store}>
        <CeleryJobMonitor />
      </Provider>
    );
    
    const queueSelect = screen.getByLabelText('Queue');
    fireEvent.change(queueSelect, { target: { value: 'embedding' } });
    
    await waitFor(() => {
      // Only embedding tasks visible
      expect(screen.getByText('embed_batch')).toBeInTheDocument();
      expect(screen.queryByText('build_index')).not.toBeInTheDocument();
    });
  });
  
  it('revokes task on button click', async () => {
    const mockRevoke = jest.fn();
    
    render(
      <Provider store={store}>
        <CeleryJobMonitor onRevoke={mockRevoke} />
      </Provider>
    );
    
    const revokeButton = screen.getAllByRole('button', { name: /revoke/i })[0];
    fireEvent.click(revokeButton);
    
    await waitFor(() => {
      expect(mockRevoke).toHaveBeenCalledWith('task-1');
    });
  });
});
```

---

### Pattern 2: Integration Testing with Mock Service Worker

```typescript
// src/__tests__/integration/celery-admin.integration.test.tsx
import { setupServer } from 'msw/node';
import { rest } from 'msw';
import { render, screen, waitFor } from '@testing-library/react';
import { App } from '../App';

// Mock API server
const server = setupServer(
  rest.get('/api/admin/celery/tasks', (req, res, ctx) => {
    return res(
      ctx.json([
        { id: 'task-1', name: 'embed_batch', state: 'SUCCESS', queue: 'embedding' },
        { id: 'task-2', name: 'build_index', state: 'STARTED', queue: 'indexing' },
      ])
    );
  }),
  
  rest.post('/api/admin/celery/tasks/:taskId/revoke', (req, res, ctx) => {
    return res(ctx.json({ status: 'revoked', task_id: req.params.taskId }));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('Celery Admin Integration', () => {
  it('loads and displays tasks from API', async () => {
    render(<App />);
    
    // Navigate to admin
    fireEvent.click(screen.getByText('Admin'));
    fireEvent.click(screen.getByText('Celery Tasks'));
    
    await waitFor(() => {
      expect(screen.getByText('embed_batch')).toBeInTheDocument();
      expect(screen.getByText('build_index')).toBeInTheDocument();
    });
  });
  
  it('revokes task and updates UI', async () => {
    render(<App />);
    
    // Navigate and revoke
    // ... navigation code
    
    const revokeButton = screen.getAllByRole('button', { name: /revoke/i })[0];
    fireEvent.click(revokeButton);
    
    await waitFor(() => {
      expect(screen.getByText('REVOKED')).toBeInTheDocument();
    });
  });
});
```

---

## Build & Deployment

### Production Build Optimization

```javascript
// webpack.config.prod.js
const TerserPlugin = require('terser-webpack-plugin');
const CompressionPlugin = require('compression-webpack-plugin');
const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');

module.exports = {
  mode: 'production',
  
  optimization: {
    minimize: true,
    minimizer: [
      new TerserPlugin({
        terserOptions: {
          compress: {
            drop_console: true, // Remove console.log in production
          },
        },
      }),
    ],
    
    // Split vendor code
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        // React + core deps
        vendor: {
          test: /[\\/]node_modules[\\/](react|react-dom|react-router-dom)[\\/]/,
          name: 'vendor',
          priority: 10,
        },
        // Material-UI
        mui: {
          test: /[\\/]node_modules[\\/]@mui[\\/]/,
          name: 'mui',
          priority: 9,
        },
        // AG-Grid (large)
        aggrid: {
          test: /[\\/]node_modules[\\/]ag-grid-react[\\/]/,
          name: 'aggrid',
          priority: 8,
        },
        // Charts
        charts: {
          test: /[\\/]node_modules[\\/]recharts[\\/]/,
          name: 'charts',
          priority: 7,
        },
      },
    },
  },
  
  plugins: [
    // Gzip compression
    new CompressionPlugin({
      filename: '[path][base].gz',
      algorithm: 'gzip',
      test: /\.(js|css|html|svg)$/,
      threshold: 10240,
      minRatio: 0.8,
    }),
    
    // Bundle analysis
    new BundleAnalyzerPlugin({
      analyzerMode: 'static',
      openAnalyzer: false,
      reportFilename: 'bundle-report.html',
    }),
  ],
};
```

### CI/CD Pipeline

```yaml
# .github/workflows/frontend-deploy.yml
name: Deploy Frontend

on:
  push:
    branches: [main]
    paths:
      - 'frontend/**'

jobs:
  build-deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
        working-directory: frontend
      
      - name: Run tests
        run: npm test -- --coverage
        working-directory: frontend
      
      - name: Build
        run: npm run build
        working-directory: frontend
        env:
          REACT_APP_API_URL: ${{ secrets.API_URL }}
          REACT_APP_WS_URL: ${{ secrets.WS_URL }}
      
      - name: Deploy to S3
        run: |
          aws s3 sync frontend/build s3://apfa-admin-frontend/
          aws cloudfront create-invalidation --distribution-id ${{ secrets.CF_DIST_ID }} --paths "/*"
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

---

## References

- [Module Federation Documentation](https://webpack.js.org/concepts/module-federation/)
- [Redux Toolkit Entity Adapters](https://redux-toolkit.js.org/api/createEntityAdapter)
- [RTK Query Documentation](https://redux-toolkit.js.org/rtk-query/overview)
- [React Window (Virtualization)](https://react-window.vercel.app/)
- [Frontend Admin Dashboards](frontend-admin-dashboards.md)

---

**Document Status:** Complete - Ready for Implementation  
**Next Steps:** Begin frontend development following this architecture

