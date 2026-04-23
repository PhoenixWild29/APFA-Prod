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
  | 'market-index'
  | 'investment-growth'
  | 'asset-allocation'
  | 'documents';

interface GrowthCalcInputs {
  initial?: number;
  monthly?: number;
  years?: number;
  rate?: number;
}

interface PreferencesState {
  widgetOrder: WidgetId[];
  hiddenWidgets: Set<WidgetId>;

  // Investment Growth calculator saved values
  growthInitial: number;
  growthMonthly: number;
  growthYears: number;
  growthRate: number;

  // Actions
  hideWidget: (id: WidgetId) => void;
  showWidget: (id: WidgetId) => void;
  moveWidget: (id: WidgetId, direction: 'up' | 'down') => void;
  setGrowthValues: (inputs: GrowthCalcInputs) => void;
}

const DEFAULT_ORDER: WidgetId[] = [
  'advisor-insight',
  'market-index',
  'investment-growth',
  'asset-allocation',
  'documents',
];

// Widget ID aliases for backwards compatibility with older persisted state
// (the dashboard previously used loan-flavored IDs). These get migrated
// transparently on read.
const LEGACY_WIDGET_ALIASES: Record<string, WidgetId> = {
  'rate-trend': 'market-index',
  'dti-calculator': 'investment-growth',
  'loan-comparison': 'asset-allocation',
};

function migrateWidgetIds<T extends string>(ids: T[] | undefined): WidgetId[] {
  if (!ids || !Array.isArray(ids)) return DEFAULT_ORDER;
  const mapped = ids
    .map((id) => (LEGACY_WIDGET_ALIASES[id] as WidgetId) || (id as WidgetId))
    .filter((id): id is WidgetId => DEFAULT_ORDER.includes(id));
  // Ensure every default widget is still represented (add any missing at the
  // end) so migrations don't strip the newly-introduced widgets.
  const present = new Set(mapped);
  for (const def of DEFAULT_ORDER) {
    if (!present.has(def)) mapped.push(def);
  }
  return mapped;
}

export const usePreferencesStore = create<PreferencesState>()(
  persist(
    (set) => ({
      widgetOrder: DEFAULT_ORDER,
      hiddenWidgets: new Set<WidgetId>(),
      growthInitial: 10000,
      growthMonthly: 500,
      growthYears: 20,
      growthRate: 7,

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

      setGrowthValues: (inputs) => {
        set((s) => ({
          growthInitial:
            inputs.initial !== undefined ? inputs.initial : s.growthInitial,
          growthMonthly:
            inputs.monthly !== undefined ? inputs.monthly : s.growthMonthly,
          growthYears:
            inputs.years !== undefined ? inputs.years : s.growthYears,
          growthRate: inputs.rate !== undefined ? inputs.rate : s.growthRate,
        }));
      },
    }),
    {
      name: 'apfa-preferences',
      partialize: (state) => ({
        widgetOrder: state.widgetOrder,
        hiddenWidgets: Array.from(state.hiddenWidgets),
        growthInitial: state.growthInitial,
        growthMonthly: state.growthMonthly,
        growthYears: state.growthYears,
        growthRate: state.growthRate,
      }),
      merge: (persisted: unknown, current) => {
        const p = persisted as Record<string, unknown> | undefined;
        const persistedOrder = p?.widgetOrder as string[] | undefined;
        const persistedHidden = p?.hiddenWidgets as string[] | undefined;
        return {
          ...current,
          ...(p || {}),
          widgetOrder: migrateWidgetIds(persistedOrder),
          hiddenWidgets: new Set(
            (persistedHidden || [])
              .map((id) => LEGACY_WIDGET_ALIASES[id] || id)
              .filter((id): id is WidgetId =>
                DEFAULT_ORDER.includes(id as WidgetId)
              )
          ),
        };
      },
    }
  )
);
