import { create } from 'zustand';
import type { Message, Source } from '@/types/conversation';

interface ConversationStoreState {
  activeConversationId: string | null;
  messages: Message[];

  isStreaming: boolean;
  streamingContent: string;
  streamingSources: Source[];
  streamingFollowUps: string[];
  abortController: AbortController | null;

  draft: string;

  setActiveConversation: (id: string | null) => void;
  hydrateMessages: (messages: Message[]) => void;
  addMessage: (msg: Message) => void;
  clearMessages: () => void;

  startStream: () => AbortController;
  appendChunk: (chunk: string) => void;
  setSources: (sources: Source[]) => void;
  setFollowUps: (followUps: string[]) => void;
  endStream: () => { content: string; sources: Source[]; followUps: string[] };
  abortStream: () => string;
  setDraft: (draft: string) => void;
}

export const useConversationStore = create<ConversationStoreState>()((set, get) => ({
  activeConversationId: null,
  messages: [],
  isStreaming: false,
  streamingContent: '',
  streamingSources: [],
  streamingFollowUps: [],
  abortController: null,
  draft: '',

  setActiveConversation: (id) => {
    set({ activeConversationId: id, messages: [], draft: '' });
  },

  hydrateMessages: (messages) => {
    set({ messages });
  },

  addMessage: (msg) => {
    set((s) => ({ messages: [...s.messages, msg] }));
  },

  clearMessages: () => {
    set({ messages: [], activeConversationId: null });
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
