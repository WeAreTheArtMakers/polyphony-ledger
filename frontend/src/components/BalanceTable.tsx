'use client';

import { BalanceRow } from '@/lib/types';

type Props = {
  rows: BalanceRow[];
};

export default function BalanceTable({ rows }: Props): React.JSX.Element {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="mb-2 text-lg font-semibold">Projected Balances</h3>
      <div className="max-h-[440px] overflow-auto">
        <table className="w-full text-left text-xs">
          <thead className="sticky top-0 bg-slate-100">
            <tr>
              <th className="px-2 py-2">workspace</th>
              <th className="px-2 py-2">account</th>
              <th className="px-2 py-2">asset</th>
              <th className="px-2 py-2">balance</th>
              <th className="px-2 py-2">updated_at</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, idx) => (
              <tr key={`${row.account_id}-${row.asset}-${idx}`} className="border-b border-slate-100">
                <td className="px-2 py-2">{row.workspace_id}</td>
                <td className="px-2 py-2">{row.account_id}</td>
                <td className="px-2 py-2">{row.asset}</td>
                <td className="px-2 py-2">{row.balance}</td>
                <td className="px-2 py-2">{new Date(row.updated_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
