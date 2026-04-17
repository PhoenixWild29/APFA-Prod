import { useRef, useCallback } from 'react';
import { Send, Square, Paperclip } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface ComposerProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  onAbort: () => void;
  isStreaming: boolean;
  disabled?: boolean;
}

export default function Composer({
  value,
  onChange,
  onSubmit,
  onAbort,
  isStreaming,
  disabled,
}: ComposerProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (value.trim() && !isStreaming && !disabled) {
          onSubmit();
        }
      }
    },
    [value, isStreaming, disabled, onSubmit]
  );

  return (
    <div className="border-t bg-background px-4 pb-4 pt-3">
      <div className="mx-auto max-w-3xl">
        <div className="flex items-end gap-2 rounded-xl border bg-card p-2 shadow-sm focus-within:ring-2 focus-within:ring-ring">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 shrink-0 text-muted-foreground"
                disabled={isStreaming}
                aria-label="Attach document"
              >
                <Paperclip className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Attach document</TooltipContent>
          </Tooltip>

          <Textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask your financial advisor..."
            disabled={disabled}
            className="min-h-[40px] max-h-[200px] flex-1 resize-none border-0 bg-transparent p-1 text-sm shadow-none focus-visible:ring-0"
            rows={1}
          />

          {isStreaming ? (
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 shrink-0 text-neg"
                  onClick={onAbort}
                  aria-label="Stop generating"
                >
                  <Square className="h-4 w-4 fill-current" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Stop generating</TooltipContent>
            </Tooltip>
          ) : (
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 shrink-0 text-teal-700 dark:text-teal-300"
                  onClick={onSubmit}
                  disabled={!value.trim() || disabled}
                  aria-label="Send message"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Send (Enter)</TooltipContent>
            </Tooltip>
          )}
        </div>

        <p className="mt-2 text-center text-[10px] text-muted-foreground">
          APFA may produce inaccurate information. Always verify financial
          advice with a licensed professional before making decisions.
        </p>
      </div>
    </div>
  );
}
