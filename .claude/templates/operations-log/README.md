# Pacchetto opzionale: registro dei microstep

> Registro cronologico degli interventi operativi, uno per voce, dove ogni voce dichiara che cosa è stato fatto, a che cosa serve, come è stato verificato e con quale esito. Copre una granularità che i file di memoria del sistema non coprono: `memory/progress.md` registra il passo di sessione e `memory/decisions.md` la decisione architetturale, mentre qui vive il singolo intervento con la sua prova. Nasce da un progetto istanziato da questo template, dove ha raggiunto quasi cento voci prima di essere estratto come pacchetto.

## Il problema che risolve

Un lavoro fatto e non verificato è indistinguibile da un lavoro dichiarato. La differenza fra i due si vede soltanto quando qualcosa si rompe mesi dopo, e a quel punto la domanda non è che cosa sia stato fatto ma come si sapesse che funzionava. Il work log di sessione non risponde, perché registra il passo e non la prova; il registro delle decisioni nemmeno, perché registra la scelta e non la sua esecuzione. Resta scoperta la fascia più densa di lavoro reale, cioè l'intervento singolo.

Il secondo problema è più sottile e si manifesta solo nel tempo lungo: un registro che si corregge riscrivendo le voci passate racconta un lavoro senza errori, che non è mai esistito, e chi lo eredita ripete gli errori che nessuno ha scritto. La convenzione di questo pacchetto è quindi `append-only` come quella dei file di memoria, ma con due presidi che l'esperienza ha mostrato necessari e che il semplice `append-only` non fornisce.

## I due presidi, che sono la parte non ovvia

Il primo è la dichiarazione del legame con lo scopo. Ogni voce dichiara, subito dopo il perimetro, a quale fase o obiettivo del progetto serve e che cosa dipenda da essa. La ragione è che un registro di interventi operativi tende a diventare illeggibile come cronaca di sistemistica: chi lo legge dall'inizio incontra configurazioni, strumenti e diagnosi, e perde di vista il prodotto. Quando un intervento non serve alcuna fase lo dichiara apertamente, perché un legame inventato è peggio di un legame assente: fa credere che tutto sia giustificato e toglie valore alle giustificazioni vere.

Il secondo è l'indice delle voci superate. In un registro che cresce in avanti, una voce superata non sa di esserlo: chi legge la voce vecchia e si ferma là non ha modo di sapere che una voce successiva la smentisce, e la responsabilità di scoprirlo ricade sul lettore che arriva in fondo. Aggiungere un rimando dentro la voce vecchia sarebbe una riscrittura e violerebbe la convenzione; un indice a parte non lo è. L'indice va aggiornato ogni volta che una voce ne supera una precedente, e questo è parte della convenzione e non un lavoro facoltativo.

## Mappa di istanziazione

```
templates/operations-log/OPERATIONS-LOG.md          ->  <radice>/docs/OPERATIONS-LOG.md          (tracciato)
templates/operations-log/tracciabilita-microstep.md ->  <radice>/docs/<riferimenti>/tracciabilita-microstep.md  (tracciato, facoltativo)
```

Il secondo file si istanzia soltanto in un progetto che abbia già molte voci senza il legame con lo scopo, cioè come correzione additiva del passato. In un progetto nuovo non serve, perché il legame lo dichiara ogni voce.

Il percorso di destinazione presuppone un albero `docs/`. In un progetto che non ne abbia uno, il registro va dove vive la documentazione tecnica, e il criterio è che sia versionato e raggiungibile dal `CLAUDE.md`, non che stia in una cartella con quel nome.

## Quando adottarlo, e quando no

Si adotta quando il progetto comporta lavoro operativo verificabile: configurazione di ambienti, procedure di installazione, interventi su una macchina, migrazioni, integrazione di strumenti di terze parti. In quei casi la domanda "come sapevamo che funzionasse" si pone davvero, e il registro è ciò che le risponde.

Non si adotta in un progetto di solo codice applicativo dove la stessa domanda ha già una risposta migliore, cioè la suite di test: là un registro di interventi duplicherebbe ciò che il controllo di versione e i test dicono meglio. E non si adotta per il gusto della completezza in un progetto piccolo, dove il work log di sessione basta: un registro che nessuno aggiorna è peggio della sua assenza, perché suggerisce una copertura che non c'è.

## Rapporto con gli altri livelli

Con `memory/progress.md` la divisione è di granularità e di destinatario: il work log è meta-stato per chi riprende il progetto, il registro è livello tecnico-didattico per chi lo legge. Un intervento produce tipicamente una voce nel registro e, se la sessione è significativa, un paragrafo nel work log che la indicizza senza duplicarla.

Con `memory/decisions.md` la divisione è di natura: una decisione non ovvia diventa un ADR, la sua esecuzione diventa uno o più microstep. Un ADR che nessun microstep esegue resta una intenzione; un microstep che esegue una scelta non ovvia senza ADR nasconde la decisione dentro il lavoro.

Con la skill `studio-didattico`, dove presente, la divisione è di ampiezza: il microstep racconta l'intervento, il livello didattico racconta perché una forma di fare le cose era fragile e perché quella che l'ha sostituita è migliore. Il secondo si attiva sui salti di qualità e non su ogni voce.
