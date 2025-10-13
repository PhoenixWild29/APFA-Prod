/**
 * Data Export Component
 * 
 * Allows administrators to:
 * - Download system metrics in CSV/JSON
 * - Export audit logs
 * - Configure export parameters
 */
import React, { useState } from 'react';
import axios from 'axios';

type ExportFormat = 'csv' | 'json';
type ExportType = 'metrics' | 'audit_logs' | 'celery_tasks' | 'cache_stats';

export const DataExporter: React.FC = () => {
  const [exportType, setExportType] = useState<ExportType>('metrics');
  const [exportFormat, setExportFormat] = useState<ExportFormat>('json');
  const [timeRange, setTimeRange] = useState('24h');
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    setExporting(true);
    
    try {
      const response = await axios.get('/admin/export', {
        params: {
          type: exportType,
          format: exportFormat,
          time_range: timeRange
        },
        responseType: 'blob'
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${exportType}_${timeRange}.${exportFormat}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      alert('Export completed successfully');
    } catch (error) {
      alert('Export failed: ' + error.message);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="data-exporter">
      <h2>Data Export</h2>
      
      <div className="export-form">
        <div className="form-group">
          <label>Export Type:</label>
          <select 
            value={exportType} 
            onChange={(e) => setExportType(e.target.value as ExportType)}
          >
            <option value="metrics">System Metrics</option>
            <option value="audit_logs">Audit Logs</option>
            <option value="celery_tasks">Celery Tasks</option>
            <option value="cache_stats">Cache Statistics</option>
          </select>
        </div>

        <div className="form-group">
          <label>Format:</label>
          <select 
            value={exportFormat} 
            onChange={(e) => setExportFormat(e.target.value as ExportFormat)}
          >
            <option value="json">JSON</option>
            <option value="csv">CSV</option>
          </select>
        </div>

        <div className="form-group">
          <label>Time Range:</label>
          <select 
            value={timeRange} 
            onChange={(e) => setTimeRange(e.target.value)}
          >
            <option value="1h">Last Hour</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
        </div>

        <button 
          onClick={handleExport}
          disabled={exporting}
          className="btn-primary"
        >
          {exporting ? 'Exporting...' : 'Export Data'}
        </button>
      </div>
    </div>
  );
};

