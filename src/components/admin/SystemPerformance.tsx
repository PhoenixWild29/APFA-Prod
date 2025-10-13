/**
 * System Performance Monitoring Component
 * 
 * Displays:
 * - CPU usage
 * - Memory usage
 * - Response time metrics
 * - Drill-down capabilities
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface SystemPerformanceProps {
  refreshInterval?: number;
}

interface PerformanceMetrics {
  cpu_percent: number;
  memory_mb: number;
  memory_percent: number;
  avg_response_time_ms: number;
  p95_response_time_ms: number;
  active_requests: number;
  requests_per_second: number;
}

export const SystemPerformance: React.FC<SystemPerformanceProps> = ({ 
  refreshInterval = 2000 
}) => {
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const [history, setHistory] = useState<PerformanceMetrics[]>([]);
  const [showDrilldown, setShowDrilldown] = useState(false);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await axios.get('/admin/performance/pipeline');
        const data = response.data;
        
        setMetrics(data);
        setHistory(prev => [...prev.slice(-59), data]); // Keep last 60 samples
      } catch (error) {
        console.error('Failed to fetch performance metrics:', error);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, refreshInterval);

    return () => clearInterval(interval);
  }, [refreshInterval]);

  if (!metrics) return <div>Loading performance metrics...</div>;

  const isHealthy = (metric: string, value: number): boolean => {
    switch (metric) {
      case 'cpu': return value < 80;
      case 'memory': return value < 85;
      case 'response_time': return value < 3000;
      default: return true;
    }
  };

  return (
    <div className="system-performance">
      <h2>System Performance</h2>
      
      <div className="performance-grid">
        <div className={`metric-card ${isHealthy('cpu', metrics.cpu_percent) ? '' : 'warning'}`}>
          <h3>CPU Usage</h3>
          <div className="value">{metrics.cpu_percent.toFixed(1)}%</div>
          <div className="threshold">Threshold: 80%</div>
        </div>

        <div className={`metric-card ${isHealthy('memory', metrics.memory_percent) ? '' : 'warning'}`}>
          <h3>Memory Usage</h3>
          <div className="value">{metrics.memory_mb.toFixed(0)} MB</div>
          <div className="percentage">({metrics.memory_percent.toFixed(1)}%)</div>
        </div>

        <div className={`metric-card ${isHealthy('response_time', metrics.avg_response_time_ms) ? '' : 'warning'}`}>
          <h3>Avg Response Time</h3>
          <div className="value">{metrics.avg_response_time_ms.toFixed(0)} ms</div>
          <div className="p95">P95: {metrics.p95_response_time_ms.toFixed(0)} ms</div>
        </div>

        <div className="metric-card">
          <h3>Active Requests</h3>
          <div className="value">{metrics.active_requests}</div>
          <div className="rate">{metrics.requests_per_second.toFixed(1)} req/s</div>
        </div>
      </div>

      <button 
        onClick={() => setShowDrilldown(!showDrilldown)}
        className="btn-secondary"
      >
        {showDrilldown ? 'Hide' : 'Show'} Detailed Metrics
      </button>

      {showDrilldown && (
        <div className="drilldown-section">
          <h3>Performance History (Last 60s)</h3>
          <div className="mini-chart">
            {history.map((h, idx) => (
              <div 
                key={idx} 
                className="bar" 
                style={{ height: `${h.cpu_percent}%` }}
                title={`CPU: ${h.cpu_percent.toFixed(1)}%`}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

