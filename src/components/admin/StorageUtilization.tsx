/**
 * Storage Utilization Component
 * 
 * Displays real-time storage metrics
 */
import React, { useState, useEffect } from 'react';
import { HardDrive } from 'lucide-react';

export default function StorageUtilization() {
  const [storage, setStorage] = useState({
    used_gb: 0,
    total_gb: 0,
    utilization_percent: 0,
    documents_count: 0,
    embeddings_count: 0,
    indexes_count: 0
  });

  useEffect(() => {
    fetchStorageMetrics();
    const interval = setInterval(fetchStorageMetrics, 30000); // Update every 30s
    return () => clearInterval(interval);
  }, []);

  const fetchStorageMetrics = async () => {
    try {
      const response = await fetch('/api/admin/integration/minio-status', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      const data = await response.json();
      
      setStorage({
        used_gb: data.total_storage_gb - data.available_storage_gb || 0,
        total_gb: data.total_storage_gb || 1000,
        utilization_percent: data.storage_utilization_percent || 0,
        documents_count: data.total_objects || 0,
        embeddings_count: 0,
        indexes_count: 0
      });
    } catch (error) {
      console.error('Error fetching storage metrics:', error);
    }
  };

  return (
    <div className="rounded-lg border bg-card p-6">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold">Storage Utilization</h3>
        <HardDrive className="h-6 w-6 text-muted-foreground" />
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="mb-2 flex items-center justify-between text-sm">
          <span>{storage.used_gb.toFixed(1)} GB used</span>
          <span className="font-semibold">{storage.utilization_percent.toFixed(1)}%</span>
        </div>
        <div className="h-3 w-full overflow-hidden rounded-full bg-secondary">
          <div
            className={`h-full transition-all duration-300 ${
              storage.utilization_percent > 80 ? 'bg-red-500' :
              storage.utilization_percent > 60 ? 'bg-yellow-500' :
              'bg-green-500'
            }`}
            style={{ width: `${storage.utilization_percent}%` }}
          />
        </div>
      </div>

      {/* Storage Breakdown */}
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-muted-foreground">Total Objects:</span>
          <span className="font-medium">{storage.documents_count.toLocaleString()}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Available:</span>
          <span className="font-medium">
            {(storage.total_gb - storage.used_gb).toFixed(1)} GB
          </span>
        </div>
      </div>
    </div>
  );
}

