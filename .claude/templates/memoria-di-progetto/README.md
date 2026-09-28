# memoria-di-progetto

Un controllo che segnala il lavoro atterrato nel repository senza lasciare traccia nella memoria di progetto. Estratto da un progetto istanziato da questo template il 2026-09-21, dopo che la regola corrispondente aveva dovuto essere richiamata più volte dallo stakeholder.

## Il problema, e perché non si risolve scrivendo meglio la regola

Quasi ogni progetto che adotta questo sistema arriva a una regola della forma "si documenta mentre si fa, non dopo". È una regola giusta e ha un difetto strutturale: **dipende interamente dalla memoria di chi esegue**, e quindi fallisce esattamente quando serve, cioè nelle sessioni lunghe in cui si è concentrati su altro.

Il sintomo che la regola non basta è preciso e riconoscibile: qualcuno deve ripeterla. Nel progetto di origine è stata scritta una volta, riaffermata in forma enfatica, e richiamata ancora dopo alcuni giorni. A quel punto la conclusione non è che vada scritta più forte, ma che **una direttiva che va ripetuta resta una speranza finché non ha un presidio**.

È la stessa conclusione già tratta due volte nello stesso progetto per ragioni diverse: su uno strumento tipografico che aveva rotto una compilazione, dove il presidio è diventato una guardia nel codice invece della prudenza di chi lanciava; e sulle prove, dove la domanda "questa prova cadrebbe se il difetto tornasse" è diventata un passo obbligato invece di un'intenzione.

## Che cosa controlla

**Commit senza voce di registro.** Ogni commit ha una data, il registro ha voci datate. Se esistono commit più recenti dell'ultima voce, quel lavoro non è tracciato. La severità dipende da che cosa quei commit hanno toccato: codice sorgente senza una voce è un difetto, sola documentazione è un avviso, perché spesso la documentazione è essa stessa la voce.

**Voci chiuse senza data.** Una voce di un registro di pendenti marcata come fatta deve dire quando. Una chiusura senza data è una fotografia senza scatto: non si può né verificare né collocare.

**Voci senza l'elenco di ciò che hanno toccato.** Una voce che non dichiara su che cosa ha agito costringe chi legge a ricostruirlo dal diff, che è precisamente il lavoro che la voce dovrebbe risparmiare. Il controllo si applica solo dalle voci successive a una data di adozione, perché imporre una regola al passato produce solo rumore.

## Che cosa NON controlla, e va detto

Non verifica che una voce sia **buona**, né che dica il perché invece del solo cosa. Quella è una proprietà di contenuto e nessun controllo meccanico la raggiunge.

Lo strumento distingue **il silenzio dalla presenza**, che è meno di quanto servirebbe e molto più di niente. Credere che copra più di quanto copre sarebbe peggio che non averlo, perché produrrebbe fiducia in una copertura inesistente.

## Come si adotta

Si copia `tools/lint-memoria.py` nel progetto e si adattano le tre costanti in testa al file: il percorso del registro cronologico, il percorso del registro dei pendenti, e la data da cui la dichiarazione dei file toccati diventa obbligatoria.

Poi, e questa è la parte che conta più dello strumento, si aggancia alla regola che presidia: la direttiva sul tracciamento dichiara esplicitamente che il controllo va eseguito **prima di consegnare i comandi di version control**, insieme agli altri controlli documentali. **Un controllo che esiste e che nessun documento nomina non viene eseguito**, ed è lo stesso motivo per cui una regola che nessun documento cita non viene caricata.

## Quando offrirlo

Al gate, insieme agli altri pacchetti, in qualunque progetto che tenga un registro cronologico del lavoro. Non ha senso dove quel registro non esiste, e in quel caso la domanda precedente è se serva.
