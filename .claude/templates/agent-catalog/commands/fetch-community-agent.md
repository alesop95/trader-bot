---
description: Scarica un singolo subagent da una fonte del catalogo community in .claude/agents/
argument-hint: <fonte> <nome-agente>
---

# Fetch di un subagent community

Esegue `tools/fetch-community-agent.ps1`/`.sh` per scaricare `$ARGUMENTS` (fonte e nome dell'agente, per esempio `0xfurai react-expert`) dentro `.claude/agents/` del progetto, registrando la provenienza in `.claude/agent-catalog/state.json`.

## Procedura

1. Se il nome esatto dell'agente non e' certo, esegui prima `/list-community-agents <fonte>` per verificarlo: non indovinare mai un nome di file.
2. Esegui lo script nella variante giusta: `./tools/fetch-community-agent.ps1 -Source <fonte> -Agent <nome>` su Windows, `./tools/fetch-community-agent.sh <fonte> <nome>` su Linux/macOS.
3. Se il file esiste gia' in `.claude/agents/`, lo script si rifiuta di sovrascrivere senza `-Force`/`--force`: chiedi conferma esplicita all'utente prima di riprovare con quel flag, non assumerla.
4. Dopo il download, apri il file e rivedi il frontmatter con l'utente: il campo `name` deve restare univoco tra gli agenti gia' presenti nel progetto (rinominare in caso di collisione), e il campo `model`, se presente, spesso fissa uno snapshot specifico che puo' non essere piu' quello corrente: segnalalo e proponi di allinearlo al modello che il progetto usa di default.
5. Ricorda che l'agente scaricato e' testo di terze parti non verificato dal sistema di progetto: va letto prima di fidarsene, non solo installato.

## Vincolo

Non generare mai tu stesso il contenuto di un agente al posto dello script quando l'utente chiede esplicitamente di "prendere" o "pescare" un agente da una fonte community: il valore del comando e' scaricare esattamente cio' che la fonte offre, non produrne una versione tua.
