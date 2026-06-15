# Automated Trading System — Handoff Part 3: Hosting e Operatività 24/7

---

## 1. Il Problema del 24/7 — Cosa Deve Reggere

Prima di scegliere il provider, è utile capire esattamente cosa deve stare su sempre e perché:

```
Timeline giornaliera (orari ET = Eastern Time, Italia +6h)

00:00–05:00   IB Gateway in idle post-restart. Bot in standby.
05:45 (CET)   IB Gateway daily restart (23:45 ET).
              → Disconnessione ~3 min → IBC riautentica automaticamente.
09:25 (15:25) Pre-market check: posizioni residue, warmup dati.
09:30 (15:30) Mercato aperto. Bot entra in loop attivo.
15:45 (21:45) Stop nuovi ingressi.
15:55 (21:55) Chiusura posizioni intraday.
16:05 (22:05) Report EOD. Bot in idle.
16:00–09:30   Bot idle, IB Gateway connesso, GTC stop orders attivi su IBKR.
```

**Cosa succede se il VPS va giù durante le ore di trading?**
Le posizioni non esplodono. Gli ordini GTC (Good Till Cancel) di stop loss sono già piazzati sui server IBKR e rimangono attivi indipendentemente dalla connessione del bot. Il rischio è perdere nuovi segnali e non poter aprire/chiudere posizioni manualmente. Il bot deve tornare su nel minor tempo possibile.

---

## 2. Architettura di Hosting Raccomandata

Per questo use case (algorithmic stock trading, non HFT), l'architettura ottimale è:

```
┌─────────────────────────────────────────────────┐
│           VPS primario (New Jersey/NY)           │
│                                                  │
│  IB Gateway + IBC                                │
│  Trading Bot (Python + PostgreSQL)               │
│  Prometheus + Grafana                            │
│  Health check HTTP endpoint (:8080/health)       │
│                                                  │
│  Uptime: 99.9% SLA target                       │
└──────────────────────┬──────────────────────────┘
                       │ latenza <5ms
                       ▼
              IBKR NY4/NY5 Secaucus, NJ
              (server ordini IBKR)

         ┌─────────────────────────┐
         │  UptimeRobot (esterno)  │
         │  Ping ogni 5 minuti     │
         │  Alert Telegram/Email   │
         └─────────────────────────┘

         ┌─────────────────────────┐
         │  Backup storage         │
         │  (Cloudflare R2 o S3)   │
         │  PostgreSQL dump 1/giorno│
         └─────────────────────────┘
```

**Perché non HA (High Availability) con due VPS?**
Il failover automatico con due istanze di IB Gateway e una strategia stateful è molto complesso e introduce rischi di doppio ordine. Per un retail trader, il risk/benefit è negativo. La soluzione giusta è: un VPS robusto + GTC stop orders sempre piazzati + recovery entro 2-3 minuti via systemd.

---

## 3. Scelta del Provider — Matrice Decisionale

### Il punto chiave sulla latenza

L'infrastruttura primaria IBKR per equity, opzioni ed ETF USA si trova nel corridoio New York/New Jersey, specificamente a Equinix NY4 e NY5 a Secaucus. Un VPS in New York è la scelta corretta per questi strumenti.

Un trader retail che esegue Interactive Brokers TWS da una connessione domestica ha una latenza round-trip media di 50-150ms verso i server IBKR, contro meno di 5ms da un VPS colocato nello stesso hub finanziario.

Per verificare la latenza del proprio provider: `ping gw1.ibllc.com` (server IBKR in Greenwich, CT).

**Però**: se la tua strategia dipende dalla latenza al millisecondo, IBKR (e i broker retail in generale) non sono la soluzione giusta. Ha senso solo nel contesto di chi è la tua competizione. Per strategie su timeframe da 5 minuti in su, 50ms di latenza sono completamente irrilevanti. Anche 200ms lo sono.

### Opzioni a confronto

| Provider | Location | Latenza IBKR | Prezzo | Spec consigliate | Pro | Contro |
|---|---|---|---|---|---|---|
| **Vultr High Frequency** (EWR) | New Jersey | ~2-5ms | ~$24/mese | 2 vCPU / 4GB / NVMe | Latenza ottima, NVMe, Linux | Support mediocre |
| **AWS EC2 t3.medium** (us-east-1) | Virginia | ~10-30ms | ~$30/mese (on-demand) / ~$18 (reserved 1y) | 2 vCPU / 4GB | Ecosystem managed, CloudWatch, RDS | Più caro, setup più complesso |
| **Hetzner CCX23** (Ashburn VA) | Virginia, USA | ~30-50ms | ~€14/mese | 4 vCPU / 8GB / NVMe | Miglior rapporto prezzo/spec | Meno datacenter US, nessun SLA formale |
| **Hetzner CX32** (Europa) | Francoforte/Helsinki | ~150-200ms | ~€8/mese | 4 vCPU / 8GB | Economicissimo | Latenza alta su US |
| **QuantVPS NY** | New York (NY4) | <1ms | ~$60/mese | 4 vCPU / 8GB / NVMe | Vicinissimo a IBKR, pre-conf. | Costoso, Windows-oriented |

### Raccomandazione per questo progetto

**Strategia ≥ 5 minuti di timeframe → Vultr High Frequency New Jersey (~$24/mese)**

È il punto ottimale: latenza eccellente, NVMe, Linux nativo, prezzo ragionevole. La differenza tra 5ms e 1ms è irrilevante per strategie non-HFT.

**Alternativa economica se si è disposti a accettare ~50ms → Hetzner Ashburn VA**

Hetzner ha aperto un datacenter in Ashburn, Virginia. Una CX32 a circa $7.59/mese dà 4 vCPU e 8GB RAM, spec che costerebbero $48/mese dai competitor. Per strategie swing o intraday su timeframe ≥ 15 minuti, la latenza di 30-50ms è completamente trasparente.

**Se si fa anche scalping su 1-min bars → AWS EC2 c5.large us-east-1**

Instance type con CPU ad alta frequenza (3.5GHz+), latenza ~10ms su IBKR, e la possibilità di usare RDS per PostgreSQL managed senza gestire backup manualmente.

---

## 4. Setup Completo del VPS (Vultr NJ — Ubuntu 24.04)

### 4.1 Provisioning iniziale

```bash
# Accedi come root, poi:

# Aggiorna tutto
apt update && apt upgrade -y

# Crea utente non-root
adduser trader
usermod -aG sudo trader

# Abilita SSH key-only (disabilita password)
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd

# Firewall: apri solo SSH, chiudi tutto il resto
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh          # 22
ufw allow from 127.0.0.1 to any port 5432   # PostgreSQL solo localhost
ufw allow from 127.0.0.1 to any port 4002   # IB Gateway solo localhost
# Porta health check: solo dalla tua IP
ufw allow from <TUO_IP_CASA> to any port 8080
ufw enable

# Swap (utile se IB Gateway ha memory spike)
fallocate -l 4G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile swap swap defaults 0 0' >> /etc/fstab
```

### 4.2 Configurazione display virtuale persistente

IB Gateway richiede un display X anche in modalità headless. Usiamo Xvfb gestito da systemd:

```ini
# /etc/systemd/system/xvfb.service
[Unit]
Description=Virtual Framebuffer Display
After=network.target

[Service]
Type=forking
ExecStart=/usr/bin/Xvfb :1 -screen 0 1024x768x24 -ac
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
systemctl enable xvfb
systemctl start xvfb
```

### 4.3 Ordine di avvio dei servizi (dipendenze systemd)

```
PostgreSQL → Xvfb → IB Gateway (IBC) → Trading Bot
```

Il service del Trading Bot deve dichiarare `After=ibgateway.service`:

```ini
# /etc/systemd/system/trading-bot.service
[Unit]
Description=Automated Trading Bot
After=network.target postgresql.service ibgateway.service
Requires=postgresql.service

[Service]
Type=simple
User=trader
WorkingDirectory=/home/trader/trading-bot
EnvironmentFile=/etc/trading/credentials.env
ExecStart=/home/trader/trading-bot/.venv/bin/python -m trading.main
Restart=on-failure
RestartSec=30
RestartPreventExitStatus=1    # non riavviare su exit code 1 (errore critico intenzionale)

# Limiti risorse
MemoryLimit=2G
CPUQuota=80%

# Logging su journald
StandardOutput=journal
StandardError=journal
SyslogIdentifier=trading-bot

[Install]
WantedBy=multi-user.target
```

### 4.4 Sequenza di boot automatica

```bash
# Abilita tutti i service per auto-start al reboot
systemctl enable postgresql
systemctl enable xvfb
systemctl enable ibgateway
systemctl enable trading-bot

# Verifica ordine avvio
systemctl list-dependencies trading-bot
```

**Test reboot:**
```bash
reboot
# Attendi 2-3 minuti poi verifica
ssh trader@VPS_IP
systemctl status ibgateway trading-bot
journalctl -u trading-bot -n 50
```

---

## 5. Health Check Endpoint

Il bot deve esporre un endpoint HTTP che risponde con il suo stato. È necessario per il monitoring esterno.

```python
# src/trading/monitoring/healthcheck.py
"""
Server HTTP minimalista per health check esterno.
UptimeRobot pinga http://VPS_IP:8080/health ogni 5 minuti.
"""
from aiohttp import web
import json
from datetime import datetime

class HealthCheckServer:
    def __init__(self, bot):
        self.bot = bot
        self.app = web.Application()
        self.app.router.add_get("/health", self.health_handler)
        self.start_time = datetime.utcnow()

    async def health_handler(self, request):
        ib_connected = self.bot.ib._connected
        uptime_seconds = (datetime.utcnow() - self.start_time).total_seconds()

        status = {
            "status": "ok" if ib_connected else "degraded",
            "ibkr_connected": ib_connected,
            "uptime_seconds": int(uptime_seconds),
            "timestamp": datetime.utcnow().isoformat(),
        }
        http_status = 200 if ib_connected else 503
        return web.Response(
            text=json.dumps(status),
            status=http_status,
            content_type="application/json"
        )

    async def start(self, host="0.0.0.0", port=8080):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
```

---

## 6. Monitoring Esterno — UptimeRobot

UptimeRobot è gratuito (fino a 50 monitor, check ogni 5 minuti) e invia alert su Telegram/email quando il bot non risponde.

**Setup:**
1. Registrarsi su [uptimerobot.com](https://uptimerobot.com) (gratuito)
2. Creare monitor tipo "HTTP(S)"
3. URL: `http://VPS_IP:8080/health`
4. Check ogni: 5 minuti
5. Alert quando: status code ≠ 200 per 2 check consecutivi
6. Notification: Telegram bot + email

**Alternativa self-hosted**: Uptime Kuma (Docker, gratuito, più feature):

```yaml
# Aggiungere a docker-compose.yml
  uptime-kuma:
    image: louislam/uptime-kuma:latest
    restart: unless-stopped
    ports:
      - "127.0.0.1:3001:3001"
    volumes:
      - uptime_kuma_data:/app/data
```

---

## 7. Backup Automatico PostgreSQL

### Strategy: dump giornaliero + upload su storage esterno

```bash
# /usr/local/bin/backup-trading-db.sh
#!/bin/bash
set -e

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/trader/backups"
DB_NAME="trading"
BACKUP_FILE="$BACKUP_DIR/trading_$DATE.sql.gz"
RETENTION_DAYS=30

mkdir -p "$BACKUP_DIR"

# Dump compresso
pg_dump -U trader "$DB_NAME" | gzip > "$BACKUP_FILE"

# Upload su Cloudflare R2 (o S3)
# aws s3 cp "$BACKUP_FILE" "s3://trading-backups/$DATE/" --endpoint-url "$R2_ENDPOINT"

# Pulisci backup locali vecchi
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completato: $BACKUP_FILE"
```

```bash
# Cron job: backup ogni giorno alle 17:00 ET (23:00 CET)
# /etc/cron.d/trading-backup
0 23 * * * trader /usr/local/bin/backup-trading-db.sh >> /var/log/trading-backup.log 2>&1
```

### Restore rapido (disaster recovery)

```bash
# Ripristino da backup in caso di perdita VPS
gunzip -c trading_20260613_230000.sql.gz | psql -U trader trading

# Verifica: conta trade
psql -U trader trading -c "SELECT COUNT(*) FROM trades;"
```

---

## 8. Gestione IB Gateway Daily Restart

Questo è il punto critico per il 24/7. IB Gateway si riavvia **ogni giorno alle 23:45 ET (05:45 CET)** per default. Durante il restart (~3-5 minuti) il socket API è irraggiungibile.

### IBC configurazione restart

```ini
# In ~/ibc/config.ini
# Configura l'orario del restart automatico
# Default: 23:45 ET. Puoi cambiarlo se necessario.
# ATTENZIONE: non cambiare a orari di mercato (09:30-16:00 ET)

# IBC gestisce automaticamente il re-login dopo il restart
IbAutoRestartTime=23:45
```

### Gestione nel bot

```python
# src/trading/broker/client.py
import asyncio
from loguru import logger

class IBClient:
    # ...

    async def _handle_disconnect(self):
        """
        Chiamato da ib_async quando la connessione si interrompe.
        Attende e riprova — il restart di IB Gateway dura ~5 minuti.
        """
        logger.warning("Disconnesso da IB Gateway")
        self._connected = False

        retry_intervals = [30, 60, 60, 120, 120, 300]  # secondi tra i tentativi
        for wait in retry_intervals:
            logger.info(f"Riconnessione tra {wait}s...")
            await asyncio.sleep(wait)
            try:
                await self.connect()
                logger.info("Riconnesso con successo")
                return
            except Exception as e:
                logger.warning(f"Tentativo fallito: {e}")

        # Se dopo tutti i tentativi non si è riconnesso, alert critico
        from trading.notifications.telegram import send
        await send("🚨 Impossibile riconnettersi a IB Gateway dopo 10+ minuti", level="CRITICAL")
```

### Cosa succede alle posizioni durante il restart

- Gli ordini **GTC** (Good Till Cancel) piazzati su IBKR **sopravvivono** al restart del gateway — sono sui server IBKR
- Gli ordini **DAY** scadono automaticamente alle 16:00 ET (quindi non ci sono a mezzanotte)
- Le posizioni aperte rimangono aperte
- Al riavvio del bot, deve fare `reqPositions()` per risincronizzare lo stato locale

```python
async def post_reconnect_sync(self):
    """Dopo ogni riconnessione, risincronizza stato dal server IBKR."""
    # Posizioni
    positions = await self.ib.reqPositionsAsync()
    logger.info(f"Posizioni post-reconnect: {len(positions)}")

    # Ordini aperti
    open_orders = await self.ib.reqOpenOrdersAsync()
    logger.info(f"Ordini aperti post-reconnect: {len(open_orders)}")

    # Aggiorna DB con stato reale
    # (implementare in db/repository.py)
```

---

## 9. Strategia di Logging per Produzione

### Rotazione log

```python
# In main.py — configurazione logger loguru
from loguru import logger

logger.add(
    "logs/trading_{time:YYYY-MM-DD}.log",
    rotation="00:00",            # nuovo file ogni giorno a mezzanotte
    retention="90 days",         # mantieni 90 giorni (utile per debug e fiscale)
    compression="gz",            # comprimi log vecchi
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} | {message}",
    enqueue=True,                # thread-safe per asyncio
)

# Log separato per errori critici (più lunga retention)
logger.add(
    "logs/errors_{time:YYYY-MM-DD}.log",
    rotation="1 week",
    retention="1 year",          # tieni gli errori per un anno
    level="WARNING",
    compression="gz",
    enqueue=True,
)

# Log separato per trade (utile per riconciliazione fiscale)
logger.add(
    "logs/trades_{time:YYYY}.log",   # un file per anno
    rotation="1 year",
    retention="10 years",            # mantieni per la dichiarazione dei redditi
    level="INFO",
    filter=lambda record: "TRADE" in record["message"],
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {message}",
    enqueue=True,
)
```

### Cosa loggare (e a quale livello)

```python
# Pattern di logging standardizzati nel codice:

# Ogni ordine inviato (sempre INFO, incluso nel log TRADE)
logger.info(f"TRADE BUY {shares} {symbol} @ ${price:.2f} | strategy={strategy_name} | reason={reason}")

# Ogni fill ricevuto (sempre INFO)
logger.info(f"TRADE FILL {side} {qty} {symbol} @ ${fill_price:.2f} | execId={exec_id} | commission=${commission:.4f}")

# Risk block (WARNING — non è un errore ma merita attenzione)
logger.warning(f"RISK BLOCK {symbol}: {reason}")

# Circuit breaker (CRITICAL)
logger.critical(f"CIRCUIT BREAKER: {reason}")

# Connessione (sempre loggata)
logger.info(f"IB Gateway connected | port={port} | account={account}")
logger.warning(f"IB Gateway disconnected | will retry in {wait}s")
```

---

## 10. Accesso Remoto e Operatività

### SSH port forwarding per Grafana (no esposizione pubblica)

```bash
# Da casa/ufficio, accedi a Grafana senza esporre la porta:
ssh -L 3000:localhost:3000 trader@VPS_IP

# Poi apri: http://localhost:3000 nel browser
```

### Comandi operativi utili

```bash
# Stato di tutti i servizi
systemctl status ibgateway trading-bot postgresql xvfb

# Log real-time del bot
journalctl -u trading-bot -f

# Log ultime 100 righe con errori
journalctl -u trading-bot -n 100 | grep -E "ERROR|CRITICAL|WARNING"

# Restart manuale del bot (senza toccare IB Gateway)
systemctl restart trading-bot

# Riavvio pulito dell'intera stack
systemctl restart xvfb && sleep 5
systemctl restart ibgateway && sleep 30
systemctl restart trading-bot

# Verifica posizioni correnti (query diretta al DB)
psql -U trader trading -c "SELECT symbol, quantity, avg_cost FROM positions WHERE quantity != 0;"

# P&L di oggi
psql -U trader trading -c "SELECT date, realized_pnl, num_trades FROM daily_pnl ORDER BY date DESC LIMIT 7;"

# Ultimi 20 trade
psql -U trader trading -c "SELECT symbol, side, quantity, fill_price, executed_at FROM trades ORDER BY executed_at DESC LIMIT 20;"
```

### Emergency stop manuale

```bash
# 1. Ferma nuovi trade (ferma il bot ma mantieni GTC stop su IBKR)
systemctl stop trading-bot

# 2. Chiudi tutte le posizioni via script di emergenza
cd /home/trader/trading-bot
source .venv/bin/activate
python scripts/emergency_flatten.py   # chiama flatten_all_positions() + cancel_all_orders()

# 3. Verifica
python scripts/check_positions.py
```

---

## 11. Costi Mensili Totali Stimati

| Voce | Provider | Costo/mese |
|---|---|---|
| VPS (Vultr NJ, 2vCPU/4GB) | Vultr | ~$24 |
| Backup storage (10GB) | Cloudflare R2 | ~$0 (free tier) |
| Monitoring esterno | UptimeRobot | $0 (free plan) |
| Market data IBKR (NYSE+NASDAQ) | IBKR | ~$0* |
| **Totale infrastruttura** | | **~$24/mese** |

*Le market data subscription IBKR (~$9/mese totali) vengono rimborsate automaticamente se generi >$30/mese di commissioni. Un bot attivo con qualche trade al giorno supera facilmente questa soglia.

---

## 12. Checklist Go-Live Infrastructure

- [ ] VPS provisioned in New Jersey/New York
- [ ] Firewall configurato (solo SSH e :8080 da IP noto)
- [ ] Xvfb + IBC + IB Gateway si avviano automaticamente al boot
- [ ] Test reboot: tutti i servizi tornano su entro 5 minuti
- [ ] PostgreSQL con backup cron attivo e testato (restore verificato)
- [ ] Health endpoint risponde su :8080/health
- [ ] UptimeRobot (o Uptime Kuma) configurato con alert Telegram
- [ ] Logs ruotano correttamente (controllare dopo 48h)
- [ ] `ping gw1.ibllc.com` dal VPS mostra < 20ms
- [ ] Emergency stop script testato in paper
- [ ] SSH key-only, no password login
- [ ] Swap configurato (4GB)

---

*Part 3 — Versione 1.0 — Giugno 2026*
*Da leggere insieme a Part 1 e Part 2.*
