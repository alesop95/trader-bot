from datetime import UTC, datetime
from enum import StrEnum

from loguru import logger


class CircuitState(StrEnum):
    CLOSED = "CLOSED"        # operatività normale
    OPEN = "OPEN"            # trading bloccato
    HALF_OPEN = "HALF_OPEN"  # test di ripristino


class CircuitBreaker:
    """
    State machine che blocca il trading dopo troppi errori consecutivi.

    Transizioni:
      CLOSED   → OPEN      : dopo `failure_threshold` record_failure() consecutivi
      OPEN     → HALF_OPEN : automaticamente dopo `recovery_seconds` dall'apertura
      HALF_OPEN→ CLOSED    : su record_success() — il sistema ha superato il test
      HALF_OPEN→ OPEN      : su record_failure() — ripartenza fallita, reset timer

    is_open() restituisce True sia in OPEN sia in HALF_OPEN: nessun ordine viene
    piazzato finché il breaker non è tornato esplicitamente a CLOSED.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_seconds: float = 300.0,
    ) -> None:
        self._failure_threshold = failure_threshold
        self._recovery_seconds = recovery_seconds
        self._consecutive_failures: int = 0
        self._state: CircuitState = CircuitState.CLOSED
        self._opened_at: datetime | None = None

    @property
    def state(self) -> CircuitState:
        """Restituisce lo stato corrente, avanzando da OPEN a HALF_OPEN se il timer è scaduto."""
        if self._state == CircuitState.OPEN and self._opened_at is not None:
            elapsed = (datetime.now(UTC) - self._opened_at).total_seconds()
            if elapsed >= self._recovery_seconds:
                self._state = CircuitState.HALF_OPEN
                logger.info(
                    "CircuitBreaker: OPEN → HALF_OPEN dopo {:.0f}s", elapsed
                )
        return self._state

    def is_open(self) -> bool:
        """True se il breaker blocca nuovi ordini (OPEN o HALF_OPEN)."""
        return self.state != CircuitState.CLOSED

    def record_failure(self, reason: str = "") -> None:
        """
        Registra un errore. Se i fallimenti consecutivi raggiungono il threshold,
        o se il breaker era HALF_OPEN, porta lo stato a OPEN.
        """
        self._consecutive_failures += 1
        if (
            self._state == CircuitState.HALF_OPEN
            or self._consecutive_failures >= self._failure_threshold
        ):
            self._state = CircuitState.OPEN
            self._opened_at = datetime.now(UTC)
            self._consecutive_failures = 0
            suffix = f" — {reason}" if reason else ""
            logger.warning(
                "CircuitBreaker: → OPEN (soglia {} raggiunta{}){}",
                self._failure_threshold,
                "" if not reason else "",
                suffix,
            )

    def record_success(self) -> None:
        """
        Registra un'operazione riuscita. Chiude il breaker solo se era HALF_OPEN:
        un successo in CLOSED non azzera i fallimenti accumulati sotto threshold.
        """
        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.CLOSED
            self._consecutive_failures = 0
            self._opened_at = None
            logger.info("CircuitBreaker: HALF_OPEN → CLOSED")

    def reset(self) -> None:
        """Reset manuale a CLOSED — da usare solo in test o in emergenza operatore."""
        prev = self._state
        self._state = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._opened_at = None
        logger.warning("CircuitBreaker: reset manuale (era {})", prev)
