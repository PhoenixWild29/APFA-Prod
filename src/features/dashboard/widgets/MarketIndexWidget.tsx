import { useState } from 'react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import WidgetCard from '../components/WidgetCard';
import type { WidgetId } from '@/store/preferencesStore';
import { useDashboardSummary, useMarketHistory } from '@/hooks/useMarket';

const TIME_RANGES = [
  { label: '1W', days: 7 },
  { label: '1M', days: 30 },
  { label: '3M', days: 90 },
  { label: '1Y', days: 365 },
] as const;

const INDICES = [
  { ticker: 'SPY', label: 'S&P 500' },
  { ticker: 'QQQ', label: 'NASDAQ 100' },
  { ticker: 'DIA', label: 'Dow Jones' },
] as const;

type TickerId = (typeof INDICES)[number]['ticker'];

interface MarketIndexWidgetProps {
  onHide: (id: WidgetId) => void;
}

export default function MarketIndexWidget({ onHide }: MarketIndexWidgetProps) {
  const [rangeIdx, setRangeIdx] = useState(1);
  const [tickerId, setTickerId] = useState<TickerId>('SPY');

  const range = TIME_RANGES[rangeIdx];
  const { data: summary } = useDashboardSummary();
  const { data: history, isLoading } = useMarketHistory(
    tickerId,
    'quote',
    range.days
  );

  const currentQuote = summary?.quotes.find((q) => q.ticker === tickerId);
  const hasHistory = history && history.points.length > 1;
  const chartData = hasHistory
    ? history.points.map((p) => ({ date: p.date, value: p.value }))
    : [];

  const currentValue = currentQuote?.price ?? chartData[chartData.length - 1]?.value ?? 0;
  const firstValue = chartData[0]?.value ?? currentValue;
  const change = currentValue - firstValue;
  const pctChange = firstValue > 0 ? (change / firstValue) * 100 : 0;

  return (
    <WidgetCard
      id="market-index"
      title="Market Index"
      onHide={onHide}
      isLoading={isLoading}
      action={
        <div className="flex gap-0.5">
          {TIME_RANGES.map((r, i) => (
            <Button
              key={r.label}
              variant="ghost"
              size="sm"
              className={cn(
                'h-6 px-2 text-[10px]',
                rangeIdx === i && 'bg-muted font-semibold'
              )}
              onClick={() => setRangeIdx(i)}
            >
              {r.label}
            </Button>
          ))}
        </div>
      }
    >
      <div className="mb-2 flex gap-1">
        {INDICES.map((idx) => (
          <Button
            key={idx.ticker}
            variant="ghost"
            size="sm"
            className={cn(
              'h-6 px-2 text-[10px]',
              tickerId === idx.ticker && 'bg-muted font-semibold'
            )}
            onClick={() => setTickerId(idx.ticker)}
          >
            {idx.label}
          </Button>
        ))}
      </div>

      {currentQuote && (
        <div className="mb-3 flex items-baseline gap-3">
          <span className="tabular-nums text-2xl font-semibold">
            ${currentValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
          {hasHistory && (
            <span
              className={cn(
                'tabular-nums text-xs font-medium',
                change >= 0 ? 'text-pos' : 'text-neg'
              )}
            >
              {change >= 0 ? '+' : ''}
              {change.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ({pctChange >= 0 ? '+' : ''}
              {pctChange.toFixed(2)}%)
            </span>
          )}
          {currentQuote.is_stale && (
            <span className="rounded bg-amber-100 px-1.5 py-0.5 text-[9px] font-medium text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
              Delayed
            </span>
          )}
        </div>
      )}

      {hasHistory ? (
        <div className="h-40">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="indexGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#1D8A84" stopOpacity={0.15} />
                  <stop offset="100%" stopColor="#1D8A84" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 10, fill: 'var(--muted-foreground)' }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                domain={['dataMin - 5', 'dataMax + 5']}
                tick={{ fontSize: 10, fill: 'var(--muted-foreground)' }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v: number) =>
                  `$${v.toLocaleString('en-US', { maximumFractionDigits: 0 })}`
                }
                width={55}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'var(--popover)',
                  border: '1px solid var(--border)',
                  borderRadius: 8,
                  fontSize: 12,
                }}
                formatter={(value) =>
                  `$${Number(value).toLocaleString('en-US', { minimumFractionDigits: 2 })}`
                }
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#1D8A84"
                strokeWidth={2}
                fill="url(#indexGrad)"
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div className="flex h-40 flex-col items-center justify-center gap-2 text-muted-foreground">
          <AlertCircle className="h-5 w-5" />
          <p className="text-xs">
            {currentQuote
              ? 'Chart data is accumulating. Historical trends will appear within a few days.'
              : 'No market data available. Check data pipeline status.'}
          </p>
        </div>
      )}
    </WidgetCard>
  );
}
