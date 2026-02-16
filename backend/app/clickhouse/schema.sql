CREATE DATABASE IF NOT EXISTS polyphony;

CREATE TABLE IF NOT EXISTS polyphony.ledger_entries_raw
(
    ingested_at DateTime64(3) DEFAULT now64(3),
    occurred_at DateTime64(3),
    workspace_id String,
    batch_id String,
    tx_id String,
    event_id String,
    correlation_id String,
    account_id String,
    side LowCardinality(String),
    asset LowCardinality(String),
    amount Decimal(38, 18)
)
ENGINE = MergeTree
ORDER BY (workspace_id, occurred_at, tx_id, account_id);

CREATE TABLE IF NOT EXISTS polyphony.volume_per_asset_1m
(
    bucket DateTime,
    workspace_id String,
    asset LowCardinality(String),
    volume Decimal(38, 18)
)
ENGINE = SummingMergeTree
ORDER BY (bucket, workspace_id, asset);

CREATE TABLE IF NOT EXISTS polyphony.netflow_per_account_1m
(
    bucket DateTime,
    workspace_id String,
    account_id String,
    asset LowCardinality(String),
    netflow Decimal(38, 18)
)
ENGINE = SummingMergeTree
ORDER BY (bucket, workspace_id, account_id, asset);

CREATE TABLE IF NOT EXISTS polyphony.top_accounts_5m
(
    bucket DateTime,
    workspace_id String,
    asset LowCardinality(String),
    account_id String,
    netflow Decimal(38, 18)
)
ENGINE = SummingMergeTree
ORDER BY (bucket, workspace_id, asset, account_id);

CREATE MATERIALIZED VIEW IF NOT EXISTS polyphony.mv_volume_per_asset_1m
TO polyphony.volume_per_asset_1m
AS
SELECT
    toStartOfMinute(occurred_at) AS bucket,
    workspace_id,
    asset,
    sum(amount) AS volume
FROM polyphony.ledger_entries_raw
GROUP BY bucket, workspace_id, asset;

CREATE MATERIALIZED VIEW IF NOT EXISTS polyphony.mv_netflow_per_account_1m
TO polyphony.netflow_per_account_1m
AS
SELECT
    toStartOfMinute(occurred_at) AS bucket,
    workspace_id,
    account_id,
    asset,
    sum(if(side = 'debit', amount, -amount)) AS netflow
FROM polyphony.ledger_entries_raw
GROUP BY bucket, workspace_id, account_id, asset;

CREATE MATERIALIZED VIEW IF NOT EXISTS polyphony.mv_top_accounts_5m
TO polyphony.top_accounts_5m
AS
SELECT
    toStartOfInterval(occurred_at, INTERVAL 5 minute) AS bucket,
    workspace_id,
    asset,
    account_id,
    sum(if(side = 'debit', amount, -amount)) AS netflow
FROM polyphony.ledger_entries_raw
GROUP BY bucket, workspace_id, asset, account_id;
