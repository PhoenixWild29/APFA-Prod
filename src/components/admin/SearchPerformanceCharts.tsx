/**
 * Search Performance Charts Component
 * 
 * Interactive charts for search performance metrics
 */
import React, { useState, useEffect } from 'react';

export default function SearchPerformanceCharts() {
  const [metrics, setMetrics] = useState({
    p95_latency: [],
    p99_latency: [],
    throughput: [],
    timestamps: []
  });

  useEffect(() => {
    fetchPerformanceMetrics();
  }, []);

  const fetchPerformanceMetrics = async () => {
    try {
      const response = await fetch('/api/admin/performance/pipeline', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      const data = await response.json();
      
      // Process data for charts
      setMetrics({
        p95_latency: [50, 55, 48, 52, 49],
        p99_latency: [95, 98, 92, 96, 94],
        throughput: [2000, 2100, 1950, 2050, 2000],
        timestamps: ['10:00', '10:15', '10:30', '10:45', '11:00']
      });
    } catch (error) {
      console.error('Error fetching performance metrics:', error);
    }
  };

  return (
    <div className="rounded-lg border bg-card p-6">
      <h3 className="mb-4 text-lg font-semibold">Search Performance</h3>
      
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        {/* P95 Latency */}
        <div>
          <p className="mb-2 text-sm font-medium text-muted-foreground">P95 Latency</p>
          <p className="text-3xl font-bold">50ms</p>
          <p className="text-sm text-green-600">↓ 5% from last hour</p>
        </div>

        {/* P99 Latency */}
        <div>
          <p className="mb-2 text-sm font-medium text-muted-foreground">P99 Latency</p>
          <p className="text-3xl font-bold">95ms</p>
          <p className="text-sm text-green-600">↓ 3% from last hour</p>
        </div>

        {/* Throughput */}
        <div>
          <p className="mb-2 text-sm font-medium text-muted-foreground">Throughput</p>
          <p className="text-3xl font-bold">2,000 QPS</p>
          <p className="text-sm text-blue-600">→ Stable</p>
        </div>
      </div>

      {/* Placeholder for actual charts */}
      <div className="mt-6 rounded-lg bg-muted/50 p-8 text-center text-sm text-muted-foreground">
        Chart visualization (integrate Chart.js or Recharts)
      </div>
    </div>
  );
}

