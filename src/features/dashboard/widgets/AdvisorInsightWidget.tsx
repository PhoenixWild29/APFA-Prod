import { useNavigate } from 'react-router-dom';
import { Lightbulb, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import WidgetCard from '../components/WidgetCard';
import type { WidgetId } from '@/store/preferencesStore';

interface AdvisorInsightWidgetProps {
  onHide: (id: WidgetId) => void;
}

export default function AdvisorInsightWidget({ onHide }: AdvisorInsightWidgetProps) {
  const navigate = useNavigate();

  // Placeholder — will be GET /users/me/insights/latest
  const insight = {
    text: 'Rebalancing your equity/fixed-income split from 55/45 back to your target 50/50 would realize $1,900 of Q1 gains and reduce sector concentration risk. Consider reviewing in advisor.',
    conversationId: null as string | null,
  };

  return (
    <WidgetCard id="advisor-insight" title="Advisor Insight" onHide={onHide}>
      <div className="flex gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gold-100 dark:bg-gold-700/20">
          <Lightbulb className="h-4 w-4 text-gold-700 dark:text-gold-300" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm leading-relaxed text-foreground">
            {insight.text}
          </p>
          <Button
            variant="link"
            size="sm"
            className="mt-2 h-auto p-0 text-xs text-teal-700 dark:text-teal-300"
            onClick={() => navigate('/app/advisor')}
          >
            Explore in advisor
            <ArrowRight className="ml-1 h-3 w-3" />
          </Button>
        </div>
      </div>
    </WidgetCard>
  );
}
