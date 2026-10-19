---
name: cerca-pacchetto
description: >
  Prima di costruire a mano una capacità, cerca nel catalogo dei pacchetti del template se
  esiste già, e se esiste la propone all'utente. Si carica quando si sta per scrivere uno
  strumento, una mappa, un convertitore, un controllo di qualità o un'integrazione con un
  programma o un servizio che non sono specifici del progetto; quando l'utente indica un
  programma, una suite o un servizio da usare e non si sa come pilotarlo; quando il
  progetto comincia a fare qualcosa che all'inizio non faceva, come raccogliere fonti,
  produrre documenti, impaginare, trascrivere o distribuire un'applicazione; e quando si
  sta per chiedere all'utente come procedere su una pratica che il template potrebbe già
  prescrivere. Non installa nulla senza una risposta esplicita e non esegue mai git add,
  commit o push.
---

# cerca-pacchetto

Il catalogo `.claude/templates/PACKAGES.md` arriva in ogni progetto istanziato con l'allineamento, ma nessun punto letto in sessione lo nomina, e il gate che lo attraversa, `gate-pacchetti`, si esegue solo all'inizializzazione e a ogni tornata di allineamento, non su invocazione dell'agente. Fra un gate e l'altro il catalogo è quindi invisibile proprio quando servirebbe, cioè quando il lavoro arriva. Il caso che ha fatto nascere questa skill, il 2026-10-19 in un progetto istanziato: l'utente ha indicato una suite di applicazioni installata sulla macchina, e l'agente ha cercato sul disco, letto le note di rilascio e interrogato un eseguibile per ricostruirsi una mappa che il pacchetto `craft-apps` conteneva già, artefatto per artefatto. Nella stessa giornata ha chiesto due volte al proprietario come procedere su pratiche che il template prescriveva.

Questa skill è il terzo momento del gate: non l'inizializzazione, non l'allineamento, ma il punto in cui si sta per rifare a mano qualcosa.

## Procedura

Si descrive il lavoro con le parole con cui si presenta, non con il nome di un pacchetto che si suppone esista, e si interroga il catalogo:

```
python .claude/templates/tools/cerca-pacchetto.py --progetto . <parole del lavoro>
```

Lo strumento confronta le parole con la colonna «Quando offrirlo» di ogni voce, che è il suo innesco, e restituisce le poche voci pertinenti con il rimando alla riga intera. La ricerca è per parole e non giudica: una voce in testa non è per questo la risposta, e una domanda formulata male non trova niente. Se non trova niente, si riprova una volta con i sinonimi del lavoro e poi si procede a mano dichiarandolo.

Per ogni voce candidata si legge la riga intera del catalogo, non il solo estratto, e si decide se risponde davvero. Se risponde, si propone all'utente con le tre frasi del gate, cioè che cosa fa, perché a questo progetto serve adesso e che cosa costa, compresi le dipendenze esterne e i token che un server MCP occupa a ogni turno, e si chiede. Un sì si istanzia come dice la colonna «Cosa istanzia» e si registra dove il progetto registra le scelte del gate; un no si registra allo stesso modo, così che la prossima tornata sappia che era stato escluso e non dimenticato.

Se la voce dice che il pacchetto è già istanziato, non lo si propone: lo si usa, leggendone la skill o il README. L'etichetta «non rilevato» non prova il contrario, perché lo strumento riconosce skill e strumenti ma non le schede o le regole che alcuni pacchetti istanziano.

## Che cosa non è

Non sostituisce `gate-pacchetti`, che attraversa il catalogo per settore e resta la procedura delle tornate. Non si carica a ogni sessione e non elenca i pacchetti all'avvio: il catalogo supera i centomila caratteri e un elenco di nomi non dice quando servono, quindi entrambe le vie costerebbero contesto a ogni sessione che non ne ha bisogno. Il costo di questa skill è la sua descrizione, che l'ambiente annuncia da sé, più una ricerca quando la situazione si presenta.
