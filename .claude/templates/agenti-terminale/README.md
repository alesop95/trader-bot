# Pacchetto opzionale: agenti-terminale

> Catena completa per far convivere **N radici di Claude Code e M radici di Codex CLI** sulla stessa macchina, isolate, ripristinabili da zero e ripulite all'uscita. Installazione, avvio, pulizia selettiva, comandi brevi di shell e misura del consumo. È generico: non contiene alcun valore di alcuna macchina.

L'attuazione corrente di questo pacchetto è PowerShell su Windows: i sette script di installazione, avvio, pulizia e consumo non hanno ancora varianti Linux. Il comando `chiudi` del sistema di progetto ha invece una variante Bash installabile separatamente con `templates/tools/installa-chiudi.sh`. Chi porta il template su Linux può usare quel flusso di chiusura, ma deve ancora progettare e provare la gestione multi-account di questo pacchetto per ottenere la stessa capacità della macchina Windows.

## Cosa risolve

Usare più account dello stesso agente, o due agenti diversi, sulla stessa macchina pone quattro problemi che nessuno dei due strumenti risolve da sé: tenere le identità **isolate**, poterle **ricostruire** dopo una formattazione, **ripulire** ciò che resta a fine sessione, e **sapere quanto si è consumato** su ciascuna.

Il pacchetto li copre tutti e quattro, per entrambi gli agenti, sotto un unico punto d'ingresso.

## L'asimmetria fra i due agenti, che spiega perché i motori sono diversi

È l'unica cosa da capire prima di leggere il resto, e non è arbitraria.

**Claude Code ha un hook di fine sessione**: un comando registrato nel `settings.json` dell'account che punta a un file. Lo script di pulizia **deve** quindi esistere come copia dentro ogni radice, e l'installatore lo mette lì sostituendo i segnaposto.

**Codex ha un hook di fine sessione e non se ne può servire.** Si avvia quindi da un **wrapper**, che imposta la radice, verifica le guardie e fa la pulizia al ritorno del processo. I suoi script restano nel pacchetto e nessuna copia finisce nelle radici.

> **Questa riga diceva il falso fino al 2026-09-22**, e la correzione vale più della frase corretta. Si leggeva *"Codex non ha un hook di ciclo di vita"*. È vero il contrario da `codex-cli 0.155.1`: esiste `SessionEnd`, si configura in `<CODEX_HOME>\hooks.json`, scatta, e riceve già pronti `session_id` e `cwd` della sessione. Misurato: parte in 0,38 secondi e il payload contiene tutto il necessario.
>
> Il wrapper resta lo stesso, per **due limiti indipendenti**, ciascuno sufficiente da solo.
>
> **Non scatta su `codex exec`.** Tutto il lavoro non interattivo è scoperto, a cominciare dal pacchetto `lavoro-a-lotti`, che invoca esattamente quel comando. Ed è il caso che pesa di più: una giornata di lavoro a mano lascia tre o quattro sessioni, un corpus a lotti ne lascia decine.
>
> **Non può rimuovere la sessione che si sta chiudendo.** `SessionEnd` scatta *right before a session ends*, quando la sessione è ancora aperta e di proprietà del processo che sta uscendo: `codex delete` su di essa esce con codice 1 e `Error: failed to delete session`. La stessa sessione, stesso identificativo e stessa radice, viene rimossa senza errori un secondo dopo dal `finally` del wrapper.
>
> **La regola strutturale che ne discende:** la pulizia deve avvenire quando il processo è **già uscito**, e nessun hook interno può trovarsi in quel momento. Non è una limitazione di questa versione, da rivedere al prossimo aggiornamento: è una proprietà dell'ordine degli eventi.
>
> Ne segue che l'asimmetria fra i due agenti **non è sulla presenza dell'hook** - ce l'hanno entrambi - ma su **quanto l'hook riesce a coprire**. Chi rivaluta questo punto in futuro parta da qui invece di riaprire l'indagine: è costata una giornata.

Stessa invocazione per l'utente, motori diversi sotto. Ciò che l'utente vede è simmetrico:

```powershell
cd <progetto>
claude-account2
codex-account2
```

## I pezzi

| File | Ruolo |
|---|---|
| `.claude/templates/agenti-terminale/tools/Installa-Agenti.ps1` | **punto d'ingresso**: prerequisiti, dipendenze, chiama i due installatori e i comandi |
| `.claude/templates/agenti-terminale/tools/Installa-Claude.ps1` + `merge-claude-settings.js` | installa il wipe di fine sessione nelle radici Claude e registra l'hook nel `settings.json` preservando ogni altra chiave |
| `.claude/templates/agenti-terminale/tools/Installa-Codex.ps1` | crea le radici Codex, vi scrive la configurazione di riferimento e il puntatore `AGENTS.md` |
| `.claude/templates/agenti-terminale/tools/Avvia-Codex.ps1` | avvio su radice isolata, con vincolo sulla cartella di lavoro e pulizia all'uscita |
| `.claude/templates/agenti-terminale/tools/Pulisci-Codex.ps1` | wipe degli store: conserva solo le sessioni vive, riconosciute dal lock sui thread, e tocca i database solo a radice ferma |
| `.claude/templates/agenti-terminale/tools/Installa-Comandi.ps1` | scrive nel profilo PowerShell i comandi brevi per tutte le radici presenti |
| `.claude/templates/agenti-terminale/tools/Consumo-Agenti.ps1` | consumo di token di **tutte** le radici dei due agenti, radici di default comprese |
| `.claude/templates/agenti-terminale/tools/riserva-agenti.py` | riserva dei subagent sul limite del piano, per tutte le radici dei due agenti: scrive la soglia, decide per il wrapper Codex, registra l'ultima lettura |
| `.claude/templates/agenti-terminale/tools/Installa-Plugin.ps1` | porta in ogni radice la riserva e i plugin scelti per la macchina, da un file di valori del repository di macchina |
| `.claude/templates/agenti-terminale/codex-config.riferimento.toml` | configurazione di una radice Codex |
| `.claude/templates/agenti-terminale/codex-agents.riferimento.md` | `AGENTS.md` distribuito nelle radici: puntatore, mai copia |
| `.claude/templates/agenti-terminale/comunicazione-fra-sessioni.md` | studio, non attuazione: quale canale fra sessioni esiste davvero, e il vincolo di sandbox che decide il disegno di quelli che mancano |

## Che cosa NON contiene, e perché

**Nessun valore di macchina.** I due soli valori specifici sono i **prefissi degli slug da preservare** nel wipe, che dipendono dalle lettere di disco su cui vivono i progetti, e il **numero di radici**. Sono parametri, e vivono nel repository della macchina insieme al suo punto d'ingresso.

**Nessuna credenziale, mai.** Il ripristino ricostruisce radici e configurazioni, non gli accessi: si rifà un login per radice e per agente. Non è un limite ma la scelta corretta, e vale dirla per esteso perché la tentazione opposta è forte: una credenziale copiata da una macchina all'altra è una credenziale uscita dal proprio custode, e sopravvive in un backup molto più a lungo della ragione per cui era stata copiata.

**Nessun orchestratore.** Far lavorare più agenti insieme su un compito è materia del pacchetto `lavoro-a-lotti`, che poggia su questo ma non lo richiede.

**Nessun canale fra sessioni, ma lo studio di come farne uno.** Orchestrare e comunicare sono due cose diverse: la prima distribuisce un compito, la seconda lascia che sessioni già avviate si scambino quello che hanno scoperto. Il pacchetto non attua la seconda, e `comunicazione-fra-sessioni.md` spiega perché una delle due strade ovvie è una trappola e quale vincolo decide l'altra. Fra sessioni Claude Code il canale esiste già ed è nativo: non va installato niente.

## La chiusura di una sessione

Il pacchetto porta con sé la regola `.claude/templates/agenti-terminale/rules/chiusura-delle-sessioni.md`, che va dichiarata fra quelle caricate. Il principio in una riga: **una sessione che si considera chiusa per davvero va rimossa, non abbandonata**, perché abbandonarla la lascia in un magazzino che il wipe preserva apposta.

Le attuazioni differiscono: Codex ha il comando nativo `/delete`, che cancella la sessione ed esce; Claude Code non ha un equivalente e la rimozione va fatta a mano sul magazzino dell'account.

È il completamento del wipe, non un suo doppione: **il wipe copre l'incuria, questa regola copre la volontà.**

## Mappa di istanziazione

| Dal pacchetto | Nel progetto di macchina |
|---|---|
| tutto `tools/` e i due riferimenti | **niente**: si chiamano dal template, non si copiano |
| - | uno script sottile che conosce il percorso del template e i prefissi della macchina |

È la differenza rispetto agli altri pacchetti, e va detta: **questo non si istanzia copiando.** Il repository della macchina non ne contiene una copia ma una **chiamata**, perché due copie divergerebbero in silenzio e la correzione fatta in una non arriverebbe all'altra.

## Ripristino dopo una formattazione

```powershell
.\scripts\Agenti.ps1 verifica
.\scripts\Agenti.ps1 installa
```

Il primo non modifica nulla. Il secondo installa Codex se manca, crea le radici dei due agenti, vi scrive configurazioni e hook, registra i comandi brevi, e stampa l'elenco dei login da fare.

Su una macchina nuova servono due cloni: il template, che porta la catena, e il repository di macchina, che porta i valori.

## Vincoli e onestà

Gli installatori sono **idempotenti**: rieseguirli non sovrascrive ciò che c'è, salvo `-Forza`, che riallinea dai riferimenti. Ma `-Forza` sostituisce **l'intero** file di configurazione, e Codex vi scrive anche proprio stato: ciò che l'agente ha messo da sé viene perso. È successo davvero con la scelta della sandbox di Windows, riportando radici già configurate allo stato iniziale.

I **prefissi del wipe non si indovinano, si leggono**, con il modo di sola lettura di `Pulisci-Codex.ps1`. Un insieme sbagliato non produce un errore: preserva l'insieme vuoto e cancella tutto, facendo esattamente ciò che gli è stato chiesto.

I **server MCP di account** non sono ripristinati e vanno ricreati a mano.

Gli script del pacchetto si scrivono in **solo ASCII**. PowerShell 5.1 legge i `.ps1` in ANSI: un carattere non ASCII salvato da un editor UTF-8 si corrompe, spacca la stringa che lo contiene e produce un errore di analisi. Uno script che non si analizza **non parte affatto**, quindi non lascia nemmeno la riga di diagnostica messa apposta per non restare senza traccia. Il controllo costa due comandi e si fa prima di consegnare, non dopo:

```powershell
# nessuna riga in uscita = il file e' pulito
Select-String -Path .\script.ps1 -Pattern '[^\x00-\x7F]' -Encoding utf8
$e = $null; [void][System.Management.Automation.Language.Parser]::ParseFile('.\script.ps1', [ref]$null, [ref]$e); $e
```

**Script operativi con impronte.** Il preflight incorporato va eseguito nello stesso interprete usato dall'operatore prima di consegnare il comando. Il solo controllo sintattico e un hash calcolato separatamente non verificano che la costante nello script sia corretta. La modalità di prova si ferma prima di copie, SSH e azioni; quando un hash differisce mostra valore atteso e rilevato. Un carattere in più in una costante ha causato uno stop evitabile pur con il file locale invariato.

## Se si vuole comunque un hook di Codex: tre cose che non si vedono

Non serve per la pulizia, per le ragioni già dette. Ma il meccanismo esiste, prima o poi qualcuno lo userà per altro, e queste tre cose si pagano una volta ciascuna.

**La fiducia si concede a mano e nessuno script può farlo al posto tuo.** Un hook nuovo o modificato non viene eseguito finché non lo si approva in una schermata interattiva all'avvio della sessione. L'approvazione si registra come `hooks.state."<percorso>:<evento>:<i>:<j>".trusted_hash` **dentro `config.toml`**, ed è il digest del contenuto: cambiare il comando richiede una nuova approvazione. La chiave contiene il percorso assoluto e la posizione dell'hook nel file, quindi anche **spostare il file o riordinare gli hook** riporta tutto a non fidato. Un installatore può quindi distribuire il `hooks.json`, non attivarlo: serve un passaggio umano per radice, e di nuovo a ogni aggiornamento.

**Un hook non fidato non parte e non lo dice.** Nessun messaggio, nessun errore, nessuna riga di registro. Identico, dall'esterno, a un hook che funziona e non trova niente da fare.

**`-Forza` cancella anche la fiducia.** Rimpiazzando l'intero `config.toml` si perde il blocco `[hooks.state]`, e l'hook resta sul disco, appare configurato in `/hooks`, e non viene più eseguito. È la stessa trappola già descritta sopra per la scelta della sandbox, su un secondo oggetto.

Due note tecniche che fanno risparmiare mezza giornata a chi ci prova.

Il campo `command` **non è una riga di shell affidabile**: virgolette annidate e metacaratteri non sopravvivono al passaggio, e il fallimento è muto. Ci va il percorso di uno script, senza spazi, e la logica sta nello script.

Il tetto di esecuzione di `SessionEnd` è **3 secondi**, non aggirabile: un `timeout` maggiore viene ignorato con un avviso, e `async: true` non aiuta. `SessionStart` e `Stop` non hanno questo tetto.

> **Implicazione di sicurezza, da non perdere.** La fiducia si calcola sul **comando**, non su ciò che il comando esegue. Un `hooks.json` che punta a uno script rende lo script modificabile per sempre senza che nessuna approvazione venga più chiesta, e la schermata di approvazione dichiara che **un hook fidato gira fuori dalla sandbox**. Lo script puntato da un hook non va quindi tenuto dentro la radice dell'account, ma dove solo l'amministratore scrive.

## Che cosa si preserva nel wipe, e perché la risposta giusta tende a "niente"

Il wipe ha un insieme di prefissi da preservare, e la tentazione è riempirlo con i dischi di progetto, così che le sessioni di lavoro sopravvivano e si possano riprendere. **È la scelta sbagliata**, e la ragione non è di igiene ma di coerenza con il sistema.

La memoria di un progetto vive **dentro il progetto**, versionata: `.claude/memory/`, il work-log, il diario, i file di ripresa. È scritto nella regola `token-economy.md`, alla voce su ciò che non si fa: non si accumula stato fuori dal progetto. Una trascrizione di sessione che sopravvive nella radice di un account è esattamente quello: **memoria fuori dal progetto, non versionata, non ispezionabile, e che nessuno rileggerà mai**.

Se la ripresa di un lavoro dipende da una trascrizione conservata in `<CODEX_HOME>\sessions\`, il difetto sta nel lavoro che non ha lasciato traccia dove doveva, e il wipe si limita a renderlo visibile. La risposta è scrivere il file di ripresa, invece di preservare la trascrizione.

Ne segue che l'insieme dei prefissi preservati dovrebbe essere **vuoto per default**, e che ogni prefisso aggiunto è un'eccezione da giustificare. Vale allo stesso modo per l'altro agente, dove la stessa logica è espressa come elenco di slug di progetto da conservare.

**Due avvertenze, perché la cosa non si faccia alla cieca.** Preservare l'insieme vuoto **non produce un errore**: fa esattamente ciò che gli è stato chiesto, cioè cancellare tutto, ed è indistinguibile da un insieme di prefissi sbagliato. Ed è un'operazione **non reversibile**: le trascrizioni non stanno nel controllo di versione e non c'è cestino. Si guarda prima l'elenco con il modo di sola lettura, e solo dopo si esegue.

## Dal 2026-10-09: nessun prefisso, si conservano solo le sessioni vive

Il proprietario ha deciso il 2026-10-08 che in locale non deve restare niente delle sessioni, per Claude Code e per Codex con la stessa ragione, e `Pulisci-Codex.ps1` ha da allora l'insieme dei prefissi vuoto per scelta dichiarata, `$nienteDaPreservare = $true`, al posto di `D:\` ed `E:\` compilati il 2026-09-21. Ciò che resta sono le sole sessioni vive. Una sessione è viva se il suo file `<CODEX_HOME>\thread-writer-locks\<id>.lock` è bloccato da un processo: aprirlo riesce comunque, è il lock su un byte a fallire. Verificato il 2026-10-09 su questa macchina con tre sessioni interattive aperte, una per radice: un file bloccato per ciascuna, i file `.coordination.lock` liberi, e le tre corrispondevano alle cartelle di lavoro dei tre processi. Il modo `-Lista` le marca `VIVA`.

Prima di quella data il wrapper chiamava la pulizia con `-Tutto` a ogni uscita, e `-Tutto` cancellava anche i database di stato della radice mentre il demone `app-server` della stessa radice, sempre in esecuzione, li teneva aperti: un database SQLite tolto sotto un processo che lo usa può restare incoerente. Oggi `-Tutto` tocca database, `sessions\` e `tmp\` solo in una radice senza sessioni vive e senza demone, riconosciuto dall'eseguibile sotto `<radice>\packages`; altrimenti lo dice e salta. Le sessioni chiuse si tolgono sempre, con `codex delete`, che lascia coerenti gli indici. La memoria nascosta di Codex resta spenta in configurazione, `[features] memories = false`, quindi `memories_1.sqlite` esiste ma non si usa.

Il resoconto di `stato-magazzino.ps1`, nel pacchetto degli strumenti del template, mostra le sessioni Codex di ogni radice, vive e chiuse, accanto a quelle di Claude Code, con il comando di questa pulizia. Il pacchetto resta solo per Windows: su Linux le radici di Codex non hanno ancora una pulizia equivalente.

## «Background server has incompatible feature settings»

Osservato fino al 2026-10-09: all'avvio di una sessione Codex compariva il messaggio, seguito da `This session requires api_key_model_discovery to be disabled` e dalla scelta fra lavorare senza il demone, riavviarlo con le impostazioni condivise, o annullare. La causa sta nelle versioni. Il demone `app-server` di ogni radice si aggiorna da solo, in `<CODEX_HOME>\packages\app-server-daemon\releases\`, mentre la CLI installata con npm si aggiorna solo a mano; il 2026-10-09 la CLI era alla 0.160.1 e i demoni alla 0.161.0, e quando le due versioni hanno impostazioni predefinite diverse la sessione rifiuta il demone. Dopo l'aggiornamento della CLI il messaggio è sparito, ma il 2026-10-10 la CLI era alla 0.162.0 e i demoni alla 0.162.1, quindi può tornare al prossimo aggiornamento di uno solo dei due. Il rimedio è aggiornare la CLI, `npm install -g @openai/codex@latest`, e scegliere intanto di lavorare senza il demone, che non cambia le impostazioni condivise. Riavviarlo con le impostazioni della sessione le rende persistenti per tutti i client di quella radice, come avverte il messaggio stesso. Ogni radice conserva inoltre le versioni precedenti del demone, dieci per radice dalla 0.158.0 alla 0.162.1 alla stessa data: la cartella è gestita da Codex, e la pulizia non la tocca.

## Passaggio fra account dopo la pulizia

Prima di chiudere una sessione, consolidare nel progetto obiettivo, istruzioni permanenti dell’operatore, decisioni, evidenze e loro impronte, risultati distinti dai piani, pendenze, comandi successivi e modifiche parallele escluse. Verificare i riferimenti e aggiornare memoria canonica e file di ripresa. Se un altro progetto dipende da quel lavoro, il suo contesto va riconciliato nello stesso giro. La completezza si controlla sui file del progetto, non conservando la vecchia chat.

Gli ID digitati a mano possono essere incompleti: prima del wipe confrontarli con le sessioni vive rilevate dalla procedura, senza indovinare UUID e senza leggere le loro conversazioni. Eseguire l’anteprima della pulizia standard. Una sessione ancora viva, inclusa quella che prepara la chiusura, resta protetta; per rimuovere anche quella occorre uscire e lasciare eseguire il wrapper oppure richiamare il pulitore dal terminale esterno. I database condivisi di una radice in uso restano protetti: non promettere un azzeramento fisico integrale mentre altri lavori devono continuare. La pulizia non sostituisce backup delle evidenze private e non pubblica il lavoro Git.

Riaprire con Avvia-Codex.ps1, Account e Progetto espliciti, usando l’account richiesto; rileggere AGENTS.md e la memoria del progetto e verificare l’impronta prima di proseguire. Non copiare credenziali o sessioni fra radici e non scambiare il login di un account con l’identità Git locale del repository. Le procedure del pacchetto restano la fonte operativa: nessuna nuova modalità di cancellazione è introdotta da questa nota.

## Uscire da Codex e ripulire le sessioni

La funzione breve codex-account<N> passa dal launcher Avvia-Codex.ps1: alla conclusione del processo il blocco finally richiama Pulisci-Codex.ps1 per quella radice. Non dipende dal ricordarsi un comando di cancellazione. Un client o un avvio che non attraversano il launcher non hanno per questo acquisito il suo automatismo. La chiusura di una scheda dell’interfaccia e l’uscita del processo sono eventi da distinguere.

Per tutte le radici di account, Pulisci-Codex.ps1 senza -Account le scopre automaticamente; -DryRun -Tutto mostra l’effetto senza rimuovere dati. L’esecuzione con -Tutto usa codex delete per le sessioni chiuse e conserva sempre quelle vive, rilevate con i lock, anche quando appartengono ad altri account. I database e le directory di stato si azzerano solo quando la radice non ha thread vivi o app-server. La radice desktop predefinita resta esclusa, salvo -IncludiDefault ad applicazione chiusa. I percorsi del progetto non sono store di conversazioni e non vengono cancellati.

Prima del wipe conservare conoscenza, fonti e ripresa nel progetto, completare il versionamento manuale e la sua impronta. L’attuale sessione si potrà rimuovere solo dopo la sua uscita; le altre sessioni vive restano protette. Il comando CLI codex delete SESSION elimina una sessione salvata e non equivale a salvare o chiudere il progetto. La verifica del30/10 nel progetto home-lab ha eseguito soltanto l’anteprima: nessuna rimozione dichiarata.

## Cassetta comune,30/10/2026

posta-sessioni.py registra partecipanti e offre elenca, invia e leggi con archiviazione esplicita; dal 2026-11-09 la cassetta vive per difetto sotto la radice di `ProgramData`, fuori dai dischi di progetto, e `invia` rifiuta senza scavalcamento un messaggio che contenga dati reali, con gli schemi del pacchetto `anonymization` e nominando le sole categorie trovate; Posta-Sessioni.ps1 collega entrambi i launcher. Avvia-Claude.ps1 e Avvia-Codex.ps1 espongono PROJECT_AGENT_MAILBOX_ROOT/ID/TOOL e concedono il solo percorso aggiuntivo tramite --add-dir. I messaggi restano dati da verificare, non ordini da eseguire. [Contratto e limiti](../../../docs/allineamento-e-posta-sessioni.md), incluso il fatto che registrazione non equivale a heartbeat e che le sessioni già aperte non acquisiscono i nuovi permessi.

Dal 2026-11-17, su decisione del proprietario, la cassetta non è un secondo magazzino. Si apre solo in una cartella che è un progetto istanziato dal template, cioè che ha `.claude/PROJECT-SYSTEM.md`: altrove il launcher non scrive niente fuori dalla cartella e non chiede di aggiungere percorsi, perché la registrazione porta il percorso del progetto e la leggono tutte le sessioni della macchina, comprese quelle dei progetti aziendali. Il caso che l'ha prodotto è un avvio da una cartella di documenti privati. Ogni registrazione porta il PID del launcher, e `posta-sessioni.py pulisci` toglie le sessioni finite con i loro messaggi, cioè quelle congedate e quelle registrate il cui processo non esiste più, lasciando intatte le vive, che continuano a parlarsi. La chiamano il launcher all'avvio e all'uscita, dopo il congedo, e il blocco 5 di `session-end-wipe.ps1` a ogni chiusura di sessione. Una registrazione scritta prima di questa versione non ha PID e la chiude la scopa per età. Una cartella creata da una sessione avviata come amministratore non si toglie da un processo normale: `pulisci` la conta a parte e prosegue, e la radice della cassetta deve dare all'utente il pieno controllo ereditabile, che si concede una volta con `icacls <radice> /grant <utente>:(OI)(CI)F /T` da amministratore.

Dal 2026-11-19 la scopa per età non chiude una registrazione il cui PID è vivo: fino a quel giorno non lo guardava, e ogni sessione aperta da più di sette giorni avrebbe perso la cassetta al primo avvio successivo, misurato su due sessioni Codex vive dal 12/11 (lezione L-053 di un progetto istanziato). Una registrazione scritta prima dei PID, di una sessione ancora viva, si completa con il PID del terminale che l'ha avviata, cioè il processo padre di `codex.js` o di `claude`, con la funzione `pubblica` dello strumento. Nello stesso giorno `Pulisci-Codex.ps1` ha smesso di fermarsi al primo `codex delete` fallito: con la preferenza di errore a Stop, in Windows PowerShell 5.1 una riga di stderr di un comando nativo rediretta con `2>&1` ferma lo script, e ora l'esito si legge dal codice di uscita e un fallimento si dice e non ferma le altre sessioni (L-054). `codex delete` può togliere il file della conversazione e fallire sull'indice tenuto aperto dal demone: l'esito si verifica rilanciando con `-DryRun`.

L'hook di Codex installato in esercizio non punta alla copia nel template ma a una copia in una cartella che solo l'amministratore scrive, per la ragione detta sopra sulla fiducia per comando: su Windows `C:/ProgramData/riserva-agenti/riserva-agenti.py`, con la cartella protetta da `icacls` e il `hooks.json` di ogni radice che passa `--radice` in modo esplicito. Aggiornare lo strumento vuol dire ricopiarlo da un terminale amministratore e rilanciarne `--autotest`; il comando dell'hook non cambia, quindi Codex non chiede una nuova approvazione, ed è proprio per questo che la copia deve stare dove nessuna sessione scrive.

## Progetti MCP disponibili anche agli account nuovi

Gli installatori dei due agenti leggono, se presente, `%LOCALAPPDATA%/agenti-terminale/progetti.json`. È configurazione privata della macchina, non memoria dell’agente. Il registro contiene soltanto percorsi assoluti già autorizzati e nomi dei server attesi, senza token. Lo schema è `agent-projects-0.1`; `projects` è una lista di oggetti con `path` e `mcp_servers`, per esempio `{"path":"<RADICE-PROGETTO>","mcp_servers":["<SERVER>"]}`. Il percorso reale si compila sulla macchina. Se il registro esiste serve Python 3.11 o successivo.

`Progetti-Agenti.ps1` chiama `configura-progetti.py` anche per gli installatori invocati direttamente: la catena della macchina e quella del template applicano la stessa procedura. Per Codex aggiunge la fiducia ai soli progetti elencati dopo aver verificato le definizioni MCP locali. Una fiducia esistente diversa blocca l’operazione; non viene trasformata silenziosamente in fiducia. Per Claude verifica definizioni e abilitazioni di progetto, che la nuova radice ritrova quando apre quel progetto. Il normale login dell’account e l’eventuale dialogo iniziale del client restano parte dell’apertura, senza approvazioni generali aggiunte.

Non si copiano file di autenticazione, token NAS o server MCP globali da un account esistente. I servizi e i relativi segreti rimangono nel progetto proprietario; la scelta dell’account dell’agente non cambia l’identità del servizio. `-Verifica` legge soltanto. In applicazione si conservano backup della configurazione Codex prima dell’aggiunta; una seconda esecuzione non aggiunge doppioni. `-Forza` riapplica il registro dopo la configurazione di riferimento. Il ripristino su un’altra macchina richiede ricreare il registro con percorsi autorizzati e ripristinare separatamente i progetti e le loro credenziali.

Le prove usano profili temporanei, e dal 2026-11-16 `chiudi` le esegue nel template a ogni commit, insieme a quelle di `riserva-agenti.py`, attraverso `.claude/templates/tools/test-agenti-terminale.py`. Una esegue l’installatore Codex reale per una radice nuova e controlla che il progetto sia fidato, mantenendo assente il login. Un difetto che omette il richiamo alla procedura fa fallire proprio questa prova; le altre coprono idempotenza, politica di approvazione invariata, credenziali intatte e conflitto di fiducia. Le definizioni condivise e la fiducia per progetto sono documentate in [Claude MCP](https://code.claude.com/docs/en/mcp) e [Codex MCP](https://developers.openai.com/codex/mcp); il registro e la riconciliazione sono scelte interne del pacchetto.

## Riserva dei subagent e plugin, uguali per i due agenti

Dal 2026-11-16, su richiesta del proprietario, ciò che è nativo di Claude Code deve valere anche per Codex, se serve attraverso il wrapper. Due cose seguono questa regola.

La riserva. In Claude Code la mod `instradamento-modelli` nega lo spawn dei subagent quando il limite del piano ha passato una soglia. Codex non offre un punto equivalente dentro la sessione, ma scrive nei propri file di sessione la percentuale usata delle due finestre del piano e accetta all'avvio `--disable multi_agent`, che toglie gli strumenti con cui apre altri agenti; `codex features list` lo conferma. `Avvia-Codex.ps1` chiede quindi a `riserva-agenti.py` prima di partire se la soglia è passata, e all'uscita gli fa registrare l'ultima lettura prima che la pulizia cancelli le sessioni. La soglia ha la stessa forma nei due client e si scrive con un comando solo, `python riserva-agenti.py imposta --settimanale 80`; `stato` mostra tutte le radici. I limiti sono tre: la lettura di Codex è dell'ultima sessione chiusa con il wrapper e non di adesso, la decisione vale per l'intera sessione, e una sessione avviata senza il wrapper non ha riserva. Diciassette prove interne; una finestra già azzerata, una lettura assente e una soglia assente non negano.

I plugin e i valori. `Installa-Plugin.ps1` legge un file JSON che sta nel repository di macchina, non nel template, con la soglia e l'elenco dei plugin per ciascun client, e li porta in ogni radice senza reinstallare ciò che c'è. `Installa-Agenti.ps1` lo richiama alla fine, cercando `agenti-macchina.json` nella cartella da cui è lanciato o nella sua sottocartella `scripts`, oppure dove indica `-Valori`; con `-Verifica` dice soltanto che cosa manca. La forma del file è nell'intestazione dello script.

Dentro la sessione di Codex: l'hook, provato dal vero e non installato da sé. Il wrapper decide all'avvio e solo per le sessioni che avvia lui. Dal 2026-11-16 esiste la strada che vale dentro la sessione e per qualunque avvio: Codex ha hook propri, e uno di tipo `PreToolUse` può negare una chiamata, e su Windows lo fa in modo affidabile solo con un JSON sullo standard output, come spiega la prova descritta qui sotto. `riserva-agenti.py hook` è quel comando: legge dallo standard input la chiamata, lascia passare tutto ciò che non è l'avvio di un subagent, e per quello legge la percentuale più recente dai file della sessione in corso, non quella dell'ultima sessione chiusa. `hooks-codex.esempio.json` è la definizione da copiare come `hooks.json` nella radice dell'account, dopo aver sostituito il percorso della cartella degli strumenti. Provato dal vero il 2026-11-17, in tre passaggi, con Codex 0.169 su Windows e la prova del livello privato del template, `_notes/prova-hook-codex/Prova-Hook-Codex.ps1`. Il proprietario ha approvato l'hook con `/hooks`, e l'hook è stato chiamato prima di ogni strumento. L'agente di prova in formato Codex, scritto come lo scrive `crea-agente`, è partito come subagent e ha risposto giusto. Il primo passaggio oltre soglia ha lasciato partire il subagent, perché Codex chiama lo strumento di delega `collaborationspawn_agent`, cioè il nome con davanti quello del suo gruppo, mentre la documentazione dice `spawn_agent`. Lo strumento ora riconosce ogni nome che finisce in `spawn_agent`, e il filtro dell'esempio è `^(.*spawn_agent|Agent)$`. Il secondo passaggio ha deciso di negare, ma Codex ha riportato «hook exited with code 1» e ha proseguito: su Windows l'uscita 2 si perde nella shell con cui Codex lancia il comando, e un hook che esce con un altro codice vale come guasto, che non blocca. Il diniego si consegna quindi come JSON di `PreToolUse` sullo standard output, `hookSpecificOutput.permissionDecision` uguale a `deny` con il motivo, e uscita 0, la forma che la documentazione indica come preferita. Il terzo passaggio ha mostrato «Blocked by hook» con il motivo, e il modello si è fermato senza fare il lavoro da sé. Le prove interne sono ventiquattro, e tornare al confronto esatto sul nome fa fallire la prova che porta il nome registrato dal vero. L'hook resta comunque fuori dagli installatori: ogni radice di account lo esegue solo dopo l'approvazione di una persona in `/hooks`, e la approvazione va rifatta se cambia il comando. Metterlo nelle tre radici è una scelta del proprietario; fino ad allora la strada che vale è il wrapper. La prova di questo pacchetto non si può fare da una sessione dell'agente: lanciare Codex saltando l'approvazione degli hook è stato rifiutato dal sistema di permessi il 2026-11-16, ed è giusto così. Lo stesso giorno il wrapper ha cominciato a spegnere due funzioni e non una, `multi_agent` e `multi_agent_v2`: Codex 0.169 dichiara deprecata la prima e stabile la seconda, e una riserva che ne chiude una sola smetterebbe di valere il giorno in cui il client accende l'altra.
