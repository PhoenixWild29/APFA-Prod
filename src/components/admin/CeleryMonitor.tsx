/**
 * Celery Job Monitoring Component
 * 
 * Displays:
 * - Real-time task status
 * - Queue lengths
 * - Worker information
 * - Task history
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface CeleryMonitorProps {
  refreshInterval?: number;
  compact?: boolean;
}

interface CeleryMetrics {
  active_tasks: number;
  pending_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  workers: Array<{
    name: string;
    status: string;
    tasks_processed: number;
  }>;
  queues: Record<string, number>;
}

export const CeleryMonitor: React.FC<CeleryMonitorProps> = ({ 
  refreshInterval = 5000, 
  compact = false 
}) => {
  const [metrics, setMetrics] = useState<CeleryMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await axios.get('/admin/integration/celery-status');
        setMetrics(response.data);
        setLoading(false);
      } catch (error) {
        console.error('Failed to fetch Celery metrics:', error);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, refreshInterval);

    return () => clearInterval(interval);
  }, [refreshInterval]);

  if (loading) return <div>Loading Celery metrics...</div>;
  if (!metrics) return <div>Failed to load Celery data</div>;

  return (
    <div className={`celery-monitor ${compact ? 'compact' : ''}`}>
      <h2>Celery Job Monitor</h2>
      
      <div className="metrics-grid">
        <div className="metric-card">
          <h3>Active Tasks</h3>
          <div className="value">{metrics.active_tasks}</div>
        </div>
        <div className="metric-card">
          <h3>Pending</h3>
          <div className="value">{metrics.pending_tasks}</div>
        </div>
        <div className="metric-card">
          <h3>Completed</h3>
          <div className="value success">{metrics.completed_tasks}</div>
        </div>
        <div className="metric-card">
          <h3>Failed</h3>
          <div className="value error">{metrics.failed_tasks}</div>
        </div>
      </div>

      {!compact && (
        <>
          <div className="workers-section">
            <h3>Workers</h3>
            <table>
              <thead>
                <tr>
                  <th>Worker Name</th>
                  <th>Status</th>
                  <th>Tasks Processed</th>
                </tr>
              </thead>
              <tbody>
                {metrics.workers.map((worker, idx) => (
                  <tr key={idx}>
                    <td>{worker.name}</td>
                    <td>
                      <span className={`status ${worker.status}`}>
                        {worker.status}
                      </span>
                    </td>
                    <td>{worker.tasks_processed}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="queues-section">
            <h3>Queue Depths</h3>
            <ul>
              {Object.entries(metrics.queues).map(([queue, depth]) => (
                <li key={queue}>
                  <span className="queue-name">{queue}</span>
                  <span className="queue-depth">{depth}</span>
                </li>
              ))}
            </ul>
          </div>
        </>
      )}
    </div>
  );
};

