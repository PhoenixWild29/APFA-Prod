import { useMemo } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import WidgetCard from '../components/WidgetCard';
import { usePreferencesStore, type WidgetId } from '@/store/preferencesStore';

interface InvestmentGrowthCalculatorWidgetProps {
  onHide: (id: WidgetId) => void;
}

/**
 * Projects future portfolio value from an initial investment, monthly
 * contribution, annualized return, and holding period. This replaces the
 * former DTI (debt-to-income) calculator as part of APFA's pivot from loan
 * advisory to investment research.
 */
export default function InvestmentGrowthCalculatorWidget({
  onHide,
}: InvestmentGrowthCalculatorWidgetProps) {
  const {
    growthInitial,
    growthMonthly,
    growthYears,
    growthRate,
    setGrowthValues,
  } = usePreferencesStore();

  const projection = useMemo(() => {
    const years = Math.max(0, Math.min(growthYears || 0, 50));
    const monthly = Math.max(0, growthMonthly || 0);
    const initial = Math.max(0, growthInitial || 0);
    const annualRate = Math.max(-50, Math.min(growthRate || 0, 50));
    const monthlyRate = annualRate / 100 / 12;

    const points: { year: number; contributions: number; value: number }[] = [];
    let balance = initial;
    let totalContrib = initial;
    points.push({ year: 0, contributions: totalContrib, value: balance });

    for (let y = 1; y <= years; y++) {
      for (let m = 0; m < 12; m++) {
        balance = balance * (1 + monthlyRate) + monthly;
      }
      totalContrib += monthly * 12;
      points.push({
        year: y,
        contributions: Math.round(totalContrib),
        value: Math.round(balance),
      });
    }

    const finalValue = points[points.length - 1]?.value ?? 0;
    const finalContrib = points[points.length - 1]?.contributions ?? 0;
    const gains = Math.max(0, finalValue - finalContrib);

    return { points, finalValue, finalContrib, gains };
  }, [growthInitial, growthMonthly, growthYears, growthRate]);

  const fmt = (n: number) => `$${Math.round(n).toLocaleString()}`;

  return (
    <WidgetCard
      id="investment-growth"
      title="Investment Growth Calculator"
      onHide={onHide}
    >
      <div className="space-y-4">
        {/* Inputs */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <Label htmlFor="growth-initial" className="text-xs">
              Initial Investment
            </Label>
            <div className="relative mt-1">
              <span className="absolute left-2.5 top-2 text-xs text-muted-foreground">
                $
              </span>
              <Input
                id="growth-initial"
                type="number"
                value={growthInitial || ''}
                onChange={(e) =>
                  setGrowthValues({ initial: Number(e.target.value) })
                }
                placeholder="10000"
                className="h-8 pl-6 text-xs tabular-nums"
              />
            </div>
          </div>
          <div>
            <Label htmlFor="growth-monthly" className="text-xs">
              Monthly Contribution
            </Label>
            <div className="relative mt-1">
              <span className="absolute left-2.5 top-2 text-xs text-muted-foreground">
                $
              </span>
              <Input
                id="growth-monthly"
                type="number"
                value={growthMonthly || ''}
                onChange={(e) =>
                  setGrowthValues({ monthly: Number(e.target.value) })
                }
                placeholder="500"
                className="h-8 pl-6 text-xs tabular-nums"
              />
            </div>
          </div>
          <div>
            <Label htmlFor="growth-years" className="text-xs">
              Years
            </Label>
            <Input
              id="growth-years"
              type="number"
              min={1}
              max={50}
              value={growthYears || ''}
              onChange={(e) =>
                setGrowthValues({ years: Number(e.target.value) })
              }
              placeholder="20"
              className="mt-1 h-8 text-xs tabular-nums"
            />
          </div>
          <div>
            <Label htmlFor="growth-rate" className="text-xs">
              Annual Return
            </Label>
            <div className="relative mt-1">
              <Input
                id="growth-rate"
                type="number"
                step={0.1}
                min={-20}
                max={30}
                value={growthRate || ''}
                onChange={(e) =>
                  setGrowthValues({ rate: Number(e.target.value) })
                }
                placeholder="7"
                className="h-8 pr-7 text-xs tabular-nums"
              />
              <span className="absolute right-2.5 top-2 text-xs text-muted-foreground">
                %
              </span>
            </div>
          </div>
        </div>

        {/* Projected value summary */}
        <div className="grid grid-cols-3 gap-2 rounded-lg border bg-muted/30 p-2 text-center">
          <div>
            <p className="text-[10px] uppercase tracking-wide text-muted-foreground">
              Contributions
            </p>
            <p className="tabular-nums text-sm font-semibold">
              {fmt(projection.finalContrib)}
            </p>
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-wide text-muted-foreground">
              Growth
            </p>
            <p className="tabular-nums text-sm font-semibold text-pos">
              {fmt(projection.gains)}
            </p>
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-wide text-muted-foreground">
              Future Value
            </p>
            <p className="tabular-nums text-lg font-bold">
              {fmt(projection.finalValue)}
            </p>
          </div>
        </div>

        {/* Projection chart */}
        <div className="h-28">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={projection.points}>
              <defs>
                <linearGradient id="growthGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#1D8A84" stopOpacity={0.25} />
                  <stop offset="100%" stopColor="#1D8A84" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis
                dataKey="year"
                tick={{ fontSize: 10, fill: 'var(--muted-foreground)' }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(y: number) => `Y${y}`}
              />
              <YAxis
                tick={{ fontSize: 10, fill: 'var(--muted-foreground)' }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v: number) => `$${Math.round(v / 1000)}k`}
                width={50}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'var(--popover)',
                  border: '1px solid var(--border)',
                  borderRadius: 8,
                  fontSize: 12,
                }}
                formatter={(value: number, name: string) => [
                  fmt(value),
                  name === 'value' ? 'Portfolio' : 'Contributions',
                ]}
                labelFormatter={(y: number) => `Year ${y}`}
              />
              <Area
                type="monotone"
                dataKey="contributions"
                stroke="#7E8989"
                strokeWidth={1.5}
                fill="none"
                dot={false}
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#1D8A84"
                strokeWidth={2}
                fill="url(#growthGrad)"
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </WidgetCard>
  );
}
