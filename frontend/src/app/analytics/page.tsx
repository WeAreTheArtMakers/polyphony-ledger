'use client';

import { useEffect, useMemo, useState } from 'react';

import AnalyticsCharts from '@/components/AnalyticsCharts';
import { api } from '@/lib/api';
import { AnalyticsPoint, TopAccountPoint } from '@/lib/types';

export default function AnalyticsPage(): React.JSX.Element {
  const [workspaceId, setWorkspaceId] = useState('default');
  const [minutes, setMinutes] = useState(60);
  const [accountId, setAccountId] = useState('acct_001');
  const [asset, setAsset] = useState('USDT');

  const [volumeRows, setVolumeRows] = useState<AnalyticsPoint[]>([]);
  const [netflowRows, setNetflowRows] = useState<AnalyticsPoint[]>([]);
  const [topRows, setTopRows] = useState<TopAccountPoint[]>([]);

  const refresh = async () => {
    const [volume, netflow, top] = await Promise.all([
      api.volumePerAsset(minutes, workspaceId),
      api.netflow(accountId, minutes, workspaceId),
      api.topAccounts(asset, minutes, workspaceId)
    ]);
    setVolumeRows((volume.rows || []).map((r: any) => ({ ...r, volume: Number(r.volume || 0) })));
    setNetflowRows((netflow.rows || []).map((r: any) => ({ ...r, netflow: Number(r.netflow || 0) })));
    setTopRows((top.rows || []).map((r: any) => ({ ...r, netflow: Number(r.netflow || 0) })));
  };

  useEffect(() => {
    void refresh();
  }, [workspaceId, minutes, accountId, asset]);

  const summary = useMemo(() => {
    return {
      volume: volumeRows.reduce((acc, row) => acc + Number(row.volume || 0), 0),
      netflow: netflowRows.reduce((acc, row) => acc + Number(row.netflow || 0), 0)
    };
  }, [volumeRows, netflowRows]);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">ClickHouse Analytics</h1>
      <div className="grid gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:grid-cols-2 xl:grid-cols-5">
        <input
          className="rounded-lg border border-slate-300 px-3 py-2"
          value={workspaceId}
          onChange={(e) => setWorkspaceId(e.target.value)}
          placeholder="workspace_id"
        />
        <input
          className="rounded-lg border border-slate-300 px-3 py-2"
          type="number"
          value={minutes}
          onChange={(e) => setMinutes(Number(e.target.value || 60))}
        />
        <input
          className="rounded-lg border border-slate-300 px-3 py-2"
          value={accountId}
          onChange={(e) => setAccountId(e.target.value)}
          placeholder="account_id"
        />
        <input
          className="rounded-lg border border-slate-300 px-3 py-2"
          value={asset}
          onChange={(e) => setAsset(e.target.value.toUpperCase())}
          placeholder="asset"
        />
        <button onClick={refresh} className="rounded-lg bg-ink px-3 py-2 font-medium text-white">
          Refresh
        </button>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs uppercase tracking-wide text-slate-500">Total Volume (window)</p>
          <p className="mt-1 text-2xl font-semibold">{summary.volume.toFixed(4)}</p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs uppercase tracking-wide text-slate-500">Total Netflow (window)</p>
          <p className="mt-1 text-2xl font-semibold">{summary.netflow.toFixed(4)}</p>
        </div>
      </div>
      <AnalyticsCharts volumeRows={volumeRows} netflowRows={netflowRows} topRows={topRows} />
    </div>
  );
}
