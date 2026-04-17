import { useNavigate, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowLeft,
  FileText,
  MessageSquare,
  CheckCircle2,
  Clock,
  AlertCircle,
  Loader2,
  Download,
  Hash,
  Calendar,
  HardDrive,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import apiClient from '@/api/apiClient';

interface DocumentDetail {
  id: string;
  filename: string;
  file_size: number;
  uploaded_at: string;
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
  document_type?: string;
  tags?: string[];
  chunk_count?: number;
  content_hash?: string;
  similar_documents?: { id: string; filename: string; score: number }[];
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / 1048576).toFixed(1)} MB`;
}

export default function DocumentDetailPage() {
  const { documentId } = useParams();
  const navigate = useNavigate();

  const { data: doc, isLoading } = useQuery({
    queryKey: ['document', documentId],
    queryFn: async () => {
      try {
        const res = await apiClient.get<DocumentDetail>(
          `/documents/${documentId}/status`
        );
        return res.data;
      } catch {
        return null;
      }
    },
    enabled: !!documentId,
    staleTime: 30_000,
  });

  // Fetch similar documents
  const { data: similar } = useQuery({
    queryKey: ['document-similar', documentId],
    queryFn: async () => {
      try {
        const res = await apiClient.get(`/documents/${documentId}/similar`);
        return res.data;
      } catch {
        return [];
      }
    },
    enabled: !!documentId,
    staleTime: 120_000,
  });

  if (isLoading) {
    return (
      <div className="space-y-6 p-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!doc) {
    return (
      <div className="flex flex-col items-center gap-4 p-16 text-center">
        <FileText className="h-12 w-12 text-muted-foreground/30" />
        <p className="font-medium">Document not found</p>
        <Button variant="outline" onClick={() => navigate('/app/documents')}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to documents
        </Button>
      </div>
    );
  }

  const statusMap = {
    completed: { icon: CheckCircle2, label: 'Indexed', color: 'text-pos' },
    processing: { icon: Loader2, label: 'Processing', color: 'text-warn' },
    failed: { icon: AlertCircle, label: 'Failed', color: 'text-neg' },
    pending: { icon: Clock, label: 'Pending', color: 'text-muted-foreground' },
  };
  const status = statusMap[doc.processing_status] ?? statusMap.pending;
  const StatusIcon = status.icon;

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-6">
      {/* Back button */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => navigate('/app/documents')}
        className="gap-1.5 text-muted-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Documents
      </Button>

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-muted">
            <FileText className="h-6 w-6 text-muted-foreground" />
          </div>
          <div>
            <h1 className="text-xl font-semibold">{doc.filename}</h1>
            <div className="mt-1 flex items-center gap-2">
              <StatusIcon
                className={cn('h-4 w-4', status.color, doc.processing_status === 'processing' && 'animate-spin')}
              />
              <span className={cn('text-sm', status.color)}>{status.label}</span>
            </div>
          </div>
        </div>

        {/* Ask about this document */}
        {doc.processing_status === 'completed' && (
          <Button
            onClick={() =>
              navigate('/app/advisor', {
                state: { groundingDocId: doc.id, groundingDocName: doc.filename },
              })
            }
          >
            <MessageSquare className="mr-2 h-4 w-4" />
            Ask about this
          </Button>
        )}
      </div>

      <Separator />

      {/* Metadata grid */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <MetaItem icon={HardDrive} label="Size" value={formatBytes(doc.file_size)} />
        <MetaItem
          icon={Calendar}
          label="Uploaded"
          value={new Date(doc.uploaded_at).toLocaleDateString()}
        />
        <MetaItem
          icon={Hash}
          label="Chunks"
          value={doc.chunk_count != null ? String(doc.chunk_count) : '—'}
        />
        <MetaItem
          icon={FileText}
          label="Type"
          value={doc.document_type ?? doc.filename.split('.').pop()?.toUpperCase() ?? '—'}
        />
      </div>

      {/* Tags */}
      {doc.tags && doc.tags.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-medium text-muted-foreground">Tags</p>
          <div className="flex flex-wrap gap-1.5">
            {doc.tags.map((tag) => (
              <Badge key={tag} variant="secondary">
                {tag}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Similar documents */}
      {Array.isArray(similar) && similar.length > 0 && (
        <div>
          <p className="mb-3 text-sm font-semibold">Similar Documents</p>
          <div className="space-y-2">
            {similar.map((s: { id: string; filename: string; score: number }) => (
              <button
                key={s.id}
                onClick={() => navigate(`/app/documents/${s.id}`)}
                className="flex w-full items-center gap-3 rounded-lg border p-3 text-left transition-colors hover:bg-accent/50"
              >
                <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
                <span className="flex-1 truncate text-sm">{s.filename}</span>
                <Badge variant="secondary" className="tabular-nums text-[10px]">
                  {Math.round(s.score * 100)}% match
                </Badge>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function MetaItem({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-lg border bg-card p-3">
      <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
        <Icon className="h-3.5 w-3.5" />
        {label}
      </div>
      <p className="mt-1 text-sm font-medium tabular-nums">{value}</p>
    </div>
  );
}
