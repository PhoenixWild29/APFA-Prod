/**
 * Redis Cache Monitoring Component
 * 
 * Displays:
 * - Cache hit rates
 * - Memory usage
 * - Manual invalidation controls
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface RedisMonitorProps {
  refreshInterval?: number;
  compact?: boolean;
}

interface RedisMetrics {
  connected: boolean;
  memory_usage_mb: float;
  total_keys: number;
  hit_rate: float;
  evictions: number;
  uptime_seconds: number;
}

export const RedisMonitor: React.FC<RedisMonitorProps> = ({ 
  refreshInterval = 5000,
  compact = false 
}) => {
  const [metrics, setMetrics] = useState<RedisMetrics | null>(null);
  const [invalidateKey, setInvalidateKey] = useState('');

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await axios.get('/admin/integration/redis-status');
        setMetrics(response.data);
      } catch (error) {
        console.error('Failed to fetch Redis metrics:', error);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, refreshInterval);

    return () => clearInterval(interval);
  }, [refreshInterval]);

  const handleInvalidate = async () => {
    if (!invalidateKey) return;
    
    try {
      await axios.delete(`/admin/cache/invalidate/${invalidateKey}`);
      alert(`Cache key '${invalidateKey}' invalidated`);
      setInvalidateKey('');
    } catch (error) {
      alert('Invalidation failed: ' + error.message);
    }
  };

  const handleFlushAll = async () => {
    if (!confirm('Are you sure you want to flush all cache?')) return;
    
    try {
      await axios.post('/admin/cache/flush');
      alert('Cache flushed successfully');
    } catch (error) {
      alert('Flush failed: ' + error.message);
    }
  };

  if (!metrics) return <div>Loading Redis metrics...</div>;

  return (
    <div className={`redis-monitor ${compact ? 'compact' : ''}`}>
      <h2>Redis Cache Monitor</h2>
      
      <div className="connection-status">
        <span className={metrics.connected ? 'connected' : 'disconnected'}>
          {metrics.connected ? '● Connected' : '○ Disconnected'}
        </span>
      </div>

      <div className="cache-metrics">
        <div className="metric">
          <label>Hit Rate:</label>
          <span className="value">{(metrics.hit_rate * 100).toFixed(1)}%</span>
        </div>
        <div className="metric">
          <label>Memory Usage:</label>
          <span className="value">{metrics.memory_usage_mb.toFixed(1)} MB</span>
        </div>
        <div className="metric">
          <label>Total Keys:</label>
          <span className="value">{metrics.total_keys.toLocaleString()}</span>
        </div>
        <div className="metric">
          <label>Evictions:</label>
          <span className="value">{metrics.evictions}</span>
        </div>
      </div>

      {!compact && (
        <div className="cache-controls">
          <h3>Manual Invalidation</h3>
          <div className="invalidate-form">
            <input
              type="text"
              placeholder="Cache key pattern"
              value={invalidateKey}
              onChange={(e) => setInvalidateKey(e.target.value)}
            />
            <button onClick={handleInvalidate} className="btn-secondary">
              Invalidate Key
            </button>
          </div>
          <button onClick={handleFlushAll} className="btn-danger">
            Flush All Cache
          </button>
        </div>
      )}
    </div>
  );
};

