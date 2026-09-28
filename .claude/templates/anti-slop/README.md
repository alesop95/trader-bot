# Pacchetto: anti-slop

> Guida, fonti e due rilevatori deterministici per i segni ricorrenti dei contenuti generati da un modello, sei nella prosa e otto nelle interfacce. Il pacchetto non riscrive niente: misura, dice dove guardare e spiega perché ogni segno è un difetto e che cosa si fa al suo posto.

<!-- readme-summary: segni di prosa e interfacce generate, con fonti e due rilevatori -->

## Il problema che risolve

Un contenuto generato senza indicazioni tende alle scelte più frequenti, e il risultato si riconosce: paragrafi della stessa misura, un'autorità citata senza nome, tutto a gruppi di tre, e nelle interfacce lo sfondo crema con l'accento ambra, la parola del titolo in corsivo, le card dentro le card. Il template ha sempre avuto due skill esterne per questo, `humanizer` per la prosa e `taste-skill` per le interfacce, ma nessuna regola nominava i segni e nessuno strumento li cercava: un difetto che si vede solo rileggendo con attenzione è un difetto che passa quando l'attenzione è altrove, secondo la sezione 17 di `PROJECT-SYSTEM.md`.

Il pacchetto nasce da un carosello di quattordici schede portato dall'utente come elenco di ciò che il template non deve produrre. Ogni segno del carosello è stato riscontrato su fonti primarie prima di entrare nella guida, e due che nessuna fonte letta conferma, il gergo forzato e la finta finestra di terminale, lo dichiarano.

## Che cosa contiene

```
anti-slop/
├── README.md                   questo file
├── GUIDA.md                    i quattordici segni, a campi fissi, con misure e fonti
├── FONTI.md                    registro: la fonte visiva di partenza e 12 fonti pubblicate
├── rules/
│   └── design-non-generico.md  regola per i progetti con interfaccia
├── githooks/
│   └── pre-commit.d/anti-slop  passo di avviso per i commit manuali
└── tools/
    ├── lint-prosa.py           P1-P6 su Markdown e testo, zero dipendenze
    └── lint-ui.py              U1-U10 su HTML, CSS, JSX, TSX, Vue, Svelte, zero dipendenze
```

Per la prosa la regola non sta nel pacchetto ma in `.claude/rules/interaction-style.md`, sezione "I segni del testo generato", perché vale per ogni progetto e per il template stesso.

## Come funzionano i due strumenti

Entrambi leggono e non scrivono, escono con zero salvo l'opzione `--gate`, e stampano per ogni segnalazione il codice del segno, così che il perché si trovi nella voce corrispondente della guida.

```
python tools/lint-prosa.py docs README.md
python tools/lint-prosa.py --solo P2,P3 docs
python tools/lint-ui.py src
python tools/lint-prosa.py --self-test
python tools/lint-ui.py --self-test
```

`lint-prosa.py` salta i blocchi di codice, il front matter, i commenti HTML, le tabelle e le citazioni in blocco, e tratta il testo fra virgolette come una menzione e non come un uso: una guida che cita "gli esperti ritengono" per spiegarlo non attribuisce niente a nessuno. `lint-ui.py` legge i sorgenti e non il rendering, riconosce le classi di utilità per nome e non ne conosce la palette, e segnala scelte da motivare; l'unico controllo normativo è U9, il contrasto WCAG del testo dove testo e sfondo sono dichiarati nella stessa regola CSS.

## Che cosa hanno misurato, e perché le soglie sono quelle

Le soglie sono in chiaro in testa a ciascuno strumento, con il motivo. La più istruttiva è quella di P1. Sul singolo paragrafo l'uniformità delle frasi non separa un testo generato da uno scritto a mano: il paragrafo generato del carosello ha una variazione di 0,18, e paragrafi del template scritti a mano stanno fra 0,11 e 0,22. Separa invece la quota di paragrafi uniformi nel documento, al massimo 0,20 nei file del template misurabili contro 1,00 nel campione, e quindi lo strumento segnala il documento e non il paragrafo. Il campione è piccolo e la soglia va rivista quando se ne avranno altri.

La prima corsa sulla prosa di sistema del template, cioè le regole, `PROJECT-SYSTEM.md`, `README.md`, `GUIDA-USO.md` e `CASE-STUDIES.md`, ha trovato il parallelismo negativo quattordici volte in sei file e la prevalenza delle triadi in sette file. La prima corsa di `lint-ui.py` sulle due pagine HTML del template ha trovato la palette crema con accento caldo e, su una pagina di catalogo, undici sezioni con la stessa struttura, che lì è corretta perché i dati sono omogenei. Una revisione dello stesso giorno ha poi riscritto tutti i parallelismi negativi del template e le triadi retoriche, lasciando le triadi che elencano cose reali, e ha ridisegnato la pagina HTML con la palette calda; lo stato dopo la revisione è descritto nella guida, voce per voce.

Tre prove di non vacuità sono state fatte reintroducendo un difetto in una copia degli strumenti: la soglia delle card resa irraggiungibile, il rimando alla fonte ignorato, e il confine di parola dopo un apostrofo, che non scatta mai perché apostrofo e spazio sono entrambi caratteri non di parola. In tutti e tre i casi è caduta la prova che doveva cadere. Il terzo difetto non era ipotetico: stava nel codice, e la e seguita dall'apostrofo, scritta al posto della e accentata, non veniva riconosciuta finché una verifica sul comportamento, non sul testo del codice, non lo ha mostrato.

## Cosa istanzia, e dove

```
templates/anti-slop/tools/lint-prosa.py          ->  tools/lint-prosa.py            in ogni progetto che produce prosa
templates/anti-slop/tools/lint-ui.py             ->  tools/lint-ui.py               nei progetti con interfaccia
templates/anti-slop/rules/design-non-generico.md ->  .claude/rules/                 nei progetti con interfaccia
templates/anti-slop/GUIDA.md e FONTI.md          ->  docs/anti-slop/                interi
templates/anti-slop/githooks/pre-commit.d/anti-slop -> .githooks/pre-commit.d/      dove c'è l'hook di readme-sync
```

Il passo di `.githooks/pre-commit.d/` porta gli strumenti nei commit manuali: esamina i soli file di prosa e di interfaccia in stage e stampa le segnalazioni nel terminale di chi committa, senza mai fermare il commit. Si appoggia all'hook `pre-commit` del pacchetto `readme-sync`, che esegue gli script di quella cartella; dove l'hook non c'è, lo si richiama da un hook proprio. Provato il 2026-09-23 in un repository temporaneo con un file dal nome contenente spazi: segnalazioni stampate, commit eseguito.

La guida e il registro si copiano interi, perché le regole e gli strumenti vi rimandano per il perché di ogni segno.

## Quando offrirlo

A ogni progetto che produce prosa destinata a un lettore o un'interfaccia, cioè quasi sempre: `lint-prosa.py` serve già a un progetto di sola documentazione, `lint-ui.py` e la regola di design solo dove c'è un frontend. Non si offre a un progetto di solo codice senza documentazione né interfaccia. Si affianca alle skill esterne `humanizer` e `taste-skill` senza sostituirle: quelle riscrivono o guidano la generazione, questo pacchetto verifica il risultato, e si usano in quest'ordine.

## Come si aggiorna

Il lessico di P6 invecchia con i modelli, e la pagina di Wikipedia da cui viene lo dichiara: "delve" è crollata nel 2025. L'elenco si rivede quando la pagina cambia, e la data di revisione nel registro è ciò che permette di accorgersene. Un segno nuovo entra nella guida solo con una fonte, oppure con la dichiarazione che nessuna fonte lo conferma ancora.
