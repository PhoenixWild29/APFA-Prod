/**
 * Statistics Cards Component
 * 
 * Displays document count statistics by type, status, and stage
 */
import React, { useState, useEffect } from 'react';
import { FileText, CheckCircle2, Clock, XCircle } from 'lucide-react';

interface Statistics {
  total_documents: number;
  by_type: Record<string, number>;
  by_status: Record<string, number>;
  by_stage: Record<string, number>;
}

export default function StatisticsCards() {
  const [stats, setStats] = useState<Statistics>({
    total_documents: 0,
    by_type: {},
    by_status: {},
    by_stage: {}
  });

  useEffect(() => {
    fetchStatistics();
  }, []);

  const fetchStatistics = async () => {
    try {
      const response = await fetch('/api/admin/dashboard/statistics', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error fetching statistics:', error);
    }
  };

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
      {/* Total Documents */}
      <div className="rounded-lg border bg-card p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">Total Documents</p>
            <p className="text-3xl font-bold">{stats.total_documents.toLocaleString()}</p>
          </div>
          <FileText className="h-8 w-8 text-blue-500" />
        </div>
      </div>

      {/* Completed */}
      <div className="rounded-lg border bg-card p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">Completed</p>
            <p className="text-3xl font-bold text-green-600">
              {(stats.by_status?.completed || 0).toLocaleString()}
            </p>
          </div>
          <CheckCircle2 className="h-8 w-8 text-green-500" />
        </div>
      </div>

      {/* Processing */}
      <div className="rounded-lg border bg-card p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">Processing</p>
            <p className="text-3xl font-bold text-blue-600">
              {(stats.by_status?.processing || 0).toLocaleString()}
            </p>
          </div>
          <Clock className="h-8 w-8 text-blue-500" />
        </div>
      </div>

      {/* Failed */}
      <div className="rounded-lg border bg-card p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">Failed</p>
            <p className="text-3xl font-bold text-red-600">
              {(stats.by_status?.failed || 0).toLocaleString()}
            </p>
          </div>
          <XCircle className="h-8 w-8 text-red-500" />
        </div>
      </div>

      {/* By Type */}
      <div className="col-span-full rounded-lg border bg-card p-6">
        <h3 className="mb-4 text-lg font-semibold">Documents by Type</h3>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {Object.entries(stats.by_type).map(([type, count]) => (
            <div key={type}>
              <p className="text-sm text-muted-foreground">{type}</p>
              <p className="text-2xl font-bold">{count}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

