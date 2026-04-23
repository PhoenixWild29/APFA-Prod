/**
 * Conversation Store — session messages + transient streaming state.
 *
 * Messages persist in Zustand for the browser session (survives
 * Dashboard→Advisor navigation, lost on page refresh). When the
 * /conversations backend ships, this store becomes the in-memory
 * cache layer with React Query on top for persistence.
 *
 * Streaming state (content, sources, follow-ups) is transient:
 * populated while a response streams in, cleared on commit.
 */
import { create } from 'zustand';
import type { Message, Source } from '@/types/conversation';

interface ConversationStoreState {
  // Committed messages (session-only, survives navigation)
  messages: Message[];

  // Current streaming state
  isStreaming: boolean;
  streamingContent: string;
  streamingSources: Source[];
  streamingFollowUps: string[];
  abortController: AbortController | null;

  // Draft (what the user is typing)
  draft: string;

  // Message actions
  addMessage: (msg: Message) => void;
  clearMessages: () => void;

  // Streaming actions
  startStream: () => AbortController;
  appendChunk: (chunk: string) => void;
  setSources: (sources: Source[]) => void;
  setFollowUps: (followUps: string[]) => void;
  endStream: () => { content: string; sources: Source[]; followUps: string[] };
  abortStream: () => string;
  setDraft: (draft: string) => void;
}

export const useConversationStore = create<ConversationStoreState>()((set, get) => ({
  messages: [],
  isStreaming: false,
  streamingContent: '',
  streamingSources: [],
  streamingFollowUps: [],
  abortController: null,
  draft: '',

  addMessage: (msg) => {
    set((s) => ({ messages: [...s.messages, msg] }));
  },

  clearMessages: () => {
    set({ messages: [] });
  },

  startStream: () => {
    const controller = new AbortController();
    set({
      isStreaming: true,
      streamingContent: '',
      streamingSources: [],
      streamingFollowUps: [],
      abortController: controller,
    });
    return controller;
  },

  appendChunk: (chunk) => {
    set((s) => ({ streamingContent: s.streamingContent + chunk }));
  },

  setSources: (sources) => {
    set({ streamingSources: sources });
  },

  setFollowUps: (followUps) => {
    set({ streamingFollowUps: followUps });
  },

  endStream: () => {
    const { streamingContent, streamingSources, streamingFollowUps } = get();
    set({
      isStreaming: false,
      streamingContent: '',
      streamingSources: [],
      streamingFollowUps: [],
      abortController: null,
    });
    return {
      content: streamingContent,
      sources: streamingSources,
      followUps: streamingFollowUps,
    };
  },

  abortStream: () => {
    const { abortController, streamingContent } = get();
    abortController?.abort();
    // Commit partial content before clearing streaming state so the
    // user sees what was received before they aborted.
    if (streamingContent) {
      set((s) => ({
        messages: [
          ...s.messages,
          {
            id: `msg-partial-${Date.now()}`,
            role: 'assistant' as const,
            content: streamingContent,
            is_partial: true,
            created_at: new Date().toISOString(),
          },
        ],
        isStreaming: false,
        abortController: null,
      }));
    } else {
      set({
        isStreaming: false,
        abortController: null,
      });
    }
    return streamingContent;
  },

  setDraft: (draft) => {
    set({ draft });
  },
}));
