import { useQuery } from '@tanstack/react-query';
import { fetchBillingStatus } from '@/api/billingApi';

export function useBillingStatus() {
  return useQuery({
    queryKey: ['billing-status'],
    queryFn: fetchBillingStatus,
    staleTime: 30_000,
    refetchInterval: 60_000,
  });
}
