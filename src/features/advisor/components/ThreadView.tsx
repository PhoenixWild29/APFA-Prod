import { useEffect, useRef } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import UserMessage from './UserMessage';
import AssistantMessage from './AssistantMessage';
import SuggestedFollowUps from './SuggestedFollowUps';
import type { Message, Source } from '@/types/conversation';

interface ThreadViewProps {
  messages: Message[];
  isStreaming: boolean;
  streamingContent: string;
  streamingSources: Source[];
  streamingFollowUps: string[];
  onFeedback: (messageId: string, type: 'up' | 'down') => void;
  onRegenerate: () => void;
  onFollowUp: (prompt: string) => void;
}

export default function ThreadView({
  messages,
  isStreaming,
  streamingContent,
  streamingSources,
  streamingFollowUps,
  onFeedback,
  onRegenerate,
  onFollowUp,
}: ThreadViewProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll on new content
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length, streamingContent]);

  // Get follow-ups from the last assistant message
  const lastAssistant = [...messages].reverse().find((m) => m.role === 'assistant');
  const followUps = lastAssistant?.follow_ups ?? [];

  return (
    <ScrollArea className="flex-1">
      <div className="mx-auto max-w-3xl space-y-6 px-4 py-6">
        {/* Empty state */}
        {messages.length === 0 && !isStreaming && (
          <div className="flex flex-col items-center gap-4 py-16 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-teal-700/10 dark:bg-teal-300/10">
              <span className="font-serif text-2xl font-semibold text-teal-700 dark:text-teal-300">
                A
              </span>
            </div>
            <div>
              <h2 className="font-serif text-xl font-semibold">
                How can I help you today?
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Ask about investments, markets, portfolio strategy, or any
                financial question. Every answer cites its sources.
              </p>
            </div>
            <div className="flex flex-wrap justify-center gap-2">
              {[
                'Explain the current rate environment',
                'What drives equity market valuations?',
                'Walk me through portfolio diversification',
                'Analyze my investment documents',
              ].map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => onFollowUp(prompt)}
                  className="rounded-lg border border-dashed px-3 py-2 text-sm text-muted-foreground transition-colors hover:border-teal-500 hover:text-foreground"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Messages */}
        {messages.map((msg, idx) =>
          msg.role === 'user' ? (
            <UserMessage key={msg.id} message={msg} />
          ) : (
            <AssistantMessage
              key={msg.id}
              message={msg}
              onFeedback={onFeedback}
              onRegenerate={idx === messages.length - 1 ? onRegenerate : undefined}
            />
          )
        )}

        {/* Streaming message */}
        {isStreaming && streamingContent && (
          <AssistantMessage
            message={{
              id: 'streaming',
              role: 'assistant',
              content: streamingContent,
              sources: streamingSources,
              created_at: new Date().toISOString(),
            }}
            isStreaming
            onFeedback={() => {}}
          />
        )}

        {/* Suggested follow-ups */}
        {!isStreaming && (followUps.length > 0 || streamingFollowUps.length > 0) && (
          <SuggestedFollowUps
            prompts={followUps.length > 0 ? followUps : streamingFollowUps}
            onSelect={onFollowUp}
            disabled={isStreaming}
          />
        )}

        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}
