import { useState } from 'react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Line,
  LineChart,
  ReferenceLine,
} from 'recharts';
import { Bell, BellOff, Plus, Trash2, TrendingDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
  DialogClose,
} from '@/components/ui/dialog';

// Demo rate history — will be GET /rates?history=365d
const RATE_HISTORY = Array.from({ length: 52 }, (_, i) => {
  const date = new Date();
  date.setDate(date.getDate() - (51 - i) * 7);
  return {
    date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    rate30: 7.2 - i * 0.012 + (Math.random() - 0.5) * 0.15,
    rate15: 6.5 - i * 0.01 + (Math.random() - 0.5) * 0.12,
  };
});

interface RateAlert {
  id: string;
  product: '30yr' | '15yr';
  threshold: number;
  direction: 'below' | 'above';
  active: boolean;
}

export default function InsightsPage() {
  const [alerts, setAlerts] = useState<RateAlert[]>([
    { id: '1', product: '30yr', threshold: 6.5, direction: 'below', active: true },
  ]);
  const [newThreshold, setNewThreshold] = useState('');
  const [newProduct, setNewProduct] = useState<'30yr' | '15yr'>('30yr');

  const currentRate30 = RATE_HISTORY[RATE_HISTORY.length - 1].rate30;
  const currentRate15 = RATE_HISTORY[RATE_HISTORY.length - 1].rate15;
  const weekAgoRate30 = RATE_HISTORY[RATE_HISTORY.length - 2].rate30;
  const delta30 = currentRate30 - weekAgoRate30;

  const addAlert = () => {
    const threshold = parseFloat(newThreshold);
    if (isNaN(threshold) || threshold <= 0) return;
    setAlerts((prev) => [
      ...prev,
      {
        id: `alert-${Date.now()}`,
        product: newProduct,
        threshold,
        direction: 'below',
        active: true,
      },
    ]);
    setNewThreshold('');
  };

  const removeAlert = (id: string) => {
    setAlerts((prev) => prev.filter((a) => a.id !== id));
  };

  const toggleAlert = (id: string) => {
    setAlerts((prev) =>
      prev.map((a) => (a.id === id ? { ...a, active: !a.active } : a))
    );
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div>
        <h1 className="font-serif text-2xl font-semibold">Insights</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Rate trends and alerts to help you time decisions.
        </p>
      </div>

      {/* Current rates */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        <div className="rounded-xl border bg-card p-4">
          <p className="text-xs font-medium text-muted-foreground">30-Year Fixed</p>
          <p className="mt-1 tabular-nums text-2xl font-semibold">
            {currentRate30.toFixed(2)}%
          </p>
          <p
            className={`mt-0.5 flex items-center gap-1 text-xs font-medium ${
              delta30 < 0 ? 'text-pos' : 'text-neg'
            }`}
          >
            <TrendingDown className="h-3 w-3" />
            <span className="tabular-nums">
              {delta30 > 0 ? '+' : ''}
              {delta30.toFixed(2)}% this week
            </span>
          </p>
        </div>
        <div className="rounded-xl border bg-card p-4">
          <p className="text-xs font-medium text-muted-foreground">15-Year Fixed</p>
          <p className="mt-1 tabular-nums text-2xl font-semibold">
            {currentRate15.toFixed(2)}%
          </p>
        </div>
        <div className="rounded-xl border bg-card p-4 sm:col-span-1 col-span-2">
          <p className="text-xs font-medium text-muted-foreground">Active Alerts</p>
          <p className="mt-1 text-2xl font-semibold">
            {alerts.filter((a) => a.active).length}
          </p>
        </div>
      </div>

      {/* Rate history chart */}
      <div className="rounded-xl border bg-card p-4">
        <h2 className="mb-4 text-sm font-semibold">Rate History (52 weeks)</h2>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={RATE_HISTORY}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 10, fill: 'var(--muted-foreground)' }}
                tickLine={false}
                axisLine={false}
                interval={7}
              />
              <YAxis
                domain={['dataMin - 0.2', 'dataMax + 0.2']}
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
                formatter={(value: number, name: string) => [
                  `${value.toFixed(2)}%`,
                  name === 'rate30' ? '30yr Fixed' : '15yr Fixed',
                ]}
              />
              {/* Alert threshold lines */}
              {alerts
                .filter((a) => a.active)
                .map((alert) => (
                  <ReferenceLine
                    key={alert.id}
                    y={alert.threshold}
                    stroke="#C79A2B"
                    strokeDasharray="4 4"
                    label={{
                      value: `Alert: ${alert.threshold}%`,
                      fill: '#C79A2B',
                      fontSize: 10,
                      position: 'right',
                    }}
                  />
                ))}
              <Line
                type="monotone"
                dataKey="rate30"
                stroke="#1D8A84"
                strokeWidth={2}
                dot={false}
                name="rate30"
              />
              <Line
                type="monotone"
                dataKey="rate15"
                stroke="#7C5CBF"
                strokeWidth={1.5}
                dot={false}
                name="rate15"
                strokeDasharray="5 5"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-3 flex gap-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1.5">
            <span className="h-0.5 w-4 bg-teal-500" /> 30yr Fixed
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-0.5 w-4 border-t-2 border-dashed border-[#7C5CBF]" /> 15yr Fixed
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-0.5 w-4 border-t border-dashed border-gold-500" /> Alert threshold
          </span>
        </div>
      </div>

      {/* Alerts management */}
      <div className="rounded-xl border bg-card p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold">Rate Alerts</h2>
          <Dialog>
            <DialogTrigger asChild>
              <Button size="sm" variant="outline">
                <Plus className="mr-1.5 h-3.5 w-3.5" />
                Add alert
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>New Rate Alert</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div>
                  <Label className="text-xs">Product</Label>
                  <div className="mt-1.5 flex gap-2">
                    {(['30yr', '15yr'] as const).map((p) => (
                      <button
                        key={p}
                        onClick={() => setNewProduct(p)}
                        className={`rounded-md border px-3 py-1.5 text-sm ${
                          newProduct === p
                            ? 'border-teal-500 bg-teal-500/10 text-teal-700 dark:text-teal-300'
                            : 'text-muted-foreground'
                        }`}
                      >
                        {p} Fixed
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <Label htmlFor="threshold" className="text-xs">
                    Alert when rate drops below
                  </Label>
                  <div className="relative mt-1.5">
                    <Input
                      id="threshold"
                      type="number"
                      step="0.01"
                      value={newThreshold}
                      onChange={(e) => setNewThreshold(e.target.value)}
                      placeholder="6.50"
                      className="pr-6 tabular-nums"
                    />
                    <span className="absolute right-3 top-2 text-sm text-muted-foreground">
                      %
                    </span>
                  </div>
                </div>
              </div>
              <DialogFooter>
                <DialogClose asChild>
                  <Button variant="outline">Cancel</Button>
                </DialogClose>
                <DialogClose asChild>
                  <Button onClick={addAlert}>Create Alert</Button>
                </DialogClose>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

        <Separator className="my-3" />

        {alerts.length === 0 ? (
          <p className="py-4 text-center text-sm text-muted-foreground">
            No alerts set. Add one to get notified when rates hit your target.
          </p>
        ) : (
          <div className="space-y-2">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className="flex items-center justify-between rounded-lg border p-3"
              >
                <div className="flex items-center gap-3">
                  {alert.active ? (
                    <Bell className="h-4 w-4 text-gold-500" />
                  ) : (
                    <BellOff className="h-4 w-4 text-muted-foreground" />
                  )}
                  <div>
                    <p className="text-sm font-medium">
                      {alert.product} Fixed below{' '}
                      <span className="tabular-nums">{alert.threshold}%</span>
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Currently{' '}
                      <span className="tabular-nums">
                        {(alert.product === '30yr' ? currentRate30 : currentRate15).toFixed(2)}%
                      </span>
                      {' — '}
                      {(alert.product === '30yr' ? currentRate30 : currentRate15) <=
                      alert.threshold ? (
                        <Badge className="bg-pos/10 text-pos text-[10px]">Triggered</Badge>
                      ) : (
                        <span>
                          {(
                            (alert.product === '30yr' ? currentRate30 : currentRate15) -
                            alert.threshold
                          ).toFixed(2)}
                          % away
                        </span>
                      )}
                    </p>
                  </div>
                </div>
                <div className="flex gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7"
                    onClick={() => toggleAlert(alert.id)}
                    aria-label={alert.active ? 'Mute alert' : 'Enable alert'}
                  >
                    {alert.active ? (
                      <BellOff className="h-3.5 w-3.5" />
                    ) : (
                      <Bell className="h-3.5 w-3.5" />
                    )}
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 text-neg"
                    onClick={() => removeAlert(alert.id)}
                    aria-label="Delete alert"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
