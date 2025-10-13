/**
 * Analytics Dashboard Page
 * 
 * Integrates all visualization components:
 * - Performance metrics
 * - Embedding throughput
 * - FAISS performance
 * - System resources
 */
import React, { useState, useEffect } from 'react';
import { PerformanceMetricsChart } from '../components/charts/PerformanceMetricsChart';
import { EmbeddingThroughputGraph } from '../components/charts/EmbeddingThroughputGraph';
import { FaissPerformanceChart } from '../components/charts/FaissPerformanceChart';
import { SystemResourceUtilizationChart } from '../components/charts/SystemResourceUtilizationChart';
import { TimeRangeSelector } from '../components/common/TimeRangeSelector';
import { ChartExportButton } from '../components/common/ChartExportButton';

export const AnalyticsDashboard: React.FC = () => {
  const [timeRange, setTimeRange] = useState({ start: new Date(), end: new Date(), preset: '1h' });
  const [performanceData, setPerformanceData] = useState([]);
  const [embeddingData, setEmbeddingData] = useState([]);
  const [faissData, setFaissData] = useState([]);
  const [resourceData, setResourceData] = useState([]);

  useEffect(() => {
    fetchChartData();
    const interval = setInterval(fetchChartData, 5000);
    return () => clearInterval(interval);
  }, [timeRange]);

  const fetchChartData = async () => {
    try {
      // Fetch from backend APIs
      // const perfResponse = await fetch('/api/analytics/performance');
      // setPerformanceData(await perfResponse.json());
      
      // Mock data for demonstration
      setPerformanceData(generateMockPerformanceData());
      setEmbeddingData(generateMockEmbeddingData());
      setFaissData(generateMockFaissData());
      setResourceData(generateMockResourceData());
    } catch (error) {
      console.error('Failed to fetch chart data:', error);
    }
  };

  return (
    <div className="analytics-dashboard">
      <header className="dashboard-header">
        <h1>Analytics Dashboard</h1>
        <TimeRangeSelector 
          onRangeChange={setTimeRange}
          defaultPreset="1h"
        />
      </header>

      <div className="charts-grid">
        <div className="chart-container">
          <PerformanceMetricsChart data={performanceData} />
          <ChartExportButton 
            chartId="performance-chart" 
            data={performanceData}
            filename="performance_metrics"
          />
        </div>

        <div className="chart-container">
          <EmbeddingThroughputGraph data={embeddingData} />
          <ChartExportButton 
            chartId="embedding-chart" 
            data={embeddingData}
            filename="embedding_throughput"
          />
        </div>

        <div className="chart-container">
          <FaissPerformanceChart data={faissData} />
          <ChartExportButton 
            chartId="faiss-chart" 
            data={faissData}
            filename="faiss_performance"
          />
        </div>

        <div className="chart-container">
          <SystemResourceUtilizationChart data={resourceData} />
          <ChartExportButton 
            chartId="resource-chart" 
            data={resourceData}
            filename="system_resources"
          />
        </div>
      </div>
    </div>
  );
};

// Mock data generators (remove in production)
function generateMockPerformanceData() {
  const now = Date.now();
  return Array.from({ length: 60 }, (_, i) => ({
    timestamp: new Date(now - (60 - i) * 1000).toISOString(),
    response_time_ms: 180 + Math.random() * 50,
    throughput_rps: 140 + Math.random() * 20,
    cpu_percent: 60 + Math.random() * 15,
    memory_percent: 40 + Math.random() * 10
  }));
}

function generateMockEmbeddingData() {
  const now = Date.now();
  return Array.from({ length: 30 }, (_, i) => ({
    timestamp: new Date(now - (30 - i) * 2000).toISOString(),
    embeddings_per_second: 20 + Math.random() * 10,
    total_embeddings: (i + 1) * 500,
    batch_size: 1000
  }));
}

function generateMockFaissData() {
  return [
    { index_name: 'IndexFlatIP', search_latency_ms: 45.2, accuracy_score: 0.92, vector_count: 100000 },
    { index_name: 'IndexIVFFlat', search_latency_ms: 38.5, accuracy_score: 0.89, vector_count: 500000 },
    { index_name: 'IndexIVFPQ', search_latency_ms: 22.0, accuracy_score: 0.85, vector_count: 1000000 }
  ];
}

function generateMockResourceData() {
  const now = Date.now();
  return Array.from({ length: 60 }, (_, i) => ({
    timestamp: new Date(now - (60 - i) * 1000).toISOString(),
    cpu_percent: 65 + Math.sin(i / 10) * 10,
    memory_percent: 42 + Math.cos(i / 15) * 8,
    disk_io_percent: 15 + Math.random() * 10
  }));
}

