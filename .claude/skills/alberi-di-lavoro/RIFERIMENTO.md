# Più alberi di lavoro: ambienti separati, memoria unica

> Riferimento normativo della skill `alberi-di-lavoro`, che lo carica quando un progetto usa più di un albero di lavoro, cioè più cartelle agganciate allo stesso repository con `git worktree`, per esempio per tenere separati un ambiente di produzione, uno di test e il lavoro su una funzionalità. Gli alberi di lavoro sono la forma L2 del catalogo `skills/separazione-ambienti/RIFERIMENTO.md`, cioè una delle scelte sull'asse che riguarda come stanno i sorgenti sulla macchina di chi sviluppa, non il modo di sviluppare né un modo di separare test e produzione da solo: si adottano quando quel gate li sceglie, e questa regola ne governa le conseguenze. Nasce da un caso osservato il 2026-09-23 in un progetto istanziato da questo template, ed è generale: vale per qualunque progetto che versioni la memoria dell'agente dentro il repository e apra più di un albero.

## Il modello: un albero per ambiente

Il modello si sceglie al gate della separazione degli ambienti, e ha senso quando i diversi stati del progetto devono girare insieme sulla stessa macchina, ciascuno con il proprio server di sviluppo o la propria anteprima. Dove la separazione vive altrove, in macchine distinte, in progetti di hosting distinti o in configurazioni dello stesso albero, un albero solo basta e questa regola non si carica. Un albero di lavoro in più non è una copia del repository ma una seconda cartella che condivide con la prima la stessa base di oggetti git e porta in uscita una branch diversa. È il modo meno costoso di tenere aperti insieme due o più stati del progetto senza cambiare branch avanti e indietro nella stessa cartella: la branch di produzione resta in uscita in un albero che non si tocca mentre si lavora, quella di test o di staging in un secondo, e una funzionalità in corso in un terzo. Ciascun albero ha il proprio ambiente materializzato, cioè dipendenze installate, file `.env`, porta del server di sviluppo ed eventuale base dati locale, e questa separazione è precisamente ciò che si vuole: un server di test che gira sulla porta di quello di produzione, o che scrive sulla stessa base dati, annulla la ragione per cui gli alberi sono due.

La forma è la seguente, documentata in entrambe le sintassi perché il lettore non è noto. Si crea un albero accanto a quello principale, mai dentro, perché una cartella di lavoro annidata in un'altra finisce nel suo `git status` come contenuto non tracciato.

```powershell
git worktree add "../<progetto>-staging" staging
git worktree add -b "<feature>" "../<progetto>-<feature>" staging
git worktree list
```

```bash
git worktree add "../<progetto>-staging" staging
git worktree add -b "<feature>" "../<progetto>-<feature>" staging
git worktree list
```

Tre vincoli di git vanno conosciuti prima di pianificare gli alberi, perché nessuno dei tre si scopre leggendo il comando. Una branch può stare in uscita in un solo albero alla volta, quindi due sessioni non lavorano mai sulla stessa branch da due cartelle. Ciò che è ignorato da git non passa da un albero all'altro, quindi `_notes/`, `CLAUDE.local.md`, `settings.local.json`, `.env` e l'ambiente materializzato vanno ricreati in ogni albero nuovo, e il bootstrap della sezione 13 di `PROJECT-SYSTEM.md` va eseguito in ciascuno. E un albero si rimuove con `git worktree remove`, non cancellando la cartella, altrimenti git continua a considerare in uscita la sua branch finché non si esegue `git worktree prune`.

La tabella degli alberi vive nella scheda `context/deployment.md`, con percorso, branch, ambiente che rappresenta, porta, e l'indicazione di quale sia l'albero autorevole per la memoria, di cui si dice sotto. Serve a rispondere in un colpo alla domanda "dove sto lavorando", che con più alberi smette di avere una risposta ovvia.

## Il tranello: la memoria versionata descrive la branch, non il progetto

Un sistema che versiona la memoria dell'agente dentro il repository ottiene una proprietà preziosa, cioè che la memoria viaggi con il codice e che un clone la veda. Ma da quel momento la memoria non descrive più lo stato del progetto: descrive lo stato della branch su cui è scritta, e chi apre un albero su una branch indietro riceve una fotografia vecchia che ha tutta l'aria di essere quella giusta.

Non è un difetto da correggere, ed è utile riconoscerlo subito perché toglie la tentazione di cercare una soluzione che non esiste. Le due proprietà sono la stessa guardata da due lati: la memoria sta nel repository perché sia riproducibile, revisionabile in una pull request e presente in un clone, e tutto ciò che sta nel repository è soggetto al versionamento, che è esattamente il meccanismo che fa convivere stati diversi su branch diverse. La memoria eredita la semantica del codice, cioè vale per la branch, mentre chi la legge le attribuisce la semantica del progetto, cioè vale e basta. Finché l'albero è uno solo lo scarto non si vede; il giorno in cui si apre il secondo, il progetto ha due memorie senza che nessuno lo abbia deciso.

Il caso che ha prodotto questa regola lo misura. Tre alberi sulla stessa macchina: la vetrina su `staging`, il lavoro grafico su una branch tematica con otto giorni di commit non ancora fusi, e un terzo albero aperto quel giorno per una funzionalità indipendente, nato da `staging` perché il suo lavoro non dipendeva da quello grafico. Il terzo albero ha ricevuto uno snapshot ancorato a un commit vecchio di otto giorni e un registro con sedici decisioni contro le trentadue realmente prese. Mancavano, fra le altre, la decisione che istituiva il modello a più alberi, quindi una sessione aperta lì non avrebbe saputo di non essere sola; quella su come promuovere il lavoro grafico, quindi avrebbe potuto toccare file che un'altra sessione stava riscrivendo; e tutte le decisioni di schema del periodo, cioè la forma reale della base dati su cui avrebbe lavorato.

Il fallimento è silenzioso e ben formato. Un file mancante produce un errore; qui il file c'è, si apre, ha la forma giusta, prosa coerente, una tabella completa e una data coerente con il commit che dichiara. È semplicemente la verità di un'altra branch. E colpisce chi segue le istruzioni, non chi le ignora, perché la procedura di ripresa prescrive giustamente di leggere la memoria per prima. Un'aggravante si vede solo dove la memoria è scritta bene: più è densa e sicura di sé, più è convincente da vecchia, perché una memoria fatta di frasi caute verrebbe verificata e una fatta di affermazioni precise viene creduta.

## La diagnosi, che costa dieci secondi

Entrando in un albero, prima di leggere qualunque scheda, si confronta lo stato dichiarato dalla memoria con quello osservabile del repository e degli altri alberi. Lo fa `tools/verifica-ripresa.py`, che dalla sua prima riga di esito segnala ogni altro albero la cui branch porti modifiche a `.claude/memory/` che questo albero non ha, oppure modifiche non committate alla memoria, e nomina il percorso della memoria più avanti. Dove lo strumento non è istanziato, la stessa domanda si pone a mano.

```
git worktree list
git log --oneline -1
git diff --stat HEAD...<branch dell'altro albero> -- .claude/memory
```

La terza riga è quella che decide: la notazione a tre punti mostra ciò che l'altra branch ha cambiato nella memoria dal punto in cui le due si sono separate, cioè esattamente ciò che la memoria di questo albero non contiene. Se l'uscita non è vuota, la memoria di questo albero non è quella del progetto e va trattata come tale.

## La regola, e le due correzioni sbagliate

La memoria si legge dall'albero autorevole, per percorso assoluto, e non si copia né si fonde negli altri.

Copiarla è sbagliato perché crea due memorie divergenti: da quel momento ogni aggiornamento va fatto due volte o riconciliato a mano, e la riconciliazione manuale della memoria è precisamente il lavoro che un sistema di memoria esiste per eliminare. Fonderla è sbagliato per una ragione meno ovvia: porterebbe nella branch nuova commit che non le appartengono, cioè la storia di un altro lavoro, e ne sporcherebbe la pull request, che invece di mostrare l'aggiunta di una funzionalità mostrerebbe anche otto giorni di lavoro grafico altrui.

L'albero autorevole è quello della branch più avanti, cioè quella che contiene il lavoro che le altre non hanno ancora ricevuto, e può essere tanto il più vecchio quanto uno in cui nessuno sta lavorando. Con tre alberi la domanda non ha una risposta ovvia, ed è per questo che la risposta si scrive nella tabella degli alberi invece di lasciarla dedurre. Ne segue anche dove si scrive la memoria nuova: una decisione presa lavorando in un albero secondario si registra nella memoria dell'albero autorevole, per percorso assoluto, e arriva agli altri alberi per la via ordinaria, cioè quando le branch si fondono.

## Dove va l'avviso, in ordine di costo crescente

La prima contromisura copre da sola la maggior parte del rischio. Il file di ripresa `_notes/RESUME-PROMPT.md` di ogni albero che non sia quello autorevole si apre, prima di ogni altra cosa, con l'avviso e con il percorso assoluto della memoria valida. Il file di ripresa è privato e non versionato, quindi è il solo posto che non eredita il tranello che descrive: ogni albero ha il proprio, e nessuna fusione lo sovrascrive.

La seconda è la tabella degli alberi nella scheda `context/deployment.md`, descritta sopra, con la regola della memoria accanto.

La terza insegna la propria cecità al motore di riconciliazione. Un motore che confronta commit dichiara allineato ciò che non sa vedere, e le sue due cecità fanno parte del contratto: non vede il lavoro non committato, e non vede che la propria memoria appartenga a un'altra branch. La prima è già stata pagata in un progetto istanziato, con una settimana in cui il motore dichiarava tutto allineato mentre novanta file non committati dicevano altro. La skill `sync-context` le dichiara entrambe e apre il proprio rapporto con `git status` e `git worktree list`, e `verifica-ripresa.py` le trasforma in un avviso all'apertura della sessione.

## La generalizzazione: un documento di stato dichiara in testa a quale commit e branch si riferisce

Il tranello non riguarda la memoria in quanto memoria, ma ogni documento versionato che descriva lo stato presente invece di una regola. Uno snapshot, un registro di decisioni, una scheda di lavoro in corso, una roadmap e un work-log rispondono tutti alla domanda "a che punto siamo", che ha una risposta diversa per branch. I documenti che descrivono regole degradano molto meglio, in proporzione alla lentezza con cui cambiano: un file di istruzioni vecchio di una settimana è quasi sempre ancora vero, uno snapshot vecchio di una settimana è quasi sempre già falso. Non sono esenti, sono meno esposti, e la prudenza giusta è proporzionata e non uniforme.

Ne discende una regola di redazione che vale anche con un albero solo: un documento di stato dichiara sempre a quale commit e a quale branch si riferisce, e lo dichiara in testa e non in fondo. Le schede di `context/` lo fanno con il frontmatter di riconciliazione, lo snapshot `memory/index.md` con il blocco di stato che apre il file. La dichiarazione permette a chi legge di accorgersi in due secondi che sta leggendo la verità di un'altra branch, senza dover sapere in anticipo che il tranello esiste.
