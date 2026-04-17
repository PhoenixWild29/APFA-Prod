import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { MessageSquare, Plus, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import apiClient from '@/api/apiClient';
import WidgetCard from '../components/WidgetCard';
import type { Conversation } from '@/types/conversation';
import type { WidgetId } from '@/store/preferencesStore';

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

interface RecentConversationsWidgetProps {
  onHide: (id: WidgetId) => void;
}

export default function RecentConversationsWidget({
  onHide,
}: RecentConversationsWidgetProps) {
  const navigate = useNavigate();

  const { data: conversations = [], isLoading } = useQuery({
    queryKey: ['conversations', { limit: 4 }],
    queryFn: async () => {
      try {
        const res = await apiClient.get<Conversation[]>('/conversations', {
          params: { limit: 4 },
        });
        return res.data;
      } catch {
        return [];
      }
    },
    staleTime: 60_000,
  });

  return (
    <WidgetCard
      id="recent-conversations"
      title="Recent Conversations"
      onHide={onHide}
      isLoading={isLoading}
    >
      {conversations.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-4 text-center">
          <MessageSquare className="h-8 w-8 text-muted-foreground/40" />
          <p className="text-xs text-muted-foreground">
            No conversations yet. Start by asking your advisor a question.
          </p>
          <Button size="sm" onClick={() => navigate('/app/advisor')}>
            <Plus className="mr-1.5 h-3.5 w-3.5" />
            Start conversation
          </Button>
        </div>
      ) : (
        <div className="space-y-1">
          {conversations.map((conv) => (
            <button
              key={conv.id}
              onClick={() => navigate(`/app/advisor/c/${conv.id}`)}
              className="flex w-full items-center gap-3 rounded-lg px-2 py-2 text-left transition-colors hover:bg-muted"
            >
              <MessageSquare className="h-4 w-4 shrink-0 text-muted-foreground" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{conv.title}</p>
                {conv.preview && (
                  <p className="truncate text-xs text-muted-foreground">
                    {conv.preview}
                  </p>
                )}
              </div>
              <span className="shrink-0 text-[10px] text-muted-foreground">
                {timeAgo(conv.updated_at)}
              </span>
            </button>
          ))}
          <Button
            variant="ghost"
            size="sm"
            className="mt-1 w-full text-xs"
            onClick={() => navigate('/app/advisor')}
          >
            View all conversations
            <ArrowRight className="ml-1 h-3 w-3" />
          </Button>
        </div>
      )}
    </WidgetCard>
  );
}
