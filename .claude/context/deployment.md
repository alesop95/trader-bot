---
generated-from-commit: 8a47d3039a88d6258bc44197ff3ea5189dd0f5b9
generated-from-branch: main
generated-date: 2026-06-15
covers-paths:
  - docker-compose.yml
  - Dockerfile
  - .github/workflows/**
  - alembic.ini
last-verified-commit: 8a47d3039a88d6258bc44197ff3ea5189dd0f5b9
---

# Deployment

## Livelli

| Fase | TRADING_MODE | Hosting | Costo | Note |
|---|---|---|---|---|
| 0 — Sviluppo | `paper` | Oracle Cloud Always Free ARM | €0 | 4 vCPU / 24 GB RAM / Ubuntu 24.04 |
| 1 — Live piccolo | `live` | Oracle Cloud Always Free ARM | €0 + commissioni | Solo dopo 2 settimane paper OK |
| 2 — Full scale | `live` | Vultr NJ High Frequency x86 | ~$24/mese | 2 vCPU / 4 GB / NVMe — latenza <5ms a IBKR |

**Non passare alla Fase 1 prima di:** 2 settimane paper trading + backtest out-of-sample positivo
+ tutte le checklist infra e bot completate (da `trading-bot-handoff-part2.md` §15).

**Oracle Cloud (Fase 0/1)**: regione `us-ashburn-1` (Virginia) vicino ai server IBKR in NJ.
IB Gateway via Docker con `platform: linux/amd64` per emulazione x86 su ARM (overhead ~30%
CPU, accettabile per timeframe ≥5 minuti).

**Vultr NJ (Fase 2)**: `gnzsnz/ib-gateway-docker` nativo senza emulazione, latenza ~2-5ms.

## Architettura di deployment

```
GitHub (main branch push)
    ↓ GitHub Actions — test + deploy.yml
    ↓ SSH deploy
Oracle Cloud / Vultr VM
├── ib-gateway  (Docker: ghcr.io/gnzsnz/ib-gateway:stable — include IBC + Xvfb)
├── postgres    (Docker: postgres:15-alpine)
├── trading-bot (Docker: build locale)
├── prometheus  (Docker: prom/prometheus:latest)
└── grafana     (Docker: grafana/grafana:latest)
```

Ordine di avvio systemd (per deploy bare-metal alternativo):
`PostgreSQL → Xvfb → IB Gateway (IBC) → Trading Bot`

## Comandi

```bash
# Setup iniziale su VM
uv sync --all-extras            # installa dipendenze
uv run alembic upgrade head     # applica migrations DB

# Avvio stack completo (Docker)
docker compose up -d

# Log real-time del bot
docker compose logs -f trading-bot
# oppure con systemd:
journalctl -u trading-bot -f

# Restart manuale (senza toccare IB Gateway)
systemctl restart trading-bot
# oppure Docker:
docker compose restart trading-bot

# Riavvio pulito dell'intera stack (systemd)
systemctl restart xvfb && sleep 5
systemctl restart ibgateway && sleep 30
systemctl restart trading-bot

# Emergency stop
systemctl stop trading-bot
uv run python scripts/emergency_flatten.py  # cancella ordini + chiude posizioni

# Verifica posizioni correnti
psql -U trader trading -c "SELECT symbol, quantity, avg_cost FROM positions WHERE quantity != 0;"

# P&L ultimi 7 giorni
psql -U trader trading -c "SELECT date, realized_pnl, num_trades FROM daily_pnl ORDER BY date DESC LIMIT 7;"

# Tax export annuale
uv run python scripts/export_tax_report.py --year 2025
```

## Porte esposte

| Porta | Servizio | Visibilità |
|---|---|---|
| 4001 | IB Gateway (paper) | solo localhost |
| 4002 | IB Gateway (live) | solo localhost |
| 5432 | PostgreSQL | solo localhost |
| 8080 | Health check HTTP | IP noto (ufw) |
| 5900 | VNC IB Gateway | solo localhost, via SSH tunnel |
| 3000 | Grafana | solo localhost, via SSH tunnel |
| 9090 | Prometheus | solo localhost |

Accesso a Grafana da remoto: `ssh -L 3000:localhost:3000 trader@VPS_IP`

## Variabili d'ambiente e segreti

Non committare mai `.env`. Usare `/etc/trading/credentials.env` (permessi 600) in produzione.

Variabili richieste: `IBKR_USERNAME`, `IBKR_PASSWORD`, `TRADING_MODE` (paper|live),
`IBKR_PORT` (4001 paper / 4002 live), `IBKR_CLIENT_ID`, `IBKR_ACCOUNT` (es. U1234567),
`DATABASE_URL`, `POSTGRES_PASSWORD`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`,
`IBKR_FLEX_TOKEN`, `IBKR_FLEX_QUERY_ID`, `MAX_POSITION_SIZE_USD`, `MAX_DAILY_LOSS_USD`,
`MAX_OPEN_POSITIONS`, `DEFAULT_STOP_LOSS_PCT`, `VNC_PASSWORD`, `GRAFANA_PASSWORD`.

Esempio completo in `.env.example` (da creare nella radice del progetto, tracciato in git).

## Monitoring esterno

UptimeRobot (gratuito, check ogni 5 minuti) su `http://VPS_IP:8080/health`.
Alert Telegram quando HTTP ≠ 200 per 2 check consecutivi.
Metriche Prometheus: `trading_pnl_daily_usd`, `trading_open_positions_count`,
`trading_orders_total{status}`, `ibkr_connection_status`, `trading_daily_loss_usd`.

## Backup DB

Cron job giornaliero alle 23:00 CET: `pg_dump | gzip → backups/trading_YYYYMMDD.sql.gz`.
Retention 30 giorni locale. Upload opzionale su Cloudflare R2.
Restore: `gunzip -c backup.sql.gz | psql -U trader trading`.
