import { useNavigate } from 'react-router-dom';
import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, Tooltip } from 'recharts';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ArrowRight } from 'lucide-react';
import WidgetCard from '../components/WidgetCard';
import type { WidgetId } from '@/store/preferencesStore';

// Placeholder — will be driven by the portfolio API (GET /portfolio/allocation).
// Rendered as an "asset allocation comparison" (current vs. target) so users
// can see drift at a glance.
const ALLOCATIONS = [
  {
    type: 'US Equities',
    current: 55,
    target: 50,
    value: 68668,
    ytdReturn: 12.1,
    tags: ['Core'],
  },
  {
    type: "Int'l Equities",
    current: 20,
    target: 20,
    value: 24970,
    ytdReturn: 6.8,
    tags: ['Diversifier'],
  },
  {
    type: 'Fixed Income',
    current: 20,
    target: 25,
    value: 24970,
    ytdReturn: 3.2,
    tags: ['Stability'],
  },
  {
    type: 'Cash',
    current: 5,
    target: 5,
    value: 6243,
    ytdReturn: 4.5,
    tags: ['Reserve'],
  },
];

const chartData = ALLOCATIONS.map((a) => ({
  name: a.type,
  Current: a.current,
  Target: a.target,
}));

interface AssetAllocationWidgetProps {
  onHide: (id: WidgetId) => void;
}

export default function AssetAllocationWidget({ onHide }: AssetAllocationWidgetProps) {
  const navigate = useNavigate();

  return (
    <WidgetCard
      id="asset-allocation"
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
      {/* Per-asset cards with current vs. target */}
      <div className="grid grid-cols-4 gap-2">
        {ALLOCATIONS.map((item) => {
          const drift = item.current - item.target;
          return (
            <div
              key={item.type}
              className="flex flex-col items-center rounded-lg border p-2 text-center"
            >
              <p className="text-[10px] font-medium text-muted-foreground">
                {item.type}
              </p>
              <p className="tabular-nums text-lg font-semibold">{item.current}%</p>
              <p className="text-[10px] tabular-nums text-muted-foreground">
                Target {item.target}%
                {drift !== 0 && (
                  <span
                    className={
                      drift > 0 ? 'ml-1 text-warn' : 'ml-1 text-muted-foreground'
                    }
                  >
                    ({drift > 0 ? '+' : ''}
                    {drift})
                  </span>
                )}
              </p>
              <div className="mt-1 flex flex-wrap justify-center gap-1">
                {item.tags.map((tag) => (
                  <Badge
                    key={tag}
                    variant="secondary"
                    className="px-1 py-0 text-[9px]"
                  >
                    {tag}
                  </Badge>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Current vs. Target bar chart */}
      <div className="mt-3 h-28">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} barSize={14}>
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
              formatter={(value: number, name: string) => [`${value}%`, name]}
            />
            <Bar dataKey="Current" fill="#1D8A84" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Target" fill="#C79A2B" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </WidgetCard>
  );
}
