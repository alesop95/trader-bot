# Far parlare due sessioni: che cosa esiste, che cosa no, e il vincolo che decide il disegno

> Su una macchina con N radici di Claude Code e M radici di Codex, **un solo canale fra sessioni esiste davvero ed è nativo**: quello fra sessioni Claude Code. Tutto il resto va costruito, e il vincolo che ne decide la forma non è il trasporto: è la sandbox di Codex. Questo documento misura ciò che c'è, spiega perché una delle due strade ovvie è una trappola, e descrive il disegno che resta.

Materia affine al resto del pacchetto, che tiene isolate e ripulite le radici dei due agenti. Qui non si parla di isolamento ma del suo opposto: come far passare informazione *fra* sessioni che il pacchetto tiene separate.

## Le tre combinazioni, e solo una funziona

| Direzione | Stato | Come |
|---|---|---|
| Claude Code → Claude Code | **nativo, funzionante** | `ListAgents` per scoprire, `SendMessage` per inviare |
| Claude Code ↔ Codex | **inesistente** | nessun canale comune |
| Codex → Codex | **non esposto** | il demone `app-server` è impiantistica interna, non un bus |

La prima riga non è teorica. Il 2026-10-26 due sessioni Claude Code indipendenti su questa macchina hanno diagnosticato in coppia un guasto hardware scambiandosi cinque messaggi, senza aprire alcun subagent. Ciascuna ha corretto almeno un errore dell'altra, e l'ordine definitivo dei fatti è emerso solo incrociando un dato di registro di una sessione con gli eventi disco al millisecondo dell'altra. **Il canale nativo regge lavoro vero, non solo segnalazioni.**

Il modo di indirizzare è il nome di sessione, non un percorso: `ListAgents` elenca i pari vivi con nome e riferimento breve, e il nome è l'indirizzo. Una sessione occupata riceve comunque: i messaggi si accodano e si consegnano al suo giro di strumenti successivo.

## I due trasporti, osservati

Misurato su questa macchina, non dedotto dalla documentazione.

**Claude Code** apre una named pipe per sessione:

```
\\.\pipe\LOCAL\cc-msg-<32 cifre esadecimali>
```

Una per sessione viva, e l'indirizzo che compare nei messaggi in arrivo la riporta con il prefisso `uds:`. Quel prefisso è la cosa interessante per chi porta il template su Linux: l'astrazione è *socket di dominio Unix*, realizzata come named pipe su Windows. Il meccanismo è quindi concettualmente portabile, ma **non è stato verificato su Linux** e questa riga non va letta come se lo fosse.

**Codex** non apre nulla di simile. Ha invece, per ogni radice, un demone annunciato su file:

```
<CODEX_HOME>\app-server-control\app-server-control.sock    0 byte
<CODEX_HOME>\app-server-daemon\daemon.pid                  ~334 byte
```

Le sessioni Codex vive ascoltano su **TCP di loopback**, con porte assegnate dinamicamente.

## Perché non si costruisce un ponte sul demone di Codex

È la strada che viene in mente per prima, e va scartata. Tre ragioni, ciascuna sufficiente.

**L'annuncio non contiene un indirizzo.** Il file `daemon.pid`, nonostante le dimensioni, non ha né porta né token:

```json
{"pid":37040,"processStartTime":"...","executableIdentity":{"digest":[...],"path_digest":[...]}}
```

È un'asserzione di identità dell'eseguibile, non un punto di contatto. La porta su cui ascolta una sessione viva va scoperta altrove, e il modo non è documentato.

**Il protocollo è privato e fragile fra versioni.** Questo pacchetto già documenta, nella sezione «Background server has incompatible feature settings», che cosa succede quando due versioni di Codex si incontrano sullo stesso demone. Un ponte costruito lì sopra si romperebbe a ogni aggiornamento, e si romperebbe in silenzio.

**Il template lo tratta già come impiantistica altrui.** `Pulisci-Codex.ps1` riconosce il demone solo per *non* toccarlo. Usarlo come bus contraddirebbe quella scelta.

> La regola generale, che vale oltre questo caso: **un canale fra agenti non si apre dentro l'impiantistica privata di uno dei due.** Si apre su un terreno che entrambi sanno già calpestare con gli strumenti che hanno.

## Il vincolo che decide tutto: la sandbox di Codex

Qui sta il punto che un disegno fatto a tavolino sbaglia.

Le radici Codex di riferimento girano con:

```toml
sandbox_mode = "workspace-write"

[sandbox_workspace_write]
writable_roots = []
network_access = false
```

Tradotto: **una sessione Codex può scrivere solo dentro il proprio spazio di lavoro.** Non su una cartella neutra condivisa, non in `%USERPROFILE%`, e non via rete perché la rete è chiusa.

Ne discendono due conseguenze che riguardano qualunque disegno, non solo quello proposto qui.

La prima: una cassetta postale condivisa collocata fuori dagli spazi di lavoro **non è scrivibile da Codex**, e il fallimento non è un errore di permessi del sistema operativo che si possa diagnosticare a colpo d'occhio: è la sandbox che rifiuta. Per abilitarla bisogna aggiungere quel percorso a `writable_roots`, che è una modifica **deliberata, visibile e da documentare**, non un dettaglio di installazione.

La seconda: siccome `network_access = false`, ogni disegno basato su loopback, HTTP o porte è escluso in partenza per Codex. Anche volendo ignorare la sezione precedente.

> **Il trasporto non è la variabile libera. Lo è il perimetro di scrittura.** Chi progetta partendo da «quale protocollo» ha già sbagliato la domanda: la domanda è «quale cartella vedono entrambi, e a che prezzo».

## Il disegno che resta: fermo posta su file

L'unico terreno comune fra uno strumento che parla su named pipe e uno chiuso in una sandbox di scrittura è **il filesystem**, dentro un perimetro concesso di proposito.

Forma minima:

```
<radice-concordata>/
  <nome-partecipante>/
    in/            messaggi da leggere
    letti/         messaggi consumati, spostati qui
```

Quattro regole, e nessuna di più:

**Un messaggio è un file, e nasce già completo.** Si scrive su nome temporaneo nella stessa cartella e si rinomina al nome definitivo. Il rinomino sulla stessa unità è atomico: un lettore non vede mai mezzo messaggio. Senza questo accorgimento serve un lock, e un lock fra processi che non si conoscono è il punto dove il disegno marcisce.

**Il nome ordina.** `<ISO8601>-<mittente>-<identificativo>.md` si ordina lessicalmente per tempo, senza leggere i contenuti.

**Leggere significa spostare.** Il consumatore sposta il file in `letti/`. Nessuno scrive mai nel file di un altro, quindi non serve coordinamento: ogni scrittore crea soltanto, ogni lettore muove soltanto ciò che è suo.

**Nessuno cancella la posta altrui.** La potatura è un'operazione separata, esplicita, e appartiene al proprietario della casella.

### Che cosa questo disegno non risolve, e va detto

**Non notifica.** Un file che compare non sveglia nessuno. Chi aspetta deve guardare.

**Non autentica.** Chiunque possa scrivere nella cartella può firmarsi con qualunque nome. Va bene fra sessioni dello stesso utente sulla stessa macchina, che è il caso d'uso; non va bene per nient'altro.

**Non ordina fra mittenti diversi.** Il timestamp nel nome è quello di chi scrive. Due sessioni con orologi allineati sulla stessa macchina sono abbastanza, ma è un'assunzione, non una garanzia.

**Non sostituisce il canale nativo fra sessioni Claude Code.** Quello spinge, notifica e indirizza per nome. Il fermo posta è il ponte *verso Codex*, non un rimpiazzo di ciò che già funziona meglio.

## L'asimmetria, di nuovo, e in una forma peggiore

Il pacchetto spiega altrove perché i motori di pulizia dei due agenti sono diversi: l'asimmetria non è sulla presenza dell'hook, ma su quanto l'hook riesce a coprire. Sulla comunicazione l'asimmetria è più netta.

**Claude Code riceve.** Un messaggio in arrivo si consegna da solo al giro di strumenti successivo, anche a sessione occupata. Non serve guardare una cassetta.

**Codex può solo guardare.** Non ha un canale di ingresso, quindi deve controllare la propria casella, e qualcuno deve dirglielo. Le due sedi possibili sono l'`AGENTS.md` della radice, che è istruzione permanente, oppure il wrapper di avvio, che è attuazione. La prima costa contesto a ogni sessione; la seconda costa un passaggio in più nel wrapper.

Ne segue una regola pratica: **le conversazioni importanti si iniziano da Codex verso Claude, non il contrario.** Chi scrive a Codex deve mettere in conto che la lettura avvenga molto dopo, o mai in quella sessione.

## Osservazione di macchina, 2026-10-26

Da verificare prima di appoggiarci qualcosa, perché è uno stato osservato e non una proprietà dello strumento.

Nessuna delle tre radici Codex di questa macchina contiene un `hooks.json`. Però la configurazione di una di esse porta ancora lo stato di un hook per un file che non c'è:

```toml
[hooks.state]
[hooks.state.'C:\Users\Utente\.codex-account2\hooks.json:session_end:0:0']
trusted_hash = "sha256:..."
```

Lo stato di fiducia di un hook sopravvive al file che lo definiva. Chi contasse su `SessionEnd` di Codex per notificare l'arrivo di posta troverebbe una configurazione che *sembra* dire che l'hook c'è. **Non si deduce la presenza di un hook dallo stato in `config.toml`: si guarda il file.**

## Come si misura se funziona

Un canale si dichiara funzionante quando regge una correzione, non quando consegna un messaggio.

La prova minima è questa: due sessioni ricevono lo stesso problema con fonti diverse, e si scambiano le evidenze. Il canale funziona se almeno una delle due **ritira un'affermazione** sulla base di ciò che ha ricevuto. Un canale che consegna soltanto conferme non è stato provato: è stato usato per il traffico facile.

Nella prova del 2026-10-26 entrambe le sessioni hanno ritirato qualcosa, e la ricostruzione finale conteneva un ordine di eventi che nessuna delle due possedeva da sola.

## Stato di questo documento

Studio e disegno, **non attuazione**. Il pacchetto non contiene oggi alcuno script di fermo posta, e l'elenco dei pezzi non ne cita. Chi lo realizza deve, nell'ordine: scegliere la radice condivisa, aggiungerla a `writable_roots` delle radici Codex interessate documentando la modifica, e decidere dove istruire Codex a guardare la casella.

Il canale nativo fra sessioni Claude Code, invece, è disponibile senza installare niente.

## Attuazione del30/10/2026

Lo studio precedente rimane la fotografia dei limiti osservati. Ora il pacchetto contiene posta-sessioni.py, Posta-Sessioni.ps1 e un launcher Claude parallelo a quello Codex. Il [contratto aggiornato](../../../docs/allineamento-e-posta-sessioni.md) descrive la cassetta, il perimetro --add-dir e le verifiche. La consegna su file è attuata; il polling ai giri di lavoro è esplicito e nessuna notifica push viene promessa. Non si presume che sessioni già aperte abbiano caricato il nuovo impianto.
