from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Index, Integer, Numeric, String, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Trade(Base):
    """Singolo fill ricevuto da IBKR. Immutabile dopo la creazione."""

    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Chiave di idempotenza — ogni execId IBKR è globalmente univoco per fill
    ibkr_exec_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    exchange: Mapped[str] = mapped_column(String(20), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    direction: Mapped[str] = mapped_column(String(5), nullable=False)   # LONG | SHORT
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    fill_price: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    commission: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False, server_default="0")
    fill_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    order_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    strategy_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # Tasso EUR/USD al momento del fill — per il calcolo del P&L in EUR (dichiarazione IT)
    eur_usd_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    pnl_usd: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    __table_args__ = (
        Index("ix_trades_symbol", "symbol"),
        Index("ix_trades_fill_time", "fill_time"),
    )


class Position(Base):
    """Posizione corrente per simbolo. Aggiornata a ogni fill; quantity=0 = chiusa."""

    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    exchange: Mapped[str] = mapped_column(String(20), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    avg_cost: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, server_default="0")
    current_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    unrealized_pnl: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    realized_pnl: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), nullable=False, server_default="0"
    )
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )


class Signal(Base):
    """Log di ogni segnale generato, agito o no."""

    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    direction: Mapped[str] = mapped_column(String(5), nullable=False)
    strength: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    strategy_name: Mapped[str] = mapped_column(String(100), nullable=False)
    stop_loss_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    take_profit_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    acted_upon: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    __table_args__ = (Index("ix_signals_symbol_time", "symbol", "generated_at"),)


class DailyPnL(Base):
    """Aggregazione giornaliera — una riga per giorno di trading."""

    __tablename__ = "daily_pnl"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    realized_pnl: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), nullable=False, server_default="0"
    )
    unrealized_pnl: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), nullable=False, server_default="0"
    )
    num_trades: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    num_winning_trades: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    max_drawdown_pct: Mapped[Decimal | None] = mapped_column(Numeric(7, 4), nullable=True)
    portfolio_value: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
