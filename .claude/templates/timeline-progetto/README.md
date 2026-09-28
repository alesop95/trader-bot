# timeline-progetto

> Pacchetto opzionale del sistema di progetto. Tiene una linea temporale sempre aggiornata di tutto ciò che è stato fatto, un microstep per voce, con accanto la ragione tecnologica adottata per quel passo. La linea temporale non si scrive: si genera dai registri che il progetto già tiene, e vive interamente dentro il repository.

## Che problema risolve

Un progetto lungo accumula centinaia di microstep, e di ciascuno restano due cose che vivono separate. Il fatto sta nel work-log e nei commit: che cosa è stato fatto, quando, su quali file. La ragione per cui quel fatto è stato fatto così e non altrimenti sta nel registro delle decisioni, oppure da nessuna parte.

Le due cose non si leggono insieme, quindi in pratica non si leggono. Per sapere perché a marzo si è scelta una certa tecnologia bisogna incrociare a mano un work-log scritto in ordine cronologico inverso con un registro numerato che non segue le stesse date, e nessuno lo fa se non è costretto. Il risultato è che la storia tecnica del progetto esiste su disco ed è illeggibile, che dal punto di vista di chi deve decidere il prossimo passo equivale a non esserci.

Questo pacchetto le mette in una linea sola, leggibile dall'inizio alla fine, dove ogni passo porta accanto il proprio perché.

## Il vincolo che governa tutto: l'artefatto è del progetto

La linea temporale e tutto ciò da cui deriva vivono dentro la cartella del progetto, tracciati da git se il progetto lo vuole. Nulla viene scritto nella directory di configurazione dell'account Claude, nella memoria automatica nativa o in qualunque magazzino fuori dal repository.

Non è una preferenza ma il principio della sezione sull'auto-memory dello standard, applicato al caso in cui è più facile dimenticarlo: tutto ciò che persiste deve vivere dentro la cartella di progetto ed essere recuperabile da un clone. Una cronologia del progetto che vivesse nell'account sarebbe invisibile a chiunque altro, non entrerebbe in nessun clone, e sparirebbe con il primo wipe del magazzino nascosto, che è il modo peggiore di perdere proprio la cosa che serviva a ricordare.

## Che cosa istanzia

Un file, `tools/costruisci-timeline.py`, da copiare in `tools/` del progetto ospite. Python 3, sola libreria standard, nessun segnaposto da sostituire. Produce un file HTML unico e autosufficiente, per difetto `docs/TIMELINE.html`, che non chiama la rete e si apre da solo.

Una voce di permesso, come per gli altri pacchetti che portano strumenti.

```
Bash(python tools/costruisci-timeline.py:*)
```

## Da dove legge, e come si aggancia una ragione a un passo

Legge due registri, perché un progetto può tenere i propri microstep in entrambi. Il work-log `.claude/memory/progress.md` dà il passo con la sua data, i file toccati e il motivo. Il registro operativo `docs/OPERATIONS-LOG.md`, quando il pacchetto `operations-log` è attivo, dà il microstep numerato con il perimetro, il legame con lo scopo del progetto e l'esito verificato; leggere il solo work-log su un progetto che ha anche quel registro mostrerebbe meno di quanto il progetto sa di sé, e il difetto sarebbe invisibile perché il documento prodotto resterebbe plausibile. A entrambi si somma il registro delle decisioni `.claude/memory/decisions.md`, che dà la ragione tecnologica per esteso quando un passo ne cita una voce. Non aggiunge informazione: la raccoglie. La regola del sistema è che ciò che si può derivare non si scrive, e questo è il caso da manuale, perché una linea temporale tenuta a mano diverge dal work-log entro la settimana e diventa una seconda fonte di verità di cui nessuno sa più quale sia quella buona.

L'aggancio fra un microstep e la sua ragione non si indovina, si dichiara, e le forme coprono casi diversi. Nel registro operativo la ragione è il campo che dichiara il legame con lo scopo del progetto, cioè a quale fase serve quell'intervento e che cosa ne dipende: è la forma più propria, perché è precisamente la domanda a cui una linea temporale deve rispondere. Nel work-log le forme sono due. Una voce di work-log che nomina una decisione, per esempio `ADR-007`, eredita la motivazione di quella decisione: è la forma giusta quando la scelta è architetturale e vive di vita propria. Una voce che porta un campo `Ratio:` dichiara la ragione sul posto: è la forma giusta quando la scelta tecnologica non merita una decisione architetturale ma non è nemmeno ovvia, che è il caso della maggioranza dei microstep.

```
## 2026-03-01 - Separato il calcolo dalla resa

Commit: aaa1111 Area: architettura File toccati: src/uno.py Motivo: separare il calcolo dalla resa. Ratio: la resa cambia ogni mese e il calcolo no, quindi separarli rende stabile il pezzo che non deve muoversi.
```

Il campo `Area:` classifica il passo e serve alla leggibilità della linea: architettura, dati, interfaccia, sicurezza, infrastruttura, documentazione, prove. Dove non è dichiarato il passo resta classificato come altro, il che è corretto e non è un difetto.

## Il microstep senza perché, che è la segnalazione più utile

Un passo senza né una decisione citata né un campo `Ratio:` finisce nella linea temporale con la ragione dichiarata mancante, in evidenza. Non si inventa una ragione plausibile, e la differenza è tutta qui: un perché dedotto a posteriori da chi non c'era ha l'aspetto di una spiegazione e il valore di un'ipotesi, e una volta scritto nessuno lo distinguerà più da quelli veri.

```
python tools/costruisci-timeline.py --senza-ragione
```

Elenca i soli passi scoperti ed esce con codice diverso da zero se ce n'è almeno uno, quindi si può mettere in un controllo prima di un commit. È la forma che rende operativa la regola sulla persistenza: un fatto registrato senza il suo perché è esattamente ciò che il sistema esiste per non perdere, e conviene accorgersene mentre il perché è ancora in testa a qualcuno.

## Perché l'uscita è deterministica

Nessuna data di generazione, nessun ordine che dipenda dal filesystem, tutto ordinato. Un file generato che cambia a ogni corsa produce un diff a ogni commit, e un diff sempre rumoroso non si guarda.

Il punto non è la pulizia: il valore della linea temporale sta soprattutto nel vederne il diff. Una revisione che aggiunge tre microstep mostra tre righe nuove, e una che ne toglie uno lo dichiara invece di nasconderlo. È la stessa ragione per cui il file generato si versiona, contro la regola generale che vuole ignorati i derivati: qui il derivato è un documento che si legge e si confronta, non un artefatto di build.

## Sull'accessibilità della resa, che non è un dettaglio estetico

L'area di un passo porta un colore, ma l'identità non è mai affidata al solo colore: accanto compare sempre l'etichetta testuale. Un colore non si legge a voce, non sopravvive a una stampa in bianco e nero, e non esiste per chi non lo distingue. Una linea temporale che codifichi l'informazione solo nel colore è leggibile da una parte dei lettori e decorativa per gli altri.

## Uso

```
python tools/costruisci-timeline.py
python tools/costruisci-timeline.py --out docs/STORIA.html --nome "Nome del progetto"
python tools/costruisci-timeline.py --senza-ragione
```

Si rigenera quando il work-log cambia, cioè alla fine di un giro di lavoro sostanziale, insieme all'aggiornamento della memoria. Dove il progetto abbia attivo `hooks-starter`, la rigenerazione è un candidato naturale per un hook di chiusura sessione.

## Rapporto con gli altri pacchetti, dichiarato per non duplicare

Con `operations-log` il rapporto non è di alternativa ma di lettura: quel pacchetto tiene il registro dei microstep, con la verifica e l'esito di ciascuno, ed è la fonte più propria di questa linea temporale; questo pacchetto non lo sostituisce e non lo riscrive, lo legge insieme al work-log e ne produce la vista unica. Un progetto che abbia entrambi continua a scrivere dove scriveva, e guadagna la linea.

Con `documentazione-didattica` la relazione è di profondità crescente. La linea temporale dice in una riga perché un passo è stato fatto così; una scheda didattica dice, su un passo che se lo merita, che cosa lo rendeva fragile prima e perché la forma nuova regge, entrando nel codice reale. Un progetto che abbia entrambi trova nella linea temporale l'indice e nelle schede l'approfondimento, e la linea temporale non pretende di sostituirle.

Con `alignment` il rapporto è che quello controlla le affermazioni che invecchiano e questo produce un documento che per costruzione non invecchia, perché si rigenera. Sono due risposte allo stesso problema applicate a materiali diversi.

## Collaudo

```
python tools/costruisci-timeline.py --self-test
```

Ventitre controlli su un albero sintetico. Coprono la lettura delle voci e l'ordinamento cronologico crescente, che è l'opposto di quello in cui il work-log è scritto; le due forme di aggancio della ragione e il fatto che un passo scoperto resti scoperto invece di ricevere una spiegazione inventata; la separazione dei campi dentro una voce, dove un campo che ne mangia un altro produrrebbe una riga plausibile e sbagliata; il determinismo, verificato confrontando due corse byte per byte; l'assenza di chiamate di rete nella pagina prodotta; il fatto che il testo di una voce non possa iniettare marcatura nella pagina; e il progetto che non ha ancora un work-log, che non deve far cadere il programma.
