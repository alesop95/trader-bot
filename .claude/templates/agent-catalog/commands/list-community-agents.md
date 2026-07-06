---
description: Elenca i subagent disponibili nelle fonti flat del catalogo community (agent-catalog)
argument-hint: [chiave-fonte]
---

# Elenco dei subagent community disponibili

Esegue `tools/list-community-agents.ps1`/`.sh` (variante del sistema operativo del progetto) e mostra i subagent disponibili in ciascuna fonte "flat" registrata in `.claude/agent-catalog/sources.json`. Senza argomento elenca tutte le fonti flat; con `$ARGUMENTS` filtra su una sola fonte per chiave, per esempio `0xfurai`.

## Procedura

1. Esegui lo script nella variante giusta: `./tools/list-community-agents.ps1 -Source $ARGUMENTS` su Windows, `./tools/list-community-agents.sh $ARGUMENTS` su Linux/macOS. Se `$ARGUMENTS` e' vuoto, ometti il filtro.
2. Se lo script segnala il limite di 60 richieste/ora dell'API GitHub non autenticata, dillo esplicitamente all'utente invece di ritentare a raffica.
3. Presenta l'elenco raggruppato per fonte, con il conteggio finale gia' stampato dallo script. Se l'utente chiede un agente per dominio (per esempio "qualcosa per React"), cerca nell'elenco restituito invece di indovinare un nome plausibile.
4. Per scaricare un agente specifico, rimanda a `/fetch-community-agent <fonte> <nome>`.

## Vincolo

Non inventare mai un nome di file che non compare nell'output dello script: se un agente cercato non c'e' nella fonte interrogata, dillo e proponi di controllare un'altra fonte o l'indice curato `hesreallyhim/awesome-claude-code` a mano.
