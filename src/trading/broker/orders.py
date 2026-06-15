from ib_async import IB, LimitOrder, Order, Stock, StopOrder, Trade
from loguru import logger

from trading.broker.client import IBClient

# Universo azionario supportato: symbol → (exchange, currency)
# Regola: nessun titolo con transaction tax locale
#   IT BVME/MTAA → Tobin Tax 0,2%   → ESCLUSI
#   FR SBF/EPA   → TTF ~0,3%        → ESCLUSI
UNIVERSE: dict[str, tuple[str, str]] = {
    # US NYSE/NASDAQ — SMART routing, settlement USD
    "NVDA": ("SMART", "USD"),
    "META": ("SMART", "USD"),
    "GOOGL": ("SMART", "USD"),
    "AMZN": ("SMART", "USD"),
    "TSLA": ("SMART", "USD"),
    "AMD": ("SMART", "USD"),
    "CRM": ("SMART", "USD"),
    "SNOW": ("SMART", "USD"),
    "PLTR": ("SMART", "USD"),
    "NET": ("SMART", "USD"),
    "DDOG": ("SMART", "USD"),
    "MDB": ("SMART", "USD"),
    "CRWD": ("SMART", "USD"),
    "PANW": ("SMART", "USD"),
    "COIN": ("SMART", "USD"),
    # EU XETRA (Germania) — nessuna transaction tax
    "SAP": ("IBIS", "EUR"),
    "IFX": ("IBIS", "EUR"),
    "AIXA": ("IBIS", "EUR"),
    "SRT3": ("IBIS", "EUR"),
    # EU Euronext Amsterdam — nessuna transaction tax
    "ASML": ("AEB", "EUR"),
    "ADYEN": ("AEB", "EUR"),
    "BESI": ("AEB", "EUR"),
}


# ─── FACTORY FUNCTIONS (pure, testabili senza IBKR) ──────────────────────────


def get_contract(symbol: str) -> Stock:
    """
    Ritorna il contratto IBKR corretto per il simbolo.
    Solleva ValueError se il simbolo non è nell'universo supportato.
    """
    if symbol not in UNIVERSE:
        raise ValueError(
            f"Simbolo '{symbol}' non nell'universo supportato. "
            f"Aggiungerlo a UNIVERSE in broker/orders.py."
        )
    exchange, currency = UNIVERSE[symbol]
    return Stock(symbol, exchange, currency)


def make_limit_order(
    action: str,
    quantity: int,
    limit_price: float,
    tif: str = "DAY",
) -> LimitOrder:
    """
    Crea un LimitOrder. outsideRth=False garantisce no pre/after-market.
    tif="DAY" per ordini intraday; tif="GTC" per ordini che devono sopravvivere
    al restart di IB Gateway (usato raramente — preferire GTC solo per stop loss).
    """
    order = LimitOrder(action, quantity, round(limit_price, 4))
    order.tif = tif
    order.outsideRth = False
    return order


def make_stop_order(action: str, quantity: int, stop_price: float) -> Order:
    """
    Crea uno StopOrder GTC. tif="GTC" obbligatorio: l'ordine deve sopravvivere
    al restart giornaliero di IB Gateway (23:45 ET) e proteggere la posizione
    anche quando il bot è disconnesso.
    """
    order = StopOrder(action, quantity, round(stop_price, 4))
    order.tif = "GTC"
    order.outsideRth = False
    return order


# ─── ORDER MANAGER ────────────────────────────────────────────────────────────


class OrderManager:
    """
    Invia ordini a IBKR tramite ib_async.IB. Non contiene logica di sizing
    o timing: riceve prezzi e quantità già calcolati dalla execution algo.

    ib_async.placeOrder() è sincrono (restituisce Trade subito); il fill
    arriva in modo asincrono via IBClient.execDetailsEvent.
    """

    def __init__(self, ib_client: IBClient) -> None:
        self._ib: IB = ib_client.ib

    def place_limit_order(
        self,
        symbol: str,
        action: str,
        quantity: int,
        limit_price: float,
        tif: str = "DAY",
    ) -> Trade:
        """Piazza un limit order. Registrare sempre un GTC stop subito dopo il fill."""
        contract = get_contract(symbol)
        order = make_limit_order(action, quantity, limit_price, tif)
        trade = self._ib.placeOrder(contract, order)
        logger.info(
            "LIMIT {} {} {} @ {:.4f} tif={}",
            action, quantity, symbol, limit_price, tif,
        )
        return trade

    def place_stop_order(
        self,
        symbol: str,
        action: str,
        quantity: int,
        stop_price: float,
    ) -> Trade:
        """
        Piazza un GTC stop loss. Da chiamare immediatamente dopo il fill del BUY,
        passando la quantità effettivamente riempita (non quella richiesta).
        """
        contract = get_contract(symbol)
        order = make_stop_order(action, quantity, stop_price)
        trade = self._ib.placeOrder(contract, order)
        logger.info(
            "STOP {} {} {} @ {:.4f} GTC",
            action, quantity, symbol, stop_price,
        )
        return trade

    def cancel_order(self, trade: Trade) -> None:
        self._ib.cancelOrder(trade.order)
        logger.info(
            "Ordine cancellato: {} {} {}",
            trade.order.action,
            trade.order.totalQuantity,
            trade.contract.symbol,
        )

    def cancel_all_open_orders(self) -> int:
        """
        Cancella tutti gli ordini aperti (inclusi GTC stop loss).
        Usare solo in emergency flatten — normalmente i GTC stop non vanno toccati.
        Ritorna il numero di ordini cancellati.
        """
        open_trades = self._ib.openTrades()
        for t in open_trades:
            self._ib.cancelOrder(t.order)
        if open_trades:
            logger.warning(
                "Emergency: {} ordini aperti cancellati", len(open_trades)
            )
        return len(open_trades)
