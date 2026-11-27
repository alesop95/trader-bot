# analisi-codice

> Pacchetto con una skill di sistema. Dal 2026-11-26 la skill `analisi-codice` arriva in ogni progetto con l'allineamento, e gli strumenti si usano da `.claude/templates/analisi-codice/tools/` senza istanziarli, come per `craft-apps`. Serve a rispondere a una domanda su un sistema software, per esempio "a che cosa serve questo campo" o "perché un utente vede questi record", con un'analisi del codice su più livelli: dove è usato ogni oggetto coinvolto in tutti i repository che compongono il sistema, con il link permanente a file e riga, il commit che ha introdotto ogni riga e l'effetto per chi usa il sistema.

<!-- readme-summary: analisi d'impatto del codice su più repository, con mappa generata delle occorrenze, link permanenti a riga, commit introduttivi da git blame e pagine con il design system del progetto -->

## Da dove viene

Il metodo è nato il 2026-11-26 in un progetto istanziato che analizza un'istanza Odoo composta da 62 repository clonati da un Dockerfile, ed è stato generalizzato lo stesso giorno su richiesta del proprietario. La prima ricerca ha trovato in un override di `write` un comando dell'ORM[^1] che cancella il record invece di togliere il collegamento: un difetto che nessuna lettura di un solo file mostra, e che emerge solo seguendo il campo in tutti i punti in cui compare. Il pacchetto esiste perché quella lettura si ripeta uguale a ogni domanda.

## Il principio

Quando l'analisi scopre un oggetto, cioè un campo, un metodo, un gruppo, una regola di accesso, una vista, si cerca subito dove altro è usato in tutto il sistema, e lo si descrive su due piani. Il piano tecnico dice modulo, file, riga, commit che l'ha introdotta e meccanismo che la esegue. Il piano operativo dice che cosa vede o può fare chi usa il sistema. Ogni affermazione sul codice porta il link a file e riga al commit registrato, e ogni difetto porta il commit che l'ha introdotto, ricavato con `git blame` e non dedotto dal messaggio di commit.

## Gli strumenti

```
tools/sorgenti.py          scarica i repository del sistema in sorgenti/, dal file di composizione e dall'elenco della configurazione
tools/dove-usato.py        ogni occorrenza di un termine: tipo, livello, contesto, effetto, link a riga, commit introduttivo
tools/ricerca.py           nuova, mappa, controlla, genera: il ciclo di una ricerca, l'indice e i collegamenti sul Desktop
tools/documento-genera.py  dal Markdown alla pagina HTML con il design system dichiarato, sezioni comprimibili
tools/documento-estrai.py  il percorso inverso, usato dalla prova del giro chiuso fra testo e pagina
assets/documento.css       foglio dei documenti, letto dal generatore insieme ai token del design system
```

Si lanciano dalla radice del progetto, per percorso: `python .claude/templates/analisi-codice/tools/ricerca.py genera <nome>`. Un progetto che li modifica li copia in `tools/` e da quel momento `ricerca.py` preferisce la copia del progetto. I controlli che `ricerca.py` esegue prima di generare vengono dagli strumenti tipografici e anti-slop del template, che cerca prima in `tools/` del progetto e poi nei pacchetti del template.

## La configurazione

Il progetto dichiara il sistema in `analisi-codice.json` nella radice, dal modello `analisi-codice.esempio.json`. Il blocco `sorgenti` dice da dove si ricava l'elenco dei repository: `composizione` è il file, di solito un Dockerfile, da cui si leggono le righe `git clone -b <ramo> <url>`, e `repository` aggiunge sorgenti che quel file non nomina, come il core del framework. `famiglie` assegna una famiglia per proprietario GitHub, `facoltative` elenca le famiglie grandi che si scaricano solo con `--con`, e `storia_completa` i repository di cui serve il blame, che si clonano interi mentre gli altri si clonano a profondità uno. Le chiavi `sistema`, `descrizione` e `organizzazione` finiscono nelle intestazioni delle pagine, e `cartella_desktop`, se c'è, crea sul Desktop una cartella con un collegamento per pagina.

`sorgenti/` contiene il codice di altri e va ignorato da git. GitHub si raggiunge con `gh`, che fa anche da gestore delle credenziali di git: i repository privati si scaricano con l'account attivo, e quelli non accessibili si registrano come tali nel manifesto. Ogni conclusione del tipo "compare solo in" vale quindi sui sorgenti accessibili, e va scritta così.

## Una ricerca, una pagina

Ogni ricerca ha due sorgenti, `analisi.md` scritta da chi analizza e `mappa.md` generata da `dove-usato.py`, ma una pagina sola, `analisi.html`: la mappa vi entra come macro-sezione «Mappa delle occorrenze», prima delle Note, con un riepilogo per termine e un sottolivello per termine. Così chi legge un difetto trova nella stessa pagina tutti i punti in cui compare l'oggetto, senza passare da un file all'altro; la scelta è del 2026-11-26, quando il proprietario ha chiesto perché analisi e mappa fossero due file.

L'impatto operativo è la prima cosa che la pagina mostra. L'analisi ha in testa, dopo la risposta, la sezione «Impatto operativo», con chi è toccato, che cosa vede o può fare e da quale riga viene. E ogni termine della mappa porta l'impatto operativo in un riquadro sopra le sue occorrenze, scritto da chi analizza nella chiave `impatti` di `ricerca.json`, perché dal codice si deduce il tipo di un'occorrenza e non che cosa cambia per chi usa il sistema: `ricerca.py` rifiuta di generare se un termine non ce l'ha.

## Le pagine

Le pagine si generano con il design system che il progetto dichiara in `_notes/.tema.txt`, con caratteri e stile incorporati, quindi si aprono e si inviano come file singoli. Senza dichiarazione il generatore lo dice nella pagina invece di inventare uno stile. La prosa occupa tutta la larghezza del contenitore, e ogni titolo `##` e `###` è comprimibile con il più/meno a destra, come il componente Accordion del design system aziendale: la pagina si apre con le sezioni chiuse e compattate, cioè con poco spazio fra l'una e l'altra e titoli ridotti, così che l'indice dell'analisi stia in una schermata; ha i comandi Espandi tutto e Comprimi tutto in cima ed esce intera in stampa. Un sottolivello si scrive quindi come `###`, non come paragrafo che comincia con il suo nome.

## I limiti dichiarati

La ricerca è testuale con confini di parola sulle estensioni `.py`, `.xml`, `.csv`, `.js` e sulle traduzioni `it.po`, quindi non trova una chiamata costruita a runtime e non risolve l'ereditarietà dei modelli. La classificazione di tipo, livello ed effetto conosce gli oggetti di Odoo; su un altro stack le occorrenze restano classificate come uso in codice, definizione o dato, mentre link, contesto e commit valgono uguali. I sorgenti si leggono da GitHub. Su Windows un repository con nomi di file non ammessi si estrae da `git archive` saltando quei file, e lo strumento lo dichiara nell'uscita.

[^1]: *ORM*, Object-Relational Mapping: lo strato che traduce le scritture sui campi in istruzioni SQL.
