import { useCallback, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useConversationStore } from '@/store/conversationStore';
import { useAdvisorStream } from './hooks/useAdvisorStream';
import { useConversation, useCreateConversation } from '@/hooks/useConversations';
import { setMessageFeedback } from '@/api/conversationApi';
import ThreadView from './components/ThreadView';
import Composer from './components/Composer';
import ConversationSidebar from './components/ConversationSidebar';

export default function AdvisorPage() {
  const { conversationId } = useParams<{ conversationId?: string }>();
  const navigate = useNavigate();
  const {
    activeConversationId,
    draft,
    setDraft,
    messages,
    setActiveConversation,
    hydrateMessages,
  } = useConversationStore();
  const {
    sendMessage,
    isStreaming,
    streamingContent,
    streamingSources,
    streamingFollowUps,
    abortStream,
  } = useAdvisorStream();

  const createMutation = useCreateConversation();
  const { data: conversationDetail } = useConversation(activeConversationId);

  useEffect(() => {
    if (conversationId && conversationId !== activeConversationId) {
      setActiveConversation(conversationId);
    }
  }, [conversationId, activeConversationId, setActiveConversation]);

  useEffect(() => {
    if (conversationDetail?.messages) {
      hydrateMessages(conversationDetail.messages);
    }
  }, [conversationDetail, hydrateMessages]);

  const ensureConversation = useCallback(async (): Promise<string> => {
    if (activeConversationId) return activeConversationId;
    const conv = await createMutation.mutateAsync();
    setActiveConversation(conv.id);
    navigate(`/app/advisor/${conv.id}`, { replace: true });
    return conv.id;
  }, [activeConversationId, createMutation, setActiveConversation, navigate]);

  const handleSend = useCallback(async () => {
    const text = draft.trim();
    if (!text || isStreaming) return;
    setDraft('');
    const convId = await ensureConversation();
    sendMessage({ query: text, conversationId: convId });
  }, [draft, isStreaming, setDraft, ensureConversation, sendMessage]);

  const handleFollowUp = useCallback(
    async (prompt: string) => {
      if (isStreaming) return;
      setDraft('');
      const convId = await ensureConversation();
      sendMessage({ query: prompt, conversationId: convId });
    },
    [isStreaming, setDraft, ensureConversation, sendMessage]
  );

  const handleFeedback = useCallback(
    async (messageId: string, type: 'up' | 'down') => {
      if (!activeConversationId) return;
      try {
        await setMessageFeedback(activeConversationId, messageId, type);
      } catch {
        // Non-critical — don't disrupt the user
      }
    },
    [activeConversationId]
  );

  const handleRegenerate = useCallback(() => {
    const lastUserMsg = [...messages].reverse().find((m) => m.role === 'user');
    if (lastUserMsg) {
      sendMessage({ query: lastUserMsg.content });
    }
  }, [messages, sendMessage]);

  const handleAbort = useCallback(() => {
    abortStream();
  }, [abortStream]);

  return (
    <div className="flex h-full">
      <ConversationSidebar />

      <div className="flex flex-1 flex-col">
        <ThreadView
          messages={messages}
          isStreaming={isStreaming}
          streamingContent={streamingContent}
          streamingSources={streamingSources}
          streamingFollowUps={streamingFollowUps}
          onFeedback={handleFeedback}
          onRegenerate={handleRegenerate}
          onFollowUp={handleFollowUp}
        />

        <Composer
          value={draft}
          onChange={setDraft}
          onSubmit={handleSend}
          onAbort={handleAbort}
          isStreaming={isStreaming}
        />
      </div>
    </div>
  );
}
