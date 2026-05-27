import apiClient from '@/api/apiClient';

export interface BillingStatus {
  tier: 'free' | 'pro' | 'enterprise';
  query_count_this_period: number;
  limit: number;
  billing_period_start: string | null;
  usage_percentage: number;
  has_subscription: boolean;
}

export async function fetchBillingStatus(): Promise<BillingStatus> {
  const { data } = await apiClient.get<BillingStatus>('/api/billing/status');
  return data;
}

export async function createCheckoutSession(tier: 'pro' | 'enterprise'): Promise<string> {
  const { data } = await apiClient.post<{ checkout_url: string }>(
    '/api/billing/checkout',
    { tier },
  );
  return data.checkout_url;
}

export async function createPortalSession(): Promise<string> {
  const { data } = await apiClient.post<{ portal_url: string }>(
    '/api/billing/portal',
  );
  return data.portal_url;
}
