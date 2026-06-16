"""
Client per il Flex Web Service di IBKR — scarica report di eseguiti per la rendicontazione fiscale.
Flusso in due chiamate HTTP: SendRequest → GetStatement (con retry se il report non è pronto).
Documentazione ufficiale: Account Management > Reports > Flex Queries.
"""

import asyncio
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx
from loguru import logger

# Endpoint pubblici del Flex Web Service IBKR (v3)
_SEND_URL = (
    "https://ndcdyn.interactivebrokers.com"
    "/AccountManagement/FlexWebService/SendRequest"
)
_GET_URL = (
    "https://ndcdyn.interactivebrokers.com"
    "/AccountManagement/FlexWebService/GetStatement"
)

# Messaggio che IBKR restituisce quando il report è ancora in generazione
_NOT_READY = "Statement generation in progress"


@dataclass
class FlexTrade:
    """Trade estratto dal report Flex — una riga per ogni eseguito parziale o totale."""

    ibkr_exec_id: str
    symbol: str
    action: str          # "BUY" o "SELL"
    quantity: int
    price: float
    commission: float    # sempre negativo nella convenzione IBKR
    realized_pnl: float
    trade_datetime: datetime


class FlexQueryClient:
    """
    Scarica e parsa il report Flex di IBKR tramite il Flex Web Service v3.

    Flusso:
      1. SendRequest  → ReferenceCode (il report viene accodato lato IBKR)
      2. GetStatement → XML con i trade (retry finché "not ready")
      3. Parsing XML  → list[FlexTrade]

    Se il client non è configurato (token o query_id vuoti), download_trades()
    ritorna immediatamente una lista vuota senza effettuare chiamate HTTP.
    """

    def __init__(self, token: str, query_id: str) -> None:
        self._token = token
        self._query_id = query_id
        self._enabled = bool(token and query_id)

    async def download_trades(
        self,
        max_retries: int = 8,
        retry_delay: float = 5.0,
    ) -> list[FlexTrade]:
        """
        Scarica il report Flex e ritorna i trade del periodo configurato nella query.
        In caso di errore non recuperabile, logga e ritorna lista vuota.
        """
        if not self._enabled:
            logger.debug("FlexQueryClient non configurato, nessun download")
            return []

        async with httpx.AsyncClient(timeout=30.0) as client:
            ref_code = await self._request_report(client)
            if ref_code is None:
                return []

            xml_text = await self._download_report(client, ref_code, max_retries, retry_delay)
            if xml_text is None:
                return []

        return self._parse_trades(xml_text)

    async def _request_report(self, client: httpx.AsyncClient) -> str | None:
        """Invia la richiesta di generazione report e ritorna il ReferenceCode."""
        try:
            resp = await client.get(
                _SEND_URL,
                params={"t": self._token, "q": self._query_id, "v": "3"},
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("FlexQuery SendRequest fallita: {}", exc)
            return None

        root = ET.fromstring(resp.text)
        status = root.findtext("Status", default="")
        if status != "Success":
            error = root.findtext("ErrorMessage", default=resp.text[:200])
            logger.error("FlexQuery SendRequest errore: {}", error)
            return None

        ref_code = root.findtext("ReferenceCode", default="")
        if not ref_code:
            logger.error("FlexQuery: ReferenceCode mancante nella risposta")
            return None

        logger.debug("FlexQuery: ReferenceCode={}", ref_code)
        return ref_code

    async def _download_report(
        self,
        client: httpx.AsyncClient,
        ref_code: str,
        max_retries: int,
        retry_delay: float,
    ) -> str | None:
        """
        Scarica il report usando il ReferenceCode.
        IBKR può rispondere con 'Statement generation in progress' per i primi tentativi.
        """
        for attempt in range(1, max_retries + 1):
            try:
                resp = await client.get(
                    _GET_URL,
                    params={"q": ref_code, "v": "3"},
                )
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                logger.error("FlexQuery GetStatement tentativo {}: {}", attempt, exc)
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay)
                continue

            # Il report non è ancora pronto
            if _NOT_READY in resp.text:
                logger.debug(
                    "FlexQuery: report non pronto (tentativo {}/{}), attendo {:.0f}s",
                    attempt, max_retries, retry_delay,
                )
                await asyncio.sleep(retry_delay)
                continue

            return resp.text

        logger.error(
            "FlexQuery: report non disponibile dopo {} tentativi", max_retries
        )
        return None

    def _parse_trades(self, xml_text: str) -> list[FlexTrade]:
        """
        Parsa il documento XML Flex e ritorna i trade.
        I campi assenti o non numerici vengono saltati con un warning.
        """
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            logger.error("FlexQuery: errore parsing XML: {}", exc)
            return []

        trades: list[FlexTrade] = []
        for trade_el in root.iter("Trade"):
            try:
                trades.append(self._parse_trade_element(trade_el))
            except (KeyError, ValueError) as exc:
                logger.warning(
                    "FlexQuery: trade ignorato (campo mancante o non valido): {}", exc
                )

        logger.info("FlexQuery: {} trade estratti dal report", len(trades))
        return trades

    @staticmethod
    def _parse_trade_element(el: ET.Element) -> FlexTrade:
        """
        Converte un elemento <Trade> XML in FlexTrade.
        Il campo dateTime di IBKR usa il formato 'YYYYMMDD;HHMMSS'.
        """
        dt_raw = el.attrib["dateTime"]          # es. "20260616;093512"
        date_part, time_part = dt_raw.split(";")
        trade_dt = datetime(
            year=int(date_part[:4]),
            month=int(date_part[4:6]),
            day=int(date_part[6:8]),
            hour=int(time_part[:2]),
            minute=int(time_part[2:4]),
            second=int(time_part[4:6]),
            tzinfo=UTC,
        )

        return FlexTrade(
            ibkr_exec_id=el.attrib["ibExecID"],
            symbol=el.attrib["symbol"],
            action="BUY" if el.attrib["buySell"].upper() == "BUY" else "SELL",
            quantity=int(float(el.attrib["quantity"])),
            price=float(el.attrib["tradePrice"]),
            commission=float(el.attrib.get("commission", "0")),
            realized_pnl=float(el.attrib.get("realizedPnL", "0")),
            trade_datetime=trade_dt,
        )


# ─── FACTORY ─────────────────────────────────────────────────────────────────


def build_flex_client() -> FlexQueryClient:
    """Costruisce FlexQueryClient leggendo settings. Se non configurato, è no-op."""
    from trading.config import settings

    return FlexQueryClient(
        token=settings.ibkr_flex_token,
        query_id=settings.ibkr_flex_query_id,
    )
