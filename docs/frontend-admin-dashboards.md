# Frontend Admin Dashboards - Technical Specification

**Version:** 1.0  
**Last Updated:** 2025-10-11  
**Owner:** Frontend Team  
**Status:** Design - Implementation Pending

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Component Specifications](#component-specifications)
4. [Integration Patterns](#integration-patterns)
5. [State Management](#state-management)
6. [Error Handling](#error-handling)
7. [Performance Optimization](#performance-optimization)
8. [Security Considerations](#security-considerations)
9. [Testing Strategy](#testing-strategy)
10. [Deployment](#deployment)

---

## Overview

### Purpose

Provide operational visibility into APFA's background job processing system through real-time admin dashboards. Enables SRE and backend teams to monitor, debug, and manage Celery tasks without requiring command-line access.

### Target Users

- **SRE Team:** Monitor system health, respond to alerts
- **Backend Engineers:** Debug failed tasks, trigger manual jobs
- **Product Team:** View system metrics, capacity planning
- **On-Call Engineers:** Quick status checks during incidents

### Key Requirements

1. **Real-time updates:** <5 second latency for task status changes
2. **Historical data:** View tasks from past 24 hours
3. **Admin actions:** Trigger jobs, revoke tasks, scale workers
4. **Responsive design:** Mobile-friendly for on-call scenarios
5. **Performance:** Handle 1000+ concurrent tasks without UI lag

---

## Architecture

### Technology Stack

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| **Framework** | React | 18.2+ | Component reusability, ecosystem |
| **State Management** | Redux Toolkit | 1.9+ | Predictable state, DevTools |
| **Real-time** | Socket.IO | 4.5+ | WebSocket with fallback |
| **HTTP Client** | Axios | 1.4+ | Interceptors, retry logic |
| **UI Library** | Material-UI (MUI) | 5.14+ | Production-ready components |
| **Charts** | Recharts | 2.8+ | React-native charting |
| **Data Grid** | AG-Grid React | 30+ | High-performance tables |
| **Notifications** | React-Toastify | 9.1+ | Toast messages |

### Application Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── admin/
│   │   │   ├── CeleryJobMonitor/
│   │   │   │   ├── CeleryJobMonitor.tsx
│   │   │   │   ├── CeleryJobMonitor.test.tsx
│   │   │   │   ├── CeleryJobMonitor.styles.ts
│   │   │   │   └── index.ts
│   │   │   ├── BatchProcessingStatus/
│   │   │   │   ├── BatchProcessingStatus.tsx
│   │   │   │   └── ...
│   │   │   ├── IndexManagement/
│   │   │   │   ├── IndexManagement.tsx
│   │   │   │   └── ...
│   │   │   ├── QueueMonitor/
│   │   │   │   ├── QueueMonitor.tsx
│   │   │   │   └── ...
│   │   │   └── WorkerDashboard/
│   │   │       ├── WorkerDashboard.tsx
│   │   │       └── ...
│   ├── api/
│   │   ├── celery.api.ts
│   │   ├── metrics.api.ts
│   │   └── websocket.ts
│   ├── store/
│   │   ├── slices/
│   │   │   ├── celerySlice.ts
│   │   │   ├── metricsSlice.ts
│   │   │   └── authSlice.ts
│   │   └── store.ts
│   ├── hooks/
│   │   ├── useWebSocket.ts
│   │   ├── useCeleryTasks.ts
│   │   └── usePolling.ts
│   ├── types/
│   │   ├── celery.types.ts
│   │   └── metrics.types.ts
│   └── utils/
│       ├── formatters.ts
│       └── validators.ts
```

---

## Component Specifications

### 1. CeleryJobMonitor

**Purpose:** Real-time monitoring of all Celery tasks across all queues.

#### Component Interface

```typescript
// src/types/celery.types.ts
export interface CeleryTask {
  id: string;
  name: string;
  state: 'PENDING' | 'STARTED' | 'RETRY' | 'FAILURE' | 'SUCCESS';
  queue: 'embedding' | 'indexing' | 'maintenance';
  args: any[];
  kwargs: Record<string, any>;
  worker: string;
  timestamp: string;
  runtime?: number;
  retries?: number;
  exception?: string;
  result?: any;
}

export interface CeleryJobMonitorProps {
  autoRefresh?: boolean;
  refreshInterval?: number; // milliseconds
  maxTasks?: number;
  filters?: {
    queue?: string[];
    state?: string[];
    worker?: string[];
  };
  onTaskClick?: (task: CeleryTask) => void;
}
```

#### Component Implementation

```typescript
// src/components/admin/CeleryJobMonitor/CeleryJobMonitor.tsx
import React, { useState, useEffect, useMemo } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  IconButton,
  Tooltip,
  LinearProgress,
} from '@mui/material';
import { AgGridReact } from 'ag-grid-react';
import RefreshIcon from '@mui/icons-material/Refresh';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import StopIcon from '@mui/icons-material/Stop';
import { useWebSocket } from '../../../hooks/useWebSocket';
import { fetchCeleryTasks, revokeTask } from '../../../store/slices/celerySlice';
import { formatDuration, formatTimestamp } from '../../../utils/formatters';
import type { CeleryTask, CeleryJobMonitorProps } from '../../../types/celery.types';

export const CeleryJobMonitor: React.FC<CeleryJobMonitorProps> = ({
  autoRefresh = true,
  refreshInterval = 5000,
  maxTasks = 1000,
  filters,
  onTaskClick,
}) => {
  const dispatch = useDispatch();
  const { tasks, loading, error } = useSelector((state: RootState) => state.celery);
  const [selectedQueue, setSelectedQueue] = useState<string>('all');
  const [selectedState, setSelectedState] = useState<string>('all');

  // WebSocket connection for real-time updates
  const { connected, messages } = useWebSocket('/ws/celery/tasks', {
    autoConnect: autoRefresh,
    reconnect: true,
  });

  // Fetch initial data
  useEffect(() => {
    dispatch(fetchCeleryTasks());
  }, [dispatch]);

  // Handle WebSocket messages
  useEffect(() => {
    if (messages.length > 0) {
      const latestMessage = messages[messages.length - 1];
      if (latestMessage.type === 'task_update') {
        // Update task in Redux store
        dispatch(updateTask(latestMessage.data));
      }
    }
  }, [messages, dispatch]);

  // Filter tasks
  const filteredTasks = useMemo(() => {
    let filtered = [...tasks];

    if (selectedQueue !== 'all') {
      filtered = filtered.filter(task => task.queue === selectedQueue);
    }

    if (selectedState !== 'all') {
      filtered = filtered.filter(task => task.state === selectedState);
    }

    if (filters) {
      if (filters.queue) {
        filtered = filtered.filter(task => filters.queue!.includes(task.queue));
      }
      if (filters.state) {
        filtered = filtered.filter(task => filters.state!.includes(task.state));
      }
      if (filters.worker) {
        filtered = filtered.filter(task => filters.worker!.includes(task.worker));
      }
    }

    return filtered.slice(0, maxTasks);
  }, [tasks, selectedQueue, selectedState, filters, maxTasks]);

  // AG-Grid column definitions
  const columnDefs = useMemo(() => [
    {
      field: 'state',
      headerName: 'Status',
      width: 120,
      cellRenderer: (params: any) => {
        const stateColors = {
          PENDING: 'default',
          STARTED: 'primary',
          RETRY: 'warning',
          FAILURE: 'error',
          SUCCESS: 'success',
        };
        return <Chip label={params.value} color={stateColors[params.value]} size="small" />;
      },
    },
    {
      field: 'name',
      headerName: 'Task Name',
      width: 250,
      cellRenderer: (params: any) => (
        <Tooltip title={params.value}>
          <span>{params.value.split('.').pop()}</span>
        </Tooltip>
      ),
    },
    {
      field: 'queue',
      headerName: 'Queue',
      width: 120,
      cellRenderer: (params: any) => {
        const queueColors = {
          embedding: '#1976d2',
          indexing: '#f57c00',
          maintenance: '#388e3c',
        };
        return (
          <Chip
            label={params.value}
            size="small"
            style={{ backgroundColor: queueColors[params.value] }}
          />
        );
      },
    },
    {
      field: 'worker',
      headerName: 'Worker',
      width: 150,
    },
    {
      field: 'timestamp',
      headerName: 'Started',
      width: 160,
      valueFormatter: (params: any) => formatTimestamp(params.value),
    },
    {
      field: 'runtime',
      headerName: 'Duration',
      width: 100,
      valueFormatter: (params: any) => formatDuration(params.value),
    },
    {
      field: 'retries',
      headerName: 'Retries',
      width: 80,
      cellRenderer: (params: any) =>
        params.value > 0 ? (
          <Chip label={params.value} color="warning" size="small" />
        ) : (
          <span>-</span>
        ),
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 100,
      cellRenderer: (params: any) => (
        <IconButton
          size="small"
          onClick={() => handleRevokeTask(params.data.id)}
          disabled={['SUCCESS', 'FAILURE'].includes(params.data.state)}
        >
          <StopIcon fontSize="small" />
        </IconButton>
      ),
    },
  ], []);

  // Handle task revocation
  const handleRevokeTask = async (taskId: string) => {
    if (window.confirm('Are you sure you want to revoke this task?')) {
      await dispatch(revokeTask(taskId));
    }
  };

  // Manual refresh
  const handleRefresh = () => {
    dispatch(fetchCeleryTasks());
  };

  return (
    <Card>
      <CardHeader
        title="Celery Task Monitor"
        subheader={
          <>
            {connected ? (
              <Chip label="Live" color="success" size="small" />
            ) : (
              <Chip label="Disconnected" color="error" size="small" />
            )}
            <span style={{ marginLeft: 8 }}>
              {filteredTasks.length} tasks ({tasks.filter(t => t.state === 'STARTED').length} active)
            </span>
          </>
        }
        action={
          <Box display="flex" gap={1}>
            <FormControl size="small" style={{ minWidth: 120 }}>
              <InputLabel>Queue</InputLabel>
              <Select value={selectedQueue} onChange={(e) => setSelectedQueue(e.target.value)}>
                <MenuItem value="all">All Queues</MenuItem>
                <MenuItem value="embedding">Embedding</MenuItem>
                <MenuItem value="indexing">Indexing</MenuItem>
                <MenuItem value="maintenance">Maintenance</MenuItem>
              </Select>
            </FormControl>

            <FormControl size="small" style={{ minWidth: 120 }}>
              <InputLabel>State</InputLabel>
              <Select value={selectedState} onChange={(e) => setSelectedState(e.target.value)}>
                <MenuItem value="all">All States</MenuItem>
                <MenuItem value="PENDING">Pending</MenuItem>
                <MenuItem value="STARTED">Started</MenuItem>
                <MenuItem value="SUCCESS">Success</MenuItem>
                <MenuItem value="FAILURE">Failure</MenuItem>
              </Select>
            </FormControl>

            <Tooltip title="Refresh">
              <IconButton onClick={handleRefresh} disabled={loading}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>
        }
      />
      <CardContent>
        {loading && <LinearProgress />}
        {error && <Alert severity="error">{error}</Alert>}

        <div className="ag-theme-material" style={{ height: 600, width: '100%' }}>
          <AgGridReact
            columnDefs={columnDefs}
            rowData={filteredTasks}
            pagination={true}
            paginationPageSize={50}
            onRowClicked={(event) => onTaskClick?.(event.data)}
            animateRows={true}
            enableCellTextSelection={true}
          />
        </div>
      </CardContent>
    </Card>
  );
};

export default CeleryJobMonitor;
```

#### State Management (Redux Slice)

```typescript
// src/store/slices/celerySlice.ts
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { celeryAPI } from '../../api/celery.api';
import type { CeleryTask } from '../../types/celery.types';

interface CeleryState {
  tasks: CeleryTask[];
  loading: boolean;
  error: string | null;
  lastUpdate: string | null;
}

const initialState: CeleryState = {
  tasks: [],
  loading: false,
  error: null,
  lastUpdate: null,
};

// Async thunks
export const fetchCeleryTasks = createAsyncThunk(
  'celery/fetchTasks',
  async (filters?: any) => {
    const response = await celeryAPI.getTasks(filters);
    return response.data;
  }
);

export const revokeTask = createAsyncThunk(
  'celery/revokeTask',
  async (taskId: string) => {
    await celeryAPI.revokeTask(taskId);
    return taskId;
  }
);

export const triggerEmbeddingJob = createAsyncThunk(
  'celery/triggerEmbedding',
  async () => {
    const response = await celeryAPI.triggerJob('embed_all_documents');
    return response.data;
  }
);

// Slice
const celerySlice = createSlice({
  name: 'celery',
  initialState,
  reducers: {
    updateTask: (state, action: PayloadAction<CeleryTask>) => {
      const index = state.tasks.findIndex(t => t.id === action.payload.id);
      if (index !== -1) {
        state.tasks[index] = action.payload;
      } else {
        state.tasks.unshift(action.payload);
      }
      state.lastUpdate = new Date().toISOString();
    },
    clearTasks: (state) => {
      state.tasks = [];
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchCeleryTasks.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchCeleryTasks.fulfilled, (state, action) => {
        state.loading = false;
        state.tasks = action.payload;
        state.lastUpdate = new Date().toISOString();
      })
      .addCase(fetchCeleryTasks.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch tasks';
      })
      .addCase(revokeTask.fulfilled, (state, action) => {
        const task = state.tasks.find(t => t.id === action.payload);
        if (task) {
          task.state = 'REVOKED';
        }
      });
  },
});

export const { updateTask, clearTasks } = celerySlice.actions;
export default celerySlice.reducer;
```

---

### 2. BatchProcessingStatus

**Purpose:** Monitor batch embedding jobs with progress indicators.

#### Component Interface

```typescript
// src/types/celery.types.ts
export interface BatchJob {
  jobId: string;
  taskId: string;
  totalBatches: number;
  completedBatches: number;
  failedBatches: number;
  status: 'running' | 'completed' | 'failed' | 'paused';
  startTime: string;
  endTime?: string;
  estimatedTimeRemaining?: number;
  throughput?: number; // docs/sec
  errors?: string[];
}

export interface BatchProcessingStatusProps {
  jobId?: string; // If provided, show specific job; otherwise show all active jobs
  showHistory?: boolean;
  maxHistoryItems?: number;
}
```

#### Component Implementation

```typescript
// src/components/admin/BatchProcessingStatus/BatchProcessingStatus.tsx
import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  LinearProgress,
  Box,
  Typography,
  Grid,
  Chip,
  Button,
  Alert,
} from '@mui/material';
import { Line } from 'react-chartjs-2';
import { useSelector, useDispatch } from 'react-redux';
import { fetchBatchJobs, pauseBatchJob, resumeBatchJob } from '../../../store/slices/celerySlice';
import type { BatchJob } from '../../../types/celery.types';

export const BatchProcessingStatus: React.FC<BatchProcessingStatusProps> = ({
  jobId,
  showHistory = false,
  maxHistoryItems = 10,
}) => {
  const dispatch = useDispatch();
  const { batchJobs } = useSelector((state: RootState) => state.celery);

  useEffect(() => {
    dispatch(fetchBatchJobs(jobId));
  }, [dispatch, jobId]);

  const activeJobs = batchJobs.filter(job => job.status === 'running');
  const jobsToDisplay = jobId
    ? batchJobs.filter(job => job.jobId === jobId)
    : showHistory
    ? batchJobs.slice(0, maxHistoryItems)
    : activeJobs;

  return (
    <Box>
      {jobsToDisplay.map((job) => (
        <Card key={job.jobId} style={{ marginBottom: 16 }}>
          <CardHeader
            title={`Batch Job: ${job.jobId}`}
            subheader={`Started: ${new Date(job.startTime).toLocaleString()}`}
            action={
              <Box>
                <Chip
                  label={job.status}
                  color={
                    job.status === 'completed'
                      ? 'success'
                      : job.status === 'failed'
                      ? 'error'
                      : 'primary'
                  }
                />
                {job.status === 'running' && (
                  <Button
                    size="small"
                    onClick={() => dispatch(pauseBatchJob(job.jobId))}
                    style={{ marginLeft: 8 }}
                  >
                    Pause
                  </Button>
                )}
                {job.status === 'paused' && (
                  <Button
                    size="small"
                    onClick={() => dispatch(resumeBatchJob(job.jobId))}
                    style={{ marginLeft: 8 }}
                  >
                    Resume
                  </Button>
                )}
              </Box>
            }
          />
          <CardContent>
            <Grid container spacing={2}>
              {/* Progress Bar */}
              <Grid item xs={12}>
                <Box display="flex" alignItems="center">
                  <Box width="100%" mr={1}>
                    <LinearProgress
                      variant="determinate"
                      value={(job.completedBatches / job.totalBatches) * 100}
                      color={job.failedBatches > 0 ? 'warning' : 'primary'}
                    />
                  </Box>
                  <Box minWidth={35}>
                    <Typography variant="body2" color="textSecondary">
                      {Math.round((job.completedBatches / job.totalBatches) * 100)}%
                    </Typography>
                  </Box>
                </Box>
              </Grid>

              {/* Statistics */}
              <Grid item xs={3}>
                <Typography variant="subtitle2" color="textSecondary">
                  Total Batches
                </Typography>
                <Typography variant="h6">{job.totalBatches}</Typography>
              </Grid>
              <Grid item xs={3}>
                <Typography variant="subtitle2" color="textSecondary">
                  Completed
                </Typography>
                <Typography variant="h6" color="success.main">
                  {job.completedBatches}
                </Typography>
              </Grid>
              <Grid item xs={3}>
                <Typography variant="subtitle2" color="textSecondary">
                  Failed
                </Typography>
                <Typography variant="h6" color="error.main">
                  {job.failedBatches}
                </Typography>
              </Grid>
              <Grid item xs={3}>
                <Typography variant="subtitle2" color="textSecondary">
                  Throughput
                </Typography>
                <Typography variant="h6">
                  {job.throughput?.toFixed(0) || '-'} docs/s
                </Typography>
              </Grid>

              {/* Estimated Time Remaining */}
              {job.status === 'running' && job.estimatedTimeRemaining && (
                <Grid item xs={12}>
                  <Alert severity="info">
                    Estimated time remaining: {formatDuration(job.estimatedTimeRemaining * 1000)}
                  </Alert>
                </Grid>
              )}

              {/* Errors */}
              {job.errors && job.errors.length > 0 && (
                <Grid item xs={12}>
                  <Alert severity="error">
                    <Typography variant="subtitle2">Recent Errors:</Typography>
                    <ul>
                      {job.errors.slice(0, 3).map((error, idx) => (
                        <li key={idx}>{error}</li>
                      ))}
                    </ul>
                  </Alert>
                </Grid>
              )}
            </Grid>
          </CardContent>
        </Card>
      ))}

      {jobsToDisplay.length === 0 && (
        <Card>
          <CardContent>
            <Typography variant="body1" color="textSecondary" align="center">
              No batch jobs {jobId ? `with ID ${jobId}` : showHistory ? 'found' : 'currently running'}
            </Typography>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default BatchProcessingStatus;
```

---

### 3. IndexManagement

**Purpose:** Manage FAISS indexes, trigger rebuilds, view versions.

#### Component Interface

```typescript
// src/types/index.types.ts
export interface FAISSIndex {
  version: string;
  vectorCount: number;
  dimensions: number;
  indexType: 'IndexFlatIP' | 'IndexIVFFlat' | 'IndexIVFPQ';
  memoryMB: number;
  createdAt: string;
  isActive: boolean;
  buildDuration?: number;
  migrationUrgency?: number; // 0-100 score
}

export interface IndexManagementProps {
  allowManualOperations?: boolean;
}
```

#### Component Implementation

```typescript
// src/components/admin/IndexManagement/IndexManagement.tsx
import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
  Alert,
  CircularProgress,
  Box,
} from '@mui/material';
import { useSelector, useDispatch } from 'react-redux';
import {
  fetchIndexes,
  triggerIndexRebuild,
  swapIndex,
} from '../../../store/slices/indexSlice';
import type { FAISSIndex } from '../../../types/index.types';

export const IndexManagement: React.FC<IndexManagementProps> = ({
  allowManualOperations = true,
}) => {
  const dispatch = useDispatch();
  const { indexes, activeIndex, loading } = useSelector((state: RootState) => state.index);
  const [rebuildDialogOpen, setRebuildDialogOpen] = useState(false);
  const [swapDialogOpen, setSwapDialogOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState<FAISSIndex | null>(null);

  useEffect(() => {
    dispatch(fetchIndexes());
  }, [dispatch]);

  const handleTriggerRebuild = async () => {
    await dispatch(triggerIndexRebuild());
    setRebuildDialogOpen(false);
  };

  const handleSwapIndex = async () => {
    if (selectedIndex) {
      await dispatch(swapIndex(selectedIndex.version));
      setSwapDialogOpen(false);
    }
  };

  const getMigrationUrgencyColor = (urgency: number) => {
    if (urgency < 70) return 'success';
    if (urgency < 90) return 'warning';
    return 'error';
  };

  return (
    <>
      <Card>
        <CardHeader
          title="FAISS Index Management"
          subheader={`Active Index: ${activeIndex?.version || 'None'}`}
          action={
            allowManualOperations && (
              <Button
                variant="contained"
                color="primary"
                onClick={() => setRebuildDialogOpen(true)}
                disabled={loading}
              >
                Rebuild Index
              </Button>
            )
          }
        />
        <CardContent>
          {loading && (
            <Box display="flex" justifyContent="center" py={4}>
              <CircularProgress />
            </Box>
          )}

          {!loading && indexes.length === 0 && (
            <Alert severity="warning">No indexes found. Trigger a rebuild to create one.</Alert>
          )}

          {!loading && indexes.length > 0 && (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Status</TableCell>
                    <TableCell>Version</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Vectors</TableCell>
                    <TableCell>Memory</TableCell>
                    <TableCell>Created</TableCell>
                    <TableCell>Migration Urgency</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {indexes.map((index) => (
                    <TableRow key={index.version}>
                      <TableCell>
                        {index.isActive ? (
                          <Chip label="Active" color="success" size="small" />
                        ) : (
                          <Chip label="Inactive" color="default" size="small" />
                        )}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" fontFamily="monospace">
                          {index.version}
                        </Typography>
                      </TableCell>
                      <TableCell>{index.indexType}</TableCell>
                      <TableCell>{index.vectorCount.toLocaleString()}</TableCell>
                      <TableCell>{index.memoryMB.toFixed(2)} MB</TableCell>
                      <TableCell>{new Date(index.createdAt).toLocaleString()}</TableCell>
                      <TableCell>
                        {index.migrationUrgency !== undefined ? (
                          <Box display="flex" alignItems="center" gap={1}>
                            <CircularProgress
                              variant="determinate"
                              value={index.migrationUrgency}
                              size={30}
                              color={getMigrationUrgencyColor(index.migrationUrgency)}
                            />
                            <Typography variant="body2">
                              {index.migrationUrgency.toFixed(0)}%
                            </Typography>
                          </Box>
                        ) : (
                          '-'
                        )}
                      </TableCell>
                      <TableCell>
                        {!index.isActive && allowManualOperations && (
                          <Button
                            size="small"
                            onClick={() => {
                              setSelectedIndex(index);
                              setSwapDialogOpen(true);
                            }}
                          >
                            Activate
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}

          {/* Migration Warning */}
          {activeIndex && activeIndex.migrationUrgency && activeIndex.migrationUrgency > 70 && (
            <Alert severity={activeIndex.migrationUrgency > 90 ? 'error' : 'warning'} style={{ marginTop: 16 }}>
              <Typography variant="subtitle2">
                {activeIndex.migrationUrgency > 90
                  ? 'CRITICAL: Index migration required immediately'
                  : 'WARNING: Plan index migration within 30 days'}
              </Typography>
              <Typography variant="body2">
                Current: {activeIndex.vectorCount.toLocaleString()} vectors (
                {activeIndex.indexType})
              </Typography>
              <Typography variant="body2">
                Recommended: Migrate to IndexIVFFlat for vectors &gt; 500K
              </Typography>
              <Button
                size="small"
                variant="outlined"
                style={{ marginTop: 8 }}
                onClick={() =>
                  window.open('/docs/adrs/002-faiss-indexflat-to-ivfflat-migration.md', '_blank')
                }
              >
                View Migration Guide
              </Button>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Rebuild Confirmation Dialog */}
      <Dialog open={rebuildDialogOpen} onClose={() => setRebuildDialogOpen(false)}>
        <DialogTitle>Rebuild FAISS Index</DialogTitle>
        <DialogContent>
          <Typography>
            This will trigger a full index rebuild from all embedding batches in MinIO.
            <br />
            <br />
            <strong>Duration:</strong> 10-30 minutes for 100K vectors
            <br />
            <strong>Impact:</strong> No downtime (hot-swap on completion)
            <br />
            <br />
            Continue?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRebuildDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleTriggerRebuild} color="primary" variant="contained">
            Rebuild
          </Button>
        </DialogActions>
      </Dialog>

      {/* Swap Confirmation Dialog */}
      <Dialog open={swapDialogOpen} onClose={() => setSwapDialogOpen(false)}>
        <DialogTitle>Activate Index Version</DialogTitle>
        <DialogContent>
          <Typography>
            Activate index version: <strong>{selectedIndex?.version}</strong>
            <br />
            <br />
            This will perform a hot-swap with zero downtime. All APFA instances will load the new
            index.
            <br />
            <br />
            Continue?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSwapDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSwapIndex} color="primary" variant="contained">
            Activate
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default IndexManagement;
```

---

### 4. QueueMonitor

**Purpose:** Real-time visualization of queue depths and worker status.

#### Component Implementation

```typescript
// src/components/admin/QueueMonitor/QueueMonitor.tsx
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, Grid, Box, Typography, LinearProgress, Chip } from '@mui/material';
import { Line } from 'react-chartjs-2';
import { useSelector } from 'react-redux';
import { usePolling } from '../../../hooks/usePolling';
import { fetchQueueStats } from '../../../api/celery.api';

export const QueueMonitor: React.FC = () => {
  const [queueStats, setQueueStats] = useState({
    embedding: { depth: 0, workers: 0, rate: 0 },
    indexing: { depth: 0, workers: 0, rate: 0 },
    maintenance: { depth: 0, workers: 0, rate: 0 },
  });

  // Poll queue stats every 5 seconds
  usePolling(async () => {
    const stats = await fetchQueueStats();
    setQueueStats(stats.data);
  }, 5000);

  const getQueueHealth = (depth: number) => {
    if (depth < 10) return 'success';
    if (depth < 50) return 'warning';
    return 'error';
  };

  return (
    <Grid container spacing={2}>
      {Object.entries(queueStats).map(([queueName, stats]) => (
        <Grid item xs={12} md={4} key={queueName}>
          <Card>
            <CardHeader
              title={queueName.charAt(0).toUpperCase() + queueName.slice(1)}
              subheader={`${stats.workers} workers active`}
              action={<Chip label={getQueueHealth(stats.depth)} color={getQueueHealth(stats.depth)} />}
            />
            <CardContent>
              <Box mb={2}>
                <Typography variant="body2" color="textSecondary">
                  Queue Depth
                </Typography>
                <Typography variant="h4">{stats.depth}</Typography>
                <LinearProgress
                  variant="determinate"
                  value={Math.min((stats.depth / 50) * 100, 100)}
                  color={getQueueHealth(stats.depth)}
                  style={{ marginTop: 8 }}
                />
              </Box>

              <Box>
                <Typography variant="body2" color="textSecondary">
                  Processing Rate
                </Typography>
                <Typography variant="h6">{stats.rate.toFixed(1)} tasks/sec</Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
};

export default QueueMonitor;
```

---

### 5. WorkerDashboard

**Purpose:** Monitor Celery worker health, CPU, memory.

#### Component Implementation

```typescript
// src/components/admin/WorkerDashboard/WorkerDashboard.tsx
import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  LinearProgress,
  Box,
  Typography,
  IconButton,
  Tooltip,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import { usePolling } from '../../../hooks/usePolling';
import { fetchWorkerStats } from '../../../api/celery.api';

interface Worker {
  name: string;
  status: 'online' | 'offline';
  queue: string;
  activeTasks: number;
  cpu: number;
  memory: number;
  uptime: number;
}

export const WorkerDashboard: React.FC = () => {
  const [workers, setWorkers] = useState<Worker[]>([]);

  usePolling(async () => {
    const response = await fetchWorkerStats();
    setWorkers(response.data);
  }, 10000);

  return (
    <Card>
      <CardHeader
        title="Celery Workers"
        subheader={`${workers.filter(w => w.status === 'online').length} / ${workers.length} online`}
        action={
          <IconButton onClick={() => window.location.reload()}>
            <RefreshIcon />
          </IconButton>
        }
      />
      <CardContent>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Status</TableCell>
                <TableCell>Worker</TableCell>
                <TableCell>Queue</TableCell>
                <TableCell>Active Tasks</TableCell>
                <TableCell>CPU</TableCell>
                <TableCell>Memory</TableCell>
                <TableCell>Uptime</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {workers.map((worker) => (
                <TableRow key={worker.name}>
                  <TableCell>
                    <Chip
                      label={worker.status}
                      color={worker.status === 'online' ? 'success' : 'error'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{worker.name}</TableCell>
                  <TableCell>{worker.queue}</TableCell>
                  <TableCell>{worker.activeTasks}</TableCell>
                  <TableCell>
                    <Box display="flex" alignItems="center" gap={1}>
                      <LinearProgress
                        variant="determinate"
                        value={worker.cpu}
                        color={worker.cpu > 90 ? 'error' : worker.cpu > 70 ? 'warning' : 'primary'}
                        style={{ width: 100 }}
                      />
                      <Typography variant="body2">{worker.cpu}%</Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Box display="flex" alignItems="center" gap={1}>
                      <LinearProgress
                        variant="determinate"
                        value={worker.memory}
                        color={worker.memory > 90 ? 'error' : worker.memory > 70 ? 'warning' : 'primary'}
                        style={{ width: 100 }}
                      />
                      <Typography variant="body2">{worker.memory}%</Typography>
                    </Box>
                  </TableCell>
                  <TableCell>{formatUptime(worker.uptime)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </CardContent>
    </Card>
  );
};

const formatUptime = (seconds: number) => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  return `${hours}h ${minutes}m`;
};

export default WorkerDashboard;
```

---

## Integration Patterns

### 1. WebSocket Integration (Real-time Updates)

**Use Case:** Task status changes, queue depth updates

**Implementation:**

```typescript
// src/api/websocket.ts
import { io, Socket } from 'socket.io-client';

class WebSocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  connect(endpoint: string, options?: any): Socket {
    if (this.socket?.connected) {
      return this.socket;
    }

    this.socket = io(`${process.env.REACT_APP_WS_URL}${endpoint}`, {
      auth: {
        token: localStorage.getItem('authToken'),
      },
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: this.maxReconnectAttempts,
      ...options,
    });

    this.socket.on('connect', () => {
      console.log(`[WebSocket] Connected to ${endpoint}`);
      this.reconnectAttempts = 0;
    });

    this.socket.on('disconnect', (reason) => {
      console.log(`[WebSocket] Disconnected: ${reason}`);
    });

    this.socket.on('connect_error', (error) => {
      console.error(`[WebSocket] Connection error:`, error);
      this.reconnectAttempts++;

      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        console.error('[WebSocket] Max reconnection attempts reached');
        // Fall back to HTTP polling
        this.fallbackToPolling();
      }
    });

    return this.socket;
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  private fallbackToPolling() {
    // Emit event to switch to polling mode
    window.dispatchEvent(new CustomEvent('websocket:fallback'));
  }
}

export const websocketService = new WebSocketService();
```

**React Hook:**

```typescript
// src/hooks/useWebSocket.ts
import { useEffect, useState } from 'react';
import { websocketService } from '../api/websocket';

export const useWebSocket = (endpoint: string, options?: any) => {
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const socket = websocketService.connect(endpoint, options);

    socket.on('connect', () => setConnected(true));
    socket.on('disconnect', () => setConnected(false));
    socket.on('error', (err) => setError(err.message));

    // Listen for task updates
    socket.on('task_update', (data) => {
      setMessages((prev) => [...prev, data]);
    });

    return () => {
      socket.off('connect');
      socket.off('disconnect');
      socket.off('error');
      socket.off('task_update');
    };
  }, [endpoint]);

  return { connected, messages, error };
};
```

---

### 2. HTTP Polling Integration (Fallback)

**Use Case:** Fallback when WebSocket unavailable

**Implementation:**

```typescript
// src/hooks/usePolling.ts
import { useEffect, useRef } from 'react';

export const usePolling = (
  callback: () => Promise<void>,
  interval: number,
  options?: {
    enabled?: boolean;
    immediate?: boolean;
  }
) => {
  const { enabled = true, immediate = true } = options || {};
  const savedCallback = useRef(callback);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // Update callback ref
  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    if (!enabled) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      return;
    }

    // Execute immediately if requested
    if (immediate) {
      savedCallback.current();
    }

    // Set up interval
    intervalRef.current = setInterval(async () => {
      await savedCallback.current();
    }, interval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [interval, enabled, immediate]);
};
```

**Hybrid Strategy (WebSocket + Polling):**

```typescript
// src/hooks/useCeleryTasks.ts
import { useState, useEffect } from 'react';
import { useWebSocket } from './useWebSocket';
import { usePolling } from './usePolling';
import { fetchCeleryTasks } from '../api/celery.api';

export const useCeleryTasks = () => {
  const [tasks, setTasks] = useState([]);
  const [usePolling, setUsePolling] = useState(false);

  // Try WebSocket first
  const { connected, messages } = useWebSocket('/ws/celery/tasks', {
    autoConnect: true,
  });

  // Fall back to polling if WebSocket fails
  useEffect(() => {
    const handleFallback = () => setUsePolling(true);
    window.addEventListener('websocket:fallback', handleFallback);
    return () => window.removeEventListener('websocket:fallback', handleFallback);
  }, []);

  // WebSocket updates
  useEffect(() => {
    if (connected && messages.length > 0) {
      const latestMessage = messages[messages.length - 1];
      setTasks((prev) => updateTasksArray(prev, latestMessage.data));
    }
  }, [connected, messages]);

  // HTTP Polling (fallback)
  usePolling(
    async () => {
      const response = await fetchCeleryTasks();
      setTasks(response.data);
    },
    5000,
    { enabled: usePolling || !connected }
  );

  return { tasks, connected: !usePolling && connected };
};
```

---

### 3. Error Handling & Retry Logic

**Implementation:**

```typescript
// src/api/axios.config.ts
import axios from 'axios';
import { toast } from 'react-toastify';

const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 30000,
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor with retry
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { config, response } = error;

    // Retry logic for 5xx errors
    if (response?.status >= 500 && config.retryCount < 3) {
      config.retryCount = (config.retryCount || 0) + 1;
      const delay = Math.pow(2, config.retryCount) * 1000; // Exponential backoff

      await new Promise((resolve) => setTimeout(resolve, delay));
      return apiClient(config);
    }

    // Handle specific errors
    if (response?.status === 401) {
      // Unauthorized - redirect to login
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    } else if (response?.status === 429) {
      // Rate limited
      toast.error('Rate limit exceeded. Please try again later.');
    } else if (response?.status >= 500) {
      toast.error('Server error. Please try again.');
    } else {
      toast.error(response?.data?.detail || 'An error occurred');
    }

    return Promise.reject(error);
  }
);

export default apiClient;
```

---

## Deployment

### Environment Configuration

```typescript
// .env.production
REACT_APP_API_URL=https://api.apfa.io
REACT_APP_WS_URL=wss://api.apfa.io
REACT_APP_POLLING_INTERVAL=10000
REACT_APP_WS_RECONNECT_ATTEMPTS=5
```

### Build & Deploy

```bash
# Build for production
npm run build

# Deploy to S3 + CloudFront
aws s3 sync build/ s3://apfa-frontend-prod/
aws cloudfront create-invalidation --distribution-id E123456 --paths "/*"
```

---

## Performance Optimization

### 1. Code Splitting

```typescript
// Lazy load admin components
const CeleryJobMonitor = React.lazy(() => import('./components/admin/CeleryJobMonitor'));
const BatchProcessingStatus = React.lazy(() => import('./components/admin/BatchProcessingStatus'));

<Suspense fallback={<CircularProgress />}>
  <CeleryJobMonitor />
</Suspense>
```

### 2. Memoization

```typescript
// Memoize expensive computations
const filteredTasks = useMemo(() => {
  return tasks.filter(/* ... */).slice(0, maxTasks);
}, [tasks, maxTasks, filters]);
```

### 3. Virtualization for Large Lists

```typescript
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={600}
  itemCount={tasks.length}
  itemSize={50}
  width="100%"
>
  {({ index, style }) => <TaskRow task={tasks[index]} style={style} />}
</FixedSizeList>
```

---

## Testing Strategy

### Unit Tests

```typescript
// CeleryJobMonitor.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { CeleryJobMonitor } from './CeleryJobMonitor';
import { configureStore } from '@reduxjs/toolkit';
import celeryReducer from '../../../store/slices/celerySlice';

describe('CeleryJobMonitor', () => {
  const mockStore = configureStore({
    reducer: { celery: celeryReducer },
  });

  it('renders task list', async () => {
    render(
      <Provider store={mockStore}>
        <CeleryJobMonitor />
      </Provider>
    );

    await waitFor(() => {
      expect(screen.getByText('Celery Task Monitor')).toBeInTheDocument();
    });
  });

  it('filters tasks by queue', () => {
    // Test implementation
  });
});
```

---

## Security Considerations

### 1. Authentication

- All admin endpoints require JWT token
- Tokens expire after 30 minutes
- Refresh tokens for seamless experience

### 2. Authorization

- Role-based access: Only admins can trigger jobs
- Audit log for all admin actions

### 3. Input Validation

- Validate all user inputs client-side
- Server-side validation as final check

---

## Monitoring & Observability

### Frontend Metrics

```typescript
// Track component performance
useEffect(() => {
  const startTime = performance.now();

  return () => {
    const duration = performance.now() - startTime;
    if (duration > 1000) {
      console.warn(`Slow component render: ${duration}ms`);
    }
  };
}, []);
```

---

**Document Status:** Design Complete - Ready for Implementation  
**Estimated Implementation Time:** 2-3 weeks (frontend team)  
**Dependencies:** Backend APIs documented in [API Integration Patterns](api-integration-patterns.md)

---

**References:**
- [APFA Backend Documentation](background-jobs.md)
- [Observability Guide](observability.md)
- [API Documentation](../docs/api.md)

