import { useNavigate } from 'react-router-dom';
import {
  FileText,
  MessageSquare,
  Clock,
  CheckCircle2,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';

export interface DocumentItem {
  id: string;
  filename: string;
  file_size: number;
  uploaded_at: string;
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
  document_type?: string;
  tags?: string[];
  chunk_count?: number;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / 1048576).toFixed(1)} MB`;
}

function statusConfig(status: DocumentItem['processing_status']) {
  switch (status) {
    case 'completed':
      return { icon: CheckCircle2, label: 'Indexed', className: 'text-pos' };
    case 'processing':
      return { icon: Loader2, label: 'Processing', className: 'text-warn animate-spin' };
    case 'failed':
      return { icon: AlertCircle, label: 'Failed', className: 'text-neg' };
    default:
      return { icon: Clock, label: 'Pending', className: 'text-muted-foreground' };
  }
}

interface DocumentCardProps {
  document: DocumentItem;
}

export default function DocumentCard({ document }: DocumentCardProps) {
  const navigate = useNavigate();
  const status = statusConfig(document.processing_status);
  const StatusIcon = status.icon;

  return (
    <div
      className="group flex items-center gap-4 rounded-lg border bg-card p-4 transition-colors hover:bg-accent/50 cursor-pointer"
      onClick={() => navigate(`/app/documents/${document.id}`)}
    >
      {/* File icon */}
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-muted">
        <FileText className="h-5 w-5 text-muted-foreground" />
      </div>

      {/* Info */}
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{document.filename}</p>
        <div className="mt-1 flex items-center gap-3 text-xs text-muted-foreground">
          <span className="tabular-nums">{formatBytes(document.file_size)}</span>
          <span>&middot;</span>
          <span>{new Date(document.uploaded_at).toLocaleDateString()}</span>
          {document.chunk_count != null && (
            <>
              <span>&middot;</span>
              <span>{document.chunk_count} chunks</span>
            </>
          )}
        </div>
        {document.tags && document.tags.length > 0 && (
          <div className="mt-1.5 flex flex-wrap gap-1">
            {document.tags.map((tag) => (
              <Badge key={tag} variant="secondary" className="text-[10px] px-1.5 py-0">
                {tag}
              </Badge>
            ))}
          </div>
        )}
      </div>

      {/* Status */}
      <div className="flex items-center gap-2">
        <Tooltip>
          <TooltipTrigger>
            <StatusIcon className={cn('h-4 w-4', status.className)} />
          </TooltipTrigger>
          <TooltipContent>{status.label}</TooltipContent>
        </Tooltip>

        {/* Ask button */}
        {document.processing_status === 'completed' && (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 opacity-0 group-hover:opacity-100"
                onClick={(e) => {
                  e.stopPropagation();
                  navigate('/app/advisor', {
                    state: { groundingDocId: document.id, groundingDocName: document.filename },
                  });
                }}
                aria-label="Ask about this document"
              >
                <MessageSquare className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Ask about this document</TooltipContent>
          </Tooltip>
        )}
      </div>
    </div>
  );
}
