# Pacchetto opzionale: instradamento-modelli

> Mod di Claude Code che manda il lavoro meccanico su un modello più economico e misura, richiesta per richiesta, quanto costa ciascun modello. Vive dentro il template, si registra per account, e parte in un modo che non instrada niente finché la linea di partenza non è stata misurata.

<!-- readme-summary: il lavoro meccanico dei subagent su un modello più economico, impostabile per account, con la misura dei token per modello -->

## Cosa risolve

La regola `token-economy.md` porta una misura presa su un pilota reale e la enuncia come principio: lo stesso lotto, con lo stesso mandato, è costato centoventiduemila token per elemento con il modello generico a ragionamento medio e tredicimila con il modello economico a ragionamento basso, cioè un fattore nove, e il tempo è sceso nella stessa proporzione. Da lì discende la frase che il sistema ripete da allora, cioè che il modello si sceglie dal compito e non dalla sessione. Quella frase, finché non esiste questo pacchetto, è una buona intenzione: va ricordata, applicata a mano agente per agente, e nessuno si accorge quando smette di essere applicata.

Il pacchetto la rende un fatto della macchina. Quando un subagent sta per partire, un hook guarda il suo tipo in una tabella e, se quel tipo è lavoro meccanico, lo fa partire su un modello più economico e con lo sforzo di ragionamento che gli serve davvero. L'utente non deve ricordarsene, l'agente principale non deve chiederlo, e la decisione resta scritta in un file invece che nella memoria di qualcuno.

C'è una seconda cosa che risolve, e in ordine di importanza viene prima. Il settore «economia del contesto» del catalogo ha una regola sola, cioè che prima si misura la linea di partenza, perché senza di essa nessun guadagno dichiarato è verificabile. Fino a oggi quella misura veniva da `ccusage`, che legge i verbali a posteriori e riporta per sessione e per progetto. Questa mod misura dall'interno e con un'altra grana: somma i token di ogni singola richiesta, separandoli per modello, distinguendo ingresso, uscita, cache letta e cache scritta. È la misura che serve per decidere se un instradamento ha pagato, perché è presa sullo stesso asse su cui si instrada.

## Come funziona

Una mod è un plugin fatto di gestori di eventi che Claude Code chiama dentro il proprio processo, descritti in `https://code.claude.com/docs/en/plugins/mods/overview`. Questa ne registra sei, e ciascuno fa una cosa sola.

`agent.spawn` scatta quando un subagent sta per partire e può riscriverne il modello. È il punto in cui avviene l'instradamento vero, ed è anche il solo punto in cui si può intervenire senza toccare la conversazione principale. `turn.step` scatta prima di ogni richiesta al modello, una per turno più una per ogni giro di tool, e porta due cose: lo sforzo di ragionamento, che `agent.spawn` non espone e che qui si applica alle sole richieste del subagent instradato, e i conteggi di token che l'API riporta a richiesta conclusa. `turn.complete` e `session.end` riversano i conteggi nello store del plugin. `agent.offer` serve solo a sapere quali nomi di agente esistono davvero nella sessione. `session.start` legge la configurazione e registra il comando `/instradamento`.

I modi sono tre e il predefinito non instrada niente. In `osserva` la mod scrive in trascrizione che cosa instraderebbe e lascia correre: è il modo in cui si misura la linea di partenza e si controlla che la tabella nomini agenti che esistono. In `instrada` riscrive davvero. In `spento` non fa nulla, nemmeno la misura, ed è il modo con cui si esclude la mod da una sessione senza disinstallarla.

Quattro casi lasciano passare uno spawn intatto anche in modo `instrada`, e ciascuno per una ragione propria. Un fork eredita il contesto e il modello del genitore per definizione, quindi il campo verrebbe ignorato. Un modello già chiesto da chi apre il subagent è una decisione presa da chi ne sa più della tabella, e si rispetta salvo configurazione contraria. Un tipo di agente che la tabella non nomina non si tocca. E qualunque errore, di lettura o di configurazione, lascia passare la chiamata: una mod che instrada non è una guardia di sicurezza, e il suo guasto non deve mai fermare il lavoro. Questa scelta è dichiarata nel codice con un gestore di errore esplicito, perché `claude plugin validate` segnala come degna di nota ogni mod che possa trattenere uno spawn.

## La configurazione, che è per account

Il requisito che ha dato la forma al pacchetto è che ogni account locale sia impostabile per conto proprio. La mod sta quindi in un posto solo, dentro il template, e ciò che cambia da un account all'altro è il file di configurazione, che vive nella radice di quell'account.

La configurazione si compone leggendo due file, in quest'ordine. Il primo è `<CLAUDE_CONFIG_DIR>/instradamento-modelli.json`, cioè la radice dell'account corrente, che su questa macchina è `C:\Users\<utente>\.claude-account<N>` e su una installazione normale è `~/.claude`. Il secondo, facoltativo, è `.claude/instradamento-modelli.json` dentro il progetto aperto, e sovrascrive chiave per chiave quello di account: serve al caso in cui un progetto preciso voglia una tabella diversa, per esempio perché il suo lavoro meccanico ha un'altra forma. Se nessuno dei due esiste, la mod resta in `osserva` con la tabella vuota e non fa niente.

| Campo | Valore | Che cosa fa |
|---|---|---|
| `modo` | `spento`, `osserva`, `instrada` | Decide se la mod misura e se riscrive. Il predefinito è `osserva`, che misura e dichiara ma non riscrive |
| `agenti` | mappa da tipo di agente a regola | La tabella di instradamento. La regola si scrive in forma breve, `"Explore": "haiku"`, oppure estesa, `"Explore": { "modello": "haiku", "sforzo": "low" }` |
| `conversazione` | `{ "modello": ..., "sforzo": ... }` | Tocca la conversazione principale. Vuoto per scelta nel file di riferimento: vedi la sezione sui limiti prima di riempirlo |
| `rispettaModelloChiesto` | vero o falso | Se vero, e lo è di default, un modello chiesto esplicitamente da chi apre il subagent non viene riscritto |
| `annuncia` | vero o falso | Se vero, e lo è di default, ogni instradamento lascia una riga in trascrizione che Claude non legge |
| `promemoriaDopo` | un numero, 10 di default | Quante occasioni accumulate in modo `osserva` bastano perché la mod ricordi da sola che sta misurando e non instradando. Zero spegne il promemoria |

I valori del campo `modello` sono quelli che Claude Code accetta altrove, cioè un alias come `haiku`, `sonnet` o `opus`, oppure un identificativo completo. I valori dello sforzo sono `low`, `medium`, `high`, `xhigh` e `max`.

I nomi sotto `agenti` devono corrispondere esattamente ai tipi che la sessione offre, e un refuso qui non produce alcun errore: produce una regola che non scatta mai, cioè un risparmio che non arriva e nessuno sa perché. Per questo la mod tiene nota dei tipi che la sessione ha offerto davvero e `/instradamento` segna con una nota i nomi della tabella che non ha mai visto offrire.

## Installazione, una radice alla volta

L'installatore non copia la mod dentro le radici: vi scrive la configurazione di partenza e registra il percorso del template in `env.CLAUDE_CODE_PLUGIN_DIRS` dentro il `settings.json` di quella radice. Due copie della stessa mod divergerebbero in silenzio, che è il difetto che il resto del sistema esiste per evitare; una registrazione, invece, punta sempre alla versione che il template ha oggi.

Su Windows, da PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".claude/templates/instradamento-modelli/tools/installa-instradamento.ps1" -Verifica
powershell -NoProfile -ExecutionPolicy Bypass -File ".claude/templates/instradamento-modelli/tools/installa-instradamento.ps1" -Account 2
```

Su Linux o macOS:

```bash
bash .claude/templates/instradamento-modelli/tools/installa-instradamento.sh --verifica
bash .claude/templates/instradamento-modelli/tools/installa-instradamento.sh --account 2
```

Il primo comando è in sola lettura e dice, radice per radice, se la mod è registrata e in che modo si trova. Il secondo serve una radice sola; senza `-Account` le radici servite sono la 1, la 2 e la 3, e `-IncludiDefault` aggiunge la radice `.claude`. `-Forza` riscrive una configurazione già presente dalla copia di riferimento, `-Rimuovi` toglie la registrazione dal `settings.json` e lascia la configurazione sul disco, perché quella è lavoro dell'utente.

Al posto dei numeri di account si può nominare una radice per percorso, con `-Radice` e `--radice`, ripetibile: serve alle installazioni che non seguono la convenzione `.claude-account<N>` e alle prove, che non possono scrivere nella home vera.

La domanda che la verifica pone, cioè se quella cartella risulti registrata in quel `settings.json`, la risolve `merge-instradamento-settings.js` in modo `--stato`, che è di sola lettura e confronta percorsi risolti dopo `JSON.parse`. Per questo anche la verifica richiede Node, e lo dichiara invece di rispondere lo stesso. La ragione è un difetto osservato il 2026-10-12, il giorno dopo l'installazione: `-Verifica` rispondeva «NON registrata» per account1, account2 e account3 mentre la mod era attiva in tutti e tre e aveva già contato quarantatré richieste nel proprio store. Cercava il percorso nel testo grezzo del file, e dentro il JSON le barre rovesciate sono raddoppiate, quindi il percorso scritto con barre singole non si trovava mai. Il difetto non ha mai prodotto un errore: ha prodotto una risposta plausibile e sbagliata su una domanda a cui si ricorre proprio per non dover verificare, cioè il caso peggiore fra quelli che `chat-non-e-memoria.md` descrive a proposito dei registri di stato. La prova che lo copre sta in `tools/test-instradamento.py` e passa dall'installatore vero, non dal solo script di fusione, perché il difetto stava nel modo in cui la domanda veniva posta e non nella risposta.

La scrittura del `settings.json` passa da uno script Node, `merge-instradamento-settings.js`, per la stessa ragione per cui ci passa `agenti-terminale`: `ConvertFrom-Json` di PowerShell 5.1 tratta le chiavi JSON come indifferenti alle maiuscole e fallisce su file che ne contengano due che differiscono solo per quelle, mentre `JSON.parse` ha la semantica che Claude Code applica a quel file. Lo script valida il JSON prodotto, scrive su un temporaneo, lo rilegge da disco e solo allora sostituisce l'originale, e si rifiuta di toccare un file che non è riuscito a interpretare.

Una sessione già aperta non vede la mod appena registrata: si apre una sessione nuova oppure si lancia `/reload-plugins`. Che sia attiva lo dice `/plugin`, con una riga che conta le mod attive e le nomina.

## Che cosa si vede, e dove

Il modo `osserva` ha un difetto che si produce da sé: fa esattamente il suo mestiere, cioè niente, e chi lo installa se ne dimentica, così la misura raccolta non la guarda nessuno. Per questo la mod tiene il conto cumulato delle occasioni, cioè degli spawn che avrebbe instradato, e quando superano la soglia lo dice da sé all'avvio di ogni sessione, una riga sola, nominando il file da cambiare invece di dire genericamente di cambiarlo. Il promemoria tace appena il modo diventa `instrada`, perché a quel punto ha finito il suo lavoro, e si spegne del tutto mettendo `promemoriaDopo` a zero.

Il comando `/instradamento`, senza argomenti, scrive in trascrizione il modo corrente, i file di configurazione da cui è composto, la tabella con la nota sui nomi mai offerti, quanti spawn sono stati instradati su quanti proposti, i token di questa sessione per modello e quelli cumulati sulla macchina. Il resoconto esce come riga di diario e non come messaggio, quindi non entra nel contesto di Claude e non costa token a chi lo legge: è la stessa ragione per cui esiste il pacchetto.

Accanto ai token, dal 2026-10-12, il resoconto porta due numeri sullo sforzo di ragionamento, e vanno letti insieme perché il segnale sta nel loro rapporto: quanti spawn sono stati instradati con una regola di sforzo, e quante richieste quello sforzo lo hanno davvero ricevuto. Sotto, per ogni livello applicato, compare anche lo sforzo che la richiesta aveva in entrata, cioè quello che il motore aveva già deciso, perché una riscrittura che sostituisce un valore con se stesso non è un risparmio ed è bene vederlo. Se gli spawn crescono e le richieste restano a zero, la mod lo dichiara con una riga di attenzione invece di lasciare che si deduca da un numero che non c'è.

Quei due numeri esistono per una ragione precisa. Il modello riscritto si vede subito, perché compare una riga nuova nei conteggi; lo sforzo riscritto non si vede da nessuna parte, e fino a questa versione restava una cosa che le prove coprivano a livello di evento e che nessuno aveva osservato su una sessione vera. Ora il guasto, se c'è, ha un posto dove manifestarsi.

Gli argomenti del comando sono quattro. `instrada`, `osserva` e `spento` cambiano il modo per la sola sessione corrente e non toccano il file, che resta la verità durevole. `ricarica` rilegge i file di configurazione senza riavviare la sessione, ed è il modo con cui si prova una tabella nuova. `azzera` azzera i conteggi cumulati.

I conteggi cumulati vivono nello store del plugin, che è condiviso fra tutte le sessioni della macchina. Vale saperlo per due motivi: il totale che si legge comprende il lavoro di altre sessioni aperte nello stesso periodo, e due sessioni che riversano insieme possono perdere una parte dell'incremento, perché lo store non offre una lettura e scrittura atomica. È un libro mastro, non una contabilità: per il consumo fatturato resta `ccusage`, che legge i verbali.

## Che cosa non fa, e perché

Non riduce i token, riduce il costo dei token. È la stessa distinzione che `token-economy.md` fa a proposito del parallelismo, e vale ripeterla perché porta a diagnosi sbagliate: un lavoro instradato su un modello economico consuma all'incirca gli stessi token, e paga meno e prima. La misura a coppia del 2026-10-12, con lo stesso mandato dato a due subagent, dà 21 879 token su Haiku contro 21 235 su Opus, cioè uguali entro il tre per cento, e un costo di listino circa cinquanta volte minore.

Quanto valga su un piano in abbonamento è una domanda diversa, e la risposta onesta è che dipende da quale limite si sta toccando. Una versione precedente di questa sezione diceva che il guadagno si vede come lavoro che entra nella stessa finestra: la documentazione la smentisce, ed è stata corretta il 2026-10-12. La pagina degli errori di Claude Code dichiara che «i limiti di sessione e settimanale sono condivisi fra tutti i modelli, quindi cambiare modello non ripristina l'accesso», e quindi su quell'asse instradare non allarga niente. Accanto a quelli esistono però limiti per famiglia di modello, Opus e Sonnet, che «si applicano soltanto alle richieste di quella famiglia»: un subagent mandato su Haiku non consuma il limite di Opus, che resta disponibile per la conversazione principale, cioè per il lavoro che quel modello lo richiede davvero. È questo il guadagno in abbonamento, ed è reale ma circoscritto.

Resta un buco dichiarato, e va trattato come tale invece di essere colmato per ipotesi: nessuna pagina ufficiale dice a quale velocità ciascun modello consumi la finestra condivisa, né esiste un fattore pubblicato del tipo «Opus consuma N volte più in fretta». Le cifre che circolano su siti di terzi non sono ufficiali e si contraddicono. Chi vuole sapere se l'instradamento gli stia allungando la finestra lo misura con `/usage`, che sui piani in abbonamento attribuisce l'uso recente anche ai subagent, prima e dopo averlo acceso. Su un account a consumo, invece, il risparmio è diretto e si legge in fattura.

Non tocca la conversazione principale, se non glielo si chiede. Il campo `conversazione` esiste, e in un file di configurazione vuoto resta vuoto. La ragione è misurata altrove e vale la pena enunciarla: un modello economico che sbaglia un passo intermedio non costa il passo, costa tutto ciò che vi si appoggia dopo, e la conversazione principale è precisamente il posto dove ogni passo si appoggia al precedente. Il subagent, al contrario, ha un mandato chiuso e restituisce un risultato che l'agente principale rilegge. Cambiare il modello della conversazione a metà turno, inoltre, invalida la cache del prompt, quindi la richiesta successiva si ripaga per intero.

Non instrada verso modelli che non siano di Anthropic, e non è un gateway. Il lavoro aperto che il proprietario ha descritto il 2026-10-10, cioè collegare Claude Code a modelli gratuiti di terze parti, resta un pacchetto a sé: richiede un gateway locale, pone il vincolo assoluto di non far mai partire una fatturazione a consumo, e apre la questione di quali dati possano raggiungere un fornitore che addestra sui prompt. Questo pacchetto è la parte di quel disegno che si può avere subito senza nessuno di quei rischi, perché resta dentro l'abbonamento e dentro i modelli che la sessione già usa.

Non sostituisce la scelta umana per il singolo compito. Chi apre un subagent sapendo che quel compito richiede giudizio può continuare a chiedere il modello che vuole, e la mod lo rispetta.

## Fiducia, perché una mod non è in sandbox

Una mod è codice che gira dentro Claude Code con i permessi dell'utente: legge e scrive file, avvia processi, raggiunge la rete, vede ogni richiesta e ogni chiamata di tool, e la sandbox dei comandi di shell non la contiene. La documentazione ufficiale lo dice in apertura, e vale per questa come per qualunque altra. La contromisura non è la fiducia nell'autore ma l'ispezione, che `claude plugin validate` rende meccanica: elenca gli eventi gestiti e tutte le chiamate che la mod fa, senza eseguirla.

```powershell
claude plugin validate ".claude/templates/instradamento-modelli/mod"
```

Su questa mod l'elenco è quello che segue, ed è il perimetro intero: gli eventi `session.start`, `command.run`, `agent.offer`, `agent.spawn`, `turn.step`, `turn.complete` e `session.end`; le chiamate `$.command.register`, `$.env.get`, `$.fs.read`, `$.session.cwd`, `$.store.get`, `$.store.set` e `$.ui.log`; nessuna scrittura di variabili d'ambiente; le sole variabili lette sono `CLAUDE_CONFIG_DIR`, `HOME` e `USERPROFILE`. Non c'è `$.http.fetch`, non c'è `$.process.run`, non c'è `$.fs.write`: la mod non raggiunge la rete, non avvia processi e non scrive file, e un elenco diverso da questo in una versione futura è la domanda da porre a chi l'ha cambiata.

## Le prove, e che cosa misurano

Le prove della mod si eseguono con il collaudatore nativo, che fa partire gli eventi senza sessione, senza accesso e senza rete. Quelle dell'installatore sono in Python, perché la parte capace di fare danno non è la mod ma la scrittura dentro il `settings.json` di un account.

```powershell
claude plugin test ".claude/templates/instradamento-modelli/mod"
python .claude/templates/instradamento-modelli/tools/test-instradamento.py
```

```bash
claude plugin test .claude/templates/instradamento-modelli/mod
python3 .claude/templates/instradamento-modelli/tools/test-instradamento.py
```

Le quattordici prove della mod coprono un ramo di decisione ciascuna, perché un caso che ne esercita due non dice quale dei due lo tiene verde: instrada, osserva, modello chiesto dal chiamante, tipo assente dalla tabella, fork, sforzo applicato al solo subagent instradato, somma dei token per modello, nome di agente mai offerto, modo spento, configurazione illeggibile, e quattro sul promemoria, cioè le occasioni contate e riversate, la comparsa oltre la soglia, il silenzio in modo `instrada` e il silenzio sotto la soglia. Le sedici prove dell'installatore hanno tutte la forma «dopo l'operazione, che cosa c'è ancora che c'era prima», perché una fusione che perde una chiave di un `settings.json` costa all'utente la configurazione del suo account e il danno non si vede finché qualcos'altro non smette di funzionare per una ragione apparentemente diversa.

Misura del 2026-10-12, su questa macchina, con Claude Code 2.1.296: quattordici prove della mod verdi e sedici dell'installatore verdi. Otto mutazioni della mod, cioè guardia sul fork tolta, guardia sul modello chiesto tolta, modo `osserva` reso equivalente a `instrada`, riscrittura dello sforzo tolta, somma dei token tolta, promemoria cieco al modo, occasioni non riversate nello store e soglia del promemoria ignorata, fanno fallire ciascuna esattamente le prove che la coprono e nessun'altra. Due mutazioni dell'installatore, cioè le cartelle di plugin già registrate dimenticate e la deduplicazione tolta, fanno fallire rispettivamente due casi e uno.

## Quello che ancora non è misurato

Il risparmio sul campo non è misurato, e finché non lo è questo pacchetto va letto come codice scritto e provato con un effetto atteso, non come un guadagno ottenuto. La forma onesta, che `interaction-style.md` prescrive proprio per questo caso, è dire che cosa manca: serve una sessione reale che lavori in modo `osserva` per un periodo rappresentativo, un'annotazione dei conteggi per modello letti da `/instradamento`, lo stesso lavoro in modo `instrada`, e il confronto. Il primo numero da guardare non è il totale ma la quota di richieste che cambia modello: se gli spawn instradati sono pochi rispetto ai proposti, la tabella nomina agenti che quel progetto non usa, e il problema sta nella tabella e non nell'instradamento.

Resta da verificare sul campo anche che lo sforzo riscritto su `turn.step` arrivi davvero alle richieste di un subagent avviato in background, caso che le prove coprono sul piano degli eventi ma non su una sessione vera.
