"""
Pianificazione dei job di trading per le sessioni EU (XETRA) e US (NYSE/NASDAQ).
I calendari ufficiali di exchange-calendars gestiscono automaticamente DST e festivi.
"""

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

import exchange_calendars as xcals
import pandas as pd
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

# Calendari ufficiali — istanza a livello modulo, costosi da creare
_CAL_EU = xcals.get_calendar("XETR")   # XETRA Frankfurt (EU stocks)
_CAL_US = xcals.get_calendar("XNYS")   # NYSE (orari validi anche per NASDAQ)


# ─── HELPER FUNZIONI DI SESSIONE ─────────────────────────────────────────────


def is_eu_session(now: datetime | None = None) -> bool:
    """
    True se XETRA è operativo in questo momento.
    exchange-calendars tiene conto dei festivi tedeschi e dei pre/post-market.
    """
    ts = pd.Timestamp(now or datetime.now(UTC))
    return bool(_CAL_EU.is_open_on_minute(ts))


def is_us_session(now: datetime | None = None) -> bool:
    """
    True se NYSE è operativo in questo momento.
    exchange-calendars tiene conto dei festivi USA e delle half-day sessions.
    """
    ts = pd.Timestamp(now or datetime.now(UTC))
    return bool(_CAL_US.is_open_on_minute(ts))


def is_any_session_open(now: datetime | None = None) -> bool:
    """True se almeno uno dei due mercati è operativo — guard rapido per i callback."""
    t = now or datetime.now(UTC)
    return is_eu_session(t) or is_us_session(t)


# ─── SCHEDULER ────────────────────────────────────────────────────────────────


class TradingScheduler:
    """
    Wrapper su APScheduler 3.x AsyncIOScheduler.

    Job registrati da setup():
      on_bar        ogni 5 minuti (07:00-21:59 UTC, lun-ven)
      on_exit_check ogni 30 secondi (07:00-21:59 UTC, lun-ven)
      on_eu_open    09:00 CET/CEST lun-ven  — open XETRA
      on_us_open    09:30 ET/EDT lun-ven    — open NYSE/NASDAQ
      on_eu_close   17:25 CET/CEST lun-ven  — 5 min prima della chiusura XETRA
      on_us_close   15:55 ET/EDT lun-ven    — 5 min prima della chiusura NYSE

    L'intervallo 07:00-21:59 UTC copre l'apertura estiva EU (07:00 UTC = 09:00 CEST)
    e la chiusura invernale US (21:00 UTC = 16:00 EST). I callback on_bar e
    on_exit_check devono chiamare is_any_session_open() e uscire subito se falso.

    max_instances=1 e coalesce=True su on_bar e on_exit_check garantiscono che
    un'esecuzione lenta non accumuli istanze concorrenti.
    """

    def __init__(self) -> None:
        self._scheduler = AsyncIOScheduler(timezone="UTC")

    def setup(
        self,
        on_bar: Callable[[], Awaitable[None]],
        on_exit_check: Callable[[], Awaitable[None]],
        on_eu_open: Callable[[], Awaitable[None]],
        on_us_open: Callable[[], Awaitable[None]],
        on_eu_close: Callable[[], Awaitable[None]],
        on_us_close: Callable[[], Awaitable[None]],
    ) -> None:
        """Registra tutti i job. Chiamare prima di start()."""

        # Bar processing — ogni 5 minuti durante la finestra di mercato
        self._scheduler.add_job(
            on_bar,
            CronTrigger(day_of_week="mon-fri", hour="7-21", minute="*/5", timezone="UTC"),
            id="on_bar",
            max_instances=1,
            coalesce=True,
            replace_existing=True,
        )

        # Exit check — ogni 30 secondi durante la finestra di mercato
        # second='*/30' → :00 e :30 di ogni minuto; minute omesso → ogni minuto
        self._scheduler.add_job(
            on_exit_check,
            CronTrigger(day_of_week="mon-fri", hour="7-21", second="*/30", timezone="UTC"),
            id="on_exit_check",
            max_instances=1,
            coalesce=True,
            replace_existing=True,
        )

        # Session open events — timezone-aware: APScheduler gestisce DST internamente
        self._scheduler.add_job(
            on_eu_open,
            CronTrigger(
                day_of_week="mon-fri", hour=9, minute=0, timezone="Europe/Berlin"
            ),
            id="on_eu_open",
            replace_existing=True,
        )
        self._scheduler.add_job(
            on_us_open,
            CronTrigger(
                day_of_week="mon-fri", hour=9, minute=30, timezone="America/New_York"
            ),
            id="on_us_open",
            replace_existing=True,
        )

        # Session close events — 5 min prima dell'orario ufficiale
        self._scheduler.add_job(
            on_eu_close,
            CronTrigger(
                day_of_week="mon-fri", hour=17, minute=25, timezone="Europe/Berlin"
            ),
            id="on_eu_close",
            replace_existing=True,
        )
        self._scheduler.add_job(
            on_us_close,
            CronTrigger(
                day_of_week="mon-fri", hour=15, minute=55, timezone="America/New_York"
            ),
            id="on_us_close",
            replace_existing=True,
        )

        logger.info("TradingScheduler: 6 job registrati")

    def start(self) -> None:
        self._scheduler.start()
        logger.info("TradingScheduler avviato")

    def shutdown(self) -> None:
        self._scheduler.shutdown(wait=False)
        logger.info("TradingScheduler fermato")

    def next_run_times(self) -> dict[str, str]:
        """Prossima esecuzione di ogni job — esposto all'healthcheck e ai log di diagnostica."""
        result: dict[str, str] = {}
        for job in self._scheduler.get_jobs():
            nrt = job.next_run_time
            result[job.id] = nrt.isoformat() if nrt else "non pianificato"
        return result
