import { useEffect, useState } from 'react';
import { ScrollText, ChevronLeft, ChevronRight, Filter } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import apiClient from '@/api/apiClient';

interface AuditEntry {
  id: number;
  timestamp: string | null;
  source_connector: string;
  action: string;
  status: string;
  chunk_count: number;
  parent_document_id: string;
  content_hash: string;
  error_code: string;
}

interface AuditResponse {
  entries: AuditEntry[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

const STATUS_COLORS: Record<string, string> = {
  success: 'bg-pos/10 text-pos',
  partial: 'bg-warn/10 text-warn',
  rejected: 'bg-neg/10 text-neg',
};

export default function AdminAuditPage() {
  const [data, setData] = useState<AuditResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [actionFilter, setActionFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    setLoading(true);
    setError(null);
    const params: Record<string, string | number> = { page, page_size: 25 };
    if (actionFilter) params.action = actionFilter;
    if (statusFilter) params.status = statusFilter;

    apiClient
      .get<AuditResponse>('/admin/audit-logs', { params })
      .then((res) => setData(res.data))
      .catch((err) => setError(err.response?.data?.detail || 'Failed to load audit logs'))
      .finally(() => setLoading(false));
  }, [page, actionFilter, statusFilter]);

  const entries = data?.entries ?? [];

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-serif text-2xl font-semibold">Pipeline Audit Log</h1>
          <p className="mt-0.5 text-sm text-muted-foreground">
            {data ? `${data.total_count} pipeline event${data.total_count !== 1 ? 's' : ''}` : 'Loading...'}
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => setShowFilters((f) => !f)}>
          <Filter className="mr-1.5 h-3.5 w-3.5" />
          Filter
        </Button>
      </div>

      {showFilters && (
        <div className="flex flex-wrap gap-3 rounded-lg border bg-muted/30 p-4">
          <Select
            value={actionFilter || '__all__'}
            onValueChange={(v) => {
              setPage(1);
              setActionFilter(!v || v === '__all__' ? '' : v);
            }}
          >
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Action" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="__all__">All actions</SelectItem>
              <SelectItem value="create">create</SelectItem>
              <SelectItem value="update">update</SelectItem>
              <SelectItem value="delete">delete</SelectItem>
            </SelectContent>
          </Select>

          <Select
            value={statusFilter || '__all__'}
            onValueChange={(v) => {
              setPage(1);
              setStatusFilter(!v || v === '__all__' ? '' : v);
            }}
          >
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="__all__">All statuses</SelectItem>
              <SelectItem value="success">success</SelectItem>
              <SelectItem value="partial">partial</SelectItem>
              <SelectItem value="rejected">rejected</SelectItem>
            </SelectContent>
          </Select>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-neg/20 bg-neg/5 p-4 text-sm text-neg">
          {error}
        </div>
      )}

      <div className="space-y-2">
        {loading ? (
          <div className="rounded-lg border bg-card p-8 text-center text-sm text-muted-foreground">
            Loading...
          </div>
        ) : entries.length === 0 ? (
          <div className="rounded-lg border bg-card p-8 text-center text-sm text-muted-foreground">
            No audit log entries found.
          </div>
        ) : (
          entries.map((entry) => (
            <div
              key={entry.id}
              className="flex items-start gap-4 rounded-lg border bg-card p-4"
            >
              <ScrollText className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <Badge
                    className={`text-[10px] ${STATUS_COLORS[entry.status] ?? ''}`}
                    variant="secondary"
                  >
                    {entry.status}
                  </Badge>
                  <code className="text-xs text-muted-foreground">{entry.action}</code>
                  <Badge variant="secondary" className="text-[10px]">
                    {entry.source_connector}
                  </Badge>
                </div>
                {entry.parent_document_id && (
                  <p className="mt-1 truncate text-sm">{entry.parent_document_id}</p>
                )}
                <p className="mt-1 text-xs text-muted-foreground">
                  {entry.chunk_count > 0 && `${entry.chunk_count} chunks`}
                  {entry.chunk_count > 0 && entry.error_code && ' · '}
                  {entry.error_code && (
                    <span className="text-neg">{entry.error_code}</span>
                  )}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {entry.timestamp
                    ? new Date(entry.timestamp).toLocaleString()
                    : '—'}
                </p>
              </div>
            </div>
          ))
        )}
      </div>

      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-xs text-muted-foreground">
            Page {data.page} of {data.total_pages}
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
            >
              <ChevronLeft className="mr-1 h-3.5 w-3.5" />
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= data.total_pages}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
              <ChevronRight className="ml-1 h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
