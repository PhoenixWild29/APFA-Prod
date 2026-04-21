/**
 * SSE streaming hook for /generate-advice.
 *
 * Supports two modes:
 * 1. SSE streaming (text/event-stream) — real-time chunks
 * 2. JSON fallback — if backend returns application/json, we animate the text
 *
 * Per CoWork spec §6.4: chunks land in useConversationStore, committed to
 * React Query cache on completion.
 */
import { useCallback } from 'react';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { useQueryClient } from '@tanstack/react-query';
import { useConversationStore } from '@/store/conversationStore';
import { getAccessToken } from '@/config/auth';
import { authConfig } from '@/config/auth';
import type { Message, Source, ConversationDetail } from '@/types/conversation';
import apiClient from '@/api/apiClient';

interface SendMessageOptions {
  conversationId: string | null;
  query: string;
  onNewConversation?: (id: string) => void;
}

export function useAdvisorStream() {
  const queryClient = useQueryClient();
  const {
    isStreaming,
    streamingContent,
    streamingSources,
    streamingFollowUps,
    startStream,
    appendChunk,
    setSources,
    setFollowUps,
    endStream,
    abortStream,
  } = useConversationStore();

  const sendMessage = useCallback(
    async ({ conversationId, query, onNewConversation }: SendMessageOptions) => {
      const token = getAccessToken();
      if (!token) return;

      const controller = startStream();

      // Optimistically add user message to cache
      const userMsg: Message = {
        id: `temp-user-${Date.now()}`,
        role: 'user',
        content: query,
        created_at: new Date().toISOString(),
      };

      if (conversationId) {
        queryClient.setQueryData<ConversationDetail>(
          ['conversation', conversationId],
          (old) => {
            if (!old) return old;
            return { ...old, messages: [...old.messages, userMsg] };
          }
        );
      }

      try {
        // Try SSE first
        let usedSSE = false;

        await fetchEventSource(
          `${authConfig.apiEndpoint}/generate-advice`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${token}`,
              Accept: 'text/event-stream',
            },
            body: JSON.stringify({
              query,
              conversation_id: conversationId,
            }),
            signal: controller.signal,

            onopen: async (response) => {
              const contentType = response.headers.get('content-type') || '';

              // Error responses — show friendly message instead of raw JSON
              if (!response.ok) {
                let errorMsg = 'Sorry, I encountered an error processing your request. Please try again.';
                try {
                  const errData = await response.json();
                  if (errData.detail && typeof errData.detail === 'string') {
                    errorMsg = `Sorry, something went wrong: ${errData.detail}`;
                  }
                } catch {}
                appendChunk(errorMsg);
                const result = endStream();
                commitMessage(conversationId, result, queryClient, onNewConversation);
                return;
              }

              if (contentType.includes('text/event-stream')) {
                usedSSE = true;
                return;
              }

              // JSON fallback — read the full response and animate
              if (contentType.includes('application/json')) {
                const data = await response.json();
                const text =
                  data.advice?.response ||
                  data.response ||
                  data.content ||
                  'I received your question but couldn\'t generate a complete response. Please try again.';

                // Progressive render: reveal text over 600ms
                const words = text.split(' ');
                const interval = Math.max(10, 600 / words.length);
                for (let i = 0; i < words.length; i++) {
                  if (controller.signal.aborted) break;
                  appendChunk((i > 0 ? ' ' : '') + words[i]);
                  await new Promise((r) => setTimeout(r, interval));
                }

                // Extract sources from JSON response
                if (data.advice?.sources || data.sources) {
                  const rawSources = data.advice?.sources || data.sources || [];
                  setSources(
                    rawSources.map((s: Record<string, unknown>) => ({
                      document_id: s.document_id || s.id || '',
                      title: s.title || s.source || 'Unknown',
                      section: s.section || '',
                      excerpt: s.excerpt || s.content || '',
                      relevance_score: Math.round(
                        ((s.relevance_score as number) || (s.score as number) || 0) * 100
                      ),
                    }))
                  );
                }

                // Commit
                const result = endStream();
                commitMessage(conversationId, result, queryClient, onNewConversation);
                return;
              }

              throw new Error(`Unexpected content-type: ${contentType}`);
            },

            onmessage: (event) => {
              if (!usedSSE) return;

              switch (event.event) {
                case 'chunk':
                case '':
                  if (event.data) {
                    appendChunk(event.data);
                  }
                  break;
                case 'sources':
                  try {
                    const sources: Source[] = JSON.parse(event.data);
                    setSources(sources);
                  } catch {}
                  break;
                case 'follow_ups':
                  try {
                    const followUps: string[] = JSON.parse(event.data);
                    setFollowUps(followUps);
                  } catch {}
                  break;
                case 'done':
                  // Stream complete — commit to cache
                  const result = endStream();
                  commitMessage(conversationId, result, queryClient, onNewConversation);
                  break;
              }
            },

            onerror: (err) => {
              // On error, commit whatever we have as partial
              const partial = abortStream();
              if (partial) {
                commitPartialMessage(conversationId, partial, queryClient);
              }
              throw err; // stop retrying
            },

            onclose: () => {
              // If we didn't get a "done" event, commit what we have
              if (useConversationStore.getState().isStreaming) {
                const result = endStream();
                commitMessage(conversationId, result, queryClient, onNewConversation);
              }
            },
          }
        );
      } catch (err) {
        if ((err as Error).name === 'AbortError') {
          // User aborted — commit partial
          return;
        }

        // Fallback: try regular POST if SSE fails entirely
        try {
          const response = await apiClient.post('/generate-advice', {
            query,
            conversation_id: conversationId,
          });
          const data = response.data;
          const text =
            data.advice?.response || data.response || data.content || '';

          // Show text immediately
          appendChunk(text);

          if (data.advice?.sources || data.sources) {
            const rawSources = data.advice?.sources || data.sources || [];
            setSources(
              rawSources.map((s: Record<string, unknown>) => ({
                document_id: s.document_id || s.id || '',
                title: s.title || s.source || 'Unknown',
                section: s.section || '',
                excerpt: s.excerpt || s.content || '',
                relevance_score: Math.round(
                  ((s.relevance_score as number) || (s.score as number) || 0) * 100
                ),
              }))
            );
          }

          const result = endStream();
          commitMessage(conversationId, result, queryClient, onNewConversation);
        } catch {
          const partial = abortStream();
          if (partial) {
            commitPartialMessage(conversationId, partial, queryClient);
          }
        }
      }
    },
    [
      startStream,
      appendChunk,
      setSources,
      setFollowUps,
      endStream,
      abortStream,
      queryClient,
    ]
  );

  return {
    sendMessage,
    isStreaming,
    streamingContent,
    streamingSources,
    streamingFollowUps,
    abortStream,
  };
}

function commitMessage(
  conversationId: string | null,
  result: { content: string; sources: Source[]; followUps: string[] },
  queryClient: ReturnType<typeof useQueryClient>,
  onNewConversation?: (id: string) => void
) {
  const assistantMsg: Message = {
    id: `msg-${Date.now()}`,
    role: 'assistant',
    content: result.content,
    sources: result.sources,
    follow_ups: result.followUps,
    created_at: new Date().toISOString(),
  };

  if (conversationId) {
    queryClient.setQueryData<ConversationDetail>(
      ['conversation', conversationId],
      (old) => {
        if (!old) return old;
        return { ...old, messages: [...old.messages, assistantMsg] };
      }
    );
    // Refresh conversation list
    queryClient.invalidateQueries({ queryKey: ['conversations'] });
  } else {
    // New conversation — we'd normally get an ID from the backend
    // For now, generate a temporary one
    const newId = `conv-${Date.now()}`;
    queryClient.setQueryData<ConversationDetail>(['conversation', newId], {
      id: newId,
      title: result.content.slice(0, 50) + '...',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      message_count: 2,
      messages: [
        {
          id: `temp-user-${Date.now() - 1}`,
          role: 'user',
          content: '',
          created_at: new Date().toISOString(),
        },
        assistantMsg,
      ],
    });
    onNewConversation?.(newId);
  }
}

function commitPartialMessage(
  conversationId: string | null,
  content: string,
  queryClient: ReturnType<typeof useQueryClient>
) {
  if (!content || !conversationId) return;

  const partialMsg: Message = {
    id: `msg-partial-${Date.now()}`,
    role: 'assistant',
    content,
    is_partial: true,
    created_at: new Date().toISOString(),
  };

  queryClient.setQueryData<ConversationDetail>(
    ['conversation', conversationId],
    (old) => {
      if (!old) return old;
      return { ...old, messages: [...old.messages, partialMsg] };
    }
  );
}
