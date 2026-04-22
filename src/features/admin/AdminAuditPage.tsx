import { ScrollText, Filter } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

// Placeholder — will wire to audit log API
const DEMO_EVENTS = [
  { id: '1', action: 'user.login', user: 'admin', timestamp: '2026-04-17T09:30:00Z', details: 'Successful login from 67.205.140.55' },
  { id: '2', action: 'document.upload', user: 'admin', timestamp: '2026-04-17T09:25:00Z', details: 'Uploaded vanguard_capital_markets_2026.pdf (2.1 MB)' },
  { id: '3', action: 'advice.generated', user: 'demo_user', timestamp: '2026-04-17T08:12:00Z', details: 'Query: "AI infrastructure investment thesis" — 3 sources cited' },
  { id: '4', action: 'index.rebuild', user: 'system', timestamp: '2026-04-16T23:00:00Z', details: 'FAISS index rebuilt: 20 docs, 142 chunks' },
  { id: '5', action: 'user.register', user: 'demo_user', timestamp: '2026-04-16T14:30:00Z', details: 'New account created' },
];

function actionBadge(action: string) {
  if (action.startsWith('user.')) return { label: 'Auth', variant: 'secondary' as const };
  if (action.startsWith('document.')) return { label: 'Document', variant: 'default' as const };
  if (action.startsWith('advice.')) return { label: 'Advisor', variant: 'secondary' as const };
  if (action.startsWith('index.')) return { label: 'System', variant: 'secondary' as const };
  return { label: 'Other', variant: 'secondary' as const };
}

export default function AdminAuditPage() {
  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-serif text-2xl font-semibold">Audit Log</h1>
          <p className="mt-0.5 text-sm text-muted-foreground">
            System activity and security events.
          </p>
        </div>
        <Button variant="outline" size="sm">
          <Filter className="mr-1.5 h-3.5 w-3.5" />
          Filter
        </Button>
      </div>

      <div className="space-y-2">
        {DEMO_EVENTS.map((event) => {
          const badge = actionBadge(event.action);
          return (
            <div
              key={event.id}
              className="flex items-start gap-4 rounded-lg border bg-card p-4"
            >
              <ScrollText className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <Badge variant={badge.variant} className="text-[10px]">
                    {badge.label}
                  </Badge>
                  <code className="text-xs text-muted-foreground">{event.action}</code>
                </div>
                <p className="mt-1 text-sm">{event.details}</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {event.user} &middot;{' '}
                  {new Date(event.timestamp).toLocaleString()}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
