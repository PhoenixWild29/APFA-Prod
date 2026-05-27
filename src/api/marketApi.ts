import apiClient from '@/api/apiClient';

export interface MarketQuote {
  ticker: string;
  price: number;
  change_pct: number | null;
  open: number | null;
  high: number | null;
  low: number | null;
  prev_close: number | null;
  updated_at: string;
  is_stale: boolean;
}

export interface EconomicIndicator {
  code: string;
  name: string;
  value: number;
  unit: string;
  updated_at: string;
  is_stale: boolean;
}

export interface DashboardSummary {
  quotes: MarketQuote[];
  indicators: EconomicIndicator[];
  last_updated: string | null;
  staleness_warning: string | null;
}

export interface MarketHistoryPoint {
  date: string;
  value: number;
  change_pct: number | null;
}

export interface MarketHistoryResponse {
  ticker: string;
  data_type: string;
  points: MarketHistoryPoint[];
  total_points: number;
}

export interface LatestInsight {
  preview: string;
  conversation_id: string;
  created_at: string;
  has_more: boolean;
}

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  const { data } = await apiClient.get<DashboardSummary>(
    '/market/dashboard-summary'
  );
  return data;
}

export async function fetchMarketHistory(
  ticker: string,
  dataType = 'quote',
  days = 30
): Promise<MarketHistoryResponse> {
  const { data } = await apiClient.get<MarketHistoryResponse>(
    '/market/history',
    { params: { ticker, data_type: dataType, days } }
  );
  return data;
}

export async function fetchLatestInsight(): Promise<LatestInsight | null> {
  const { data } = await apiClient.get<LatestInsight | null>(
    '/market/latest-insight'
  );
  return data;
}
