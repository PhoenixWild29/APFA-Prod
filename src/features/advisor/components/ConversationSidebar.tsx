import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Trash2, MessageSquare } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import {
  useConversationList,
  useCreateConversation,
  useDeleteConversation,
} from '@/hooks/useConversations';
import { useConversationStore } from '@/store/conversationStore';
import { cn } from '@/lib/utils';

export default function ConversationSidebar() {
  const navigate = useNavigate();
  const { data: conversations, isLoading } = useConversationList();
  const createMutation = useCreateConversation();
  const deleteMutation = useDeleteConversation();
  const { activeConversationId, setActiveConversation, clearMessages } =
    useConversationStore();

  const handleNew = useCallback(() => {
    clearMessages();
    navigate('/app/advisor');
  }, [clearMessages, navigate]);

  const handleSelect = useCallback(
    (id: string) => {
      if (id === activeConversationId) return;
      setActiveConversation(id);
      navigate(`/app/advisor/${id}`);
    },
    [activeConversationId, setActiveConversation, navigate]
  );

  const handleDelete = useCallback(
    (e: React.MouseEvent, id: string) => {
      e.stopPropagation();
      deleteMutation.mutate(id, {
        onSuccess: () => {
          if (activeConversationId === id) {
            clearMessages();
          }
        },
      });
    },
    [activeConversationId, clearMessages, deleteMutation]
  );

  return (
    <div className="flex h-full w-64 flex-col border-r border-border bg-muted/30">
      <div className="flex items-center justify-between p-3">
        <span className="text-sm font-medium text-muted-foreground">
          Conversations
        </span>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          onClick={handleNew}
          title="New conversation"
        >
          <Plus className="h-4 w-4" />
        </Button>
      </div>

      <ScrollArea className="flex-1">
        <div className="space-y-0.5 px-2 pb-2">
          {isLoading &&
            Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full rounded-md" />
            ))}

          {conversations?.map((conv) => (
            <button
              key={conv.id}
              onClick={() => handleSelect(conv.id)}
              className={cn(
                'group flex w-full items-start gap-2 rounded-md px-2 py-2 text-left text-sm transition-colors hover:bg-accent',
                activeConversationId === conv.id && 'bg-accent'
              )}
            >
              <MessageSquare className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium">{conv.title}</p>
                {conv.preview && (
                  <p className="truncate text-xs text-muted-foreground">
                    {conv.preview}
                  </p>
                )}
              </div>
              <button
                onClick={(e) => handleDelete(e, conv.id)}
                className="hidden shrink-0 rounded p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive group-hover:block"
                title="Delete conversation"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </button>
          ))}

          {!isLoading && conversations?.length === 0 && (
            <p className="px-2 py-4 text-center text-xs text-muted-foreground">
              No conversations yet. Start chatting!
            </p>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
