---
description: Controlla se le fonti del catalogo community di subagent hanno nuovi commit upstream
argument-hint: (nessun argomento)
---

# Controllo aggiornamento delle fonti community

Esegue `tools/check-agent-sources.ps1`/`.sh`, che confronta l'ultimo commit di ciascuna fonte registrata in `.claude/agent-catalog/sources.json` con lo sha registrato l'ultima volta in `.claude/agent-catalog/state.json`. E' la stessa strategia di confronto a costo zero del pacchetto `claude-code-handoff`, applicata qui a piu' fonti invece che a una sola.

## Procedura

1. Esegui lo script nella variante giusta: `./tools/check-agent-sources.ps1` su Windows, `./tools/check-agent-sources.sh` su Linux/macOS. Di default lo script aggiorna anche lo stato tracciato dopo aver riportato l'esito; se si vuole solo un controllo senza scrivere nulla, usa `-Check`/`--check`.
2. Riporta all'utente, fonte per fonte, se c'e' un aggiornamento disponibile (con lo sha prima e dopo), se non c'e' nulla di nuovo, o se non era mai stata controllata prima.
3. Se una fonte segnala di non essere stata controllata da piu' di trenta giorni, dillo esplicitamente: qui lo stallo e' della verifica locale, non della fonte come nel caso di `claude-code-handoff`, perche' nessuna di queste fonti si auto-aggiorna a cadenza nota.
4. Per una fonte con aggiornamento disponibile, proponi `/list-community-agents <fonte>` per vedere cosa e' cambiato nell'elenco, prima di scaricare qualcosa con `/fetch-community-agent`.

## Vincolo

Questo comando non scarica nulla da solo: si limita a segnalare la differenza di commit. Il fetch di un agente specifico resta sempre un passo separato e a scelta dell'utente.
