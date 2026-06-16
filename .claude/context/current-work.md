---
generated-from-commit: 8a47d3039a88d6258bc44197ff3ea5189dd0f5b9
generated-from-branch: main
generated-date: 2026-06-15
covers-paths:
  - src/**
  - pyproject.toml
  - docker-compose.yml
  - Dockerfile
  - .github/**
  - scripts/**
  - tests/**
last-verified-commit: 4df3cb6
stato: implementazione completata — 23/23 step ✓ — tutto committato — fase operativa
---

# Lavoro in corso

## Stato

L'implementazione dei 23 step è completata e interamente committata (HEAD = 4df3cb6).
La fase successiva è operativa: apertura account IBKR, provisioning server Oracle,
configurazione segreti GitHub Actions, paper trading due settimane, poi go-live.

## Ordine di implementazione — completato

```
Step  1: pyproject.toml — uv, Python 3.12, tutte le dipendenze (prod + dev)          ✓ 795f243
Step  2: .env.example + src/trading/config.py — Pydantic Settings                    ✓ 795f243
Step  3: src/trading/db/models.py — Trade, Position, Signal, DailyPnL                ✓ 795f243
Step  4: src/trading/db/migrations/ — Alembic setup, prima migration                 ✓ 795f243
Step  5: src/trading/db/repository.py — operazioni CRUD                              ✓ 795f243
Step  6: src/trading/broker/client.py — IBClient, reconnect, fill handler            ✓ bee393b
Step  7: src/trading/broker/market_data.py — warmup yfinance + real-time 5s→5min     ✓ bee393b
Step  8: src/trading/broker/orders.py — get_contract() EU/US, Limit + GTC Stop       ✓ bee393b
Step  9: src/trading/features/pipeline.py — pandas-ta-classic, 15 colonne            ✓ bee393b
Step 10: src/trading/strategy/interfaces.py — 6 ABC + Direction + RawSignal          ✓ bee393b
Step 11: src/trading/strategy/composer.py + registry.py                              ✓ bee393b
Step 12: src/trading/strategy/implementations/ma_crossover.py                        ✓ bee393b
Step 13: src/trading/risk/manager.py + circuit_breaker.py                            ✓ bee393b
Step 14: src/trading/scheduler/jobs.py — dual session EU CET + US ET                 ✓ bee393b
Step 15: src/trading/notifications/telegram.py                                       ✓ bee393b
Step 16: src/trading/monitoring/healthcheck.py — FastAPI :8080/health + /metrics     ✓ bee393b
Step 17: src/trading/reporting/flex_query.py — IBKR Flex Web Service                 ✓ bee393b
Step 18: src/trading/main.py — TradingBot, integrazione completa                     ✓ 4df3cb6
Step 19: docker-compose.yml + monitoring/ — stack completo con Grafana               ✓ 4df3cb6
Step 20: Dockerfile + .dockerignore — build uv-based, utente non-root                ✓ 4df3cb6
Step 21: .github/workflows/deploy.yml — ruff + pytest gate, SSH deploy               ✓ 4df3cb6
Step 22: tests/unit/ — 40 test unitari, conftest.py                                  ✓ 4df3cb6
Step 23: scripts/ — emergency_flatten, check_positions, export_tax_report            ✓ 4df3cb6
```

## Fase operativa — checklist completa

Questa sezione traccia tutto ciò che rimane da fare fuori dal codice per portare
il bot in produzione. Va letta dall'alto verso il basso: ogni blocco dipende dal
precedente.

### Blocco A — Account Interactive Brokers (non ancora iniziato)

A1. Verificare se esistono promozioni attive prima di aprire l'account.
    IBKR offre periodicamente commissioni gratuite per i primi mesi e ha un
    programma referral. Vale la pena controllare la pagina promo ufficiale e
    forum come r/interactivebrokers prima di procedere.

A2. Aprire account su IBKR Europe (entità irlandese o lussemburghese per
    residenti italiani — non la controparte US).
    Tipo: Individual → Margin (necessario se in futuro si usano short o CFD;
    per long-only con il capitale attuale si può anche partire con Cash e
    convertire poi). Funding minimo effettivo: nessun requisito formale per i
    nuovi account IBKR standard dal 2024.

A3. KYC: caricare documento d'identità e prova di residenza. Tempi: 1-3 giorni
    lavorativi.

A4. Abilitare IB Gateway paper trading dal portale Account Management.
    Paper trading è separato dall'account reale; usa credenziali distinte
    che IBKR invia via email dopo l'approvazione dell'account.

A5. Sottoscrivere i dati di mercato necessari (possono essere gratuiti o a
    pagamento in base all'attività):
    - NYSE/NASDAQ Basic: gratuito per clienti con commissioni >= $10/mese,
      altrimenti $1.50/mese.
    - Euronext Amsterdam (simboli AEB): ~$4.50/mese.
    - XETRA (simboli IBIS): ~$5/mese o incluso in bundle EU.
    Nota: in paper trading i dati sono ritardati di 15 min a meno di
    sottoscrivere il feed live.

A6. Recuperare le credenziali da usare nel .env:
    - IBKR_USERNAME (paper: username + "paper" suffix, es. "U1234567paper")
    - IBKR_PASSWORD
    - IBKR_ACCOUNT (numero DU... per paper, U... per live)
    - Porta IB Gateway: 4001 (paper) o 4002 (live)

### Blocco B — Server e infrastruttura (non ancora iniziato)

B1. Provisioning server. Opzione zero-cost: Oracle Cloud Free Tier.
    - Shape: VM.Standard.A1.Flex — 4 vCPU Ampere, 24 GB RAM, 200 GB disco.
    - OS: Ubuntu 24.04 Minimal (ARM64).
    - Aprire porta 22 (SSH) nella Security List; opzionalmente 3000 (Grafana)
      solo da IP specifici.

B2. Installare Docker + Docker Compose sul server.
    ```bash
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    ```

B3. Clonare il repository.
    ```bash
    git clone git@github-personal:alesop95/trader-bot.git ~/trader-bot
    ```

B4. Creare il file .env sul server (MAI committare in git).
    Partire da .env.example e compilare tutti i campi:
    ```
    IBKR_USERNAME=...
    IBKR_PASSWORD=...
    IBKR_ACCOUNT=DU...
    IBKR_HOST=ib-gateway
    IBKR_PORT=4001
    TRADING_MODE=paper
    DATABASE_URL=postgresql+asyncpg://trader:<pw>@postgres:5432/trader
    POSTGRES_PASSWORD=<pw-casuale>
    GRAFANA_PASSWORD=<pw-casuale>
    VNC_PASSWORD=<pw-casuale>
    TELEGRAM_BOT_TOKEN=         # opzionale
    TELEGRAM_CHAT_ID=           # opzionale
    ```

B5. Primo avvio stack:
    ```bash
    cd ~/trader-bot
    docker compose up -d
    docker compose logs -f bot
    ```
    Verifica che il bot si connetta a IB Gateway (attende ~90s per l'healthcheck).

B6. Verificare /health:
    ```bash
    curl http://localhost:8080/health
    ```
    Risposta attesa: `{"status":"ok","ib_connected":true,...}`

B7. Aprire Grafana su http://<server-ip>:3000 (admin / GRAFANA_PASSWORD).
    La datasource Prometheus è già configurata via provisioning. Il primo
    dashboard va creato manualmente o importato.

### Blocco C — GitHub Actions secrets (fare prima del primo push automatico)

Nel repository GitHub: Settings → Environments → Crea environment "production"
→ Environment secrets:

    DEPLOY_HOST      IP pubblico del server Oracle
    DEPLOY_USER      utente SSH (es. "ubuntu" o "opc")
    DEPLOY_KEY       contenuto della chiave privata SSH (quella che autentica
                     la macchina di deploy verso il server — non quella IBKR)
    DEPLOY_PORT      22

Protezione consigliata: abilitare "Required reviewers" sull'environment
production — così ogni deploy richiede approvazione manuale su GitHub prima
di proseguire.

### Blocco D — Paper trading (2 settimane minimo)

D1. Verificare su Telegram che le notifiche di apertura sessione arrivino
    correttamente (EU 09:00 CET, US 15:30 CET).
D2. Osservare i segnali generati: la strategia MA Crossover richiede un
    crossover EMA9/EMA21 con RSI < 70 e MACDh > 0. In periodi laterali
    può non generare segnali per giorni.
D3. Verificare che i GTC stop loss vengano piazzati correttamente dopo
    ogni fill (check su IB Gateway TWS / Activity Statement).
D4. Eseguire check_positions.py alla fine di ogni sessione:
    ```bash
    uv run python scripts/check_positions.py
    ```
D5. Monitorare la Grafana dashboard: TRADES_TOTAL, DAILY_PNL_USD,
    CIRCUIT_BREAKER_STATE, IB_CONNECTED.
D6. Dopo 2 settimane: valutare se il paper PnL è accettabile e se la
    logica di entrata/uscita si comporta come atteso prima di passare al live.

### Blocco E — Go live (solo dopo Blocco D soddisfacente)

E1. Modificare TRADING_MODE=live nel .env sul server.
E2. Aggiornare IBKR_PORT=4002 e le credenziali live (account U...).
E3. Ricaricare lo stack: `docker compose up -d bot`
E4. Partire con un capitale ridotto (es. 10% del capitale target) per
    verificare l'esecuzione reale prima di scalare.
E5. Compilare W-8BEN su Account Management IBKR (riduce la ritenuta
    dividendi USA dal 30% al 15% — irrilevante per l'universo attuale
    senza dividendi, ma buona pratica per il futuro).

## Domande aperte

IBKR PDT rule: la Pattern Day Trader rule ($25.000 minimum equity) è stata
eliminata dalla SEC il 4 giugno 2026. Per account IBKR Ireland/Luxembourg
non era mai stata applicata ai residenti EU, ma vale la pena confermare lo
status dell'account prima del go-live.

IDA vs FX manuale: per un investitore EUR che opera su azioni USD, verificare
se conviene IDA (Integrated Data Access, conversione FX automatica a ogni
trade) o gestire manualmente il saldo USD. Il modello Trade registra già
eur_usd_rate e pnl_usd per la dichiarazione dei redditi.

Strategia alternativa: il StrategyRegistry supporta più strategie in
parallelo. Dopo aver validato MA Crossover in paper, si può aggiungere
una seconda strategia (es. mean reversion) con capital_fraction distinta.

## Riconciliazione

Ultima verifica: 2026-06-16. Tutti i 23 step committati. Commit 4df3cb6 contiene
steps 18-23 (main.py, docker-compose, Dockerfile, deploy.yml, tests/unit/, scripts/).
Il server Oracle Cloud è in attesa di provisioning (Terraform stack salvato — out of
capacity su tutti e 3 gli AD di Frankfurt, riprovare 02:00-05:00 CEST).
