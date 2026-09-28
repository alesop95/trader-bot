# Pacchetto opzionale: md-unwrap

> Formatter Markdown a diff minimo che srotola i paragrafi hard-wrapped: il testo di ogni blocco torna su una riga sorgente unica, senza a capo manuali a metà frase. È l'attuazione meccanica della convenzione di formattazione dei file `.md` descritta nella regola `.claude/rules/interaction-style.md`, sezione "Formattazione dei file Markdown". Non normalizza nient'altro: marcatori di lista, tabelle, stili di titolo, escaping e ordine restano esattamente come sono.

## Il problema e il perimetro della soluzione

Un file Markdown scritto con l'a capo manuale a colonna fissa, tipicamente a settanta o ottanta caratteri, produce sorgenti in cui una frase è spezzata su tre o quattro righe. La resa a video non cambia, perché il renderer tratta l'a capo singolo come uno spazio, ma il sorgente diventa ostile a tutto ciò che lavora per riga: un diff git segna come modificate righe che nessuno ha toccato, perché la riscrittura di una parola a inizio paragrafo ri-avvolge tutte le righe successive; una ricerca testuale per frase non trova nulla, perché la frase è interrotta da un newline; una modifica puntuale richiede di rifloware a mano il resto del paragrafo. Con i paragrafi su riga unica il diff torna a segnare esattamente i paragrafi cambiati, la ricerca per frase funziona e l'avvolgimento a video resta compito dell'editor, che è il posto giusto in cui deciderlo.

Lo strumento fa una cosa sola: unisce le righe di continuazione interne a un blocco di testo, inserendo un singolo spazio tra i pezzi e togliendo l'indentazione di continuazione. I blocchi di testo sono i paragrafi, le voci di elenco puntato e numerato, e le righe di continuazione dentro una citazione, dove il prefisso `>` della prima riga viene conservato e quello delle righe assorbite scompare insieme all'a capo. Tutto il resto è fuori perimetro per costruzione: se una modifica non è "togliere un a capo interno a un blocco di testo", lo strumento non la fa.

Ciò che resta intatto è un elenco vincolante, non una lista di buone intenzioni: le righe vuote che separano i blocchi, i titoli ATX[^1] e Setext[^2], le linee orizzontali, il front matter[^3] YAML o TOML in testa al file, i blocchi di codice recintati e quelli indentati di quattro spazi, le tabelle GFM[^4] riga per riga e senza riallineamento, i blocchi HTML, le definizioni di link di riferimento, le interruzioni di riga intenzionali marcate da due spazi finali o da un backslash, l'indentazione che definisce l'annidamento di una lista, e per ogni file la sua fine riga (CRLF[^5] o LF[^6]), la presenza o assenza del newline finale e l'eventuale BOM[^7].

## Come si disambigua ciò che è ambiguo

Il cuore della correttezza sta in tre punti dove la stessa sequenza di caratteri significa cose diverse a seconda del contesto. Questa sezione descrive le decisioni prese, perché sono verificabili leggendo il codice in `tools/md-unwrap.py` e sono il punto in cui un dubbio va risolto guardando qui invece di indovinare.

Il primo punto è la sequenza `---`, che può essere una linea orizzontale, il sottolineato di un titolo Setext di secondo livello, o il delimitatore del front matter. La disambiguazione è posizionale e segue tre regole in ordine. Se `---` (oppure `+++`) è la prima riga del file e più avanti esiste una riga di chiusura corrispondente (`---` o `...` per lo YAML, `+++` per il TOML), tutto il tratto fino alla chiusura inclusa è front matter e viene emesso verbatim. Se `---` compare come riga di continuazione immediatamente dopo una riga di testo, senza riga vuota in mezzo, è un sottolineato Setext: il blocco di testo che lo precede è un titolo, quindi non viene unito e viene lasciato intatto insieme al sottolineato. In ogni altra posizione, cioè dopo una riga vuota o all'inizio di un blocco, è una linea orizzontale ed è emessa verbatim come riga a sé. La stessa logica di continuazione vale per `===`, che esiste solo come sottolineato Setext, e per le varianti `***`, `___` e `- - -` della linea orizzontale, riconosciute prima dei marcatori di lista così che `- - -` non venga confuso con una voce di elenco.

Una precisazione onesta sul front matter: la regola "prima riga del file più chiusura corrispondente" è la stessa euristica adottata dagli strumenti dell'ecosistema (Prettier, remark-frontmatter), e come loro tratta un file che inizia con una linea orizzontale seguita più avanti da un'altra `---` come se il tratto in mezzo fosse front matter. La conseguenza non è un danno ma una rinuncia: quel tratto viene emesso verbatim, quindi non viene srotolato. Lo strumento non corrompe il file, si limita a non toccarlo dove non è sicuro.

Il secondo punto è la chiusura di un blocco di codice recintato. L'apertura è una riga che comincia, dopo un'indentazione fino a tre spazi relativa al contenitore, con almeno tre backtick o almeno tre tilde; per i backtick l'apertura è valida solo se la info string che segue non contiene a sua volta un backtick, che è la regola CommonMark[^8] e serve a non confondere un testo che inizia con dei backtick con un vero recinto. La chiusura è una riga composta soltanto dallo stesso carattere dell'apertura, ripetuto un numero di volte maggiore o uguale a quello di apertura, seguito solo da spazi facoltativi. Da qui seguono i due comportamenti che contano: un recinto aperto con quattro backtick non viene chiuso da una riga di tre backtick al suo interno, e una riga di tre backtick trovata dentro un recinto di tilde è contenuto, non chiusura. Se il file finisce senza chiusura, il recinto si considera chiuso a fine documento e il suo contenuto resta comunque verbatim. Dentro una citazione la catena di marcatori `>` viene rimossa prima di applicare le stesse regole, così un recinto scritto dentro una citazione viene riconosciuto e il suo contenuto non viene mai unito.

Il terzo punto è l'indentazione di quattro spazi, che a inizio blocco significa blocco di codice indentato e come riga di continuazione significa semplicemente testo indentato. La distinzione segue CommonMark: un blocco di codice indentato non può interrompere un paragrafo, quindi una riga indentata che segue direttamente una riga di testo è continuazione e viene unita, mentre la stessa riga dopo una riga vuota è codice e resta verbatim. La soglia non è assoluta ma relativa al contenitore: dentro una voce di elenco il cui contenuto comincia a colonna due, il codice indentato comincia a colonna sei, e una riga a colonna quattro è invece una lista annidata. Per questo lo scanner tiene una pila delle voci di elenco aperte, con l'indentazione del marcatore e quella del contenuto, e la aggiorna a ogni inizio di blocco.

Restano due decisioni deliberatamente conservative. Le righe che sembrano una riga separatrice di tabella e i sottolineati Setext cambiano la natura del blocco che li precede: quando lo scanner ne incontra uno, il blocco appena raccolto viene emesso verbatim invece di essere unito, perché unirlo cambierebbe l'intestazione della tabella o il testo del titolo. E le definizioni di link di riferimento restano righe a sé, insieme all'eventuale riga di titolo o di URL che le completa, perché assorbirle in un paragrafo le invaliderebbe come definizioni.

Una terza categoria di prudenza riguarda i code span inline, e viene dal primo file che l'oracolo ha bocciato in tutto il corpus. Un code span si apre con una sequenza di backtick e si chiude con una sequenza della stessa lunghezza esatta, e nulla vieta che apertura e chiusura stiano su righe diverse: capita quando un blocco di configurazione viene scritto con un solo backtick invece di un recinto. Unire quelle righe cambia il contenuto reso, perché CommonMark normalizza lo spazio ai bordi di un code span e un `<code> CHIAVE=valore` diventa `<code>CHIAVE=valore`. Quando un code span attraversa un a capo, quindi, il paragrafo intero si emette verbatim: l'estensione da guardare è il paragrafo, perché un code span vive dentro un solo blocco. Una sequenza di backtick che non si chiude mai non è invece un problema, perché per CommonMark è testo letterale, e quei paragrafi si uniscono normalmente.

Su quest'ultima categoria serve una distinzione che la prima versione dello strumento non faceva, ed è emersa applicandolo ai file reali di questo repository. Una riga `[etichetta]: resto` è una definizione di link solo se il resto ha la forma di una destinazione, cioè un singolo token senza spazi (o fra parentesi angolari) con un titolo facoltativo tra virgolette; è il caso di `[rif]: https://example.com/pagina`. Se invece il resto è prosa, come in `[^2]: *OAuth*, Open Authorization - protocollo di autorizzazione con cui...`, quella riga non è una definizione di link ma una nota a piè di pagina, o più in generale testo etichettato, e si comporta come una voce di elenco: assorbe le proprie righe di continuazione conservando il prefisso `[^2]: `. Senza questa distinzione le note a piè di pagina restavano spezzate a metà, che su documentazione dove gli acronimi si spiegano in nota, come impone la regola di stile del sistema, è proprio il caso più frequente. La sicurezza della distinzione poggia sul fatto che una prosa dopo `[etichetta]:` non è comunque una definizione di link valida per CommonMark, quindi unirla non cambia il rendering, e l'oracolo lo verifica su ogni file.

## L'oracolo di correttezza

La garanzia che sia stato tolto solo il wrap, e non cambiato il significato, non poggia sulla fiducia nello scanner ma su due verifiche eseguite su ogni file prima di scriverlo.

La prima è un'invariante interna, sempre attiva e a costo zero: rimossi gli spazi bianchi e i marcatori di citazione a inizio riga, che l'unione di una citazione assorbe per definizione, il flusso dei caratteri dell'output deve essere identico a quello dell'input. Questo intercetta immediatamente qualsiasi perdita, duplicazione o alterazione di contenuto, che è la classe di guasto peggiore.

La seconda è l'oracolo di rendering, attivo quando `markdown-it-py` è importabile: l'originale e l'output vengono resi in HTML con un parser CommonMark con le estensioni GFM di tabella e strikethrough, e i due HTML vengono confrontati dopo aver normalizzato lo spazio bianco, così che un soft break reso come newline e uno spazio risultino equivalenti. Se il rendering normalizzato differisce, il file non viene scritto e viene segnalato come errore con il motivo. È questo il criterio che distingue "ho tolto il wrap" da "ho cambiato la struttura del documento": la struttura HTML, cioè la sequenza dei tag, è esattamente ciò che la normalizzazione dello spazio bianco non maschera.

L'oracolo si governa con `--oracle`: `auto` lo usa se disponibile e si limita all'invariante interna altrimenti, `require` pretende che sia disponibile e fallisce subito se non lo è, `off` lo disattiva lasciando la sola invariante. Per una passata su molti progetti la modalità consigliata è `require`, così che nessun file venga scritto senza la verifica più forte. L'installazione della dipendenza è la sola riga `pip install markdown-it-py`, ed è una dipendenza di sviluppo: lo strumento funziona senza, con una garanzia più debole.

A queste due verifiche si aggiunge il controllo di idempotenza: prima di scrivere, lo strumento ri-applica la trasformazione al proprio output e pretende che non cambi nulla. Una seconda corsa su un file già srotolato non produce quindi alcuna modifica, ed è anche il modo in cui `--check` diventa affidabile come gate.

## Uso

Lo strumento è un singolo file Python 3 senza dipendenze obbligatorie, invocato con l'interprete di sistema.

```
python tools/md-unwrap.py                          # cartella corrente, scrittura in-place
python tools/md-unwrap.py docs README.md           # cartelle e file, misti
python tools/md-unwrap.py "docs/**/*.md"           # glob, ricorsivo
python tools/md-unwrap.py --check .                # dry-run: esce 1 se qualcosa cambierebbe
python tools/md-unwrap.py --diff docs              # mostra il diff unificato, non scrive
python tools/md-unwrap.py --oracle require .       # pretende l'oracolo di rendering
python tools/md-unwrap.py --only-tracked .         # solo i file tracciati da git
python tools/md-unwrap.py --exclude "_notes" .     # esclusione aggiuntiva
```

La scrittura in-place è la modalità di default e riguarda i soli file con estensione `.md` e `.markdown`, modificabile con `--ext`. Le modalità `--check` e `--diff` non scrivono mai nulla. I codici di uscita sono tre: `0` quando tutto è a posto, `1` in `--check` quando almeno un file cambierebbe, `2` quando c'è stato un errore, cioè un file non decodificabile come UTF-8, un percorso inesistente, una scrittura fallita, o un file che l'oracolo ha bocciato. Il riepilogo finale dice sempre quanti file sono stati esaminati, quanti modificati, quante righe unite e quanti saltati con il motivo.

Un'opzione conta più delle altre quando si passa su molti repository in serie: `--only-tracked`, che processa i soli file tracciati da git ed enumera direttamente da `git ls-files` invece di camminare l'albero del filesystem. La differenza non è teorica: su un progetto reale che teneva un corpus documentale non tracciato di 289.322 file Markdown, la sola enumerazione del filesystem costava trenta secondi e il controllo del tracciamento file per file avrebbe richiesto ore, mentre l'enumerazione da git porta la stessa corsa a cinque secondi sui 118 file che contano davvero. Se il percorso passato non è un repository git l'opzione non processa nulla e lo dichiara con un errore, invece di riportare in silenzio zero file esaminati. Serve perché una scrittura su un file tracciato è sempre annullabile con `git checkout -- <file>`, mentre una scrittura su un file ignorato, tipico di `_notes/` o di un `CLAUDE.local.md`, non ha nessuna rete di recupero. Su un repository con il worktree pulito la coppia `--only-tracked --oracle require` è la postura corretta per una passata non supervisionata; i file ignorati si trattano dopo, uno per uno e con l'occhio sopra, quando si è deciso che vale la pena.

Sono escluse di default le cartelle di controllo di versione e di build (`.git`, `node_modules`, `.venv`, `__pycache__`, `dist`, `build`, `out`, `.next`, `target`, e altre della stessa natura), e `--exclude` ne aggiunge altre come pattern glob confrontati sia con i singoli segmenti del percorso sia con il percorso relativo. Esiste inoltre un marcatore per proteggere un intero sottoalbero: un file vuoto o commentato di nome `.md-unwrap-ignore` dentro una cartella esclude quella cartella e tutte le sue discendenti, anche quando un file al suo interno viene passato per nome. È il meccanismo con cui le fixture di test di questo pacchetto, che devono restare identiche byte per byte, sono protette da una passata sull'intero repository.

## Test

La suite copre le fixture, l'idempotenza, l'oracolo di rendering e la CLI, e non richiede alcun framework.

```
python tests/run-tests.py          # riepilogo
python tests/run-tests.py -v       # una riga per controllo
```

Le fixture stanno in `tests/fixtures/<caso>/`, con `input.md` e `expected.md` confrontati byte per byte. I venticinque casi coprono il paragrafo hard-wrapped, l'elenco puntato e quello numerato con continuazioni regolari e pigre, la lista annidata su tre livelli, la citazione con continuazione pigra e la citazione annidata, il recinto con dentro una tabella ASCII, il recinto di tilde, il recinto di quattro backtick che contiene tre backtick, il recinto dentro una voce di elenco, la tabella GFM con allineamenti, il front matter YAML e quello TOML, il titolo Setext su due righe, le quattro forme della linea orizzontale, l'interruzione di riga voluta con due spazi e con backslash, il blocco di codice indentato, le definizioni di link con riga di titolo, il blocco HTML e il commento HTML, le note a piè di pagina su più righe accanto alle vere definizioni di link, il code span inline che attraversa un a capo accanto a quello chiuso sulla stessa riga, i casi limite dei backtick a fine riga e del pipe in mezzo alla frase, il file CRLF, il file LF, il file a EOL misto, il file senza newline finale, il file con BOM, e un file già conforme su cui non deve cambiare nulla. Ogni fixture viene inoltre passata dall'oracolo di rendering e dal test di idempotenza, e la suite verifica anche che l'oracolo bocci davvero una trasformazione volutamente scorretta, per non lasciare la garanzia a un controllo che non scatta.

Sul repository di questo template, che contiene un centinaio di file Markdown scritti a mano, la passata reale ha srotolato cinquanta file per 1327 righe unite, senza nessun file saltato dall'oracolo, portando il bilancio git a 471 righe inserite contro 1774 rimosse. Oltre all'oracolo, la passata è stata verificata con un audit indipendente che ricava dai due testi sei proiezioni strutturali (righe di tabella, titoli, contenuto dei recinti, front matter, conteggio delle righe vuote, blocchi di codice indentati) e pretende che siano identiche: zero divergenze su tutti e cinquanta i file.

## Mappa di istanziazione

```
templates/md-unwrap/tools/md-unwrap.py   ->  <radice>/tools/md-unwrap.py       (tracciato)
templates/md-unwrap/tests/               ->  <radice>/tools/tests/md-unwrap/   (tracciato, opzionale)
```

Nella maggioranza dei progetti si istanzia il solo strumento: è autosufficiente e la suite di test vive qui, nel template, dove ha senso mantenerla. La suite si porta nel progetto solo se in quel progetto si intende modificare lo strumento, perché in quel caso i test sono la rete di protezione della modifica.

## Convenzione di progetto e frammento riusabile

La convenzione che lo strumento attua è normativa nel sistema di progetto: sta nella regola `.claude/rules/interaction-style.md`, sezione "Formattazione dei file Markdown", e vale per ogni file `.md` scritto o modificato in un progetto che adotta il template. Per un progetto che non ha quella regola, il frammento seguente si incolla nel suo `CLAUDE.md` ed è autosufficiente.

```markdown
## Convenzione Markdown

I file `.md` si scrivono con i paragrafi su una riga sorgente continua: nessun a capo manuale a
colonna fissa, nessuna riga spezzata a meta' frase. L'a capo separa due paragrafi distinti, mai
due frasi o due porzioni della stessa frase, e l'avvolgimento a video resta compito dell'editor.
Restano intatti: le righe vuote tra i blocchi, i titoli, le tabelle, i blocchi di codice recintati
e indentati, il front matter, le definizioni di link di riferimento e l'indentazione che definisce
l'annidamento delle liste. Una voce di elenco sta su una riga sola, marcatore incluso. Un `<br>`
si ottiene solo con due spazi a fine riga, e solo quando l'interruzione e' intenzionale. La fine
riga del file (CRLF o LF), il newline finale e l'eventuale BOM si conservano come sono.

Dopo aver creato o modificato un file `.md`, esegui lo strumento di unwrap:

    python tools/md-unwrap.py <file o cartella>

Prima di committare, la verifica non distruttiva e' `python tools/md-unwrap.py --check .`, che
esce con codice diverso da zero se qualche file non rispetta la convenzione. Se lo strumento non
e' presente in questo progetto, rispetta la convenzione a mano.
```

## Gate opzionale in pre-commit e in CI

Il gate non è installato da questo pacchetto e non va installato senza una scelta esplicita, perché un hook di pre-commit che blocca un commit è un cambiamento del flusso di lavoro, non un dettaglio di formattazione. Le due forme proposte sono le seguenti, e vanno intese come da valutare, non come attive.

La prima è un hook git locale in `.git/hooks/pre-commit`, che verifica i soli file `.md` in stage e blocca il commit se non sono conformi, lasciando all'utente il comando per sistemarli. Vive fuori dal repository, quindi non si propaga a un clone, ed è la forma più leggera.

```bash
#!/bin/sh
# .git/hooks/pre-commit - verifica la convenzione Markdown sui file in stage
files=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(md|markdown)$')
[ -z "$files" ] && exit 0
python tools/md-unwrap.py --check $files || {
  echo "md-unwrap: paragrafi da srotolare. Esegui: python tools/md-unwrap.py $files"
  exit 1
}
```

La seconda è un job di CI[^9] su GitHub Actions, che fa la stessa verifica sull'intero repository a ogni push e pull request. È la forma che si propaga al team, e non blocca il lavoro locale.

```yaml
name: markdown
on: [push, pull_request]
jobs:
  unwrap-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.x'
      - run: pip install markdown-it-py
      - run: python tools/md-unwrap.py --check --oracle require .
```

## Confronto con prettier --prose-wrap never

La domanda se serva uno strumento dedicato quando esiste già Prettier è legittima, e la risposta è che Prettier risolve lo stesso problema ma non con lo stesso perimetro.

Con `--prose-wrap never` Prettier srotola effettivamente i paragrafi, ed è uno strumento maturo, integrato in ogni editor. Il costo è che Prettier è un formatter completo, quindi normalizza anche altro nello stesso passaggio: unifica il marcatore delle liste puntate su un carattere solo, riallinea e ricostruisce le tabelle GFM padding compreso, uniforma i titoli allo stile ATX convertendo i Setext, riscrive l'escaping di alcuni caratteri, normalizza le virgolette e gli spazi dentro l'enfasi, e riscrive la fine riga secondo la propria opzione `endOfLine`. Su un repository di documentazione scritta a mano il risultato è un diff enorme in cui la modifica voluta, la rimozione del wrap, è indistinguibile da centinaia di righe di normalizzazione non richiesta. Aggiungere Prettier comporta inoltre una dipendenza Node con la sua configurazione, il che è irrilevante in un progetto JavaScript e sproporzionato in un repository di soli documenti.

Il vantaggio dello strumento di questo pacchetto è esattamente il perimetro: un diff che contiene solo gli a capo tolti, nessuna dipendenza obbligatoria, l'oracolo di rendering che rifiuta di scrivere un file di cui non è certo, e il marcatore per proteggere sottoalberi che devono restare intatti. Il costo è che si tratta di codice locale al template invece di uno strumento con una comunità dietro, ed è conservativo per scelta: dove il contesto è ambiguo lascia il wrap invece di rischiare, quindi può restare qualche paragrafo non srotolato in situazioni rare come il tratto tra due `---` a inizio file. Per il caso d'uso di questo sistema, cioè molti file `.md` di documentazione su molti progetti diversi con la storia git da tenere leggibile, il default resta il formatter a diff minimo. Prettier resta l'alternativa sensata in un progetto che lo usa già per il codice e che accetta di normalizzare anche il Markdown al suo standard.

[^1]: *ATX* - stile di titolo Markdown con i cancelletti a inizio riga (`## Titolo`), dal formato omonimo di Aaron Swartz.
[^2]: *Setext* - stile di titolo Markdown in cui il titolo è sottolineato dalla riga successiva composta di `=` o `-`, dal formato Structure Enhanced Text.
[^3]: *front matter* - blocco di metadati in testa a un file Markdown, delimitato da `---` per lo YAML o `+++` per il TOML, letto dai generatori di siti statici e non reso come contenuto.
[^4]: *GFM*, GitHub Flavored Markdown - estensione di CommonMark che aggiunge tabelle, task list, strikethrough e autolink.
[^5]: *CRLF*, Carriage Return Line Feed - fine riga a due caratteri usata dai file di testo Windows.
[^6]: *LF*, Line Feed - fine riga a un carattere usata dai file di testo Unix, Linux e macOS.
[^7]: *BOM*, Byte Order Mark - sequenza di byte facoltativa in testa a un file UTF-8 che ne dichiara la codifica; alcuni editor Windows la scrivono.
[^8]: *CommonMark* - specifica formale e non ambigua del Markdown, base di riferimento dei parser moderni e del comportamento descritto in questo documento.
[^9]: *CI*, Continuous Integration - esecuzione automatica di controlli e test su un servizio remoto a ogni push o pull request.
