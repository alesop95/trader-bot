# Guida ai paradigmi di separazione fra test e produzione

> Documento tecnico-didattico del pacchetto `separazione-ambienti`. La norma `.claude/skills/separazione-ambienti/RIFERIMENTO.md` dice che cosa si sceglie e come si registra; questa guida spiega che cosa significa ogni scelta rispetto alle altre, perché funziona, che cosa costa e come fallisce. La skill `separazione-ambienti` attinge da qui le spiegazioni che dà durante il gate, così che la spiegazione in conversazione e quella sul disco siano la stessa. Le sigle fra parentesi quadre rimandano al registro `FONTI.md`: le `C` sono casi osservati nei progetti, le `F` fonti pubblicate.

## Perché si separa, e che cosa si separa davvero

Separare test e produzione significa far sì che un errore commesso provando non raggiunga le persone e i dati che dipendono dal sistema vero. La formulazione sembra ovvia, e la sua parte utile è la seconda metà: un errore raggiunge la produzione per un canale preciso, e la separazione vale quanto il canale meno separato. I casi osservati mostrano cinque canali distinti, e conviene nominarli perché ogni paradigma di questa guida ne chiude alcuni e ne lascia aperti altri.

Il primo è il codice: una modifica non provata che finisce nell'artefatto che gira in produzione. Il secondo sono i dati: una prova che scrive nella base dati vera, o che invia posta ai clienti veri partendo da dati copiati. Il terzo è l'identità: due ambienti che condividono la registrazione presso il fornitore di identità condividono segreti e chiavi di firma, e un utente autenticato in prova può ritrovarsi in produzione. Il quarto è la rete: un ambiente di prova raggiungibile da chiunque accanto alla produzione espone ciò che la produzione protegge. Il quinto sono le risorse: due ambienti sulla stessa macchina si contendono memoria e processore, e un carico di prova rallenta gli utenti veri.

Un paradigma di separazione è una scelta su quali di questi canali chiudere, con quale strumento e a quale costo. La sovrapposizione che sdoppiava il solo frontend condividendo il backend [C4] chiudeva il primo canale per metà e lasciava aperti il secondo e il terzo, ed è per questo che sembrava una separazione e non lo era.

## Come si legge questa guida

La separazione si compone di quattro scelte indipendenti, una per asse. L'asse R dice dove girano gli ambienti, l'asse P come il codice passa dall'uno all'altro, l'asse D da dove vengono i dati di prova, l'asse L come stanno i sorgenti sulla macchina di chi sviluppa. Un progetto sceglie una forma per asse, e la combinazione si scrive con le sigle, per esempio `R2 a richiesta, P1, D0, L1`.

Ogni forma si descrive con gli stessi campi, così che due forme si confrontino campo per campo. *Che cos'è* la definisce. *Che cosa significa sceglierla* la mette a confronto con le forme vicine dello stesso asse, ed è il campo che serve a decidere. *Come funziona* ne mostra la meccanica con un estratto annotato. *Che cosa richiede* elenca ciò che deve esistere prima. *Che cosa costa* dichiara il prezzo. *Come fallisce* riporta ciò che si è rotto nei casi reali o che la fonte dichiara. *Quando passare ad altro* dice quale segnale indica che la forma non basta più.

Le forme osservate nei casi portano la sigla del caso; quelle raccomandate dalla letteratura e non ancora osservate in un progetto lo dichiarano nel titolo, e la regola sull'onestà del contenuto vale anche qui: una pratica non osservata si presenta come tale e si promuove fra le osservate quando un progetto la adotta davvero.

## Asse R: dove girano gli ambienti

### R0, solo produzione con backup e istantanee

**Che cos'è.** Un solo ambiente, e la rete di sicurezza è il ripristino: un'istantanea prima di ogni aggiornamento e un backup verificato della base dati. [C8]

**Che cosa significa sceglierla.** Significa dichiarare che non c'è codice proprio da provare. È la scelta corretta per un'applicazione di terze parti di cui si installano soltanto le release del fornitore, perché il solo cambiamento è l'aggiornamento e il solo rischio è che vada male, e per quel rischio un ripristino rapido vale più di un ambiente di prova che nessuno manterrebbe allineato. Rispetto a R1 rinuncia a provare prima, e compensa con la capacità di tornare indietro dopo.

**Come funziona.** Su una macchina virtuale Proxmox l'istantanea prima dell'aggiornamento e il ritorno si fanno con due comandi [F33]; il backup completo della macchina è sempre pieno e comprende configurazione e dati [F34].

```
qm snapshot <vmid> prima-aggiornamento --vmstate 0   # istantanea dei soli dischi, senza la memoria
qm rollback <vmid> prima-aggiornamento                # ritorno allo stato dell'istantanea
```

**Che cosa richiede.** Un backup della base dati pianificato e provato con un ripristino, non soltanto configurato. L'istantanea della macchina non sostituisce il backup della base dati: nel modo a istantanea la fonte stessa dichiara un piccolo rischio di incoerenza rispetto al modo con arresto [F34].

**Che cosa costa.** Quasi niente in esercizio. Il costo è tutto nel momento del guasto: il tempo di ripristino e i dati scritti fra l'istantanea e il ritorno, che si perdono.

**Come fallisce.** Nel caso osservato il backup della base dati era ancora un proposito, e qualcuno aveva creato un progetto di prova dentro l'istanza di produzione [C8]. Il primo difetto toglie la rete di sicurezza, il secondo trasforma R0 in un ambiente di prova non separato, cioè nella forma peggiore di tutte.

**Quando passare ad altro.** Quando si comincia a scrivere codice proprio, anche solo moduli o personalizzazioni, o quando serve provare con i dati prima di aggiornare: a quel punto R1 o R2 con D2.

### R1, gemelli sulla stessa macchina dietro il reverse proxy

**Che cos'è.** Due processi o due stack della stessa applicazione sulla stessa macchina, su porte locali diverse, pubblicati da due host virtuali del proxy. [C7] [C9] [C2]

**Che cosa significa sceglierla.** Significa separare il processo e, se lo si fa, la base dati, e condividere tutto il resto: sistema, risorse, configurazione del proxy. Rispetto a R2 rinuncia all'isolamento di rete e di volumi che i container danno gratis, e in cambio non richiede container. È la forma più economica che meriti il nome di separazione.

**Come funziona.** Il punto delicato è l'indirizzo su cui ascolta il gemello di prova. Senza indicazione, nginx ascolta su tutte le interfacce [F36]; legarlo all'interfaccia locale, o a un indirizzo preciso quando la prova deve essere raggiunta da alcuni client, è una riga. L'indirizzo dell'esempio appartiene al blocco riservato alla documentazione e va sostituito.

```nginx
server {
    listen 192.0.2.10:8090;         # un indirizzo preciso, non tutte le interfacce; 127.0.0.1 se la prova serve solo a questa macchina
    server_name prova.interno;
    include snippets/ammessi.conf;  # una sola lista di indirizzi ammessi, inclusa da entrambi
    location / { proxy_pass http://127.0.0.1:5010; }
}
```

**Che cosa richiede.** Due basi dati distinte se l'applicazione scrive dati [C9], e una configurazione del proxy che non duplichi le parti comuni.

**Che cosa costa.** Una configurazione in due copie da tenere allineata, e la contesa delle risorse.

**Come fallisce.** Nel caso osservato i due host virtuali portavano la stessa lista di indirizzi ammessi scritta per esteso [C7]: va aggiornata in due posti, e una copia dimenticata si rompe in silenzio alla prima modifica della rete. La correzione è il file incluso dell'estratto sopra. In un altro caso l'ambiente di prova era raggiungibile dalla rete accanto alla produzione [C9].

**Quando passare ad altro.** Quando la prova deve somigliare alla produzione anche nei servizi di appoggio, cioè code, cache, motori di ricerca, identità: allora R2.

### R2, stack di container isolati sulla stessa macchina

**Che cos'è.** Due stack completi, ciascuno con i propri container, la propria rete, i propri volumi e il proprio file di segreti, sulla stessa macchina. Si presenta in due varianti con compromessi opposti. [C3] [C4] [C6]

**Che cosa significa sceglierla.** Significa chiudere i canali dei dati, dell'identità e della rete senza pagare una seconda macchina. Rispetto a R1 aggiunge l'isolamento completo dei servizi di appoggio; rispetto a R3 rinuncia a separare le risorse e a rendere la produzione un artefatto immutabile. È la forma più robusta fra quelle a macchina singola.

**Come funziona, variante sempre accesa.** Un solo file di composizione parametrizzato serve entrambi gli ambienti. Il nome del progetto è ciò che separa: Compose lo ricava in ordine dall'opzione `-p`, dalla variabile `COMPOSE_PROJECT_NAME`, dall'attributo `name:` e dalla cartella [F24], e da quel nome deriva i nomi di container, volumi e rete. I valori predefiniti riproducono esattamente la produzione, così che la parametrizzazione non cambi niente finché non la si usa, e lo si verifica confrontando `docker compose config` prima e dopo [C3]. L'esempio completo sta in `esempi/compose.parametrizzato.yaml`.

```yaml
name: ${COMPOSE_PROJECT_NAME:-portale}         # portale in produzione, portale-staging in prova
services:
  edge:
    ports:
      - "${EDGE_HTTPS_PORT:-443}:443"            # 443 in produzione, 8443 in prova
    environment:
      SITE_ORIGIN: ${SITE_ORIGIN:?manca SITE_ORIGIN}   # obbligatoria: senza, Compose si ferma
```

```
docker compose --env-file .env.produzione up -d
docker compose --env-file .env.staging -p portale-staging up -d
```

**Come funziona, variante a richiesta.** Un file di composizione di prova indipendente, con nome fisso, rete, volumi, porte e configurazione del proxy propri, spento per default. Si accende per provare e si spegne dopo [C4]. L'esempio completo sta in `esempi/compose.prova.yaml`. Le porte si legano all'interfaccia locale o a un indirizzo preciso, perché senza indirizzo Docker pubblica su tutte le interfacce [F37].

```yaml
name: servizio-prova                 # nome fisso: non può collidere con la produzione per distrazione
services:
  app:
    ports:
      - "127.0.0.1:4443:443"         # solo la macchina stessa raggiunge la prova
    env_file: .env.prova             # identità, segreti e indirizzi di ritorno propri
```

**Che cosa richiede.** Un file di segreti per ambiente, e una registrazione separata presso il fornitore di identità per ciascuno [C4] [F08]. Per la variante sempre accesa, la memoria per due stack; per quella a richiesta, la disciplina descritta sotto.

**Che cosa costa.** La variante sempre accesa costa la memoria di due stack e una porta non standard nell'indirizzo dello staging [C3]. La variante a richiesta non costa memoria a riposo, e permette di provare due linee di codice solo in sequenza.

**Come fallisce.** Nella variante a richiesta entrambi gli stack si costruiscono dalle stesse cartelle, quindi ricostruire la produzione mentre in uscita c'è una branch di lavoro porta in produzione codice non deciso [C4]. La regola che lo presidia è che la produzione si ricostruisce solo con la branch principale in uscita, e il modo più sicuro di rispettarla è uno script di rilascio che verifica la branch prima di costruire. Nella variante sempre accesa il difetto osservato è stato un file di segreti non coperto dall'esclusione di git [C3].

**La forma da non adottare.** La sovrapposizione che sdoppia il solo frontend e condivide backend, automazioni e basi dati con la produzione. Nel caso osservato un accesso autenticato partito dalla prova atterrava sulla produzione, e ogni modifica al backend colpiva subito gli utenti reali [C4]. Chiude il canale del codice per metà e lascia aperti quelli dei dati e dell'identità.

**Quando passare ad altro.** Quando la contesa delle risorse diventa visibile, quando la produzione deve essere riproducibile da un artefatto, o quando la macchina di produzione deve stare altrove: allora R3.

### R3, macchina di staging separata e produzione immutabile

**Che cos'è.** Sviluppo e staging su una macchina, produzione su un'altra che non sviluppa e non ha gli strumenti per farlo: esegue soltanto l'immagine costruita da una pipeline fuori da lei. [C5]

**Che cosa significa sceglierla.** Significa chiudere anche il canale delle risorse, e soprattutto trasformare la produzione da cartella a artefatto. È l'applicazione diretta di due principi della letteratura: costruire una sola volta e promuovere lo stesso pacchetto [F05], e separare rigidamente costruzione, rilascio ed esecuzione, dove un rilascio non si modifica una volta creato [F01]. Rispetto a R2 costa una seconda macchina e una pipeline, e in cambio ciò che gira in produzione è esattamente ciò che è stato provato.

**Come funziona.** La pipeline costruisce l'immagine a ogni modifica della branch principale, la etichetta con il commit, e la produzione la scarica e la esegue. Le migrazioni della base dati in produzione sono esplicite, mentre in sviluppo possono allinearsi da sole [C5]. Su un'infrastruttura Proxmox la macchina di staging nasce convenientemente da un modello, con un clone pieno se deve vivere indipendente dal modello e uno collegato se si accetta la dipendenza in cambio dello spazio [F32].

**Che cosa richiede.** Una pipeline e un registro di immagini, e una configurazione iniettata al rilascio e non incorporata nell'immagine.

**Che cosa costa.** Due macchine, una pipeline, e il tempo di costruzione a ogni rilascio.

**Come fallisce.** Due modi, entrambi osservati o dichiarati. Il primo è credere che lo staging sia identico alla produzione quando gira in modalità di sviluppo: non lo è, e la prova finale va fatta sull'immagine [C5]. Il secondo è la configurazione fissata alla costruzione, che contraddice il principio dell'artefatto unico senza che nessuno se ne accorga: in Next.js le variabili con prefisso `NEXT_PUBLIC_` vengono sostituite nel pacchetto al momento della costruzione, e la documentazione avverte che con una sola immagine rilasciata in più ambienti restano congelate al valore di allora [F35]. Il rimedio è leggere quei valori a runtime dal server, oppure accettare dichiaratamente un'immagine per ambiente.

**Quando passare ad altro.** Raramente verso una forma più semplice. Verso una più ricca, quando serve ridurre il rischio del singolo rilascio: le tecniche di rilascio descritte più sotto.

### R4, progetti gemelli su una piattaforma gestita

**Che cos'è.** Dove il backend è un servizio gestito che permette progetti distinti, sviluppo e produzione sono due progetti con base dati, autenticazione, funzioni e fatturazione proprie, e il codice sceglie a quale parlare con un selettore d'ambiente. [C1]

**Che cosa significa sceglierla.** Significa delegare l'isolamento alla piattaforma: i cinque canali sono chiusi per costruzione, perché i due progetti non condividono nulla. È anche ciò che la documentazione del fornitore raccomanda, un progetto separato per ogni ambiente [F26]. Rispetto alle forme R1-R3 non richiede di amministrare macchine, e in cambio la parità fra i due progetti si tiene a mano.

**Come funziona.** Il selettore d'ambiente sceglie il blocco di configurazione, e un interruttore distinto accende gli emulatori per le prove automatiche. Tenere i due interruttori separati è ciò che impedisce alle prove di toccare il progetto di sviluppo reale [C1].

```typescript
const ambiente = process.env.REACT_APP_ENVIRONMENT ?? "test";   // test per default: mai produzione per distrazione
const config = ambiente === "prod" ? configProduzione : configSviluppo;
if (process.env.REACT_APP_USE_EMULATORS === "true") {           // interruttore distinto da "sviluppo"
  collegaEmulatori();                                            // solo prove automatiche, mai dati reali
}
```

Le anteprime per richiesta di modifica danno a ogni ramo un indirizzo nuovo [F27], e risolvono il problema dei rami paralleli che si sovrascrivono sull'unico sito di sviluppo [C1].

**Che cosa richiede.** Un piano della piattaforma che permetta i progetti gemelli, una pipeline che pubblichi le anteprime, e la registrazione di ogni dominio presso i servizi che la richiedono, come le chiavi anti-robot e le origini di autenticazione.

**Che cosa costa.** Tre costi, da scrivere. La parità si tiene a mano: configurazioni, estensioni e variabili delle funzioni vanno replicate [C1]. Le anteprime "always interact with real project resources" [F27], quindi non isolano i dati: condividono la base dati del progetto di sviluppo. E gli emulatori non sono servizi da ospitare, perché "are not appropriate to use in production" [F28].

**Come fallisce.** Il progetto di sviluppo ha una fatturazione propria, e nel caso osservato è stato declassato alla fine di un periodo di prova, fermando l'accesso per ore [C1]. I progetti gemelli vanno sotto lo stesso account di fatturazione.

**Quando passare ad altro.** Quando le anteprime devono isolare anche i dati, cioè quando serve un ambiente effimero completo, descritto più sotto.

## Asse P: come il codice passa da un ambiente all'altro

La letteratura concorda su un punto che orienta tutto l'asse: la separazione degli ambienti non si fa con le branch. Le branch servono a integrare il lavoro, la configurazione a distinguere gli ambienti, e confondere le due cose produce la forma P3, che la fonte principale sul branching chiama un anti-pattern [F13]. La consegna continua, cioè la capacità di rilasciare in qualunque momento [F02] [F12], è l'orizzonte verso cui le forme di questo asse si ordinano, non un obbligo.

### P1, una branch stabile e rami brevi con richiesta di modifica

**Che cos'è.** La branch principale è l'unica stabile; ogni modifica di codice nasce su un ramo breve, passa da una richiesta di modifica e viene fusa; il ramo si cancella dopo la fusione [F16]. Il rilascio in produzione è un gesto separato. [C1] [C4] [C5]

**Che cosa significa sceglierla.** Significa assumere una sola versione in produzione e un'integrazione frequente sulla branch principale, che è esattamente il presupposto dichiarato di GitHub Flow [F13]. Rispetto a P2 elimina la branch di integrazione condivisa e i suoi difetti di visibilità; rispetto al trunk-based puro conserva la revisione prima della fusione.

**Come funziona.** Un ramo per modifica, vita breve, fusione dopo la verifica. La fonte sul trunk-based fissa un ordine di grandezza utile: oltre due giorni un ramo rischia di diventare un ramo di lunga durata [F15]. Conviene dichiarare quali percorsi possono andare direttamente sulla branch principale, tipicamente documentazione e memoria, e quali passano sempre dalla richiesta [C1].

**Che cosa richiede.** Una verifica automatica sulla richiesta, perché il ramo sano è quello su cui ogni commit viene costruito e provato [F13].

**Che cosa costa.** La disciplina dei rami brevi, e il tempo della revisione.

**Come fallisce.** Quando i rami si allungano, l'integrazione diventa rara e si ricade nei problemi che P1 voleva evitare. La ricerca DORA misura la soglia: i gruppi con tre o meno rami attivi hanno prestazioni di consegna migliori [F09].

**Quando passare ad altro.** Verso il trunk-based con interruttori, quando il gruppo cresce e i rilasci diventano frequenti.

### P2, una branch di staging fra i rami di lavoro e la produzione

**Che cos'è.** I rami di lavoro confluiscono in una branch di integrazione condivisa che alimenta un ambiente di staging; una richiesta di rilascio porta quella branch in produzione; le correzioni urgenti partono dalla produzione e si riportano sullo staging. È una forma semplificata di git-flow [F14]. [C2] [C3]

**Che cosa significa sceglierla.** Significa volere un punto di integrazione e di collaudo condiviso prima della produzione, con un ambiente di lunga durata dove più persone vedono insieme lo stato integrato. Rispetto a P1 aggiunge una tappa, e con essa una branch mutabile che nessuno possiede. L'autore di git-flow, nella nota del 2020, restringe il proprio modello al software con più versioni in produzione e suggerisce un flusso più semplice a chi fa consegna continua [F14]; P2 ne è una versione ridotta, e ne eredita il limite.

**Come funziona.** Il flusso è ramo di lavoro, richiesta verso staging, collaudo sullo staging, richiesta di rilascio verso la branch principale, rilascio. Il presidio che la rende sostenibile è la visibilità: a inizio sessione si aggiornano i riferimenti remoti, e lo snapshot `memory/index.md` porta la riga degli ambienti con il commit corrente di produzione e di staging [C2].

```
git fetch --prune
git rev-parse --short origin/main origin/staging
git rev-list --left-right --count origin/staging...HEAD
```

La terza riga dice quanti commit lo staging ha che il ramo non ha, e viceversa: è la divergenza da scrivere nello snapshot.

**Che cosa richiede.** La protezione delle due branch sulla piattaforma, un ambiente di staging reale con base dati e servizi di prova propri, e una pipeline di verifica: senza di essa il cancello dichiarato nella regola di flusso non esiste [C2].

**Che cosa costa.** Una tappa in più a ogni rilascio, e la manutenzione di una branch condivisa.

**Come fallisce.** Tutti i difetti osservati sono di visibilità. Una fusione annullata sulla branch di staging senza che nessuno lo segnalasse è stata scoperta due settimane dopo; un rilascio in produzione non era tracciabile dal repository; un servizio è entrato in produzione scavalcando lo staging; e lo staging è avanzato di nove commit cambiando un calcolo da cui dipendeva il ramo di lavoro [C2]. Un difetto di meccanica merita di essere conosciuto prima: una fusione annullata non si ripristina fondendo di nuovo, perché git considera quei commit già integrati, e serve annullare l'annullamento.

**Quando passare ad altro.** Verso P1, quando lo staging diventa un collo di bottiglia o una fonte di sorprese; il costo del passaggio è sostituire il collaudo condiviso con anteprime per ramo e con interruttori di funzionalità.

### P3, una branch per ambiente con configurazione divergente, forma sconsigliata

**Che cos'è.** Ogni ambiente è una branch permanente che porta la propria configurazione: porte, volumi, filtro delle basi dati, numero di processi, limiti di risorse. [C6]

**Che cosa significa sceglierla.** Significa usare le branch per distinguere gli ambienti, che è ciò che la fonte principale sul branching chiama "the classic example of an Anti Pattern - something that looks appealing when you start, but soon leads to a world of misery", con la prescrizione "Keep any environmental changes minimal, and don't use source branching to apply them" [F13]. La ragione è strutturale: le branch divergono per sempre e ogni correzione va riportata a mano, il che nel caso osservato ha toccato anche la configurazione della base dati [C6]. È descritta qui perché esiste e funziona in un progetto reale, non perché si raccomandi.

**Come se ne esce.** La stessa fonte indica la via: "If configuration changes are required they must be isolated through mechanisms such as explicit configuration files or environment variables" [F13]. In pratica si porta la configurazione divergente in un file per ambiente, per esempio un file aggiuntivo di Compose che contenga solo le differenze [F24], e si torna a P1 o P2 con una branch sola.

```
docker compose -f compose.yaml -f compose.prova.override.yaml up -d
```

**Quando tollerarla.** Quando la configurazione dell'ambiente è imposta da un fornitore che la versiona così, e la migrazione costerebbe più della divergenza. In quel caso si elencano i file che divergono, così che una fusione che li tocca si riconosca.

### P4, trunk-based development con interruttori di funzionalità, non ancora osservata

**Che cos'è.** Tutti lavorano sulla branch principale, chiamata *trunk*, e resistono alla pressione di creare branch di sviluppo di lunga durata [F15]; il lavoro incompleto arriva in produzione spento dietro un interruttore di funzionalità [F17].

**Che cosa significa sceglierla.** Significa spostare la separazione dal repository al comportamento: il codice nuovo è in produzione, ma nessuno lo vede finché l'interruttore è spento. Rispetto a P1 elimina anche i rami brevi o li riduce a poche ore; rispetto a P2 elimina lo staging come luogo dell'integrazione. La ricerca DORA lo indica come pratica richiesta dall'integrazione continua [F09].

**Come funziona.** Un interruttore di rilascio permette di "shipped to production as latent code which may never be turned on" [F17]. La fonte ne distingue altre tre categorie: sperimentali, operativi e di permesso [F17].

```typescript
if (interruttori.attivo("nuovo-calcolo-preventivo", utente)) {  // interruttore di rilascio: temporaneo per definizione
  return calcoloNuovo(richiesta);
}
return calcoloAttuale(richiesta);                                  // si rimuove quando l'interruttore diventa permanente
```

**Che cosa richiede.** Una pipeline di verifica affidabile su ogni commit della branch principale, e un meccanismo di interruttori con un proprietario per ciascuno. Senza la pipeline questa forma non è una scelta ma un rischio.

**Che cosa costa.** Gli interruttori sono un inventario "which comes with a carrying cost" [F17]: ogni interruttore raddoppia i percorsi da provare, e la fonte avverte che il processo di consegna "becomes more complex, particularly in regard to testing" [F17]. Vanno rimossi appena servono meno.

**Quando adottarla.** Con un gruppo che cresce, rilasci frequenti e una pipeline già in piedi. In un progetto di una persona con rilascio manuale non aggiunge nulla a P1.

## Asse D: da dove vengono i dati dell'ambiente di prova

La ricerca DORA formula il requisito in due frasi: dati di prova adeguati a far girare le prove automatiche complete, e dati isolati, in ambienti ben definiti con ingressi controllati [F10]. Le quattro forme osservate sono quattro modi di rispondere, e si ordinano per fedeltà crescente e per rischio crescente.

### D0, vuoti o con un seme versionato

**Che cos'è.** L'ambiente di prova parte da volumi vuoti o da un insieme di dati di prova versionato. [C3] [C4] [C5]

**Che cosa significa sceglierla.** Significa rinunciare alla fedeltà dei dati reali in cambio dell'assenza totale di rischio sui dati sensibili. È il default giusto quando i dati reali sono personali o riservati.

**Come fallisce, in apparenza.** Un servizio che al primo avvio chiede di creare l'amministratore non è rotto: sta leggendo un volume vuoto e separato [C4]. Conviene scriverlo in anticipo nella scheda, perché sembra un guasto.

**Quando passare ad altro.** Quando i difetti vivono nei dati reali e un seme non li riproduce.

### D1, dati propri dello sviluppo, con promozione controllata

**Che cos'è.** L'ambiente di sviluppo accumula i propri dati, e ciò che deve arrivare in produzione vi arriva con uno strumento dedicato. [C1]

**Che cosa significa sceglierla.** Significa trattare lo sviluppo come il luogo dove i contenuti nascono, con un verso solo, dallo sviluppo alla produzione. È adatta quando i contenuti si preparano prima e si pubblicano dopo.

**Come funziona.** Lo strumento di promozione lavora a elenco di ammessi e rifiuta tutto il resto, ha una prova a vuoto, ed esclude credenziali, posta e limiti di frequenza [C1].

**Come fallisce.** Quando serve il verso opposto, cioè riportare in sviluppo un difetto nato sui dati di produzione: questa forma non lo prevede.

### D2, copia della produzione resa innocua

**Che cos'è.** La base dati di produzione si duplica nell'ambiente di prova e subito dopo si neutralizza. [C6]

**Che cosa significa sceglierla.** Significa volere la massima fedeltà, accettando di maneggiare dati reali. È il modo più fedele di provare un gestionale, perché i difetti vivono nei dati, ed è la forma che il fornitore stesso adotta per i propri ambienti di staging, che "create neutralized duplicates of the production database" [F31].

**Come funziona.** Una base dati neutralizzata è "a non-production database on which several parameters are deactivated" per non toccare la produzione, per esempio inviando posta ai clienti [F30]. Dalla versione che la documenta, il fornitore offre un comando dedicato che può anche soltanto stampare le istruzioni invece di applicarle [F30].

```
odoo-bin --addons-path <percorsi> neutralize -d <base-dati-di-prova> --stdout   # stampa le istruzioni, non le applica
odoo-bin --addons-path <percorsi> neutralize -d <base-dati-di-prova>            # le applica
```

Nel caso osservato la neutralizzazione era un modulo proprio con un insieme di istruzioni versionato che disattiva i server di posta alterandone anche l'indirizzo, ferma le attività pianificate, ripulisce gli asset e imposta credenziali di prova [C6].

**Che cosa richiede.** Che la neutralizzazione sia uno strumento e non una procedura a memoria, e che l'elenco di ciò che neutralizza sia rivisto: la documentazione stessa dichiara il proprio elenco "a non-exhaustive list" [F30].

**Come fallisce.** L'incidente tipico di questa forma è un ambiente di prova che invia posta ai clienti veri. Un secondo limite è dichiarato dal fornitore: sulle copie di produzione le prove unitarie non girano, perché si appoggiano a dati dimostrativi che lì non ci sono [F31].

### D3, istantanea dei volumi di produzione su richiesta

**Che cos'è.** L'ambiente di prova parte vuoto e si popola da un'istantanea solo quando serve e solo su richiesta esplicita. [C4]

**Che cosa significa sceglierla.** È il compromesso fra D0 e D2 dove non esiste uno strumento di neutralizzazione: la fedeltà si paga caso per caso, e la decisione di maneggiare dati reali diventa esplicita ogni volta.

## Asse L: come stanno i sorgenti sulla macchina di chi sviluppa

### L1, un albero solo e il cambio di branch

**Che cos'è.** Una cartella, una branch in uscita alla volta. È il default e basta nella maggior parte dei casi, compresi tutti quelli in cui gli ambienti vivono su macchine, progetti o stack diversi. È la forma di tutti i casi ispezionati direttamente, salvo i due cloni che uno di essi tiene sulla macchina di esercizio [C3].

### L2, un albero di lavoro per branch

**Che cos'è.** Più cartelle agganciate allo stesso repository con `git worktree`, ciascuna con una branch in uscita [F25].

**Che cosa significa sceglierla.** Significa far girare insieme più stati del codice sulla stessa macchina, ciascuno con il proprio server di sviluppo, o far lavorare in parallelo più sessioni su rami diversi. Rispetto a L1 evita di cambiare branch avanti e indietro; rispetto a L3 condivide gli oggetti git invece di duplicarli.

**Che cosa richiede e come fallisce.** Tre vincoli di git non si leggono dal comando: una branch non può stare in uscita in due alberi, salvo forzarlo [F25]; un albero si rimuove solo pulito [F25]; e la configurazione del repository è condivisa fra gli alberi salvo l'estensione dedicata [F25]. Il fallimento più insidioso non è di git ma del sistema di memoria: la memoria versionata vale per la branch su cui è scritta, e un albero su una branch indietro riceve uno snapshot ben formato e vecchio. La norma `skills/alberi-di-lavoro/RIFERIMENTO.md` ne governa le conseguenze.

### L3, cloni indipendenti, uno per ambiente

**Che cos'è.** Sulla macchina che esegue, un clone sulla branch di produzione e uno su quella di staging, allineati a mano [C3]. Accompagna R2 nella variante sempre accesa. Un albero di lavoro in più ne sarebbe la variante che risparmia il secondo clone.

## Le pratiche trasversali

Le pratiche seguenti non appartengono a un asse: si applicano a qualunque combinazione e ne correggono i punti deboli. Alcune sono già osservate nei casi, altre vengono dalla letteratura e lo dichiarano.

### Costruire una volta, promuovere lo stesso artefatto

**Che cos'è.** Il pacchetto si costruisce una sola volta, e lo stesso pacchetto passa di ambiente in ambiente: "Only build packages once. We want to be sure the thing we're deploying is the same thing we've tested" [F05]. Il primo stadio della pipeline produce i binari per tutti gli stadi successivi [F03], e ogni rilascio è un registro che si allunga e non si modifica [F01].

**Che cosa cambia rispetto a non farlo.** Senza questa pratica ogni ambiente riceve una costruzione propria, e ciò che è stato provato non è ciò che gira. È osservata in R3 [C5] e contraddetta, senza che nessuno se ne accorga, dalla configurazione fissata alla costruzione [F35].

### Configurazione separata dal codice

**Che cos'è.** Tutto ciò che cambia fra un ambiente e l'altro sta fuori dal codice, e il criterio per sapere se ci si è riusciti è la domanda della fonte: il codice potrebbe diventare pubblico in qualunque momento senza esporre credenziali? [F01]

**Che cosa cambia rispetto a non farlo.** La differenza fra ambienti smette di vivere nel codice, dove nessuna prova la esercita in produzione. Il caso opposto è osservato: valori fittizi inseriti nella logica di dominio quando l'ambiente è di prova [C2].

### Parità fra gli ambienti

**Che cos'è.** Sviluppo, staging e produzione il più simili possibile, riducendo tre divari: il tempo fra scrivere e rilasciare, la distanza fra chi scrive e chi esercisce, la differenza degli strumenti. La fonte è esplicita sull'ultimo: resistere alla tentazione di usare servizi di appoggio diversi fra sviluppo e produzione [F01]. Lo stesso vale per il procedimento di rilascio, che deve essere lo stesso in ogni ambiente, produzione compresa [F05] [F11].

**Che cosa cambia rispetto a non farlo.** Ogni divario è un luogo dove un difetto sopravvive alla prova. La scheda `deployment.md` elenca le differenze ammesse, così che una differenza non ammessa si riconosca.

### Ambienti effimeri completi, non ancora osservati

**Che cos'è.** Un ambiente completo, backend e dati compresi, creato per ogni richiesta di modifica e distrutto alla chiusura.

**Che cosa cambia rispetto alle anteprime.** Le anteprime osservate [C1] isolano il frontend ma "always interact with real project resources" [F27]; una piattaforma può perfino usare le variabili di produzione in un rilascio di prova, e la sua documentazione avverte che così "testing can access production services and data" [F29]. Un ambiente effimero completo chiude anche il canale dei dati, al costo di automatizzare la creazione della base dati e del suo seme.

### Tecniche di rilascio, non ancora osservate

Riducono il rischio del singolo rilascio in produzione, e si scelgono in base a che cosa si vuole poter fare quando va male. Nessun caso osservato ne usa una: tutti rilasciano manualmente e tornano indietro ripristinando.

**Blu e verde.** Due ambienti di produzione identici; si rilascia su quello inattivo e si sposta il traffico con il router [F18]. Tornare indietro è spostarlo di nuovo. La fonte indica lo schema della base dati come il problema principale, da separare dal rilascio applicativo [F18].

**Rilascio canarino.** La nuova versione raggiunge prima una piccola parte degli utenti e poi tutti [F19]. Un canarino al cinque per cento con un tasso d'errore del venti per cento produce un impatto complessivo dell'uno per cento [F22]. Richiede metriche attribuibili al cambiamento e non al rumore, e comporta più versioni in produzione insieme [F19] [F22].

**Lancio al buio.** Il comportamento nuovo gira sul traffico reale senza che l'utente se ne accorga [F21]. Adatto a comportamenti automatici del backend, non a funzionalità che l'utente sceglie [F21].

### Migrazioni della base dati in due tempi, non ancora osservate

**Che cos'è.** Un cambiamento incompatibile dello schema si divide in tre fasi: espandere per supportare insieme la forma vecchia e la nuova, migrare i client, contrarre togliendo la vecchia [F20]. Per le basi dati la fonte chiama fase di transizione il periodo in cui lo schema supporta entrambi gli accessi [F23], e ogni cambiamento è uno script di migrazione versionato insieme al codice [F23].

**Che cosa cambia rispetto a non farlo.** Rende possibili le tecniche di rilascio sopra, che richiedono due versioni del codice sulla stessa base dati, e rende sicuro tornare indietro. Il rischio dichiarato dalla fonte: se la contrazione non si esegue, lo stato finale è peggiore di quello iniziale [F20].

### Infrastruttura dichiarata, non ancora osservata

**Che cos'è.** L'infrastruttura definita in file versionati ed eseguibili, trattata come qualunque altro codice [F06]. All'estremo, un sistema in cui lo stato desiderato è dichiarato, versionato, recuperato da agenti e riconciliato di continuo con lo stato reale [F07].

**Che cosa cambia rispetto a non farlo.** Un ambiente previsto e non creato non può più sembrare esistente, perché esiste solo ciò che è dichiarato ed è stato applicato. È la risposta al difetto osservato di uno staging completo descritto nei documenti e mai creato [C3].

### Segreti per ambiente

**Che cos'è.** Ogni ambiente ha i propri segreti, conservati separatamente secondo il carico e la sensibilità [F08], ruotati con regolarità [F08], iniettati al rilascio e mai incorporati nell'artefatto [F08].

**Che cosa cambia rispetto a non farlo.** È ciò che chiude il canale dell'identità. Il caso osservato: con una sola registrazione presso il fornitore di identità, prova e produzione condividevano i segreti e la chiave di firma dei token [C4].

### Ambienti di prova legati alla rete giusta

**Che cos'è.** Un ambiente di prova ascolta sull'interfaccia locale o su un indirizzo preciso, oppure resta spento quando non serve. Senza indicazione sia nginx [F36] sia Docker [F37] ascoltano su tutte le interfacce, e la documentazione di Docker lo dice senza giri di parole: "Publishing container ports is insecure by default" [F37].

**Che cosa cambia rispetto a non farlo.** È il difetto più frequente fra quelli osservati, trovato su quattro macchine con modelli diversi [C4] [C5] [C9] e in un servizio in sviluppo accanto alla produzione [C3]. Il predefinito di Docker si può portare sull'interfaccia locale per l'intera macchina [F37].

## Come le forme evolvono insieme al progetto

Una combinazione non è per sempre, e il gate si riesegue a ogni allineamento proprio per questo. I percorsi di crescita osservati o indicati dalla letteratura sono pochi e prevedibili. Sull'asse R si sale da R0 a R1 quando nasce codice proprio, da R1 a R2 quando la prova deve somigliare alla produzione nei servizi di appoggio, da R2 a R3 quando la produzione deve diventare un artefatto riproducibile; R4 resta dove il backend è gestito. Sull'asse P si scende da P3 a P1 o P2 portando la configurazione in file per ambiente [F13], e si passa da P2 a P1 e poi a P4 quando il gruppo cresce e la pipeline è affidabile [F09] [F14]. Sull'asse D si sale da D0 a D2 quando i difetti vivono nei dati, solo se esiste uno strumento di neutralizzazione. L'asse L segue le altre scelte e non le guida.

Il segnale che una forma non basta più è quasi sempre lo stesso: un difetto che la prova non ha visto e la produzione sì, rintracciato fino a un canale che la forma lasciava aperto. È la domanda da porsi a ogni incidente, e la risposta va nella scheda `deployment.md` insieme alla forma che la chiude.
