# Pacchetto notebooklm-bridge

> Pacchetto opzionale del sistema di progetto. Scaffolda il metodo di ricerca fondata che collega NotebookLM (gratuito) come motore di recupero ancorato alle fonti dell'utente e Claude come motore di ragionamento e scrittura, nei quattro passi del loop grounded: NotebookLM sintetizza con citazioni, Claude ragiona sulla sintesi, Claude rimanda a NotebookLM cio che va verificato, Claude scrive la versione finale. Si offre al gate dei pacchetti (vedi ../PACKAGES.md) ai progetti che ragionano o scrivono a partire da un corpus di fonti proprie dell'utente, quando conviene tenere il corpus fuori dal contesto di Claude e farvi ragionare sopra solo una sintesi densa e citata. Il pacchetto e' costruito interamente attorno al piano gratuito di NotebookLM: non usa l'API Enterprise a pagamento e non presuppone alcun account aziendale.

## Perche' esiste, sui due piani

Il pacchetto vive esattamente all'incrocio dei due assi indicati alla sua nascita, il risparmio di token e la ricerca, e li serve con lo stesso meccanismo.

Sul piano della token economy, il guadagno e' strutturale. Un corpus di decine di documenti puo' valere oltre un milione di token: caricarlo in conversazione per farci ragionare Claude e' sia costoso sia degradante per la qualita', perche' oltre le 120-150 mila token utili il rumore prende il sopravvento, come descritto in `.claude/rules/token-economy.md`. NotebookLM tiene quel corpus nel proprio indice, fuori dalla finestra di contesto di Claude, e restituisce solo una sintesi densa con citazioni. In conversazione entra quella sintesi, poche migliaia di token, non il corpus intero. E' lo stesso principio di disclosure progressiva del pacchetto `doc-ingest`, portato un gradino piu' in la': dove `doc-ingest` genera localmente uno scheletro di Livello 1 che l'agente legge per decidere quale sezione aprire, qui il Livello 1 e' una sintesi gia' ancorata e citata prodotta da un motore di recupero esterno, che risponde anche a domande mirate senza mai versare il testo grezzo in contesto.

Sul piano della ricerca, il pacchetto chiude il divario che gli strumenti di ricerca non colmano da soli, il tema esplicito degli screenshot di origine: Claude ragiona in modo brillante ma non e' ancorato alle fonti dell'utente, NotebookLM e' ancorato alle fonti ma non ragiona ne' scrive al posto tuo. Il loro accoppiamento produce una ricerca in cui ogni affermazione resta tracciabile a una fonte, mentre il ragionamento, il confronto tra angolazioni, la ricerca di contraddizioni e la stesura finale restano a Claude. Complementa gli altri pacchetti di ricerca senza sovrapporsi: `academic-researcher` governa la bibliografia e la Corpus Analysis Suite su paper gia' in conversazione, la skill `deep-research` fa fan-out di ricerche sul web con verifica avversariale, mentre questo pacchetto aggiunge lo strato di recupero ancorato su un corpus di fonti che l'utente possiede e carica lui stesso.

## Il vincolo del piano gratuito

Il pacchetto assume tassativamente NotebookLM nel piano gratuito. Questo fissa alcuni limiti concreti che il metodo tiene in conto invece di ignorarli. Il piano gratuito consente fino a cinquanta fonti per notebook e impone un tetto giornaliero alle interrogazioni; ogni singola fonte puo' arrivare a circa cinquecentomila parole. Soprattutto, il piano gratuito e' accessibile solo dal browser: non esiste un'API pubblica per consumatori. L'unica API ufficiale di NotebookLM e' quella Enterprise, che richiede credenziali aziendali e un progetto Google Cloud a pagamento, ed e' quindi fuori perimetro per scelta. Ne discende che l'accesso avviene sempre attraverso un browser con un account Google connesso, nei due modi descritti sotto.

## I due modi di accesso

Il modo manuale e' quello di default, il piu' semplice e l'unico pienamente conforme ai termini di servizio. L'utente carica le fonti su NotebookLM dal browser, chiede la sintesi con citazioni, e incolla il risultato a Claude. NotebookLM lo guida un essere umano, Claude ragiona sul testo incollato. Non richiede alcuna dipendenza, alcuno script e alcuna automazione: e' il flusso disegnato negli screenshot di origine e resta il comportamento raccomandato per default.

Il modo assistito e' opzionale e si attiva solo su richiesta esplicita. Qui Claude pilota il NotebookLM gratuito dentro il browser tramite un server MCP di automazione della community, che riusa un profilo Chrome con l'account Google gia' connesso e legge le citazioni dal DOM. E' comodo quando il loop va ripetuto molte volte, ma va scelto con cognizione: nessuno di questi server e' ufficiale, ne' Google ne' Anthropic li avallano, e sul piano gratuito l'automazione del browser vive in una zona grigia dei termini di servizio, perche' l'unico endpoint pienamente conforme resta l'API Enterprise. Per questo il modo assistito non e' mai il default e la sua riga di catalogo (`notebooklm-mcp`) si propone separatamente al gate MCP, con questo caveat in chiaro. Il testo delle fonti e le risposte che rientrano dal browser sono input non fidato e un vettore di prompt injection: valgono le stesse cautele della regola dei permessi.

## La verifica di disponibilita'

Prima di iniziare il loop, il pacchetto verifica che NotebookLM sia effettivamente raggiungibile per questo progetto, che e' la seconda meta' della richiesta di origine. Lo strumento `tools/notebooklm-check.ps1` (Windows) e `tools/notebooklm-check.sh` (Linux) enumera i browser Chromium presenti sulla macchina, Chrome ed Edge, e per ciascuno legge dal file `Local State` i profili configurati con il nome e l'email dell'account Google associato, cosi' da mostrare quali account sono candidati all'uso di NotebookLM. Lo stesso strumento segnala se esiste gia' un profilo dedicato del server `notebooklm-mcp` (quindi un login assistito gia' persistito) e se nel `.mcp.json` del progetto risulta configurato un MCP di automazione del browser, `playwright-mcp` o un `notebooklm-mcp`.

Va detto con onesta' cosa lo strumento non puo' fare: dall'esterno del browser non e' possibile confermare che un dato account sia davvero loggato su NotebookLM e abbia accesso. Quella conferma e' necessariamente visiva. Per questo, coerentemente con la regola `.claude/rules/manual-screenshots.md`, l'ultimo passo della verifica e' chiedere all'utente uno screenshot di `notebooklm.google.com` aperto e loggato, che l'agente legge per confermare l'account attivo prima di procedere. La modalita' scelta per il progetto (manuale o assistita), l'account usato e l'URL del notebook si annotano in `memory/progress.md`, cosi' il progetto sa come usa NotebookLM senza doverlo ridedurre a ogni sessione.

## Mappa di istanziazione

L'istanziazione copia la skill del loop in `.claude/skills/` del progetto e i due strumenti di verifica in `tools/`, nella variante del sistema operativo scelto al gate. La cache della ricerca si crea alla prima esecuzione sotto `_notes/`, gia' ignorato da git secondo `.claude/PROJECT-SYSTEM.md`.

```
templates/notebooklm-bridge/skills/notebooklm-bridge/  ->  <radice>/.claude/skills/notebooklm-bridge/   (tracciato)
templates/notebooklm-bridge/tools/notebooklm-check.ps1 ->  <radice>/tools/notebooklm-check.ps1          (tracciato, variante Windows)
templates/notebooklm-bridge/tools/notebooklm-check.sh  ->  <radice>/tools/notebooklm-check.sh           (tracciato, variante Linux)
(cache generata durante il loop)                           <radice>/_notes/notebooklm/<topic>/          (locale, ignorata)
```

## Il loop in quattro passi

La skill `notebooklm-bridge` orchestra il loop degli screenshot di origine, dopo la verifica di disponibilita' come passo zero.

Il primo passo alimenta NotebookLM e gli chiede di sintetizzare. Le fonti (PDF, documenti, link, trascrizioni) si caricano nel notebook e si chiede una sintesi dei temi chiave con citazioni, con la formula collaudata "Summarize the key themes with citations". NotebookLM legge solo le fonti fornite, senza aggiungere fatti dal proprio addestramento, e ogni affermazione resta tracciabile a una fonte.

Il secondo passo porta la sintesi a Claude. La sintesi ancorata si incolla in `_notes/notebooklm/<topic>/synthesis.md` e diventa il contesto di ragionamento: ora Claude dispone dei fatti oltre che della capacita' di ragionare, e la si mette a confrontare angolazioni, trovare contraddizioni, costruire una struttura, produrre outline e controargomenti.

Il terzo passo rimanda a NotebookLM cio che va verificato. Si chiede a Claude "cosa qui va verificato", si riportano le affermazioni segnalate alle citazioni di NotebookLM, e questo chiude l'anello tra ragionamento e ancoraggio: cio che Claude deduce viene ricontrollato contro le fonti prima di entrare nella versione finale. Le affermazioni verificate e quelle da correggere si annotano in `_notes/notebooklm/<topic>/verification.md`.

Il quarto passo lascia a Claude la stesura finale. Articolo, thread, report o presentazione: NotebookLM ha fatto da motore di recupero a zero allucinazioni, Claude da motore di ragionamento e scrittura, e il deliverable finale, che e' un file normale del progetto e non materiale effimero, poggia su una ricerca di cui ci si puo' fidare perche' ancorata alle fonti.

## Persistenza e igiene

La cache del loop vive sotto `_notes/notebooklm/<topic>/`, locale e ignorata da git, e contiene l'elenco delle fonti, la sintesi citata e il log di verifica. Tenerla locale e non versionarla e' voluto: il materiale delle fonti puo' essere sensibile e non deve finire nel repository. Nel repository finisce solo il deliverable finale scritto da Claude, come qualunque altro file di progetto, piu' il puntatore breve in `memory/progress.md` con topic, URL del notebook, numero di fonti e data. Questo segue la stessa convenzione gia' descritta nel README di radice per l'ingestione manuale di documenti voluminosi.

## Uso

Dopo l'attivazione, il flusso tipico e' questo. Si lancia la verifica di disponibilita', si sceglie il modo e si conferma l'account con uno screenshot, poi si invoca la skill per il loop.

```powershell
# Windows: verifica quali account Google e browser sono disponibili per NotebookLM
powershell -NoProfile -ExecutionPolicy Bypass -File tools/notebooklm-check.ps1
```

```bash
# Linux: stessa verifica
bash tools/notebooklm-check.sh
```

Il modo manuale non richiede altro che il browser. Il modo assistito richiede, in aggiunta e solo se scelto, un MCP di automazione: la riga di catalogo `notebooklm-mcp` per il server dedicato, oppure `playwright-mcp` come automazione generica del browser, entrambi proposti separatamente al gate MCP con il caveat sui termini di servizio.

## Crediti

Il metodo dei quattro passi e' distillato dagli screenshot di un metodo pubblico "NotebookLM + Claude" condiviso dall'utente, ripuliti nel loro impianto e ricondotti alla disciplina di token economy e ricerca del sistema. NotebookLM e' un prodotto Google; il piano gratuito e' accessibile da browser su https://notebooklm.google.com e non espone un'API pubblica per consumatori. L'unica API ufficiale e' quella Enterprise, documentata su Google Cloud e non usata da questo pacchetto perche' a pagamento e fuori dal vincolo del piano gratuito.

Per il modo assistito opzionale, i server MCP della community citati nel catalogo sono progetti indipendenti, non ufficiali, che pilotano il browser: `PleasePrompto/notebooklm-mcp` (licenza MIT, guida un Chrome reale via Patchright riusando un profilo con login persistito, https://github.com/PleasePrompto/notebooklm-mcp), con alternative come `jacob-bd/notebooklm-mcp-cli` (accesso via CLI, MCP e skill, https://github.com/jacob-bd/notebooklm-mcp-cli) e `julianoczkowski/notebooklm-mcp-2026` (https://github.com/julianoczkowski/notebooklm-mcp-2026). L'automazione del browser sul piano gratuito non e' avallata da Google ne' da Anthropic e vive in una zona grigia dei termini di servizio: il modo manuale resta il default conforme, l'assistito e' opt-in a ragion veduta.
