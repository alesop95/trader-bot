# Pacchetto opzionale: alignment

> Controllo eseguibile che dice quali affermazioni di un progetto stanno invecchiando in silenzio: le scadenze scritte in prosa che nessuno guarda, le misure più vecchie della loro cadenza, le domande aperte che nessun programma può chiudere, e gli invarianti fra ciò che i documenti affermano e ciò che sta davvero nel repository. È l'attuazione meccanica della regola `rules/affermazioni-verificabili.md` di questo pacchetto, che va istanziata insieme allo strumento perché è il criterio, e lo strumento da solo non decide nulla.

## Il problema, e perché non è il drift delle schede

Il sistema di questo template ha già un motore di riconciliazione, la skill `sync-context`, e copre bene la domanda "questa scheda descrive ancora il codice che dichiara di coprire". Confronta il frontmatter con il diff dei percorsi coperti e propone edit chirurgici.

C'è però una classe di obsolescenza che quel motore non vede, perché risponde a una domanda diversa da quella per cui la skill è stata scritta. Il drift si misura contro il *codice*, cioè contro qualcosa che sta nel repository e che git conosce. Un'affermazione su un fatto esterno non ha nulla contro cui essere misurata: che una copia di backup fuori sede esista, che una licenza sia coperta, che un'automazione stia girando, che una persona abbia risposto a una domanda. Nessun `git diff` la contraddice mai. Nasce vera e il momento in cui smette di esserlo non lascia traccia.

La differenza pratica fra i due strumenti è anche di natura. `sync-context` è una procedura guidata dall'LLM, quindi costa contesto, richiede una sessione e produce un giudizio; questo è un test deterministico con un codice di uscita, quindi si mette in un hook di avvio, non consuma contesto e produce un fatto. I due si usano insieme: il primo aggiorna le schede, il secondo dice che c'è qualcosa da guardare.

## Perché la buona volontà non basta, in tre numeri

Nel progetto reale da cui questo pacchetto è estratto, in una sola mattina sono state misurate tre obsolescenze, e nessuna era una contraddizione che un lettore attento avrebbe potuto cogliere leggendo i documenti. La copia di backup fuori sede era ferma da sei settimane e ogni documento del progetto continuava ad affermare che esisteva. La scheda dello stack elencava cinque script su ventuno. Una pendenza dichiarava scaduta una cadenza che era invece rispettata.

Nello stesso passaggio si è contato che nei file tracciati vivevano *sedici date* di scadenza o di presidio scritte in prosa, e che nessun meccanismo le guardava. Ogni incidente che in quel progetto aveva fatto danno era una di quelle date: una licenza scaduta che ha spento per due giorni la fonte automatica con cui si verificava il lavoro, e un abbonamento di spazio cloud scaduto che ha messo una data di cancellazione sull'unica copia storica dei backup.

Nei cinque giorni successivi all'adozione, lo stesso impianto ha trovato un'automazione pianificata che non era mai partita, una replica fuori sede che i documenti davano per esistente e che non esisteva, un guard-rail che non cercava dodici valori reali, e due voci di un registro arrivate in un commit con lo stesso numero perché scritte lo stesso giorno da due sessioni di lavoro diverse. Conta meno la quantità del fatto che nessuno di questi fosse visibile leggendo.

## Le quattro famiglie di controllo

Le *scadenze* sono le date scritte in prosa, portate nel registro con il loro preavviso e con la conseguenza scritta accanto. La conseguenza non è un ornamento: una data senza la sua ricaduta non fa agire nessuno, ed è la differenza fra "il 22 novembre scade una licenza" e "il 22 novembre la fonte con cui verifichiamo la configurazione smette di rispondere".

La *freschezza* confronta l'età di una misura con la cadenza dichiarata per la fonte che la produce. Della misura si legge la sola data di modifica, mai il contenuto, così nomi host, utenti e indirizzi non entrano nell'output nemmeno per errore. Se il file dichiara dentro di sé la data della misura, il campo `campo_data` la preferisce alla data di modifica, che è più fragile.

La freschezza e la raggiungibilità sono due domande diverse. Uno snapshot può essere vecchio perché il rinfresco non è stato eseguito, oppure perché il processo non riesce più a trovare la sorgente pur avendola ancora sul disco. Un resolver portabile usa in ordine un override esplicito, le variabili della piattaforma, il percorso registrato nell'ultima baseline locale e infine una ricerca limitata; il percorso della baseline è un candidato, non un'autorità, e si accetta soltanto se esiste e l'identità della sorgente coincide con quella attesa. Se nessun candidato supera la validazione, il controllo dichiara la fonte non raggiungibile e non produce né un verde né una baseline nuova. La regola nasce da un caso reale in cui le variabili automatiche puntavano a un secondo aggancio vuoto, mentre tre baseline ignorate da git conservavano ancora i percorsi validi delle librerie sorvegliate.

Le *asserzioni umane* sono le affermazioni che nessun programma può verificare, e ricevono perciò una validità dichiarata: quando scade tornano a video come domanda, con la domanda già scritta e il ruolo della persona a cui porla. Scrivere la domanda adesso è la parte che si dimentica, ed è quella che conta: fra due mesi nessuno ricostruirà che cosa andava chiesto.

Gli *invarianti* sono quattro e stanno nel codice, non nel registro, perché un invariante è strutturale mentre una scadenza è un fatto. Gli script presenti nella cartella e non citati nella scheda dello stack. Le decisioni richiamate da qualunque documento e non definite nel registro delle decisioni. L'unicità dei numeri e degli identificatori di un registro numerato, se il progetto ne ha uno. E il campo di firma delle schede, che merita un paragrafo a sé.

## L'invariante sul campo di firma, sbagliato due volte prima di essere giusto

Vale la pena conoscere entrambi gli errori, perché sono la ragione per cui questo invariante è scritto in un modo che a prima vista sembra troppo complicato.

La prima versione confrontava `last-verified-commit` con HEAD. Segnalava tutte le schede dopo qualunque commit, anche uno che non le riguardava: un giallo perpetuo, cioè il difetto che tutto questo impianto esiste per evitare.

La seconda lo confrontava con il commit che aveva toccato la scheda per ultimo. Meglio, e ancora impossibile: la regola prescrive di bumpare dopo il commit, ma il bump scrive dentro la scheda, quindi genera un commit nuovo che la tocca e riporta il confronto in giallo. Una sessione veniva segnalata per aver rispettato la regola, che è la forma peggiore di avviso perpetuo perché punisce il comportamento corretto e insegna a ignorare il controllo proprio a chi lo sta usando bene.

La distinzione che scioglie il nodo è fra una *modifica* e una *firma*. Un commit che tocca i soli campi di firma non cambia la scheda, la firma. Il controllo risale la storia del singolo file saltando i commit di sola firma, trova l'ultima modifica di contenuto, e verifica per *discendenza* e non per uguaglianza: la scheda è allineata se l'hash dichiarato è quel commit o un suo discendente. Ne discende che resta verde anche chi rilegge una scheda immutata a una data successiva e porta l'hash in avanti, che è esattamente ciò che la regola del bump chiede di fare.

Due dettagli del comportamento, entrambi scelti. Un commit che aggiunge una riga di contenuto e ribumpa insieme conta come modifica di contenuto: nel dubbio il controllo segnala. E un hash che non risolve nella storia non è un disallineamento ma un *riferimento rotto*, riportato in rosso a parte, perché la causa è diversa, cioè un hash scritto a mano male o una storia riscritta sotto i piedi.

## Che cosa ha trovato la prova su questo repository, e perché è scritto qui

Il pacchetto è stato provato sul template, che per un controllo del genere è il caso peggiore: il repository del template non adotta il proprio sistema su di sé, quindi non ha schede, né registro delle decisioni, né cartella di script. La prova ha trovato tre difetti che la prova sul progetto di origine non poteva trovare, e vale conoscerli perché due riguardano il modo in cui lo strumento va usato.

Il primo: senza registro lo strumento esce con codice 2, correttamente, ma con un registro *vuoto* dichiarava "allineato, nessuna affermazione scaduta", cioè esattamente il verde non calcolato che tutta la sua ragione d'essere condanna. Ora un registro vuoto è un esito giallo dichiarato, e gli invarianti restano calcolati perché non dipendono dal registro.

Il secondo: le voci di esempio, copiate senza modifiche, producevano un rosso finto su date segnaposto illeggibili. Nascono perciò *inerti*, nelle chiavi che cominciano per `_esempio` e che lo strumento non legge, e si copiano dentro gli array quando si scrive la prima voce vera.

Il terzo riguarda una scelta di generalizzazione. Allargando l'ampiezza del richiamo numerico da tre a quattro cifre, per accogliere registri più grandi, il controllo ha segnalato come riferimento a una voce inesistente il numero di un ticket di un sistema esterno citato in prosa: un falso positivo inventato alla prima esecuzione su un corpus reale, che è il modo più rapido per perdere la fiducia di chi legge il report. Il default è quindi tornato stretto, due o tre cifre, e l'ampiezza si dichiara nel registro con `richiami_cifre` quando un progetto numera oltre il migliaio.

## Rumoroso e non bloccante, che è una scelta

Lo strumento gira a ogni avvio di sessione e non blocca. La ragione è la stessa che governa le tolleranze dei singoli invarianti: un controllo che fallisce sempre smette di essere letto, e questo gira ogni volta. Distingue perciò nel codice di uscita il *giallo* dal *rosso*, dove il giallo è un'affermazione che sta invecchiando e non marca la sessione come fallita, e il rosso è qualcosa di già rotto. Esce comunque con un codice diverso da zero sul rosso, così che un domani possa diventare bloccante senza riscriverlo.

Ne discende una pratica sullo scrivere il registro. Un'eccezione decisa da una persona si dichiara nel posto dove il controllo la legge, con la sua ragione accanto, e il controllo la conta a parte: un'eccezione dichiarata resta visibile come eccezione, un'eccezione subita diventa rumore.

## Cosa istanzia, e dove

Nel progetto vanno tre cose.

Lo strumento `tools/Test-Allineamento.py` va in `tools/`, oppure in `scripts/` se il progetto usa quella convenzione. Non porta cablata l'anatomia di nessun progetto: i percorsi si dichiarano nel blocco `percorsi` del registro, e una voce messa a `null` dichiara che quella cosa nel progetto non esiste, così l'invariante corrispondente si annuncia non applicabile invece di fallire.

Il registro va tracciato. Si copia `scadenze.example.json` in `data/scadenze.json`, oppure altrove passando `--registro`, e si sostituiscono le voci di esempio con quelle vere. Va tracciato perché è la parte del progetto che dichiara cosa scade, e va tenuto pulito allo stesso modo dei documenti: date, cadenze e riferimenti, mai importi né identificativi né nomi di persona, perché l'esito del controllo finisce sotto gli occhi di chiunque guardi la sessione. Se il file manca, lo strumento esce con codice 2 e lo dichiara, invece di stampare un verde che non ha calcolato.

La regola `rules/affermazioni-verificabili.md` va in `.claude/rules/` e va dichiarata fra quelle da caricare sempre nel `CLAUDE.md` del progetto. È il passo che si dimentica, ed è quello che rende il registro non vuoto: senza il vincolo su ciò che si scrive, il controllo ha pochi dati da guardare e sembra inutile.

Infine si registra l'esecuzione in un hook `SessionStart` di `settings.json`, accanto agli altri controlli di avvio del progetto.

```
python tools/Test-Allineamento.py                report completo
python tools/Test-Allineamento.py --silenzioso   solo il verdetto
python tools/Test-Allineamento.py --giorni 30    orizzonte delle scadenze mostrate
python tools/Test-Allineamento.py --registro X   registro in una posizione diversa
python tools/Test-Allineamento.py --radice Y     radice del repository
```

## Quando offrirlo

Si offre a un progetto che ha almeno una di queste tre cose: fatti esterni che il repository non contiene, cioè licenze, abbonamenti, contratti, misure prese da fonti vive; documentazione che descrive un'infrastruttura o un sistema di terzi, che cambia senza notificare; oppure più sessioni di lavoro o più persone che scrivono sugli stessi file.

Non si offre a un progetto di solo codice dove ogni affermazione è verificabile eseguendo i test: là il posto giusto per un invariante è la suite, non un registro di scadenze.

## Portabilità

Lo strumento risale alla radice del repository dalla posizione del proprio file, cercando `.git` sia come cartella sia come file perché in un worktree e in un submodulo è un file che punta altrove, e accetta `--radice` per i casi in cui la risalita non basti. La ragione è che la cartella corrente dipende da chi invoca, e chi invoca può essere una sessione, un hook, un'attività pianificata o un altro script: quattro cartelle diverse per lo stesso comando.

Non usa dipendenze esterne, non apre connessioni, non legge credenziali e non scrive nulla: legge file già sul disco e interroga git. È la ragione per cui si automatizza senza pensarci, a differenza degli script che rinfrescano una misura interrogando un fornitore.

## Requisiti e stato

Python 3.8 o superiore, git nel PATH. Nessuna libreria esterna.

Estratto da un progetto reale di documentazione infrastrutturale, dove gira a ogni avvio di sessione da settembre 2026 su ventisei controlli fra scadenze, cadenze, asserzioni e invarianti. La versione di questo pacchetto è generalizzata: i percorsi sono configurabili, gli invarianti specifici di quel dominio non sono risaliti, e la verifica meccanica prescritta da questo template è che una ricerca dei nomi del progetto di origine dentro questi file dia zero riscontri.
