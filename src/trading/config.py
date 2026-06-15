from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ─── IBKR ─────────────────────────────────────────────────────────────────
    ibkr_username: str
    ibkr_password: str
    trading_mode: Literal["paper", "live"] = "paper"
    ibkr_host: str = "127.0.0.1"
    ibkr_port: int = 4001
    ibkr_client_id: int = 1
    ibkr_account: str

    # ─── DATABASE ─────────────────────────────────────────────────────────────
    database_url: str
    postgres_password: str = ""

    # ─── TELEGRAM ─────────────────────────────────────────────────────────────
    # Vuoti = notifiche disabilitate; il bot avvia lo stesso
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # ─── TAX REPORTING ────────────────────────────────────────────────────────
    ibkr_flex_token: str = ""
    ibkr_flex_query_id: str = ""

    # ─── RISK LIMITS ──────────────────────────────────────────────────────────
    max_position_size_usd: float = 10_000.0
    max_daily_loss_usd: float = 500.0
    max_open_positions: int = 5
    default_stop_loss_pct: float = 0.02

    # ─── MONITORING ───────────────────────────────────────────────────────────
    vnc_password: str = ""
    grafana_password: str = "admin"

    # ─── VALIDATORS ───────────────────────────────────────────────────────────

    @field_validator("ibkr_port")
    @classmethod
    def ibkr_port_must_be_valid(cls, v: int) -> int:
        if v not in (4001, 4002):
            raise ValueError("IBKR_PORT deve essere 4001 (paper) o 4002 (live)")
        return v

    @field_validator("database_url")
    @classmethod
    def ensure_asyncpg_driver(cls, v: str) -> str:
        # SQLAlchemy 2.0 async richiede postgresql+asyncpg://
        # Accetta anche postgresql:// e lo corregge silenziosamente
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @field_validator("default_stop_loss_pct")
    @classmethod
    def stop_loss_must_be_positive(cls, v: float) -> float:
        if not 0 < v < 1:
            raise ValueError("DEFAULT_STOP_LOSS_PCT deve essere tra 0 e 1 (es. 0.02 = 2%)")
        return v

    # ─── PROPERTIES ───────────────────────────────────────────────────────────

    @property
    def is_paper(self) -> bool:
        return self.trading_mode == "paper"

    @property
    def telegram_enabled(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_chat_id)

    @property
    def flex_reporting_enabled(self) -> bool:
        return bool(self.ibkr_flex_token and self.ibkr_flex_query_id)


# Singleton — importare sempre da qui: `from trading.config import settings`
# Non reinstanziare Settings() altrove: ogni istanza rilegge os.environ.
settings = Settings()
