# comandi-ragionamento

<!-- readme-summary: Sedici comandi a invocazione manuale per analisi critica, decisione, stile della risposta e produzione, senza costo di contesto e uguali in Claude Code e Codex. -->

> Sedici comandi che cambiano il modo in cui l'agente affronta una richiesta: sette di analisi critica, due di decisione, quattro di stile della risposta e tre di creatività e produzione. Sono skill a invocazione manuale: non pesano sul contesto finché non si scrivono, e valgono allo stesso modo in Claude Code e in Codex.

## Da dove vengono

L'elenco dei nomi e la riga che descrive ciascuno vengono da una scheda intitolata «16 Claude Commands Worth Stealing», firmata GenAI.works e datata novembre 2026, che il proprietario ha consegnato come testo il 2026-11-12. La scheda è un'immagine e non una fonte che si possa interrogare, quindi non sta nel registro delle fonti a monte. Dà soltanto nomi e una riga: il testo di ogni skill è stato scritto qui, legandolo alle regole del sistema dove un comando le tocca. Il proprietario ha deciso lo stesso giorno che entrano tutti, compresi quelli che cambiano soltanto il tono.

## I comandi

| Comando | Gruppo | Che cosa fa |
|---|---|---|
| `/secondorder` | Analisi critica | Mostra che cosa succede dopo l'esito ovvio di una scelta: le conseguenze di secondo e terzo ordine. |
| `/redteam` | Analisi critica | Prova a rompere un piano, un codice o un documento: casi limite, punti ciechi, modi di abusarne. |
| `/assumptions` | Analisi critica | Tira fuori le assunzioni nascoste di un piano e segnala quelle che più probabilmente sono false. |
| `/steelman` | Analisi critica | Costruisce la versione più forte della posizione opposta a quella che si sta per adottare. |
| `/premortem` | Analisi critica | Dà per fallito il piano fra qualche mese e risale alle cause più probabili, prima di cominciare. |
| `/devil` | Analisi critica | Sostiene con convinzione la tesi opposta a qualunque cosa sia stata appena affermata. |
| `/roast` | Analisi critica | Dà un giudizio franco e senza attenuazioni su un lavoro: che cosa non va e perché, senza complimenti di cortesia. |
| `/ooda` | Decisione | Affronta una situazione con il ciclo osserva, orienta, decidi, agisci, dichiarando ogni passaggio. |
| `/matrix` | Decisione | Mette tutte le opzioni di una scelta in una sola tabella di confronto, con criteri espliciti. |
| `/brief` | Stile di risposta | Risponde in tre righe al massimo. |
| `/silent` | Stile di risposta | Esegue il compito senza spiegarlo: solo il risultato. |
| `/lockin` | Stile di risposta | Resta sul compito indicato e su nient'altro, senza deviazioni né migliorie non chieste. |
| `/ghost` | Stile di risposta | Scrive un testo che si legge come scritto da una persona, senza i segni tipici del testo generato. |
| `/godmode` | Creatività e produzione | Affronta il compito al massimo dell'impegno: più alternative esplorate, la migliore sviluppata fino in fondo. |
| `/artefatto` | Creatività e produzione | Consegna il risultato come artefatto visivo o interattivo invece che come testo: pagina, diagramma, tabella navigabile. |
| `/steal` | Creatività e produzione | Smonta qualcosa che funziona per capire perché funziona, e ne ricava ciò che si può riusare. |

Quindici portano il nome della scheda. Il sedicesimo nella scheda si chiama `artifacts`, e qui si chiama `artefatto`, perché `/artifacts` in Claude Code è già un comando del client.

## Perché non costano contesto

Ogni skill dichiara `disable-model-invocation: true`. La documentazione di Claude Code, letta il 2026-11-12 nella pagina delle skill, dice che con quel campo la descrizione non sta nel contesto e la skill si carica solo quando l'utente scrive il comando. Ne seguono due cose: sedici comandi in più non spostano il carico di avvio che `misura-istruzioni.py` sorveglia, e l'agente non li invoca mai da sé, quindi restano strumenti di chi scrive.

## Parità fra Claude Code e Codex

In Claude Code si scrive `/premortem il piano di migrazione`. In Codex la stessa skill si richiama con `$premortem` o dal selettore delle skill, attraverso l'adattatore che `tools/sync-codex-skills.py` genera sotto `.agents/skills/` a partire dalla skill canonica: il testo è uno solo. Nessuno dei sedici, per quanto ho verificato, ha un equivalente nativo con lo stesso scopo in uno dei due client, tranne il caso del nome `artifacts` detto sopra; la verifica sui comandi nativi di Codex non è stata fatta sulla sua documentazione, e prima di istanziare si controlla con il selettore delle skill che nessun nome sia già preso.

## Istanziazione

Si copiano in `.claude/skills/` del progetto le cartelle dei comandi scelti, una per comando, anche solo alcune; poi, dove il progetto usa Codex, si esegue `python tools/sync-codex-skills.py`. Non c'è altro: nessuna dipendenza, nessuna riga da aggiungere al `CLAUDE.md`, nessuna regola.

```
.claude/templates/comandi-ragionamento/skills/<comando>/SKILL.md  ->  .claude/skills/<comando>/SKILL.md
```

## Limiti e rimozione

Tre comandi chiedono all'agente una risposta più corta o più asciutta, cioè `brief`, `silent` e `lockin`, e nessuno dei tre sospende ciò che le regole del sistema chiedono a ogni giro: la memoria su disco si aggiorna e la riga dei file scritti resta. `godmode` alza di proposito il costo in token. `redteam` vale per il lavoro e i sistemi propri. `ghost` migliora un testo e non serve a nasconderne l'origine a chi ha diritto di conoscerla.

Per togliere un comando si cancella la sua cartella sotto `.claude/skills/` e si rilancia `sync-codex-skills.py`, che toglie l'adattatore.
