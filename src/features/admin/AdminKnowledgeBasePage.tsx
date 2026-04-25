import { useEffect, useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { RefreshCw } from 'lucide-react';
import apiClient from '@/api/apiClient';

interface KBStats {
  total_documents: number;
  total_chunks: number;
  vector_count: number;
  index_type: string;
  embedding_model: string;
  last_reindex: string | null;
}

interface KBDocument {
  id: string;
  filename: string;
  source_type: string;
  chunk_count: number;
  created_at: string;
}

// Simplified knowledge base page using the two existing backend endpoints:
// GET /admin/knowledge-base/stats and GET /admin/knowledge-base/documents.
// The full KnowledgeBaseDashboard called 6 endpoints that don't exist.
// Re-enable the full dashboard when those endpoints are built.

export default function AdminKnowledgeBasePage() {
  const [stats, setStats] = useState<KBStats | null>(null);
  const [documents, setDocuments] = useState<KBDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsRes, docsRes] = await Promise.allSettled([
        apiClient.get('/admin/knowledge-base/stats'),
        apiClient.get('/admin/knowledge-base/documents'),
      ]);

      if (statsRes.status === 'fulfilled') {
        setStats(statsRes.value.data);
      }
      if (docsRes.status === 'fulfilled') {
        const docs = docsRes.value.data;
        setDocuments(Array.isArray(docs) ? docs : docs?.documents || []);
      }

      // Show error for failures
      if (statsRes.status === 'rejected' && docsRes.status === 'rejected') {
        setError('Failed to load knowledge base data. Check admin permissions.');
      } else if (statsRes.status === 'rejected') {
        setError('Could not load statistics. Document list loaded successfully.');
      } else if (docsRes.status === 'rejected') {
        setError('Could not load document list. Statistics loaded successfully.');
      }
    } catch {
      setError('Failed to load knowledge base data.');
    } finally {
      setLoading(false);
    }
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps -- fetch once on mount
  useEffect(() => { fetchData(); }, []);

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-serif text-2xl font-semibold">Knowledge Base</h1>
          <p className="mt-0.5 text-sm text-muted-foreground">
            Document management and RAG index statistics.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={fetchData}
          disabled={loading}
        >
          <RefreshCw className={`mr-1.5 h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {error && (
        <div className="rounded-lg border border-neg/20 bg-neg/5 p-4 text-sm text-neg">
          {error}
        </div>
      )}

      {/* Stats cards */}
      {stats && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div className="rounded-xl border bg-card p-4">
            <p className="text-xs font-medium text-muted-foreground">Vector Count</p>
            <p className="mt-1 tabular-nums text-2xl font-semibold">
              {(stats.vector_count ?? 0).toLocaleString()}
            </p>
          </div>
          <div className="rounded-xl border bg-card p-4">
            <p className="text-xs font-medium text-muted-foreground">Documents</p>
            <p className="mt-1 tabular-nums text-2xl font-semibold">
              {(stats.total_documents ?? 0).toLocaleString()}
            </p>
          </div>
          <div className="rounded-xl border bg-card p-4">
            <p className="text-xs font-medium text-muted-foreground">Chunks</p>
            <p className="mt-1 tabular-nums text-2xl font-semibold">
              {(stats.total_chunks ?? 0).toLocaleString()}
            </p>
          </div>
          <div className="rounded-xl border bg-card p-4">
            <p className="text-xs font-medium text-muted-foreground">Embedding Model</p>
            <p className="mt-1 truncate text-sm font-medium">
              {stats.embedding_model || 'N/A'}
            </p>
          </div>
        </div>
      )}

      {/* Documents table */}
      <div className="rounded-xl border bg-card">
        <div className="border-b px-4 py-3">
          <h2 className="text-sm font-semibold">
            Documents {!loading && `(${documents.length})`}
          </h2>
        </div>
        {loading ? (
          <div className="p-8 text-center text-sm text-muted-foreground">Loading...</div>
        ) : documents.length === 0 ? (
          <div className="p-8 text-center text-sm text-muted-foreground">
            No documents in the knowledge base yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-xs text-muted-foreground">
                  <th className="px-4 py-2 font-medium">Filename</th>
                  <th className="px-4 py-2 font-medium">Source</th>
                  <th className="px-4 py-2 font-medium">Chunks</th>
                  <th className="px-4 py-2 font-medium">Created</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => (
                  <tr key={doc.id} className="border-b last:border-0 hover:bg-muted/50">
                    <td className="px-4 py-2 font-medium">{doc.filename}</td>
                    <td className="px-4 py-2">
                      <Badge variant="secondary" className="text-[10px]">
                        {doc.source_type}
                      </Badge>
                    </td>
                    <td className="px-4 py-2 tabular-nums">{doc.chunk_count}</td>
                    <td className="px-4 py-2 text-muted-foreground">
                      {doc.created_at ? new Date(doc.created_at).toLocaleDateString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
