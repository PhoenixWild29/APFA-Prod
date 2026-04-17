import { lazy, Suspense } from 'react';
import { Skeleton } from '@/components/ui/skeleton';

// Reuse existing dashboard — wrap with new design chrome
const SystemMonitoringDashboard = lazy(
  () => import('@/pages/admin/SystemMonitoringDashboard')
);

export default function AdminMonitoringPage() {
  return (
    <div className="space-y-4 p-6">
      <div>
        <h1 className="font-serif text-2xl font-semibold">System Monitoring</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Real-time system health, workers, and performance metrics.
        </p>
      </div>
      <div className="rounded-xl border bg-card p-4">
        <Suspense
          fallback={
            <div className="space-y-4">
              <Skeleton className="h-8 w-48" />
              <Skeleton className="h-64 w-full" />
            </div>
          }
        >
          <SystemMonitoringDashboard />
        </Suspense>
      </div>
    </div>
  );
}
