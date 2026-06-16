"""
Esporta i trade dell'anno fiscale in CSV per la rendicontazione.
I dati vengono letti dal database locale (tabella trades).

    uv run python scripts/export_tax_report.py                  # anno corrente
    uv run python scripts/export_tax_report.py --year 2025      # anno specifico
    uv run python scripts/export_tax_report.py --out custom.csv

Colonne nel CSV:
  fill_time, symbol, exchange, currency, direction, quantity,
  fill_price, fill_price_eur, commission, pnl_usd, eur_usd_rate,
  strategy_name, ibkr_exec_id

fill_price_eur è calcolato come fill_price / eur_usd_rate quando
currency == 'USD' ed eur_usd_rate è presente; altrimenti uguale a fill_price.
Utile per il quadro RT della dichiarazione dei redditi italiana.
"""

import argparse
import asyncio
import csv
from datetime import UTC, datetime
from decimal import Decimal

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from trading.config import settings
from trading.db.models import Trade


async def export(year: int, out_path: str) -> None:
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    start = datetime(year, 1, 1, tzinfo=UTC)
    end = datetime(year + 1, 1, 1, tzinfo=UTC)

    async with session_factory() as session:
        result = await session.execute(
            select(Trade)
            .where(Trade.fill_time >= start, Trade.fill_time < end)
            .order_by(Trade.fill_time)
        )
        trades = result.scalars().all()

    await engine.dispose()

    if not trades:
        logger.warning("Nessun trade nel database per l'anno {}", year)
        return

    fieldnames = [
        "fill_time", "symbol", "exchange", "currency",
        "direction", "quantity", "fill_price", "fill_price_eur",
        "commission", "pnl_usd", "eur_usd_rate",
        "strategy_name", "ibkr_exec_id",
    ]

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for t in trades:
            fill_price_eur = _to_eur(t.fill_price, t.currency, t.eur_usd_rate)
            writer.writerow({
                "fill_time": t.fill_time.isoformat(),
                "symbol": t.symbol,
                "exchange": t.exchange,
                "currency": t.currency,
                "direction": t.direction,
                "quantity": t.quantity,
                "fill_price": _fmt(t.fill_price),
                "fill_price_eur": _fmt(fill_price_eur),
                "commission": _fmt(t.commission),
                "pnl_usd": _fmt(t.pnl_usd) if t.pnl_usd is not None else "",
                "eur_usd_rate": _fmt(t.eur_usd_rate) if t.eur_usd_rate is not None else "",
                "strategy_name": t.strategy_name,
                "ibkr_exec_id": t.ibkr_exec_id,
            })

    logger.info("{} trade esportati → {}", len(trades), out_path)

    # Riepilogo
    buys = sum(1 for t in trades if t.direction == "BUY")
    sells = sum(1 for t in trades if t.direction == "SELL")
    realized = sum(t.pnl_usd or Decimal("0") for t in trades)
    print(f"\nAnno {year}: {len(trades)} trade ({buys} BUY, {sells} SELL)")
    print(f"PnL realizzato totale: {realized:+.2f} USD")
    print(f"File: {out_path}")


def _to_eur(
    price: Decimal,
    currency: str,
    eur_usd_rate: Decimal | None,
) -> Decimal:
    if currency == "USD" and eur_usd_rate and eur_usd_rate > 0:
        return (price / eur_usd_rate).quantize(Decimal("0.0001"))
    return price


def _fmt(value: Decimal | None) -> str:
    return str(value) if value is not None else ""


def main() -> None:
    parser = argparse.ArgumentParser(description="Esporta trade per rendicontazione fiscale")
    parser.add_argument(
        "--year",
        type=int,
        default=datetime.now().year,
        help="Anno fiscale (default: anno corrente)",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Percorso file CSV di output (default: trades_<anno>.csv)",
    )
    args = parser.parse_args()
    out = args.out or f"trades_{args.year}.csv"
    asyncio.run(export(year=args.year, out_path=out))


if __name__ == "__main__":
    main()
