# Chiusura delle sessioni degli agenti da terminale

> Regola modulare del pacchetto `agenti-terminale`. Si carica sempre dove esiste più di una radice di agente. Riguarda ciò che resta sul disco quando una sessione finisce, ed è il completamento del wipe: il wipe copre l'incuria, questa regola copre la volontà.

## Il principio

> **Una sessione che si considera chiusa per davvero va rimossa, non abbandonata.**

Abbandonarla non la fa sparire: la lascia in un magazzino che il wipe **preserva apposta**, perché appartiene a un progetto vivo. È il comportamento corretto del wipe, non un suo difetto: senza quella preservazione non si potrebbe riprendere il lavoro del giorno prima.

Ne discende la distinzione che va fatta ogni volta, e che nessuno strumento può fare al posto di chi lavora:

| Intenzione | Azione | Cosa resta |
|---|---|---|
| **Riprenderò questa conversazione** | si esce e basta | tutto, ed è quello che si vuole |
| **Ho finito con questa conversazione** | si **rimuove** la sessione | niente |

Nessun automatismo distingue i due casi, perché la differenza sta nell'intenzione di chi ha lavorato, non in un dato osservabile. Un wipe che decidesse da sé cancellerebbe lavoro che serviva ancora; uno che non cancella mai accumula per sempre.

## Le due attuazioni

Sono diverse perché i due agenti offrono meccanismi diversi, e la differenza va conosciuta per non dare per scontato che l'altro faccia lo stesso.

**Codex ha un comando nativo.** Dentro la sessione:

```text
/delete
```

Cancella quella sessione ed esce. È la via corretta e non richiede altro.

**Claude Code non ha un equivalente.** Non esiste un comando per cancellare la sessione corrente, e il wipe di fine sessione **preserva** i progetti che si è scelto di preservare. Una conversazione chiusa per davvero su un progetto preservato **resta** finché non la si toglie a mano dal magazzino dell'account.

## Perché la regola esiste, invece di lasciar fare al wipe

Il wipe risponde alla domanda *"che cosa è rimasto indietro?"*. Questa regola risponde a *"che cosa ho deciso che non serve più?"*, e sono domande diverse con risposte diverse.

Il caso che le distingue si è presentato davvero: una sessione chiusa per errore è stata **recuperata** il giorno dopo proprio perché il wipe l'aveva preservata, e in quel momento la preservazione era esattamente ciò che serviva. La stessa preservazione, su una sessione che non serviva più, sarebbe stata accumulo.

## Che cosa questa regola non risolve

**Non rende una sessione irrecuperabile lato server.** Ciò che è stato inviato al modello vive secondo la politica di conservazione dell'area di lavoro, che è una configurazione lato fornitore e non si tocca da qui. Cancellare la sessione locale e credere di aver cancellato la conversazione è l'errore da non fare.

**Non sostituisce il wipe.** Copre solo ciò che si è deciso di chiudere; tutto il resto, comprese le sessioni interrotte, i log e gli store effimeri, resta materia del wipe.

## Le chiusure che nessuno ha deciso

Una sessione può anche chiudersi senza che nessuno lo voglia, quando muore il terminale che la ospita. Il 2026-11-24 una scorciatoia di sistema che apriva un terminale elevato, creata da una sessione e premuta più volte, ha fatto chiudere a Windows Terminal tutte le schede insieme, quattro sessioni Claude e una Codex, e il wipe ne ha cancellato le trascrizioni in tre minuti (L-018 di un progetto istanziato). Da allora il wipe sposta in quarantena dopo ogni chiusura non canonica, e la procedura di recupero sta in `.claude/templates/agenti-terminale/recupero-dopo-crash.md`.

Ne discende una prescrizione che vale prima del danno. Una modifica che tocca il terminale o la shell condivisi da tutte le sessioni, cioè una scorciatoia di sistema, un'attività pianificata elevata, il profilo PowerShell, le impostazioni di Windows Terminal o una variabile d'ambiente di sistema, si prova con una scheda fittizia aperta accanto, per esempio un `ping -t 127.0.0.1`, e con nessuna sessione di lavoro attiva. Superata la prova la scheda fittizia è ancora viva; se si è chiusa, la modifica rompe i terminali e si toglie prima di aprire altro. La sessione che prepara la modifica non la prova su sé stessa: la consegna, la fa provare così e lo scrive nella voce del lavoro, perché è l'unica sessione che non può vedere la propria chiusura.
