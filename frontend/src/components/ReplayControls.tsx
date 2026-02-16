'use client';

import { useState } from 'react';

import { api } from '@/lib/api';

export default function ReplayControls(): JSX.Element {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string>('');

  const runReplay = async () => {
    setLoading(true);
    try {
      const response = await api.replayFromLedger();
      setResult(JSON.stringify(response, null, 2));
    } catch (error) {
      setResult(String(error));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="text-lg font-semibold">Deterministic Projection Replay</h3>
      <p className="text-sm text-slate-600">
        This action truncates <code>account_balances</code> and rebuilds projection from immutable <code>ledger_entries</code>.
      </p>
      <button
        onClick={runReplay}
        disabled={loading}
        className="rounded-lg bg-coral px-4 py-2 font-medium text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {loading ? 'Replaying...' : 'Replay from Ledger'}
      </button>
      {result && <pre className="overflow-auto rounded-lg bg-slate-100 p-3 text-xs">{result}</pre>}
    </div>
  );
}
