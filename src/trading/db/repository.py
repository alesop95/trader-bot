from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from trading.config import settings
from trading.db.models import DailyPnL, Position, Signal, Trade

engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
SessionFactory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine, expire_on_commit=False
)


@asynccontextmanager
async def get_repository() -> AsyncGenerator["Repository", None]:
    """Context manager per ottenere un Repository con sessione e transazione gestiti."""
    async with SessionFactory() as session:
        async with session.begin():
            yield Repository(session)


class Repository:
    """
    Unico punto di accesso al database. Nessun altro modulo esegue query SQL direttamente.
    Ogni istanza vive per una singola transazione (via get_repository()).
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ─── TRADES ───────────────────────────────────────────────────────────────

    async def save_trade(
        self,
        *,
        ibkr_exec_id: str,
        symbol: str,
        exchange: str,
        currency: str,
        direction: str,
        quantity: int,
        fill_price: Decimal,
        commission: Decimal,
        fill_time: datetime,
        strategy_name: str,
        order_id: int | None = None,
        eur_usd_rate: Decimal | None = None,
        pnl_usd: Decimal | None = None,
    ) -> Trade | None:
        """
        Inserisce un fill. Idempotente: se ibkr_exec_id esiste già, non fa nulla e ritorna None.
        Questo gestisce partial fill e retry senza duplicati.
        """
        stmt = (
            insert(Trade)
            .values(
                ibkr_exec_id=ibkr_exec_id,
                symbol=symbol,
                exchange=exchange,
                currency=currency,
                direction=direction,
                quantity=quantity,
                fill_price=fill_price,
                commission=commission,
                fill_time=fill_time,
                strategy_name=strategy_name,
                order_id=order_id,
                eur_usd_rate=eur_usd_rate,
                pnl_usd=pnl_usd,
            )
            .on_conflict_do_nothing(index_elements=["ibkr_exec_id"])
            .returning(Trade)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_trades(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[Trade]:
        stmt = select(Trade).order_by(Trade.fill_time)
        if start_date:
            stmt = stmt.where(Trade.fill_time >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            stmt = stmt.where(Trade.fill_time <= datetime.combine(end_date, datetime.max.time()))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ─── POSITIONS ────────────────────────────────────────────────────────────

    async def get_open_positions(self) -> list[Position]:
        """Ritorna le posizioni con quantity != 0."""
        result = await self.session.execute(
            select(Position).where(Position.quantity != 0)
        )
        return list(result.scalars().all())

    async def get_position(self, symbol: str) -> Position | None:
        result = await self.session.execute(
            select(Position).where(Position.symbol == symbol)
        )
        return result.scalar_one_or_none()

    async def upsert_position(
        self,
        *,
        symbol: str,
        exchange: str,
        currency: str,
        quantity: int,
        avg_cost: Decimal,
        current_price: Decimal | None = None,
        unrealized_pnl: Decimal | None = None,
        realized_pnl: Decimal | None = None,
        opened_at: datetime | None = None,
    ) -> None:
        """Crea o aggiorna la posizione per simbolo. updated_at viene impostato dal DB."""
        now = datetime.utcnow()
        stmt = (
            insert(Position)
            .values(
                symbol=symbol,
                exchange=exchange,
                currency=currency,
                quantity=quantity,
                avg_cost=avg_cost,
                current_price=current_price,
                unrealized_pnl=unrealized_pnl,
                realized_pnl=realized_pnl or Decimal("0"),
                opened_at=opened_at,
                updated_at=now,
            )
            .on_conflict_do_update(
                index_elements=["symbol"],
                set_=dict(
                    quantity=quantity,
                    avg_cost=avg_cost,
                    current_price=current_price,
                    unrealized_pnl=unrealized_pnl,
                    realized_pnl=realized_pnl or Decimal("0"),
                    updated_at=now,
                ),
            )
        )
        await self.session.execute(stmt)

    # ─── SIGNALS ──────────────────────────────────────────────────────────────

    async def save_signal(
        self,
        *,
        symbol: str,
        direction: str,
        strength: float,
        reason: str,
        strategy_name: str,
        generated_at: datetime,
        stop_loss_pct: float | None = None,
        take_profit_pct: float | None = None,
    ) -> Signal:
        signal = Signal(
            symbol=symbol,
            direction=direction,
            strength=Decimal(str(strength)),
            reason=reason,
            strategy_name=strategy_name,
            generated_at=generated_at,
            stop_loss_pct=Decimal(str(stop_loss_pct)) if stop_loss_pct else None,
            take_profit_pct=Decimal(str(take_profit_pct)) if take_profit_pct else None,
        )
        self.session.add(signal)
        await self.session.flush()
        return signal

    async def mark_signal_acted_upon(self, signal_id: int) -> None:
        await self.session.execute(
            update(Signal).where(Signal.id == signal_id).values(acted_upon=True)
        )

    # ─── DAILY P&L ────────────────────────────────────────────────────────────

    async def get_or_create_daily_pnl(self, trading_date: date) -> DailyPnL:
        result = await self.session.execute(
            select(DailyPnL).where(DailyPnL.date == trading_date)
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = DailyPnL(date=trading_date)
            self.session.add(row)
            await self.session.flush()
        return row

    async def update_daily_pnl(
        self,
        trading_date: date,
        *,
        realized_pnl: Decimal | None = None,
        unrealized_pnl: Decimal | None = None,
        num_trades: int | None = None,
        num_winning_trades: int | None = None,
        max_drawdown_pct: Decimal | None = None,
        portfolio_value: Decimal | None = None,
    ) -> None:
        now = datetime.utcnow()
        values: dict = {"updated_at": now}
        if realized_pnl is not None:
            values["realized_pnl"] = realized_pnl
        if unrealized_pnl is not None:
            values["unrealized_pnl"] = unrealized_pnl
        if num_trades is not None:
            values["num_trades"] = num_trades
        if num_winning_trades is not None:
            values["num_winning_trades"] = num_winning_trades
        if max_drawdown_pct is not None:
            values["max_drawdown_pct"] = max_drawdown_pct
        if portfolio_value is not None:
            values["portfolio_value"] = portfolio_value

        await self.session.execute(
            update(DailyPnL).where(DailyPnL.date == trading_date).values(**values)
        )

    async def get_realized_pnl_today(self, trading_date: date) -> Decimal:
        result = await self.session.execute(
            select(DailyPnL.realized_pnl).where(DailyPnL.date == trading_date)
        )
        value = result.scalar_one_or_none()
        return value if value is not None else Decimal("0")
