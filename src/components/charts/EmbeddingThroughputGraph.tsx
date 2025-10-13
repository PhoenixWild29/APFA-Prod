/**
 * Embedding Generation Throughput Graph
 * 
 * Real-time visualization with:
 * - Processing rates over time
 * - Zoom and pan capabilities
 * - Interactive tooltips
 */
import React, { useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Brush } from 'recharts';

interface EmbeddingThroughputProps {
  data: Array<{
    timestamp: string;
    embeddings_per_second: number;
    total_embeddings: number;
    batch_size: number;
  }>;
}

export const EmbeddingThroughputGraph: React.FC<EmbeddingThroughputProps> = ({ data }) => {
  const [zoomDomain, setZoomDomain] = useState<[number, number] | null>(null);

  return (
    <div className="embedding-throughput-chart">
      <h3>Embedding Generation Throughput</h3>
      <ResponsiveContainer width="100%" height={400}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="colorThroughput" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#8884d8" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="timestamp"
            tickFormatter={(value) => new Date(value).toLocaleTimeString()}
          />
          <YAxis label={{ value: 'Embeddings/sec', angle: -90, position: 'insideLeft' }} />
          <Tooltip 
            labelFormatter={(value) => new Date(value).toLocaleString()}
            formatter={(value: number) => [value.toFixed(2), 'Embeddings/sec']}
          />
          <Area 
            type="monotone" 
            dataKey="embeddings_per_second" 
            stroke="#8884d8" 
            fillOpacity={1} 
            fill="url(#colorThroughput)" 
          />
          <Brush 
            dataKey="timestamp" 
            height={30} 
            stroke="#8884d8"
            tickFormatter={(value) => new Date(value).toLocaleTimeString()}
          />
        </AreaChart>
      </ResponsiveContainer>
      
      <div className="chart-stats">
        <span>Total Embeddings: {data[data.length - 1]?.total_embeddings || 0}</span>
        <span>Avg Batch Size: {(data.reduce((sum, d) => sum + d.batch_size, 0) / data.length).toFixed(0)}</span>
      </div>
    </div>
  );
};

