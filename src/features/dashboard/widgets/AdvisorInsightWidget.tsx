import { useNavigate } from 'react-router-dom';
import { Lightbulb, ArrowRight, MessageSquare } from 'lucide-react';
import { Button } from '@/components/ui/button';
import WidgetCard from '../components/WidgetCard';
import type { WidgetId } from '@/store/preferencesStore';
import { useLatestInsight } from '@/hooks/useMarket';

interface AdvisorInsightWidgetProps {
  onHide: (id: WidgetId) => void;
}

export default function AdvisorInsightWidget({ onHide }: AdvisorInsightWidgetProps) {
  const navigate = useNavigate();
  const { data: insight, isLoading } = useLatestInsight();

  return (
    <WidgetCard id="advisor-insight" title="Advisor Insight" onHide={onHide} isLoading={isLoading}>
      {insight ? (
        <div className="flex gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gold-100 dark:bg-gold-700/20">
            <Lightbulb className="h-4 w-4 text-gold-700 dark:text-gold-300" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm leading-relaxed text-foreground">
              {insight.preview}
            </p>
            <Button
              variant="link"
              size="sm"
              className="mt-2 h-auto p-0 text-xs text-teal-700 dark:text-teal-300"
              onClick={() =>
                navigate(`/app/advisor/${insight.conversation_id}`)
              }
            >
              {insight.has_more ? 'Continue conversation' : 'View conversation'}
              <ArrowRight className="ml-1 h-3 w-3" />
            </Button>
          </div>
        </div>
      ) : (
        <div className="flex gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-muted">
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm text-muted-foreground">
              No advisor insights yet. Start a conversation to get personalized
              financial guidance.
            </p>
            <Button
              variant="link"
              size="sm"
              className="mt-2 h-auto p-0 text-xs text-teal-700 dark:text-teal-300"
              onClick={() => navigate('/app/advisor')}
            >
              Ask advisor
              <ArrowRight className="ml-1 h-3 w-3" />
            </Button>
          </div>
        </div>
      )}
    </WidgetCard>
  );
}
