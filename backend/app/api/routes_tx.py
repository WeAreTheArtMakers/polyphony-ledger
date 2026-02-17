from __future__ import annotations

import asyncio
import random
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.config import get_settings
from app.db.session import get_pg_pool
from app.kafka.producer import KafkaProducer
from app.kafka.serde import get_serde
from app.logging import get_logger
from app.metrics import TX_INGESTED_TOTAL
from app.tracing import current_trace_id, get_tracer, inject_trace_headers

router = APIRouter(prefix="/tx", tags=["transactions"])
logger = get_logger(__name__)
tracer = get_tracer(__name__)


class TxIngestRequest(BaseModel):
    payer_account: str = Field(..., min_length=3)
    payee_account: str = Field(..., min_length=3)
    asset: str = Field(..., min_length=3)
    amount: Decimal = Field(..., gt=0)
    occurred_at: datetime | None = None
    event_id: UUID
    correlation_id: str | None = None
    payment_memo: str | None = None
    workspace_id: str | None = None
    client_id: str | None = None
    force_v1: bool = False


class TrafficGenerator:
    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._running = False
        self._rate_per_sec = 2.0

    async def _loop(self, rate_per_sec: float) -> None:
        settings = get_settings()
        serde = get_serde()
        producer = KafkaProducer(client_id_suffix="traffic-generator")
        self._running = True
        self._rate_per_sec = rate_per_sec
        interval = max(0.01, 1.0 / rate_per_sec)
        accounts = [f"acct_{i:03d}" for i in range(1, 31)]
        assets = sorted(settings.allowed_assets_set)

        try:
            while self._running:
                payer = random.choice(accounts)
                payee = random.choice([x for x in accounts if x != payer])
                asset = random.choice(assets)
                amount = Decimal(random.choice(["0.01", "0.1", "1", "2.5", "5"]))
                event_id = str(uuid.uuid4())
                correlation_id = str(uuid.uuid4())
                workspace_id = random.choice(["default", "team-red", "team-blue"])
                payload = {
                    "payer_account": payer,
                    "payee_account": payee,
                    "asset": asset,
                    "amount": amount,
                    "occurred_at": datetime.now(timezone.utc),
                    "event_id": event_id,
                    "correlation_id": correlation_id,
                    "payment_memo": "seeded-traffic",
                    "workspace_id": workspace_id,
                    "client_id": "loadgen",
                }
                wire = serde.serialize_tx_raw(payload, force_v1=random.random() < 0.35)
                headers = inject_trace_headers(
                    {
                        "correlation_id": correlation_id,
                        "trace_id": current_trace_id(),
                    }
                )
                producer.produce_sync(
                    topic=settings.tx_raw_topic,
                    key=payer,
                    value=wire,
                    headers=headers,
                )
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            pass
        finally:
            producer.flush()
            self._running = False

    def status(self) -> dict[str, object]:
        return {
            "running": self._running,
            "rate_per_sec": self._rate_per_sec,
        }

    async def start(self, rate_per_sec: float) -> None:
        if self._task and not self._task.done():
            self._running = False
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        self._task = asyncio.create_task(self._loop(rate_per_sec))

    async def stop(self) -> None:
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task


import contextlib


_generator = TrafficGenerator()


def get_generator() -> TrafficGenerator:
    return _generator


@router.post("/ingest")
async def ingest_tx(req: TxIngestRequest) -> dict[str, object]:
    settings = get_settings()
    if req.asset.upper().strip() not in settings.allowed_assets_set:
        raise HTTPException(status_code=400, detail=f"asset must be one of {sorted(settings.allowed_assets_set)}")

    serde = get_serde()
    producer = KafkaProducer(client_id_suffix="api")

    event_id = str(req.event_id)
    correlation_id = req.correlation_id or str(uuid.uuid4())
    workspace_id = req.workspace_id or "default"
    occurred_at = (req.occurred_at or datetime.now(timezone.utc)).astimezone(timezone.utc)
    version = "v1" if req.force_v1 else "v2"

    with tracer.start_as_current_span("api.tx.ingest") as span:
        span.set_attribute("event_id", event_id)
        span.set_attribute("correlation_id", correlation_id)
        span.set_attribute("payer", req.payer_account)
        span.set_attribute("asset", req.asset.upper().strip())
        span.set_attribute("amount", str(req.amount))

        record = {
            "payer_account": req.payer_account,
            "payee_account": req.payee_account,
            "asset": req.asset.upper().strip(),
            "amount": req.amount,
            "occurred_at": occurred_at,
            "event_id": event_id,
            "correlation_id": correlation_id,
            "payment_memo": req.payment_memo,
            "workspace_id": workspace_id,
            "client_id": req.client_id,
        }
        wire = serde.serialize_tx_raw(record, force_v1=req.force_v1)
        headers = inject_trace_headers(
            {
                "correlation_id": correlation_id,
                "trace_id": current_trace_id(),
            }
        )

        producer.produce_sync(
            topic=settings.tx_raw_topic,
            key=req.payer_account.lower(),
            value=wire,
            headers=headers,
        )
        producer.flush()

    TX_INGESTED_TOTAL.labels(version=version, asset=req.asset.upper().strip(), workspace_id=workspace_id).inc()

    return {
        "status": "accepted",
        "event_id": event_id,
        "correlation_id": correlation_id,
        "workspace_id": workspace_id,
        "schema_version": version,
    }


@router.get("/recent/raw")
async def recent_raw(limit: int = Query(default=30, ge=1, le=200)) -> list[dict]:
    pool = get_pg_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT event_id::text, workspace_id, correlation_id, payload, received_at
            FROM events
            ORDER BY id DESC
            LIMIT $1
            """,
            limit,
        )
    return [dict(r) for r in rows]


@router.get("/recent/validated")
async def recent_validated(limit: int = Query(default=30, ge=1, le=200)) -> list[dict]:
    pool = get_pg_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT tx_id::text, event_id::text, workspace_id, payer_account, payee_account,
                   asset, amount::text, correlation_id, occurred_at, created_at
            FROM ledger_transactions
            ORDER BY created_at DESC
            LIMIT $1
            """,
            limit,
        )
    return [dict(r) for r in rows]


@router.post("/generator/start")
async def generator_start(rate_per_sec: float = Query(default=5.0, ge=0.1, le=100.0)) -> dict[str, object]:
    await _generator.start(rate_per_sec)
    return {"status": "started", **_generator.status()}


@router.post("/generator/stop")
async def generator_stop() -> dict[str, object]:
    await _generator.stop()
    return {"status": "stopped", **_generator.status()}


@router.get("/generator/status")
async def generator_status() -> dict[str, object]:
    return _generator.status()
