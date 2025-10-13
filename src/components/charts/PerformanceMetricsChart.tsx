/**
 * Performance Metrics Chart Component
 * 
 * Interactive visualization for:
 * - System response times
 * - Throughput metrics
 * - Resource utilization
 */
import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface PerformanceMetricsChartProps {
  data: Array<{
    timestamp: string;
    response_time_ms: number;
    throughput_rps: number;
    cpu_percent: number;
    memory_percent: number;
  }>;
  height?: number;
}

export const PerformanceMetricsChart: React.FC<PerformanceMetricsChartProps> = ({ 
  data, 
  height = 400 
}) => {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey="timestamp" 
          tickFormatter={(value) => new Date(value).toLocaleTimeString()}
        />
        <YAxis yAxisId="left" />
        <YAxis yAxisId="right" orientation="right" />
        <Tooltip 
          labelFormatter={(value) => new Date(value).toLocaleString()}
          formatter={(value: number) => value.toFixed(2)}
        />
        <Legend />
        <Line 
          yAxisId="left"
          type="monotone" 
          dataKey="response_time_ms" 
          stroke="#8884d8" 
          name="Response Time (ms)"
          strokeWidth={2}
        />
        <Line 
          yAxisId="left"
          type="monotone" 
          dataKey="throughput_rps" 
          stroke="#82ca9d" 
          name="Throughput (req/s)"
          strokeWidth={2}
        />
        <Line 
          yAxisId="right"
          type="monotone" 
          dataKey="cpu_percent" 
          stroke="#ffc658" 
          name="CPU %"
          strokeWidth={2}
        />
        <Line 
          yAxisId="right"
          type="monotone" 
          dataKey="memory_percent" 
          stroke="#ff7c7c" 
          name="Memory %"
          strokeWidth={2}
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

