from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    app_name: str = "polyphony-ledger-backend"
    environment: Literal["dev", "prod", "test"] = "dev"
    log_level: str = "INFO"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000"

    postgres_dsn: str = "postgresql://polyphony:polyphony@postgres:5432/polyphony"
    postgres_min_pool: int = 2
    postgres_max_pool: int = 20

    kafka_bootstrap_servers: str = "redpanda:9092"
    schema_registry_url: str = "http://redpanda:8081"
    kafka_client_id: str = "polyphony-ledger"
    kafka_startup_timeout_seconds: float = 90.0
    producer_max_retries: int = 6
    producer_retry_base_ms: int = 200

    tx_raw_topic: str = "tx_raw"
    tx_validated_topic: str = "tx_validated"
    ledger_entry_batches_topic: str = "ledger_entry_batches"
    balance_snapshots_topic: str = "balance_snapshots"
    dlq_tx_raw_topic: str = "dlq_tx_raw"
    dlq_tx_validated_topic: str = "dlq_tx_validated"
    dlq_ledger_batches_topic: str = "dlq_ledger_batches"
    dlq_clickhouse_topic: str = "dlq_clickhouse"

    validator_group_id: str = "validator-cg"
    ledger_writer_group_id: str = "ledger-writer-cg"
    balance_projector_group_id: str = "balance-projector-cg"
    clickhouse_writer_group_id: str = "clickhouse-writer-cg"

    clickhouse_host: str = "clickhouse"
    clickhouse_port: int = 8123
    clickhouse_username: str = "default"
    clickhouse_password: str = ""
    clickhouse_database: str = "polyphony"

    otel_enabled: bool = True
    otel_exporter_endpoint: str = "http://otel-collector:4317"

    traffic_generator_enabled: bool = False
    traffic_generator_rate_per_sec: float = 2.0

    outbox_batch_size: int = 200
    outbox_poll_interval_ms: int = 500

    balance_snapshot_every_batches: int = 20

    allowed_assets: str = Field(default="BTC,ETH,USDT")
    auth_mode: Literal["off", "header", "oidc"] = "off"
    default_workspace_role: Literal["viewer", "operator", "admin", "owner"] = "owner"
    default_workspace_monthly_tx_quota: int = 1_000_000
    oidc_issuer_url: str = ""
    oidc_audience: str = ""
    oidc_jwks_url: str = ""
    oidc_role_claim: str = "realm_access.roles"
    oidc_workspace_claim: str = "workspace_id"
    oidc_subject_claim: str = "sub"
    oidc_algorithms: str = "RS256,ES256"
    autoscale_target_lag: int = 200
    autoscale_target_throughput_per_minute: float = 120.0

    @property
    def allowed_assets_set(self) -> set[str]:
        return {x.strip().upper() for x in self.allowed_assets.split(",") if x.strip()}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
