---
description: >
  Mantiene un livello documentale didattico, distinto dalle schede tecniche di stato: un racconto
  evolutivo che contrappone "com'era e perché era fragile" a "il salto di qualità e perché è
  meglio", con deep-dive che entrano nel codice reale. Da usare SOLO se il progetto ha adottato
  questa pratica esplicitamente (non è parte del ciclo di default): quando chi lavora sul
  progetto vuole imparare rileggendo le proprie decisioni architetturali, non solo saperne lo
  stato. Attivare a ogni refactor o scelta di qualità non ovvia, non per ogni commit.
---

## Cosa risolve

Le schede tecniche sotto `.claude/context/` (`STACK.md`, `design-and-security.md`, e simili)
registrano *cosa* è vero oggi nel codice, e si aggiornano o si sostituiscono quando lo stato
cambia: sono fotografie, non hanno memoria di come si è arrivati lì. Il registro
`memory/decisions.md` in stile ADR-lite[^1] fissa *quale* decisione architetturale è stata presa,
con motivazione e conseguenze, in forma sintetica e append-only.

Nessuno dei due copre un bisogno diverso: capire, con dettaglio pedagogico e nel codice reale,
perché una certa forma ingenua di scrivere una cosa è fragile e perché la forma alternativa è
un salto di qualità. Questo bisogno esiste quando chi lavora sul progetto lo tratta anche come
materiale di apprendimento personale, non solo come stato da mantenere. In quel caso, e solo in
quel caso, si adotta questo livello aggiuntivo.

## Struttura dei due file

Il livello didattico vive in due tipi di documento, entrambi sotto `.claude/context/`, entrambi
tracciati (sono conoscenza tecnica recuperabile da un clone, non narrativa personale da
confinare in `_notes/`).

Un documento *master*, punto d'ingresso unico, con un nome riconoscibile come
`studio-didattico-master.md`. È un racconto evolutivo che **cresce per voci numerate in ordine
cronologico**, non si riscrive né si riordina: ogni intervento nuovo aggiunge una voce in fondo.
Ogni voce segue una struttura fissa in quattro parti.

```
## N. Titolo breve e concreto della voce

Contesto. Perché si è intervenuti, in una manciata di righe, senza ripetere lo stato già
noto dalle voci precedenti.

Com'era e perché era fragile. La forma precedente del codice o della decisione, descritta
con precisione, e la ragione strutturale (non stilistica) per cui era un problema: cosa
poteva rompersi, cosa si duplicava, cosa restava scollegato da un'unica fonte di verità.

Il salto senior e perché è meglio. La forma nuova, il principio generale che la guida (non
solo il dettaglio locale), e perché risolve la fragilità descritta sopra. Se il refactor ha
comportato un compromesso o una scelta di perimetro deliberata, si dichiara qui, onestamente.

Dove leggere il dettaglio: `refactor-NN-<slug-breve>.md`.
```

Un documento *deep-dive* per ogni voce del master, con nome `refactor-NN-<slug-breve>.md` dove
`NN` è un numero sequenziale a due cifre (tipicamente lo stesso indice della voce corrispondente
nel master, per corrispondenza uno a uno). È qui che si entra nel codice: estratti reali "prima"
e "dopo" annotati, non pseudocodice, con i percorsi file veri del progetto. Il registro stilistico
è quello discorsivo definito in `.claude/rules/interaction-style.md`: nessun elenco puntato nella
prosa, acronimi spiegati in note a piè di pagina numerate, termini densi in corsivo, frammenti di
codice in blocchi monospazio. Il deep-dive chiude tipicamente con una sezione che spiega come
estendere il pattern in futuro, così che chi la applica un anno dopo non debba dedurla da zero.

## Quando attivarla

Non è parte del ciclo di feature descritto nella sezione 9 di `PROJECT-SYSTEM.md`, e non si
assume mai per default: è una decisione esplicita, gated allo stesso modo della scelta di creare
un `README.md` pubblico (sezione 2). Si attiva o quando il progetto la adotta fin dall'inizio
(annotato in `CLAUDE.md`, con un rimando ai due file nella tabella dei layer di configurazione),
o in qualsiasi momento successivo su richiesta esplicita di chi lavora sul progetto.

Una volta attiva, si aggiorna a ogni refactor o scelta di qualità non ovvia (non a ogni commit,
non per un fix banale): estrazione di un pattern duplicato in un'unica fonte, cambio di
architettura dello stato, introduzione di una convenzione che sostituisce una precedente. Un
bugfix isolato senza portata architetturale non genera una voce.

## Procedura operativa

Quando si chiude un intervento che merita una voce:

1. Se `studio-didattico-master.md` non esiste ancora nel progetto, crearlo con un'intestazione
   breve che ne dichiara lo scopo (racconto evolutivo, non stato) e la prima voce.
2. Scrivere la voce nel master, in fondo al file, con la struttura in quattro parti sopra. Non
   toccare le voci precedenti.
3. Scrivere il deep-dive corrispondente, `refactor-NN-<slug-breve>.md`, con gli estratti di
   codice reali prima e dopo, nel registro discorsivo del progetto.
4. Aggiornare `memory/progress.md` con una voce di lavoro che registra il fatto in sintesi (data,
   cosa è cambiato, verifiche eseguite) e rimanda al deep-dive per il perché: il work-log non
   duplica la narrazione, la indicizza. Questo evita di raddoppiare la spesa di lettura a ogni
   sessione futura.
5. Se la decisione ha anche portata architetturale in senso ADR, valutare se merita anche una
   voce in `memory/decisions.md`: i due registri non sono a scelta singola, coprono bisogni
   diversi e possono coesistere sulla stessa decisione.

## Cosa non fare

Non generare voci retroattive per tutta la storia del progetto quando la pratica viene adottata
a metà percorso: si parte dalla prima voce dal momento dell'adozione in avanti, senza ricostruire
artificialmente il passato. Non usare questo livello come sostituto delle schede tecniche di
stato: se qualcuno clona il progetto e vuole sapere *cosa* è vero oggi nello stack, deve poter
rispondere da `STACK.md`, non dover leggere l'intero racconto evolutivo per dedurlo. Non
comprimere la struttura in quattro parti per risparmiare spazio: è la struttura stessa, applicata
con disciplina voce dopo voce, che rende il master leggibile come percorso di apprendimento invece
che come changelog travestito.

[^1]: *ADR*, Architecture Decision Record - un formato breve e numerato per registrare una
decisione architetturale con il suo contesto e le sue conseguenze; la variante "lite" adottata da
questo sistema ne mantiene la struttura essenziale (contesto, decisione, motivazione,
conseguenze) senza il formalismo completo del formato originale.
