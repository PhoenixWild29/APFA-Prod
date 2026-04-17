import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { Area, AreaChart, ResponsiveContainer } from 'recharts';
import { cn } from '@/lib/utils';

interface KPICardProps {
  label: string;
  value: string;
  delta?: { value: string; direction: 'up' | 'down' | 'flat' };
  sparkline?: { value: number }[];
  color?: string;
}

export default function KPICard({
  label,
  value,
  delta,
  sparkline,
  color = '#1D8A84',
}: KPICardProps) {
  const DeltaIcon =
    delta?.direction === 'up'
      ? TrendingUp
      : delta?.direction === 'down'
        ? TrendingDown
        : Minus;

  return (
    <div className="flex flex-col justify-between rounded-xl border bg-card p-4 shadow-card">
      <p className="text-xs font-medium text-muted-foreground">{label}</p>

      <div className="mt-2 flex items-end justify-between gap-3">
        <div>
          <p className="tabular-nums text-2xl font-semibold tracking-tight">
            {value}
          </p>
          {delta && (
            <div
              className={cn(
                'mt-1 flex items-center gap-1 text-xs font-medium',
                delta.direction === 'up' && 'text-pos',
                delta.direction === 'down' && 'text-neg',
                delta.direction === 'flat' && 'text-muted-foreground'
              )}
            >
              <DeltaIcon className="h-3 w-3" />
              <span className="tabular-nums">{delta.value}</span>
            </div>
          )}
        </div>

        {sparkline && sparkline.length > 1 && (
          <div className="h-10 w-20">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={sparkline}>
                <defs>
                  <linearGradient id={`kpi-${label}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={color} stopOpacity={0.2} />
                    <stop offset="100%" stopColor={color} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke={color}
                  strokeWidth={1.5}
                  fill={`url(#kpi-${label})`}
                  dot={false}
                  isAnimationActive={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}
