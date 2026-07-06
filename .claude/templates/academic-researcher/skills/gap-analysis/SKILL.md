---
name: gap-analysis
description: >
  Dato un insieme di paper gia' letti in profondita' o un gap gia' individuato da corpus-analysis
  (Gap Scanner o Canon Update), produce un verdetto per ciascuna direzione di ricerca: da non
  perseguire, condizionale, o promettente, con motivazione strutturata e argomentazione a doppio
  taglio (a favore e contro), ispirandosi al pattern gap-to-topic. Dispone gia' di un prompt di
  verdetto usabile da subito. PARZIALMENTE STUB: la soglia di dominio che separa condizionale da
  promettente resta da calibrare all'attivazione, sul dominio disciplinare specifico del progetto.
disable-model-invocation: true
---

## Stato: parzialmente stub

Il documento di riferimento descrive questa skill come stadio 5 della pipeline (sezione 9 punto 5), ispirata al pattern community `gap-to-topic` (sezione 8), e fissa gia' la scala di verdetto a tre valori. Cio' che non fissa e' la soglia di dominio con cui si decide se un'evidenza e' abbastanza forte da meritare "promettente" invece di "condizionale": una soglia ragionevole in econometria non e' la stessa che in biologia molecolare, e dipende dal dominio disciplinare stabilito nel gate di `research-scoping`. Il prompt sotto e' pero' gia' operativo con un placeholder di dominio: produce un verdetto motivato da subito, e la calibrazione successiva stringe o allenta l'interpretazione delle sue domande, senza cambiarne la struttura.

## Cosa e' gia' fissato

Il verdetto finale si esprime su una scala a tre valori: da non perseguire, condizionale, promettente, sempre con una motivazione esplicita legata ai paper effettivamente letti, mai a conoscenza generale del modello. Il riferimento completo e' la sezione 9 punto 5 di `research-vault/reference/claude-ricercatore-universitario-completo.md`; per il pattern community citato come ispirazione, vedi la voce `WenyuChiou/ai-research-skills` nella sezione 8 dello stesso documento.

## Il prompt di verdetto

Questo prompt e' elaborato per questo pacchetto, non estratto dal metodo esterno gia' citato nelle altre skill (quello screenshot, account `@techwith.ram`, non copre la valutazione di direzioni di ricerca): ne riprende pero' lo stile, in particolare la doppia argomentazione a favore e contro gia' vista in Steelman e Skeptic (`deep-paper-reading`) e la disciplina quote-first. Si applica a una direzione di ricerca gia' emersa, tipicamente dal Gap Scanner o dal Canon Update di `corpus-analysis`, o proposta direttamente dall'utente.

```
ROLE
You are a research strategist evaluating potential research directions for [FIELD / TOPIC], using ONLY the uploaded papers and prior findings in this project.

TASK
For the research direction "[DIRECTION]", produce a structured verdict. For every factual claim, quote the source first, then interpret.

1. State the direction as a single testable question.
2. Closest existing work: which uploaded paper comes nearest to it, and what does it leave open? (quote)
3. Strongest argument FOR pursuing it — one idea, steelman style.
4. Strongest argument AGAINST pursuing it — one idea, skeptic style: what could make it a dead end?
5. What resources, data, or methods would it require that are not yet available in this literature?
6. What would the field gain if it succeeded, and what would be lost in wasted effort if it failed?

VERDICT — choose exactly one:
- NOT WORTH PURSUING: state the specific reason (feasibility, redundancy with existing work, or negative prior evidence).
- CONDITIONAL: state the precise condition that would flip the verdict to promising.
- PROMISING: state the single strongest piece of supporting evidence.

WRITING STYLE — Plain English, no hedging in the verdict line itself.
```

## Come si registra l'esito

Il verdetto, con la direzione valutata e la data, si aggiunge a `research-vault/scope.md` o a una sezione dedicata di `.claude/context/current-work.md` se il progetto la usa gia' per la feature attiva: cosi' una direzione gia' valutata come "da non perseguire" non si ripropone da zero in una sessione successiva senza sapere che era gia' stata scartata.

## Come completare la calibrazione di dominio

All'attivazione, una volta noto il dominio disciplinare (da `research-scoping`), si affina l'interpretazione dei punti 5 e 6 del prompt con criteri specifici del dominio (per esempio, quale dimensione campionaria conta come "risorsa non disponibile" in un contesto sperimentale, o quale livello di replicabilita' e' lo standard atteso in quel campo), senza bisogno di riscrivere la struttura del prompt stesso.
