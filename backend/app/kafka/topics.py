from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TopicSpec:
    name: str
    partitions: int
    replication_factor: int = 1


TX_RAW = "tx_raw"
TX_VALIDATED = "tx_validated"
LEDGER_ENTRY_BATCHES = "ledger_entry_batches"
BALANCE_SNAPSHOTS = "balance_snapshots"
DLQ_TX_RAW = "dlq_tx_raw"
DLQ_TX_VALIDATED = "dlq_tx_validated"
DLQ_LEDGER_BATCHES = "dlq_ledger_batches"
DLQ_CLICKHOUSE = "dlq_clickhouse"


def required_topics() -> list[TopicSpec]:
    return [
        TopicSpec(TX_RAW, 6),
        TopicSpec(TX_VALIDATED, 6),
        TopicSpec(LEDGER_ENTRY_BATCHES, 12),
        TopicSpec(BALANCE_SNAPSHOTS, 6),
        TopicSpec(DLQ_TX_RAW, 3),
        TopicSpec(DLQ_TX_VALIDATED, 3),
        TopicSpec(DLQ_LEDGER_BATCHES, 3),
        TopicSpec(DLQ_CLICKHOUSE, 3),
    ]
