/**
 * Batch Processing Progress Tracker
 * 
 * Displays:
 * - Visual progress bars for active batches
 * - Estimated completion times
 * - Processing statistics
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface BatchProgressTrackerProps {
  refreshInterval?: number;
}

interface BatchJob {
  batch_id: string;
  total_documents: number;
  processed_documents: number;
  failed_documents: number;
  progress_percentage: number;
  estimated_completion: string | null;
  status: string;
}

export const BatchProgressTracker: React.FC<BatchProgressTrackerProps> = ({ 
  refreshInterval = 3000 
}) => {
  const [batches, setBatches] = useState<BatchJob[]>([]);

  useEffect(() => {
    const fetchBatches = async () => {
      try {
        // In production, fetch active batches from API
        const response = await axios.get('/admin/documents/active-batches');
        setBatches(response.data.batches || []);
      } catch (error) {
        console.error('Failed to fetch batch progress:', error);
      }
    };

    fetchBatches();
    const interval = setInterval(fetchBatches, refreshInterval);

    return () => clearInterval(interval);
  }, [refreshInterval]);

  return (
    <div className="batch-progress-tracker">
      <h2>Batch Processing Progress</h2>
      
      {batches.length === 0 && (
        <div className="no-batches">No active batch jobs</div>
      )}

      {batches.map((batch) => (
        <div key={batch.batch_id} className="batch-item">
          <div className="batch-header">
            <span className="batch-id">{batch.batch_id}</span>
            <span className={`batch-status ${batch.status}`}>{batch.status}</span>
          </div>
          
          <div className="progress-bar-container">
            <div 
              className="progress-bar" 
              style={{ width: `${batch.progress_percentage}%` }}
            />
          </div>
          
          <div className="batch-stats">
            <span>{batch.processed_documents} / {batch.total_documents} processed</span>
            <span>{batch.progress_percentage.toFixed(1)}% complete</span>
            {batch.failed_documents > 0 && (
              <span className="error">{batch.failed_documents} failed</span>
            )}
          </div>
          
          {batch.estimated_completion && (
            <div className="estimated-completion">
              Est. completion: {new Date(batch.estimated_completion).toLocaleTimeString()}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

