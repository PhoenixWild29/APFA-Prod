import { useState } from 'react';
import { FileText, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import type { Source } from '@/types/conversation';

interface SourceCardsProps {
  sources: Source[];
}

export default function SourceCards({ sources }: SourceCardsProps) {
  const [expanded, setExpanded] = useState(false);

  if (!sources.length) return null;

  const visible = expanded ? sources : sources.slice(0, 3);
  const hasMore = sources.length > 3;

  return (
    <div className="mt-3">
      <p className="mb-2 text-xs font-medium text-muted-foreground">
        Sources ({sources.length})
      </p>
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {visible.map((source, idx) => (
          <div
            key={source.document_id + idx}
            className="flex flex-col gap-1.5 rounded-lg border bg-card p-3 shadow-sm transition-colors hover:bg-accent/50"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-1.5">
                <FileText className="h-3.5 w-3.5 shrink-0 text-teal-600 dark:text-teal-300" />
                <span className="text-xs font-medium leading-tight line-clamp-1">
                  {source.title}
                </span>
              </div>
              <Badge
                variant="secondary"
                className={cn(
                  'shrink-0 tabular-nums text-[10px]',
                  source.relevance_score >= 80
                    ? 'bg-pos/10 text-pos'
                    : source.relevance_score >= 50
                      ? 'bg-gold-100 text-gold-700'
                      : 'bg-muted text-muted-foreground'
                )}
              >
                {source.relevance_score}%
              </Badge>
            </div>
            {source.section && (
              <span className="text-[10px] text-muted-foreground">
                {source.section}
              </span>
            )}
            <p className="text-xs leading-relaxed text-muted-foreground line-clamp-3">
              {source.excerpt}
            </p>
          </div>
        ))}
      </div>
      {hasMore && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-2 flex items-center gap-1 text-xs text-muted-foreground transition-colors hover:text-foreground"
        >
          {expanded ? (
            <>
              <ChevronUp className="h-3 w-3" /> Show less
            </>
          ) : (
            <>
              <ChevronDown className="h-3 w-3" /> Show {sources.length - 3} more
            </>
          )}
        </button>
      )}
    </div>
  );
}
