# Work-log

> Append-only, in ordine cronologico inverso (la voce più recente in alto). Ogni passo
> significativo di codice e ogni intervento manuale rilevante lascia una voce con data, file
> toccati, motivo e commit di riferimento. Qui confluisce anche il log di riconciliazione dei
> documenti `.docx`, con il nome del documento sorgente e l'esito, così la data di allineamento
> sopravvive a un clone.

## 2026-06-15 — Popolamento schede context/ da handoff primo-prompt

Commit: 8a47d30
File toccati: tutte le schede di `context/` (STACK.md, design-and-security.md, deployment.md,
dev-testing.md, current-work.md, roadmap.md).
Motivo: distillazione dei 5 file di handoff in `primo-prompt/` nelle schede di contesto. Prima
della popolazione le schede avevano solo frontmatter e placeholder template. Ora contengono
la specifica completa del progetto: stack (Python 3.12, uv, ib-async, PostgreSQL, SQLAlchemy 2.0
async, Alembic, pandas-ta-classic, vectorbt, APScheduler, Loguru, FastAPI, Docker Compose v2),
architettura (6-interface pattern, StrategyComposer, StrategyRegistry, Repository pattern),
deployment (3 fasi Oracle Cloud ARM → Vultr NJ, Docker, GitHub Actions, systemd),
test (pytest + pytest-asyncio, vectorbt backtesting, pre-live checklist), piano di lavoro
(23 step di implementazione in ordine) e roadmap. Schede tracciabili al commit 8a47d30.

## 2026-06-15 — Ancoraggio greenfield al primo commit

Commit: 8a47d30
File toccati: tutte le schede di `context/` e `memory/index.md`.
Motivo: sostituzione del segnaposto PENDING-FIRST-COMMIT con l'hash reale di HEAD dopo il
primo commit manuale. Schede ancorate: STACK.md, design-and-security.md, deployment.md,
dev-testing.md, current-work.md, roadmap.md.

## 2026-06-15 — Inizializzazione del sistema di progetto

Commit: 8a47d30
File toccati: anatomia di `.claude`, `CLAUDE.md`, `.gitignore`, schede di `context/`.
Motivo: installazione del sistema portabile di contesto, documentazione e version control
descritto in `.claude/PROJECT-SYSTEM.md`. Schede create con struttura e frontmatter, da popolare
leggendo il codice nelle sessioni successive.
