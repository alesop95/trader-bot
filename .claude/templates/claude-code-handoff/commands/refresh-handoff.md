---
description: Ri-distilla .claude/context/claude-code-handoff.md dalla guida upstream scaricata in _notes/upstream/claude-code-guide.md
argument-hint: (nessun argomento)
---

# Refresh dell'handoff Claude Code

Rigenera `.claude/context/claude-code-handoff.md` a partire dalla fonte upstream aggiornata, mantenendone struttura e stile. E' il complemento in-sessione dello script `tools/update-handoff.ps1`/`.sh`: lo script scarica e, se puo', distilla da solo; questo comando distilla quando lo script non ha potuto farlo o quando si vuole rifinire il risultato a mano.

## Prerequisito

Deve esistere `_notes/upstream/claude-code-guide.md`, scaricato dallo script di aggiornamento. Se manca, chiedi all'utente di eseguire prima lo script nella variante del suo sistema operativo:

```
./tools/update-handoff.ps1 -Force     # Windows
./tools/update-handoff.sh --force    # Linux/macOS
```

## Procedura

1. Leggi l'intestazione di `_notes/upstream/claude-code-guide.md` per la versione upstream, poi il documento per sezioni, senza caricarlo tutto insieme se e' voluminoso: prima i titoli, poi solo le sezioni pertinenti alle differenze.
2. Leggi l'attuale `.claude/context/claude-code-handoff.md` per conoscerne struttura, sezioni numerate e stile.
3. Rigenera il documento mantenendo la stessa numerazione e gli stessi titoli di sezione (paragrafi 0-13), lo stile conciso in italiano con i termini tecnici in inglese, i marcatori `[OFFICIAL]`, `[COMMUNITY]` e `[NEW]`, e le sezioni 0 (collocazione nel sistema) e 13 (auto-aggiornamento) invariate. Aggiorna solo i contenuti realmente cambiati upstream: nuovi flag CLI, comandi slash, opzioni di permessi, MCP, hooks, subagent, agent teams.
4. Aggiorna il frontmatter del documento: `upstream-release` alla versione appena letta, `distilled-date` a oggi.
5. Se lo stato in `.claude/handoff-state.json` non riporta gia' la stessa versione, allinealo.
6. Riporta all'utente in tre-cinque punti cosa e' cambiato rispetto alla versione precedente, citando le versioni upstream di partenza e di arrivo, e ricorda che il diff va rivisto e che il commit resta manuale.

## Caso della fonte in stallo

Se lo script ha segnalato che la fonte upstream e' ferma (ultimo check upstream piu' vecchio di quattordici giorni), la guida scaricata e' essa stessa vecchia. In quel caso non limitarti a ri-distillare: verifica le voci piu' volatili (flag CLI, comandi slash, modalita' di permesso) direttamente con `claude --help`, `/help` e le docs ufficiali `code.claude.com/docs`, integra le differenze trovate marcandole `[OFFICIAL]`, e annota nel frontmatter che la distillazione ha integrato fonti oltre la guida in stallo.

## Vincoli

Non inventare feature: includi solo cio' che e' documentato nella fonte, o che hai verificato direttamente con `claude --help` e le docs ufficiali nel caso della fonte in stallo. Non allungare: l'handoff resta un riferimento operativo denso, non una copia della guida, che resta comunque consultabile in `_notes/upstream/claude-code-guide.md`. Dove la fonte community contraddice una regola del sistema (per esempio sulle modalita' di permesso), l'handoff registra l'opzione e rimanda alla regola, che resta normativa.
