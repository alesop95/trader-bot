"""
Notifiche Telegram per eventi operativi del bot.
Quando le credenziali non sono configurate, tutti i metodi sono no-op:
il resto del codice non ha bisogno di verificare `telegram_enabled`.
"""

from datetime import date

import telegram
from loguru import logger

from trading.strategy.interfaces import AllocatedSignal, Direction


class TelegramNotifier:
    """
    Invia messaggi HTML al canale Telegram configurato.
    Istanziare con build_notifier() che legge settings.

    Lifecycle: chiamare start() dopo l'avvio e stop() allo shutdown per
    inizializzare/rilasciare il client HTTP di python-telegram-bot 20.x.
    """

    def __init__(self, token: str, chat_id: str) -> None:
        self._bot = telegram.Bot(token=token) if token else None
        self._chat_id = chat_id
        self._enabled = bool(token and chat_id)

    # ─── LIFECYCLE ────────────────────────────────────────────────────────────

    async def start(self) -> None:
        if self._bot is not None:
            await self._bot.initialize()
            logger.info("TelegramNotifier avviato")

    async def stop(self) -> None:
        if self._bot is not None:
            await self._bot.shutdown()
            logger.info("TelegramNotifier fermato")

    # ─── PRIMITIVA ────────────────────────────────────────────────────────────

    async def send(self, text: str) -> None:
        """Invia un messaggio HTML. No-op se non configurato. Non solleva mai."""
        if self._bot is None or not self._chat_id:
            return
        try:
            await self._bot.send_message(
                chat_id=self._chat_id,
                text=text,
                parse_mode="HTML",
            )
        except Exception as exc:
            logger.warning("Telegram send fallita: {}", exc)

    # ─── MESSAGGI OPERATIVI ───────────────────────────────────────────────────

    async def notify_entry(self, signal: AllocatedSignal) -> None:
        direction = "LONG" if signal.direction == Direction.LONG else "SHORT"
        stop_line = (
            f"\nStop: -{signal.stop_loss_pct:.1%}" if signal.stop_loss_pct else ""
        )
        price_line = (
            f" @ <code>${signal.limit_price:.4f}</code>" if signal.limit_price else ""
        )
        await self.send(
            f"[ENTRY] <b>{signal.symbol}</b> {direction}\n"
            f"Shares: {signal.shares}{price_line}\n"
            f"Target: ${signal.target_usd:,.0f} USD{stop_line}"
        )

    async def notify_exit(self, symbol: str, pnl_usd: float) -> None:
        sign = "+" if pnl_usd >= 0 else ""
        await self.send(
            f"[EXIT] <b>{symbol}</b>\n"
            f"PnL realizzato: {sign}${pnl_usd:,.2f}"
        )

    async def notify_daily_summary(
        self,
        pnl_usd: float,
        trades: int,
        session_date: date | None = None,
    ) -> None:
        sign = "+" if pnl_usd >= 0 else ""
        date_str = session_date.isoformat() if session_date else "oggi"
        await self.send(
            f"[DAILY] Riepilogo {date_str}\n"
            f"PnL: {sign}${pnl_usd:,.2f} | Trade: {trades}"
        )

    async def notify_risk_alert(self, message: str) -> None:
        await self.send(f"[RISK] {message}")

    async def notify_bot_started(self, mode: str = "paper") -> None:
        await self.send(
            f"[OK] Bot avviato\n"
            f"Modalita: <code>{mode}</code>"
        )

    async def notify_bot_stopped(self) -> None:
        await self.send("[STOP] Bot fermato")


# ─── FACTORY ─────────────────────────────────────────────────────────────────


def build_notifier() -> TelegramNotifier:
    """Costruisce TelegramNotifier leggendo settings. Se non configurato, è no-op."""
    from trading.config import settings

    return TelegramNotifier(
        token=settings.telegram_bot_token,
        chat_id=settings.telegram_chat_id,
    )
