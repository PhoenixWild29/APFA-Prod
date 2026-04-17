import { lazy, Suspense } from 'react';
import { Skeleton } from '@/components/ui/skeleton';

const KnowledgeBaseDashboard = lazy(
  () => import('@/pages/admin/KnowledgeBaseDashboard')
);

export default function AdminKnowledgeBasePage() {
  return (
    <div className="space-y-4 p-6">
      <div>
        <h1 className="font-serif text-2xl font-semibold">Knowledge Base</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Document management, processing, and search performance.
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
          <KnowledgeBaseDashboard />
        </Suspense>
      </div>
    </div>
  );
}
