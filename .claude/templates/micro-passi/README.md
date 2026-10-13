# Pacchetto: micro-passi

> Modalità di interazione a botta e risposta, da attivare quando l'utente ha lo schermo davanti e deve eseguire. Non sostituisce `interaction-style.md`, lo restringe per la durata di una sequenza operativa.

<!-- readme-summary: un passo per volta con l'output atteso, e il dettaglio nei documenti -->

## A che serve

Il modo ordinario in cui un agente risponde, cioè consegnare il risultato con il ragionamento che lo giustifica, funziona bene quando chi legge sta decidendo. Funziona male quando chi legge sta **eseguendo**: una persona con il terminale aperto o il browser su una schermata di prova deve sapere che cosa fare adesso e quale esito riportare, e ogni paragrafo in più fra lei e il gesto è tempo in cui deve cercare l'istruzione dentro la spiegazione.

Il pacchetto codifica quella restrizione come modalità selezionabile, perché l'esperienza da cui nasce ha mostrato due cose. La prima è che la modalità serve davvero: un giro di verifica manuale fatto a micro-passi si conclude in una frazione del tempo. La seconda è che **si sbaglia in entrambe le direzioni**, e la seconda direzione è meno ovvia della prima.

## La regola

Durante una sequenza operativa si consegna **un passo per volta**: che cosa fare, e quale output serve indietro. Si attende l'esito e si consegna il passo successivo. Non si consegnano tre passi insieme sperando che chi legge li esegua in ordine, perché un esito intermedio può cambiare i due successivi, e quando cambia la persona ha già fatto il lavoro sbagliato.

**Ogni passo porta però quanto basta a deciderlo.** Se il passo è un gesto, bastano il gesto e l'output atteso. Se il passo è una scelta, servono le alternative, il rischio di ciascuna e una raccomandazione: una domanda con due opzioni e nessun criterio non è un micro-passo, è un passo impossibile. Questa precisazione non è teorica. Nel progetto da cui il pacchetto nasce, la prima stesura della regola diceva "senza spiegazione estesa", l'agente l'ha letta come "senza spiegazione", e il risultato è stato una scelta fra A e B consegnata senza dire che cosa distinguesse l'una dall'altra. L'utente ha risposto, testualmente, che si era passati dal chiacchierare troppo al non spiegare niente.

Quello che si toglie è il contorno: l'inquadramento architetturale, la cronaca di come ci si è arrivati, le alternative scartate. Quello che non si toglie è il contenuto della decisione.

## Dove va a finire quello che non si dice

Il pacchetto funziona solo in coppia con una disciplina di scrittura su disco, altrimenti non comprime la comunicazione, perde informazione. La spiegazione non sparisce: **cambia destinazione**. Il perché di una scelta, le misure prese, le trappole incontrate e le vie scartate si scrivono nei documenti versionati nello stesso giro in cui nascono, come prescrive `chat-non-e-memoria.md`; in sessione resta l'istruzione eseguibile.

Detto altrimenti, questa modalità **rafforza** la regola sulla persistenza invece di indebolirla, perché sposta ancora più contenuto dal volatile al durevole. Adottarla senza quella regola produce un progetto in cui nessuno ha mai scritto perché le cose sono come sono.

## Quando NON si applica

Fuori dalle sequenze operative lo stile discorsivo resta quello di `interaction-style.md`. In particolare non si applica quando si sta ragionando su un disegno, quando si riporta l'esito di un'indagine, quando si spiega un difetto trovato, e quando si risponde a una domanda che non è un passo di una procedura. La modalità governa il **come si lavora insieme a una persona che esegue**, non il registro della documentazione né quello delle risposte di merito.

## Come si attiva

È una decisione d'uso, non un file da installare: si registra come ADR nel progetto che la adotta, così la sessione successiva la trova scritta invece di doverla dedurre dal tono. Il pacchetto non porta strumenti e non pesa sul budget degli instruction file.

Formula consigliata per l'ADR: durante una sequenza operativa si consegna un micro-passo per volta con l'output atteso; ogni passo porta quanto basta a deciderlo, e se è una scelta porta le alternative con il rischio di ciascuna e una raccomandazione; il dettaglio va nei documenti versionati nello stesso giro.
