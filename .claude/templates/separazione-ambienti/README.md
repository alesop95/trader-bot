# Pacchetto: separazione-ambienti

> Guida tecnico-didattica, registro delle fonti ed esempi annotati per scegliere e capire come separare test e produzione. Il pacchetto non sceglie niente da solo: è il materiale da cui la skill `separazione-ambienti` attinge le spiegazioni durante il gate, e quello che un progetto porta con sé per ricordare perché ha scelto una forma invece di un'altra.

<!-- readme-summary: paradigmi di separazione fra test e produzione, spiegati e con le fonti -->

## Il problema che risolve

Un progetto separa test e produzione quasi sempre in un modo che nessuno ha scelto: è il modo del primo tutorial seguito, o di chi ha avviato il progetto, o l'unico che si conosceva. Finché va bene non se ne parla, e quando va male non si sa se il difetto stia nella forma o nella sua esecuzione, perché nessuno ha mai scritto quali canali quella forma chiudeva e quali lasciava aperti.

Il pacchetto risponde a due bisogni distinti. Il primo è scegliere: al gate dell'inizializzazione o dell'allineamento, chi decide deve poter confrontare le forme possibili su una base comune, cioè che cosa significa sceglierne una rispetto alle altre, che cosa richiede, che cosa costa e come fallisce. Il secondo è capire dopo: fra sei mesi, chi apre la scheda `deployment.md` del progetto deve trovare non solo la sigla della forma scelta ma il documento che ne spiega la meccanica e i rischi, con le fonti da cui quella spiegazione viene.

## Che cosa contiene

```
separazione-ambienti/
├── README.md                          questo file: istanziazione e uso
├── GUIDA.md                           guida ai paradigmi, per asse e per forma, a campi fissi
├── FONTI.md                           registro delle fonti: 9 casi osservati e 37 fonti pubblicate
└── esempi/
    ├── compose.parametrizzato.yaml    forma R2 sempre accesa, un file per due ambienti
    ├── compose.prova.yaml             forma R2 a richiesta, stack di prova indipendente
    ├── variabili-per-ambiente.example modello dei nomi delle variabili, senza valori
    └── adr-separazione-ambienti.md    scheletro della voce ADR che registra la scelta
```

La guida descrive quattro assi indipendenti, cioè dove girano gli ambienti, come passa il codice, da dove vengono i dati di prova e come stanno i sorgenti, e per ogni forma usa gli stessi campi: che cos'è, che cosa significa sceglierla rispetto alle vicine, come funziona con un estratto annotato, che cosa richiede, che cosa costa, come fallisce, quando passare ad altro. Chiude con le pratiche trasversali, cioè costruire una volta e promuovere, configurazione separata dal codice, parità, ambienti effimeri, tecniche di rilascio, migrazioni in due tempi, infrastruttura dichiarata, segreti per ambiente e ambienti di prova legati alla rete giusta, e con i percorsi di crescita da una forma all'altra.

Il registro delle fonti ha una voce per fonte, con indirizzo letto, data dichiarata, licenza dichiarata, data di consultazione, stato di lettura, su che cosa la fonte è autorevole, citazioni letterali brevi, limiti che la fonte stessa dichiara e punti del template in cui è usata. I casi osservati sono descritti per archetipo, senza nomi propri.

## Rapporto con la regola e con la skill

Tre oggetti, tre ruoli, e nessuna duplicazione. La norma `.claude/skills/separazione-ambienti/RIFERIMENTO.md` è la norma breve: il catalogo delle forme, i rischi trasversali, il gate e dove si registra l'esito. La skill `.claude/skills/separazione-ambienti/` è la procedura dell'interazione: raccoglie i fatti, pone le domande, propone e spiega. Questo pacchetto è la conoscenza: la skill ne legge la sezione pertinente invece di improvvisare la spiegazione, così che ciò che l'utente sente al gate e ciò che trova sul disco dopo sia la stessa cosa.

## Cosa istanzia, e dove

Il pacchetto si istanzia quando il gate della separazione si conclude con una scelta, cioè di regola sempre, salvo un progetto che registri il rinvio.

```
templates/separazione-ambienti/GUIDA.md   ->  docs/separazione-ambienti/GUIDA.md
templates/separazione-ambienti/FONTI.md   ->  docs/separazione-ambienti/FONTI.md
templates/separazione-ambienti/esempi/    ->  solo i file della forma scelta, adattati, dove il progetto tiene la propria infrastruttura
```

La guida e il registro si copiano interi e non si potano: una guida che contiene solo la forma scelta non permette più di capire perché le altre sono state scartate, che è precisamente la domanda del prossimo allineamento. Gli esempi invece si copiano solo se corrispondono alla forma scelta, e si adattano al progetto: sono modelli annotati, non configurazioni pronte, e i valori predefiniti vanno verificati contro la composizione esistente con il confronto descritto in testa a `compose.parametrizzato.yaml`. Lo scheletro dell'ADR diventa una voce di `memory/decisions.md`, e la sezione "Modello di separazione" di `context/deployment.md` rimanda a `docs/separazione-ambienti/GUIDA.md` per la spiegazione.

## Quando offrirlo

Il pacchetto non passa dal gate dei pacchetti come gli altri, perché la decisione a cui serve è già un gate a sé: lo porta la skill `separazione-ambienti` quando il gate si chiude con una scelta. Resta nel catalogo `PACKAGES.md` perché sia visibile e perché un progetto che ha rinviato la scelta possa istanziarlo dopo.

## Come si aggiorna

Una forma entra nella guida come osservata solo quando un progetto la usa, con la sigla del caso nel registro; fino ad allora sta fra le pratiche non ancora osservate, con le sue fonti. Una fonte di documentazione di prodotto si riverifica quando il prodotto cambia versione, e la data di consultazione di ogni voce è ciò che permette di sapere quando. Un caso nuovo, osservato in un allineamento, entra nel registro con la sua sigla nello stesso giro di lavoro, secondo `chat-non-e-memoria.md`, e se smentisce una forma la guida si corregge dichiarando la correzione, non riscrivendo il passato.

## Requisiti e stato

Nessuna dipendenza: è documentazione e quattro file di esempio. I due esempi di composizione sono stati risolti con `docker compose config` sotto Docker Compose 5.5.1 il 2026-09-23: il file parametrizzato si ferma se manca `SITE_ORIGIN`, e con `-p <progetto>-staging` produce volumi e rete con il prefisso dello staging, distinti da quelli di produzione; il file di prova pubblica la porta sulla sola interfaccia locale. Non sono stati avviati, perché gli esempi non hanno un'applicazione da costruire.
