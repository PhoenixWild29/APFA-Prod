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

// Placeholder data — will be GET /rates?history=...
const DEMO_DATA: Record<TimeRange, { date: string; rate: number }[]> = {
  '1W': [
    { date: 'Mon', rate: 6.72 },
    { date: 'Tue', rate: 6.68 },
    { date: 'Wed', rate: 6.71 },
    { date: 'Thu', rate: 6.65 },
    { date: 'Fri', rate: 6.62 },
  ],
  '1M': Array.from({ length: 20 }, (_, i) => ({
    date: `${i + 1}`,
    rate: 6.8 - Math.random() * 0.3,
  })),
  '3M': Array.from({ length: 12 }, (_, i) => ({
    date: `W${i + 1}`,
    rate: 7.0 - i * 0.03 - Math.random() * 0.1,
  })),
  '1Y': Array.from({ length: 12 }, (_, i) => ({
    date: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][i],
    rate: 7.2 - i * 0.05 - Math.random() * 0.15,
  })),
};

interface RateTrendWidgetProps {
  onHide: (id: WidgetId) => void;
}

export default function RateTrendWidget({ onHide }: RateTrendWidgetProps) {
  const [range, setRange] = useState<TimeRange>('1M');
  const data = DEMO_DATA[range];
  const currentRate = data[data.length - 1]?.rate ?? 0;

  return (
    <WidgetCard
      id="rate-trend"
      title="30-Year Conforming Rate"
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
          {currentRate.toFixed(2)}%
        </span>
      </div>
      <div className="h-40">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="rateGrad" x1="0" y1="0" x2="0" y2="1">
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
              domain={['dataMin - 0.1', 'dataMax + 0.1']}
              tick={{ fontSize: 10, fill: 'var(--muted-foreground)' }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v: number) => `${v.toFixed(1)}%`}
              width={45}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'var(--popover)',
                border: '1px solid var(--border)',
                borderRadius: 8,
                fontSize: 12,
              }}
              formatter={(value: number) => [`${value.toFixed(2)}%`, 'Rate']}
            />
            <Area
              type="monotone"
              dataKey="rate"
              stroke="#1D8A84"
              strokeWidth={2}
              fill="url(#rateGrad)"
              dot={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </WidgetCard>
  );
}
