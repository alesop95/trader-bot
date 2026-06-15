import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from ib_async import IB, Fill, Trade
from loguru import logger

from trading.config import settings

# Intervalli di attesa tra tentativi di reconnect (secondi)
_RECONNECT_DELAYS = [30, 60, 60, 120, 120, 300]


class IBClient:
    """
    Wrapper su ib_async.IB. Responsabile esclusivamente di:
    - connessione e disconnessione
    - reconnect automatico con backoff esponenziale dopo il restart 23:45 ET
    - routing dell'evento execDetails verso i callback registrati
    - routing degli errori IBKR al logger

    Non contiene logica di trading: ordini e dati di mercato vivono
    in OrderManager e MarketDataManager.
    """

    def __init__(self) -> None:
        self.ib = IB()
        self._fill_callbacks: list[Callable[[Fill], Awaitable[None]]] = []
        self._is_connected = False
        self._reconnecting = False

        self.ib.disconnectedEvent += self._on_disconnect
        self.ib.execDetailsEvent += self._on_exec_details
        self.ib.errorEvent += self._on_error

    # ─── CONNESSIONE ──────────────────────────────────────────────────────────

    async def connect(self) -> None:
        await self.ib.connectAsync(
            host=settings.ibkr_host,
            port=settings.ibkr_port,
            clientId=settings.ibkr_client_id,
            readonly=False,
        )
        self._is_connected = True
        logger.info(
            "Connesso a IB Gateway {}:{} (clientId={})",
            settings.ibkr_host,
            settings.ibkr_port,
            settings.ibkr_client_id,
        )

    async def disconnect(self) -> None:
        self._is_connected = False
        self.ib.disconnect()
        logger.info("Disconnesso da IB Gateway")

    @property
    def is_connected(self) -> bool:
        return self._is_connected and self.ib.isConnected()

    # ─── FILL CALLBACKS ───────────────────────────────────────────────────────

    def register_fill_callback(self, callback: Callable[[Fill], Awaitable[None]]) -> None:
        """Registra un handler asincrono chiamato a ogni fill ricevuto da IBKR."""
        self._fill_callbacks.append(callback)

    # ─── SINCRONIZZAZIONE POST-RECONNECT ──────────────────────────────────────

    async def post_reconnect_sync(self) -> None:
        """
        Dopo un reconnect, risincronizza lo stato locale con IB Gateway.
        Le posizioni aperte e gli ordini GTC sono già sui server IBKR e
        sopravvivono al restart; qui aggiorniamo la vista in memoria.
        """
        positions = await self.ib.reqPositionsAsync()
        open_trades = self.ib.openTrades()
        logger.info(
            "Post-reconnect: {} posizioni IBKR, {} ordini aperti",
            len(positions),
            len(open_trades),
        )

    # ─── EVENT HANDLERS ───────────────────────────────────────────────────────

    def _on_disconnect(self) -> None:
        """
        Chiamato da ib_async quando la connessione cade.
        Tipicamente: restart IB Gateway 23:45 ET, perdita di rete, crash Gateway.
        """
        if self._is_connected and not self._reconnecting:
            logger.warning("IB Gateway disconnesso — avvio sequenza di reconnect")
            asyncio.ensure_future(self._reconnect_loop())

    async def _reconnect_loop(self) -> None:
        self._is_connected = False
        self._reconnecting = True
        for i, delay in enumerate(_RECONNECT_DELAYS, start=1):
            logger.info("Reconnect tentativo {}/{} tra {}s", i, len(_RECONNECT_DELAYS), delay)
            await asyncio.sleep(delay)
            try:
                await self.connect()
                await self.post_reconnect_sync()
                self._reconnecting = False
                logger.info("Reconnect riuscito al tentativo {}", i)
                return
            except Exception as exc:
                logger.warning("Tentativo {} fallito: {}", i, exc)
        self._reconnecting = False
        logger.error(
            "Tutti i {} tentativi di reconnect falliti — intervento manuale necessario",
            len(_RECONNECT_DELAYS),
        )

    def _on_exec_details(self, trade: Trade, fill: Fill) -> None:
        """Chiamato da ib_async a ogni fill. Smista ai callback registrati."""
        asyncio.ensure_future(self._dispatch_fill(fill))

    async def _dispatch_fill(self, fill: Fill) -> None:
        for callback in self._fill_callbacks:
            try:
                await callback(fill)
            except Exception as exc:
                logger.error(
                    "Errore nel fill callback per execId={}: {}",
                    fill.execution.execId,
                    exc,
                )

    def _on_error(
        self,
        req_id: int,
        error_code: int,
        error_string: str,
        contract: Any,
    ) -> None:
        """
        Classifica gli errori IBKR per livello di log.
        Codici < 1000 sono errori reali; >= 2000 sono notifiche informative.
        """
        if error_code == 162:
            # Pacing violation: troppi reqHistoricalData in poco tempo
            logger.warning("IBKR pacing violation (162): {}", error_string)
        elif error_code in (200, 354):
            # 200 = no security definition, 354 = not subscribed
            logger.warning("IBKR contratto/dati non disponibili ({}): {}", error_code, error_string)
        elif 1100 <= error_code <= 1102:
            # Connectivity: 1100=lost, 1101=restored, 1102=restored (data ok)
            logger.warning("IBKR connettività ({}): {}", error_code, error_string)
        elif error_code >= 2000:
            logger.debug("IBKR info ({}): {}", error_code, error_string)
        else:
            logger.error("IBKR errore {} (reqId={}): {}", error_code, req_id, error_string)
