CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS events (
    id BIGSERIAL PRIMARY KEY,
    event_id UUID NOT NULL UNIQUE,
    event_type TEXT NOT NULL,
    workspace_id TEXT NOT NULL DEFAULT 'default',
    correlation_id TEXT NOT NULL,
    payload JSONB NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS processed_events (
    consumer_name TEXT NOT NULL,
    event_id TEXT NOT NULL,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (consumer_name, event_id)
);

CREATE TABLE IF NOT EXISTS ledger_transactions (
    tx_id UUID PRIMARY KEY,
    event_id UUID NOT NULL,
    workspace_id TEXT NOT NULL DEFAULT 'default',
    payer_account TEXT NOT NULL,
    payee_account TEXT NOT NULL,
    asset TEXT NOT NULL,
    amount NUMERIC(38, 18) NOT NULL CHECK (amount > 0),
    correlation_id TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ledger_entries (
    entry_id BIGSERIAL PRIMARY KEY,
    tx_id UUID NOT NULL REFERENCES ledger_transactions(tx_id),
    workspace_id TEXT NOT NULL DEFAULT 'default',
    account_id TEXT NOT NULL,
    side TEXT NOT NULL CHECK (side IN ('debit', 'credit')),
    asset TEXT NOT NULL,
    amount NUMERIC(38, 18) NOT NULL CHECK (amount > 0),
    correlation_id TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ledger_entries_tx_id ON ledger_entries(tx_id);
CREATE INDEX IF NOT EXISTS idx_ledger_entries_account_asset ON ledger_entries(workspace_id, account_id, asset);
CREATE INDEX IF NOT EXISTS idx_ledger_entries_occurred_at ON ledger_entries(occurred_at DESC);

CREATE TABLE IF NOT EXISTS account_balances (
    workspace_id TEXT NOT NULL DEFAULT 'default',
    account_id TEXT NOT NULL,
    asset TEXT NOT NULL,
    balance NUMERIC(38, 18) NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (workspace_id, account_id, asset)
);

CREATE TABLE IF NOT EXISTS balance_snapshots (
    snapshot_id BIGSERIAL PRIMARY KEY,
    workspace_id TEXT NOT NULL DEFAULT 'default',
    account_id TEXT NOT NULL,
    asset TEXT NOT NULL,
    balance NUMERIC(38, 18) NOT NULL,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_batch_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_balance_snapshots_captured ON balance_snapshots(captured_at DESC);

CREATE TABLE IF NOT EXISTS workspace_quotas (
    workspace_id TEXT PRIMARY KEY,
    monthly_tx_quota BIGINT NOT NULL CHECK (monthly_tx_quota >= 0),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS workspace_usage (
    workspace_id TEXT NOT NULL,
    period_month DATE NOT NULL,
    tx_ingested BIGINT NOT NULL DEFAULT 0 CHECK (tx_ingested >= 0),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (workspace_id, period_month),
    FOREIGN KEY (workspace_id) REFERENCES workspace_quotas(workspace_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS workspace_members (
    workspace_id TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('viewer', 'operator', 'admin', 'owner')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (workspace_id, subject_id),
    FOREIGN KEY (workspace_id) REFERENCES workspace_quotas(workspace_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS outbox (
    id BIGSERIAL PRIMARY KEY,
    topic TEXT NOT NULL,
    key TEXT NOT NULL,
    workspace_id TEXT NOT NULL DEFAULT 'default',
    payload BYTEA NOT NULL,
    headers JSONB NOT NULL DEFAULT '{}'::JSONB,
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    next_attempt_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_outbox_pending ON outbox(published_at, next_attempt_at) WHERE published_at IS NULL;

CREATE OR REPLACE FUNCTION prevent_mutation_append_only()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'Table % is append-only; mutation blocked', TG_TABLE_NAME;
END;
$$;

DROP TRIGGER IF EXISTS trg_no_update_delete_events ON events;
CREATE TRIGGER trg_no_update_delete_events
BEFORE UPDATE OR DELETE ON events
FOR EACH ROW
EXECUTE FUNCTION prevent_mutation_append_only();

DROP TRIGGER IF EXISTS trg_no_update_delete_ledger_transactions ON ledger_transactions;
CREATE TRIGGER trg_no_update_delete_ledger_transactions
BEFORE UPDATE OR DELETE ON ledger_transactions
FOR EACH ROW
EXECUTE FUNCTION prevent_mutation_append_only();

DROP TRIGGER IF EXISTS trg_no_update_delete_ledger_entries ON ledger_entries;
CREATE TRIGGER trg_no_update_delete_ledger_entries
BEFORE UPDATE OR DELETE ON ledger_entries
FOR EACH ROW
EXECUTE FUNCTION prevent_mutation_append_only();
