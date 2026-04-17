import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { FileText, Upload, ArrowRight, MessageSquare } from 'lucide-react';
import { Button } from '@/components/ui/button';
import apiClient from '@/api/apiClient';
import WidgetCard from '../components/WidgetCard';
import type { WidgetId } from '@/store/preferencesStore';

interface DocumentSummary {
  id: string;
  filename: string;
  file_size: number;
  uploaded_at: string;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / 1048576).toFixed(1)} MB`;
}

interface DocumentsWidgetProps {
  onHide: (id: WidgetId) => void;
}

export default function DocumentsWidget({ onHide }: DocumentsWidgetProps) {
  const navigate = useNavigate();

  const { data: documents = [], isLoading } = useQuery({
    queryKey: ['documents', { limit: 4 }],
    queryFn: async () => {
      try {
        const res = await apiClient.get<DocumentSummary[]>('/documents', {
          params: { limit: 4 },
        });
        return Array.isArray(res.data) ? res.data : [];
      } catch {
        return [];
      }
    },
    staleTime: 60_000,
  });

  return (
    <WidgetCard
      id="documents"
      title="Recent Documents"
      onHide={onHide}
      isLoading={isLoading}
    >
      {documents.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-4 text-center">
          <FileText className="h-8 w-8 text-muted-foreground/40" />
          <p className="text-xs text-muted-foreground">
            Upload documents to ground your advisor in your financial data.
          </p>
          <Button
            size="sm"
            onClick={() => navigate('/app/documents/upload')}
          >
            <Upload className="mr-1.5 h-3.5 w-3.5" />
            Upload document
          </Button>
        </div>
      ) : (
        <div className="space-y-1">
          {documents.map((doc) => (
            <div
              key={doc.id}
              className="flex items-center gap-3 rounded-lg px-2 py-2 transition-colors hover:bg-muted"
            >
              <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">
                  {doc.filename}
                </p>
                <p className="text-[10px] text-muted-foreground tabular-nums">
                  {formatBytes(doc.file_size)} &middot;{' '}
                  {new Date(doc.uploaded_at).toLocaleDateString()}
                </p>
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 shrink-0"
                onClick={() => navigate('/app/advisor')}
                aria-label="Ask about this document"
              >
                <MessageSquare className="h-3.5 w-3.5" />
              </Button>
            </div>
          ))}
          <Button
            variant="ghost"
            size="sm"
            className="mt-1 w-full text-xs"
            onClick={() => navigate('/app/documents')}
          >
            View all documents
            <ArrowRight className="ml-1 h-3 w-3" />
          </Button>
        </div>
      )}
    </WidgetCard>
  );
}
