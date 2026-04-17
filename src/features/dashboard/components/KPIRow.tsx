import KPICard from './KPICard';

// Placeholder data — will be replaced with real API data
const DEMO_KPIs = [
  {
    label: 'Net Worth',
    value: '$124,850',
    delta: { value: '+$2,400', direction: 'up' as const },
    sparkline: [10, 12, 11, 14, 13, 15, 16, 15, 17, 18].map((v) => ({ value: v })),
    color: '#1D8A84',
  },
  {
    label: 'DTI Ratio',
    value: '34.2%',
    delta: { value: '-1.8%', direction: 'up' as const },
    sparkline: [42, 40, 39, 38, 37, 36, 35, 35, 34, 34].map((v) => ({ value: v })),
    color: '#18A06B',
  },
  {
    label: 'FICO Estimate',
    value: '742',
    delta: { value: '+8 pts', direction: 'up' as const },
    sparkline: [720, 725, 722, 728, 730, 735, 732, 738, 740, 742].map((v) => ({ value: v })),
    color: '#C79A2B',
  },
  {
    label: 'Cash Reserve',
    value: '$18,420',
    delta: { value: '-$320', direction: 'down' as const },
    sparkline: [20, 19.5, 19.8, 19.2, 18.8, 18.5, 18.6, 18.4, 18.5, 18.4].map((v) => ({ value: v })),
    color: '#7E8989',
  },
];

export default function KPIRow() {
  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {DEMO_KPIs.map((kpi) => (
        <KPICard key={kpi.label} {...kpi} />
      ))}
    </div>
  );
}
