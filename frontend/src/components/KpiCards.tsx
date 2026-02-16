'use client';

import { LedgerKpis } from '@/lib/types';

type Props = {
  kpis: LedgerKpis | null;
  throughputPerMin?: number;
  generatorRunning?: boolean;
};

export default function KpiCards({ kpis, throughputPerMin, generatorRunning }: Props): React.JSX.Element {
  const cards = [
    { label: 'Transactions', value: kpis?.tx_count ?? '-' },
    { label: 'Ledger Entries', value: kpis?.entry_count ?? '-' },
    { label: '24h Volume', value: kpis?.volume_24h ?? '-' },
    { label: 'Distinct Accounts', value: kpis?.distinct_accounts ?? '-' },
    { label: 'Throughput/min', value: throughputPerMin?.toFixed(2) ?? '-' },
    { label: 'Seed Generator', value: generatorRunning ? 'ON' : 'OFF' }
  ];

  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
      {cards.map((card) => (
        <div key={card.label} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs uppercase tracking-wide text-slate-500">{card.label}</p>
          <p className="mt-2 text-2xl font-semibold text-ink">{card.value}</p>
        </div>
      ))}
    </div>
  );
}
