# community-sources

Pacchetto per le fonti che nessuno strumento di sessione raggiunge e che per certi domini tecnici sono la sola documentazione esistente: quelle che vivono dentro canali di conversazione di community, e quelle che vivono dentro catene di discussioni pubbliche che si citano a vicenda. La ragione d'essere del pacchetto è meno ovvia di quanto sembri, ed è la stessa per entrambe le famiglie: le vie per leggerle sono più d'una, e alcune hanno conseguenze che vale conoscere prima di scegliere.

Contiene sei strumenti, che servono bisogni distinti e non si sostituiscono a vicenda. I primi tre recuperano, gli altri tre riducono ciò che il recupero ha prodotto, e la distinzione conta perché un recupero senza riduzione produce materiale che nessuno legge.

Dei tre che recuperano, `fetch-discord.py` legge un canale attraverso un bot account ufficiale e tiene un cursore, quindi è quello degli aggiornamenti frequenti dove un bot è stato invitato. `export-discord.py` orchestra un esportatore di terze parti su un insieme di canali scelti e motivati, quindi è quello delle esportazioni ampie e rare, comprese quelle sui server dove un bot non può entrare. `fetch-reddit.py` attraversa il grafo dei rinvii a partire da un post di Reddit e ne produce una copia leggibile con la mappa di chi linka che cosa, quindi è quello delle fonti che non stanno in un canale ma in una catena di discussioni che si citano a vicenda.

Dei tre che riducono, `read-chat-export.py` trasforma l'export in JSON di un canale, Discord o Telegram, in Markdown filtrato per parola chiave e per intervallo di date. `vtt-to-text.py` ricostruisce il parlato di un video dai sottotitoli a scorrimento, che ripetono ogni riga e senza questo passo producono un file tre o quattro volte più lungo del parlato. `censimento-fonti.py` prende una corsa del lettore di Reddit, cioè centinaia di nodi e archi, e ne fa un elenco di fonti distinte raggruppate per argomento, con le righe pronte per il registro delle fonti del progetto.

La regola che le distingue è `.claude/skills/fonti-non-recuperabili/RIFERIMENTO.md`, che appartiene alle regole sempre caricate e non a questo pacchetto: il pacchetto è lo strumento, la regola è il criterio. Chi istanzia questo pacchetto senza quella regola si ritrova con un programma che funziona e senza il vocabolario per decidere quando usarlo.

## Che cosa istanzia

Sei file, da copiare in `tools/` del progetto ospite, insieme o separatamente perché non dipendono l'uno dall'altro. Python 3 e sola libreria standard, con una sola dipendenza facoltativa: `fetch-reddit.py` usa il pacchetto `certifi` se lo trova, per la ragione misurata che la sezione sulle radici dei certificati spiega, e senza di esso torna alle radici del sistema invece di fallire.

`fetch-discord.py` funziona da solo. `export-discord.py` invoca un programma esterno, DiscordChatExporter, che non è una dipendenza del repository e vive fuori da esso: la procedura per procurarselo è più sotto. E porta una tabella dei canali che all'istanziazione va sostituita, perché quella che il file contiene è un esempio della forma e non una configurazione di partenza.

`fetch-reddit.py` è il più semplice da istanziare dei tre, e vale dire perché invece di lasciarlo scoprire: non porta alcuna tabella da sostituire, perché il punto di partenza è un argomento di riga di comando e i filtri sono opzioni, quindi nel file non c'è conoscenza del progetto ospite; e non richiede nulla in `.env`, perché la via che percorre non usa credenziali. L'unico segnaposto da sostituire è lo user agent, come negli altri due. La radice si ricava dalla posizione del file, cioè la cartella che contiene `tools/`, quindi copiato in `<progetto>/tools/` scrive sotto `<progetto>/_notes/fonti/` senza che nessuno configuri un percorso; eseguito invece dove vive nel template quel calcolo cadrebbe dentro il pacchetto, e per quel solo caso esiste l'opzione `--radice`.

Dei tre strumenti di riduzione, due non hanno alcun segnaposto: `read-chat-export.py` e `vtt-to-text.py` lavorano su un file che ricevono come argomento e non sanno nulla del progetto ospite. `censimento-fonti.py` invece ne porta uno che va sostituito e che non è una stringa ma una tabella, cioè il livello di affidabilità per host: la forma resta, i pochi host che contiene sono quelli il cui livello non dipende dal dominio di cui il progetto si occupa, e il resto lo scrive chi quel dominio lo conosce. Lasciarla come si trova non rompe niente e produce un censimento in cui quasi tutto è di livello cinque, che è il livello predefinito e vuol dire community: il difetto è quindi silenzioso, ed è la ragione per cui è scritto qui.

Resta una voce di permesso da aggiungere a mano nel progetto ospite, e non sta nel `settings.json` di base perché quella baseline non elenca gli strumenti dei pacchetti opzionali e non è questo il posto per cominciare. Senza di essa nulla si rompe: si conferma a ogni invocazione, che è attrito e non un ostacolo.

```
Bash(python tools/fetch-reddit.py:*)
```

## Perché un programma e non un server MCP

La scelta va motivata perché la letteratura sul tema raccomanda l'altra strada, e la raccomandazione è giusta per un contesto diverso da questo. Un server MCP dedicato a Discord serve quando un agente residente deve poter chiamare quel tool nel mezzo di una conversazione, decidendo lui quando leggere; è il caso di un assistente che vive su un server e a cui si chiede che cosa sia stato detto in un canale.

Qui il compito è un altro: leggere una fonte e trasferirne la sintesi nel registro delle fonti del progetto. È lavoro deterministico, e la regola `token-economy.md` prescrive di tenere il lavoro deterministico su codice invece che su modello. Un programma sulla sola libreria standard fa quel lavoro senza aggiungere un ambiente di esecuzione ulteriore, un pacchetto di terze parti a cui affidare una credenziale, e uno strato di protocollo interposto fra il chiamante e una richiesta HTTP.

Le due vie non si escludono, perché usano il medesimo bot account: un progetto che avesse entrambe le esigenze può istanziare questo strumento e configurare un server MCP con lo stesso token.

## Il secondo strumento, e la disciplina che porta con sé

`export-discord.py` non esporta: orchestra. Riceve la scelta dei canali dalla propria tabella interna, invoca l'esportatore esterno una volta per canale, salta ciò che è già stato esportato, prosegue quando un canale fallisce e riferisce alla fine. Ha una prova a vuoto che stampa che cosa farebbe senza eseguire e senza chiedere alcuna credenziale.

La parte riusabile di quello strumento non è il codice ma la disciplina della sua tabella, e va conservata all'istanziazione: ogni canale dichiara a quale domanda aperta del progetto risponde. La ragione è che un canale scelto per argomento produce materiale da leggere, mentre un canale scelto per domanda produce risposte, e la differenza si vede al momento di leggere l'export, quando è troppo tardi per cambiarla. La tabella è anche il documento che, fra sei mesi, dirà se un canale vale ancora la pena.

Da questa disciplina discendono due proprietà pratiche. I canali si raggruppano per priorità, cosicché si esporti il gruppo che risponde a una domanda invece di tutto insieme: su un server di sviluppo maturo i canali sono decine e quelli utili sono pochi, e l'esperienza registrata è di trenta canali scelti su quasi quattrocento. E i server esclusi si dichiarano con il motivo, perché una esclusione senza motivo è indistinguibile da una dimenticanza e verrà riaperta dalla prossima sessione.

Il token si chiede in modo interattivo, e la ragione va conosciuta perché è un errore facile: PowerShell registra la cronologia dei comandi in un file di testo in chiaro, il cui percorso si ottiene con `(Get-PSReadlineOption).HistorySavePath`, quindi una credenziale passata come argomento finisce su disco senza che nessuno l'abbia scritta lì, e ripulirla richiede di modificare quel file a mano. La richiesta interattiva non lascia quella traccia.

## Il terzo strumento, e la via che si è aperta dopo un vicolo cieco

`fetch-reddit.py` risolve un problema di forma diversa dagli altri due. Là la fonte è un canale e il compito è leggerne la cronologia; qui la fonte è un post che dice poco di suo e rinvia a decine di altri post, ciascuno dei quali rinvia altrove, quindi la conoscenza sta nel grafo e non nel nodo di partenza. Leggere il solo post che si ha in mano significa leggere l'indice e credere di aver letto il libro.

La via merita di essere raccontata perché la regola sulle fonti non recuperabili dichiarava Reddit un vicolo cieco, e quella dichiarazione era vera quando è stata scritta. Gli endpoint che restituiscono JSON rifiutano, i frontend alternativi e i proxy di lettura rifiutano, il crawler del modello dichiara di non poter raggiungere il dominio, e l'API ufficiale a sole credenziali applicative è rimasta inaccessibile perché la registrazione dell'applicazione è stata rifiutata dal server senza motivo dichiarato. Una sola cosa è cambiata rispetto a quel registro, ed è più insidiosa di un rifiuto: la pagina HTML oggi risponde con un codice di successo, ma quegli ottomila byte sono la pagina di verifica anti-bot e non contengono nulla.

La via che si è aperta è un archivio pubblico di terze parti, Arctic Shift, successore di Pushshift, che pubblica di propria iniziativa un'API documentata sul proprio archivio di Reddit e non chiede alcuna credenziale. È un caso che il criterio di legittimità della regola non copriva, e vale enunciare come vi rientra: non è il canale di automazione del fornitore del servizio, e non c'è alcun meccanismo di consenso perché non c'è nulla da autorizzare; ciò che la rende legittima è che si interroga un servizio che ha costruito quel canale per l'accesso programmatico, con limiti di frequenza pensati per traffico automatico, chiedendogli i propri dati e non quelli di Reddit. Il costo si sposta di conseguenza dal permesso alla fedeltà, ed è la sola cosa che va sorvegliata.

Le due debolezze sono opposte e vanno conosciute prima di usare lo strumento, non dopo. Un archivio ha latenza, quindi un post molto recente può non essere ancora indicizzato: l'assenza di un post dallo strumento non prova che il post non esista, ed è la ragione per cui quell'esito si chiama assente e non inesistente. E un archivio conserva anche ciò che su Reddit è stato cancellato, quindi il materiale prodotto può contenere testo che il suo autore ha rimosso: l'intestazione di ogni file dichiara perciò la provenienza e il momento di archiviazione del record, e l'identificativo dell'autore viaggia accanto al contenuto, che è il primo dei quattro accorgimenti descritti più sotto.

L'attraversamento è in ampiezza, per due ragioni che non sono di gusto. La prima è economica: l'archivio accetta fino a cinquecento identificativi in una sola richiesta, quindi raccogliere tutti i post di un livello prima di chiamare trasforma centinaia di richieste in una manciata. La seconda riguarda la qualità di ciò che resta fuori quando un tetto si esaurisce, perché in ampiezza si taglia il materiale più lontano dal punto di partenza, che è quasi sempre il meno pertinente, mentre in profondità si taglierebbe a caso.

I tetti esistono perché il grafo non ha un confine naturale, e introducono un difetto proprio che va presidiato invece che accettato: una corsa troncata è indistinguibile da una completa, e chi ne legge il risultato crede di avere tutto. Il presidio è che ciò che il tetto ha escluso non scompare ma finisce elencato come non raggiunto nell'indice e come pendente nello stato su disco, cosicché la copertura parziale resti dichiarata e un rilancio con il tetto alzato prosegua invece di ricominciare.

Lo stesso principio governa i collegamenti esterni, che finiscono in uno di tre stati da non confondere. Scaricato è la pagina letta e ridotta a testo. Catalogato è l'indirizzo registrato con il motivo per cui non si scarica, cioè un video di cui servirebbe la trascrizione, un documento che vive dentro uno scheletro JavaScript, un file binario, una pagina che richiede autenticazione, un dominio escluso da chi ha lanciato la corsa. Fallito è il tentativo fatto e non riuscito, con il codice osservato. Contare un catalogato come uno scaricato produrrebbe esattamente quella falsa impressione di copertura che i tetti dichiarati cercano di evitare.

L'uscita è una cartella per corsa, sotto `_notes/fonti/`, e i due file da cui si parte rispondono a domande diverse. `_INDEX.md` dice che cosa c'è, cioè l'elenco dei nodi con i loro dati e il loro esito, ed è il Livello 1 della disclosure progressiva che `token-economy.md` prescrive. `MAPPA.md` dice come le fonti si tengono, cioè quale contenuto rinvia a quale altro e con che parole, ed è la sola forma in cui si vede dove la catena si interrompe, perché un nodo catalogato o non raggiunto compare comunque nell'albero nel punto in cui qualcuno lo ha citato. L'albero non è il grafo ma una sua lettura, perché i post di un raccoglitore si citano a vicenda e quindi il grafo ha cicli: un nodo già comparso si segnala come tale invece di essere espanso una seconda volta, e il grafo vero, senza quella semplificazione, sta in `mappa.json` per l'uso da programma. Accanto resta il JSON grezzo di ogni post e l'HTML grezzo di ogni pagina, perché l'estrattore di testo che sta nel file è minimo per scelta e il grezzo permette di rifare meglio il lavoro senza ri-scaricare nulla. La cartella porta infine un `.md-unwrap-ignore`, che la esenta dal normalizzatore di Markdown del sistema, e la ragione non è di comodo: quei file riportano prosa di terzi verbatim, e la convenzione di un paragrafo per riga sorgente è una regola sui documenti che scriviamo noi e non una licenza a riscrivere il testo di qualcun altro.

Verso l'archivio non c'è nulla da negoziare, perché si governa da sé con i limiti di frequenza che dichiara nelle intestazioni. Verso un sito qualunque, invece, lo strumento è un programma che visita pagine altrui e si comporta di conseguenza: legge `robots.txt` una volta per host e ne rispetta il divieto, attende un intervallo minimo fra due richieste allo stesso host, dichiara uno user agent descrittivo e rifiuta le risposte oltre un tetto di dimensione. Non esiste un'opzione per disattivare nulla di questo, per la stessa ragione per cui il primo strumento non espone un modo per inviare un'intestazione da account personale.

```
python tools/fetch-reddit.py --self-test
python tools/fetch-reddit.py crawl <url o id> --dry-run
python tools/fetch-reddit.py crawl <url o id> --max-post 50 --max-profondita 1
python tools/fetch-reddit.py crawl <url o id> --max-post 500 --esterni
python tools/fetch-reddit.py crawl <url o id> --esterni --dominio-escluso youtube.com
python tools/fetch-reddit.py riprendi <cartella> --max-post 1000
python tools/fetch-reddit.py post <id>
```

La prova a vuoto non è quella dell'orchestratore di export, e la differenza va detta perché altrimenti si prende per una promessa non mantenuta: quella non chiama nulla, questa chiama una volta, perché il grafo di un crawler non si conosce senza guardare il primo nodo. Scarica il solo punto di partenza e riferisce la frontiera che genererebbe al primo livello, con il costo in richieste, senza scrivere nulla su disco. Su un post raccoglitore conviene sempre precedere con essa una corsa piena, perché è là che si scopre se la frontiera del primo livello ha decine di elementi o centinaia.

## Procurarsi l'esportatore esterno

DiscordChatExporter è un programma di terze parti, maturo e diffuso, che esporta la cronologia di un canale in HTML, testo, JSON o CSV e scarica gli allegati. Il repository è `https://github.com/Tyrrrz/DiscordChatExporter` e i file pronti stanno nella pagina dei rilasci, `https://github.com/Tyrrrz/DiscordChatExporter/releases/latest`. Sono autonomi e non richiedono di installare alcun ambiente di esecuzione.

Gli archivi hanno un nome che dichiara piattaforma e architettura, e la scelta va fatta guardando quello invece di prendere il primo. Le voci il cui nome contiene `.Cli.` sono la riga di comando, ed è quella che serve a questo pacchetto; quelle senza sono l'interfaccia grafica, comoda la prima volta per percorrere molti server e capire quali canali esistano. Il suffisso dichiara il sistema, cioè `win`, `linux` oppure `osx`, e l'architettura, cioè `x64` per i processori Intel e AMD, `arm64` per i processori ARM, `x86` per i sistemi a trentadue bit. Esiste anche una immagine Docker, che è la via da preferire dove non si voglia estrarre nulla.

Il programma non entra nel repository, perché sono decine di megabyte di binari senza rapporto con il version control, e conviene collocarlo in una cartella condivisa dai progetti che ne hanno bisogno. Il percorso dell'eseguibile si passa a `export-discord.py` con `--dce`, oppure si mette una volta per macchina nella variabile d'ambiente `DCE_PATH`.

## La procedura completa, dall'inizio alla fine

Sette passi, e i primi tre si fanno una volta sola.

Primo, si sceglie la via: un bot account se i canali che servono stanno su server propri o su server il cui amministratore acconsente, la credenziale personale altrimenti, con la decisione registrata come tale. Il criterio è nella regola sulle fonti non recuperabili e il paragrafo seguente di questo README ne riassume il limite.

Secondo, si procura l'esportatore secondo la sezione precedente e si istanziano i due strumenti in `tools/`.

Terzo, si sostituisce la tabella dei canali di `export-discord.py` con la propria. Per compilarla servono gli identificativi, e si ottengono con i comandi dell'esportatore stesso: `guilds` elenca i server accessibili, `channels -g ID` i canali di uno di essi. Conviene salvare quei due elenchi in un file locale con annotata accanto la pertinenza di ciascuna voce, perché è il documento su cui si compila la tabella e serve di nuovo alla revisione successiva.

Quarto, si guarda che cosa farebbe, con la prova a vuoto: non chiede credenziali e non esegue nulla.

Quinto, si esporta un gruppo per volta, cominciando da quello che risponde alla domanda più urgente. Un export lungo rallenta da sé, perché l'esportatore rispetta i limiti di frequenza del servizio: è il comportamento corretto e va lasciato girare invece di interrotto e rilanciato.

Sesto, si riduce l'export a materiale leggibile e citabile con `read-chat-export.py`, che tiene autore, momento, testo, allegati e citazioni e butta il resto. Il formato JSON è quello che quello strumento digerisce; quello HTML serve alla lettura umana, e sullo stesso canale conviene produrre entrambi perché sono due usi diversi del medesimo materiale. La riduzione non è un passo facoltativo di cosmesi: un canale di poche migliaia di messaggi esce dall'esportatore come decine di megabyte, cioè come un file che in conversazione non entra.

Settimo, e è il passo che dà senso ai precedenti, si legge e si trasferisce: la sintesi con l'attribuzione entra nel registro delle fonti del progetto con la profondità che rende il file grezzo sacrificabile, e il grezzo si elimina quando non porta più informazione che non sia scritta altrove. Un export conservato accanto alla propria sintesi produce il dubbio su quale sia quella buona, e il dubbio costa più di quanto valga la copia.

Una avvertenza chiude la procedura e riguarda il metodo, non lo strumento: la ricerca per parola chiave su un export è un filtro cieco alla domanda, mentre la ricerca interna al canale fatta da chi conosce la domanda incorpora la domanda. L'esperienza registrata è che la seconda renda più della prima; ne segue che un export in blocco non sostituisce la ricerca mirata ma la precede, e che i termini da cercare vanno scelti prima di lanciare il filtro.

## Le tre vie di accesso, e quale implementa il primo strumento

La prima via è il token del proprio account personale, cioè il self-bot. Funziona tecnicamente e non richiede il permesso di nessuno, perché l'account è già dentro il server. È vietata dalle condizioni d'uso di Discord, che dedicano alla questione una pagina di supporto, e la sanzione dichiarata è la terminazione dell'account senza distinzione di intenzioni. Va aggiunto un argomento che di solito manca nella valutazione: un token utente dà accesso a tutto ciò che vede l'account, messaggi privati compresi, quindi il danno di una sua fuga è incomparabilmente più ampio di quello di un token con permessi ristretti.

La seconda via è la copia manuale del materiale pertinente. Non richiede nulla, non ha rischi, e ha una qualità che le vie automatiche non hanno: chi copia sa che cosa sta cercando, quindi il filtro incorpora la domanda. Su un progetto reale questa via ha corretto tre affermazioni errate del progetto in poche decine di schermate, con un rapporto fra segnale e volume che una lettura automatica integrale non avrebbe avuto.

La terza via è quella che questo strumento implementa, cioè un bot account creato nel portale per sviluppatori. La distinzione dalla prima poggia su fatti verificabili e non su una interpretazione benevola: il tipo di token è diverso e la documentazione ufficiale descrive il bot account come dedicato all'automazione; l'accesso a un server passa da un invito che chi amministra autorizza esplicitamente, scegliendo i permessi e potendoli revocare; il bot porta un contrassegno visibile a tutti, quindi non finge di essere una persona; l'API è pubblica, con limiti di frequenza pensati per traffico automatico, mentre un self-bot deve imitare artificialmente il ritmo di un umano; e il rischio in caso di uso scorretto ricade sull'applicazione e non sull'account personale.

## Il limite da conoscere prima di allestire

Un bot entra in un server soltanto se qualcuno con il permesso di gestione lo invita, e non esiste alcuna altra via perché è l'unico flusso che l'API espone. Su un server di cui non si è amministratori la terza via richiede quindi il consenso di terzi.

Il punto va capito nella sua forma esatta, perché è facile fraintenderlo: il cancello non è sui dati ma sul bot. I messaggi di un canale di cui si è membri sono già visibili, e nessuno autorizza a leggere ciò che il server mostra già; ciò che l'invito autorizza è far entrare una seconda identità dentro quel server. È questo che richiede il consenso, ed è corretto che lo richieda, perché altrimenti chiunque potrebbe immettere programmi nei server altrui.

Ne segue una prescrizione operativa in tre passi. Si chiede, perché chiedere è gratuito e alcune community di sviluppo accettano un lettore dichiarato. Si dichiara nella richiesta a che cosa serve e quali permessi si chiedono, cioè soltanto vedere il canale e leggerne la cronologia. E si accetta che un no sia un esito, dopo il quale resta la seconda via.

Esiste una eccezione parziale, ed è la sola che non richieda il consenso del server di origine: i canali di annunci di un server di tipo community si possono seguire da un altro server, con replica dei messaggi pubblicati, e il permesso necessario è quello di gestire i webhook nel server di destinazione, cioè nel proprio. Il limite è netto: riguarda i canali di annunci e non le discussioni, che è il posto dove sta la conoscenza tecnica. È utile per non perdere un rilascio, non per studiare un protocollo.

## Allestimento

Cinque passi, una volta sola.

Su `https://discord.com/developers/applications` si crea una applicazione e, nella sezione Bot, il bot; si copia il token, che il portale mostra una volta sola e che va trattato come una password.

Nella stessa sezione si abilita Message Content Intent, senza il quale Discord consegna i messaggi privi di testo anche a un bot che ha i permessi. La soglia oltre la quale quell'intent richiede una revisione è di diecimila utenti, non di cento server: i cento server sono la soglia della verifica formale dell'applicazione, che è cosa diversa, e confondere le due porta a credere di dover chiedere un'approvazione che non serve. Conviene spegnere Public Bot, cosicché nessun altro possa installare l'applicazione, e lasciare spento Requires OAuth2 Code Grant, che romperebbe l'invito.

Si genera l'URL di invito con i soli permessi di lettura, cioè View Channels e Read Message History, che sommati danno 66560, ossia 1024 più 65536. Il numero va calcolato e non copiato da un forum: ogni permesso è un bit di un intero, e un numero trovato altrove può concedere molto più di quanto si crede.

Si invita il bot nel server, che richiede di esserne amministratori o di ottenere il consenso di chi lo è.

Si scrive a mano `DISCORD_BOT_TOKEN` in `.env` nella radice del progetto, che il `.gitignore` esclude. Dove le regole di permesso negano i percorsi che corrispondono a `.env*`, e nel sistema di progetto di questo template lo fanno, l'agente non può creare quel file nemmeno come modello: è una limitazione voluta e non va aggirata.

## Uso

```
python tools/fetch-discord.py guilds
python tools/fetch-discord.py channels <id del server>
python tools/fetch-discord.py fetch <id del canale> --limit 500
python tools/fetch-discord.py fetch <id del canale> --limit 0 --nuovi
python tools/fetch-discord.py fetch <id> --grep "parola" --min-length 40 --since 2026-01-01
python tools/fetch-discord.py fetch <id> --append --out _notes/fonti/2026-01-31-canale.md
python tools/fetch-discord.py --self-test
```

Il cursore di `--nuovi` vive in `_notes/.discord-cursori.json` e avanza fino all'ultimo messaggio letto e non all'ultimo scritto, cosicché un filtro restrittivo non faccia rileggere ogni volta i messaggi che ha scartato. È la sola parte del costo che dipende da chi legge.

## I server piccoli, esportati interi

Le due tabelle dell'orchestratore non sono alternative di gusto e la scelta fra loro segue una regola. `CANALI` elenca i canali scelti uno per uno e produce un archivio leggibile, perché trenta canali scelti si leggono e un server intero no: è la via preferibile ogni volta che gli identificativi dei canali si conoscono. `GUILDS` elenca i server da esportare interi, si appoggia al sottocomando `exportguild` dell'esportatore esterno e non richiede alcun identificativo di canale.

Il caso che rende necessaria la seconda tabella è quello in cui gli identificativi non si conoscono, e vale enunciare perché non si risolve indovinandoli: il servizio, quando riceve un identificativo che non è un numero valido, risponde con un errore sul corpo della richiesta che non nomina il campo sbagliato, cioè con un messaggio che somiglia a un problema di permessi e non lo è. Davanti a identificativi ignoti la scelta corretta è cambiare granularità invece di tentare.

L'uscita di questa via è una cartella per server invece di un file per canale, perché i nomi dei canali si conoscono soltanto a esportazione avvenuta: l'esportatore esterno, quando riceve una cartella come destinazione, nomina da sé i file. La protezione contro la sovrascrittura è la stessa dell'altra via, cioè una cartella che esiste e non è vuota viene saltata a meno di `--forza`.

## Il presidio, e il principio che esemplifica

Lo strumento invia sempre l'intestazione di autorizzazione nella forma prevista per i bot, e prima di qualunque lettura verifica che l'account autenticato sia dichiarato tale, arrestandosi con la ragione se non lo è. Un token personale inserito per errore in quella variabile non produce quindi una lettura riuscita ma un rifiuto.

Il principio vale oltre il caso e governa anche il controllo degli identificativi e quello della data del filtro: una distinzione normativa diventa effettiva soltanto quando è resa meccanica nel punto in cui potrebbe essere violata per distrazione. Dichiararla nella documentazione la rende conoscibile, verificarla nel codice la rende operante.

Il presidio non va rimosso per far funzionare la prima via. Se un progetto decide di percorrerla, quella decisione va registrata come tale e richiede uno strumento diverso, non la disattivazione di un controllo dentro questo.

## Le difese contro un canale vero

Sette difese esistono perché un canale di prova non esercita nulla, e la circostanza vale come lezione generale sul collaudo. La prima esecuzione riuscita, su un progetto reale, era avvenuta su un canale con cinque messaggi e aveva dato esito positivo su ogni passo; ma un canale con cinque messaggi non impagina, non raggiunge alcun limite di frequenza, non produce guasti di rete, non contiene discussioni annidate né contenuti non testuali, e non ospita testo di terzi capace di rompere il file prodotto. Un collaudo riuscito misura anche ciò che l'apparato di prova sapeva sollecitare, e quel secondo dato non compare nel suo esito.

Il limite di frequenza è governato in modo reattivo, attendendo quanto il servizio dichiara nel rifiuto e prendendo il maggiore fra il valore dell'intestazione e quello del corpo, e in modo preventivo, leggendo a ogni risposta quante richieste restano nella finestra e attendendo quando sono esaurite: la seconda modalità evita il rifiuto invece di reagirvi.

I guasti transitori, cioè errori di rete, timeout e risposte di errore del servizio, non interrompono una cronologia a metà ma fanno riprovare con attesa raddoppiata fino a un tetto, e l'abbandono definitivo riferisce l'ultimo esito osservato invece di un messaggio generico.

Le discussioni e i post di forum sono canali con identificativo proprio e nelle community di sviluppo sono il posto dove sta la conoscenza: l'elenco dei canali li include interrogando l'endpoint dedicato, e la lettura funziona su un loro identificativo come su quello di un canale.

Il contenuto che non è testo, cioè i blocchi incorporati e la citazione del messaggio a cui una risposta si riferisce, entra nella resa e nei filtri: ignorarlo renderebbe vuoti messaggi che portano contenuto, e li farebbe scartare proprio dal filtro di lunghezza.

Il testo di terzi che apre con un cancelletto viene protetto, perché altrimenti forgerebbe un'intestazione e spezzerebbe la nota, con l'eccezione dei blocchi di codice recintati dove quel carattere appartiene al linguaggio.

La data del filtro viene verificata nella forma, perché una data scritta con le barre passerebbe senza errore e scarterebbe tutto o nulla: è il genere di filtro che sbaglia senza dirlo.

E la scrittura può aggiungersi in coda a un file esistente invece di sovrascriverlo, con l'intestazione scritta una volta sola; quando sovrascrive, avvisa.

## Collaudo

`--self-test` esercita l'intera logica contro un trasporto finto e non richiede credenziali: trentasette controlli, quattro dei quali negativi, cioè che fallirebbero se un presidio venisse rimosso. Il trasporto finto accetta un programma di risposte, cosicché un rifiuto o un guasto si possano collocare in una posizione precisa della sequenza e si verifichi non soltanto che la lettura riesca, ma quanto si è atteso e quante richieste sono state fatte.

`fetch-reddit.py` porta la propria suite con la stessa forma e lo stesso principio: ottantadue controlli contro un trasporto finto, dei quali tredici negativi. Il trasporto finto risponde da quattro tabelle, cioè post, alberi di commenti, collegamenti brevi e pagine esterne con i loro `robots.txt`, e questo permette di esercitare la parte che nessun servizio reale renderebbe riproducibile: un grafo con un ciclo, un tetto che si esaurisce a metà di un livello, un divieto di `robots.txt`, un rifiuto per eccesso di frequenza collocato in una posizione precisa della sequenza, e una ripresa che deve saltare ciò che è già fatto. Contro il servizio reale sono stati esercitati il recupero di un post, l'albero completo dei commenti, il lotto di più identificativi in una richiesta, la ricorsione su un post figlio e la forma della risposta di errore per un campo non selezionabile; restano non osservati il limite di frequenza sotto traffico prolungato e il tasso di fallimento sui domini esterni protetti.

Tre difetti sono emersi solo all'uso reale, e nessuno di essi sarebbe stato preso dalla suite: è il genere di errore che sopravvive a un collaudo verde, e per questo vale registrarli.

Il primo è di logica. Il campo dell'indirizzo di un post di testo contiene il permalink del post stesso, quindi seguirlo significa seguire sé stessi, e il confronto va fatto sulla chiave canonica e non sul prefisso della stringa perché le due forme dello stesso indirizzo differiscono per lo spezzone di titolo che una delle due porta dentro.

Gli altri due sono di scala, e si sono visti soltanto portando una corsa fino in fondo su un grafo di quasi settemila nodi. Il budget di sei tentativi con attesa crescente, che è giusto verso l'archivio perché quelle richieste sono la spina dorsale della corsa, su una pagina esterna che non risponde costa minuti, e con centinaia di collegamenti esterni quella somma domina la durata: le pagine esterne hanno quindi un budget proprio e molto più piccolo. E i due file di sintesi crescevano quanto il materiale che riassumono, cioè un indice da quasi tre megabyte e una mappa da quasi sette, che è il modo esatto in cui un Livello 1 smette di essere un Livello 1; oltre una soglia i catalogati si raggruppano per host e motivo, i non raggiunti si contano per motivo e per profondità, e l'elenco piano degli archi resta nel solo file destinato a un programma. Nella stessa occasione il materiale grezzo è passato a JSON compatto, che su un albero di commenti di un thread popolare dimezza il file senza togliergli un dato.

La lezione comune ai due difetti di scala è che un collaudo su un apparato piccolo non misura né i tempi né le dimensioni, e che entrambi hanno una soglia oltre la quale una scelta corretta diventa sbagliata.

Contro il servizio sono stati esercitati, su un progetto reale, l'elenco dei server, l'elenco dei canali e delle discussioni attive, la lettura della cronologia con il testo presente, i filtri, l'aggiunta in coda e il cursore. Restano non osservati sul servizio l'impaginazione oltre i cento messaggi, le due attese sui limiti di frequenza, la ripresa dopo un guasto e la lettura di una discussione popolata: tutto questo è provato contro il trasporto finto, e la distinzione fra i due stati è dichiarata nella nota di collaudo dentro il file e va conservata.

## Che cosa resta da rispettare comunque

La legittimità del token non esaurisce la questione, perché i messaggi di un canale sono scritti da altre persone e archiviarli sistematicamente tocca la loro privacy anche quando il canale è visibile a tutti i membri.

Quattro accorgimenti rendono la conservazione difendibile invece di soltanto dichiarata, e lo strumento ne attua il primo per costruzione. Si conserva l'identificativo dell'autore accanto al contenuto, perché senza di esso una richiesta di cancellazione mirata non è eseguibile e prometterla sarebbe una promessa vuota. Si tiene il materiale in un luogo unico, cosicché una cancellazione sia un'operazione e non una ricerca. Si elimina il materiale grezzo quando la sintesi con l'attribuzione lo ha reso superfluo, che è già la forma minima di limitazione della conservazione. E si richiedono i soli permessi necessari, perché domandarne di ampi per prudenza è il contrario della prudenza.

Se il server non è proprio, va inoltre considerato che la comunità ha diritto di sapere: una regola visibile nel canale, o la dichiarazione nella richiesta di invito, rende i tre accorgimenti precedenti verificabili dall'esterno invece che soltanto affermati.

## I tre strumenti di riduzione, e perché sono arrivati dopo

Questa sezione racconta una correzione, non una aggiunta, e conviene leggerla come tale perché la lezione di metodo vale più dei tre programmi. Fino alla revisione precedente questo README dichiarava mancanti due strumenti, il convertitore di un export di chat e il ripulitore dei sottotitoli di un video, e spiegava bene perché servissero. Esistevano già entrambi, scritti e usati per mesi dentro il progetto reale su cui il pacchetto è nato, e nessuno li aveva portati qui perché nessuno li aveva guardati: la dichiarazione di assenza era sincera e sbagliata insieme, che è la forma peggiore perché chi la legge smette di cercare.

`read-chat-export.py` riduce a Markdown l'export in JSON di un canale, e riconosce due formati dalla forma del documento e non dall'estensione: quello di DiscordChatExporter, con le chiavi che nominano il server e il canale, e quello ufficiale di Telegram Desktop, dove il testo di un messaggio può essere una stringa oppure una lista di frammenti con la formattazione, che lo strumento ricompone. Tiene autore, momento, testo, allegati e citazioni, e filtra per parola chiave, per intervallo di date e per lunghezza minima. Quest'ultimo filtro non è un vezzo: buona parte dei messaggi di un canale tecnico è fatta di conferme di una parola, che non sono citabili e occupano lo stesso spazio delle risposte.

`vtt-to-text.py` ricostruisce il parlato di un video dai sottotitoli automatici. Il problema che risolve non è la conversione ma la duplicazione: i sottotitoli a scorrimento ripetono quasi per intero il blocco precedente aggiungendo poche parole, così che a video il testo sembri salire, e convertirli ingenuamente produce un file tre o quattro volte più lungo del parlato con ogni frase ripetuta. La catena completa per una fonte video è quella che la regola sulle fonti prescrive, cioè scaricare i soli sottotitoli senza il video, ripulirli e conservarli accanto all'identificativo del video, perché una trascrizione da sola non dice da dove viene. Dove i sottotitoli non esistono serve il riconoscimento vocale, e nel catalogo dei pacchetti è `voicestudio`, che lo fa in locale.

`censimento-fonti.py` è il terzo, ed è quello che nessuno aveva previsto. Il lettore di Reddit produce un grafo, cioè nodi, archi e file grezzi sotto `_notes/` che git ignora; il registro delle fonti del progetto vuole invece righe curate, ciascuna con ciò su cui la fonte si può citare. Fra le due cose mancava un passo, e il passo è deterministico: normalizzare le cinque forme in cui lo stesso indirizzo compare, deduplicare, raggruppare, contare. La regola sull'economia del contesto prescrive esattamente questo, cioè che il lavoro meccanico stia in un programma e che all'LLM resti il solo salto semantico, che qui è decidere quanto una fonte sia affidabile e su che cosa la si possa citare.

Del raggruppamento vale dire da dove viene, perché è la scelta meno ovvia dello strumento: un post di raccolta ben scritto porta già la propria tassonomia sotto forma di intestazioni, e il programma la legge invece di imporne una. I cluster sono quindi quelli che l'autore della fonte ha scelto, il che li tiene confrontabili con la fonte e sfrutta una tassonomia scritta da chi conosce il dominio invece di una inventata da chi lo sta imparando. Ai collegamenti che compaiono nei commenti si assegna un cluster proprio, perché la distinzione fra ciò che l'autore ha organizzato e ciò che i lettori hanno aggiunto è essa stessa informazione.

Lo strumento riconosce come intestazione sia la riga interamente in grassetto che apre con un numero, che è la forma più frequente nei post di raccolta, sia l'intestazione Markdown vera. Accettarle entrambe costa due righe e copre un difetto che sarebbe silenzioso: su un post scritto con i cancelletti, senza la seconda forma, tutti i collegamenti finirebbero in un cluster solo, e un censimento con un cluster solo somiglia al censimento di un post non organizzato invece che a un difetto del lettore.

## Che cosa il lettore di Reddit ha imparato sul campo

Il terzo strumento è tornato dal progetto reale con tre correzioni che nessuna prova a tavolino avrebbe prodotto, e tutte e tre hanno la stessa forma: un difetto che non si manifesta come errore ma come una fonte in meno, silenziosamente.

La prima riguarda le radici dei certificati. Su una macchina reale l'archivio di sistema conteneva nove certificati scaduti, e fra questi una copia di ISRG Root X2 scaduta nel settembre 2025. I siti che si appoggiano a quell'autorità, che sono moltissimi, servono una catena che termina in X2 firmata da X1, la quale resta valida fino al 2035; ma la verifica, trovando X2 fra le radici di cui si fida, si ferma là e la dichiara scaduta invece di proseguire sul ramo firmato che è valido. L'effetto è che siti in piedi, e con essi centotrenta nodi di una corsa, risultano irraggiungibili a questo programma mentre rispondono a qualunque browser. Il rimedio è un archivio di radici corrente, che il pacchetto `certifi` fornisce; ciò che non si fa in nessun caso è disattivare la verifica, perché il difetto è nell'elenco di chi ci si fida e non nel fatto di fidarsi. Lo strumento usa `certifi` se lo trova e torna alle radici di sistema se non c'è, e una prova dedicata controlla che nell'archivio in uso non ci sia una radice ISRG scaduta.

La seconda riguarda il significato di un `robots.txt` che non risponde. La lettura prudente della specifica dice di trattare un servizio indisponibile come un divieto totale, e il lettore lo faceva; ma un divieto scritto è una proprietà del sito e vale finché il sito non cambia idea, mentre un `robots.txt` irraggiungibile è una proprietà dell'istante, e trattare i due allo stesso modo trasforma un guasto di pochi minuti in una esclusione permanente che nessuna ripresa ritenta, perché il nodo risulta deciso. Il secondo caso finisce quindi fra i pendenti con il proprio motivo, e l'opzione `--riprova-transitori` recupera le corse fatte prima che la distinzione esistesse. Il caso non è ipotetico: una corsa reale aveva catalogato per questa ragione centotrenta nodi su trentadue host, e il loro `robots.txt` consentiva esplicitamente le pagine che erano state escluse.

La terza riguarda l'estrazione dei collegamenti da una pagina esterna. Mancava una delle forme in cui un indirizzo compare, cioè il testo dell'ancora seguito dall'indirizzo fra parentesi tonde, che è precisamente quella che l'estrattore da HTML dello strumento produce da sé. L'assenza non si vedeva perché il numero dei collegamenti trovati restava plausibile: su una pagina enciclopedica reale ce ne sono sessanta in quella forma e l'estrazione ne trovava due, entrambi dall'intestazione che lo strumento stesso scrive. È il difetto tipico che una prova verde non coglie, perché un conteggio plausibile è indistinguibile da un conteggio giusto finché qualcuno non conta a mano.

Tutte e tre stanno nel collaudo dello strumento, che alla revisione attuale conta centodieci controlli contro un trasporto finto, senza rete.

## Che cosa manca a questo pacchetto

I due strumenti che questa sezione dichiarava mancanti non mancano più, e la sezione precedente racconta come e perché quella dichiarazione fosse sbagliata. Vale tenerne memoria qui invece di cancellarla: un pacchetto che dichiara un buco e poi lo colma resta leggibile, mentre uno che riscrive la propria storia perde la sola prova che il buco fosse stato visto.

Il terzo mancante era il lettore dell'API di Reddit a sole credenziali applicative, e non manca più, ma non è quello che era stato dichiarato: `fetch-reddit.py` non usa credenziali applicative perché quella via è risultata inaccessibile, e passa per un archivio pubblico di terze parti. La sostituzione va registrata invece che nascosta, perché le due vie non sono equivalenti: quella dichiarata avrebbe letto Reddit, questa legge una copia di Reddit, e la differenza è la latenza dell'indicizzazione e la sopravvivenza di ciò che è stato cancellato. Se un giorno la registrazione dell'applicazione dovesse riuscire, la via ufficiale resterebbe preferibile per fedeltà, e questo strumento resterebbe utile per ciò che l'API non dà, cioè il materiale più vecchio dei limiti di ricerca.

Vanno portati con il metodo usato per questi due, che vale registrare perché è la ragione per cui le copie non divergeranno: il file si copia e si sostituisce la sola prosa, con una tabella di sostituzioni esplicita, e la verifica è un confronto delle righe di codice dopo aver escluso commenti e stringhe di documentazione. Sul lettore hanno differito tredici righe su cinquecentocinquanta e nessuna di logica; sull'orchestratore sei righe di funzione, più la tabella dei canali che è stata deliberatamente sostituita da un esempio perché è conoscenza del progetto ospite e non codice riusabile.
