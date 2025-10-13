/**
 * System Resource Utilization Dashboard
 * 
 * Real-time visualization of:
 * - CPU usage
 * - Memory usage
 * - Disk I/O
 */
import React from 'react';
import { ComposedChart, Line, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface SystemResourceProps {
  data: Array<{
    timestamp: string;
    cpu_percent: number;
    memory_percent: number;
    disk_io_percent: number;
  }>;
}

export const SystemResourceUtilizationChart: React.FC<SystemResourceProps> = ({ data }) => {
  const getStatusColor = (value: number): string => {
    if (value >= 90) return '#ff4d4d';
    if (value >= 75) return '#ffa500';
    return '#00c49f';
  };

  const latestData = data[data.length - 1];

  return (
    <div className="system-resource-chart">
      <h3>System Resource Utilization</h3>
      
      <div className="current-stats">
        <div className="stat-card" style={{ borderColor: getStatusColor(latestData?.cpu_percent || 0) }}>
          <label>CPU</label>
          <div className="value">{latestData?.cpu_percent.toFixed(1)}%</div>
        </div>
        <div className="stat-card" style={{ borderColor: getStatusColor(latestData?.memory_percent || 0) }}>
          <label>Memory</label>
          <div className="value">{latestData?.memory_percent.toFixed(1)}%</div>
        </div>
        <div className="stat-card" style={{ borderColor: getStatusColor(latestData?.disk_io_percent || 0) }}>
          <label>Disk I/O</label>
          <div className="value">{latestData?.disk_io_percent.toFixed(1)}%</div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={350}>
        <ComposedChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="timestamp"
            tickFormatter={(value) => new Date(value).toLocaleTimeString()}
          />
          <YAxis domain={[0, 100]} label={{ value: 'Utilization %', angle: -90, position: 'insideLeft' }} />
          <Tooltip 
            labelFormatter={(value) => new Date(value).toLocaleString()}
            formatter={(value: number) => value.toFixed(2) + '%'}
          />
          <Legend />
          <Area 
            type="monotone" 
            dataKey="cpu_percent" 
            fill="#8884d8" 
            stroke="#8884d8" 
            name="CPU %"
            fillOpacity={0.6}
          />
          <Line 
            type="monotone" 
            dataKey="memory_percent" 
            stroke="#82ca9d" 
            name="Memory %"
            strokeWidth={2}
          />
          <Line 
            type="monotone" 
            dataKey="disk_io_percent" 
            stroke="#ffc658" 
            name="Disk I/O %"
            strokeWidth={2}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

