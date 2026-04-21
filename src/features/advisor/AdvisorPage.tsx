import { useState, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import apiClient from '@/api/apiClient';
import { useConversationStore } from '@/store/conversationStore';
import { useAdvisorStream } from './hooks/useAdvisorStream';
import ConversationListPanel from './components/ConversationListPanel';
import ThreadView from './components/ThreadView';
import Composer from './components/Composer';
import type { Conversation, ConversationDetail } from '@/types/conversation';

export default function AdvisorPage() {
  const navigate = useNavigate();
  const { conversationId } = useParams();
  const [searchQuery, setSearchQuery] = useState('');

  const { draft, setDraft } = useConversationStore();
  const {
    sendMessage,
    isStreaming,
    streamingContent,
    streamingSources,
    streamingFollowUps,
    abortStream,
  } = useAdvisorStream();

  // Fetch conversation list
  const { data: conversations = [], isLoading: listLoading } = useQuery({
    queryKey: ['conversations'],
    queryFn: async () => {
      try {
        const res = await apiClient.get<Conversation[]>('/conversations');
        return res.data;
      } catch {
        // Backend doesn't have /conversations yet — return empty
        return [];
      }
    },
    staleTime: 60_000,
  });

  // Fetch current conversation detail
  const { data: conversation } = useQuery({
    queryKey: ['conversation', conversationId],
    queryFn: async () => {
      try {
        const res = await apiClient.get<ConversationDetail>(
          `/conversations/${conversationId}`
        );
        return res.data;
      } catch {
        return null;
      }
    },
    enabled: !!conversationId,
    staleTime: 30_000,
  });

  const messages = conversation?.messages ?? [];

  const handleNewConversation = useCallback(() => {
    navigate('/app/advisor');
  }, [navigate]);

  const handleSend = useCallback(() => {
    const text = draft.trim();
    if (!text || isStreaming) return;

    setDraft('');
    sendMessage({
      conversationId: conversationId ?? null,
      query: text,
      onNewConversation: (id) => {
        navigate(`/app/advisor/c/${id}`, { replace: true });
      },
    });
  }, [draft, isStreaming, conversationId, setDraft, sendMessage, navigate]);

  const handleFollowUp = useCallback(
    (prompt: string) => {
      setDraft('');
      sendMessage({
        conversationId: conversationId ?? null,
        query: prompt,
        onNewConversation: (id) => {
          navigate(`/app/advisor/c/${id}`, { replace: true });
        },
      });
    },
    [conversationId, setDraft, sendMessage, navigate]
  );

  const handleFeedback = useCallback(
    async (messageId: string, type: 'up' | 'down') => {
      try {
        await apiClient.post(`/messages/${messageId}/feedback`, {
          type,
        });
      } catch {
        // Feedback endpoint may not exist yet — silently skip
      }
    },
    []
  );

  const handleRegenerate = useCallback(() => {
    // Find the last user message and re-send it
    const lastUserMsg = [...messages].reverse().find((m) => m.role === 'user');
    if (lastUserMsg) {
      sendMessage({
        conversationId: conversationId ?? null,
        query: lastUserMsg.content,
      });
    }
  }, [messages, conversationId, sendMessage]);

  const handleAbort = useCallback(() => {
    abortStream();
  }, [abortStream]);

  return (
    <div className="flex h-full">
      {/* Left rail — hidden until /conversations endpoint is built */}
      {/* TODO: Uncomment when GET/POST/DELETE /conversations ships
      <div className="hidden lg:block">
        <ConversationListPanel
          conversations={conversations}
          isLoading={listLoading}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          onNewConversation={handleNewConversation}
        />
      </div>
      */}

      {/* Center: thread + composer */}
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
