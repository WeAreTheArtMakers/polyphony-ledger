'use client';

import { useEffect, useState } from 'react';

import LedgerTable from '@/components/LedgerTable';
import { api } from '@/lib/api';
import { BatchRow, LedgerRow } from '@/lib/types';

function BatchPanel({ rows }: { rows: BatchRow[] }): React.JSX.Element {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="mb-2 text-lg font-semibold">Batches by tx_id</h3>
      <div className="max-h-[260px] overflow-auto">
        <table className="w-full text-left text-xs">
          <thead className="sticky top-0 bg-slate-100">
            <tr>
              <th className="px-2 py-2">tx_id</th>
              <th className="px-2 py-2">workspace</th>
              <th className="px-2 py-2">entries</th>
              <th className="px-2 py-2">debit</th>
              <th className="px-2 py-2">credit</th>
              <th className="px-2 py-2">created_at</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.tx_id} className="border-b border-slate-100">
                <td className="px-2 py-2">{row.tx_id}</td>
                <td className="px-2 py-2">{row.workspace_id}</td>
                <td className="px-2 py-2">{row.entries}</td>
                <td className="px-2 py-2">{row.total_debit}</td>
                <td className="px-2 py-2">{row.total_credit}</td>
                <td className="px-2 py-2">{new Date(row.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function LedgerPage(): React.JSX.Element {
  const [ledgerRows, setLedgerRows] = useState<LedgerRow[]>([]);
  const [batches, setBatches] = useState<BatchRow[]>([]);

  const refresh = async () => {
    const [entries, batchRows] = await Promise.all([api.ledgerRecent(150), api.ledgerBatches(80)]);
    setLedgerRows(entries);
    setBatches(batchRows);
  };

  useEffect(() => {
    void refresh();
    const interval = setInterval(() => {
      void refresh();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Ledger</h1>
      <BatchPanel rows={batches} />
      <LedgerTable rows={ledgerRows} />
    </div>
  );
}
