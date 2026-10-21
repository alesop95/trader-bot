# Pacchetto notebooklm-bridge

> Pacchetto opzionale del sistema di progetto. Scaffolda il metodo di ricerca fondata che collega NotebookLM (gratuito) come motore di recupero ancorato alle fonti dell'utente e Claude come motore di ragionamento e scrittura, nei quattro passi del loop grounded: NotebookLM sintetizza con citazioni, Claude ragiona sulla sintesi, Claude rimanda a NotebookLM cio che va verificato, Claude scrive la versione finale. Si offre al gate dei pacchetti (vedi ../PACKAGES.md) ai progetti che ragionano o scrivono a partire da un corpus di fonti proprie dell'utente, quando conviene tenere il corpus fuori dal contesto di Claude e farvi ragionare sopra solo una sintesi densa e citata. Il pacchetto è costruito interamente attorno al piano gratuito di NotebookLM: non usa l'API Enterprise a pagamento e non presuppone alcun account aziendale.

## Perché esiste, sui due piani

Il pacchetto vive esattamente all'incrocio dei due assi indicati alla sua nascita, il risparmio di token e la ricerca, e li serve con lo stesso meccanismo.

Sul piano della token economy, il guadagno è strutturale. Un corpus di decine di documenti può valere oltre un milione di token: caricarlo in conversazione per farci ragionare Claude è sia costoso sia degradante per la qualità, perché oltre le 120-150 mila token utili il rumore prende il sopravvento, come descritto in `.claude/rules/token-economy.md`. NotebookLM tiene quel corpus nel proprio indice, fuori dalla finestra di contesto di Claude, e restituisce solo una sintesi densa con citazioni. In conversazione entra quella sintesi, poche migliaia di token, non il corpus intero. È lo stesso principio di disclosure progressiva del pacchetto `doc-ingest`, portato un gradino più in là: dove `doc-ingest` genera localmente uno scheletro di Livello 1 che l'agente legge per decidere quale sezione aprire, qui il Livello 1 è una sintesi già ancorata e citata prodotta da un motore di recupero esterno, che risponde anche a domande mirate senza mai versare il testo grezzo in contesto.

Sul piano della ricerca, il pacchetto chiude il divario che gli strumenti di ricerca non colmano da soli, il tema esplicito degli screenshot di origine: Claude ragiona in modo brillante ma non è ancorato alle fonti dell'utente, NotebookLM è ancorato alle fonti ma non ragiona né scrive al posto tuo. Il loro accoppiamento produce una ricerca in cui ogni affermazione resta tracciabile a una fonte, mentre il ragionamento, il confronto tra angolazioni, la ricerca di contraddizioni e la stesura finale restano a Claude. Complementa gli altri pacchetti di ricerca senza sovrapporsi: `academic-researcher` governa la bibliografia e la Corpus Analysis Suite su paper già in conversazione, la skill `deep-research` fa fan-out di ricerche sul web con verifica avversariale, mentre questo pacchetto aggiunge lo strato di recupero ancorato su un corpus di fonti che l'utente possiede e carica di persona.

## Il vincolo del piano gratuito

Il pacchetto assume tassativamente NotebookLM nel piano gratuito. Questo fissa alcuni limiti concreti che il metodo tiene in conto invece di ignorarli. Il piano gratuito consente fino a cinquanta fonti per notebook e impone un tetto giornaliero alle interrogazioni; ogni singola fonte può arrivare a circa cinquecentomila parole. Soprattutto, il piano gratuito è accessibile solo dal browser: non esiste un'API pubblica per consumatori. L'unica API ufficiale di NotebookLM è quella Enterprise, che richiede credenziali aziendali e un progetto Google Cloud a pagamento, ed è quindi fuori perimetro per scelta. Ne discende che l'accesso avviene sempre attraverso un browser con un account Google connesso, nei due modi descritti sotto.

## Il modo di accesso e le sue condizioni

Il modo è uno solo, quello manuale, l'unico pienamente conforme ai termini di servizio. La persona carica le fonti su NotebookLM dal browser, chiede la sintesi con citazioni e la incolla a Claude: NotebookLM lo guida un essere umano, Claude ragiona sul testo incollato. Non installa niente e non automatizza niente. Dal 2026-10-21, su decisione del proprietario, il pacchetto ha un solo modo, quello manuale, con tre condizioni che valgono per ogni progetto qualunque sia il suo account Google. Claude non pilota NotebookLM: lo usa la persona, nel browser. La sessione non si conserva: NotebookLM si apre in una finestra privata o ospite del browser, il login Google non si memorizza e alla chiusura della finestra non resta niente; a fine analisi il notebook si elimina, salvo che la persona decida di tenerlo. Ciò che ne torna si usa solo nel progetto che l'ha chiesto: la sintesi e le verifiche stanno sotto `_notes/notebooklm/` del progetto, locali e non versionate, e non si copiano in un altro progetto né in una memoria globale.

Fino al 2026-10-21 esisteva un modo assistito, in cui Claude pilotava NotebookLM tramite un server MCP della community che riusava un profilo Chrome con il login Google persistito. Il server raccomandato, `PleasePrompto/notebooklm-mcp`, è stato archiviato dall'autore, e il modo è stato tolto. Se un giorno servisse di nuovo, la sola via ammessa è un fork di quel server sviluppato e mantenuto qui, per il template e per i progetti che lo ereditano, con vincoli che il server originale non rispettava: gira tutto in locale; usa un profilo del browser effimero, creato per la sessione e cancellato alla chiusura, senza cookie né login persistiti; non salva le sessioni di NotebookLM; e non porta fuori dal progetto niente di ciò che legge. Il testo delle fonti e le risposte che rientrano dal browser restano in ogni caso input non fidato e un vettore di prompt injection.

## La verifica di disponibilità

Prima di iniziare il loop, il pacchetto verifica che NotebookLM sia effettivamente raggiungibile per questo progetto, che è la seconda metà della richiesta di origine. Lo strumento `tools/notebooklm-check.ps1` (Windows) e `tools/notebooklm-check.sh` (Linux) enumera i browser Chromium presenti sulla macchina, Chrome ed Edge, e per ciascuno legge dal file `Local State` i profili configurati con il nome e l'email dell'account Google associato, così da mostrare quali account sono candidati all'uso di NotebookLM. Lo stesso strumento segnala se esiste ancora un profilo dedicato del server `notebooklm-mcp`, cioè un login persistito rimasto dal modo assistito che va cancellato, e se nel `.mcp.json` del progetto risulta configurato un MCP di automazione del browser, che il pacchetto non usa.

Va detto con onestà cosa lo strumento non può fare: dall'esterno del browser non è possibile confermare che un dato account sia davvero loggato su NotebookLM e abbia accesso. Quella conferma è necessariamente visiva. Per questo, coerentemente con la regola `.claude/rules/manual-screenshots.md`, l'ultimo passo della verifica è chiedere all'utente uno screenshot di `notebooklm.google.com` aperto e loggato, che l'agente legge per confermare l'account attivo prima di procedere. L'account usato e l'URL del notebook si annotano in `memory/progress.md`, così il progetto sa come usa NotebookLM senza doverlo ridedurre a ogni sessione.

## Mappa di istanziazione

L'istanziazione copia la skill del loop in `.claude/skills/` del progetto e i due strumenti di verifica in `tools/`, nella variante del sistema operativo scelto al gate. La cache della ricerca si crea alla prima esecuzione sotto `_notes/`, già ignorato da git secondo `.claude/PROJECT-SYSTEM.md`.

```
templates/notebooklm-bridge/skills/notebooklm-bridge/  ->  <radice>/.claude/skills/notebooklm-bridge/   (tracciato)
templates/notebooklm-bridge/tools/notebooklm-check.ps1 ->  <radice>/tools/notebooklm-check.ps1          (tracciato, variante Windows)
templates/notebooklm-bridge/tools/notebooklm-check.sh  ->  <radice>/tools/notebooklm-check.sh           (tracciato, variante Linux)
(cache generata durante il loop)                           <radice>/_notes/notebooklm/<topic>/          (locale, ignorata)
```

## Il loop in quattro passi

La skill `notebooklm-bridge` orchestra il loop degli screenshot di origine, dopo la verifica di disponibilità come passo zero.

Il primo passo alimenta NotebookLM e gli chiede di sintetizzare. Le fonti (PDF, documenti, link, trascrizioni) si caricano nel notebook e si chiede una sintesi dei temi chiave con citazioni, con la formula collaudata "Summarize the key themes with citations". NotebookLM legge solo le fonti fornite, senza aggiungere fatti dal proprio addestramento, e ogni affermazione resta tracciabile a una fonte.

Il secondo passo porta la sintesi a Claude. La sintesi ancorata si incolla in `_notes/notebooklm/<topic>/synthesis.md` e diventa il contesto di ragionamento: ora Claude dispone dei fatti oltre che della capacità di ragionare, e la si mette a confrontare angolazioni, trovare contraddizioni, costruire una struttura, produrre outline e controargomenti.

Il terzo passo rimanda a NotebookLM cio che va verificato. Si chiede a Claude "cosa qui va verificato", si riportano le affermazioni segnalate alle citazioni di NotebookLM, e questo chiude l'anello tra ragionamento e ancoraggio: cio che Claude deduce viene ricontrollato contro le fonti prima di entrare nella versione finale. Le affermazioni verificate e quelle da correggere si annotano in `_notes/notebooklm/<topic>/verification.md`.

Il quarto passo lascia a Claude la stesura finale. Articolo, thread, report o presentazione: NotebookLM ha fatto da motore di recupero a zero allucinazioni, Claude da motore di ragionamento e scrittura, e il deliverable finale, che è un file normale del progetto e non materiale effimero, poggia su una ricerca di cui ci si può fidare perché ancorata alle fonti.

## Persistenza e igiene

La cache del loop vive sotto `_notes/notebooklm/<topic>/`, locale e ignorata da git, e contiene l'elenco delle fonti, la sintesi citata e il log di verifica. Tenerla locale e non versionarla è voluto: il materiale delle fonti può essere sensibile e non deve finire nel repository. Nel repository finisce solo il deliverable finale scritto da Claude, come qualunque altro file di progetto, più il puntatore breve in `memory/progress.md` con topic, URL del notebook, numero di fonti e data. Questo segue la stessa convenzione già descritta nel README di radice per l'ingestione manuale di documenti voluminosi.

## Uso

Dopo l'attivazione, il flusso tipico è questo. Si lancia la verifica di disponibilità, si sceglie il modo e si conferma l'account con uno screenshot, poi si invoca la skill per il loop.

```powershell
# Windows: verifica quali account Google e browser sono disponibili per NotebookLM
powershell -NoProfile -ExecutionPolicy Bypass -File tools/notebooklm-check.ps1
```

```bash
# Linux: stessa verifica
bash tools/notebooklm-check.sh
```

Il modo manuale non richiede altro che il browser, in una finestra privata o ospite.

## Crediti

Il metodo dei quattro passi è distillato dagli screenshot di un metodo pubblico "NotebookLM + Claude" condiviso dall'utente, ripuliti nel loro impianto e ricondotti alla disciplina di token economy e ricerca del sistema. NotebookLM è un prodotto Google; il piano gratuito è accessibile da browser su https://notebooklm.google.com e non espone un'API pubblica per consumatori. L'unica API ufficiale è quella Enterprise, documentata su Google Cloud e non usata da questo pacchetto perché a pagamento e fuori dal vincolo del piano gratuito.

Per il modo assistito, tolto il 2026-10-21, il template aveva raccomandato `PleasePrompto/notebooklm-mcp` (licenza MIT, guida un Chrome reale via Patchright riusando un profilo con login persistito, https://github.com/PleasePrompto/notebooklm-mcp), poi archiviato dall'autore, con le alternative `jacob-bd/gemini-notebook-mcp-cli`, già `notebooklm-mcp-cli` (https://github.com/jacob-bd/gemini-notebook-mcp-cli), e `julianoczkowski/notebooklm-mcp-2026` (https://github.com/julianoczkowski/notebooklm-mcp-2026), mai adottate. Restano citati come base di un eventuale fork, alle condizioni scritte sopra.
