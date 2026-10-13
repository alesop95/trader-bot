# verifica-link

<!-- readme-summary: ogni collegamento scritto nei documenti del progetto confrontato con il registro delle fonti, con il perimetro dichiarato -->

Pacchetto per i progetti che tengono un registro delle fonti e scrivono collegamenti nei propri documenti. Contiene un solo strumento, `verifica-link-progetto.py`, che risponde alla domanda che il registro da solo non sa porsi: quali indirizzi scritti nei documenti del progetto non stanno in nessun elenco. Il registro sa che cosa è stato letto; nessuno, senza questo strumento, sa che cosa il progetto cita.

## Perché serve

Il caso che lo ha fatto nascere vale la pena di raccontarlo, perché il difetto che presidia non produce alcun errore. Il 2026-10-06, in un progetto istanziato da questo template, il registro delle fonti dichiarava lette tutte le fonti, e la dichiarazione era stata verificata con cura: il registro, il residuo di un corpus di oltre duemila indirizzi, le consegne del proprietario. Poi il proprietario ha trovato un post di Reddit mai letto, incollato come collegamento breve di condivisione dentro un file di testo di un sottoprogetto. Il post non era in nessuno dei tre conti, perché nessuno dei tre guardava i collegamenti scritti nei documenti del progetto stesso, cioè handoff, note, studi e decisioni. La dichiarazione era vera per il perimetro dello strumento che la misurava ed era falsa per il progetto.

La misura che ne è seguita lo mostra in numeri. La prima corsa di questo strumento sul progetto ha riportato 1268 indirizzi non classificati. Di questi, 1124 erano le immagini di un manifesto scaricato che enumera una fonte già registrata, 15 sono caduti per regole generali (identificativi di YouTube a undici caratteri, codici brevi di Reddit a dieci, nomi riservati alla documentazione, modelli di formato), 73 erano non fonti con un motivo, cioè endpoint di strumenti, pagine di scaricamento e il repository stesso. Restavano 56 indirizzi veri, di cui 54 fonti mai registrate e 2 registrate in un'altra forma. Lette, hanno aperto 13 lacune in ciò che il progetto affermava.

Il principio generale, che vale oltre i collegamenti, sta nella norma `.claude/skills/fonti-non-recuperabili/RIFERIMENTO.md`: una dichiarazione di completezza vale per il perimetro dello strumento che la misura, e va scritta con quel perimetro. Questo pacchetto è il presidio di quel principio per una famiglia precisa di fonti, quelle che il progetto cita senza averle registrate.

## Che cosa fa

Percorre i file tracciati con le estensioni di testo e di codice e le cartelle non tracciate che la configurazione dichiara, come `_notes/`, saltando le sottocartelle indicate (testi di terzi scaricati, lotti, cloni, output compilato). Esclude i registri stessi, i prefissi tracciati dichiarati, tipicamente i modelli del template, e il proprio sorgente, le cui prove scrivono indirizzi apposta. Estrae ogni indirizzo e lo riduce a una chiave che fa coincidere le forme dello stesso contenuto: un post di Reddit diventa il suo identificativo, un video di YouTube il suo, i parametri di tracciamento e i prefissi come `www.` e `old.` si tolgono. Risolve i collegamenti brevi di Reddit, nella forma `/r/<sub>/s/<codice>`, seguendo il reindirizzamento e, se la pagina rifiuta, attraverso l'archivio pubblico Arctic Shift, e tiene le risoluzioni in una cache.

Poi confronta ogni chiave con i registri e con l'elenco motivato delle non fonti. Un indirizzo che non sta in nessuno dei due è non classificato, e con `--check` lo strumento esce con codice 1 elencandolo insieme ai file che lo citano.

Non conta come indirizzi tre forme che uno strumento scrive senza che indichino una pagina. La prima è un modello di formato, riconosciuto da un `%` che non introduce una codifica valida, da una graffa o da un parametro finale vuoto come `?url=`. La seconda è un nome riservato alla documentazione dalle RFC 2606 e 6761, cioè `example.org` e i domini di primo livello `.example`, `.test` e `.invalid`, che è la forma in cui le prove degli strumenti dovrebbero scrivere i propri esempi. La terza è un video con un identificativo di lunghezza diversa da undici caratteri. Le tre regole sono di principio e non di elenco, ed è ciò che le rende durevoli: nel progetto d'origine hanno tolto in una volta il rumore che altrimenti sarebbe finito, una voce alla volta, nell'elenco delle non fonti.

A ogni corsa lo strumento stampa il perimetro, cioè quanti file ha percorso, quanti tracciati e quanti dalle cartelle non tracciate, e quanti indirizzi noti ha letto da quanti registri. La riga esiste per lo stesso principio da cui nasce il pacchetto: chi riporta che tutti i collegamenti sono classificati la riporta con il perimetro accanto.

## L'elenco delle non fonti, e perché le voci hanno un ambito

Non ogni indirizzo citato è una fonte: l'endpoint che uno strumento chiama, la pagina da cui si scarica un programma, il repository stesso. Questi stanno in un file JSON con tre chiavi, `voci` per gli indirizzi esatti, `prefissi` per i prefissi di chiave e `file_dati` per i manifesti scaricati che enumerano il contenuto di una fonte già registrata, e ogni voce porta il motivo, perché un'esclusione senza motivo non si distingue da una dimenticanza.

Una voce può dichiarare `solo_in`, l'elenco dei file in cui vale. Serve agli indirizzi fittizi che le prove di uno strumento scrivono nel proprio sorgente: escluderli ovunque nasconderebbe lo stesso indirizzo il giorno in cui qualcuno lo scrive in un documento come fonte vera, ed è esattamente il genere di esclusione che passa inosservata. Con l'ambito, il fittizio è escluso dentro lo strumento e torna non classificato fuori.

## Che cosa istanzia

Lo strumento in `tools/`, la configurazione in `tools/verifica-link-progetto.json` a partire dall'esempio commentato, e l'elenco delle non fonti dove la configurazione lo dichiara, di solito `_notes/fonti/link-non-fonti.json`. Python 3, sola libreria standard. La rete serve soltanto per risolvere i collegamenti brevi nuovi.

```
cp .claude/templates/verifica-link/tools/verifica-link-progetto.py tools/
cp .claude/templates/verifica-link/verifica-link-progetto.esempio.json tools/verifica-link-progetto.json
cp .claude/templates/verifica-link/link-non-fonti.esempio.json _notes/fonti/link-non-fonti.json
```

La configurazione si adatta prima della prima corsa, e le chiavi da guardare sono due. `registri_testo` e `registri_json` dicono con che cosa si confronta: un registro dimenticato qui fa comparire come non classificate fonti già lette, che è un errore rumoroso e si corregge subito. `cartelle_non_tracciate` dice dove il progetto scrive senza versionare: una cartella dimenticata qui restringe il perimetro in silenzio, che è il difetto da cui il pacchetto nasce, e conviene rileggerla con la stessa cura. Le chiavi con il trattino basso sono commenti; una chiave sconosciuta senza trattino basso fa fallire la corsa, perché un refuso nel nome di una chiave non diventi un perimetro più stretto.

## Come si usa

```
python tools/verifica-link-progetto.py --prova
python tools/verifica-link-progetto.py
python tools/verifica-link-progetto.py --json _notes/link-non-classificati.json
python tools/verifica-link-progetto.py --check --senza-rete
```

La prima corsa su un progetto esistente produce quasi sempre un numero alto, e il numero è in gran parte rumore: manifesti scaricati, esempi delle prove, endpoint. Il riepilogo per host e l'uscita in JSON servono a separarlo dai collegamenti veri prima di leggerne uno. Il rumore si toglie con una regola quando ha una forma riconoscibile, con una voce motivata quando non ce l'ha, e i collegamenti veri si leggono e si registrano: è lì che stanno le lacune.

Quando il pacchetto è istanziato, `chiudi` lo esegue fra i controlli con `--check --senza-rete`, riconoscendolo dalla presenza della configurazione. Il controllo è senza rete perché una verifica prima del commit non deve dipendere dalla rete: un collegamento breve nuovo lo fa fallire finché qualcuno non lancia lo strumento senza quell'opzione, che lo risolve e lo scrive nella cache.

## Le prove

`--prova` esegue trentasette prove interne. Le prime venticinque fissano la normalizzazione e falliscono sulla versione dello strumento precedente la correzione del rumore nel progetto d'origine. Le altre provano la configurazione, cioè il rifiuto di una configurazione senza registri e di una chiave sconosciuta, e il perimetro su un progetto costruito in una cartella temporanea e percorso senza git: due forme dello stesso indirizzo registrato contano come registrate, un indirizzo mai registrato si trova sia in un documento sia in una cartella non tracciata, una sottocartella saltata e un prefisso escluso non si percorrono, lo strumento non legge il proprio sorgente, e una non fonte con ambito altrove resta non classificata nel documento.

## Che cosa non fa

Non dice se una fonte sia stata letta: dice se è registrata. Che una voce del registro corrisponda a una lettura vera è materia della norma sulle fonti non recuperabili e del modo in cui il registro si scrive. Non percorre i file binari né i documenti d'ufficio, e non vede un collegamento scritto senza schema, come un dominio nudo in prosa. Ciascuno di questi è un confine del perimetro, e va nominato quando si riporta l'esito.
