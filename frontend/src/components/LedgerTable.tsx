'use client';

import { LedgerRow } from '@/lib/types';

type Props = {
  rows: LedgerRow[];
};

export default function LedgerTable({ rows }: Props): React.JSX.Element {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="mb-2 text-lg font-semibold">Ledger Entries (append-only)</h3>
      <div className="max-h-[520px] overflow-auto">
        <table className="w-full text-left text-xs">
          <thead className="sticky top-0 bg-slate-100">
            <tr>
              <th className="px-2 py-2">entry_id</th>
              <th className="px-2 py-2">tx_id</th>
              <th className="px-2 py-2">workspace</th>
              <th className="px-2 py-2">account</th>
              <th className="px-2 py-2">side</th>
              <th className="px-2 py-2">asset</th>
              <th className="px-2 py-2">amount</th>
              <th className="px-2 py-2">correlation_id</th>
              <th className="px-2 py-2">occurred_at</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.entry_id} className="border-b border-slate-100">
                <td className="px-2 py-2">{row.entry_id}</td>
                <td className="px-2 py-2">{row.tx_id}</td>
                <td className="px-2 py-2">{row.workspace_id}</td>
                <td className="px-2 py-2">{row.account_id}</td>
                <td className={`px-2 py-2 font-semibold ${row.side === 'debit' ? 'text-mint' : 'text-coral'}`}>{row.side}</td>
                <td className="px-2 py-2">{row.asset}</td>
                <td className="px-2 py-2">{row.amount}</td>
                <td className="px-2 py-2">{row.correlation_id}</td>
                <td className="px-2 py-2">{new Date(row.occurred_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
