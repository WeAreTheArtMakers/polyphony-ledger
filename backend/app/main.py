from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from prometheus_client import make_asgi_app

from app.api.routes_analytics import router as analytics_router
from app.api.routes_balances import router as balances_router
from app.api.routes_governance import router as governance_router
from app.api.routes_health import router as health_router
from app.api.routes_ledger import router as ledger_router
from app.api.routes_observability import router as observability_router
from app.api.routes_replay import router as replay_router
from app.api.routes_tx import get_generator, router as tx_router
from app.config import get_settings
from app.db.session import close_pg_pool, get_pg_pool, init_pg_pool
from app.kafka.serde import get_serde
from app.logging import setup_logging
from app.metrics import HTTP_REQUESTS_TOTAL
from app.tracing import get_tracer, instrument_fastapi, setup_tracing
from app.websocket import stream_with_polling

settings = get_settings()
setup_logging()
setup_tracing("polyphony-api")
tracer = get_tracer(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_pg_pool()
    get_serde()
    generator = get_generator()
    if settings.traffic_generator_enabled:
        await generator.start(settings.traffic_generator_rate_per_sec)

    try:
        yield
    finally:
        await generator.stop()
        await close_pg_pool()


app = FastAPI(title=settings.app_name, default_response_class=ORJSONResponse, lifespan=lifespan)
instrument_fastapi(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/metrics", make_asgi_app())

app.include_router(health_router)
app.include_router(tx_router)
app.include_router(ledger_router)
app.include_router(balances_router)
app.include_router(replay_router)
app.include_router(analytics_router)
app.include_router(observability_router)
app.include_router(governance_router)


@app.middleware("http")
async def prometheus_http_middleware(request: Request, call_next):
    response = await call_next(request)
    HTTP_REQUESTS_TOTAL.labels(
        method=request.method,
        path=request.url.path,
        status=str(response.status_code),
    ).inc()
    return response


async def _ws_snapshot() -> dict:
    pool = get_pg_pool()
    async with pool.acquire() as conn:
        balances = await conn.fetch(
            """
            SELECT workspace_id, account_id, asset, balance::text, updated_at
            FROM account_balances
            ORDER BY updated_at DESC
            LIMIT 20
            """
        )
        ledger = await conn.fetch(
            """
            SELECT entry_id, tx_id::text, workspace_id, account_id, side, asset,
                   amount::text, correlation_id, occurred_at
            FROM ledger_entries
            ORDER BY entry_id DESC
            LIMIT 20
            """
        )
    return {
        "type": "snapshot",
        "balances": [dict(r) for r in balances],
        "ledger": [dict(r) for r in ledger],
    }


@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket) -> None:
    await stream_with_polling(websocket, fetcher=_ws_snapshot, interval_seconds=2.0)


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": settings.app_name, "status": "ok"}
