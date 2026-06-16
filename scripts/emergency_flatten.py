"""
Chiude tutte le posizioni aperte con ordini MARKET immediati.
Bypassa la strategia e il risk management: usare solo in emergenza.

    uv run python scripts/emergency_flatten.py           # dry-run (stampa senza agire)
    uv run python scripts/emergency_flatten.py --live    # esecuzione reale

Il clientId 91 è riservato agli script di manutenzione e non entra in conflitto
con il bot principale (che usa settings.ibkr_client_id, default 1).
"""

import argparse
import asyncio
import sys

from ib_async import IB, MarketOrder
from loguru import logger

from trading.config import settings


async def flatten(*, live: bool) -> None:
    ib = IB()
    await ib.connectAsync(
        host=settings.ibkr_host,
        port=settings.ibkr_port,
        clientId=91,
        readonly=not live,
    )

    portfolio = ib.portfolio()
    open_items = [(item.contract, int(item.position)) for item in portfolio if item.position != 0]

    if not open_items:
        logger.info("Nessuna posizione aperta da chiudere.")
        ib.disconnect()
        return

    logger.info("Posizioni aperte trovate: {}", len(open_items))

    for contract, qty in open_items:
        action = "SELL" if qty > 0 else "BUY"
        shares = abs(qty)

        if live:
            order = MarketOrder(action, shares)
            trade = ib.placeOrder(contract, order)
            logger.warning(
                "ORDINE PIAZZATO: {} {} {} @ MARKET (orderId={})",
                action, shares, contract.symbol, trade.order.orderId,
            )
        else:
            logger.info("DRY-RUN: {} {} {} @ MARKET", action, shares, contract.symbol)

    if live:
        await asyncio.sleep(2)
        done = {"Filled", "Cancelled"}
        still_open = [t for t in ib.openTrades() if t.orderStatus.status not in done]
        if still_open:
            logger.warning("{} ordini ancora non completati dopo 2s", len(still_open))
        else:
            logger.info("Tutti gli ordini di chiusura accettati da IBKR")

    ib.disconnect()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Emergency flatten: chiude tutte le posizioni aperte"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Esegue gli ordini su mercato reale (senza questo flag: dry-run)",
    )
    args = parser.parse_args()

    if args.live:
        print(
            "\nATTENZIONE: modalità LIVE attiva.\n"
            f"  Host: {settings.ibkr_host}:{settings.ibkr_port}\n"
            f"  Modalità: {settings.trading_mode}\n"
            "Tutti gli ordini MARKET verranno inviati immediatamente a IBKR.\n"
        )
        confirm = input("Digitare 'SI' per confermare: ").strip().upper()
        if confirm != "SI":
            print("Operazione annullata.")
            sys.exit(0)

    asyncio.run(flatten(live=args.live))


if __name__ == "__main__":
    main()
