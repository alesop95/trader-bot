"""
Mostra le posizioni aperte e i valori di conto correnti da IB Gateway.

    uv run python scripts/check_positions.py
"""

import asyncio

from ib_async import IB
from loguru import logger

from trading.config import settings

_ACCOUNT_TAGS = frozenset({"NetLiquidation", "TotalCashValue", "DailyPnL", "UnrealizedPnL"})


async def check() -> None:
    ib = IB()
    await ib.connectAsync(
        host=settings.ibkr_host,
        port=settings.ibkr_port,
        clientId=92,
        readonly=True,
    )

    # ── Posizioni ──────────────────────────────────────────────────────────────
    portfolio = ib.portfolio()
    open_items = sorted(
        [item for item in portfolio if item.position != 0],
        key=lambda x: x.contract.symbol,
    )

    print(f"\n── Posizioni aperte ({len(open_items)}) ──")
    if not open_items:
        print("  (nessuna)")
    else:
        col = f"{'Symbol':<10} {'Exch':<6} {'Qty':>8} {'MktValue':>12} {'AvgCost':>10} {'PnL':>10}"
        print(col)
        print("─" * len(col))
        for item in open_items:
            c = item.contract
            print(
                f"{c.symbol:<10}"
                f"{c.exchange:<6}"
                f"{int(item.position):>8}"
                f"{item.marketValue:>12.2f}"
                f"{item.averageCost:>10.4f}"
                f"{item.unrealizedPNL:>10.2f}"
            )

    # ── Valori di conto ────────────────────────────────────────────────────────
    print("\n── Account values ──")
    account_values = {
        av.tag: float(av.value)
        for av in ib.accountValues()
        if av.tag in _ACCOUNT_TAGS and av.currency == "USD"
    }
    for tag in ("NetLiquidation", "TotalCashValue", "UnrealizedPnL", "DailyPnL"):
        value = account_values.get(tag)
        if value is not None:
            sign = "+" if value >= 0 else ""
            print(f"  {tag:<25} {sign}{value:>12.2f} USD")

    # ── Ordini aperti ──────────────────────────────────────────────────────────
    open_trades = ib.openTrades()
    if open_trades:
        print(f"\n── Ordini aperti ({len(open_trades)}) ──")
        for trade in open_trades:
            o = trade.order
            s = trade.orderStatus
            print(
                f"  orderId={o.orderId:<8} {trade.contract.symbol:<8}"
                f" {o.action} {o.totalQuantity} @ {o.lmtPrice or 'MARKET'}"
                f"  stato={s.status}"
            )

    ib.disconnect()
    logger.info("check_positions completato")


if __name__ == "__main__":
    asyncio.run(check())
