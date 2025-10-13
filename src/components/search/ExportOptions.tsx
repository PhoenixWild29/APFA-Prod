/**
 * Export Options Component
 * 
 * Individual and bulk document export
 */
import React from 'react';
import { Button } from '@/components/ui/button';
import { Download, FileDown } from 'lucide-react';

interface ExportOptionsProps {
  searchQuery: string;
  filters: any;
}

export default function ExportOptions({ searchQuery, filters }: ExportOptionsProps) {
  const handleBulkExport = async (format: 'csv' | 'json') => {
    try {
      const response = await fetch(
        `/api/admin/dashboard/export?format=${format}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        }
      );
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `search-results-${Date.now()}.${format}`;
      a.click();
    } catch (error) {
      console.error('Error exporting:', error);
    }
  };

  return (
    <div className="flex gap-2">
      <Button variant="outline" size="sm" onClick={() => handleBulkExport('csv')}>
        <FileDown className="mr-2 h-4 w-4" />
        Export CSV
      </Button>
      <Button variant="outline" size="sm" onClick={() => handleBulkExport('json')}>
        <FileDown className="mr-2 h-4 w-4" />
        Export JSON
      </Button>
    </div>
  );
}

