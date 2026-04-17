interface SuggestedFollowUpsProps {
  prompts: string[];
  onSelect: (prompt: string) => void;
  disabled?: boolean;
}

export default function SuggestedFollowUps({
  prompts,
  onSelect,
  disabled,
}: SuggestedFollowUpsProps) {
  if (!prompts.length) return null;

  return (
    <div className="flex flex-wrap gap-2 py-2">
      {prompts.map((prompt) => (
        <button
          key={prompt}
          onClick={() => onSelect(prompt)}
          disabled={disabled}
          className="rounded-lg border border-dashed border-border px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-teal-500 hover:text-foreground disabled:cursor-not-allowed disabled:opacity-50"
        >
          {prompt}
        </button>
      ))}
    </div>
  );
}
