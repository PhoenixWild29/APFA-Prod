import { useCallback } from 'react';
import apiClient from '@/api/apiClient';
import { useConversationStore } from '@/store/conversationStore';
import { useAdvisorStream } from './hooks/useAdvisorStream';
import ThreadView from './components/ThreadView';
import Composer from './components/Composer';

// Conversation sidebar + URL-based routing are intentionally disabled until
// the backend ships GET/POST/DELETE /conversations. Messages live in Zustand
// (session-only, lost on page refresh). When persistence ships, restore the
// conversation query, URL params, and sidebar together.

export default function AdvisorPage() {
  const { draft, setDraft, messages } = useConversationStore();
  const {
    sendMessage,
    isStreaming,
    streamingContent,
    streamingSources,
    streamingFollowUps,
    abortStream,
  } = useAdvisorStream();

  const handleSend = useCallback(() => {
    const text = draft.trim();
    if (!text || isStreaming) return;
    setDraft('');
    sendMessage({ query: text });
  }, [draft, isStreaming, setDraft, sendMessage]);

  const handleFollowUp = useCallback(
    (prompt: string) => {
      if (isStreaming) return;
      setDraft('');
      sendMessage({ query: prompt });
    },
    [isStreaming, setDraft, sendMessage]
  );

  const handleFeedback = useCallback(
    async (messageId: string, type: 'up' | 'down') => {
      try {
        await apiClient.post(`/messages/${messageId}/feedback`, { type });
      } catch {
        // Feedback endpoint may not exist yet — silently skip
      }
    },
    []
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
