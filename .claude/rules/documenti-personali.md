# Documenti personali: mai letti senza richiesta espressa

> Regola modulare, da caricare sempre. Nasce da un'istruzione vincolante dell'utente del 2026-10-06 in un progetto istanziato, dove un'ingestione di massa del materiale di studio stava passando all'OCR anche contratti, documenti d'identità e pratiche amministrative che stavano nelle stesse cartelle. I casi osservati che hanno prodotto queste prescrizioni, con le misure e le date, stanno in `.claude/norme/documenti-personali.md`: quel file non si carica all'avvio di una sessione e non serve per applicare la regola, serve a chi deve estenderla o rimetterla in discussione.

## Il vincolo

I documenti personali dell'utente non si leggono mai, a nessun livello, se non su sua richiesta espressa, data in quel momento e per quei documenti. Sono personali i documenti d'identità, i contratti, le pratiche fiscali e amministrative, le domande e le ricevute di borse di studio e di iscrizione, i certificati, le buste paga, i documenti sanitari, la corrispondenza privata e tutto ciò che riguarda persone diverse dall'utente.

Leggere comprende ogni passaggio che porti il contenuto fuori dal file: l'apertura da parte dell'agente, la conversione in testo, l'OCR, l'estrazione di metadati dal contenuto, la sintesi di un modello, anche economico, e la copia in una cache. Il nome del file e la sua posizione si possono usare solo per riconoscerlo ed escluderlo.

## Come si attua

L'esclusione si scrive negli strumenti, non nella memoria di chi li lancia. Ogni strumento che percorre una cartella dell'utente per indicizzare, convertire o sintetizzare legge un elenco locale di schemi di esclusione e salta i file che vi corrispondono, prima di aprirli. L'elenco vive in un file ignorato da git, perché gli schemi stessi possono rivelare dati personali, e lo strumento dichiara nel riepilogo quanti file ha escluso. Un'esclusione non si decide caso per caso durante una corsa: se un file personale sfugge agli schemi, si corregge l'elenco e si dichiara che cosa è sfuggito.

Se un documento personale è già stato letto, convertito o copiato prima che la regola esistesse, lo si dichiara all'utente con il solo nome e si chiede che cosa fare delle copie derivate. Non si apre per verificare.

## Che cosa non è un permesso

Una richiesta generica come "ingerisci tutto", "converti la cartella" o "leggi tutto ciò che è utile" non è una richiesta espressa per i documenti personali che la cartella contiene. Non lo è nemmeno il fatto che un documento stia in una cartella già autorizzata. Il permesso nomina i documenti.

## Gli strumenti che la attuano

`doc-ingest.py` accetta `--esclusi` con un file di schemi e `lavoro-a-lotti/tools/estratti-lotto.py` lo richiede; l'elenco di partenza è `.claude/templates/doc-ingest/esclusi-personali.esempio.txt`, che copre cartelle di acquisti, fatture, ricevute, banca, fisco e salute, documenti d'identità, pratiche universitarie e certificati medici. Gli schemi si confrontano con il percorso completo del file, e un elenco di schemi si prova sempre su una cartella di prova che contiene un caso da escludere, prima di usarlo su un corpus. L'altra metà del problema sono i dati identificanti scritti in un file pubblicabile, che `anonymization/tools/Test-Anonymization.py` riconosce validando l'IBAN con la cifra di controllo modulo 97 e il numero di una carta con Luhn. Entrambi gli strumenti hanno un `--autotest` che `chiudi` esegue a ogni commit, nel template attraverso `.claude/templates/tools/test-documenti-personali.py`, che controlla anche che questa regola esista e si dichiari da caricare sempre.

Una regola che non si carica non protegge: dopo ogni modifica a questa regola o agli strumenti che la attuano l'allineamento va eseguito su tutti i progetti istanziati.
