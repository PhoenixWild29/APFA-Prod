import { useState } from 'react';
import {
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Line,
  LineChart,
  ReferenceLine,
} from 'recharts';
import { Bell, BellOff, Plus, Trash2, TrendingUp, TrendingDown } from 'lucide-react';
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

// Demo market data — will be fetched from market data API
const MARKET_HISTORY = Array.from({ length: 52 }, (_, i) => {
  const date = new Date();
  date.setDate(date.getDate() - (51 - i) * 7);
  return {
    date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    sp500: 4800 + i * 12 + (Math.random() - 0.5) * 60,
    nasdaq: 15000 + i * 40 + (Math.random() - 0.5) * 200,
  };
});

// Demo rate data for the rate tracking section
const RATE_HISTORY = Array.from({ length: 52 }, (_, i) => {
  const date = new Date();
  date.setDate(date.getDate() - (51 - i) * 7);
  return {
    date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    yield10y: 4.3 - i * 0.008 + (Math.random() - 0.5) * 0.1,
  };
});

interface PriceAlert {
  id: string;
  target: 'sp500' | 'nasdaq' | 'treasury10y';
  threshold: number;
  direction: 'below' | 'above';
  active: boolean;
}

export default function InsightsPage() {
  const [alerts, setAlerts] = useState<PriceAlert[]>([
    { id: '1', target: 'sp500', threshold: 5500, direction: 'above', active: true },
  ]);
  const [newThreshold, setNewThreshold] = useState('');
  const [newTarget, setNewTarget] = useState<'sp500' | 'nasdaq' | 'treasury10y'>('sp500');

  const currentSP = MARKET_HISTORY[MARKET_HISTORY.length - 1].sp500;
  const currentNasdaq = MARKET_HISTORY[MARKET_HISTORY.length - 1].nasdaq;
  const currentYield10y = RATE_HISTORY[RATE_HISTORY.length - 1].rate30;
  const weekAgoSP = MARKET_HISTORY[MARKET_HISTORY.length - 2].sp500;
  const deltaSP = currentSP - weekAgoSP;

  const addAlert = () => {
    const threshold = parseFloat(newThreshold);
    if (isNaN(threshold) || threshold <= 0) return;
    setAlerts((prev) => [
      ...prev,
      {
        id: `alert-${Date.now()}`,
        target: newTarget,
        threshold,
        direction: newTarget === 'treasury10y' ? 'below' : 'above',
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

  const targetLabels: Record<string, string> = {
    sp500: 'S&P 500',
    nasdaq: 'NASDAQ',
    'treasury10y': '10yr Treasury Yield',
  };

  const getCurrentValue = (target: string) => {
    if (target === 'sp500') return currentSP;
    if (target === 'nasdaq') return currentNasdaq;
    return currentYield10y;
  };

  const formatValue = (target: string, value: number) => {
    if (target === 'treasury10y') return `${value.toFixed(2)}%`;
    return value.toLocaleString(undefined, { maximumFractionDigits: 0 });
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div>
        <h1 className="font-serif text-2xl font-semibold">Insights</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Market trends, rate tracking, and alerts to help you time decisions.
        </p>
      </div>

      {/* Current metrics */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        <div className="rounded-xl border bg-card p-4">
          <p className="text-xs font-medium text-muted-foreground">S&P 500</p>
          <p className="mt-1 tabular-nums text-2xl font-semibold">
            {currentSP.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </p>
          <p
            className={`mt-0.5 flex items-center gap-1 text-xs font-medium ${
              deltaSP > 0 ? 'text-pos' : 'text-neg'
            }`}
          >
            {deltaSP > 0 ? (
              <TrendingUp className="h-3 w-3" />
            ) : (
              <TrendingDown className="h-3 w-3" />
            )}
            <span className="tabular-nums">
              {deltaSP > 0 ? '+' : ''}
              {deltaSP.toFixed(0)} this week
            </span>
          </p>
        </div>
        <div className="rounded-xl border bg-card p-4">
          <p className="text-xs font-medium text-muted-foreground">NASDAQ</p>
          <p className="mt-1 tabular-nums text-2xl font-semibold">
            {currentNasdaq.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </p>
        </div>
        <div className="rounded-xl border bg-card p-4 sm:col-span-1 col-span-2">
          <p className="text-xs font-medium text-muted-foreground">Active Alerts</p>
          <p className="mt-1 text-2xl font-semibold">
            {alerts.filter((a) => a.active).length}
          </p>
        </div>
      </div>

      {/* Market indices chart */}
      <div className="rounded-xl border bg-card p-4">
        <h2 className="mb-4 text-sm font-semibold">Market Indices (52 weeks)</h2>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={MARKET_HISTORY}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 10, fill: 'var(--muted-foreground)' }}
                tickLine={false}
                axisLine={false}
                interval={7}
              />
              <YAxis
                yAxisId="sp"
                domain={['dataMin - 100', 'dataMax + 100']}
                tick={{ fontSize: 10, fill: 'var(--muted-foreground)' }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v: number) => v.toLocaleString()}
                width={50}
              />
              <YAxis yAxisId="nq" hide />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'var(--popover)',
                  border: '1px solid var(--border)',
                  borderRadius: 8,
                  fontSize: 12,
                }}
                formatter={(value: number, name: string) => [
                  value.toLocaleString(undefined, { maximumFractionDigits: 0 }),
                  name === 'sp500' ? 'S&P 500' : 'NASDAQ',
                ]}
              />
              <Line
                yAxisId="sp"
                type="monotone"
                dataKey="sp500"
                stroke="#1D8A84"
                strokeWidth={2}
                dot={false}
                name="sp500"
              />
              <Line
                yAxisId="nq"
                type="monotone"
                dataKey="nasdaq"
                stroke="#7C5CBF"
                strokeWidth={1.5}
                dot={false}
                name="nasdaq"
                strokeDasharray="5 5"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-3 flex gap-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1.5">
            <span className="h-0.5 w-4 bg-teal-500" /> S&P 500
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-0.5 w-4 border-t-2 border-dashed border-[#7C5CBF]" /> NASDAQ
          </span>
        </div>
      </div>

      {/* Rate tracking section */}
      <div className="rounded-xl border bg-card p-4">
        <h2 className="mb-2 text-sm font-semibold">Rate Tracking</h2>
        <p className="mb-4 text-xs text-muted-foreground">10-Year Treasury Yield: <span className="tabular-nums font-medium text-foreground">{currentYield10y.toFixed(2)}%</span></p>
        <div className="h-40">
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
                formatter={(value: number) => [`${value.toFixed(2)}%`, '10yr Treasury']}
              />
              {alerts
                .filter((a) => a.active && a.target === 'treasury10y')
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
                dataKey="yield10y"
                stroke="#C79A2B"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Alerts management */}
      <div className="rounded-xl border bg-card p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold">Price &amp; Rate Alerts</h2>
          <Dialog>
            <DialogTrigger asChild>
              <Button size="sm" variant="outline">
                <Plus className="mr-1.5 h-3.5 w-3.5" />
                Add alert
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>New Alert</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div>
                  <Label className="text-xs">Target</Label>
                  <div className="mt-1.5 flex gap-2">
                    {(['sp500', 'nasdaq', 'treasury10y'] as const).map((t) => (
                      <button
                        key={t}
                        onClick={() => setNewTarget(t)}
                        className={`rounded-md border px-3 py-1.5 text-sm ${
                          newTarget === t
                            ? 'border-teal-500 bg-teal-500/10 text-teal-700 dark:text-teal-300'
                            : 'text-muted-foreground'
                        }`}
                      >
                        {targetLabels[t]}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <Label htmlFor="threshold" className="text-xs">
                    {newTarget === 'treasury10y' ? 'Alert when yield drops below' : 'Alert when price reaches'}
                  </Label>
                  <div className="relative mt-1.5">
                    <Input
                      id="threshold"
                      type="number"
                      step={newTarget === 'treasury10y' ? '0.01' : '10'}
                      value={newThreshold}
                      onChange={(e) => setNewThreshold(e.target.value)}
                      placeholder={newTarget === 'treasury10y' ? '6.50' : '5500'}
                      className="pr-6 tabular-nums"
                    />
                    {newTarget === 'treasury10y' && (
                      <span className="absolute right-3 top-2 text-sm text-muted-foreground">
                        %
                      </span>
                    )}
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
            No alerts set. Add one to get notified when prices or rates hit your target.
          </p>
        ) : (
          <div className="space-y-2">
            {alerts.map((alert) => {
              const current = getCurrentValue(alert.target);
              const triggered = alert.target === 'treasury10y'
                ? current <= alert.threshold
                : current >= alert.threshold;
              const distance = Math.abs(current - alert.threshold);

              return (
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
                        {targetLabels[alert.target]}{' '}
                        {alert.target === 'treasury10y' ? 'below' : 'reaches'}{' '}
                        <span className="tabular-nums">{formatValue(alert.target, alert.threshold)}</span>
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Currently{' '}
                        <span className="tabular-nums">
                          {formatValue(alert.target, current)}
                        </span>
                        {' — '}
                        {triggered ? (
                          <Badge className="bg-pos/10 text-pos text-[10px]">Triggered</Badge>
                        ) : (
                          <span>
                            {formatValue(alert.target, distance)} away
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
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
