---
name: gate-pacchetti
description: >
  Attraversa il catalogo dei pacchetti opzionali per settore, spiegando ciascun pacchetto
  nel terminale e chiedendone l'attivazione una voce per volta. Riconosce dai fatti del
  progetto quali settori lo riguardano, dichiara il riconoscimento e lo fa correggere, poi
  propone i soli pacchetti dei settori riconosciuti, ognuno con che cosa fa, perché a questo
  progetto potrebbe servire e che cosa costa. Si esegue in inizializzazione, a ogni tornata
  di allineamento, e ogni volta che l'obiettivo del progetto cambia. Non installa nulla
  senza una risposta esplicita e non esegue mai git add, commit o push.
disable-model-invocation: true
---

## Contesto del progetto (best-effort, pre-iniettato)

!`git log -1 --format="%h %ad %s" --date=short`

## Che cosa fa questa skill, e perché non è un elenco

Il catalogo `.claude/templates/PACKAGES.md` contiene più di ottanta voci opzionali. Un gate che le proponga tutte in fila è un gate che nessuno legge fino in fondo, e un gate che ne scelga tre a occhio nasconde le altre senza dirlo. Questa skill risolve il problema cambiando l'unità della domanda: si riconosce prima a quali settori il progetto appartiene, e si attraversano i soli settori riconosciuti. Un progetto appartiene tipicamente a due o tre settori su dieci, quindi le domande restano pertinenti.

La fonte di verità di che cosa esista resta il catalogo, che va letto e non ricordato. Questa skill è la procedura, non il contenuto: se le due divergono, ha ragione il catalogo.

## Passo 1 - Raccogliere i fatti prima di ipotizzare

Il riconoscimento dei settori poggia su fatti del progetto, non su una impressione. Prima di qualunque domanda si guarda, in sola lettura, che cosa il progetto è già.

Si legge `CLAUDE.md` se c'è, perché la sezione che dice che cosa sia il progetto è la dichiarazione più diretta dell'obiettivo. Si legge `.claude/memory/index.md` se c'è, per sapere a che punto è. Si guarda la forma della radice: quali linguaggi, se esista una cartella di documenti, se esista una cartella di fonti, se esistano già `tools/` e che cosa contenga. Si guarda se il repository abbia una storia lunga o sia appena nato, perché un progetto ereditato e uno greenfield hanno bisogni opposti. Si guarda se esista già un `.mcp.json` e quanti server dichiari, perché quel numero è il vincolo del settore delle integrazioni. E si guarda quali pacchetti siano già istanziati, cercando i loro file nella posizione che il catalogo dichiara.

Se il progetto è nuovo e questi fatti non esistono ancora, il fatto da usare è l'obiettivo dichiarato dall'utente, e in quel caso lo si chiede esplicitamente prima di proseguire, in una domanda sola: che cosa questo progetto deve fare, e che cosa produrrà.

## Passo 2 - Dichiarare i settori riconosciuti, e farsi correggere

Si presentano all'utente i settori riconosciuti, ciascuno con il fatto da cui lo si è riconosciuto, e i settori esclusi con la ragione dell'esclusione. La forma è breve e va scritta come una ipotesi, perché è una ipotesi: chi conosce il progetto è l'utente.

```
Settori riconosciuti per questo progetto

  Fondamenta e igiene          la storia git ha 180 commit e piu' di un autore
  Fonti e corpus documentali   esiste docs/fonti/ con 40 file, e SOURCES.md
  Scrittura e documentazione   il progetto produce prosa, 60 file .md tracciati

Settori esclusi

  Domini scientifici           il dominio non e' scientifico
  Apprendimento guidato        l'obiettivo dichiarato non e' imparare
  Voce e audio                 nessuna fonte parlata e nessuna produzione audio
  ...

Ne aggiungo o ne tolgo qualcuno?
```

Un settore che l'utente aggiunge si attraversa come gli altri. Un settore che l'utente toglie si salta, e l'esclusione si registra con la sua ragione: senza quella riga la tornata successiva riproporrà lo stesso settore alla stessa persona, e un gate che ripete diventa un gate che si impara a scorrere senza leggere.

## Passo 3 - Attraversare un settore per volta

Per ciascun settore riconosciuto si apre la sezione corrispondente del catalogo, si legge la frase che spiega a chi quel settore serve, e la si riporta all'utente prima delle righe: è quella frase a dire perché le domande che seguono hanno senso.

Poi, per ogni pacchetto del settore che il trigger della colonna "quando offrirlo" rende pertinente a questo progetto, si presenta la voce in tre frasi e nessuna di meno.

La prima dice che cosa fa il pacchetto, in linguaggio di chi lo userà e non in quello di chi lo ha scritto. La seconda dice perché a questo progetto potrebbe servire, e va legata a un fatto raccolto al Passo 1 invece che al trigger generico: non "utile ai progetti con molti documenti" ma "qui ci sono quaranta file sotto `docs/fonti/`". La terza dice che cosa costa, e il costo comprende le dipendenze esterne da installare, i token che un server MCP occupa a ogni turno anche quando non viene usato, il lavoro di istanziazione dove ci sono tabelle da sostituire, e soprattutto le capacità che il pacchetto duplicherebbe.

Quest'ultimo punto è quello che si dimentica e che fa danni. Dove il progetto abbia già quella capacità, in proprio o tramite un altro pacchetto, il pacchetto non si propone come aggiunta: si dice che il terreno è già coperto e si propone semmai di allineare ciò che c'è. Dove due pacchetti del catalogo coprano lo stesso terreno, si presentano insieme come una scelta fra due, mai come due domande separate, perché due sì consecutivi producono una duplicazione che nessuno ha deciso.

Poi si chiede, e si aspetta una risposta esplicita. Un silenzio non è un sì, e nemmeno la pertinenza evidente lo è.

Quando il progetto richiede stato dell'arte, bibliografia scientifica, lettura di paper, confronto paper/codice o benchmark R&D, considera esplicitamente `academic-researcher` e presenta tre decisioni separabili: `openalex` per scoperta e metadati bibliografici, `paperqa2` per interrogare un corpus locale e `feynman` per ricerca e audit tramite CLI autonoma. Chiedi per ciascuno «sì», «no» o «non ora», sia in inizializzazione sia in allineamento quando la scelta non è già registrata. Spiega il costo concreto: OpenAlex richiede connessione MCP e accesso/budget OpenAlex; PaperQA2 richiede Python, modello e indice locale; Feynman richiede runtime, provider e controllo dei risultati. Non far sparire OpenAlex perché è stato scelto `academic-researcher`; se `academix` o `semantic-scholar-mcp` coprono già la scoperta, chiedi se mantenere, sostituire o affiancare il server esistente, mostrando duplicazione e costo. Le tre voci svolgono ruoli diversi e possono essere scelte indipendentemente. Il runbook di configurazione è in `.claude/templates/academic-researcher/INTEGRAZIONI-TOOL.md`.

## Passo 4 - Che cosa fare della risposta

Su un sì si istanzia seguendo il `README.md` del pacchetto quando è a cartella, mai ricostruendo il contenuto a memoria. Se un file di destinazione esiste già, si mostra la differenza invece di sovrascrivere. Se il pacchetto aggiunge o modifica una skill sotto `.claude/skills/` e il progetto ha `tools/sync-codex-skills.py`, si rigenerano i wrapper Codex e si verifica l'allineamento con `python tools/sync-codex-skills.py --check`; il wrapper non si scrive a mano. Subito dopo si mostra il recap d'uso, cioè i comandi e il flusso essenziali presi da quel README: un pacchetto installato di cui non si conoscono i comandi è un pacchetto che non verrà usato, e il recap costa tre righe.

Per `openalex`, `paperqa2` e `feynman`, un sì attiva il percorso pertinente del runbook: prepara la configurazione nel progetto, verifica la disponibilità del tool e annota versione, ambito del corpus e scelte di modello/provider nella memoria del progetto. Le credenziali e i token OAuth restano nel livello privato o nello store del client. Un sì a `academic-researcher` non vale come sì implicito a nessuno dei tre tool.

Su un no si registra il no. È l'altra metà della regola e vale quanto la prima: un promemoria esplicito che il pacchetto resta istanziabile in seguito, con la data e, se l'utente l'ha data, la ragione. Il posto dove registrarlo è il work log del progetto, oppure il registro delle decisioni se la scelta è architetturale, e vale qui la regola generale per cui l'agente aggiorna la memoria nello stesso giro, senza attendere una richiesta.

Su un "non ora" si registra allo stesso modo, distinguendolo da un no: sono due cose diverse alla tornata successiva.

## Passo 5 - Il vincolo sugli MCP, che attraversa i settori

I pacchetti di tipo MCP server compaiono in più settori, ma il loro vincolo è unico e si conta sul totale: non più di tre o quattro server nuovi per sessione, e non più di sei connessi in tutto. La ragione è che ogni server espone tool che occupano token nel contesto a ogni turno, anche se in quella sessione nessuno li usa, quindi il costo è fisso e si paga sempre.

Ne segue una conseguenza operativa per questa skill: il conteggio si tiene attraverso i settori e non dentro ciascuno, e quando il tetto è raggiunto lo si dice, invece di proporre il settimo server e lasciare che sia l'utente ad accorgersene. Si preferisce sempre l'implementazione ufficiale del vendor rispetto a un fork community non verificato, e i server che recuperano contenuto web o documenti esterni si esaminano prima di concedere loro permessi di scrittura, perché sono vettori di prompt injection.

## Passo 6 - Chiudere dichiarando che cosa è cambiato

Alla fine si consegna un riepilogo in quattro righe: quali settori sono stati attraversati, quali pacchetti sono stati attivati con che cosa hanno istanziato, quali sono stati rifiutati o rimandati, e quali file il gate ha scritto. L'ultima riga è il presidio della regola per cui ciò che si dice in sessione si scrive anche su disco, e se manca vuol dire che il gate è rimasto in chat.

I comandi git restano manuali dell'utente: il gate prepara i file e non committa.

## Riesecuzione, che è il caso normale e non l'eccezione

Questa skill non è un passo dell'inizializzazione soltanto. Si riesegue a ogni tornata di allineamento, e la ragione è che entrambe le cose che la governano cambiano nel tempo: il catalogo cresce, e il progetto diventa qualcosa che all'inizio non era. Un progetto che a gennaio non raccoglieva fonti e a marzo ne raccoglie ha cambiato settore senza che nessuno lo abbia dichiarato, e un gate eseguito una volta sola non se ne accorgerà mai.

Alla riesecuzione si riparte dai settori e si dichiara che cosa è cambiato rispetto alla volta precedente: quali settori sono nuovi, quali pacchetti sono comparsi nel catalogo da allora, e quali decisioni prese l'altra volta restano valide. Le voci già decise non si ripropongono come domande nuove: se ne mostra la decisione, e si chiede soltanto per quelle il cui presupposto è cambiato. Un pacchetto rifiutato quando il progetto non aveva ancora una certa caratteristica torna proponibile quando quella caratteristica compare, e dirlo esplicitamente è il modo in cui il gate resta utile alla terza tornata invece di diventare rumore.
