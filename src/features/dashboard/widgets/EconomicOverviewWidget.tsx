import { AlertCircle } from 'lucide-react';
import { useDashboardSummary } from '@/hooks/useMarket';
import WidgetCard from '../components/WidgetCard';
import type { WidgetId } from '@/store/preferencesStore';

interface EconomicOverviewWidgetProps {
  onHide: (id: WidgetId) => void;
}

const INDICATOR_ORDER = [
  'FEDFUNDS',
  'MORTGAGE30US',
  'MORTGAGE15US',
  'UNRATE',
  'CPIAUCSL',
];

const INDICATOR_CONTEXT: Record<string, { description: string; goodDirection: 'up' | 'down' | 'neutral' }> = {
  FEDFUNDS: { description: 'Federal Reserve benchmark rate', goodDirection: 'neutral' },
  MORTGAGE30US: { description: '30-year fixed mortgage rate', goodDirection: 'down' },
  MORTGAGE15US: { description: '15-year fixed mortgage rate', goodDirection: 'down' },
  UNRATE: { description: 'National unemployment rate', goodDirection: 'down' },
  CPIAUCSL: { description: 'Consumer Price Index', goodDirection: 'neutral' },
};

export default function EconomicOverviewWidget({ onHide }: EconomicOverviewWidgetProps) {
  const { data, isLoading } = useDashboardSummary();

  const indicators = data?.indicators
    ? INDICATOR_ORDER
        .map((code) => data.indicators.find((i) => i.code === code))
        .filter(Boolean)
    : [];

  const hasData = indicators.length > 0;

  return (
    <WidgetCard
      id="economic-overview"
      title="Economic Overview"
      onHide={onHide}
      isLoading={isLoading}
    >
      {hasData ? (
        <div className="space-y-3">
          {indicators.map((ind) => {
            if (!ind) return null;
            const ctx = INDICATOR_CONTEXT[ind.code];
            return (
              <div
                key={ind.code}
                className="flex items-center justify-between rounded-lg border p-3"
              >
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium">{ind.name}</p>
                  {ctx && (
                    <p className="text-[10px] text-muted-foreground">
                      {ctx.description}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <span className="tabular-nums text-lg font-semibold">
                    {ind.value}
                    {ind.unit}
                  </span>
                  {ind.is_stale && (
                    <span className="rounded bg-amber-100 px-1 py-0.5 text-[9px] font-medium text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
                      Stale
                    </span>
                  )}
                </div>
              </div>
            );
          })}
          {data?.staleness_warning && (
            <p className="flex items-center gap-1 text-[10px] text-muted-foreground">
              <AlertCircle className="h-3 w-3" />
              {data.staleness_warning}
            </p>
          )}
        </div>
      ) : (
        <div className="flex h-32 flex-col items-center justify-center gap-2 text-muted-foreground">
          <AlertCircle className="h-5 w-5" />
          <p className="text-xs">No economic data available. Check data pipeline status.</p>
        </div>
      )}
    </WidgetCard>
  );
}
