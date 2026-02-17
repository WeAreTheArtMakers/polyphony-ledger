'use client';

import { FormEvent, useState } from 'react';

import { api } from '@/lib/api';

const assets = ['BTC', 'ETH', 'USDT'];

function makeUuid(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (char) => {
    const rand = Math.random() * 16 | 0;
    const value = char === 'x' ? rand : (rand & 0x3) | 0x8;
    return value.toString(16);
  });
}

export default function TxIngestForm(): React.JSX.Element {
  const [payload, setPayload] = useState({
    payer_account: 'acct_001',
    payee_account: 'acct_002',
    asset: 'USDT',
    amount: '12.5',
    payment_memo: 'demo transfer',
    workspace_id: 'default',
    client_id: 'ui-client',
    force_v1: false
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string>('');

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setResult('');
    try {
      const eventId = makeUuid();
      const correlationId = makeUuid();
      const res = await api.ingestTx({
        ...payload,
        amount: Number(payload.amount),
        event_id: eventId,
        correlation_id: correlationId
      });
      setResult(
        JSON.stringify(
          {
            event_id: eventId,
            correlation_id: correlationId,
            response: res
          },
          null,
          2
        )
      );
    } catch (err) {
      setResult(String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={onSubmit} className="space-y-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="text-lg font-semibold">Ingest Transaction</h3>
      <div className="grid gap-3 sm:grid-cols-2">
        <input
          className="rounded-lg border border-slate-300 px-3 py-2"
          placeholder="payer_account"
          value={payload.payer_account}
          onChange={(e) => setPayload((v) => ({ ...v, payer_account: e.target.value }))}
        />
        <input
          className="rounded-lg border border-slate-300 px-3 py-2"
          placeholder="payee_account"
          value={payload.payee_account}
          onChange={(e) => setPayload((v) => ({ ...v, payee_account: e.target.value }))}
        />
        <select
          className="rounded-lg border border-slate-300 px-3 py-2"
          value={payload.asset}
          onChange={(e) => setPayload((v) => ({ ...v, asset: e.target.value }))}
        >
          {assets.map((asset) => (
            <option key={asset}>{asset}</option>
          ))}
        </select>
        <input
          className="rounded-lg border border-slate-300 px-3 py-2"
          placeholder="amount"
          value={payload.amount}
          onChange={(e) => setPayload((v) => ({ ...v, amount: e.target.value }))}
        />
        <input
          className="rounded-lg border border-slate-300 px-3 py-2"
          placeholder="workspace_id"
          value={payload.workspace_id}
          onChange={(e) => setPayload((v) => ({ ...v, workspace_id: e.target.value }))}
        />
        <input
          className="rounded-lg border border-slate-300 px-3 py-2"
          placeholder="client_id"
          value={payload.client_id}
          onChange={(e) => setPayload((v) => ({ ...v, client_id: e.target.value }))}
        />
      </div>
      <input
        className="w-full rounded-lg border border-slate-300 px-3 py-2"
        placeholder="payment_memo"
        value={payload.payment_memo}
        onChange={(e) => setPayload((v) => ({ ...v, payment_memo: e.target.value }))}
      />
      <label className="flex items-center gap-2 text-sm text-slate-600">
        <input
          type="checkbox"
          checked={payload.force_v1}
          onChange={(e) => setPayload((v) => ({ ...v, force_v1: e.target.checked }))}
        />
        Produce as tx_raw schema v1 (compatibility demo)
      </label>
      <button
        disabled={loading}
        className="rounded-lg bg-ink px-4 py-2 font-medium text-white hover:bg-sea disabled:cursor-not-allowed disabled:opacity-60"
      >
        {loading ? 'Sending...' : 'Send'}
      </button>
      {result && <pre className="overflow-auto rounded-lg bg-slate-100 p-3 text-xs text-slate-700">{result}</pre>}
    </form>
  );
}
