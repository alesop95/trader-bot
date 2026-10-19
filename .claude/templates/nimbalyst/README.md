# Pacchetto opzionale `nimbalyst`

> Spazio di lavoro desktop che fa lavorare in parallelo più agenti, Claude Code e Codex compresi, ciascuno in un worktree git separato. Il pacchetto non installa file nel progetto e non porta regole: contiene il rilevamento sulla macchina, la decisione da chiedere all'utente e il recap d'uso che il gate mostra quando l'utente lo adotta. Settore del catalogo: «Orchestrazione, sessioni e cataloghi di agenti». Fonti lette il 2026-10-16: `winget show --id Nimbalyst.Nimbalyst`, il README del repository `nimbalyst/nimbalyst` e le pagine `quickstart`, `worktrees` e `privacy` della documentazione su `nimbalyst.com/docs/`.

<!-- readme-summary: agenti in parallelo su worktree git separati in un'applicazione desktop nativa anche su Windows; se è già installata il gate chiede se usarla e ne mostra l'uso -->

## Quando il gate lo propone

Il trigger è quello del settore, cioè tre o più sessioni o rami paralleli sullo stesso progetto, con una condizione in più che lo rende diverso dagli altri strumenti del settore: se Nimbalyst è già installato sulla macchina, il gate lo dice e chiede all'utente se vuole usarlo per questo progetto, anche quando il trigger quantitativo non è raggiunto. La ragione è che uno strumento già presente non costa installazione, e non dirlo lascia all'utente un'applicazione che non sa di poter usare. La risposta, sì o no, si registra come ogni altra risposta del gate.

Il rilevamento è in sola lettura. Su Windows:

```powershell
winget list --id Nimbalyst.Nimbalyst
```

Se il comando non lo trova si guarda anche la cartella di installazione per utente, che esiste quando l'installer è stato scaricato a mano invece che da winget:

```powershell
Test-Path "$env:LOCALAPPDATA\Programs\Nimbalyst"
```

Su macOS l'applicazione sta in `/Applications/Nimbalyst.app`; su Linux si guarda il pacchetto `.deb` con `dpkg -l nimbalyst` oppure la presenza dell'AppImage dove l'utente l'ha messa. Se è installato e winget segnala una versione disponibile più recente, il gate lo dice insieme alla domanda, senza aggiornare.

## Installazione, se l'utente la chiede

Su Windows si installa da winget, che verifica l'impronta SHA-256 dell'installer contro quella dichiarata nel manifest prima di eseguirlo:

```powershell
winget install --id Nimbalyst.Nimbalyst
```

L'aggiornamento di una copia già presente è `winget upgrade --id Nimbalyst.Nimbalyst`. Su macOS e Linux si scarica dalla pagina delle release del repository `nimbalyst/nimbalyst` e si confronta l'impronta con quella pubblicata prima di eseguire. Requisiti dichiarati: Windows 10 o successivo, macOS 12 o successivo, Linux con `.deb` o AppImage.

## Recap d'uso

Un progetto, per Nimbalyst, è una cartella aperta nell'applicazione: dal *Project Manager*, raggiungibile da *Window > Project Manager* o con `Ctrl+P`, si apre la cartella del repository. Gli agenti si autenticano in *Settings > Application > AI Providers*, con l'accesso di un piano Claude o ChatGPT oppure con una chiave API; per gli agenti integrati non serve aver installato la CLI, che resta un'opzione per i flussi che la richiedono. Su questa macchina, dove ogni account Claude ha la propria radice, conviene verificare quale account l'applicazione stia usando prima di aprire un progetto di lavoro, perché il login dell'applicazione è un asse distinto dalle radici di `agenti-terminale`.

Le due modalità che servono subito sono *Files*, `Ctrl+E`, dove si lavora su un file con un agente accanto e le sue modifiche compaiono come differenze rosse e verdi da accettare o rifiutare una per una, e *Agent*, `Ctrl+K`, dove si avviano, si cercano e si riprendono le sessioni. Una sessione nuova si apre con `Ctrl+N`, o con `Ctrl+Shift+N` da qualunque modalità, e il provider si sceglie nel compositore della sessione. `Ctrl+Shift+K` apre la bacheca delle sessioni, che le tiene in vista quando sono molte. `Ctrl+/` mostra tutte le scorciatoie. La documentazione le scrive con `Cmd`, che su Windows e Linux diventa `Ctrl`.

Il lavoro parallelo passa dai worktree, che richiedono la *Developer Mode* attiva e un repository git. Una sessione isolata si apre dal menu accanto a *New session* con *New Worktree*, `Ctrl+Alt+W`, e parte su un ramo nuovo; si apre anche da una voce del tracker o da una pull request. A lavoro finito si rivedono le modifiche nel pannello della sessione, si committano e si fondono nel ramo principale dallo stesso pannello. Due cautele dal sistema di progetto. Il commit fatto dall'applicazione è un commit come un altro, quindi vale l'identità git locale della skill `identita-git` e il divieto di attribuzioni dell'hook `commit-msg`, e un progetto che ha `chiudi` continua a preferirlo per le milestone sul ramo principale. E la memoria versionata descrive il ramo e non il progetto, come stabilisce la skill `alberi-di-lavoro`, che si carica appena un worktree esiste.

## Che cosa esce dalla macchina, e come si spegne

L'applicazione raccoglie dati d'uso anonimi; la documentazione dichiara che non includono contenuti dei file, percorsi, chiavi o token, e non dice se la raccolta sia attiva per default. Si spegne in *Settings > Application > Advanced > Analytics*, ed è il primo passo dopo l'installazione. Il canale di aggiornamento resta *stable* in *Settings > Advanced > Release Channel*.

La collaborazione di gruppo passa dal servizio di sincronizzazione di Nimbalyst, e i file del progetto vi entrano solo se promossi esplicitamente; la sincronizzazione fra dispositivi personali richiede un account, e l'uso locale no. Su una macchina che ospita repository di clienti si resta in uso locale: nessun account Nimbalyst, nessun team, nessuna app mobile, nessun link condiviso a file o sessioni. La scelta si verifica nelle impostazioni dopo l'installazione, perché la documentazione non dichiara lo stato predefinito di ogni servizio.

Il rilascio del 30 settembre 2026, versione 0.79.1, introduce l'estensione *Crew*, in alpha e spenta per default, con agenti che lavorano da soli a turni entro un budget di token. Resta spenta finché un progetto non ne decide l'uso con un limite di spesa dichiarato.

## Che cosa non fa

Non decide quando convenga avviare più agenti e quanto costi: è un lanciatore, e il criterio resta quello del settore e della regola `token-economy.md`. Non è un prerequisito, perché due agenti collaborano anche scambiandosi file nel repository. E non sostituisce `agenti-terminale`: usa gli agenti, non ricostruisce le loro radici dopo una formattazione.
