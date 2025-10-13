/**
 * FAISS Index Performance Comparison Chart
 * 
 * Visualizes:
 * - Search latency across indices
 * - Accuracy metrics
 * - Comparative performance
 */
import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';

interface FaissPerformanceProps {
  data: Array<{
    index_name: string;
    search_latency_ms: number;
    accuracy_score: number;
    vector_count: number;
  }>;
}

export const FaissPerformanceChart: React.FC<FaissPerformanceProps> = ({ data }) => {
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  return (
    <div className="faiss-performance-chart">
      <h3>FAISS Index Performance Comparison</h3>
      
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="index_name" />
          <YAxis yAxisId="left" label={{ value: 'Latency (ms)', angle: -90, position: 'insideLeft' }} />
          <YAxis yAxisId="right" orientation="right" label={{ value: 'Accuracy', angle: 90, position: 'insideRight' }} />
          <Tooltip />
          <Legend />
          <Bar yAxisId="left" dataKey="search_latency_ms" name="Search Latency (ms)">
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Bar>
          <Bar yAxisId="right" dataKey="accuracy_score" name="Accuracy Score" fill="#82ca9d" />
        </BarChart>
      </ResponsiveContainer>
      
      <div className="performance-table">
        <table>
          <thead>
            <tr>
              <th>Index</th>
              <th>Vectors</th>
              <th>Latency</th>
              <th>Accuracy</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row, idx) => (
              <tr key={idx}>
                <td>{row.index_name}</td>
                <td>{row.vector_count.toLocaleString()}</td>
                <td>{row.search_latency_ms.toFixed(2)} ms</td>
                <td>{(row.accuracy_score * 100).toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

