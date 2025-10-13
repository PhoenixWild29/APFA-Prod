/**
 * Chart Export Button Component
 * 
 * Reusable export functionality for:
 * - PNG export
 * - SVG export
 * - PDF export
 */
import React, { useState } from 'react';
import { exportChartAsPNG, exportDataAsCSV, exportDataAsJSON } from '../../utils/chartUtils';

interface ChartExportButtonProps {
  chartId: string;
  data: any[];
  filename: string;
}

export const ChartExportButton: React.FC<ChartExportButtonProps> = ({ 
  chartId, 
  data, 
  filename 
}) => {
  const [showMenu, setShowMenu] = useState(false);

  const handleExport = async (format: 'png' | 'csv' | 'json') => {
    switch (format) {
      case 'png':
        await exportChartAsPNG(chartId, filename);
        break;
      case 'csv':
        exportDataAsCSV(data, filename);
        break;
      case 'json':
        exportDataAsJSON(data, filename);
        break;
    }
    setShowMenu(false);
  };

  return (
    <div className="chart-export-button">
      <button 
        onClick={() => setShowMenu(!showMenu)}
        className="btn-secondary"
      >
        📥 Export
      </button>
      
      {showMenu && (
        <div className="export-menu">
          <button onClick={() => handleExport('png')}>
            Export as PNG
          </button>
          <button onClick={() => handleExport('csv')}>
            Export as CSV
          </button>
          <button onClick={() => handleExport('json')}>
            Export as JSON
          </button>
        </div>
      )}
    </div>
  );
};

