# Profilo di stack: React (frontend, dashboard)

> Regola modulare istanziata dal pacchetto `stack-profiles` come `stack-profile.md`. Prescrive le convenzioni con cui si scrive il codice di questo stack; la descrizione dello stack reale del progetto resta nella scheda `context/STACK.md`. Adattare i comandi agli strumenti reali del progetto alla prima istanziazione.

## Componenti e stato

Componenti funzionali con hooks. Lo stato locale vive in `useState` o `useReducer`; quando il passaggio di prop attraversa piu' di due livelli si valuta un contesto o uno store, invece di accettare il prop drilling. Negli artifact destinati a claude.ai non si usano `localStorage` ne' `sessionStorage`, che li' non sono disponibili: lo stato resta in memoria.

## Data fetching e stati dell'interfaccia

Ogni fetch gestisce esplicitamente i tre stati loading, error ed empty, senza lasciare che l'interfaccia li confonda con lo stato pieno. Gli errori mostrati all'utente sono utili e non tecnici; il dettaglio tecnico va nel log.

## Accessibilita'

Le label sono associate ai controlli, i ruoli ARIA[^1] si usano dove la semantica nativa non basta, e il focus si gestisce esplicitamente nelle interazioni che spostano il contesto (dialoghi, navigazioni, notifiche). L'accessibilita' si verifica durante lo sviluppo, non a posteriori.

## Test

Con Testing Library si testa il comportamento visibile all'utente, non l'implementazione: si interroga il DOM per ruolo e testo, non per classi o struttura interna, cosi i test sopravvivono ai refactor.

## Prima di committare

Lint, typecheck (se TypeScript) e test verdi, diff rivisto, nessun secret in stage. Il commit resta manuale dell'utente, secondo la regola generale del sistema.

[^1]: *ARIA*, Accessible Rich Internet Applications - insieme di attributi HTML che comunicano semantica e stato dei componenti alle tecnologie assistive.
