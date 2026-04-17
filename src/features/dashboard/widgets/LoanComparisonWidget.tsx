import { useNavigate } from 'react-router-dom';
import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, Tooltip } from 'recharts';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ArrowRight } from 'lucide-react';
import WidgetCard from '../components/WidgetCard';
import type { WidgetId } from '@/store/preferencesStore';

// Placeholder — will use /rates + client math
const LOANS = [
  {
    type: 'Conv. 30yr',
    rate: 6.62,
    monthly: 1918,
    totalInterest: 390480,
    tags: ['Most common'],
  },
  {
    type: 'Conv. 15yr',
    rate: 5.89,
    monthly: 2520,
    totalInterest: 153600,
    tags: ['Lowest total'],
  },
  {
    type: 'FHA 30yr',
    rate: 6.25,
    monthly: 1847,
    totalInterest: 364920,
    tags: ['Low down pmt'],
  },
];

const chartData = LOANS.map((l) => ({
  name: l.type,
  interest: Math.round(l.totalInterest / 1000),
}));

interface LoanComparisonWidgetProps {
  onHide: (id: WidgetId) => void;
}

export default function LoanComparisonWidget({ onHide }: LoanComparisonWidgetProps) {
  const navigate = useNavigate();

  return (
    <WidgetCard
      id="loan-comparison"
      title="Loan Comparison"
      onHide={onHide}
      action={
        <Button
          variant="link"
          size="sm"
          className="h-auto p-0 text-xs"
          onClick={() => navigate('/app/calculators/loan-compare')}
        >
          Full compare <ArrowRight className="ml-1 h-3 w-3" />
        </Button>
      }
    >
      {/* Cards */}
      <div className="grid grid-cols-3 gap-2">
        {LOANS.map((loan) => (
          <div
            key={loan.type}
            className="flex flex-col items-center rounded-lg border p-2 text-center"
          >
            <p className="text-[10px] font-medium text-muted-foreground">
              {loan.type}
            </p>
            <p className="tabular-nums text-lg font-semibold">
              {loan.rate.toFixed(2)}%
            </p>
            <p className="tabular-nums text-xs text-muted-foreground">
              ${loan.monthly.toLocaleString()}/mo
            </p>
            <div className="mt-1 flex flex-wrap justify-center gap-1">
              {loan.tags.map((tag) => (
                <Badge
                  key={tag}
                  variant="secondary"
                  className="text-[9px] px-1 py-0"
                >
                  {tag}
                </Badge>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Bar chart */}
      <div className="mt-3 h-24">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} barSize={24}>
            <XAxis
              dataKey="name"
              tick={{ fontSize: 9, fill: 'var(--muted-foreground)' }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis hide />
            <Tooltip
              contentStyle={{
                backgroundColor: 'var(--popover)',
                border: '1px solid var(--border)',
                borderRadius: 8,
                fontSize: 11,
              }}
              formatter={(value: number) => [`$${value}K`, 'Total Interest']}
            />
            <Bar dataKey="interest" fill="#C79A2B" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </WidgetCard>
  );
}
