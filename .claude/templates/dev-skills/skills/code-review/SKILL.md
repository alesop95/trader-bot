---
name: code-review
description: Revisione di codice strutturata su qualita', correttezza, performance, sicurezza e test, nel contesto principale. Attiva su richieste come "rivedi", "review", "controlla questo codice". Nota: nel progetto mette in ombra l'eventuale skill nativa omonima di Claude Code.
---

# Code review (skill di progetto)

Esegui una revisione strutturata di codice. Questa e' la variante di progetto, versionata col repository: se la CLI offre la skill nativa `/code-review` e non serve un processo personalizzato, quella resta preferibile (vedi README del pacchetto `dev-skills`).

## Processo

1. Delimita lo scope: il diff non committato (`git diff`), file specifici indicati con `@file`, oppure una PR[^1]. Dichiara lo scope prima di iniziare.
2. Analizza per layer, nell'ordine: correttezza (edge case, gestione errori, race condition, off-by-one), sicurezza (input non validati, secret in chiaro, injection, permessi), performance (query N+1, allocazioni inutili, loop costosi, I/O bloccante), qualita' (leggibilita', naming, duplicazioni, complessita', aderenza alle convenzioni del `CLAUDE.md` e del profilo di stack), test (copertura dei casi critici, test mancanti).
3. Riporta i finding raggruppati per severita', bloccante, da sistemare, opzionale, ciascuno con file e riga, problema, conseguenza concreta e fix proposto. Se una categoria e' pulita, dichiaralo invece di ometterla.

## Vincoli

Solo analisi e proposte: non modificare il codice senza conferma esplicita. Se il progetto ha una guida di stile o un profilo di stack, citali nei finding pertinenti. Nessuna operazione git.

[^1]: *PR*, Pull Request - proposta di merge di un branch, tipicamente su GitHub, con diff revisionabile.
