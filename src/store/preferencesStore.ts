/**
 * User Preferences Store — widget visibility, order, saved scenarios.
 *
 * localStorage mirror for offline; syncs to backend /users/me/preferences
 * when that endpoint ships.
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type WidgetId =
  | 'advisor-insight'
  | 'rate-trend'
  | 'dti-calculator'
  | 'loan-comparison'
  | 'recent-conversations'
  | 'documents';

interface PreferencesState {
  widgetOrder: WidgetId[];
  hiddenWidgets: Set<WidgetId>;

  // DTI calculator saved values
  monthlyIncome: number;
  monthlyDebt: number;

  // Actions
  hideWidget: (id: WidgetId) => void;
  showWidget: (id: WidgetId) => void;
  moveWidget: (id: WidgetId, direction: 'up' | 'down') => void;
  setDTIValues: (income: number, debt: number) => void;
}

const DEFAULT_ORDER: WidgetId[] = [
  'advisor-insight',
  'rate-trend',
  'dti-calculator',
  'loan-comparison',
  'recent-conversations',
  'documents',
];

export const usePreferencesStore = create<PreferencesState>()(
  persist(
    (set, get) => ({
      widgetOrder: DEFAULT_ORDER,
      hiddenWidgets: new Set<WidgetId>(),
      monthlyIncome: 0,
      monthlyDebt: 0,

      hideWidget: (id) => {
        set((s) => {
          const next = new Set(s.hiddenWidgets);
          next.add(id);
          return { hiddenWidgets: next };
        });
      },

      showWidget: (id) => {
        set((s) => {
          const next = new Set(s.hiddenWidgets);
          next.delete(id);
          return { hiddenWidgets: next };
        });
      },

      moveWidget: (id, direction) => {
        set((s) => {
          const order = [...s.widgetOrder];
          const idx = order.indexOf(id);
          if (idx === -1) return s;
          const swapIdx = direction === 'up' ? idx - 1 : idx + 1;
          if (swapIdx < 0 || swapIdx >= order.length) return s;
          [order[idx], order[swapIdx]] = [order[swapIdx], order[idx]];
          return { widgetOrder: order };
        });
      },

      setDTIValues: (income, debt) => {
        set({ monthlyIncome: income, monthlyDebt: debt });
      },
    }),
    {
      name: 'apfa-preferences',
      partialize: (state) => ({
        widgetOrder: state.widgetOrder,
        hiddenWidgets: Array.from(state.hiddenWidgets),
        monthlyIncome: state.monthlyIncome,
        monthlyDebt: state.monthlyDebt,
      }),
      merge: (persisted: unknown, current) => {
        const p = persisted as Record<string, unknown> | undefined;
        return {
          ...current,
          ...(p || {}),
          hiddenWidgets: new Set((p?.hiddenWidgets as WidgetId[]) || []),
        };
      },
    }
  )
);
