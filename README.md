# trader-bot

Bot di trading algoritmico per Interactive Brokers, costruito su `ib-async` con un pattern di
strategia a sei interfacce (filtro dell'universo, generatore di segnali, dimensionamento delle
posizioni, allocatore di portafoglio, algoritmo di esecuzione, logica di uscita) assemblate da un
composer centrale. Una nuova strategia deve implementare solo i ruoli che le servono, il resto lo
fornisce l'infrastruttura comune: scheduling delle sessioni, gestione del rischio, notifiche,
persistenza e osservabilita'. Non e' uno script di prova: e' pensato e strutturato come un pezzo
di infrastruttura di trading vero, con dependency injection reale e un confine netto tra codice di
produzione e strumenti di sviluppo.

## Architettura della strategia

Il modulo `src/trading/strategy/interfaces.py` definisce le sei interfacce astratte (`IUniverseFilter`,
`ISignalGenerator`, `IPositionSizer`, `IPortfolioAllocator`, `IExecutionAlgo`, `IExitLogic`) e i
dataclass che viaggiano tra loro (`RawSignal`, poi arricchito in `AllocatedSignal` con il sizing).
Il `StrategyComposer` in `strategy/composer.py` assembla le implementazioni concrete in una
pipeline unica, con un `RiskValidator` che intercetta i segnali prima dell'invio agli ordini.

## Strategia attiva

L'unica strategia attualmente collegata, in `strategy/implementations/ma_crossover.py`, opera su
un incrocio rialzista EMA9/EMA21 confermato da RSI e istogramma MACD. Dimensiona ogni posizione
come frazione fissa del capitale assegnato alla strategia, esclude i simboli che vanno ex-dividendo
entro una finestra configurabile (per non subire lo sconto sistematico di prezzo del giorno
ex-div), esegue con ordini limit leggermente aggressivi ed esce sia su incrocio ribassista sia al
superamento di una soglia di drawdown dal picco di sessione della posizione.

## Rischio e affidabilita'

Attorno al nucleo di strategia operano un circuit breaker e un risk manager (`src/trading/risk/`),
pensati per bloccare l'operativita' in condizioni anomale prima che producano danno. Un job
schedulato con APScheduler (`scheduler/jobs.py`) gestisce finestre di sessione separate per i
mercati EU e US.

## Infrastruttura

Il bot notifica via Telegram (`notifications/telegram.py`), espone metriche Prometheus e un
endpoint di health-check (`monitoring/healthcheck.py`), e persiste lo stato su PostgreSQL tramite
SQLAlchemy asincrono con migrazioni Alembic (`db/`). Il `docker-compose.yml` orchestra bot,
IB Gateway, Postgres, Prometheus e Grafana come servizi separati.

## Stack tecnico

Python 3.12, `ib-async` per il collegamento a Interactive Brokers, SQLAlchemy 2 + Alembic +
asyncpg per la persistenza, APScheduler 3.x (la 4.x ha un'API incompatibile, e' pinnata sotto la
`4.0`), `pandas-ta-classic` per gli indicatori tecnici, `python-telegram-bot` per le notifiche,
FastAPI/uvicorn per l'health-check, `prometheus-client` per le metriche. Il backtesting con
`vectorbt` e' una dipendenza di solo sviluppo, tenuta fuori dal container di produzione.

## Stato del progetto

Nel codice non sono presenti credenziali ne' dati di account: la configurazione sensibile passa
per variabili d'ambiente (`.env`, vedi `.env.example`). Quanto descritto qui copre l'architettura
di sistema e la logica della strategia attiva, non risultati di trading dal vivo, che non sono
contenuti in questo repository.
