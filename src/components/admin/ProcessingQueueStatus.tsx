/**
 * Processing Queue Status Component
 * 
 * Displays real-time processing queue metrics
 */
import React, { useState, useEffect } from 'react';
import { Activity } from 'lucide-react';

export default function ProcessingQueueStatus() {
  const [queueStatus, setQueueStatus] = useState({
    active_workers: 0,
    queue_depths: {
      embedding: 0,
      indexing: 0,
      admin_jobs: 0
    },
    total_queued: 0,
    processing_rate: 0
  });

  useEffect(() => {
    fetchQueueStatus();
    const interval = setInterval(fetchQueueStatus, 5000); // Update every 5s
    return () => clearInterval(interval);
  }, []);

  const fetchQueueStatus = async () => {
    try {
      const response = await fetch('/api/admin/integration/celery-status', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      const data = await response.json();
      
      const total = Object.values(data.queue_depths || {}).reduce((sum: number, count: any) => sum + count, 0);
      
      setQueueStatus({
        active_workers: data.active_workers || 0,
        queue_depths: data.queue_depths || {},
        total_queued: total,
        processing_rate: data.task_execution_stats?.throughput || 0
      });
    } catch (error) {
      console.error('Error fetching queue status:', error);
    }
  };

  return (
    <div className="rounded-lg border bg-card p-6">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold">Processing Queue</h3>
        <Activity className="h-6 w-6 text-muted-foreground" />
      </div>

      {/* Worker Status */}
      <div className="mb-4 flex items-center justify-between rounded-lg bg-muted/50 p-3">
        <span className="text-sm font-medium">Active Workers</span>
        <span className="text-2xl font-bold text-green-600">
          {queueStatus.active_workers}
        </span>
      </div>

      {/* Queue Depths */}
      <div className="space-y-3">
        <h4 className="text-sm font-semibold">Queue Depths</h4>
        
        {Object.entries(queueStatus.queue_depths).map(([queue, depth]) => (
          <div key={queue} className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground capitalize">{queue}:</span>
            <span className="font-medium">{depth} tasks</span>
          </div>
        ))}
        
        <div className="border-t pt-3">
          <div className="flex items-center justify-between font-semibold">
            <span>Total Queued:</span>
            <span className="text-blue-600">{queueStatus.total_queued} tasks</span>
          </div>
        </div>
      </div>
    </div>
  );
}

