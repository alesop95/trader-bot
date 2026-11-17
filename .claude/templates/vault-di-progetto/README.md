# vault-di-progetto

<!-- readme-summary: Un vault Obsidian sopra la memoria e la documentazione del progetto, fatto di soli collegamenti, con i plugin di base fissati per versione e impronta in un elenco che la passata porta ai progetti e che aggiorna anche i vault esistenti. -->

> Rende navigabili in Obsidian la memoria versionata, le schede di contesto e la documentazione di un progetto, con il grafo dei rimandi fra i documenti, senza copiare un solo file e senza versionare niente di nuovo. Nasce dal mandato del proprietario del 2026-11-12: ogni memoria di progetto deve poter diventare un vault.

## Il problema che risolve

La memoria del sistema sta sotto `.claude/`, e Obsidian non mostra le cartelle il cui nome comincia con un punto: aprire la radice del progetto come vault lascia fuori proprio la memoria e le schede. La via comoda, copiarle in una cartella visibile, produce due verità, e la regola `chat-non-e-memoria.md` esiste per impedirlo. Qui il vault è una cartella di soli collegamenti alle cartelle vere, quindi ciò che si legge è il file versionato e ciò che si scrive in Obsidian finisce in quel file.

## Che cosa crea

```
_vault/
  memoria   ->  .claude/memory
  contesto  ->  .claude/context
  docs      ->  docs
  .obsidian/    plugin e impostazioni
```

Su Windows i collegamenti sono giunzioni di cartella, che non chiedono privilegi di amministratore; su Linux e macOS sono collegamenti simbolici. Una cartella che il progetto non ha viene saltata e il comando lo dice. La cartella `_vault/` è una vista e non si versiona: si ricrea con un comando, e `--ignora` aggiunge la riga al `.gitignore`.

## Uso

```bash
python tools/vault-progetto.py crea --ignora
python tools/vault-progetto.py aggiorna --rete
python tools/vault-progetto.py verifica
python tools/vault-progetto.py togli
python tools/vault-progetto.py cerca grafo
python tools/vault-progetto.py valuta dataview
python tools/vault-progetto.py fissa dataview --motivo "..." --stato facoltativo
```

Dopo `crea`, in Obsidian si sceglie «Apri cartella come vault» sulla cartella `_vault`. La prima apertura chiede di fidarsi dei plugin della cartella: è la domanda di Obsidian, e la risposta spetta a chi apre. `verifica` esce con zero se i collegamenti puntano alle cartelle vere, i plugin voluti sono installati alla versione fissata e attivi, e la cartella è ignorata da git. `togli` rimuove collegamenti e configurazione, e si ferma se al posto di un collegamento trova una cartella vera. `aggiorna` e `verifica` accettano `--vault <cartella>` per lavorare su un vault qualunque, anche uno non creato da questo strumento, come i vault che il proprietario aveva già.

## I plugin: un elenco versionato, non una lista nel codice

Dal 2026-11-17 i plugin stanno in `plugin-vault.json`, accanto alla cartella `tools` di questo pacchetto. Per ogni plugin l'elenco fissa il repository, la versione, la versione minima di Obsidian, la licenza letta a monte, lo stato, il motivo e l'impronta SHA-256 di ogni file del rilascio. Lo stato è uno di tre: `base` si installa e si attiva in ogni vault, `facoltativo` solo nei progetti che lo chiedono, `tolto` si disattiva dove c'era, lasciandone la cartella con le impostazioni.

L'elenco è ciò che rende un cambiamento propagabile. Quando il template sposta una versione o cambia uno stato, la passata di allineamento porta l'elenco nuovo a ogni progetto. Da quel momento `verifica` del progetto dice quali plugin sono indietro o tolti, e `aggiorna` porta il vault alla versione fissata. Lo stesso comando vale per un vault creato da zero e per uno che esiste già. `aggiorna` non tocca mai `data.json`, cioè le impostazioni che chi usa il vault ha dato a un plugin, né i plugin che l'elenco non nomina, che sono scelte di chi usa quel vault.

Un progetto decide per sé in `.claude/vault-plugin.json`, un file suo che la passata non scrive. Con `aggiungi` installa un plugin che l'elenco del template dichiara facoltativo, con `togli` ne esclude uno di base, e in `plugin` scrive voci intere per plugin che il template non conosce, che `fissa --progetto` compila da sé.

```json
{ "aggiungi": ["dataview"], "togli": ["embed-html"], "plugin": [] }
```

## Da dove vengono i file, e perché non c'è fiducia cieca

Un plugin è codice che gira dentro Obsidian con i permessi dell'utente. Lo strumento prende i file prima da un vault già presente sulla macchina, indicato con `--da-vault <cartella>` o in `~/.config/vault-riferimento.txt`, ma solo se le impronte coincidono con quelle fissate. Altrimenti, e solo con `--rete`, li scarica dal rilascio su GitHub da cui li prende anche Obsidian, `https://github.com/<repo>/releases/download/<versione>/<file>`. In entrambi i casi un file la cui impronta non coincide non si scrive, e il plugin resta com'era. Una versione si sposta solo con `fissa`, quindi un rilascio ripubblicato o manomesso a monte non arriva a nessun vault finché qualcuno non lo rifissa. Senza vault di riferimento e senza `--rete`, il comando scrive la configurazione e dice quali plugin mancano.

## Come un plugin entra nella base

La ricerca usa il catalogo ufficiale dei plugin di Obsidian, `https://github.com/obsidianmd/obsidian-releases`. Da lì si leggono l'elenco dei plugin, le statistiche di scaricamento e l'elenco dei plugin tolti dal catalogo con il motivo. `cerca <parole>` filtra per parole su identificativo, nome e descrizione, e ordina per scaricamenti. `valuta <id>` misura cinque criteri. Il plugin deve stare nel catalogo e non esserne stato tolto, avere una licenza dichiarata e leggibile dall'API di GitHub, un rilascio negli ultimi 365 giorni e un rilascio che porta `main.js` e `manifest.json`. La versione minima di Obsidian che chiede, infine, non deve superare quella installata, che lo strumento legge dai dati di Obsidian sulla macchina. Esce con zero solo se passano tutti.

I cinque criteri dicono se un plugin si può mettere nella base, non se serve. L'utilità per chi legge la memoria di un progetto è un giudizio, e spetta al proprietario. Il passo che registra la decisione è `fissa <id> --motivo "..."`, che rifà la valutazione e rifiuta lo stato `base` a un plugin che non la passa. Poi scarica il rilascio, ne calcola le impronte e scrive la voce. Il motivo è obbligatorio, perché un plugin senza ragione scritta è un plugin che nessuno saprà più se togliere. Il repository di ogni plugin dell'elenco va anche nel registro delle fonti del template, così che un rilascio nuovo venga segnalato e si decida se rifissarlo.

I plugin di base sono tre. Il 2026-11-12 erano i plugin comuni a cinque vault del proprietario, ed è lui che ha indicato di prendere quelli. Il 2026-11-17 sono stati rifissati all'ultimo rilascio, dopo una valutazione passata su tutti e cinque i criteri. `obsidian42-brat` 2.2.0, da `https://github.com/TfTHacker/obsidian42-brat`, installa e aggiorna plugin che non stanno nel catalogo ufficiale. `new-3d-graph` 2.8.3, da `https://github.com/Apoo711/obsidian-3d-graph`, mostra il grafo dei documenti in tre dimensioni, con filtri. `embed-html` 2.7.0, da `https://github.com/mnaoumov/obsidian-embed-html`, incorpora in una nota un file HTML, che è ciò che serve per le mappe e le guide del sistema. Tutti e tre sono sotto licenza MIT, letta a monte il 2026-11-17. La descrizione di `embed-html` nel catalogo dichiara che il plugin non è stato rivisto a mano dal personale di Obsidian: è un'informazione, non un criterio di esclusione, e resta qui perché chi decide la veda.

## Quando offrirlo, e quando no

Il gate lo propone quando Obsidian è installato sulla macchina e il progetto ha una documentazione abbastanza ampia da perdersi, cioè qualche decina di file Markdown fra `docs/`, memoria e schede, oppure quando l'utente chiede di vedere le relazioni fra i documenti. Si verifica con un comando: su Windows la cartella `Obsidian` sotto i dati locali dell'utente, altrove il comando `obsidian`.

Non si propone dove Obsidian non c'è, perché il pacchetto non lo installa. Non serve a un progetto con pochi documenti, dove l'indice della memoria basta. Non sostituisce `knowledge-wiki`, che costruisce un sapere da fonti, né il motore di lettura ancorata, che legge documenti esterni: qui si guarda soltanto ciò che il progetto ha già scritto. E su una macchina remota senza interfaccia grafica non ha oggetto.

## Limiti dichiarati

Che Obsidian segua le giunzioni di Windows è stato osservato il 2026-11-17: il proprietario ha aperto il vault del template in Obsidian 1.15.1, ha accettato i plugin, e le note di `docs/` si sono aperte attraverso la giunzione, con il grafo che le mostrava. Lo stesso giorno lo strumento ha trenta prove interne, e due mutazioni deliberate, sull'impronta del file scaricato e sul plugin tolto dal catalogo, fanno fallire ciascuna la prova che la copre. Sul vault reale del template `verifica` ha trovato i tre plugin indietro o diversi dal rilascio, `aggiorna --rete` li ha portati alla versione fissata e la `verifica` successiva è uscita con zero. Sui collegamenti simbolici di Linux e macOS l'apertura in Obsidian non è stata osservata. Il grafo del template, nella stessa prova, aveva pochi archi: la documentazione del template cita gli altri file come codice, fra apici inversi, e Obsidian traccia un arco solo per un collegamento Markdown vero. È una proprietà dei documenti e non del vault, e un progetto che scrive i rimandi come collegamenti ha un grafo più denso. Obsidian scrive nella cartella del vault anche il proprio stato di lavoro, che resta lì e non entra nel repository. I collegamenti fra documenti scritti come percorsi relativi al progetto, per esempio da `docs/` verso `.claude/memory/`, dentro il vault non si risolvono, perché la cartella si chiama `memoria`: il grafo mostra i rimandi interni a ciascuna delle tre cartelle e non quelli che le attraversano.

## Rimozione

`python tools/vault-progetto.py togli`, poi si cancella la riga di `_vault/` dal `.gitignore`. Nessun file del progetto viene toccato, e `.claude/vault-plugin.json`, se c'è, resta con le scelte del progetto.
