/**
 * Conversation Store — transient streaming state.
 *
 * This store handles the real-time streaming state that breaks
 * the React Query pattern. Completed messages get committed to
 * the React Query cache; this store only holds in-flight data.
 */
import { create } from 'zustand';
import type { Source } from '@/types/conversation';

interface ConversationStoreState {
  // Current streaming state
  isStreaming: boolean;
  streamingContent: string;
  streamingSources: Source[];
  streamingFollowUps: string[];
  abortController: AbortController | null;

  // Draft (what the user is typing)
  draft: string;

  // Actions
  startStream: () => AbortController;
  appendChunk: (chunk: string) => void;
  setSources: (sources: Source[]) => void;
  setFollowUps: (followUps: string[]) => void;
  endStream: () => { content: string; sources: Source[]; followUps: string[] };
  abortStream: () => string;
  setDraft: (draft: string) => void;
}

export const useConversationStore = create<ConversationStoreState>()((set, get) => ({
  isStreaming: false,
  streamingContent: '',
  streamingSources: [],
  streamingFollowUps: [],
  abortController: null,
  draft: '',

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
    set({
      isStreaming: false,
      abortController: null,
    });
    return streamingContent;
  },

  setDraft: (draft) => {
    set({ draft });
  },
}));
