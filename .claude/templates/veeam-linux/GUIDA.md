# Veeam Agent for Linux: allestimento replicabile, e i punti dove ci si perde

> Guida del pacchetto `veeam-linux`. Non è un manuale del prodotto, che esiste ed è altrove: è la sequenza delle decisioni e delle trappole incontrate allestendo l'agente su macchine reali, con il sintomo di ciascuna e la sua causa. La procedura si esegue sulla macchina Linux da salvare; gli script del pacchetto ne attuano la parte meccanica e lasciano a chi esegue le tre decisioni che non si possono automatizzare.

## Il punto che decide tutto, e va deciso prima di installare

Veeam Agent for Linux esiste in due pacchetti alternativi che installano lo stesso programma e differiscono in una cosa sola, cioè come ottengono l'istantanea[^1] del volume da copiare. La scelta fra i due non è una preferenza e non si corregge dopo: determina che tipo di backup la macchina potrà fare.

Il pacchetto `veeam` porta con sé un modulo del kernel, che viene compilato sulla macchina al momento dell'installazione tramite DKMS[^2] e ricompilato a ogni aggiornamento del kernel. Con esso il backup a livello di volume è sempre possibile, su qualunque tipo di disco, e produce una immagine da cui si può ripartire da zero. Il prezzo è la dipendenza dal kernel, che è reale e non teorica.

Il pacchetto `veeam-nosnap` non porta alcun modulo. Non rinuncia però all'istantanea: rinuncia a prenderla da sé, e si appoggia a quella di LVM[^3] dove i volumi sono logici. Ne discende la regola che quasi nessuno scrive e che fa perdere un pomeriggio: su una macchina con partizioni semplici, cioè senza LVM, la variante senza modulo non può fare backup a livello di volume, e resta soltanto il livello di file.

| Dischi della macchina | Variante | Livello di volume | Livello di file |
|---|---|---|---|
| partizioni semplici | `veeam` con modulo | sì | sì |
| partizioni semplici | `veeam-nosnap` | no | sì |
| volumi LVM | `veeam` con modulo | sì | sì |
| volumi LVM | `veeam-nosnap` | sì, tramite LVM | sì |

La differenza fra i due livelli non è di grado. Il livello di volume copia il volume come blocchi e permette il ripristino su ferro nudo, cioè avviare un supporto di ripristino e riscrivere il disco fino a riavere la macchina avviabile. Il livello di file copia i file con permessi e proprietà, quindi conserva tutto il contenuto, ma il ripristino passa da una installazione nuova del sistema seguita dal riversamento dei file.

Esiste una terza via che conviene conoscere prima di scegliere, perché non compete con le altre due ma le completa. Dove il livello di volume non è disponibile, l'immagine avviabile si prende lo stesso con uno strumento che lavora a macchina spenta, tipicamente Clonezilla avviato da chiavetta, che copia le partizioni così come sono senza bisogno di alcun modulo e senza dipendere dal kernel installato. Costa la presenza fisica davanti alla macchina e un disco di destinazione collegato a lei, e la combinazione ragionevole è il livello di file come copia frequente e da remoto, l'immagine come fotografia presa nei momenti che contano, per esempio subito dopo aver finito di allestire un ambiente.

## Le tre verifiche che costano cinque minuti e ne fanno risparmiare molti

La prima è il tipo di volumi, che decide la tabella qui sopra. Il comando dice subito se esiste uno strato LVM fra la partizione e il filesystem.

```bash
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT
```

La seconda, necessaria solo se serve il livello di volume, è che il modulo sia compilabile. Servono gli header del kernel in uso e `dkms`, e serve soprattutto sapere che il modulo è software di terze parti che insegue il kernel: su una distribuzione appena uscita può non averlo ancora raggiunto. La verifica vera è la compilazione stessa, che avviene durante l'installazione ed è visibile.

```bash
uname -r
```

```bash
dpkg -l | grep linux-headers
```

La terza è lo spazio della destinazione, ricordando che un deposito posto sulla stessa macchina che si salva protegge dagli errori ma non dal guasto del disco, quindi è al più un luogo di transito.

Lo script `veeam-allestisci.sh controlli` esegue queste verifiche e stampa, oltre ai fatti, la variante raccomandata e un blocco di valori già compilato da rileggere e correggere. Raccomanda e non decide: la tabella qui sopra resta il criterio, e la correzione del blocco è il momento in cui le tre decisioni della sezione seguente vengono prese davvero.

## Le tre decisioni che cambiano da una macchina all'altra

La sequenza dei comandi non cambia mai: cambiano alcuni valori e cambiano tre decisioni, e vale raccoglierle qui perché chi esegue non debba estrarle leggendo la prosa.

La prima è il tipo di volumi, che decide se il backup a livello di volume sia possibile e quindi se si otterrà una immagine avviabile o soltanto i file. Su volumi LVM entrambe le varianti lo consentono; su partizioni semplici lo consente la sola variante con modulo del kernel, e solo se quel modulo compila contro il kernel in uso.

La seconda è quali filesystem esistano, che decide il valore di `INCLUDI`. Il parametro `--includeDirs` non dichiara se l'attraversamento si fermi al confine del filesystem, quindi ogni punto di innesto che si vuole salvare va nominato esplicitamente: su una macchina con la sola radice basta `/`, su una con `/home` separato servono `/` e `/home`, su una con `/var` o `/srv` separati vanno aggiunti anche quelli. Se l'attraversamento avviene i percorsi in più sono ridondanti e innocui, se non avviene sono indispensabili, quindi la forma esplicita è corretta in entrambi i casi.

La terza è dove mettere il deposito, che decide il valore di `ESCLUDI`. Un deposito collocato dentro un percorso incluso nel backup fa sì che il lavoro copi sé stesso, quindi o sta fuori da ciò che si salva, tipicamente su un disco distinto, oppure sta dentro e va escluso esplicitamente.

Restano invariabili, e vale saperlo perché toglie decisioni inutili: il nome del gruppo `veeam` e i permessi che l'agente impone al proprio binario e al proprio deposito, la richiesta di accettare due contratti al primo uso, il fatto che ogni sottocomando richieda privilegi oppure l'appartenenza al gruppo, e il punto di innesto predefinito `/mnt/backup` per il montaggio di un punto di ripristino.

## Il file dei valori

I valori si dichiarano una volta sola in un file e si caricano con `source`, invece di scriverli nella shell. La differenza non è di comodità: quelle variabili vivono nella shell in cui sono state scritte e in nessun'altra, quindi chiudere il terminale o aprirne un secondo le fa sparire, e i comandi che seguono fallirebbero in modi che sembrano scollegati dalla causa. Il modello è `valori.example.sh`, da copiare accanto agli script e adattare.

```bash
source ./valori.sh
```

Il file contiene valori che descrivono una macchina reale, cioè il nome dell'host, i percorsi e la destinazione esterna, quindi non va versionato in un repository pubblico: il posto giusto è il livello privato del progetto, tipicamente `_notes/`.

## La sequenza operativa, dal nulla all'archivio riletto

Qui non si spiega, si esegue: le spiegazioni stanno nelle sezioni precedenti e nel troubleshooting più sotto. Ogni fase ha accanto il sottocomando dello script che la attua, per chi preferisce lo script ai comandi a mano; i comandi restano scritti per esteso perché uno script che nessuno sa rifare a mano è una scatola nera, e perché il troubleshooting si legge sui comandi.

Una nota sui privilegi, perché cambia quanto la procedura sia comoda. I comandi che seguono portano `sudo`, ed è la forma che funziona sempre; da una sessione aperta dopo l'installazione del pacchetto, però, `sudo` non serve, perché l'installazione aggiunge l'utente al gruppo `veeam` e il binario appartiene a quel gruppo. La differenza conta nella pratica, perché senza `sudo` l'intera sequenza, compresi l'avvio del lavoro e il montaggio del punto, si esegue da una sessione SSH non interattiva, quindi si automatizza; con `sudo` serve un terminale dove digitare una password.

### Fase 0, accertare i presupposti

Il tipo di volumi decide se il livello di volume sia possibile, e va letto prima di installare qualunque cosa. L'elenco dei filesystem montati è la fonte da cui si costruisce il valore di `INCLUDI`, e serve anche a scegliere dove collocare il deposito.

```bash
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT
```

```bash
df -hT -x tmpfs -x devtmpfs -x squashfs
```

Solo se si intende usare la variante con modulo del kernel, i due comandi che dicono se esistano i presupposti per compilarlo.

```bash
uname -r
```

```bash
dpkg -l | grep linux-headers
```

Va cercato qui anche un fenomeno che non si vede in nessuno dei comandi precedenti e che si paga per intero alla prima corsa, cioè i file sparsi: la voce K del troubleshooting dice che cosa sono e come si leggono, e il comando che li trova è questo.

```bash
find / /home -xdev -type f -size +2G -printf '%s\t%b\t%p\n'
```

Lo stesso esito, con la variante raccomandata, il blocco di valori proposto e i file sparsi, si ottiene con il sottocomando `controlli`.

### Fase 1, installare

Il repository di Veeam non è legato a una versione di Ubuntu: dichiara una sola distribuzione chiamata `stable` con un solo componente chiamato `veeam`, quindi una distribuzione nuova non è di per sé un ostacolo. Lo si aggiunge con un pacchetto che porta anche la chiave di firma. La versione di quel pacchetto va verificata sul sito del produttore, perché è l'unico valore della sequenza che invecchia da solo, e vive nel file dei valori come `VERSIONE_REPO` proprio per non restare sepolta in un comando.

```bash
curl -sSL -o /tmp/veeam-release-deb.deb "https://repository.veeam.com/backup/linux/agent/dpkg/debian/public/pool/veeam/v/veeam-release-deb/veeam-release-deb_${VERSIONE_REPO}_amd64.deb"
```

```bash
sudo dpkg -i /tmp/veeam-release-deb.deb
```

```bash
sudo apt update
```

```bash
sudo apt install -y "$PACCHETTO"
```

```bash
systemctl is-active veeamservice
```

Una avvertenza sulle dipendenze dichiarate, che su una distribuzione recente sembrano mancanti e non lo sono. Il pacchetto nomina `libfuse2` e `libgcc1`, che sulle versioni recenti di Ubuntu non esistono più con quel nome: sono stati sostituiti da `libfuse2t64` e `libgcc-s1`, i quali però dichiarano di fornire i nomi vecchi, quindi `apt` risolve da sé. Leggere quei nomi nell'elenco delle dipendenze e concludere che il prodotto sia incompatibile è un errore facile.

Il sottocomando `installa` esegue questa fase.

### Fase 2, accettare i due contratti

Il primo comando privilegiato dopo l'installazione chiede l'accettazione di due contratti e attende `yes` per ciascuno. Va eseguito senza redirezione, altrimenti le domande finiscono nel file e il terminale sembra bloccato: è la voce A del troubleshooting. Qualunque sottocomando va bene, e conviene usare quello che serve comunque subito dopo.

```bash
sudo veeamconfig repository list
```

### Fase 3, creare il deposito

Il deposito può essere locale, su NFS o su una condivisione SMB, e la scelta non è di comodità: un deposito remoto fa nascere l'archivio già fuori dalla macchina che si salva, quindi la fase 7 di questa guida decade insieme al rischio che la fase 7 esiste per coprire. Dove una condivisione esista, è la forma giusta.

Nella forma locale il comando crea anche la cartella se non esiste, e la assegna a `root:veeam`.

```bash
sudo veeamconfig repository create --name "$NOME_DEPOSITO" --location "$DEPOSITO" --type local
```

Nella forma SMB il percorso si scrive come `//server/condivisione`, eventualmente con una sottocartella, e le credenziali si passano con il solo nome utente: `--password` va passato senza valore, perché è quello che fa comparire il prompt, e così la password non entra né nella riga di comando né nella cronologia della shell. Il parametro `--domain` serve solo dove l'account appartenga a un dominio, e su un account locale di un NAS di norma si omette. Questa forma richiede `cifs-utils` installato, perché l'agente monta la condivisione con il client cifs del kernel.

```bash
sudo veeamconfig repository create --name "$NOME_DEPOSITO" --type smb --location "$DEPOSITO" --username "$SMB_UTENTE" --password
```

Un dettaglio che la documentazione non dichiara e che conviene sapere prima di provare: una sottocartella dentro la condivisione, cioè `//server/condivisione/cartella`, funziona, perché il client cifs la gestisce come prefisso del percorso. Misurato il 2026-10-15 su un NAS con l'agente `6.3.2.1501`.

```bash
sudo veeamconfig repository list
```

Il secondo comando è l'unica misura che distingue un deposito registrato da una cartella con il nome giusto, e la differenza conta dopo ogni ciclo di purga e reinstallazione, come dice la voce E del troubleshooting.

### Fase 4, creare il lavoro

Un lavoro a livello di file su tutto il sistema, senza pianificazione, quindi manuale. I percorsi inclusi sono quelli decisi nella sezione sulle tre decisioni, e vanno nominati tutti.

```bash
sudo veeamconfig job create fileLevel --name "$NOME_LAVORO" --repoName "$NOME_DEPOSITO" --includeDirs "$INCLUDI" --excludeDirs "$ESCLUDI" --nosnap --maxPoints "$PUNTI"
```

```bash
sudo veeamconfig job list
```

Dove la variante con modulo sia disponibile e si voglia il livello di volume, il sottocomando cambia e i percorsi spariscono.

```bash
sudo veeamconfig job create volumeLevel --name "$NOME_LAVORO" --repoName "$NOME_DEPOSITO" --backupAllSystem --maxPoints "$PUNTI"
```

Se la variante installata non può fare il livello di volume, il rifiuto è esplicito e nomina i dispositivi che non sa trattare, ed è il messaggio da riconoscere perché è il punto in cui ci si accorge di aver scelto la variante sbagliata. Il lavoro non viene creato e l'elenco dei lavori resta vuoto: non c'è nulla da correggere nella configurazione, va cambiata la variante oppure il livello.

```
Item cannot be backed up without veeam snapshot kernel module: /dev/nvme0n1p2, /dev/nvme0n1p4
```

Una decisione che si prende qui e non dopo è la cifratura, con `--setEncryption`: si cifra il lavoro e non l'archivio, quindi attivarla in seguito significa rifare il backup. Il criterio sta nella voce H del troubleshooting. Il sottocomando `configura` esegue le fasi 3 e 4 insieme, saltando ciò che esiste già.

### Fase 5, eseguire

Il comando restituisce subito l'identificativo di sessione e il percorso dei registri, e il lavoro prosegue in secondo piano.

```bash
sudo veeamconfig job start --name "$NOME_LAVORO"
```

L'avanzamento si segue da qualunque sessione, anche non privilegiata, con due comandi. Il primo dice quanto è stato scritto, il secondo dice se il lavoro sia ancora in corso: quando non stampa alcuna riga, è finito.

```bash
df -h "$DEPOSITO"
```

```bash
ps -eo etime,cmd | grep -E "veeamjobman|veeamagent" | grep -v grep
```

A corsa finita l'esito dichiarato si legge così, e va letto: un lavoro che finisce non è un lavoro che riesce, perché lo stato può essere anche `Warning` o `Failed`.

```bash
sudo veeamconfig session list
```

### Fase 6, rileggere l'archivio, che è la parte che rende il backup tale

Si prende l'identificativo del backup, poi quello del punto di ripristino, poi si monta il punto. Il montaggio espone il contenuto come filesystem percorribile e non scrive nulla sul sistema vivo; `restore` ed `export` non servono a questo scopo e su una macchina funzionante il primo è da evitare.

```bash
sudo veeamconfig backup list
```

```bash
sudo veeamconfig point list --backupId {IDENTIFICATIVO-DEL-BACKUP}
```

```bash
sudo veeamconfig point mount --id {IDENTIFICATIVO-DEL-PUNTO}
```

Il punto viene montato su `/mnt/backup`, che risulta `drwxr-xr-x` di `root:root`: il montaggio richiede privilegi, l'ispezione no, quindi tutto ciò che segue si può fare da una sessione ordinaria, anche remota.

Le tre verifiche che contano, in ordine di forza crescente. La prima è che ci sia ciò che si teme manchi, cioè il contenuto di ogni filesystem distinto dalla radice che si è scelto di includere. La seconda è il confronto per impronta fra sistema vivo e archivio, su file scelti in modo da coprire tutti i filesystem inclusi e più ordini di grandezza. La terza è il conteggio, che misura una cosa che le impronte non misurano: un confronto per impronta prova che i file scelti sono identici e non dice nulla dei file non scelti, quindi da solo non distingue una copia integrale da una copia parziale fatta bene.

```bash
for f in /etc/fstab "$HOME/.bashrc"; do sha256sum "$f" "/mnt/backup$f"; done
```

```bash
echo "vivo=$(find "$HOME" | wc -l) backup=$(find "/mnt/backup$HOME" | wc -l)"
```

Va infine verificato che il deposito non sia finito dentro sé stesso, e si verifica per assenza e non deducendolo dalla dimensione dell'archivio.

```bash
ls -A "/mnt/backup$DEPOSITO"
```

Il punto non va lasciato montato. Lo smontaggio è una chiusura di sessione e usa l'identificativo restituito dal montaggio, non quello del punto.

```bash
sudo veeamconfig session stop --id {IDENTIFICATIVO-DELLA-SESSIONE-DI-MONTAGGIO}
```

Lo script `veeam-verifica.sh` esegue l'intera fase, comprese le tre verifiche e lo smontaggio, e dichiara separatamente l'esito di ciascuna invece di riassumerle in un verde unico.

### Fase 7, portare l'archivio fuori dalla macchina

Un deposito sullo stesso disco che si salva protegge dall'errore e non dal guasto del disco, quindi questa fase non è facoltativa. Servono i due file, cioè l'archivio `.vbk` e il descrittore `.vbm`, perché senza il secondo il primo è un archivio che Veeam non sa più collocare.

L'utente non appartiene al gruppo `veeam` finché non lo si aggiunge, e l'appartenenza a un gruppo si legge al login e non ha effetto sulle sessioni già aperte.

```bash
sudo sh -c "usermod -aG veeam $(id -un); id $(id -un)"
```

Il trasferimento si fa poi dalla macchina di destinazione, con una sessione nuova. Il percorso del deposito contiene uno spazio, perché l'agente nomina la propria cartella unendo il nome della macchina e quello del lavoro, e su come proteggerlo vale la voce J del troubleshooting: un solo livello di virgolette, quelle della shell locale, e nessuna virgoletta in più per una shell remota che non esiste.

```bash
scp "<ALIAS-SSH>:<PERCORSO-DEPOSITO>/<NOME-CARTELLA>/<NOME-FILE>" "<DESTINAZIONE>"
```

La copia si verifica per impronta e non per dimensione: un trasferimento interrotto può lasciare un file della dimensione giusta, e su un archivio di backup la differenza fra una copia integra e una plausibile è tutto ciò che conta.

```bash
ssh "<ALIAS-SSH>" "sha256sum '<PERCORSO-DEPOSITO>/<NOME-CARTELLA>/<NOME-FILE>'"
```

```bash
sha256sum "<DESTINAZIONE>/<NOME-FILE>"
```

### Fase 8, la corsa successiva, e la sola decisione che porta con sé

Dalla seconda corsa in avanti le fasi da 0 a 4 non si rifanno, perché deposito e lavoro esistono già. Restano la fase 5 per eseguire, la 6 per rileggere e la 7 per portare fuori, identiche. Cambia una cosa sola, ed è una decisione che conviene prendere invece di ereditarla dal comando.

Senza opzioni, il lavoro produce un punto incrementale che dipende dal pieno precedente. Con l'opzione seguente produce un pieno nuovo e indipendente, che costa altrettanto spazio del primo e non eredita alcuna dipendenza.

```bash
veeamconfig job start --name "$NOME_LAVORO" --activeFull
```

Il criterio per scegliere non è lo spazio ma che cosa fotografa il punto precedente. Se il primo pieno ritrae uno stato che qualcuno vorrebbe davvero ripristinare, l'incrementale è la scelta economica e corretta. Se ritrae uno stato intermedio che nessuno vuole più, far dipendere il punto utile da quello inutile aggiunge una superficie di guasto senza aggiungere valore, e allora il pieno indipendente è la scelta giusta. Va inoltre ricordato che un punto incrementale non si porta fuori da solo: senza il pieno da cui dipende non ripristina nulla, quindi la copia esterna resta una catena e non un file.

Il numero di punti conservati è quello dichiarato alla creazione del lavoro con `--maxPoints`, e vale anche qui: con due punti e un pieno nuovo, il pieno precedente resta finché una terza corsa non lo espelle. Un controllo che chiude la corsa e costa un comando: i punti si elencano con il proprio tipo, e un pieno indipendente compare come `Full` e non come `Increment`.

## Troubleshooting: sintomo, causa, rimedio

Ogni voce nasce da un caso osservato su una macchina reale e non da una previsione. L'ordine è quello in cui i casi si incontrano percorrendo la sequenza.

### A, il comando resta appeso senza stampare nulla

Sintomo: il primo sottocomando privilegiato dopo l'installazione non restituisce il prompt e non mostra niente. Causa: l'agente chiede l'accettazione di due contratti, prima quello del prodotto e poi le note sui componenti di terze parti, e attende `yes` per ciascuno; se il comando redirige l'uscita su un file, la domanda finisce nel file mentre la risposta è attesa dal terminale. Rimedio: rispondere `yes` due volte al buio, oppure interrompere e rieseguire senza redirezione.

La diagnosi, se non si sa che cosa stia aspettando, è leggere il file di destinazione da un'altra sessione: le ultime righe contengono la domanda. Regola generale che ne discende: un comando che redirige l'uscita non deve mai essere il primo contatto con un programma che non si conosce. Il testo dei contratti, se si vuole leggerlo prima, sta in `/usr/share/veeam/EULA` e in `/usr/share/veeam/3rdPartyNotices.txt`, entrambi leggibili senza privilegi.

Va saputo che l'accettazione non sopravvive a una purga dei pacchetti, quindi questo sintomo può ricomparire molto dopo l'installazione, ed è il segnale della voce E.

### B, `veeamconfig: Permission denied` da utente normale

Sintomo: qualunque sottocomando, compreso `--help`, risponde con un rifiuto di permesso. Causa: `veeamconfig` e `veeam` sono collegamenti simbolici allo stesso binario `/usr/sbin/veeamworker`, che ha permessi `-rwxr-x---` e appartiene a `root:veeam`; il rifiuto arriva dal filesystem prima che il programma parta, ed è per questo che il messaggio è quello della shell.

Il rimedio non è `sudo`, o non è solo quello. Il gruppo `veeam` esiste proprio per questo, e da una sessione che lo porta il binario si esegue senza privilegi: misurato su una macchina reale da una sessione SSH ordinaria, l'elenco dei depositi, quello dei lavori, l'avvio del lavoro, il montaggio del punto di ripristino e la chiusura della sessione di montaggio riescono tutti con stato zero.

Sull'appartenenza al gruppo vale però un avvertimento che costa un'ora se si dà per scontato, e che una stesura precedente di questa voce dava per scontato. Non è vero che l'installazione del pacchetto aggiunga l'utente al gruppo: misurato il 2026-10-15 su Ubuntu 26.04 con l'agente `6.3.2.1501`, il gruppo viene creato e resta vuoto, e `getent group veeam` risponde `veeam:x:981:` senza alcun membro. Su altre macchine l'utente vi si trova, quindi il comportamento non è uniforme e la sola cosa sensata è guardare invece di assumere. Dove manchi, lo si aggiunge una volta sola.

```bash
sudo usermod -aG veeam "$(id -un)"
```

In entrambi i casi serve poi una sessione nuova, e questa è la parte che non dipende dalla distribuzione: un processo riceve i propri gruppi quando la sessione nasce e non li rilegge mai più, quindi la sessione da cui si installa non li avrà finché resta aperta. Dove non si voglia o non si possa aprirne una, `sudo` resta la via che funziona subito.

Un modo di misurare male questo caso merita una riga, perché costa tempo. Passando l'uscita a un altro comando, per esempio `head`, lo stato restituito è quello dell'ultimo elemento della pipeline e non quello di `veeamconfig`, quindi `$?` risponde zero mentre il comando è fallito. Eseguito da solo, lo stato è `126`, che in una shell POSIX significa esattamente comando trovato ma non eseguibile.

### C, `Item cannot be backed up without veeam snapshot kernel module`

Sintomo: la creazione di un lavoro a livello di volume fallisce nominando i dispositivi, e l'elenco dei lavori resta vuoto. Causa: la variante `veeam-nosnap` non prende istantanee da sé e si appoggia a quelle di LVM, che su partizioni semplici non esistono. Rimedio: o si passa alla variante con modulo del kernel, o si rinuncia al livello di volume e si usa quello di file.

### D, il modulo del kernel non compila

Sintomo: l'installazione della variante con modulo termina con un errore di DKMS. Causa: da distinguere leggendo `/var/lib/dkms/<modulo>/<versione>/build/make.log`. Rimedio: se gli errori riguardano un ambiente incompleto, per esempio header mancanti o un compilatore assente, si installa ciò che manca e si riprova; se nominano funzioni del kernel dichiarate implicitamente, membri di strutture che non esistono o funzioni chiamate con un numero di argomenti diverso da quello atteso, il modulo è scritto per una generazione di kernel precedente e non c'è nulla da aggiustare.

Su un caso osservato con un kernel della serie 7.0 e agente `6.3.2.1405` entrambi i moduli disponibili hanno fallito nel secondo modo. Il modulo storico `veeamsnap` chiama `blkdev_get_by_dev`, `blkdev_put` e `bio_set_op_attrs`, tutte rimosse, e passa tre argomenti a `bio_alloc_bioset` dove ora ne servono cinque. Il modulo nuovo `blksnap`, che è la riscrittura per i kernel moderni e si prova come alternativa perché il pacchetto `veeam` lo accetta al posto dell'altro, fallisce a sua volta perché cerca un'intestazione `linux/blk_snap.h` che non esiste, usa un membro `bd_inode` rimosso da `struct block_device` e ridefinisce una funzione che ora il kernel fornisce.

La conclusione, che vale come regola e non come resoconto, è che su una distribuzione molto recente il backup a livello di volume con Veeam può semplicemente non essere disponibile, e che questo si accerta in mezz'ora provando, non si prevede leggendo la matrice di compatibilità del produttore, che elenca le distribuzioni supportate e non quelle appena uscite.

La via di uscita dallo stato rotto è togliere tutto ciò che riguarda il modulo e reinstallare la variante che non ne ha bisogno, sapendo che quella purga innesca la voce E. Va notato che il passaggio alla variante con modulo trascina con sé l'intera catena di compilazione, cioè compilatore, librerie di sviluppo e `dkms`, per oltre duecento megabyte: se il tentativo fallisce e non si intende ripeterlo, quel materiale resta installato e va rimosso deliberatamente, perché altrimenti finisce anche dentro il backup.

```bash
sudo apt purge -y blksnap veeam veeamsnap
```

```bash
sudo apt install -y veeam-nosnap
```

### E, dopo una purga e reinstallazione il deposito e i lavori non ci sono più

Sintomo: i contratti vengono richiesti di nuovo, e `veeamconfig repository list` e `veeamconfig job list` stampano la sola riga di intestazione, pur essendo stati creati in precedenza. Causa: le due varianti del pacchetto condividono le cartelle di stato `/etc/veeam` e `/var/lib/veeam`, quindi la purga dell'una cancella la configurazione dell'altra, anche quando l'altra è stata soltanto rimossa e mai purgata. Rimedio: ricreare deposito e lavoro, cioè rieseguire le fasi 3 e 4.

La trappola vera di questa voce non è la perdita ma il modo in cui si nasconde. La purga rimuove la configurazione e non tocca la cartella dei dati, quindi resta sul disco una directory con il nome giusto, i permessi giusti e nessun deposito dietro: un `ls` risponde che c'è. La verifica corretta è chiedere al programma e non al filesystem, e costa quanto un `ls`. Regola generale: dopo ogni ciclo di purga e reinstallazione la configurazione va riverificata con i comandi del programma, perché nulla nell'esito dell'installazione segnala la perdita.

### F, l'archivio cresce e non si ferma

Sintomo: lo spazio occupato dalla destinazione aumenta ben oltre la dimensione della sorgente. Causa: il deposito si trova dentro un percorso incluso nel backup, quindi il lavoro sta copiando sé stesso. Rimedio: escludere il percorso del deposito con `--excludeDirs`. La verifica non è che l'archivio smetta di crescere, che è solo un indizio, ma che il percorso del deposito sia assente dentro il punto montato.

### G, un filesystem distinto potrebbe non entrare

Sintomo: nessuno, ed è il problema. L'aiuto di `--includeDirs` descrive il parametro come elenco di directory separate da virgola e non dichiara se l'attraversamento si fermi al confine del filesystem. Causa potenziale: su una macchina con `/home` o `/var` su partizione separata, `--includeDirs /` da solo potrebbe non includerli, e il backup riuscirebbe dichiarando successo. Rimedio: nominare esplicitamente ogni punto di innesto da salvare. Verifica: cercare dentro il punto montato un percorso che esiste solo sulla partizione in questione.

### H, i permessi dell'archivio e la destinazione esterna

Sintomo: nessuno finché l'archivio resta dov'è. Il file `.vbk` ha permessi `-rw-rw-rw-`, cioè leggibile e scrivibile da chiunque, e appartiene a `root:veeam`; la protezione effettiva viene dalla cartella che lo contiene, che è `drwxrws---` e nega l'accesso a chi non è nel gruppo `veeam`. Causa del problema: copiando l'archivio su un volume esterno con un filesystem che non conserva i permessi POSIX, quella protezione sparisce, e l'archivio contiene l'intero sistema, quindi anche `/etc/shadow`. Rimedio: decidere della cifratura prima di creare il lavoro, con `--setEncryption`, perché si cifra il lavoro e non l'archivio, quindi attivarla dopo significa rifare il backup.

### I, l'utente non riesce a leggere l'archivio per trasferirlo

Sintomo: `scp` o una copia da un'altra macchina falliscono per permesso negato sul file `.vbk`. Causa: la cartella del deposito è `drwxrws---` di `root:veeam` e l'utente non appartiene al gruppo. Rimedio: o si aggiunge l'utente al gruppo `veeam`, sapendo che l'appartenenza si legge al login e richiede quindi una sessione nuova per avere effetto, oppure si copia l'archivio in una cartella dell'utente con `sudo` e la si cancella dopo il trasferimento, al prezzo di occupare temporaneamente lo spazio una seconda volta.

### J, `scp` dice che il file non esiste, e il file esiste

Sintomo: `scp` verso un percorso remoto che contiene uno spazio risponde `No such file or directory`, mentre lo stesso percorso elencato con `ls` o `find` sulla macchina remota c'è ed è leggibile. Causa: dalla versione 9.0 OpenSSH usa per `scp` il protocollo SFTP invece del vecchio trasferimento su shell remota, quindi il percorso non viene più interpretato da alcuna shell sulla macchina remota. La ricetta tradizionale, cioè proteggere lo spazio con un secondo livello di virgolette destinato alla shell remota, produce ora un nome di file che contiene davvero i caratteri di virgoletta, e quel file non esiste.

Rimedio: un solo livello di virgolette, quello della shell locale, che passa il percorso come argomento unico. Se serve il comportamento vecchio, per esempio per usare un carattere jolly che qualcuno deve espandere, l'opzione `-O` forza il protocollo precedente e allora la shell remota torna a esistere e le due virgolette tornano necessarie. Il modo di accorgersene senza perdere tempo è che il messaggio nomina il percorso comprese le virgolette: leggerlo per intero, invece di fermarsi alle ultime parole, dice da solo qual è il problema.

### K, la corsa legge molto più di quanto la macchina contenga e non finisce mai

Sintomo: il registro della sessione dichiara `processed` molto maggiore del totale, per esempio 184 GB su un totale dichiarato di 58, e il contatore `transfer` non corrisponde alla dimensione del file che cresce sul deposito. La prima ipotesi che viene in mente è la voce F, cioè il lavoro che copia sé stesso, e di solito è sbagliata: si verifica in un comando guardando se il deposito sia montato dentro un percorso incluso.

Causa: un file *sparso*, cioè un file la cui dimensione apparente supera di molto i blocchi che occupa davvero. Una lettura sequenziale legge la dimensione apparente, mentre `du` conta i blocchi e il totale che il lavoro dichiara è calcolato a blocchi: lo scarto non si vede quindi da nessuna parte prima di provare. Caso osservato il 2026-10-15: il disco virtuale di un Docker Desktop abbandonato da nove mesi, `376,6` GB apparenti contro `1,7` GB occupati, che da solo moltiplicava per otto la durata di ogni corsa. Gli zeri si comprimono quasi a nulla, quindi l'archivio non si gonfia e il sintomo resta il solo tempo.

Rimedio: cercare i file sparsi prima di creare il lavoro e decidere di ciascuno, perché deciderlo dopo non ripulisce il pieno già scritto.

```bash
find / /home -xdev -type f -size +2G -printf '%s\t%b\t%p\n'
```

Il primo campo è la dimensione apparente, il secondo è il numero di blocchi da 512 byte: dove il primo supera largamente il secondo moltiplicato per 512, il file è sparso. Se il contenuto è vivo si include e si accetta il tempo di lettura; se è un residuo si mette fra le esclusioni.

### L, dopo una cancellazione il lavoro fallisce con `File exists`

Sintomo: subito dopo aver cancellato un backup con `backup delete --purge`, la corsa successiva fallisce con `Unable to create directory` e, come sola spiegazione, `File exists`. Il messaggio nomina l'effetto e non la causa, ed è il motivo per cui si perde tempo a cercare un residuo che non c'è.

Causa: la cancellazione sul deposito remoto non è istantanea, e la cartella del lavoro continua a essere presentata come esistente per qualche decina di secondi dopo che il comando è tornato. L'agente pretende di creare quella cartella lui e tratta `EEXIST` come errore fatale. Il caso osservato il 2026-10-15 misurava ventisei secondi fra la fine della cancellazione e l'avvio fallito.

Rimedio: aspettare e rilanciare. Prima di cercare un residuo conviene accertare che ci sia davvero, e la verifica va fatta dall'account con cui l'agente scrive, non da un altro: nel caso osservato un client SMB diverso continuava a elencare la cartella da una voce di directory rimasta in cache, mentre dall'account giusto non esisteva già più. Due viste che non concordano su un filesystem di rete sono quasi sempre una cache, non un permesso.

### M, l'health check non si riesce ad abilitare da riga di comando

Sintomo: `veeamconfig healthcheck enable --jobName <lavoro>` risponde `Argument [--jobName] requires following missing argument [--light]`, e aggiungendo `--light` risponde `Health check type 'Light' is not supported by the target repository`. Nessuna forma negata del flag viene accettata, né `--light false`, né `--light=false`, né `--light no`.

Causa: i due vincoli si incastrano. Il controllo sintattico pretende il flag, e la variante leggera esiste nel prodotto per i depositi a oggetti, non per una condivisione di rete o un percorso locale. Ne discende che su un deposito ordinario l'health check non è raggiungibile affatto da riga di comando, mentre l'impostazione esiste e si legge, perché `healthcheck show` dichiara una pianificazione con `Run health check automatically: disabled`.

Rimedio: l'interfaccia a caratteri `veeam`, che è l'altra via esposta dal prodotto, da una sessione che porta il gruppo `veeam`. Misurato il 2026-10-15 con l'agente `6.3.2.1501` su un deposito SMB.

Vale la pena sapere che cosa si perde, perché non è poco e non si vede. L'health check è la sola rilettura periodica dell'archivio già scritto: ricalcola le impronte dei blocchi e confronta con quelle registrate alla scrittura, quindi è l'unica cosa che scopre una corruzione silenziosa prima del giorno del ripristino. Su una catena *forever forward* il peso è maggiore che altrove, perché esiste un pieno solo e tutti i punti della finestra dipendono da lui: una corruzione lì non costa un giorno, costa l'intera finestra. Finché non è attivo, la rilettura resta un gesto manuale da programmare, cioè montare un punto e confrontare, come fa lo script di verifica.

## La pianificazione e la ritenzione

Un lavoro creato senza pianificazione resta manuale, e un backup manuale è un backup che qualcuno deve ricordarsi di fare. La pianificazione si aggiunge in un comando, e si legge in un altro.

```bash
sudo veeamconfig schedule set --jobName "$NOME_LAVORO" --daily --at "$ORARIO"
```

```bash
sudo veeamconfig schedule show --jobName "$NOME_LAVORO"
```

Sulla ritenzione vale una cosa che cambia il significato di tutto il resto. Senza un pieno attivo pianificato la catena è *forever forward*: esiste un pieno solo, e quando la finestra di `--maxPoints` si riempie il punto più vecchio viene fuso dentro di esso invece di accumulare pieni nuovi. Ne discendono due conseguenze pratiche. La prima è che `--maxPoints` su una macchina sempre accesa equivale a un numero di giorni, mentre sulle macchine spente di notte o nel fine settimana lo stesso numero copre un arco di calendario più lungo, ed è la ragione per cui due macchine con la stessa impostazione mostrano un numero diverso di file. La seconda è che ciò che entra nel pieno vi resta: escludere un percorso dopo non ripulisce il pieno già scritto, e per toglierlo davvero serve un pieno attivo nuovo.

```bash
sudo veeamconfig schedule activefull show --jobName "$NOME_LAVORO"
```

Quel comando va letto anche quando non si è pianificato nulla, perché dichiara `Run automatically: disabled`, ed è la riga che certifica che la catena resterà incrementale. Pianificare un pieno attivo è una scelta legittima e opposta, da prendere apposta: costa lo spazio di un pieno intero a ogni occorrenza e in cambio toglie la dipendenza dalla catena.

## Il criterio che chiude, e che quasi nessuno applica

Un backup non è tale finché non è stato riletto. La prova può essere parziale, cioè estrarre alcuni file dall'archivio e confrontarli con gli originali, e già questo distingue una copia da una speranza; la prova completa è ripristinare davvero, su una macchina di prova o dentro una macchina virtuale, e avviare il risultato. Finché quella prova non è stata fatta, la voce corrispondente del registro delle pendenze del progetto resta aperta, e il backup si dichiara allestito e non verificato.

[^1]: *istantanea*, in inglese snapshot - una vista congelata del contenuto di un volume in un dato momento, che permette di copiarlo mentre il sistema continua a scrivere. Senza di essa una copia presa a caldo può contenere file in stato intermedio.

[^2]: *DKMS*, Dynamic Kernel Module Support - il meccanismo con cui Linux ricompila automaticamente i moduli di terze parti quando il kernel cambia, così che non vadano reinstallati a mano a ogni aggiornamento.

[^3]: *LVM*, Logical Volume Manager - lo strato che su Linux permette di costruire volumi logici sopra una o più partizioni fisiche, con la possibilità di ridimensionarli e di prenderne istantanee. È la disposizione predefinita di molte installazioni, ma non di tutte.
