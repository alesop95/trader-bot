# matt-pocock-skills

> Pacchetto opzionale del sistema di progetto. Non contiene skill: contiene la scelta. La raccolta `mattpocock/skills` è pubblicata dall'autore come plugin di Claude Code e come collezione installabile file per file, quindi il sistema non ha niente da vendorare e non deve farlo. Ciò che manca a monte, e che questo pacchetto fornisce, è la mappa fra quelle skill e ciò che il sistema di progetto già ha: quali coprono un buco reale, quali duplicano una capacità esistente, e quali vanno prese cambiando il posto in cui scrivono, perché scrivono in file che qui hanno un altro nome e un altro ruolo.

## Che cosa è la raccolta a monte

Trentuno skill pubblicate più sette in lavorazione, contate il 2026-10-20 sui `SKILL.md` del commit `5beb35b` a monte, licenza MIT, scritte dall'autore per il proprio lavoro quotidiano e pubblicate come tali. La tesi dichiarata è che gli approcci che possiedono il processo, dove il processo è un impianto completo che decide per te, tolgano controllo e rendano difficile correggere un difetto del processo stesso; le skill sono quindi piccole, adattabili e componibili, e l'autore invita esplicitamente a modificarle.

Si dividono su un asse che conviene conoscere prima di sceglierne una, perché cambia quando entrano in funzione. Quelle a invocazione utente si raggiungono solo digitandole, e il loro mestiere è orchestrare; quelle a invocazione del modello possono essere raggiunte dall'agente da sé quando il compito le riguarda, e tengono la disciplina riusabile. Una skill a invocazione utente può chiamarne una a invocazione del modello, mai un'altra a invocazione utente.

Le quattro famiglie di problemi che l'autore dichiara di voler risolvere sono, nell'ordine in cui le presenta: l'agente non ha fatto ciò che volevi, cioè il disallineamento fra la richiesta e ciò che viene costruito; l'agente è troppo prolisso, perché non conosce il gergo del dominio e usa venti parole dove ne basta una; il codice non funziona, perché mancano i cicli di riscontro; e il risultato è una palla di fango, perché la velocità dell'agente accelera anche l'entropia del codice.

## Le due vie di installazione, e perché non si prendono entrambe

La prima è il plugin di Claude Code, che installa l'insieme come pacchetto gestito e in sola lettura, aggiornato quando l'autore pubblica. È la via di chi si abbona invece di forkare, e nel catalogo di questo sistema è la stessa forma con cui si prendono `wshobson-agents` e `voltagent-subagents`.

```
claude plugins install mattpocock-skills
```

La seconda copia i file dentro il progetto, dove diventano file ordinari che si possiedono e si modificano, e nulla cambia alle spalle di nessuno.

```
npx skills@latest add mattpocock/skills
```

L'autore avverte, e l'avvertenza va ripetuta qui perché è il primo errore che si fa: installarle entrambe lascia ogni skill in doppia copia. La scelta fra le due non è di gusto ma discende dal punto successivo, cioè dal fatto che alcune di queste skill vanno adattate per convivere con il sistema di progetto: chi ne prende una di quelle prende la seconda via, perché la prima è in sola lettura per costruzione.

Dopo l'installazione, la raccolta prevede una skill di configurazione da eseguire una volta per repository, che chiede quale tracciatore di problemi si usa, quali etichette si applicano in triage e dove salvare i documenti prodotti. Quella domanda non è neutra rispetto a questo sistema, ed è trattata sotto.

## La mappa: che cosa manca davvero al sistema

Questa è la ragione del pacchetto. Le righe sono divise in tre gruppi, e il gruppo dice che cosa fare, non quanto la skill sia buona: una skill ottima che duplica una capacità esistente resta una duplicazione, e installarla mette in ombra ciò che il progetto già ha.

Il primo gruppo copre un buco reale del sistema di progetto. Non esiste qui niente che faccia quel lavoro, e sono le righe da leggere per prime al gate.

| Skill | Che cosa fa | Perché è un buco del sistema |
|---|---|---|
| `grill-me` | Interroga senza sconti chi chiede, su un piano o un disegno, finché ogni ramo dell'albero delle decisioni è risolto | Il sistema ha molte regole su come scrivere ciò che si è deciso e nessuna su come far emergere ciò che non è stato deciso. È il buco più largo dei tre gruppi |
| `grill-with-docs` | La stessa interrogazione, ma costruisce insieme il vocabolario condiviso del dominio e registra le decisioni difficili | Stesso buco, con in più il fatto che il vocabolario condiviso è esattamente ciò che rende brevi le sessioni successive |
| `wait-what` | Si lancia nel momento in cui un messaggio dell'agente non arriva, e lo fa ri-esprimere con il contesto che mancava | Nessun equivalente. Costa una riga e recupera uno scambio che altrimenti si chiude con un "va bene" non capito |
| `to-questionnaire` | Trasforma una decisione che non puoi prendere da solo in un questionario per chi può, da compilare in differita o insieme | Nessun equivalente. Il sistema sa registrare una decisione presa, non sa procurarne una che dipende da un terzo |
| `diagnosing-bugs` | Ciclo disciplinato per i difetti difficili e le regressioni di prestazioni, a fasi con un cancello fra l'una e l'altra | La norma `skills/prove-che-misurano/RIFERIMENTO.md` dice come si verifica che una prova misuri; non dice come si arriva alla causa. Sono complementari e si citano bene a vicenda |
| `wayfinder` | Pianifica un lavoro più grande di quanto una sessione contenga, come mappa di decisioni da sciogliere una per volta | Il sistema ha `roadmap.md` come scheda di direzione, che è una fotografia; questo è un metodo per attraversare un lavoro lungo |
| `wizard` | Genera una procedura guidata interattiva per i passi che solo un umano può fare: credenziali, infrastruttura, cruscotti di terze parti | Il sistema ha la regola sugli screenshot per vedere ciò che non può vedere; non ha niente per condurre l'utente attraverso una procedura manuale |
| `triage` | Porta le segnalazioni attraverso una macchina a stati di ruoli di triage | Nessun equivalente, e presuppone un tracciatore di problemi |
| `prototype` | Costruisce un prototipo usa e getta per rispondere a una domanda di disegno, come file singolo o come varianti di interfaccia commutabili | Nessun equivalente. Il sistema ha `diagrams` per disegnare e niente per provare |
| `retro` | Rilegge la trascrizione di una sessione e propone modifiche all'ambiente, non al codice: puntatori di navigazione, controlli automatici, standard per il revisore, istruzioni da sfoltire, strumenti costosi, accesso alle informazioni | Il sistema ha il registro delle lezioni verso il template e la direttiva che le lezioni diventino codice e prove, ma una lezione nasce solo quando qualcuno la nota durante il lavoro: manca il passaggio sistematico che a fine sessione cerca gli attriti nella trascrizione. Va adattata, vedi la sezione sulla retrospettiva |

Il secondo gruppo copre cose che il sistema già fa, in una forma diversa. Si prendono solo scegliendo consapevolmente quale delle due tenere, e la scelta va registrata come decisione invece di lasciata al caso.

| Skill | Che cosa nel sistema fa già questo | Come scegliere |
|---|---|---|
| `code-review` | Il pacchetto `dev-skills` porta una `code-review` di progetto, il pacchetto `subagent-template` un agente `code-reviewer`, e Claude Code ha la propria skill nativa | Quella di Matt ha due assi dichiarati, gli standard del repository e la fedeltà alla specifica di partenza, eseguiti come sotto-agenti paralleli perché non si contaminino. È l'unica delle quattro che leghi la revisione alla specifica; se il progetto lavora per specifiche, è la migliore delle quattro. Altrimenti non aggiunge |
| `tdd` | La norma `skills/prove-che-misurano/RIFERIMENTO.md` | Non si scelgono: si sommano, e vanno lette insieme. La regola dice come si stabilisce che una prova misuri il difetto che dice di misurare, la skill dice come si conduce il ciclo rosso-verde. Nessuna delle due contiene l'altra, e la regola resta normativa |
| `handoff` | La regola `token-economy.md` prescrive un `HANDOFF.md` prima di ogni `/clear`, e il template `_notes/RESUME-PROMPT.md` lo istanzia | Il sistema scrive il passaggio di consegne in un file ignorato e fisso; la skill lo compone dalla conversazione. Prenderla significa farle scrivere in `_notes/RESUME-PROMPT.md` invece che dove scriverebbe: vedi la sezione sull'adattamento |
| `research` | I pacchetti `academic-researcher` e `notebooklm-bridge` | Sono ricerche diverse: quelli sono per la letteratura scientifica con tracciamento delle fonti, questa per una domanda tecnica contro fonti primarie, eseguita come agente in secondo piano. Convivono senza sovrapporsi su un progetto che faccia entrambe le cose |
| `teach` | I pacchetti `learning-agent` e `codebase-learning` | Quelli costruiscono un ambiente di apprendimento persistente con profilo e roadmap; questa insegna un concetto usando la cartella corrente come spazio di lavoro con stato. Se `learning-agent` è attivo, questa è una duplicazione |
| `writing-for-agents` | La regola `interaction-style.md` | Si sovrappongono solo in parte e la parte scoperta conta: la regola vincola come si scrive per un lettore umano esperto, la skill come si scrive un documento che un agente raggiungerà attraverso un puntatore. Chi scrive skill e regole del proprio progetto la trova utile; dove le due divergano vince la regola, perché è normativa qui |
| `implement` | La skill `init-project-system` e il ciclo di lavoro del sistema | Questa guida la costruzione a partire da una specifica o da un insieme di segnalazioni, con il ciclo di prove ai punti concordati. Presuppone la catena `to-spec` e `to-tickets`: presa da sola vale poco |

Il terzo gruppo è quello che serve a chi lavora per specifiche e segnalazioni su un tracciatore, e il sistema non prende posizione perché non ne ha una: `to-spec`, `to-tickets`, `ask-matt`, `domain-modeling`, `codebase-design`, `improve-codebase-architecture`, `grilling`, `setup-matt-pocock-skills`, più le quattro sotto `misc` che riguardano guardrail di git, pre-commit e impalcature di esercizi. Si offrono in blocco a un progetto che abbia un tracciatore attivo, e non si offrono affatto a uno che non ce l'abbia, perché senza tracciatore metà di esse non ha dove scrivere.

## L'adattamento, che è la parte che nessuno fa e poi se ne accorge tardi

Tre di queste skill scrivono in file che nel sistema di progetto esistono già con un altro nome e un altro ruolo. Installarle senza toccarle non produce un errore: produce due memorie parallele che divergono in silenzio, che è esattamente il guasto che la regola `chat-non-e-memoria.md` esiste per impedire.

Il primo caso è il documento del vocabolario condiviso. La raccolta lo chiama `CONTEXT.md` e lo tiene nella radice; qui la conoscenza strutturale sta nelle schede di `.claude/context/`, e il posto giusto per il glossario di dominio è la scheda che copre l'area, o una scheda propria se il dominio è largo. La riconciliazione con il codice passa dal frontmatter di quelle schede, che un `CONTEXT.md` nella radice non ha: tenerlo fuori significa avere un documento che nessun `sync-context` verifica mai.

Il secondo caso sono le decisioni. `grill-with-docs` e `domain-modeling` le registrano come ADR nel posto che la configurazione indica; qui il registro è `.claude/memory/decisions.md`, numerato, e ha una convenzione che le skill non conoscono: l'agente lo aggiorna nello stesso giro in cui la decisione nasce, e l'utente la rilegge nel diff prima del commit. L'adattamento è quindi di percorso e di tempistica.

Il terzo caso è il passaggio di consegne. La raccolta lo scrive come documento a sé; qui va in `_notes/RESUME-PROMPT.md`, che è ignorato da git per scelta e va aggiornato a fine sessione.

Ne segue la conseguenza pratica annunciata sopra: chi prende una di queste tre prende la via di installazione che copia i file nel progetto, perché la via del plugin è in sola lettura e non si adatta. E la configurazione iniziale della raccolta, che chiede dove salvare i documenti prodotti, si risponde con i percorsi di questo sistema e non con i suoi predefiniti.

`resolving-merge-conflicts` stava nel primo gruppo fino al 2026-10-19, quando l'autore l'ha tolta dalla raccolta senza sostituirla, e qui non si offre più.

## La retrospettiva, e dove atterra in questo sistema

`retro` si invoca solo a mano, legge la sessione corrente o quella che le si indica nei registri di sessione della macchina, classifica gli attriti in sette categorie e propone, in ordine di gravità, senza modificare nulla finché l'utente non sceglie. Due tesi la reggono e valgono anche qui. La prima: una violazione meccanica, cioè uno schema sintattico fisso o un percorso vietato, si chiude con un controllo deterministico e non con una frase, perché un controllo può fallire e una frase no; solo il giudizio resta prosa. La seconda: un repository senza alcun presidio, né hook di pre-commit né CI che lanci i controlli, è di per sé un riscontro, e un controllo che esiste ma non è collegato si collega invece di riscriverlo.

Lette queste tesi accanto al sistema, il grosso della seconda è già fatto: `chiudi-sessione` lancia accenti, trattini, comandi spezzati, riferimenti, fine riga, anonimizzazione e budget delle istruzioni, e `.githooks/pre-commit.d/` porta `anti-slop` e `instruction-budget` anche ai commit manuali. L'esempio d'uso più citato della skill, una regola di pulizia prima della pubblicazione trasformata in hook, qui esiste già come `Test-Anonymization.py` dentro `chiudi`. Ciò che la retrospettiva aggiungerebbe è a monte, nel modo in cui si scopre che un controllo manca.

L'adattamento ha quattro punti, e il primo decide se la skill funziona affatto su questa macchina. La trascrizione che la skill legge vive nella cartella `projects` dell'account, e l'hook di wipe a chiusura la cancella insieme a ogni sessione chiusa: una retrospettiva sulla giornata precedente, che la skill dichiara possibile, qui trova il vuoto. Si esegue quindi nella sessione stessa, prima di `chiudi`, oppure lo strumento di chiusura la propone prima del wipe.

Il secondo punto è la destinazione dei riscontri, che a monte vanno in `CODING_STANDARDS.md` e in `AGENTS.md` e che qui hanno sedi già definite. Un controllo meccanico entra fra quelli di `chiudi-sessione` o in `.githooks/pre-commit.d/`, con il proprio `--autotest` che cade se il difetto torna. Un puntatore di navigazione va nell'indice delle norme caricate su richiesta del `CLAUDE.md` o nella descrizione della skill che doveva scattare. Una prescrizione di giudizio va nella regola pertinente, e il caso che la giustifica in `.claude/norme/`. Un'istruzione che non cambia il comportamento si toglie, e `misura-istruzioni.py` dice quanto pesava.

Il terzo punto è il canale. In un progetto istanziato un riscontro che passa le due domande della sezione 16 di `PROJECT-SYSTEM.md` diventa una lezione con `lezioni-template.py nuova`, e da lì arriva al template con la raccolta di apertura sessione; la retrospettiva diventa così la fonte sistematica di un registro che oggi si alimenta solo per caso.

Il quarto punto è il più grosso e non è un adattamento ma una decisione aperta. La skill presuppone due stadi, un agente che implementa sotto pressione di contesto e un revisore che riceve il solo diff, e sposta gli standard sul secondo. Questo sistema non ha lo stadio di revisione come luogo degli standard: tutte le regole stanno in `.claude/rules/` e si caricano nella sessione che implementa. Adottare la tesi per intero vorrebbe dire separare le regole di giudizio che servono solo a chi rilegge un diff e caricarle in revisione, con un risparmio di contesto da misurare prima di dichiararlo.

## Che cosa il sistema di progetto ha e la raccolta non ha

Vale dirlo perché il confronto non è a senso unico, e perché un catalogo che elenca solo ciò che prende diventa una lista della spesa. La raccolta non ha una memoria versionata del progetto né una riconciliazione fra documentazione e commit, che sono il motore di questo sistema; non ha una disciplina delle fonti né un modo di trattare quelle che non si riescono a leggere; non ha regole tipografiche né strumenti che le attuino; non ha un gate dei pacchetti; e non ha una posizione sull'identità git e sull'igiene dell'account su una macchina condivisa. Le due cose si compongono bene proprio perché guardano a problemi diversi: là la conduzione di una sessione di lavoro, qui la persistenza di ciò che la sessione produce.

## Al gate

Si propone a un progetto che scriva codice, e con priorità alle prime quattro righe del primo gruppo, che sono quelle il cui valore non dipende da come il progetto è organizzato. Il terzo gruppo si propone soltanto dove esista un tracciatore di problemi attivo. A un progetto che non produca codice, per esempio una raccolta documentale o una tesi, si propongono le sole `grill-me`, `wait-what` e `to-questionnaire`, che di codice non parlano.

Quando si attiva, si dichiara subito quale via di installazione si è scelta e perché, e se sono state prese skill del secondo gruppo si scrive nel registro delle decisioni quale delle due capacità sovrapposte resta in uso. Senza quella riga, fra due mesi nessuno saprà se la `code-review` che gira sia quella del progetto, quella della raccolta o quella nativa.
