/**
 * SSE streaming hook for /generate-advice.
 *
 * Supports two modes:
 * 1. SSE streaming (text/event-stream) — real-time chunks
 * 2. JSON fallback — if backend returns application/json, we animate the text
 *
 * Messages are committed to the Zustand conversationStore, which persists
 * across navigation (Dashboard→Advisor) but not across page refreshes.
 * When /conversations persistence ships, React Query can layer on top.
 *
 * Note: the backend LoanQuery model accepts only `query: str` — no
 * conversation_id or message history. Each request is stateless.
 * TODO: Add conversation_id threading when backend supports it.
 */
import { useCallback } from 'react';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { useConversationStore } from '@/store/conversationStore';
import { getAccessToken } from '@/config/auth';
import { authConfig } from '@/config/auth';
import type { Message, Source } from '@/types/conversation';
import apiClient from '@/api/apiClient';

interface SendMessageOptions {
  query: string;
}

/**
 * Convert a non-OK `fetch` Response into a human-readable message.
 *
 * The backend returns `{ detail: "..." }` on error. We surface that detail
 * only when it's a short string — never raw JSON or a nested object — so the
 * assistant bubble never leaks internals or renders `{"detail":"..."}` verbatim.
 */
async function buildFriendlyErrorMessage(response: Response): Promise<string> {
  const generic =
    'Sorry, I had trouble generating a response. Please try again in a moment.';

  // 402 = query-limit exceeded, 503 = service warming up, 504 = LLM timeout.
  const byStatus: Record<number, string> = {
    401: 'Your session expired. Please sign in again to continue.',
    402: 'You have reached your query limit for this period. Upgrade your plan to continue.',
    429: 'You are sending questions a little too quickly. Please wait a moment and try again.',
    502: 'An upstream service is unavailable. Please try again shortly.',
    503: 'The advisor is warming up. Please try again in a moment.',
    504: 'The advisor took too long to respond. Please try again.',
  };
  if (byStatus[response.status]) {
    return byStatus[response.status];
  }

  // For 5xx errors, always use the generic message — never surface backend
  // detail strings in the UI. Backend verbosity can change at any time and
  // should not be the only defense against information disclosure.
  if (response.status >= 500) {
    return generic;
  }

  // For 4xx errors not in the status map, try to extract a safe detail.
  try {
    const errData = await response.json();
    const detail = errData?.detail;
    if (typeof detail === 'string' && detail.length > 0 && detail.length < 240) {
      return `Sorry, something went wrong: ${detail}`;
    }
  } catch {
    /* body wasn't JSON — fall through */
  }
  return generic;
}

/**
 * Convert an Axios error into a human-readable message for the chat bubble.
 * Never renders the raw Axios object, which stringifies as an unfriendly blob.
 */
function buildFriendlyAxiosErrorMessage(err: unknown): string {
  const generic =
    'Sorry, I had trouble generating a response. Please try again in a moment.';
  const e = err as {
    response?: { status?: number; data?: { detail?: unknown } };
    code?: string;
  };
  if (e?.code === 'ERR_NETWORK' || e?.code === 'ECONNABORTED') {
    return 'I could not reach the advisor service. Please check your connection and try again.';
  }
  const status = e?.response?.status;
  if (status) {
    const byStatus: Record<number, string> = {
      401: 'Your session expired. Please sign in again to continue.',
      402: 'You have reached your query limit for this period. Upgrade your plan to continue.',
      429: 'You are sending questions a little too quickly. Please wait a moment and try again.',
      502: 'An upstream service is unavailable. Please try again shortly.',
      503: 'The advisor is warming up. Please try again in a moment.',
      504: 'The advisor took too long to respond. Please try again.',
    };
    if (byStatus[status]) return byStatus[status];
    // For 5xx, always use generic — never surface backend detail strings.
    if (status >= 500) return generic;
  }
  const detail = e?.response?.data?.detail;
  if (typeof detail === 'string' && detail.length > 0 && detail.length < 240) {
    return `Sorry, something went wrong: ${detail}`;
  }
  return generic;
}

/**
 * Commit a completed assistant message to the Zustand store.
 */
function commitToStore(
  result: { content: string; sources: Source[]; followUps: string[] },
  addMessage: (msg: Message) => void
) {
  if (!result.content) return;
  addMessage({
    id: `msg-${Date.now()}`,
    role: 'assistant',
    content: result.content,
    sources: result.sources,
    follow_ups: result.followUps,
    created_at: new Date().toISOString(),
  });
}

/**
 * Commit a partial (aborted/errored) assistant message to the Zustand store.
 */
function commitPartialToStore(
  content: string,
  addMessage: (msg: Message) => void
) {
  if (!content) return;
  addMessage({
    id: `msg-partial-${Date.now()}`,
    role: 'assistant',
    content,
    is_partial: true,
    created_at: new Date().toISOString(),
  });
}

export function useAdvisorStream() {
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
    addMessage,
  } = useConversationStore();

  const sendMessage = useCallback(
    async ({ query }: SendMessageOptions) => {
      const token = getAccessToken();
      if (!token) return;

      const controller = startStream();

      // Add user message to store immediately (optimistic)
      addMessage({
        id: `user-${Date.now()}`,
        role: 'user',
        content: query,
        created_at: new Date().toISOString(),
      });

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
            body: JSON.stringify({ query }),
            signal: controller.signal,

            onopen: async (response) => {
              const contentType = response.headers.get('content-type') || '';

              // Error responses — show friendly message instead of raw JSON
              if (!response.ok) {
                const errorMsg = await buildFriendlyErrorMessage(response);
                appendChunk(errorMsg);
                const result = endStream();
                commitToStore(result, addMessage);
                return;
              }

              if (contentType.includes('text/event-stream')) {
                usedSSE = true;
                return;
              }

              // JSON fallback — read the full response and animate
              if (contentType.includes('application/json')) {
                const data = await response.json();
                // Backend OptimizedAdviceResponse has `advice: string`. Older
                // shapes nested it under `.advice.response` — keep both paths.
                const text =
                  (typeof data.advice === 'string' ? data.advice : undefined) ||
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
                commitToStore(result, addMessage);
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
                case 'done': {
                  // Stream complete — commit to store
                  const result = endStream();
                  commitToStore(result, addMessage);
                  break;
                }
              }
            },

            onerror: (err) => {
              // On error, commit whatever we have as partial
              const partial = abortStream();
              if (partial) {
                commitPartialToStore(partial, addMessage);
              }
              throw err; // stop retrying
            },

            onclose: () => {
              // If we didn't get a "done" event, commit what we have
              if (useConversationStore.getState().isStreaming) {
                const result = endStream();
                commitToStore(result, addMessage);
              }
            },
          }
        );
      } catch (err) {
        if ((err as Error).name === 'AbortError') {
          // User aborted — partial already committed by abortStream
          return;
        }

        // Fallback: try regular POST if SSE fails entirely
        try {
          const response = await apiClient.post('/generate-advice', { query });
          const data = response.data;
          const text =
            (typeof data.advice === 'string' ? data.advice : undefined) ||
            data.advice?.response ||
            data.response ||
            data.content ||
            'I received your question but couldn\'t generate a complete response. Please try again.';

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
          commitToStore(result, addMessage);
        } catch (fallbackErr) {
          // Commit any partial we already have, then render a friendly
          // error so the user isn't staring at a blank bubble (or worse,
          // raw JSON from a stringified Axios error).
          const partial = abortStream();
          if (partial) {
            commitPartialToStore(partial, addMessage);
            return;
          }
          const friendly = buildFriendlyAxiosErrorMessage(fallbackErr);
          appendChunk(friendly);
          const result = endStream();
          commitToStore(result, addMessage);
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
      addMessage,
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
