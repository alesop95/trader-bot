# Documenti personali: mai letti senza richiesta espressa

> Regola modulare, da caricare sempre. Nasce da un'istruzione vincolante dell'utente del 2026-10-06 in un progetto istanziato, dove un'ingestione di massa del materiale di studio stava passando all'OCR anche contratti, documenti d'identità e pratiche amministrative che stavano nelle stesse cartelle.

## Il vincolo

I documenti personali dell'utente non si leggono mai, a nessun livello, se non su sua richiesta espressa, data in quel momento e per quei documenti. Sono personali i documenti d'identità, i contratti, le pratiche fiscali e amministrative, le domande e le ricevute di borse di studio e di iscrizione, i certificati, le buste paga, i documenti sanitari, la corrispondenza privata e tutto ciò che riguarda persone diverse dall'utente.

Leggere comprende ogni passaggio che porti il contenuto fuori dal file: l'apertura da parte dell'agente, la conversione in testo, l'OCR, l'estrazione di metadati dal contenuto, la sintesi di un modello, anche economico, e la copia in una cache. Il nome del file e la sua posizione si possono usare solo per riconoscerlo ed escluderlo.

## Come si attua

L'esclusione si scrive negli strumenti, non nella memoria di chi li lancia. Ogni strumento che percorre una cartella dell'utente per indicizzare, convertire o sintetizzare legge un elenco locale di schemi di esclusione e salta i file che vi corrispondono, prima di aprirli. L'elenco vive in un file ignorato da git, perché gli schemi stessi possono rivelare dati personali, e lo strumento dichiara nel riepilogo quanti file ha escluso. Un'esclusione non si decide caso per caso durante una corsa: se un file personale sfugge agli schemi, si corregge l'elenco e si dichiara che cosa è sfuggito.

Se un documento personale è già stato letto, convertito o copiato prima che la regola esistesse, lo si dichiara all'utente con il solo nome e si chiede che cosa fare delle copie derivate. Non si apre per verificare.

## Che cosa non è un permesso

Una richiesta generica come "ingerisci tutto", "converti la cartella" o "leggi tutto ciò che è utile" non è una richiesta espressa per i documenti personali che la cartella contiene. Non lo è nemmeno il fatto che un documento stia in una cartella già autorizzata. Il permesso nomina i documenti.

## Gli strumenti che la attuano nel template

Sezione aggiunta il 2026-10-07. `doc-ingest.py` accetta `--esclusi` con un file di schemi, e `lavoro-a-lotti/tools/estratti-lotto.py` lo richiede. L'elenco di partenza è `.claude/templates/doc-ingest/esclusi-personali.esempio.txt`: cartelle di acquisti, fatture, ricevute, banca, fisco e salute, documenti di pagamento, dichiarazioni fiscali, buste paga, documenti d'identità, pratiche universitarie, certificati medici, chiavi di licenza. Gli schemi si confrontano con il percorso completo del file, e la ragione è un difetto trovato quel giorno: uno schema di cartella cerca un separatore prima del nome, e il percorso relativo di un file in una sottocartella di primo livello non lo ha, quindi l'esclusione falliva in silenzio proprio sulla cartella più ovvia. Un elenco di schemi si prova sempre su una cartella di prova che contiene un caso da escludere, prima di usarlo su un corpus.

Dal 2026-10-07, su richiesta del proprietario che la regola fosse robusta e non soltanto dichiarata, tre cose in più. La prima riguarda i dati bancari scritti in un file pubblicabile, che sono l'altra metà del problema: `anonymization/tools/Test-Anonymization.py` riconosce l'IBAN di qualunque paese anche a gruppi di quattro e in minuscolo, validato con la cifra di controllo modulo 97 e con la lunghezza del paese, e il numero di una carta di pagamento, validato con Luhn, con i prefissi e le lunghezze dei circuiti; prima riconosceva soltanto un IBAN italiano scritto attaccato e in maiuscolo, e nessuna carta. La seconda è l'elenco di esempio: i confini di parola sono scritti come «nessuna lettera o cifra accanto», perché il confine delle espressioni regolari considera il trattino basso parte della parola e lo schema dell'IBAN non trovava `coordinate_IBAN.pdf`, e si sono aggiunti conto corrente, carte, mutui, prestiti e rendiconti. La terza è la prova: entrambi gli strumenti hanno un `--autotest`, con casi positivi e negativi che differiscono per una sola proprietà, e `chiudi` lo esegue a ogni commit, sulle copie in `tools/` nei progetti e con `tools/test-documenti-personali.py` nel template, che controlla anche che questa regola esista e si dichiari da caricare sempre. Misura alla prima corsa: con i riconoscitori e l'elenco di prima le due prove falliscono in 8 casi su 17 e in 5 file su 21, con quelli nuovi in nessuno; sui file di testo versionati del template e di un progetto istanziato, 385 e 880, i riconoscitori nuovi non danno alcun falso allarme, dopo aver escluso le cifre lunghe attaccate che non sono carte, come gli identificativi di Discord.

Una regola che non si carica non protegge. Nel template sta in `.claude/rules/` e si carica da sé in ogni sessione; in un progetto istanziato esiste solo dopo l'allineamento dal template, e il 2026-10-07 un progetto che non era stato allineato non la caricava. Dopo ogni modifica a questa regola o agli strumenti che la attuano l'allineamento va quindi eseguito su tutti i progetti istanziati.
