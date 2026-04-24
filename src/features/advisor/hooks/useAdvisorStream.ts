/**
 * Advisor request hook for /generate-advice.
 *
 * Sends a single axios POST and progressively reveals the response
 * word-by-word for a streaming feel. When the backend ships real SSE,
 * this hook can be extended with fetchEventSource against the actual
 * event contract.
 *
 * Messages are committed to the Zustand conversationStore (session-only).
 *
 * Note: the backend LoanQuery model accepts only `query: str` — no
 * conversation_id or message history. Each request is stateless.
 * TODO: Add conversation_id threading when backend supports it.
 */
import { useCallback } from 'react';
import axios from 'axios';
import { useConversationStore } from '@/store/conversationStore';
import { getAccessToken } from '@/config/auth';
import type { Source } from '@/types/conversation';
import apiClient from '@/api/apiClient';

interface SendMessageOptions {
  query: string;
}

/**
 * Parse the /generate-advice response body into text + sources.
 *
 * The backend OptimizedAdviceResponse has `advice: string`. Older or
 * alternative shapes nested it differently — keep all paths for safety.
 */
function parseAdviceResponse(data: Record<string, unknown>): {
  text: string;
  sources: Source[];
} {
  const adviceObj = data.advice as Record<string, unknown> | string | undefined;
  const nested = typeof adviceObj === 'object' && adviceObj !== null ? adviceObj : undefined;
  const text =
    (typeof adviceObj === 'string' ? adviceObj : undefined) ||
    (typeof nested?.response === 'string' ? nested.response : undefined) ||
    (typeof data.response === 'string' ? String(data.response) : undefined) ||
    (typeof data.content === 'string' ? String(data.content) : undefined) ||
    'I received your question but couldn\'t generate a complete response. Please try again.';

  const rawSources =
    (data.advice as Record<string, unknown>)?.sources ||
    data.sources ||
    [];

  const sources = Array.isArray(rawSources)
    ? rawSources.map((s: Record<string, unknown>) => ({
        document_id: (s.document_id || s.id || '') as string,
        title: (s.title || s.source || 'Unknown') as string,
        section: (s.section || '') as string,
        excerpt: (s.excerpt || s.content || '') as string,
        relevance_score: Math.round(
          ((s.relevance_score as number) || (s.score as number) || 0) * 100
        ),
      }))
    : [];

  return { text, sources };
}

/**
 * Convert an axios error into a human-readable message for the chat bubble.
 * Never renders raw axios internals or backend detail strings for 5xx.
 */
function buildFriendlyErrorMessage(err: unknown): string {
  const generic =
    'Sorry, I had trouble generating a response. Please try again in a moment.';

  if (axios.isCancel(err)) {
    return ''; // silent cancel — no message needed
  }

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

  // For 4xx not in the map, try to extract a safe detail.
  const detail = e?.response?.data?.detail;
  if (typeof detail === 'string' && detail.length > 0 && detail.length < 240) {
    return `Sorry, something went wrong: ${detail}`;
  }

  return generic;
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
        const response = await apiClient.post(
          '/generate-advice',
          { query },
          { signal: controller.signal }
        );

        const { text, sources } = parseAdviceResponse(response.data);

        // Progressive word-by-word reveal for a streaming feel.
        // ~20ms per word, capped at 3s total so long answers don't drag.
        const words = text.split(' ');
        const interval = Math.min(20, 3000 / words.length);
        for (let i = 0; i < words.length; i++) {
          if (controller.signal.aborted) break;
          appendChunk((i > 0 ? ' ' : '') + words[i]);
          await new Promise((r) => setTimeout(r, interval));
        }

        if (sources.length > 0) {
          setSources(sources);
        }

        const result = endStream();
        if (result.content) {
          addMessage({
            id: `msg-${Date.now()}`,
            role: 'assistant',
            content: result.content,
            sources: result.sources,
            follow_ups: result.followUps,
            created_at: new Date().toISOString(),
          });
        }
      } catch (err) {
        // Silent cancel — user aborted or navigated away.
        // abortStream already committed partial content if any was revealed.
        if (axios.isCancel(err) || (err as Error).name === 'AbortError') {
          return;
        }

        // Show friendly error as an assistant message
        const friendly = buildFriendlyErrorMessage(err);
        if (friendly) {
          appendChunk(friendly);
          const result = endStream();
          addMessage({
            id: `msg-err-${Date.now()}`,
            role: 'assistant',
            content: result.content,
            created_at: new Date().toISOString(),
          });
        } else {
          endStream();
        }
      }
    },
    [startStream, appendChunk, setSources, endStream, addMessage]
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
