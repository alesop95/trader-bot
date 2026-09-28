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
| `.claude/templates/agenti-terminale/tools/Pulisci-Codex.ps1` | wipe selettivo degli store, con tre guardie |
| `.claude/templates/agenti-terminale/tools/Installa-Comandi.ps1` | scrive nel profilo PowerShell i comandi brevi per tutte le radici presenti |
| `.claude/templates/agenti-terminale/tools/Consumo-Agenti.ps1` | consumo di token di **tutte** le radici dei due agenti, radici di default comprese |
| `.claude/templates/agenti-terminale/codex-config.riferimento.toml` | configurazione di una radice Codex |
| `.claude/templates/agenti-terminale/codex-agents.riferimento.md` | `AGENTS.md` distribuito nelle radici: puntatore, mai copia |

## Che cosa NON contiene, e perché

**Nessun valore di macchina.** I due soli valori specifici sono i **prefissi degli slug da preservare** nel wipe, che dipendono dalle lettere di disco su cui vivono i progetti, e il **numero di radici**. Sono parametri, e vivono nel repository della macchina insieme al suo punto d'ingresso.

**Nessuna credenziale, mai.** Il ripristino ricostruisce radici e configurazioni, non gli accessi: si rifà un login per radice e per agente. Non è un limite ma la scelta corretta, e vale dirla per esteso perché la tentazione opposta è forte: una credenziale copiata da una macchina all'altra è una credenziale uscita dal proprio custode, e sopravvive in un backup molto più a lungo della ragione per cui era stata copiata.

**Nessun orchestratore.** Far lavorare più agenti insieme su un compito è materia del pacchetto `lavoro-a-lotti`, che poggia su questo ma non lo richiede.

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
