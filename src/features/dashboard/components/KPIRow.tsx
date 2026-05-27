import { AlertCircle } from 'lucide-react';
import { useDashboardSummary } from '@/hooks/useMarket';
import KPICard from './KPICard';
import { Skeleton } from '@/components/ui/skeleton';

const TICKER_LABELS: Record<string, string> = {
  SPY: 'S&P 500',
  QQQ: 'NASDAQ 100',
  DIA: 'Dow Jones',
  TLT: '20Y Treasury',
};

const INDICATOR_CODES = ['FEDFUNDS', 'MORTGAGE30US', 'UNRATE'];
const INDICATOR_LABELS: Record<string, string> = {
  FEDFUNDS: 'Fed Funds Rate',
  MORTGAGE30US: '30Y Mortgage',
  UNRATE: 'Unemployment',
};

const TICKER_COLORS: Record<string, string> = {
  SPY: '#1D8A84',
  QQQ: '#18A06B',
  DIA: '#C79A2B',
  TLT: '#7E8989',
};

function formatPrice(value: number): string {
  return value.toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function formatPct(value: number | null): string {
  if (value == null) return '';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

export default function KPIRow() {
  const { data, isLoading, isError } = useDashboardSummary();

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="rounded-xl border bg-card p-4">
            <Skeleton className="mb-2 h-3 w-20" />
            <Skeleton className="h-7 w-24" />
          </div>
        ))}
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="flex items-center gap-2 rounded-xl border bg-card p-4 text-sm text-muted-foreground">
        <AlertCircle className="h-4 w-4" />
        Market data unavailable
      </div>
    );
  }

  const spyQuote = data.quotes.find((q) => q.ticker === 'SPY');

  const selectedIndicators = INDICATOR_CODES.map((code) =>
    data.indicators.find((i) => i.code === code)
  ).filter(Boolean);

  const kpis: Array<{
    label: string;
    value: string;
    delta?: { value: string; direction: 'up' | 'down' | 'flat' };
    color: string;
    isStale: boolean;
  }> = [];

  if (spyQuote) {
    kpis.push({
      label: TICKER_LABELS[spyQuote.ticker] ?? spyQuote.ticker,
      value: formatPrice(spyQuote.price),
      delta: spyQuote.change_pct != null
        ? {
            value: formatPct(spyQuote.change_pct),
            direction: spyQuote.change_pct >= 0 ? 'up' : spyQuote.change_pct < 0 ? 'down' : 'flat',
          }
        : undefined,
      color: TICKER_COLORS[spyQuote.ticker] ?? '#1D8A84',
      isStale: spyQuote.is_stale,
    });
  }

  for (const ind of selectedIndicators) {
    if (!ind) continue;
    kpis.push({
      label: INDICATOR_LABELS[ind.code] ?? ind.name,
      value: `${ind.value}${ind.unit}`,
      color: '#7E8989',
      isStale: ind.is_stale,
    });
  }

  return (
    <div className="space-y-1">
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {kpis.map((kpi) => (
          <div key={kpi.label} className="relative">
            <KPICard
              label={kpi.label}
              value={kpi.value}
              delta={kpi.delta}
              color={kpi.color}
            />
            {kpi.isStale && (
              <span className="absolute right-2 top-2 rounded bg-amber-100 px-1.5 py-0.5 text-[9px] font-medium text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
                Delayed
              </span>
            )}
          </div>
        ))}
      </div>
      {data.staleness_warning && (
        <p className="flex items-center gap-1 text-[10px] text-muted-foreground">
          <AlertCircle className="h-3 w-3" />
          {data.staleness_warning}
        </p>
      )}
    </div>
  );
}
