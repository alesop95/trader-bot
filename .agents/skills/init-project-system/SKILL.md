---
name: init-project-system
description: >
  Inizializza in un progetto il sistema di contesto, documentazione e version control
  descritto in .claude/PROJECT-SYSTEM.md. Prima verifica quale account Claude Code e attivo
  sulla macchina (setup multi-account via CLAUDE_CONFIG_DIR) e chiede conferma se ne risulta
  più di uno; poi chiede quale identità git usare per i futuri commit e a quale repository
  GitHub agganciare il remoto, configurandola a livello locale (vedi
  skills/identita-git/RIFERIMENTO.md). Infine esegue il runbook di inizializzazione passo per
  passo, fermandosi a chiedere conferma dove un'azione tocca il version control o e
  difficilmente reversibile. Non esegue mai git add/commit/push: li gestisce l'utente.
---

<!-- generato da sync-codex-skills.py; non modificare -->

Leggere integralmente [`../../../.claude/skills/init-project-system/SKILL.md`](../../../.claude/skills/init-project-system/SKILL.md) e seguirne la procedura canonica. Risolvere i percorsi relativi dalla directory della skill canonica. Tradurre la sintassi o i nomi degli strumenti specifici di Claude negli equivalenti disponibili in Codex senza indebolire controlli, gate o limiti di autorizzazione.
