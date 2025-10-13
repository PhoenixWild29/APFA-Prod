/**
 * Filter Panel Component
 * 
 * Provides filtering controls for dashboard data
 */
import React from 'react';
import { Button } from '@/components/ui/button';

interface FilterPanelProps {
  filters: any;
  onFilterChange: (filters: any) => void;
}

export default function FilterPanel({ filters, onFilterChange }: FilterPanelProps) {
  return (
    <div className="rounded-lg border bg-card p-4">
      <h3 className="mb-4 font-semibold">Filters</h3>
      
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        {/* Date Range */}
        <div>
          <label className="mb-2 block text-sm font-medium">Date Range</label>
          <div className="flex gap-2">
            <input
              type="date"
              className="w-full rounded-md border bg-background px-3 py-2 text-sm"
              onChange={(e) => onFilterChange({
                ...filters,
                dateRange: { ...filters.dateRange, start: e.target.value }
              })}
            />
            <input
              type="date"
              className="w-full rounded-md border bg-background px-3 py-2 text-sm"
              onChange={(e) => onFilterChange({
                ...filters,
                dateRange: { ...filters.dateRange, end: e.target.value }
              })}
            />
          </div>
        </div>

        {/* Document Type */}
        <div>
          <label className="mb-2 block text-sm font-medium">Document Type</label>
          <select
            className="w-full rounded-md border bg-background px-3 py-2 text-sm"
            onChange={(e) => onFilterChange({
              ...filters,
              documentTypes: e.target.value ? [e.target.value] : []
            })}
          >
            <option value="">All Types</option>
            <option value="pdf">PDF</option>
            <option value="docx">Word</option>
            <option value="txt">Text</option>
            <option value="csv">CSV</option>
          </select>
        </div>

        {/* Processing Status */}
        <div>
          <label className="mb-2 block text-sm font-medium">Status</label>
          <select
            className="w-full rounded-md border bg-background px-3 py-2 text-sm"
            onChange={(e) => onFilterChange({
              ...filters,
              processingStatus: e.target.value ? [e.target.value] : []
            })}
          >
            <option value="">All Statuses</option>
            <option value="completed">Completed</option>
            <option value="processing">Processing</option>
            <option value="failed">Failed</option>
            <option value="pending">Pending</option>
          </select>
        </div>

        {/* Actions */}
        <div className="flex items-end">
          <Button
            onClick={() => onFilterChange({
              dateRange: { start: null, end: null },
              documentTypes: [],
              processingStatus: [],
              uploadedBy: null
            })}
            variant="outline"
            className="w-full"
          >
            Clear Filters
          </Button>
        </div>
      </div>
    </div>
  );
}

