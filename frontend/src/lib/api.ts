import { BalanceRow, BatchRow, LedgerKpis, LedgerRow } from '@/lib/types';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers || {})
    },
    cache: 'no-store'
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return (await res.json()) as T;
}

export const api = {
  health: () => request<{ status: string }>('/health'),
  ledgerKpis: () => request<LedgerKpis>('/ledger/kpis'),
  ledgerRecent: (limit = 100) => request<LedgerRow[]>(`/ledger/recent?limit=${limit}`),
  ledgerBatches: (limit = 50) => request<BatchRow[]>(`/ledger/batches?limit=${limit}`),
  balances: (workspaceId = 'default', limit = 200) =>
    request<BalanceRow[]>(`/balances?workspace_id=${encodeURIComponent(workspaceId)}&limit=${limit}`),
  recentRaw: (limit = 30) => request<any[]>(`/tx/recent/raw?limit=${limit}`),
  recentValidated: (limit = 30) => request<any[]>(`/tx/recent/validated?limit=${limit}`),
  ingestTx: (payload: Record<string, unknown>) =>
    request<Record<string, unknown>>('/tx/ingest', {
      method: 'POST',
      body: JSON.stringify(payload)
    }),
  replayFromLedger: () =>
    request<{ status: string; summary: Record<string, unknown> }>('/replay/from-ledger', {
      method: 'POST'
    }),
  volumePerAsset: (minutes = 60, workspaceId = 'default') =>
    request<{ rows: any[] }>(`/analytics/volume-per-asset?minutes=${minutes}&workspace_id=${workspaceId}`),
  netflow: (accountId: string, minutes = 60, workspaceId = 'default') =>
    request<{ rows: any[] }>(
      `/analytics/netflow?account_id=${encodeURIComponent(accountId)}&minutes=${minutes}&workspace_id=${workspaceId}`
    ),
  topAccounts: (asset = 'USDT', minutes = 60, workspaceId = 'default') =>
    request<{ rows: any[] }>(
      `/analytics/top-accounts?asset=${encodeURIComponent(asset)}&minutes=${minutes}&workspace_id=${workspaceId}`
    ),
  generatorStatus: () => request<{ running: boolean; rate_per_sec: number }>('/tx/generator/status'),
  generatorStart: (ratePerSec = 5) =>
    request<{ running: boolean; rate_per_sec: number }>(`/tx/generator/start?rate_per_sec=${ratePerSec}`, {
      method: 'POST'
    }),
  generatorStop: () => request<{ running: boolean; rate_per_sec: number }>('/tx/generator/stop', { method: 'POST' }),
  governanceMe: () =>
    request<{ auth_mode: string; subject_id: string; workspace_id: string; role: string }>('/governance/me'),
  governanceQuota: (workspaceId = 'default') =>
    request<{ quota: Record<string, unknown> }>(`/governance/quota?workspace_id=${encodeURIComponent(workspaceId)}`),
  governanceUsage: (workspaceId = 'default', months = 6) =>
    request<{ workspace_id: string; rows: any[] }>(
      `/governance/usage?workspace_id=${encodeURIComponent(workspaceId)}&months=${months}`
    )
};

export { API_BASE };
