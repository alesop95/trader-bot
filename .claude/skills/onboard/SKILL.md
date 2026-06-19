---
name: onboard
description: >
  Produce una spiegazione completa e strutturata del progetto a partire dal suo sistema di
  contesto versionato, per chi apre il progetto da zero: un collaboratore che ha appena clonato
  il repository, o lo stesso autore che vi torna dopo molto tempo. Legge CLAUDE.md,
  memory/index.md, context/current-work.md, le schede di context/ e memory/decisions.md, e ne
  ricava cosa e il progetto, lo stack, l'architettura, lo stato attuale, le decisioni prese e
  come si avvia e si testa. E di sola lettura: non modifica file e non esegue git.
disable-model-invocation: true
---

## Contesto git (best-effort, pre-iniettato)

!`git status --short`
!`git branch --show-current`
!`git log -1 --format="%h %ad %s" --date=short`

Se la cartella non è ancora un repository git, questi comandi stampano un errore "not a git
repository": il progetto non è ancora versionato, e l'onboarding si limita a ciò che le schede
documentano.

## Scopo

Questa skill dà il quadro completo del progetto a chi parte da zero. È distinta dalla procedura
di ripresa della sezione 12 di `PROJECT-SYSTEM.md`, che è veloce e mirata alla prossima azione e
serve a chi sta già lavorando al progetto: lì si legge `memory/index.md` e si riparte. `onboard`
invece ricostruisce l'intero quadro, perché chi la invoca non conosce ancora il progetto.

## Cosa legge, e in quest'ordine

1. `CLAUDE.md` di radice, che indicizza i file satellite tracciati e replica la procedura di ripresa.
2. `.claude/memory/index.md`, per branch, commit di riferimento, stato di verifica di ogni scheda e prossima azione concreta.
3. `.claude/context/current-work.md`, per la feature in corso, la definition of done e le domande aperte.
4. Le schede di `.claude/context/`: `STACK.md` con stack, flussi di codice e alternative deliberatamente escluse, `design-and-security.md`, `deployment.md`, `dev-testing.md`, `roadmap.md`.
5. `.claude/memory/decisions.md`, per le decisioni architetturali e la loro motivazione.
6. `.claude/memory/progress.md`, per le tappe principali del work-log.

I diagrammi sotto `context/diagrams/` si aprono se una scheda li referenzia. Il materiale privato
sotto `_notes/` non si legge, salvo richiesta esplicita dell'utente.

## Cosa produce

Una spiegazione strutturata e discorsiva che copre, nell'ordine: cos'è il progetto e a cosa
serve; lo stack e le scelte tecnologiche, con le alternative escluse e il perché; l'architettura
e i flussi principali; lo stato attuale, cioè branch, commit di riferimento, cosa è fatto e cosa
manca, ricavato da `index.md` e `current-work.md`; le decisioni architetturali rilevanti con la
motivazione; come si avvia, si builda e si testa il progetto, da `deployment.md` e
`dev-testing.md`; i punti aperti. Chiude indicando da dove conviene cominciare a lavorare, cioè
la prossima azione concreta dichiarata in `index.md`.

Se l'utente indica un taglio, ad esempio solo il deploy o solo la sicurezza, si apre per esteso
la scheda pertinente e si riassume il resto, per non bruciare contesto inutilmente.

## Vincoli

Sola lettura: non modifica file e non esegue mai `git add`, `commit` o `push`. Non inventa: se una
scheda manca o contiene solo il frontmatter senza contenuto, lo si dichiara invece di riempire per
ipotesi. Se il sistema di contesto non è presente, cioè mancano `.claude/memory/` e le schede di
`context/`, segnalare che il progetto non è ancora stato inizializzato o allineato allo standard e
rimandare alla skill `init-project-system`, senza tentare di ricostruire il quadro dal solo codice.
