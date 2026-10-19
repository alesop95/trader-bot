---
generated-from-commit: <hash del commit di prima scrittura>
generated-from-branch: <branch>
generated-date: <YYYY-MM-DD>
covers-paths:
  - <glob delle aree descritte>
last-verified-commit: <hash dell'ultima verifica o aggiornamento>
---

# Design e sicurezza applicativa

> Popolare leggendo il codice attuale. I diagrammi referenziati vivono in `diagrams/` in corrispondenza uno a uno con i componenti descritti (sezione 7).

## Paradigmi di software design

<pattern architetturali adottati, separazione delle responsabilità, contratti tra moduli>

> Da verificare popolando, se il progetto normalizza le letture dal database (un parser che riempie i valori predefiniti e traduce le forme vecchie): la regola "ogni lettura passa dal parser" ha un'eccezione strutturale. Una lettura il cui risultato viene poi riscritto per intero da un ruolo che le regole di sicurezza limitano a poche chiavi non deve essere normalizzata, o deve restituire il documento identico: altrimenti la riscrittura porta chiavi che quel ruolo non può toccare, e la scrittura viene rifiutata senza che nessuna prova lo veda, perché le prove delle regole non passano da quel flusso e quelle del flusso fingono la scrittura. Salita il 2026-10-19 da un progetto istanziato, dove l'assegnazione di un tavolo da parte del ruolo che gestisce la sala sarebbe stata rifiutata; la ragione va scritta accanto alla lettura lasciata grezza.

> Da verificare popolando, due regole d'interfaccia salite il 2026-10-19 da un progetto istanziato.
>
> Un'azione che salva da sola deve dire com'è andata, e a un errore deve rimettere a video il valore che il database ha davvero. Un salvataggio silenzioso è indistinguibile da un salvataggio non avvenuto, e un valore lasciato a schermo dopo un rifiuto afferma un dato falso. Nel caso osservato i campi in cui si scrive tenevano un pulsante di salvataggio e quelli a scelta secca si salvavano subito: l'uniformità utile non è stata un gesto unico ma un'informazione unica, cioè che ogni campo dica se è salvato, e il censimento dei controlli ha trovato due salvataggi che a un errore tornavano indietro senza una parola.
>
> Un interruttore globale promette qualcosa in ogni punto in cui si vede. Un comando "mostra spiegazioni" che accendeva riquadri in quattro schede su dieci è stato letto, dal vivo, come una funzione rotta: se un interruttore è globale, ogni schermata che lo mostra deve rispondergli.

## Sicurezza applicativa

<gestione di autenticazione e autorizzazione, validazione input, gestione dei segreti, superfici esposte e relative mitigazioni>

## Dati personali: la cancellazione

<che cosa il progetto conserva di una persona, dove, per quanto tempo, e la procedura che lo cancella su richiesta>

> Da verificare popolando, due cose salite il 2026-10-19 da un progetto istanziato, dove la "cancellazione completa" di un invitato le mancava entrambe.
>
> Un sistema di accesso che crea un'identità al primo accesso, per esempio i gettoni personalizzati di Firebase Authentication, lascia un utente con l'identificativo del gettone anche quando i dati applicativi sono cancellati. Se l'identificativo è il nome della persona, come lì, quell'utente è un dato personale, e la procedura di cancellazione deve toglierlo; un utente assente, cioè una persona mai entrata, non è un errore.
>
> La procedura di cancellazione si prova contro l'elenco delle raccolte di dati, ricavando entrambi gli elenchi dal codice, le raccolte dalle regole di sicurezza e quelle cancellate dal sorgente della procedura stessa, con fra i due un elenco di eccezioni ciascuna con la sua ragione. Una raccolta nuova fa cadere la prova finché qualcuno non decide se contiene dati della persona. È la prova di completezza di una corrispondenza descritta in `prove-che-misurano`, applicata al caso in cui la dimenticanza costa di più.

## Diagrammi

| Diagramma | Sorgente | Componenti rappresentati |
|---|---|---|
| <nome>.svg | <nome>.mmd | <elenco; corrispondenza uno a uno col codice> |
