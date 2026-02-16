export type LedgerKpis = {
  tx_count: number;
  entry_count: number;
  volume_24h: string;
  distinct_accounts: number;
};

export type BalanceRow = {
  workspace_id: string;
  account_id: string;
  asset: string;
  balance: string;
  updated_at: string;
};

export type LedgerRow = {
  entry_id: number;
  tx_id: string;
  workspace_id: string;
  account_id: string;
  side: 'debit' | 'credit';
  asset: string;
  amount: string;
  correlation_id: string;
  occurred_at: string;
  created_at?: string;
};

export type BatchRow = {
  tx_id: string;
  workspace_id: string;
  created_at: string;
  entries: number;
  total_debit: string;
  total_credit: string;
};

export type AnalyticsPoint = {
  bucket: string;
  asset?: string;
  volume?: number;
  netflow?: number;
};

export type TopAccountPoint = {
  account_id: string;
  netflow: number;
};

export type WsSnapshot = {
  type: string;
  balances: BalanceRow[];
  ledger: LedgerRow[];
};
