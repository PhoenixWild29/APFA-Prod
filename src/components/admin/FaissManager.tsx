/**
 * FAISS Index Management Component
 * 
 * Provides:
 * - Index status and performance metrics
 * - Hot-swap controls
 * - Migration readiness assessment
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface FaissManagerProps {
  refreshInterval?: number;
  compact?: boolean;
}

interface FaissIndexStatus {
  index_type: string;
  vector_count: number;
  memory_usage_mb: float;
  search_latency_p95_ms: float;
  hot_swap_ready: boolean;
  migration_readiness: {
    can_migrate: boolean;
    readiness_score: float;
    blocking_issues: string[];
  };
}

export const FaissManager: React.FC<FaissManagerProps> = ({ 
  refreshInterval = 10000,
  compact = false 
}) => {
  const [status, setStatus] = useState<FaissIndexStatus | null>(null);
  const [swapping, setSwapping] = useState(false);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await axios.get('/admin/index/status');
        setStatus(response.data);
      } catch (error) {
        console.error('Failed to fetch FAISS status:', error);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, refreshInterval);

    return () => clearInterval(interval);
  }, [refreshInterval]);

  const handleHotSwap = async () => {
    setSwapping(true);
    try {
      await axios.post('/admin/index/hot-swap', { index_version: 'latest' });
      alert('Hot-swap initiated successfully');
    } catch (error) {
      alert('Hot-swap failed: ' + error.message);
    } finally {
      setSwapping(false);
    }
  };

  if (!status) return <div>Loading FAISS index status...</div>;

  return (
    <div className={`faiss-manager ${compact ? 'compact' : ''}`}>
      <h2>FAISS Index Management</h2>
      
      <div className="index-stats">
        <div className="stat">
          <label>Index Type:</label>
          <span>{status.index_type}</span>
        </div>
        <div className="stat">
          <label>Vector Count:</label>
          <span>{status.vector_count.toLocaleString()}</span>
        </div>
        <div className="stat">
          <label>Memory:</label>
          <span>{status.memory_usage_mb.toFixed(1)} MB</span>
        </div>
        <div className="stat">
          <label>P95 Latency:</label>
          <span>{status.search_latency_p95_ms.toFixed(1)} ms</span>
        </div>
      </div>

      {!compact && (
        <>
          <div className="hot-swap-section">
            <h3>Hot-Swap Control</h3>
            <button
              onClick={handleHotSwap}
              disabled={!status.hot_swap_ready || swapping}
              className="btn-primary"
            >
              {swapping ? 'Swapping...' : 'Initiate Hot-Swap'}
            </button>
            <span className={`status ${status.hot_swap_ready ? 'ready' : 'not-ready'}`}>
              {status.hot_swap_ready ? '✓ Ready' : '✗ Not Ready'}
            </span>
          </div>

          <div className="migration-section">
            <h3>Migration Readiness</h3>
            <div className="readiness-score">
              Score: {(status.migration_readiness.readiness_score * 100).toFixed(0)}%
            </div>
            {status.migration_readiness.can_migrate ? (
              <div className="can-migrate">✓ Ready for migration</div>
            ) : (
              <div className="blocking-issues">
                <h4>Blocking Issues:</h4>
                <ul>
                  {status.migration_readiness.blocking_issues.map((issue, idx) => (
                    <li key={idx}>{issue}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

