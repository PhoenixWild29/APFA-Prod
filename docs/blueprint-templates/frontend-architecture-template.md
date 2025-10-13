# Frontend Architecture - Blueprint Template

**Section:** 14.0 Frontend Architecture  
**References:** APFA frontend-*.md docs

---

## 14.1 Overview

Frontend evolves from simple React SPA (Phase 1) to production admin dashboards with 
real-time updates (Phase 2) to micro-frontends with advanced patterns (Phase 3-5).

---

## 14.2 Phase 1: Basic React SPA

```typescript
// Simple React app
function App() {
  const [advice, setAdvice] = useState('');
  
  const handleSubmit = async (query) => {
    const response = await fetch('/generate-advice', {
      method: 'POST',
      body: JSON.stringify({ query })
    });
    setAdvice(await response.json());
  };
  
  return <form onSubmit={handleSubmit}>...</form>;
}
```

**Limitations:**
- No admin dashboard
- No real-time updates
- No state management
- No optimization

---

## 14.3 Phase 2: Production Frontend ← **DOCUMENTED & READY**

### 14.3.1 Admin Dashboard (5 Components)

**Status:** ✅ **Complete component specifications**

**Reference:** [docs/frontend-admin-dashboards.md](../frontend-admin-dashboards.md)

**Components:**
1. **CeleryJobMonitor** - Real-time task list (AG-Grid, WebSocket)
2. **BatchProcessingStatus** - Progress bars, throughput metrics
3. **IndexManagement** - FAISS version control, migration warnings
4. **QueueMonitor** - Queue depth visualization
5. **WorkerDashboard** - Worker health, CPU/memory graphs

**Stack:**
- React 18.2+ (framework)
- Redux Toolkit (state management)
- Material-UI (components)
- Socket.IO (WebSocket)
- AG-Grid (data tables)
- Recharts (charts)
- TypeScript (type safety)

---

### 14.3.2 Real-Time Integration

**Reference:** [docs/realtime-integration-advanced.md](../realtime-integration-advanced.md)

**WebSocket with Fallback:**
```typescript
const useCeleryTasks = () => {
  const [usePolling, setUsePolling] = useState(false);
  
  // Try WebSocket first
  const { connected, messages } = useWebSocket('/ws/celery/tasks');
  
  // Fall back to polling
  const { data: polledTasks } = usePolling(
    () => celeryAPI.getTasks(),
    5000,
    { enabled: usePolling || !connected }
  );
  
  return { tasks, mode: usePolling ? 'polling' : 'websocket' };
};
```

**Performance:**
- WebSocket: 50ms latency
- Polling: 2,500ms latency
- **50x improvement**

---

### 14.3.3 Advanced State Management

**Reference:** [docs/frontend-architecture-patterns.md](../frontend-architecture-patterns.md)

**Normalized Redux:**
```typescript
import { createEntityAdapter } from '@reduxjs/toolkit';

const tasksAdapter = createEntityAdapter<CeleryTask>({
  selectId: (task) => task.id,
  sortComparer: (a, b) => b.timestamp.localeCompare(a.timestamp)
});

// O(1) lookups (vs O(n) array search)
const task = tasksAdapter.selectById(state, taskId);
```

**RTK Query (Auto-caching):**
```typescript
const { data: tasks, isLoading } = useGetTasksQuery(
  { queue: 'embedding' },
  { pollingInterval: 5000 }
);

// Automatic: fetching, caching, polling, error handling
```

---

### 14.3.4 Performance Optimization

**Virtual Scrolling:**
```typescript
import { FixedSizeList } from 'react-window';

// Render 10,000 tasks without lag
<FixedSizeList
  height={600}
  itemCount={10000}
  itemSize={60}
>
  {TaskRow}
</FixedSizeList>
```

**Performance:**
- Before: 5s render for 10K items
- After: 50ms render
- **100x improvement**

**Reference:** [docs/frontend-architecture-patterns.md](../frontend-architecture-patterns.md) section "Performance Optimization"

---

## 14.4 Phase 3: Micro-Frontends

### Module Federation

**Reference:** [docs/frontend-architecture-patterns.md](../frontend-architecture-patterns.md) section "Micro-Frontend Architecture"

```javascript
// Webpack 5 Module Federation
new ModuleFederationPlugin({
  name: 'host',
  remotes: {
    celeryModule: 'celeryModule@http://localhost:3001/remoteEntry.js',
    indexModule: 'indexModule@http://localhost:3002/remoteEntry.js',
  },
  shared: {
    react: { singleton: true },
    '@reduxjs/toolkit': { singleton: true },
  }
})

// Load remote components
const CeleryJobMonitor = lazy(() => import('celeryModule/CeleryJobMonitor'));
```

**Benefits:**
- Independent deployment per dashboard
- Team autonomy (separate codebases)
- Shared dependencies (no duplication)

---

## 14.5 Summary

| Aspect | Phase 1 | Phase 2 ← DOCUMENTED | Phase 3 | Phase 4-5 |
|--------|---------|---------------------|---------|-----------|
| **Components** | Basic forms | 5 admin dashboards | Micro-frontends | Edge-rendered |
| **State** | useState | Redux + RTK Query | + Zustand | + Server state sync |
| **Real-Time** | None | WebSocket + fallback | + GraphQL subscriptions | + Server-Sent Events |
| **Performance** | 5s render | 50ms render (virtual) | + Code splitting | + Edge caching |
| **Bundle** | 2MB | 200KB | 100KB | 50KB |

**Reference:** [docs/frontend-admin-dashboards.md](../frontend-admin-dashboards.md), [docs/frontend-architecture-patterns.md](../frontend-architecture-patterns.md)

