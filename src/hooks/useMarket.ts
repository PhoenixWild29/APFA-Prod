import { useQuery } from '@tanstack/react-query';
import {
  fetchDashboardSummary,
  fetchMarketHistory,
  fetchLatestInsight,
} from '@/api/marketApi';

export function useDashboardSummary() {
  return useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: fetchDashboardSummary,
    staleTime: 60_000,
    refetchInterval: 120_000,
  });
}

export function useMarketHistory(
  ticker: string,
  dataType = 'quote',
  days = 30,
  enabled = true
) {
  return useQuery({
    queryKey: ['market-history', ticker, dataType, days],
    queryFn: () => fetchMarketHistory(ticker, dataType, days),
    staleTime: 300_000,
    enabled,
  });
}

export function useLatestInsight() {
  return useQuery({
    queryKey: ['latest-insight'],
    queryFn: fetchLatestInsight,
    staleTime: 60_000,
  });
}
