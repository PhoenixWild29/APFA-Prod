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

// Placeholder market index data — will be GET /market-data?index=sp500
const DEMO_DATA: Record<TimeRange, { date: string; value: number }[]> = {
  '1W': [
    { date: 'Mon', value: 5385 },
    { date: 'Tue', value: 5398 },
    { date: 'Wed', value: 5371 },
    { date: 'Thu', value: 5410 },
    { date: 'Fri', value: 5421 },
  ],
  '1M': Array.from({ length: 20 }, (_, i) => ({
    date: `${i + 1}`,
    value: 5250 + i * 9 + Math.round((Math.random() - 0.5) * 30),
  })),
  '3M': Array.from({ length: 12 }, (_, i) => ({
    date: `W${i + 1}`,
    value: 5100 + i * 28 + Math.round((Math.random() - 0.5) * 40),
  })),
  '1Y': Array.from({ length: 12 }, (_, i) => ({
    date: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][i],
    value: 4800 + i * 55 + Math.round((Math.random() - 0.5) * 60),
  })),
};

interface RateTrendWidgetProps {
  onHide: (id: WidgetId) => void;
}

export default function RateTrendWidget({ onHide }: RateTrendWidgetProps) {
  const [range, setRange] = useState<TimeRange>('1M');
  const data = DEMO_DATA[range];
  const currentValue = data[data.length - 1]?.value ?? 0;

  return (
    <WidgetCard
      id="rate-trend"
      title="S&P 500 Index"
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
      <div className="mb-3">
        <span className="tabular-nums text-2xl font-semibold">
          {currentValue.toLocaleString()}
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
              formatter={(value: number) => [value.toLocaleString(), 'S&P 500']}
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
