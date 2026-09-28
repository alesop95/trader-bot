# Fonti web non recuperabili automaticamente

> Riferimento normativo della skill `fonti-non-recuperabili`, che lo carica su richiesta invece di tenerlo in contesto a ogni sessione. Stabilisce cosa fare quando una fonte esiste ed è rilevante ma non si riesce a recuperarla con gli strumenti di sessione, così che il progetto non degradi silenziosamente una fonte a nota a margine. Vale per qualunque dominio, e usa Reddit e Discord come casi studiati perché sono quelli che si incontrano più spesso.

## Il principio

Una fonte che non si riesce a leggere resta una fonte non letta, e non diventa per questo inaffidabile: la distinzione va scritta ogni volta. Il rischio, altrimenti, è che il registro delle fonti si riempia di voci che sembrano consultate e non lo sono, e che un'affermazione poggi su un titolo di thread invece che sul suo contenuto.

Da qui la regola in due parti. La prima è che ogni voce non letta va etichettata come tale nel registro, con il motivo. La seconda è che, prima di etichettarla, si tenta il recupero per le vie documentate qui sotto, in ordine di costo crescente, invece di arrendersi al primo errore.

## Le vie, in ordine di costo crescente

La prima via è il recupero locale con `curl` dal terminale. Vale la pena provarla sempre, perché è indipendente dal crawler del modello: sono due agenti diversi, con due indirizzi diversi e due reputazioni diverse, e capita spesso che un dominio blocchi l'uno e non l'altro. Molti siti rispondono a `curl` solo con uno user agent da browser.

La seconda via, quando la fonte è una piattaforma abbastanza grande da averne uno, è un archivio pubblico di terze parti che ne esponga il contenuto con un'API propria. È la meno cara di tutte quelle che richiedono qualcosa, perché non chiede credenziali, non apre schede nel browser di nessuno e non consuma il tempo dell'utente, e va quindi provata subito dopo `curl`. Il suo costo non è di allestimento ma di fedeltà, e sta più sotto nel caso Reddit: un archivio ha latenza verso il presente e memoria di ciò che l'originale ha cancellato, quindi ciò che se ne ricava si annota come tratto da un archivio e non dalla fonte viva.

Per un sito che respinge `curl` con una verifica anti-bot, anche sul testo grezzo della pagina, la stessa via esiste in una forma che non dipende dalla piattaforma: la Wayback Machine dell'Internet Archive. L'elenco delle copie si chiede all'interfaccia CDX, `http://web.archive.org/cdx/search/cdx?url=<indirizzo>&output=json`, che risponde anche quando l'interfaccia di disponibilità dice che non c'è nulla. La copia si scarica con il suffisso `id_` dopo la data, `http://web.archive.org/web/<data>id_/<indirizzo>`, che restituisce i byte originali senza la barra dell'archivio. Quei byte possono arrivare compressi con gzip anche quando l'indirizzo dice HTML, e prima di leggerli va controllato che il titolo non sia quello della pagina di verifica. Caso osservato il 2026-09-25 in un progetto istanziato: una pagina di un'enciclopedia collaborativa respingeva `curl` sia sull'indirizzo normale sia sul testo grezzo, e aveva copie d'archivio di un mese prima; la copia letta è stata registrata con la sua data d'archivio accanto.

La terza via è l'automazione del browser reale dell'utente, dove è disponibile. È la via che funziona su quasi tutto, perché è un browser vero con la sessione dell'utente, e per questo va usata con misura: apre schede nel browser della persona e richiede che i permessi per quel sito siano concessi. Si chiede prima, non si fa e poi si dice.

La quarta via è l'API ufficiale del servizio, quando esiste, con credenziali dell'utente. È la più solida e la più costosa da allestire, e ha senso solo per le fonti che il progetto consulta ripetutamente. Le credenziali stanno in `.env`, che il `.gitignore` esclude, e non entrano mai in un file tracciato né in una conversazione.

Un dettaglio operativo che vale registrare, perché altrimenti sembra una dimenticanza: dove le regole di permesso del progetto negano i percorsi che corrispondono a `.env*`, e in questo sistema lo fanno, l'agente non può creare né leggere quel file, nemmeno il modello `.env.example`. Il modello va quindi creato a mano dall'utente, e le variabili che servono sono documentate nel docstring dello strumento che le consuma. È una limitazione voluta e non va aggirata.

Se nessuna delle quattro è praticabile, resta l'ultima, che non è una sconfitta: si chiede all'utente di procurare il contenuto. È la stessa logica della regola sugli screenshot, cioè quando l'agente non può vedere una cosa la chiede invece di inventarla, e la richiesta va fatta mirata su un contenuto preciso e non come lamentela generica.

## Il criterio che separa le vie legittime da quelle vietate

Prima dei casi particolari conviene fissare il criterio, perché la sua formulazione ingenua conduce alla conclusione sbagliata e perché si applica a ogni piattaforma e non alle sole due studiate qui.

Non è la quantità di dati raccolti a distinguere una via legittima da una vietata, né la finalità dichiarata di chi raccoglie: una via vietata resta vietata anche per un uso privato e minimo, e una legittima resta legittima anche per una raccolta sistematica autorizzata. Ciò che le separa sono due proprietà verificabili dall'esterno. La prima è l'esistenza di un canale di accesso che il fornitore del servizio ha costruito per l'automazione, e il suo impiego invece di uno destinato alle persone. La seconda è l'esistenza di un meccanismo di consenso: qualcuno autorizza esplicitamente, scegliendo l'ampiezza dei permessi e potendoli revocare, e chi guarda vede che un programma è presente perché la piattaforma lo dichiara.

Da questo criterio discende una conseguenza che va enunciata perché è ciò che lo rende onesto invece di autoassolutorio: proprio il meccanismo di consenso che rende lecita una via la rende inapplicabile dove il consenso non si ottiene. Una via lecita non è una via disponibile, e confondere le due cose è il modo in cui una regola viene aggirata senza che nessuno se ne accorga.

## Il caso Reddit, un vicolo cieco documentato e la via che lo ha aggirato

Reddit merita una scheda propria perché è una fonte tecnica di prima qualità su molti domini, e perché la sua indisponibilità è facile da attribuire alla causa sbagliata. La causa sta nella somma di due fatti indipendenti, entrambi fuori dal controllo di chi lavora, e la configurazione del progetto non c'entra.

| Via tentata | Esito osservato |
|---|---|
| recupero dal crawler del modello | rifiutato: il dominio non è accessibile allo user agent |
| ricerca con dominio consentito | rifiutata allo stesso modo |
| `curl` locale sugli endpoint JSON, con e senza user agent da browser | HTTP 403 |
| `curl` locale sulla pagina HTML | HTTP 200, ma il corpo è la pagina di verifica anti-bot |
| endpoint JSON del frontend storico | HTTP 302 verso la pagina di accesso, poi HTTP 403 |
| frontend alternativi | HTTP 403, oppure sfida JavaScript di verifica del browser |
| proxy di lettura | HTTP 403, oppure poche centinaia di byte senza contenuto |
| archivio pubblico di terze parti | riuscito, senza credenziali |

Una riga di quella tabella merita attenzione più delle altre, perché è la sola che inganna. La pagina HTML risponde oggi con un codice di successo, e chi si ferma al codice conclude di avere il contenuto: gli ottomila byte che arrivano sono la pagina di verifica del browser, con un titolo generico, nessun link ai commenti e nessun testo. Un successo vuoto costa più di un rifiuto, perché il rifiuto si nota e questo no, e la lezione generale è che l'esito di un recupero si verifica sul corpo e non sul codice.

I risultati di ricerca continuano a restituire indirizzi di Reddit, e quelli sono utili: dicono che una discussione esiste e su cosa. Ma il titolo di un thread non è il suo contenuto, e va trattato come un puntatore da verificare.

Sulla via dell'API ufficiale va registrato un modo di fallire che consuma tempo e sembra un errore di compilazione. L'API ha un flusso a sole credenziali applicative, senza account collegato, che basterebbe per leggere contenuto pubblico; la registrazione dell'applicazione avviene su una pagina dedicata, e su almeno un account osservato la creazione è stata rifiutata dal server ricaricando il form senza alcun errore accanto ai campi. Le due cause ipotizzate erano l'email non verificata e la mancanza di una registrazione preventiva dell'uso: entrambe sono state escluse per verifica diretta, la prima controllando lo stato dell'email e la seconda leggendo la documentazione ufficiale, che dichiara quel modulo necessario alle sole richieste commerciali, aziendali, accademiche o di superamento dei limiti.

Ne segue la conclusione onesta, che vale come regola e non come resoconto: se il rifiuto persiste dopo aver escluso le cause note, quella via non è disponibile su quell'account e non vale la pena insistere.

Restano l'automazione del browser dell'utente, che ha dimostrato di funzionare bene, e la consegna manuale. Ma non sono più le sole, e questa parte va letta come la correzione di una conclusione che era vera quando è stata scritta e oggi non lo è più. Esiste una quinta via che le quattro non contemplavano, perché non è né un canale del fornitore del servizio né una consegna manuale: l'archivio pubblico di terze parti, che nel caso di Reddit è Arctic Shift, successore di Pushshift. Pubblica di propria iniziativa un'API documentata sul proprio archivio, non chiede credenziali, e restituisce un post con il suo corpo intero e l'albero completo dei commenti. Il pacchetto `community-sources` la implementa in `fetch-reddit.py`, che attraversa anche il grafo dei rinvii a partire da un post.

Il criterio enunciato sopra non copriva questo caso e va esteso, perché applicato alla lettera lo escluderebbe per la ragione sbagliata. Le due proprietà che rendono legittima una via erano l'esistenza di un canale costruito per l'automazione e l'esistenza di un meccanismo di consenso. Qui la prima c'è, mentre la seconda non c'è e non può esserci, perché non c'è nulla da autorizzare: non si entra in casa di nessuno, si interroga un servizio chiedendogli i propri dati. Il consenso è il presidio giusto quando si chiede a una piattaforma l'accesso a ciò che custodisce; davanti a un terzo che ha già pubblicato il proprio archivio, il presidio si sposta altrove, e diventa la fedeltà.

Fedeltà significa due cose opposte, ed entrambe vanno dichiarate ogni volta che una fonte proviene da un archivio invece che dall'originale. L'archivio ha latenza, quindi un contenuto recente può mancare: la sua assenza non prova che non esista, e va scritto così. E l'archivio conserva ciò che sull'originale è stato cancellato, quindi il materiale può contenere testo che il suo autore ha rimosso: valgono qui, e con più forza, i quattro accorgimenti dell'ultimo paragrafo di questa regola, a partire dalla conservazione dell'identificativo dell'autore accanto al contenuto. Ne segue che una citazione tratta da un archivio si annota come tale, con il momento di archiviazione del record accanto, e non come una citazione della fonte viva.

La lezione di metodo, che vale oltre il caso di Reddit, è che una tabella di vie tentate è una fotografia datata e non un verdetto. Riaprirla è costato sei richieste; lasciarla chiusa sarebbe costato una fonte.

## Il caso Discord, e le tre vie di cui una si dimentica

Discord merita una scheda propria per la stessa ragione di Reddit, e per una in più: qui l'errore tipico consiste nel valutare l'unica via che si conosce, trovarla inaccettabile e concludere che il problema non abbia soluzione. Le vie sono tre.

La prima è il token del proprio account personale, cioè il self-bot. Funziona tecnicamente e non richiede il permesso di nessuno, perché l'account è già dentro il server. È vietata dalle condizioni d'uso, che dedicano alla questione una pagina di supporto, e la sanzione dichiarata è la terminazione dell'account senza distinzione di intenzioni. Va aggiunto un argomento che di solito manca nella valutazione: un token utente dà accesso a tutto ciò che vede l'account, messaggi privati compresi, quindi il danno di una sua fuga è incomparabilmente più ampio di quello di un token con permessi ristretti. Sul rilevamento vale essere precisi invece di allarmisti o rassicuranti: non è certo ma probabilistico, perché la piattaforma cerca schemi di traffico anomali e non ispeziona ogni richiesta; ne segue che non essere stati sanzionati non equivale a essere al sicuro, e che l'asimmetria fra il guadagno, cioè risparmiare una copia manuale, e la perdita possibile, cioè un account con anni di iscrizioni e conversazioni private, è il vero termine della decisione. Se un progetto decide comunque di percorrerla, la decisione va registrata come tale e non fatta scivolare dentro un altro lavoro.

La seconda è la copia manuale del materiale pertinente. Funziona sempre, non ha rischi, e ha una qualità che le vie automatiche non hanno: chi copia sa che cosa sta cercando, quindi il filtro incorpora la domanda.

La terza è un bot account creato nel portale per sviluppatori, ed è la via che il pacchetto `community-sources` implementa. La distinzione dalla prima poggia su fatti verificabili e non su una interpretazione benevola: il tipo di token è diverso e la documentazione ufficiale descrive il bot account come dedicato all'automazione; l'accesso a un server passa da un invito che chi amministra autorizza esplicitamente, scegliendo i permessi e potendoli revocare; il bot porta un contrassegno visibile a tutti, quindi non finge di essere una persona; l'API è pubblica, con limiti di frequenza pensati per traffico automatico, mentre un self-bot deve imitare artificialmente il ritmo di un umano che clicca; e il rischio in caso di uso scorretto ricade sull'applicazione e non sull'account personale.

Il limite della terza via è il rovescio del criterio enunciato sopra, e va conosciuto prima di allestirla perché altrimenti si scopre dopo. Un bot entra in un server soltanto se qualcuno con il permesso di gestione lo invita, e non esiste alcuna altra via perché è l'unico flusso che l'API espone. Il punto va capito nella sua forma esatta: il cancello non è sui dati ma sul bot, perché i messaggi di un canale di cui si è membri sono già visibili e nessuno autorizza a leggere ciò che il server mostra già; ciò che l'invito autorizza è far entrare una seconda identità dentro quel server, e è questo che richiede il consenso.

Ne segue una prescrizione in tre passi per i server non propri. Si chiede, perché chiedere è gratuito e alcune community di sviluppo accettano un lettore dichiarato. Si dichiara a che cosa serve e quali permessi si chiedono, cioè soltanto vedere il canale e leggerne la cronologia. E si accetta che un no sia un esito, dopo il quale resta la seconda via.

Una eccezione parziale esiste ed è la sola che non richieda il consenso del server di origine: i canali di annunci di un server di tipo community si possono seguire da un altro server, con replica dei messaggi pubblicati, e il permesso necessario è quello di gestire i webhook nel server di destinazione, cioè nel proprio. Il limite è netto: riguarda gli annunci e non le discussioni, che è il posto dove sta la conoscenza tecnica.

Una avvertenza sulle guide di terze parti all'allestimento, osservata su un caso reale e messa qui perché costa tempo e può costare un rifiuto. Una guida che nomina permessi va confrontata con il riferimento dei permessi prima di essere seguita, sempre. Nel caso osservato, un articolo che si presentava come guida rapida raccomandava fra i permessi anche quello di gestione dei messaggi, che è di moderazione e consente di cancellare e fissare i messaggi altrui: chiederlo per un bot di sola lettura è il modo più rapido di farsi rifiutare da chi amministra, e con ragione. Nello stesso testo comparivano un intent che nel portale non esiste, un'impostazione di server che non esiste, e nessuna menzione dei due fatti che governano davvero l'allestimento, cioè il permesso di gestione necessario sul server di destinazione e il significato dell'interruttore che rende pubblica l'applicazione. Il criterio è quello generale della gerarchia delle fonti: una guida è di livello basso, il riferimento dei permessi e la documentazione della piattaforma sono la verità, e dove divergono ha ragione la seconda.

Un'ultima avvertenza vale per il caso in cui la fonte sia una community di sviluppo che mantiene anche codice pubblico, e va detta perché ridimensiona spesso il problema: la conoscenza autorevole di quel gruppo sta di norma nel codice e nel suo tracciatore di problemi, che sono interamente accessibili senza chiedere nulla a nessuno, e il canale serve alle domande a cui il codice non risponde. Prima di allestire una via di accesso conviene verificare quanto della fonte sia già raggiungibile per altra strada.

## Come l'utente consegna il materiale, e in che formato

Quando la via resta l'ultima, cioè l'utente procura il contenuto, il contenuto si consegna salvandolo su disco in una cartella concordata, invece di incollarlo in conversazione, perché così resta disponibile anche nelle sessioni successive e non consuma contesto due volte. La cartella è `_notes/fonti/`, locale e non versionata, e la convenzione di nome è la data seguita da una parola che identifica la fonte.

Sui formati, in ordine di preferenza. Il testo semplice o Markdown è il migliore, perché è cercabile, diffabile e non porta rumore: per una discussione basta il corpo dei messaggi con l'autore e la data, senza la struttura di navigazione del sito. Il salvataggio della pagina come singolo file HTML va bene e si legge, ma contiene molto rumore. Il PDF è accettabile. Uno screenshot è l'ultima scelta, perché non è cercabile né citabile parola per parola, e va riservato ai casi in cui il contenuto è grafico.

Sulle chat esiste una forma di consegna che vale più di tutte le altre e che va chiesta esplicitamente, perché l'utente non ha motivo di inventarla. Si tratta della ricerca interna al canale con un termine concordato, di cui si consegna la lista dei risultati; l'esportazione del canale è voluminosa e richiede strumenti discutibili, e la copia di una conversazione scelta a occhio perde ciò che non si è pensato di cercare. La ragione è che il filtro incorpora la domanda, e chi cerca sa che cosa sta cercando.

Ne segue una prescrizione per chi chiede il materiale. Si concordano i termini di ricerca prima, non il canale. Si chiede il conteggio dei risultati insieme alle schermate, perché sapere che un filtro ha dato zero risultati è esso stesso un dato. E si accetta che su un filtro molto generico l'utente si fermi a una parte dei risultati, purché dichiari dove si è fermato, così che la copertura parziale resti dichiarata invece di sembrare completa.

Per un video la forma utile non è il video ma la sua trascrizione, e le due vie per ottenerla non costano lo stesso. Dove esistono i sottotitoli automatici si scaricano da riga di comando e si ripuliscono con `vtt-to-text.py` del pacchetto `community-sources`, che ricostruisce il parlato una volta sola: i sottotitoli a scorrimento ripetono quasi per intero il blocco precedente, e convertirli ingenuamente produce un file tre o quattro volte più lungo del parlato. Dove non esistono serve il riconoscimento vocale, che costa minuti invece di secondi ma non costa più una infrastruttura: il pacchetto `voicestudio` lo fa in locale, senza mandare l'audio a nessun servizio e senza un account, e scrive la trascrizione nella stessa cartella con la stessa convenzione. In entrambi i casi conviene conservare accanto l'identificativo del video, perché la trascrizione da sola non dice da dove viene; lo strumento del secondo caso scrive quella provenienza da sé, insieme al modello che ha trascritto e alla dichiarazione che il testo non è stato riletto, che è la cautela giusta perché i nomi propri e i numeri sono esattamente ciò che il riconoscimento sbaglia e ciò per cui si cita una fonte tecnica.

Una richiesta di materiale va sempre accompagnata dalla domanda a cui serve rispondere. Chiedere una discussione intera senza dire cosa si cerca produce lavoro inutile per chi la procura e lettura inutile per chi la riceve.

## Come si annota una fonte non letta

Nel registro delle fonti la voce resta, perché sapere che esiste ha valore. Cambia la descrizione, che deve dire che non è stata letta e perché. La formula da usare è indicare il dominio come luogo dove cercare e non come fonte verificata, e questa distinzione va ripetuta nella sezione che separa le fonti consultate da quelle catalogate.

Quando una fonte prima non leggibile diventa leggibile, per esempio perché sono state configurate le credenziali, l'etichetta va rimossa e la voce va aggiornata con ciò che la fonte documenta davvero. Una etichetta di indisponibilità che sopravvive alla sua causa è peggio della sua assenza, perché scoraggia dal riprovare.

## Che cosa resta di terzi anche quando la via è legittima

La legittimità della via non esaurisce la questione, perché i messaggi di un canale sono scritti da altre persone e archiviarli sistematicamente li sottrae al loro contesto; la circostanza che siano visibili a tutti i membri di quella community non equivale a un'autorizzazione a conservarli altrove.

Quattro accorgimenti rendono la conservazione difendibile invece di soltanto dichiarata. Si conserva l'identificativo dell'autore accanto al contenuto, perché senza di esso una richiesta di cancellazione mirata non è eseguibile e prometterla sarebbe una promessa vuota. Si tiene il materiale in un luogo unico, cosicché una cancellazione sia un'operazione e non una ricerca. Si elimina il materiale grezzo quando la sintesi con l'attribuzione lo ha reso superfluo, che è già la forma minima di limitazione della conservazione. E si richiedono i soli permessi necessari, perché domandarne di ampi per prudenza è il contrario della prudenza.

Dove il materiale raccolto contenga informazioni personali di residenti in giurisdizioni con una disciplina sulla protezione dei dati, valgono le considerazioni ordinarie di quella disciplina, cioè minimizzazione, finalità dichiarata e tempi di conservazione: non è un'area libera solo perché il canale è visibile all'interno della community.
