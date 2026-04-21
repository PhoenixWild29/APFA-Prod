import KPICard from './KPICard';

// Placeholder data — will be replaced with real portfolio API data
const DEMO_KPIs = [
  {
    label: 'Portfolio Value',
    value: '$124,850',
    delta: { value: '+$2,400', direction: 'up' as const },
    sparkline: [110, 112, 111, 114, 113, 115, 116, 118, 121, 124.8].map((v) => ({ value: v })),
    color: '#1D8A84',
  },
  {
    label: 'YTD Return',
    value: '+8.4%',
    delta: { value: '+1.2%', direction: 'up' as const },
    sparkline: [2, 3.1, 2.8, 4.2, 5.0, 5.8, 6.1, 7.0, 7.5, 8.4].map((v) => ({ value: v })),
    color: '#18A06B',
  },
  {
    label: 'S&P 500',
    value: '5,421',
    delta: { value: '+38 pts', direction: 'up' as const },
    sparkline: [5200, 5250, 5220, 5280, 5310, 5350, 5340, 5380, 5400, 5421].map((v) => ({ value: v })),
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
