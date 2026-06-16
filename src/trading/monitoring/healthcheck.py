"""
Healthcheck HTTP su :8080 e metriche Prometheus.
Gira come task asyncio nella stessa event loop del bot — nessun thread extra.
"""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import uvicorn
from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from loguru import logger
from prometheus_client import Counter, Gauge, make_asgi_app

from trading.risk.circuit_breaker import CircuitBreaker, CircuitState
from trading.scheduler.jobs import TradingScheduler

# ─── METRICHE PROMETHEUS (singleton a livello modulo) ─────────────────────────
# Importabili da main.py e aggiornate dove si verificano gli eventi.

TRADES_TOTAL = Counter(
    "trading_trades_total",
    "Numero totale di trade eseguiti",
)
SIGNALS_TOTAL = Counter(
    "trading_signals_generated_total",
    "Numero totale di segnali generati",
)
CIRCUIT_BREAKER_STATE = Gauge(
    "trading_circuit_breaker_state",
    "Stato circuit breaker: 0=CLOSED, 1=HALF_OPEN, 2=OPEN",
)
IB_CONNECTED = Gauge(
    "trading_ib_connected",
    "Connessione IB Gateway: 1=connesso, 0=disconnesso",
)
DAILY_PNL_USD = Gauge(
    "trading_daily_pnl_usd",
    "PnL realizzato della sessione corrente in USD",
)

_CB_STATE_VALUE: dict[CircuitState, int] = {
    CircuitState.CLOSED: 0,
    CircuitState.HALF_OPEN: 1,
    CircuitState.OPEN: 2,
}


# ─── HEALTHCHECK APP ──────────────────────────────────────────────────────────


class HealthCheck:
    """
    Espone:
      GET /health   — JSON con stato dei componenti; HTTP 503 se IB+CB entrambi KO
      GET /metrics  — endpoint Prometheus (scraped da Grafana/Prometheus)

    Dipendenze iniettate come callable per evitare accoppiamento circolare con IBClient:
      ib_connected_getter  → lambda: ib_client.ib.isConnected()
      daily_pnl_getter     → lambda: repository.get_today_pnl()

    Lifecycle: start() avvia uvicorn con asyncio.create_task(); stop() segnala
    l'uscita e attende il termine del task.
    """

    def __init__(
        self,
        circuit_breaker: CircuitBreaker,
        scheduler: TradingScheduler,
        ib_connected_getter: Callable[[], bool],
        daily_pnl_getter: Callable[[], float],
    ) -> None:
        self._cb = circuit_breaker
        self._scheduler = scheduler
        self._ib_connected = ib_connected_getter
        self._daily_pnl = daily_pnl_getter
        self._started_at: datetime | None = None
        self._server: uvicorn.Server | None = None
        self._serve_task: asyncio.Task | None = None
        self._app = self._build_app()

    def _build_app(self) -> FastAPI:
        app = FastAPI(title="trader-bot healthcheck", docs_url=None, redoc_url=None)

        @app.get("/health")
        async def health() -> Response:
            return await self._health_response()

        # Prometheus metrics — montato come sub-app ASGI
        app.mount("/metrics", make_asgi_app())

        return app

    async def _health_response(self) -> Response:
        ib_ok = self._ib_connected()
        cb_state = self._cb.state
        cb_open = self._cb.is_open()
        pnl = self._daily_pnl()

        uptime = (
            (datetime.now(UTC) - self._started_at).total_seconds()
            if self._started_at
            else 0.0
        )

        # Aggiorna metriche in occasione di ogni scrape /health
        IB_CONNECTED.set(1 if ib_ok else 0)
        CIRCUIT_BREAKER_STATE.set(_CB_STATE_VALUE.get(cb_state, 2))
        DAILY_PNL_USD.set(pnl)

        if not ib_ok and cb_open:
            status = "error"
        elif not ib_ok or cb_open:
            status = "degraded"
        else:
            status = "ok"

        body: dict[str, Any] = {
            "status": status,
            "ib_connected": ib_ok,
            "circuit_breaker": cb_state,
            "daily_pnl_usd": round(pnl, 2),
            "uptime_seconds": round(uptime, 1),
            "scheduler_next_runs": self._scheduler.next_run_times(),
        }

        http_status = 503 if status == "error" else 200
        return JSONResponse(content=body, status_code=http_status)

    async def start(self, host: str = "0.0.0.0", port: int = 8080) -> None:
        self._started_at = datetime.now(UTC)
        config = uvicorn.Config(
            self._app,
            host=host,
            port=port,
            log_level="warning",
            access_log=False,
        )
        self._server = uvicorn.Server(config)
        self._serve_task = asyncio.create_task(
            self._server.serve(), name="healthcheck-server"
        )
        logger.info("HealthCheck avviato su {}:{}", host, port)

    async def stop(self) -> None:
        if self._server is not None:
            self._server.should_exit = True
        if self._serve_task is not None:
            try:
                await asyncio.wait_for(self._serve_task, timeout=5.0)
            except TimeoutError:
                logger.warning("HealthCheck: timeout nello shutdown, task cancellato")
                self._serve_task.cancel()
        logger.info("HealthCheck fermato")
