# guardia-pubblicazione

<!-- readme-summary: Controlla prima del commit cartelle private, uscite di compilazione e artefatti da non pubblicare. -->

> Pacchetto opzionale. Impedisce che un documento riservato o un'uscita di compilazione entri in un commit, controllandolo prima di ogni consegna invece di affidarlo a una regola scritta. Nasce il 2026-11-04 in un progetto istanziato, su richiesta del proprietario, dopo che i due vincoli che questo strumento verifica erano stati enunciati in prosa e lui ha osservato che una regola in prosa non ferma un comando.

## Il problema

Un repository di progetto convive quasi sempre con materiale che non deve uscirne: documenti di governance, materiale di un cliente, note private, documenti prodotti che portano incorporato un marchio. La difesa ordinaria è per percorso, cioè una cartella ignorata da git, e funziona finché nessuno la tocca. Il guaio è che decade in silenzio e tutta insieme: basta una riga tolta da un `.gitignore`, o una cartella nuova che nessuno ha pensato di ignorare, e da quel momento ogni file di quella cartella è committabile senza che niente lo segnali.

La correzione a posteriori non è una riparazione. La storia di git non si dimentica: un contenuto rimosso in un commit successivo resta recuperabile da chiunque abbia accesso al remoto, quindi l'unica rimozione vera è la riscrittura della storia, che su un ramo condiviso è un'operazione che coinvolge tutti. L'unico momento in cui il problema si risolve davvero è prima del commit, ed è lì che questo controllo si mette.

Il secondo vincolo nasce insieme al primo e ha la stessa forma. Un generatore di siti statici scrive il sito compilato in una cartella, tipicamente `site/`, che è una copia dell'intero albero dei sorgenti: se non è ignorata, un comando abituale la committa, e se contiene la resa di un documento privato la pubblica. Dove il progetto tiene anche un censimento delle fonti, quella stessa cartella va esclusa dal censimento, altrimenti ogni ricostruzione del sito si presenta come qualche centinaio di documenti sorgente cambiati e il segnale di cambiamento smette di significare qualcosa.

## Che cosa verifica

Quattro cose, in ordine di quanto costa sbagliarle.

Le cartelle dichiarate private sono ignorate da git e non contengono file tracciati. È la chiave di volta: ogni altra protezione poggia su questo assunto, e questo è il solo controllo che lo verifica invece di presupporlo.

Le cartelle di uscita della compilazione sono ignorate e non tracciate.

Nessun artefatto documentale risulta tracciato fuori dal privato. Sono artefatti i formati impaginati, cioè `.docx`, `.pdf`, `.xlsx`, `.pptx` e simili, e le pagine HTML sopra una soglia di dimensione. La soglia è il punto fine: distingue una pagina di documentazione scritta a mano da un documento prodotto che porta incorporato un design system, e si regola dalla configurazione.

Le uscite di compilazione compaiono fra le esclusioni del censimento, dove un censimento esiste. La verifica prova gli schemi di esclusione contro un percorso campione invece di cercare il nome della cartella nel file: cercare il nome come sottostringa dichiara soddisfatta `site` perché il file contiene già una riga per `site-packages`, che è un'altra cosa e sta lì per un altro motivo.

## Che cosa non fa, e perché può stare in un repository tracciato

Non nomina nessun cliente, nessun fornitore e nessun nome proprio, e non legge il contenuto dei file: guarda collocazione, estensione e dimensione. È una scelta e non una limitazione, perché un controllo che cercasse termini riservati dovrebbe portarseli dentro, e sarebbe quindi il primo file da non pubblicare. Il controllo complementare che guarda il contenuto esiste già nel pacchetto `anonymization`, e tiene i propri termini in un file ignorato da git: i due si usano insieme.

Non corregge niente. Un riscontro si risolve spostando il file nel privato o ignorando la cartella, non allargando le esclusioni, e la decisione è di chi conosce il file.

## Uso

```
python tools/guardia-pubblicazione.py
python tools/guardia-pubblicazione.py --radice "percorso/di/un/altro/repository"
python tools/guardia-pubblicazione.py --autotest
```

Prende la radice come argomento perché il repository da proteggere non è sempre quello aperto nella sessione: il caso che ha fatto nascere il pacchetto riguardava un secondo progetto, dove il danno sarebbe stato peggiore.

Codici di uscita secondo il contratto del sistema: zero se non trova riscontri, uno se ne trova, due se non è in grado di calcolare l'esito, per esempio quando la radice non è un repository o git non è disponibile. La distinzione fra uno e due conta, perché un controllo che non ha potuto guardare non è un controllo passato.

L'autotest costruisce due repository finti in una cartella temporanea, uno pulito e uno con ogni difetto, e verifica che il primo passi e il secondo venga fermato. Si esegue insieme al controllo, non al posto suo: una guardia non provata scopre di non funzionare il giorno in cui avrebbe dovuto fermare qualcosa, e quel giorno il suo silenzio si legge come un via libera.

## Configurazione

Senza configurazione valgono i valori di difetto: private `_notes`, `knowledge` e `laboratorio`; uscite `site`, `_site`, `graphify-out` e `.cache`; soglia HTML 200.000 byte; esclusioni del censimento cercate in `_notes/.esclusi-censimento.txt`.

Un progetto che si discosta scrive `.guardia-pubblicazione.json` nella propria radice, con le chiavi `private`, `uscite`, `soglia_html` ed `esclusioni_censimento`. Il file dichiara il perimetro, quindi va tracciato: non contiene nulla di riservato, solo i nomi delle cartelle che lo sono.

## Istanziazione

Si copia `tools/guardia-pubblicazione.py` sotto `tools/` del progetto e si aggiunge la voce alla lista dei controlli di `chiudi-sessione`, due righe, una con `--autotest` e una senza. Senza l'aggancio il controllo esiste e non gira, che è la condizione in cui non protegge niente.

## Costo

Nessuna dipendenza oltre git e la libreria standard. Il controllo percorre l'elenco dei file tracciati una volta e interroga git sulle sole cartelle dichiarate, quindi il costo è di frazioni di secondo anche su un albero grande. Le chiamate a git hanno un tempo massimo e non leggono mai lo standard input, perché un controllo che gira prima di ogni commit non deve poter restare appeso.
