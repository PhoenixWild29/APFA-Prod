/**
 * Knowledge Base Management Dashboard
 * 
 * Comprehensive admin dashboard for:
 * - Document management and analytics
 * - Processing history visualization
 * - Search performance metrics
 * - Storage utilization monitoring
 */
import React, { useState, useEffect } from 'react';
import DocumentTable from '@/components/admin/DocumentTable';
import ProcessingHistoryTimeline from '@/components/admin/ProcessingHistoryTimeline';
import SearchPerformanceCharts from '@/components/admin/SearchPerformanceCharts';
import StatisticsCards from '@/components/admin/StatisticsCards';
import FilterPanel from '@/components/admin/FilterPanel';
import StorageUtilization from '@/components/admin/StorageUtilization';
import ProcessingQueueStatus from '@/components/admin/ProcessingQueueStatus';
import { Button } from '@/components/ui/button';
import { Download } from 'lucide-react';

export default function KnowledgeBaseDashboard() {
  const [filters, setFilters] = useState({
    dateRange: { start: null, end: null },
    documentTypes: [],
    processingStatus: [],
    uploadedBy: null
  });

  const handleExport = async (format: 'csv' | 'json') => {
    // Call export API
    const response = await fetch(`/api/admin/dashboard/export?format=${format}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    });
    
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `knowledge-base-export-${Date.now()}.${format}`;
    a.click();
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Knowledge Base Dashboard</h1>
          <p className="text-muted-foreground">
            Manage and monitor your document knowledge base
          </p>
        </div>
        
        <div className="flex gap-2">
          <Button onClick={() => handleExport('csv')} variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Export CSV
          </Button>
          <Button onClick={() => handleExport('json')} variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Export JSON
          </Button>
        </div>
      </div>

      {/* Statistics Cards */}
      <StatisticsCards />

      {/* Filter Panel */}
      <FilterPanel filters={filters} onFilterChange={setFilters} />

      {/* Storage & Queue Status */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <StorageUtilization />
        <ProcessingQueueStatus />
      </div>

      {/* Search Performance Charts */}
      <SearchPerformanceCharts />

      {/* Processing History Timeline */}
      <ProcessingHistoryTimeline filters={filters} />

      {/* Document Table */}
      <DocumentTable filters={filters} />
    </div>
  );
}

