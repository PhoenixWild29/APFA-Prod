import { memo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Message } from '@/types/conversation';
import SourceCards from './SourceCards';
import MessageActions from './MessageActions';

interface AssistantMessageProps {
  message: Message;
  isStreaming?: boolean;
  onFeedback: (messageId: string, type: 'up' | 'down') => void;
  onRegenerate?: () => void;
}

function AssistantMessageInner({
  message,
  isStreaming,
  onFeedback,
  onRegenerate,
}: AssistantMessageProps) {
  return (
    <div className="group/msg flex gap-3">
      {/* Avatar */}
      <div className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-teal-700/10 text-xs font-semibold text-teal-700 dark:bg-teal-300/10 dark:text-teal-300">
        A
      </div>

      <div className="min-w-0 flex-1">
        {/* Prose body */}
        <div className="prose prose-sm max-w-[760px] dark:prose-invert prose-p:leading-relaxed prose-pre:bg-ink-800 prose-pre:text-ink-100">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {isStreaming ? message.content + ' ▍' : message.content}
          </ReactMarkdown>
        </div>

        {/* Partial indicator */}
        {message.is_partial && !isStreaming && (
          <p className="mt-1 text-xs italic text-warn">
            Response was interrupted — you can regenerate.
          </p>
        )}

        {/* Sources */}
        {message.sources && message.sources.length > 0 && !isStreaming && (
          <SourceCards sources={message.sources} />
        )}

        {/* Actions */}
        {!isStreaming && (
          <div className="mt-2">
            <MessageActions
              messageId={message.id}
              content={message.content}
              feedback={message.feedback}
              onFeedback={onFeedback}
              onRegenerate={onRegenerate}
            />
          </div>
        )}
      </div>
    </div>
  );
}

const AssistantMessage = memo(AssistantMessageInner);
export default AssistantMessage;
