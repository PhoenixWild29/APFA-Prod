import { useMemo } from 'react';
import { cn } from '@/lib/utils';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import WidgetCard from '../components/WidgetCard';
import { usePreferencesStore, type WidgetId } from '@/store/preferencesStore';

const THRESHOLDS = [
  { pct: 36, label: 'Safe', color: 'text-pos', bg: 'bg-pos' },
  { pct: 43, label: 'Caution', color: 'text-warn', bg: 'bg-warn' },
  { pct: 50, label: 'Risk', color: 'text-neg', bg: 'bg-neg' },
];

interface DTICalculatorWidgetProps {
  onHide: (id: WidgetId) => void;
}

export default function DTICalculatorWidget({ onHide }: DTICalculatorWidgetProps) {
  const { monthlyIncome, monthlyDebt, setDTIValues } = usePreferencesStore();

  const dti = useMemo(() => {
    if (!monthlyIncome || monthlyIncome <= 0) return 0;
    return (monthlyDebt / monthlyIncome) * 100;
  }, [monthlyIncome, monthlyDebt]);

  const zone = THRESHOLDS.find((t) => dti <= t.pct) ?? THRESHOLDS[2];

  return (
    <WidgetCard id="dti-calculator" title="DTI Calculator" onHide={onHide}>
      <div className="space-y-4">
        {/* Inputs */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <Label htmlFor="dti-income" className="text-xs">
              Monthly Income
            </Label>
            <div className="relative mt-1">
              <span className="absolute left-2.5 top-2 text-xs text-muted-foreground">$</span>
              <Input
                id="dti-income"
                type="number"
                value={monthlyIncome || ''}
                onChange={(e) =>
                  setDTIValues(Number(e.target.value), monthlyDebt)
                }
                placeholder="0"
                className="h-8 pl-6 text-xs tabular-nums"
              />
            </div>
          </div>
          <div>
            <Label htmlFor="dti-debt" className="text-xs">
              Monthly Debt
            </Label>
            <div className="relative mt-1">
              <span className="absolute left-2.5 top-2 text-xs text-muted-foreground">$</span>
              <Input
                id="dti-debt"
                type="number"
                value={monthlyDebt || ''}
                onChange={(e) =>
                  setDTIValues(monthlyIncome, Number(e.target.value))
                }
                placeholder="0"
                className="h-8 pl-6 text-xs tabular-nums"
              />
            </div>
          </div>
        </div>

        {/* Result */}
        <div className="text-center">
          <p className={cn('tabular-nums text-3xl font-bold', zone.color)}>
            {monthlyIncome > 0 ? `${dti.toFixed(1)}%` : '—'}
          </p>
          {monthlyIncome > 0 && (
            <p className={cn('mt-1 text-xs font-medium', zone.color)}>
              {zone.label}
            </p>
          )}
        </div>

        {/* Threshold bar */}
        <div className="space-y-1.5">
          <div className="flex h-2 overflow-hidden rounded-full bg-muted">
            <div className="bg-pos" style={{ width: '36%' }} />
            <div className="bg-warn" style={{ width: '7%' }} />
            <div className="bg-neg" style={{ width: '7%' }} />
            <div className="bg-muted" style={{ width: '50%' }} />
            {/* Indicator needle */}
            {monthlyIncome > 0 && (
              <div
                className="absolute h-2 w-0.5 bg-foreground"
                style={{ left: `${Math.min(dti, 60)}%` }}
              />
            )}
          </div>
          <div className="flex justify-between text-[10px] text-muted-foreground tabular-nums">
            <span>0%</span>
            <span>36%</span>
            <span>43%</span>
            <span>50%+</span>
          </div>
        </div>
      </div>
    </WidgetCard>
  );
}
