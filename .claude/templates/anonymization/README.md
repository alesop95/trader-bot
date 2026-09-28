# Pacchetto opzionale: anonymization

> Guard-rail che passa i file del repository in cerca di *dati che identificano* persone, luoghi e infrastrutture reali, e che non devono finire in un file pubblicabile: indirizzi IP, indirizzi fisici di apparati, nomi propri, caselle di posta personali, numeri di telefono, importi, IBAN, partite IVA. È l'attuazione meccanica della regola `rules/anonymization.md` di questo pacchetto, che va istanziata insieme allo strumento perché è il criterio, e lo strumento da solo non decide nulla.

## Il problema, e perché non è il problema dei segreti

Uno scanner di credenziali cerca stringhe con una *forma* riconoscibile: una chiave AWS comincia per `AKIA`, un blocco di chiave privata ha un'intestazione, un token di un servizio ha una lunghezza e un alfabeto noti. È il mestiere di `hooks-starter/hooks/secret-scan`, e funziona proprio perché la forma è universale.

I dati che identificano non hanno quella proprietà. Un indirizzo privato qualunque è indistinguibile da un segnaposto se non si sa quale blocco usa davvero il soggetto documentato, e questo README non ne scrive nessuno di esempio proprio per non contraddire la regola che accompagna: un esempio concreto in un documento pubblicabile è il primo posto in cui una mappatura trapela. Un cognome è un cognome solo se è di qualcuno. Un importo è un dato commerciale in un documento contrattuale e un numero innocuo in una tabella di capacità. Ne discende la conseguenza architetturale su cui poggia tutto questo pacchetto: l'elenco di ciò che va cercato è specifico del progetto e non può vivere nello strumento, che invece è tracciato e finisce in pubblico insieme al resto.

La separazione è quindi netta e non negoziabile. Lo strumento è pubblicabile e non contiene nessun valore reale; ciò che cerca vive in un file di pattern nel layer privato del progetto, accanto alla mappa dei segnaposto, ignorato da git. Se quel file manca lo strumento si ferma e lo dichiara, invece di stampare un verde che non ha calcolato, perché un controllo che non trova nulla perché non sta cercando nulla è peggio dell'assenza del controllo.

## Perché la buona volontà non basta, in un numero

Nel progetto in cui questo strumento è nato la regola scritta esisteva da settimane quando è stato eseguito il primo audit. Ha trovato centoquarantotto riscontri su ottantanove file tracciati, di cui una trentina erano valori reali veri: indirizzi cablati dentro tre script, indirizzi fisici di apparati dentro due script di scrittura, indirizzi pubblici di macchine virtuali, caselle di posta personali di dipendenti e di referenti esterni, importi contrattuali.

Il riscontro peggiore non era nessuno di questi. Era una voce di registro operativo che pubblicava la corrispondenza fra un segnaposto e la persona reale, cioè il dato che rende reversibile ogni altra anonimizzazione del progetto. Un accoppiamento pubblicato vale più di cento valori nascosti.

Il fatto che governa l'uso dello strumento è però un altro, e va letto due volte: nessuno di quei residui era stato introdotto di proposito, e nessuno apparteneva alla sessione che li ha scoperti. Un residuo non si introduce, si eredita. Restare puliti sui propri file non dice niente sul repository, ed è la ragione per cui il controllo si fa sull'intero perimetro e non sul diff.

## Il perimetro, che è la parte in cui è facile sbagliare

Il perimetro predefinito è ciò che sta per essere pubblicato: i file tracciati più quelli non tracciati e non ignorati, cioè i candidati al prossimo commit. Entrambi i gruppi sono bloccanti, perché entrambi finiscono in pubblico, e quelli del secondo gruppo sono marcati a video con un avviso esplicito.

Questa definizione è il frutto di una correzione, e conviene conoscerla perché la scelta naturale è quella sbagliata. La prima versione dello strumento passava `git ls-files`, cioè i soli file *tracciati*: sembra la definizione ovvia di "ciò che è nel repository", e lascia fuori esattamente il caso peggiore, cioè il file nuovo appena scritto e non ancora aggiunto all'indice, che è invisibile al controllo proprio nel momento in cui serve guardarlo. Nel progetto di origine tre file nuovi sono passati puliti per fortuna e non per verifica, e il difetto è emerso per caso qualche giorno dopo.

Con `--tutti` entrano anche i file *ignorati*, cioè il layer narrativo locale e gli output degli strumenti. Quei file contengono valori reali per costruzione: è il motivo per cui git li ignora. I loro riscontri sono elencati a parte, aggregati per file, e *non sono bloccanti*. Il numero spiega perché: nel progetto di origine sono 10.844 riscontri su centonovantuno file ignorati, contro *zero* bloccanti nel perimetro pubblico, e fra i file più densi c'è la mappa dei segnaposto, che per definizione contiene tutti i valori reali del progetto. Se quei riscontri fossero bloccanti, il controllo fallirebbe per il solo fatto di esistere, e un controllo che fallisce sempre smette di essere letto in due settimane.

La proprietà che ne discende è quella per cui il perimetro resta corretto senza manutenzione: un percorso del layer privato diventa bloccante nell'istante in cui viene tracciato, e compare fra i primi con la marca di file non tracciato. Il controllo cambia da solo la propria valutazione quando cambia lo stato del file, e nessuno deve ricordarsi di aggiornare una lista di esclusioni.

## Rapporto con `hooks-starter/secret-scan`, che non sostituisce e non è sostituito

I due si usano insieme e coprono categorie diverse: uno cerca credenziali per forma, l'altro dati identificanti per valore. Vale però notare una differenza di *perimetro* che li rende complementari anche su questo asse, e che è utile avere chiara.

`secret-scan` è un hook `PreToolUse` che guarda `git diff --cached`, cioè il solo diff in stage, e blocca il commit. È la scelta giusta per il suo compito, perché un segreto lo si introduce e va fermato quando lo si introduce. Ha però la conseguenza che un residuo *ereditato* gli è invisibile: se un valore era già nel repository prima che l'hook esistesse, nessun commit successivo lo porta più in stage. Questo pacchetto copre l'altra metà, perché passa il perimetro intero a ogni esecuzione e trova ciò che c'era prima.

Chi adotta entrambi tenga presente anche il caveat che `secret-scan` dichiara di suo: i commit *manuali* dell'utente non passano da un hook `PreToolUse`, che intercetta le azioni dell'agente. Per coprirli serve un hook nativo di git via `core.hooksPath`, ed è il posto in cui conviene registrare anche il controllo di questo pacchetto se il progetto vuole una difesa che non dipenda da chi si ricorda di lanciarlo.

## Cosa istanzia, e dove

Nel progetto vanno tre cose, e la terza è quella che si dimentica.

Lo strumento `tools/Test-Anonymization.py` va in `tools/`, oppure in `scripts/` se il progetto usa quella convenzione. La regola `rules/anonymization.md` va in `.claude/rules/anonymization.md`, sostituendo i segnaposto tra parentesi angolari, e va dichiarata fra le regole da caricare sempre nel `CLAUDE.md` del progetto: senza il criterio, lo strumento è un elenco di riscontri che nessuno sa come giudicare.

Il terzo file è quello che non si versiona. Si copia `patterns.example.json` nel layer privato del progetto, per default `_notes/.anonymization-patterns.json`, e si sostituisce ogni valore con quelli veri. Va verificato che il percorso sia effettivamente ignorato da git prima di scrivervi dentro il primo valore reale, e non dopo: è l'unico passo dell'istanziazione in cui un errore si paga con la storia git.

Accanto ad esso conviene creare subito, sempre nel layer privato, la mappa dei segnaposto `.anonymization-map.md` e il file di sostituzioni per l'eventuale futura pulizia della storia. Nessuno dei tre è facoltativo nella pratica: la mappa serve a chi deve tradurre i segnaposto per operare davvero, e il file di sostituzioni si accumula mano a mano perché ricostruirlo a posteriori significa rifare il lavoro due volte.

## Quando offrirlo

Quando il repository è pubblico, o è condiviso più largamente di chi lo scrive, e la materia documentata appartiene a qualcun altro: infrastruttura aziendale o di un cliente, apparati, persone. Le due condizioni valgono insieme, e la regola le discute in apertura.

Non si propone per un repository che documenta soltanto codice proprio: là non c'è nulla da anonimizzare e lo strumento produrrebbe solo falsi positivi. Si propone invece anche per un repository *privato* che documenta l'infrastruttura di un cliente, perché la cerchia di chi vi accede cambia nel tempo mentre la storia git no.

## Portabilità

Lo strumento è eseguibile da *qualunque cartella* e su Windows come su Linux: risale alla radice del repository dalla posizione del proprio file, cercando `.git` sia come cartella sia come file perché in un worktree o in un sottomodulo è un file che punta altrove. Non dipende dalla cartella corrente, e la ragione è che la cartella corrente dipende da chi invoca: una sessione interattiva, un hook, un'attività pianificata e un altro script sono quattro cartelle diverse per lo stesso comando. La prima versione si rifiutava di partire se non la si lanciava dalla radice, che è precisamente il vincolo che rende uno strumento inutilizzabile dentro un'automazione.

Due parametri coprono i casi in cui la risalita non basti: `--radice` fissa la radice a mano, e `--patterns` punta a un layer privato organizzato diversamente da `_notes/`.

I domini riservati alla documentazione da RFC 2606, cioè `example.com`, `.org`, `.net`, `.edu` e il TLD `.example`, sono ammessi per costruzione come lo sono i blocchi di indirizzi di RFC 5737: non esistono e non possono appartenere a nessuno, quindi una casella su di essi è un esempio e non il dato di una persona. Senza questa simmetria ogni documento che usa un indirizzo di esempio produce un riscontro bloccante, e chi scrive documentazione impara a ignorare l'esito del controllo, che è il modo in cui un guard-rail muore.

## Requisiti e stato

Python 3, zero dipendenze. Lo strumento non apre connessioni, non usa credenziali e non scrive nulla: legge file e stampa. Codici di uscita 0 se non ci sono riscontri bloccanti, 1 se ce ne sono, 2 se il file dei pattern manca o non ha le chiavi obbligatorie, cioè se il controllo non è giudicabile.

Originale al template, estratto da un progetto reale di documentazione di rete dove gira da settembre 2026. Validato là su centoquindici file nel perimetro pubblico e su trecentosei con il layer privato incluso. Il file dei pattern del progetto di origine porta cinquantanove nomi propri, ventisei prefissi di rete reali e ventiquattro caselle ammesse, che è l'ordine di grandezza da aspettarsi dopo qualche mese di lavoro e non al primo giorno: la lista si costruisce mano a mano che si anonimizza, non in anticipo.

Due limiti dichiarati, entrambi umani e nessuno risolvibile con più codice. Lo strumento non distingue un falso positivo da una fuga quando il valore è ambiguo, per esempio un numero di versione che somiglia a un indirizzo, e per questo tiene una categoria non bloccante che va guardata a mano. E non conosce il contesto: un nome dentro una ragione sociale legale è ammesso, lo stesso nome in una frase narrativa no, e la lista delle eccezioni di contesto va tenuta corta perché più è lunga meno il controllo dice.
