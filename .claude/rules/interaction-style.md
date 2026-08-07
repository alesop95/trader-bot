# Stile di interazione e di documentazione tecnica

> Regola modulare, da caricare sempre. Codifica lo stile descritto nella sezione 8 di `PROJECT-SYSTEM.md`, così da renderlo vincolante per ogni sessione invece di affidarlo alla memoria. Vale per la documentazione prodotta e per il modo di rispondere.

## Destinatario e registro

La comunicazione si rivolge a un lettore tecnico esperto e va scritta come ci si rivolgerebbe a un responsabile tecnico: diretta, chiara, esaustiva, senza ridondanza. Si preferisce spiegare una cosa una volta sola, in modo descrittivo, senza dare per scontato nemmeno il semplice, e senza ripeterla altrove.

## Impianto del testo

L'impianto è discorsivo. I concetti vengono prima inquadrati architetturalmente, poi approfonditi con estratti di codice annotati, infine collegati ai flussi con paragrafi di raccordo. Non si usano elenchi puntati nella prosa, non si usano emoji, non si usa il grassetto nella prosa. I termini chiave densi si marcano in corsivo. Le keyword di codice dentro i blocchi sintattici si marcano in grassetto. I frammenti di codice e di configurazione stanno in blocchi monospazio. Gli alberi del filesystem si mantengono come blocchi preformattati con indentazione.

## Formattazione dei file Markdown

Ogni paragrafo di prosa si scrive come una riga sorgente unica, per quanto lunga: l'a capo separa due paragrafi distinti, mai due frasi o due porzioni della stessa frase. Non si spezza manualmente una riga per restare sotto una larghezza di colonna arbitraria: l'avvolgimento a video resta compito dell'editor o del renderer, non del file sorgente. Questo vale per ogni file `.md` scritto o modificato nel template, incluse le regole sotto `.claude/rules/`, le skill sotto `.claude/skills/` e i README dei pacchetti sotto `.claude/templates/`. Fanno eccezione i blocchi preformattati (codice, configurazione, alberi di filesystem) e le tabelle, dove l'a capo è strutturale e non va toccato, e i documenti copiati verbatim da una fonte esterna come riferimento, che mantengono la formattazione originale della fonte.

Lo stesso principio vale per il testo scritto direttamente in sessione, nel terminale: un paragrafo di prosa non si spezza a mano a metà frase per restare sotto una larghezza arbitraria, perché il terminale o il client, come l'editor per un file, gestiscono da soli l'avvolgimento a video. L'a capo manuale nell'output di sessione resta riservato a separare paragrafi distinti, voci di un elenco puntato dove l'elenco è la forma corretta, o righe strutturali (blocchi di codice, alberi di filesystem, tabelle), mai a interrompere una frase a meta'.

Nel dettaglio, e' vincolante quanto segue. Ogni paragrafo sta su una riga sorgente unica. Ogni voce di elenco sta su una riga sola, marcatore incluso, e l'indentazione che definisce l'annidamento si conserva. Le righe di continuazione dentro una citazione si uniscono alla riga che le apre, conservando il prefisso `>` di quest'ultima. Un `<br>` si ottiene solo con due spazi a fine riga, o con un backslash finale, e solo quando l'interruzione e' intenzionale: fuori da questo caso una riga non finisce mai con spazi. Restano intatti i titoli in entrambi gli stili, le linee orizzontali, il front matter, i blocchi di codice recintati e quelli indentati, le tabelle riga per riga e senza riallineamento, i blocchi HTML e le definizioni di link di riferimento. Di ogni file si conservano la fine riga (CRLF o LF), la presenza o assenza del newline finale e l'eventuale BOM.

L'attuazione meccanica di questa convenzione e' lo strumento `tools/md-unwrap.py`, dal pacchetto `md-unwrap`, che unisce le righe di continuazione senza normalizzare nient'altro e rifiuta di scrivere un file il cui rendering cambierebbe. Dopo aver creato o modificato un file `.md` si esegue `python tools/md-unwrap.py <file o cartella>`, e la verifica non distruttiva prima di un commit e' `python tools/md-unwrap.py --check .`, che esce con codice diverso da zero se qualche file non rispetta la convenzione. Nei progetti dove lo strumento non e' istanziato la convenzione si rispetta a mano: resta vincolante comunque, perche' e' la regola, non lo strumento, a definirla.

## Convenzioni tipografiche

Gli acronimi si spiegano in note a piè di pagina numerate, per non interrompere il discorso con parentesi inline. Non si usano i trattini lunghi: sono ammessi solo i trattini brevi.

## Onestà del contenuto

Non si presenta mai come fatto un contenuto inferito, speculativo o non verificato. Ciò che non è verificabile va etichettato come tale, e ciò che non si conosce va dichiarato invece di essere riempito per ipotesi. Le inferenze non confermate si marcano esplicitamente come da verificare e si promuovono a fatto solo quando una fonte le conferma.
