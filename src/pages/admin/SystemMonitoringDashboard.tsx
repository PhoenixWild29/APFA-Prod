/**
 * System Monitoring Administrative Dashboard
 * 
 * Comprehensive admin interface for monitoring and managing:
 * - Celery jobs and workers
 * - Redis cache performance
 * - FAISS index management
 * - System performance metrics
 * - Batch processing progress
 * - Task cancellation
 * - Audit logs
 * - Data export
 */
import React, { useState, useEffect } from 'react';
import { CeleryMonitor } from '../../components/admin/CeleryMonitor';
import { BatchProgressTracker } from '../../components/admin/BatchProgressTracker';
import { FaissManager } from '../../components/admin/FaissManager';
import { RedisMonitor } from '../../components/admin/RedisMonitor';
import { SystemPerformance } from '../../components/admin/SystemPerformance';
import { TaskCanceller } from '../../components/admin/TaskCanceller';
import { AuditLogViewer } from '../../components/admin/AuditLogViewer';
import { DataExporter } from '../../components/admin/DataExporter';

export const SystemMonitoringDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [refreshInterval, setRefreshInterval] = useState<number>(5000);

  return (
    <div className="admin-dashboard">
      <header className="dashboard-header">
        <h1>System Monitoring Dashboard</h1>
        <div className="controls">
          <label>
            Refresh Interval:
            <select value={refreshInterval} onChange={(e) => setRefreshInterval(Number(e.target.value))}>
              <option value={1000}>1s</option>
              <option value={5000}>5s</option>
              <option value={10000}>10s</option>
              <option value={30000}>30s</option>
            </select>
          </label>
        </div>
      </header>

      <nav className="dashboard-tabs">
        <button
          className={activeTab === 'overview' ? 'active' : ''}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={activeTab === 'celery' ? 'active' : ''}
          onClick={() => setActiveTab('celery')}
        >
          Celery Jobs
        </button>
        <button
          className={activeTab === 'cache' ? 'active' : ''}
          onClick={() => setActiveTab('cache')}
        >
          Redis Cache
        </button>
        <button
          className={activeTab === 'faiss' ? 'active' : ''}
          onClick={() => setActiveTab('faiss')}
        >
          FAISS Index
        </button>
        <button
          className={activeTab === 'performance' ? 'active' : ''}
          onClick={() => setActiveTab('performance')}
        >
          Performance
        </button>
        <button
          className={activeTab === 'audit' ? 'active' : ''}
          onClick={() => setActiveTab('audit')}
        >
          Audit Logs
        </button>
      </nav>

      <main className="dashboard-content">
        {activeTab === 'overview' && (
          <div className="overview-grid">
            <SystemPerformance refreshInterval={refreshInterval} />
            <CeleryMonitor refreshInterval={refreshInterval} compact={true} />
            <RedisMonitor refreshInterval={refreshInterval} compact={true} />
            <FaissManager refreshInterval={refreshInterval} compact={true} />
          </div>
        )}

        {activeTab === 'celery' && (
          <div className="celery-section">
            <CeleryMonitor refreshInterval={refreshInterval} />
            <BatchProgressTracker refreshInterval={refreshInterval} />
            <TaskCanceller />
          </div>
        )}

        {activeTab === 'cache' && (
          <RedisMonitor refreshInterval={refreshInterval} />
        )}

        {activeTab === 'faiss' && (
          <FaissManager refreshInterval={refreshInterval} />
        )}

        {activeTab === 'performance' && (
          <SystemPerformance refreshInterval={refreshInterval} />
        )}

        {activeTab === 'audit' && (
          <div className="audit-section">
            <AuditLogViewer />
            <DataExporter />
          </div>
        )}
      </main>
    </div>
  );
};

