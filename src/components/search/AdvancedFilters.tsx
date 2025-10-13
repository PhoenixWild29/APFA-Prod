/**
 * Advanced Filters Component
 * 
 * Faceted search with count indicators
 */
import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';

interface AdvancedFiltersProps {
  filters: any;
  onFilterChange: (filters: any) => void;
}

export default function AdvancedFilters({ filters, onFilterChange }: AdvancedFiltersProps) {
  const [facets, setFacets] = useState({
    documentTypes: {
      'PDF': 8500,
      'Word': 4200,
      'Text': 2100,
      'CSV': 620
    },
    processingStatus: {
      'completed': 14850,
      'processing': 420,
      'failed': 150
    }
  });

  return (
    <div className="grid grid-cols-1 gap-4 rounded-lg border bg-card p-4 md:grid-cols-4">
      {/* Document Type */}
      <div>
        <h3 className="mb-3 text-sm font-semibold">Document Type</h3>
        <div className="space-y-2">
          {Object.entries(facets.documentTypes).map(([type, count]) => (
            <label key={type} className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                className="rounded"
                checked={filters.documentType?.includes(type)}
                onChange={(e) => {
                  const newTypes = e.target.checked
                    ? [...(filters.documentType || []), type]
                    : (filters.documentType || []).filter((t: string) => t !== type);
                  onFilterChange({ ...filters, documentType: newTypes });
                }}
              />
              <span>{type}</span>
              <span className="ml-auto text-muted-foreground">({count})</span>
            </label>
          ))}
        </div>
      </div>

      {/* Processing Status */}
      <div>
        <h3 className="mb-3 text-sm font-semibold">Status</h3>
        <div className="space-y-2">
          {Object.entries(facets.processingStatus).map(([status, count]) => (
            <label key={status} className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                className="rounded"
                checked={filters.processingStatus?.includes(status)}
                onChange={(e) => {
                  const newStatuses = e.target.checked
                    ? [...(filters.processingStatus || []), status]
                    : (filters.processingStatus || []).filter((s: string) => s !== status);
                  onFilterChange({ ...filters, processingStatus: newStatuses });
                }}
              />
              <span className="capitalize">{status}</span>
              <span className="ml-auto text-muted-foreground">({count})</span>
            </label>
          ))}
        </div>
      </div>

      {/* Upload Date Range */}
      <div>
        <h3 className="mb-3 text-sm font-semibold">Upload Date</h3>
        <div className="space-y-2">
          <input
            type="date"
            className="w-full rounded-md border bg-background px-3 py-2 text-sm"
            onChange={(e) => onFilterChange({
              ...filters,
              uploadDateRange: { ...filters.uploadDateRange, start: e.target.value }
            })}
          />
          <input
            type="date"
            className="w-full rounded-md border bg-background px-3 py-2 text-sm"
            onChange={(e) => onFilterChange({
              ...filters,
              uploadDateRange: { ...filters.uploadDateRange, end: e.target.value }
            })}
          />
        </div>
      </div>

      {/* Clear Filters */}
      <div className="flex items-end">
        <Button
          variant="outline"
          className="w-full"
          onClick={() => onFilterChange({
            documentType: [],
            uploadDateRange: { start: null, end: null },
            processingStatus: [],
            customTags: []
          })}
        >
          Clear All Filters
        </Button>
      </div>
    </div>
  );
}

