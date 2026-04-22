import { useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import apiClient from '@/api/apiClient';
import { useConversationStore } from '@/store/conversationStore';
import { useAdvisorStream } from './hooks/useAdvisorStream';
import ThreadView from './components/ThreadView';
import Composer from './components/Composer';
import type { ConversationDetail } from '@/types/conversation';

// The conversation list sidebar is intentionally hidden until the backend
// ships GET/POST/DELETE /conversations. Once those endpoints exist, restore
// the ConversationListPanel import + query below and re-render the aside.
// See QA report: "Hide conversation sidebar until /conversations endpoint exists".

export default function AdvisorPage() {
  const navigate = useNavigate();
  const { conversationId } = useParams();

  const { draft, setDraft } = useConversationStore();
  const {
    sendMessage,
    isStreaming,
    streamingContent,
    streamingSources,
    streamingFollowUps,
    abortStream,
  } = useAdvisorStream();

  // Fetch current conversation detail — only runs when a conversationId is
  // in the URL. Kept because the detail endpoint is planned for the same
  // ship window as the list endpoint and the URL-driven load path works
  // independently of the sidebar.
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
      {/*
        Left rail / conversation list is intentionally NOT rendered until the
        backend ships the /conversations endpoints (GET list, GET detail,
        POST create, DELETE). Showing an empty sidebar wired to a 404 route
        created a broken-feeling UI and a noisy Network panel. Once the
        endpoints exist, restore this block:

          <div className="hidden lg:block">
            <ConversationListPanel ... />
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
