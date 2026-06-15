---
generated-from-commit: 8a47d3039a88d6258bc44197ff3ea5189dd0f5b9
generated-from-branch: main
generated-date: 2026-06-15
covers-paths:
  - src/trading/strategy/**
  - src/trading/risk/**
  - src/trading/broker/**
  - src/trading/db/**
last-verified-commit: 8a47d3039a88d6258bc44197ff3ea5189dd0f5b9
---

# Design e sicurezza applicativa

## Paradigmi di software design

### Architettura a livelli con gate obbligatorio

Il flusso di ogni bar segue un percorso unidirezionale:

```
MarketDataManager (5s bars → aggregati 5min)
    ↓
IUniverseFilter      — filtra simboli (dividend-free, liquidità, exchange)
    ↓
ISignalGenerator     — genera RawSignal (direction, strength, reason)
    ↓
IPositionSizer       — calcola USD da impegnare
    ↓
RiskManager.validate — GATE OBBLIGATORIO — può bloccare o modificare
    ↓
IPortfolioAllocator  — gestisce segnali multipli simultanei
    ↓
IExecutionAlgo       — traduce in ordini IBKR (LimitOrder + GTC StopOrder)
```

`IExitLogic` gira in parallelo via `_exit_check_loop` ogni 30 secondi sulle posizioni aperte.
Ogni ordine, senza eccezioni, passa per `RiskManager.validate` prima di essere inviato.

### Pattern dei 6 interfacce (composizione > eredità)

Ogni strategia è composta da 6 interfacce ABC indipendenti. Questo permette di swappare
qualsiasi componente senza toccare gli altri: si può cambiare il position sizing senza
modificare la logica del segnale. Il `StrategyComposer` è solo il collante — nessuna logica
di trading al suo interno. Il `StrategyRegistry` gestisce più strategie in parallelo con
allocazione percentuale del capitale.

### Repository pattern sul database

`src/trading/db/repository.py` è l'unico punto di accesso al DB. Nessun altro modulo esegue
query SQL direttamente. `save_trade()` è idempotente sull'`ibkr_exec_id` IBKR (chiave
globalmente univoca per ogni fill) — questo gestisce i partial fill e i retry senza duplicati.

### Universo azionario curato (no transaction tax)

La selezione degli strumenti è vincolata dalla fiscalità italiana (regime dichiarativo):

- US (NYSE/NASDAQ): `Stock(symbol, "SMART", "USD")` — nessuna transaction tax locale
- EU XETRA (Germania): `Stock(symbol, "IBIS", "EUR")` — nessuna transaction tax
- EU Euronext Amsterdam: `Stock(symbol, "AEB", "EUR")` — nessuna transaction tax
- DA EVITARE: Borsa Italiana BVME/MTAA (Tobin Tax 0,2%) e Euronext Paris SBF/EPA (TTF ~0,3%)
- Regola aggiuntiva: zero dividendi, solo azioni growth — nessuna ritenuta alla fonte

`get_contract()` in `ma_crossover.py` gestisce la mappatura exchange/valuta corretta per ogni
simbolo. `YAHOO_MAP` in `market_data.py` gestisce la conversione ticker IBKR → Yahoo Finance
per il warmup (es. `SAP` → `SAP.DE`, `ASML` → `ASML.AS`).

## Sicurezza applicativa

### Vincoli non negoziabili sugli ordini

1. Nessun Market Order — sempre `LimitOrder` con prezzo aggressivo (last ±0.1%). Il market
   order su titoli a bassa liquidità può causare slippage del 0.5% che uccide la profittabilità.
2. GTC Stop Loss obbligatorio su ogni BUY — piazzato immediatamente dopo il fill via `StopOrder`
   con `tif="GTC"`. Gli ordini GTC sopravvivono al restart di IB Gateway e al riavvio del bot.
3. `useRTH=True` sempre su `reqHistoricalData` e ordini — no pre/after-market.
4. `nextValidId` gestito da ib_async internamente — non riusare mai lo stesso `orderId`.

### Gestione credenziali

Nessuna credenziale nel codice. Nessun file `.env` committato in git (escluso da `.gitignore`).
In sviluppo locale: file `.env` nella radice del progetto (non committato).
In produzione: `/etc/trading/credentials.env` con permessi `600` e owner `trader` (utente
non-root dedicato), caricato via `EnvironmentFile` nel service systemd.

### Rete e isolamento

IB Gateway espone le porte 4001/4002 solo su `127.0.0.1` — mai su `0.0.0.0`.
In Docker: il bot si connette al servizio via nome Docker (`IBKR_HOST: ib-gateway`), non via
`127.0.0.1` (che punta al container stesso, non al container gateway).
Firewall (ufw): solo SSH (22) e health check (:8080 da IP noto). PostgreSQL e IB Gateway
solo su localhost.

### Pacing IBKR (errore 162 = pacing violation)

`reqHistoricalData` ha limite 60 richieste in 10 minuti, minimo 10 secondi tra richieste
consecutive per lo stesso contratto. Soluzione: usare `yfinance` per il warmup storico
all'apertura del mercato (nessun limite di frequenza), e IBKR solo per i dati real-time.
`MarketDataManager._enforce_pacing()` gestisce il throttling automatico per le richieste IBKR.

### IB Gateway restart giornaliero 23:45 ET

Il bot gestisce la disconnessione via `ib.disconnectedEvent += _handle_disconnect`, non via
cron. Il restart dura ~3-5 minuti; il bot riprova con intervalli esponenziali
[30, 60, 60, 120, 120, 300]. Le posizioni non sono a rischio: i GTC stop orders sono sui
server IBKR e sopravvivono alla disconnessione. Dopo la riconnessione, `post_reconnect_sync()`
risincronizza posizioni e ordini aperti.

### Circuit Breaker

`CircuitBreaker.check()` ferma il bot, cancella tutti gli ordini e chiude tutte le posizioni
se: perdita giornaliera > 5% del portafoglio, oppure IB Gateway non risponde al ping.
È un layer di sicurezza aggiuntivo rispetto al `RiskManager` (che opera per singolo trade).

## Diagrammi

| Diagramma | Sorgente | Componenti rappresentati |
|---|---|---|
| (da creare) | architecture.mmd | flusso completo dal bar al fill |
