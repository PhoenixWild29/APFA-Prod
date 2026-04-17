import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { MessageSquare } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuthStore } from '@/store/authStore';
import { usePreferencesStore, type WidgetId } from '@/store/preferencesStore';
import KPIRow from './components/KPIRow';
import AdvisorInsightWidget from './widgets/AdvisorInsightWidget';
import RateTrendWidget from './widgets/RateTrendWidget';
import DTICalculatorWidget from './widgets/DTICalculatorWidget';
import LoanComparisonWidget from './widgets/LoanComparisonWidget';
import RecentConversationsWidget from './widgets/RecentConversationsWidget';
import DocumentsWidget from './widgets/DocumentsWidget';

function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 17) return 'Good afternoon';
  return 'Good evening';
}

const WIDGET_MAP: Record<
  WidgetId,
  React.ComponentType<{ onHide: (id: WidgetId) => void }>
> = {
  'advisor-insight': AdvisorInsightWidget,
  'rate-trend': RateTrendWidget,
  'dti-calculator': DTICalculatorWidget,
  'loan-comparison': LoanComparisonWidget,
  'recent-conversations': RecentConversationsWidget,
  documents: DocumentsWidget,
};

// Widget sizing: 7-col / 5-col pairs on desktop (12-col grid)
const WIDGET_SIZES: Record<WidgetId, string> = {
  'advisor-insight': 'lg:col-span-7',
  'rate-trend': 'lg:col-span-5',
  'dti-calculator': 'lg:col-span-5',
  'loan-comparison': 'lg:col-span-7',
  'recent-conversations': 'lg:col-span-6',
  documents: 'lg:col-span-6',
};

export default function DashboardPage() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const { widgetOrder, hiddenWidgets, hideWidget } = usePreferencesStore();

  const visibleWidgets = useMemo(
    () => widgetOrder.filter((id) => !hiddenWidgets.has(id)),
    [widgetOrder, hiddenWidgets]
  );

  const today = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });

  return (
    <div className="space-y-6 p-6">
      {/* Greeting header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="font-serif text-2xl font-semibold">
            {getGreeting()}, {user?.username ?? 'there'}
          </h1>
          <p className="mt-0.5 text-sm text-muted-foreground">{today}</p>
        </div>
        <Button onClick={() => navigate('/app/advisor')}>
          <MessageSquare className="mr-2 h-4 w-4" />
          Ask advisor
        </Button>
      </div>

      {/* KPI row */}
      <KPIRow />

      {/* Widget grid — 12-col desktop, stacked mobile */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        {visibleWidgets.map((id) => {
          const Component = WIDGET_MAP[id];
          if (!Component) return null;
          return (
            <div key={id} className={WIDGET_SIZES[id]}>
              <Component onHide={hideWidget} />
            </div>
          );
        })}
      </div>

      {/* Show hidden widgets */}
      {hiddenWidgets.size > 0 && (
        <p className="text-center text-xs text-muted-foreground">
          {hiddenWidgets.size} widget{hiddenWidgets.size > 1 ? 's' : ''} hidden.{' '}
          <button
            className="text-teal-700 underline underline-offset-2 hover:text-teal-500 dark:text-teal-300"
            onClick={() => {
              hiddenWidgets.forEach((id) =>
                usePreferencesStore.getState().showWidget(id)
              );
            }}
          >
            Show all
          </button>
        </p>
      )}
    </div>
  );
}
