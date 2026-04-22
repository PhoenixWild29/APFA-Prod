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
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import WidgetCard from '../components/WidgetCard';
import type { WidgetId } from '@/store/preferencesStore';

const TIME_RANGES = ['1W', '1M', '3M', '1Y'] as const;
type TimeRange = (typeof TIME_RANGES)[number];

const INDICES = [
  { id: 'sp500', label: 'S&P 500', base: 5200, step: 12 },
  { id: 'nasdaq', label: 'NASDAQ', base: 17000, step: 40 },
  { id: 'dow', label: 'Dow Jones', base: 38500, step: 25 },
] as const;
type IndexId = (typeof INDICES)[number]['id'];

// Placeholder market index data — swap to GET /market-data?index=<id> once shipped.
function generateData(indexId: IndexId, range: TimeRange) {
  const meta = INDICES.find((i) => i.id === indexId) ?? INDICES[0];
  const points = range === '1W' ? 5 : range === '1M' ? 20 : range === '3M' ? 12 : 12;
  const step = range === '1Y' ? meta.step * 4 : meta.step;

  return Array.from({ length: points }, (_, i) => {
    const labels1W = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'];
    const labels1Y = [
      'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
    ];
    const date =
      range === '1W'
        ? labels1W[i]
        : range === '1Y'
          ? labels1Y[i]
          : range === '3M'
            ? `W${i + 1}`
            : `${i + 1}`;
    return {
      date,
      value: meta.base + i * step + Math.round((Math.random() - 0.5) * meta.step * 2),
    };
  });
}

interface MarketIndexWidgetProps {
  onHide: (id: WidgetId) => void;
}

export default function MarketIndexWidget({ onHide }: MarketIndexWidgetProps) {
  const [range, setRange] = useState<TimeRange>('1M');
  const [indexId, setIndexId] = useState<IndexId>('sp500');

  const data = generateData(indexId, range);
  const currentValue = data[data.length - 1]?.value ?? 0;
  const firstValue = data[0]?.value ?? currentValue;
  const change = currentValue - firstValue;
  const pctChange = firstValue > 0 ? (change / firstValue) * 100 : 0;
  const label = INDICES.find((i) => i.id === indexId)?.label ?? 'Index';

  return (
    <WidgetCard
      id="market-index"
      title="Market Index"
      onHide={onHide}
      action={
        <div className="flex gap-0.5">
          {TIME_RANGES.map((r) => (
            <Button
              key={r}
              variant="ghost"
              size="sm"
              className={cn(
                'h-6 px-2 text-[10px]',
                range === r && 'bg-muted font-semibold'
              )}
              onClick={() => setRange(r)}
            >
              {r}
            </Button>
          ))}
        </div>
      }
    >
      <div className="mb-2 flex gap-1">
        {INDICES.map((idx) => (
          <Button
            key={idx.id}
            variant="ghost"
            size="sm"
            className={cn(
              'h-6 px-2 text-[10px]',
              indexId === idx.id && 'bg-muted font-semibold'
            )}
            onClick={() => setIndexId(idx.id)}
          >
            {idx.label}
          </Button>
        ))}
      </div>
      <div className="mb-3 flex items-baseline gap-3">
        <span className="tabular-nums text-2xl font-semibold">
          {currentValue.toLocaleString()}
        </span>
        <span
          className={cn(
            'tabular-nums text-xs font-medium',
            change >= 0 ? 'text-pos' : 'text-neg'
          )}
        >
          {change >= 0 ? '+' : ''}
          {change.toLocaleString()} ({pctChange >= 0 ? '+' : ''}
          {pctChange.toFixed(2)}%)
        </span>
      </div>
      <div className="h-40">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
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
              domain={['dataMin - 50', 'dataMax + 50']}
              tick={{ fontSize: 10, fill: 'var(--muted-foreground)' }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v: number) => v.toLocaleString()}
              width={50}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'var(--popover)',
                border: '1px solid var(--border)',
                borderRadius: 8,
                fontSize: 12,
              }}
              formatter={(value: number) => [value.toLocaleString(), label]}
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
    </WidgetCard>
  );
}
