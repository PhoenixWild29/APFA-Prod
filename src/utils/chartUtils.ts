/**
 * Chart utility functions
 * 
 * Common functions for:
 * - Data transformation
 * - Currency formatting
 * - Timezone handling
 * - Chart export
 */

/**
 * Format currency with proper symbols and localization
 */
export const formatCurrency = (amount: number, currency: string = 'USD'): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(amount);
};

/**
 * Convert UTC timestamp to local timezone
 */
export const toLocalTimezone = (utcTimestamp: string): Date => {
  return new Date(utcTimestamp);
};

/**
 * Format timestamp for chart display
 */
export const formatChartTimestamp = (timestamp: string, format: 'time' | 'datetime' | 'date' = 'time'): string => {
  const date = new Date(timestamp);
  
  switch (format) {
    case 'time':
      return date.toLocaleTimeString();
    case 'date':
      return date.toLocaleDateString();
    case 'datetime':
      return date.toLocaleString();
    default:
      return timestamp;
  }
};

/**
 * Transform performance data for chart consumption
 */
export const transformPerformanceData = (rawData: any[]): any[] => {
  return rawData.map(item => ({
    ...item,
    timestamp: toLocalTimezone(item.timestamp),
    response_time_ms: parseFloat(item.response_time_ms || 0),
    cpu_percent: parseFloat(item.cpu_percent || 0),
    memory_percent: parseFloat(item.memory_percent || 0)
  }));
};

/**
 * Calculate average for metric array
 */
export const calculateAverage = (values: number[]): number => {
  if (values.length === 0) return 0;
  return values.reduce((sum, val) => sum + val, 0) / values.length;
};

/**
 * Calculate percentile for metric array
 */
export const calculatePercentile = (values: number[], percentile: number): number => {
  if (values.length === 0) return 0;
  
  const sorted = [...values].sort((a, b) => a - b);
  const index = Math.ceil((percentile / 100) * sorted.length) - 1;
  return sorted[Math.max(0, index)];
};

/**
 * Export chart as image (placeholder - requires html2canvas)
 */
export const exportChartAsPNG = async (elementId: string, filename: string): Promise<void> => {
  // In production, use html2canvas library
  console.log(`Export chart ${elementId} as ${filename}.png`);
  alert('Export functionality requires html2canvas library');
};

/**
 * Export data as CSV
 */
export const exportDataAsCSV = (data: any[], filename: string): void => {
  if (data.length === 0) return;
  
  const headers = Object.keys(data[0]);
  const csvContent = [
    headers.join(','),
    ...data.map(row => headers.map(h => row[h]).join(','))
  ].join('\n');
  
  const blob = new Blob([csvContent], { type: 'text/csv' });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${filename}.csv`;
  link.click();
  window.URL.revokeObjectURL(url);
};

/**
 * Export data as JSON
 */
export const exportDataAsJSON = (data: any[], filename: string): void => {
  const jsonContent = JSON.stringify(data, null, 2);
  const blob = new Blob([jsonContent], { type: 'application/json' });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${filename}.json`;
  link.click();
  window.URL.revokeObjectURL(url);
};

