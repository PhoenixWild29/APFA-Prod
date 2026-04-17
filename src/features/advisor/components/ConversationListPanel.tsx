import { useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Plus, Search, MessageSquare } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import type { Conversation } from '@/types/conversation';

interface ConversationListPanelProps {
  conversations: Conversation[];
  isLoading: boolean;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  onNewConversation: () => void;
}

function groupByDate(conversations: Conversation[]) {
  const groups: { label: string; items: Conversation[] }[] = [];
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today.getTime() - 86400000);
  const weekAgo = new Date(today.getTime() - 7 * 86400000);

  const todayItems: Conversation[] = [];
  const yesterdayItems: Conversation[] = [];
  const thisWeekItems: Conversation[] = [];
  const olderItems: Conversation[] = [];

  for (const c of conversations) {
    const d = new Date(c.updated_at);
    if (d >= today) todayItems.push(c);
    else if (d >= yesterday) yesterdayItems.push(c);
    else if (d >= weekAgo) thisWeekItems.push(c);
    else olderItems.push(c);
  }

  if (todayItems.length) groups.push({ label: 'Today', items: todayItems });
  if (yesterdayItems.length) groups.push({ label: 'Yesterday', items: yesterdayItems });
  if (thisWeekItems.length) groups.push({ label: 'This week', items: thisWeekItems });
  if (olderItems.length) groups.push({ label: 'Older', items: olderItems });

  return groups;
}

export default function ConversationListPanel({
  conversations,
  isLoading,
  searchQuery,
  onSearchChange,
  onNewConversation,
}: ConversationListPanelProps) {
  const navigate = useNavigate();
  const { conversationId } = useParams();

  const filtered = useMemo(() => {
    if (!searchQuery.trim()) return conversations;
    const q = searchQuery.toLowerCase();
    return conversations.filter(
      (c) =>
        c.title.toLowerCase().includes(q) ||
        c.preview?.toLowerCase().includes(q)
    );
  }, [conversations, searchQuery]);

  const groups = useMemo(() => groupByDate(filtered), [filtered]);

  return (
    <div className="flex h-full w-[280px] flex-col border-r bg-sidebar">
      {/* Header */}
      <div className="flex items-center justify-between border-b p-3">
        <h2 className="text-sm font-semibold">Conversations</h2>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          onClick={onNewConversation}
          aria-label="New conversation"
        >
          <Plus className="h-4 w-4" />
        </Button>
      </div>

      {/* Search */}
      <div className="p-2">
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
          <Input
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search threads..."
            className="h-8 pl-8 text-xs"
          />
        </div>
      </div>

      {/* Thread list */}
      <ScrollArea className="flex-1">
        {isLoading ? (
          <div className="space-y-2 p-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="space-y-1.5">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-full" />
              </div>
            ))}
          </div>
        ) : groups.length === 0 ? (
          <div className="flex flex-col items-center gap-3 p-8 text-center">
            <MessageSquare className="h-8 w-8 text-muted-foreground/50" />
            <div>
              <p className="text-sm font-medium">No conversations yet</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Start by asking your financial advisor a question.
              </p>
            </div>
            <Button size="sm" onClick={onNewConversation}>
              <Plus className="mr-1.5 h-3.5 w-3.5" />
              New conversation
            </Button>
          </div>
        ) : (
          <div className="p-2">
            {groups.map((group) => (
              <div key={group.label} className="mb-3">
                <p className="mb-1 px-2 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                  {group.label}
                </p>
                {group.items.map((conv) => (
                  <button
                    key={conv.id}
                    onClick={() => navigate(`/app/advisor/c/${conv.id}`)}
                    className={cn(
                      'w-full rounded-md px-2 py-2 text-left transition-colors',
                      conv.id === conversationId
                        ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                        : 'hover:bg-sidebar-accent/50'
                    )}
                  >
                    <p className="truncate text-sm font-medium">{conv.title}</p>
                    {conv.preview && (
                      <p className="mt-0.5 truncate text-xs text-muted-foreground">
                        {conv.preview}
                      </p>
                    )}
                  </button>
                ))}
              </div>
            ))}
          </div>
        )}
      </ScrollArea>
    </div>
  );
}
