import { useNavigate } from 'react-router-dom';
import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, Tooltip } from 'recharts';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ArrowRight } from 'lucide-react';
import WidgetCard from '../components/WidgetCard';
import type { WidgetId } from '@/store/preferencesStore';

// Placeholder — will use portfolio API data
const ALLOCATIONS = [
  {
    type: 'US Equities',
    allocation: 55,
    value: 68668,
    ytdReturn: 12.1,
    tags: ['Core'],
  },
  {
    type: 'Int\'l Equities',
    allocation: 20,
    value: 24970,
    ytdReturn: 6.8,
    tags: ['Diversifier'],
  },
  {
    type: 'Fixed Income',
    allocation: 25,
    value: 31212,
    ytdReturn: 3.2,
    tags: ['Stability'],
  },
];

const chartData = ALLOCATIONS.map((a) => ({
  name: a.type,
  allocation: a.allocation,
}));

interface LoanComparisonWidgetProps {
  onHide: (id: WidgetId) => void;
}

export default function LoanComparisonWidget({ onHide }: LoanComparisonWidgetProps) {
  const navigate = useNavigate();

  return (
    <WidgetCard
      id="loan-comparison"
      title="Asset Allocation"
      onHide={onHide}
      action={
        <Button
          variant="link"
          size="sm"
          className="h-auto p-0 text-xs"
          onClick={() => navigate('/app/calculators/allocation')}
        >
          Rebalance <ArrowRight className="ml-1 h-3 w-3" />
        </Button>
      }
    >
      {/* Cards */}
      <div className="grid grid-cols-3 gap-2">
        {ALLOCATIONS.map((item) => (
          <div
            key={item.type}
            className="flex flex-col items-center rounded-lg border p-2 text-center"
          >
            <p className="text-[10px] font-medium text-muted-foreground">
              {item.type}
            </p>
            <p className="tabular-nums text-lg font-semibold">
              {item.allocation}%
            </p>
            <p className="tabular-nums text-xs text-muted-foreground">
              ${item.value.toLocaleString()}
            </p>
            <div className="mt-1 flex flex-wrap justify-center gap-1">
              {item.tags.map((tag) => (
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
              formatter={(value: number) => [`${value}%`, 'Allocation']}
            />
            <Bar dataKey="allocation" fill="#C79A2B" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </WidgetCard>
  );
}
