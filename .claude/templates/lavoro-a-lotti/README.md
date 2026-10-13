# Pacchetto opzionale: lavoro-a-lotti

> Impianto per svolgere un lavoro **più grande di qualunque finestra di sessione** su un corpus di molti elementi, in modo riprendibile fra sessioni e fra giorni, e per distribuirlo su più flotte di agenti con serbatoi di quota indipendenti. Non è un orchestratore e non lancia processi: è il **contratto** che rende il lavoro interrompibile, e il presidio che impedisce di ricominciare da capo.

## Cosa risolve

Il caso è sempre lo stesso e ha sempre la stessa forma: una **mappatura** su molti elementi più una **aggregazione** finale. Parsing retroattivo di centinaia di file, studio preparatorio a un refactoring esteso, ingestione di un corpus documentale da mettere in relazione.

Il problema che si osserva è che la sessione finisce a metà. E la diagnosi istintiva, cioè "ho lanciato troppi agenti in parallelo", **è sbagliata**, come mostra l'aritmetica.

Assunto dichiarato: una passata per elemento che legge, ragiona e scrive un esito costa dell'ordine di qualche migliaio di token. Su trecento elementi si arriva **all'ordine del milione di token** per la sola mappatura, prima di qualunque aggregazione. Nessuna finestra di una sessione interattiva contiene quel lavoro, né in parallelo né in sequenza.

> **Il parallelismo non consuma più token per elemento: consuma gli stessi token in metà tempo.** Non è la causa dell'esaurimento, è l'acceleratore. Una misurazione pubblicata su un refactor di oltre trecento file riporta il limite raggiunto in circa quindici minuti in parallelo contro trenta in sequenza, sullo stesso piano e sullo stesso lavoro.

Ne segue che la domanda utile non è "come parallelizzo senza bruciare" ma **"come faccio un lavoro che non entra in una finestra"**, e la risposta è in quattro leve, in ordine di efficacia, dove il parallelismo arriva ultimo.

**Togliere elementi.** Molta mappatura è deterministica: estrazione, normalizzazione, filtro, deduplicazione per hash. Solo gli elementi che richiedono *giudizio* devono vedere un modello. Portare N da trecento a trenta vale più di qualunque ottimizzazione sui trecento, ed è l'unica leva che cambia l'ordine di grandezza.

**Rendere il lavoro riprendibile.** Se la finestra finisce all'elemento 180, ricominciare da capo è la ragione per cui questi lavori non si finiscono mai. È il pezzo che questo pacchetto fornisce, ed è quello che nessuno degli strumenti esaminati offre.

**Instradare su serbatoi indipendenti.** La mappatura ripetitiva va su una flotta di agenti con la propria quota; l'aggregazione resta sulla flotta principale. I due consumi non si sommano sullo stesso limite.

**Solo a questo punto, parallelizzare**, che comprime il tempo di attesa dentro una finestra senza cambiare il totale.

## Perché un registro e non un orchestratore

Gli orchestratori esistono, sono maturi e risolvono un problema diverso: l'**isolamento del filesystem**, perché più agenti sullo stesso repository si pestano i piedi con rami e modifiche non salvate. Danno la leva e non il criterio, e nessuno di essi risponde a *quando convenga* né a *come si riprende*.

Questo pacchetto quindi **non li sostituisce e non li duplica**: si compone con essi, e funziona anche senza. Il passaggio di consegne fra agenti è un file nel repository, il che porta tre proprietà che nessun orchestratore offre.

È **agnostico rispetto all'agente**: funziona con qualunque agente da terminale, con due agenti diversi insieme, e a mano.

È **ispezionabile**: il passaggio di consegne si legge, non è un canale opaco fra processi.

È **durevole**: sopravvive alla chiusura di tutto, perché è su disco e nel controllo di versione.

## Prima di costruire: che cosa il sistema produce già

Applicazione diretta della sezione 20 del sistema di progetto. Prima di aggiungere un registro si guarda che cosa esiste, e in questo sistema esiste parecchio.

| Già disponibile | Copre | Questo pacchetto |
|---|---|---|
| `doc-ingest` | manifest a content-hash che **non riconverte l'invariato**: ripresa della fase di **conversione** | non la duplica; la presuppone |
| `ccusage` | misura reale del consumo per sessione, modello e progetto | non stima a occhio: la stima di costo si tara su quella misura |
| `rules/token-economy.md` | disclosure progressiva a tre livelli, caricamento on-demand | è la riduzione del costo **per elemento**, e resta la prima leva |
| controllo di versione | i commit sono già un registro di ciò che è stato fatto | il registro copre il lavoro **prima** che diventi commit |

Ne segue il perimetro esatto: **il registro copre la fase di ragionamento per elemento**, cioè l'unica che nessuno degli strumenti sopra traccia.

## Il registro

Un file JSONL nel livello privato del progetto, una riga per elemento.

```json
{
  "id": "<identificativo stabile dell'elemento, tipicamente il percorso relativo>",
  "hash": "<digest del contenuto al momento della presa in carico>",
  "stato": "da-fare | in-corso | fatto | saltato | errore",
  "agente": "<etichetta della flotta che lo ha lavorato>",
  "artefatto": "<percorso relativo dell'esito prodotto, se previsto>",
  "nota": "<una riga sul perche', obbligatoria per saltato e errore>",
  "aggiornato": "<data e ora>"
}
```

Tre scelte meritano la spiegazione, perché sono quelle su cui un registro fatto male fallisce.

**L'identificativo è stabile e il contenuto è hashato.** Senza l'hash, un elemento modificato dopo essere stato marcato come fatto resta fatto per sempre, e il registro diventa una bugia che si consolida. Con l'hash, una modifica lo riporta automaticamente da fare.

**Lo stato ammette `saltato` come esito legittimo**, distinto da `errore`, e in entrambi i casi la nota è obbligatoria. Un registro che ammette solo fatto e non-fatto costringe a mentire sugli elementi che non andavano lavorati, ed è così che si perde la distinzione fra "non serviva" e "non ci sono riuscito".

**Il campo dell'agente esiste** perché senza di esso, a valle, non si sa più quale flotta ha prodotto cosa, e la prima anomalia di qualità non è attribuibile.

## Il presidio, e perché non guarda lo stato

> **Sezione 19 del sistema di progetto: un controllo che dipende da ciò che deve controllare non è un controllo.**

Il campo `stato` lo scrive **l'agente che deve superare il controllo**. Un agente che si dichiara `fatto` senza aver prodotto nulla supera qualunque verifica basata su quel campo, e lo fa senza malafede: basta che abbia interpretato male il mandato, o che sia stato interrotto dopo aver scritto lo stato e prima di scrivere l'esito.

Il presidio quindi **non consulta lo stato dichiarato: consulta l'artefatto**. Un elemento conta come concluso se e solo se il file di esito esiste, non è vuoto, e ha la forma dichiarata. Dove non è previsto un artefatto, il lavoro va ridisegnato perché ne produca uno: **un esito che non lascia traccia non è verificabile**, e un lavoro non verificabile non è riprendibile.

Il presidio dichiara anche che cosa **non** copre, come prescrive la sezione 17. Distingue la presenza dall'assenza, **non il buono dal mediocre**: sa dire che un esito esiste ed è ben formato, non che sia corretto. Credere il contrario produce fiducia in una copertura che non esiste.

E dichiara la propria discordanza come dato utile: un elemento `fatto` senza artefatto prova che qualcosa nel mandato non ha funzionato, e non si sistema in silenzio; e va guardato prima di rilanciare.

## La regola di instradamento fra flotte

Vale quando sulla macchina esistono **due o più flotte di agenti con quote indipendenti**. Il criterio è la natura del compito, non la sua difficoltà.

| Fase | Dove | Perché |
|---|---|---|
| **Mappatura** per elemento: leggere, estrarre, classificare, riassumere | flotta secondaria | ripetitiva, mandato stretto, esito breve e verificabile; è il volume |
| **Aggregazione**: mettere in relazione, decidere, scrivere | flotta principale | richiede il contesto d'insieme, che è precisamente ciò che non va sprecato |
| **Progettazione** del lotto e revisione degli esiti | flotta principale | è la parte che decide se il resto ha senso |

La flotta secondaria **non deve conoscere l'aggregazione**, e la principale **non deve leggere gli elementi grezzi**: legge gli artefatti. È la stessa disciplina del subagent come firewall di contesto, applicata fra processi diversi invece che dentro uno solo.

## Il cancello: quando NON usare questo pacchetto

Il settore dell'orchestrazione ha già un trigger quantitativo dichiarato nel catalogo: **sotto le tre sessioni o i tre rami paralleli costa più di quanto renda.** Qui se ne aggiunge uno specifico, e va posto come domanda prima di cominciare.

**Quanti elementi, e quanto costa uno?** Se il prodotto sta comodamente in una finestra, il registro è burocrazia: si fa il lavoro e basta.

**Quanti elementi richiedono davvero giudizio?** Se la risposta è "tutti", quasi sempre non è stata cercata la parte deterministica. Si torna alla prima leva.

**Esiste un artefatto per elemento?** Se no, il lavoro non è verificabile e il registro non può presidiarlo. Si ridisegna il lavoro, non si adotta il registro.

## Mappa di istanziazione

| Dal pacchetto | Nel progetto | Tracciato |
|---|---|---|
| `registro.esempio.jsonl` | `_notes/registro-<lavoro>.jsonl` | no, è stato di lavoro |
| `tools/registro.py` | `tools/registro.py` | sì |
| `tools/valida-etichette.py` | `tools/valida-etichette.py` | sì |
| la regola di instradamento | `.claude/rules/lavoro-a-lotti.md`, dichiarata fra le regole caricate | sì |

Il registro sta nel livello privato perché è **stato**, non conoscenza: cambia a ogni elemento lavorato e sporcherebbe la storia. Lo strumento e la regola sono invece impianto, e si versionano.

## Come si usa, passo per passo

Si dichiara il lavoro e si genera il registro dagli elementi del corpus. Si esegue il presidio in sola lettura per vedere quanti elementi ci sono e quale sia lo stato. Si stima il costo, con il consumo misurato invece che assunto. Si lavora un lotto, fermandosi prima della fine della finestra invece che dopo. Si esegue di nuovo il presidio, che confronta artefatti e stati e segnala le discordanze. Si riprende, anche il giorno dopo, e il registro dice da dove.

## La forma del mandato, che decide se il registro serve a qualcosa

Lezione del primo pilota su un corpus reale, ed è costata l'intero lotto. Il mandato dato all'agente era: *leggi i primi dieci elementi da fare, poi scrivi le dieci sintesi, poi aggiorna le dieci righe*.

L'agente ha letto i dieci sorgenti, ha annunciato *"ora preparo le sintesi e aggiorno il registro"*, e ha chiuso il turno. **Zero artefatti, zero righe aggiornate, quindicimila token spesi in letture da rifare.** Nessun errore, nessuna sandbox, nessun permesso negato: semplicemente un turno finito prima della fase di scrittura.

Il difetto non è dell'agente ma del mandato, e ha una forma precisa: **tutto il progresso viveva nel turno**. Un lotto strutturato come "leggi tutto, poi scrivi tutto" ha un unico punto in cui il lavoro diventa durevole, e se il turno finisce prima di quel punto non resta niente. È esattamente ciò che il registro esiste per impedire, sabotato dalla forma della richiesta.

> **La regola: il mandato deve rendere durevole ogni singolo elemento, non il lotto.** Si legge un elemento, si scrive il suo artefatto, si aggiorna la sua riga, e solo allora si passa al successivo. Un'interruzione in qualunque punto lascia gli elementi già chiusi sul disco e il registro coerente con essi.

La verifica che la forma sia giusta è una domanda sola: **se il turno finisse adesso, quanto lavoro sopravviverebbe?** Se la risposta dipende da quanti elementi mancano alla fine del lotto, la forma è sbagliata.

Ne discende anche la dimensione del lotto. Non serve tenerla piccola per prudenza: con la forma corretta un lotto grande è sicuro quanto uno piccolo, perché ogni elemento è già un punto di ripresa. La dimensione si sceglie sul tempo di attesa accettabile, non sul rischio.

## Il costo per elemento, misurato

Primo lotto reale su un corpus documentale, dieci elementi da circa nove kilobyte l'uno, mappatura con sintesi ed estrazione di entità.

| Grandezza | Valore misurato |
|---|---|
| Token per elemento | **circa 20.000** |
| Tempo per elemento | circa 68 secondi |
| Proiezione su 371 elementi | **circa 7,4 milioni di token, circa 7 ore** |

**La stima a priori era di 3-5 mila token per elemento: il valore reale è da quattro a sei volte tanto.** Non era una stima sciatta, era una stima; è esattamente per questo che la regola prescrive di misurare invece di assumere. Chi progetta un lotto sulla stima sbagliata dimensiona male tutto: la dimensione del lotto, il tempo, e la scelta se il lavoro entri o no in una finestra.

La conseguenza sul caso osservato è netta e conferma la premessa del pacchetto: sette milioni di token non entrano in nessuna finestra di sessione, quindi **quel lavoro non è affrontabile senza registro**, a prescindere da quanti agenti si lanciano in parallelo.

Il modo corretto di ricavare questo numero è misurare il consumo della flotta **prima e dopo un lotto piccolo**, e dividere. Non serve altro, e va rifatto per ogni tipo di lavoro: venti mila token per elemento valgono per questa forma di mappatura su questa taglia di documenti, non in generale.

## Il modello si sceglie dal compito, e il costo sta nei turni

Sezione nata il 2026-10-06 in un progetto istanziato, che deve schedare alcune migliaia di documenti convertiti, e scritta su istruzione dell'utente come lezione generale. Due lotti da 50 schede di fonte, scritte dal modello economico con 5 agenti da 10 schede, hanno dato le misure seguenti.

| Lotto | Parole negli estratti | Token in tutto | Token per scheda | Durata |
|---|---|---|---|---|
| estratti da 1500 parole | circa 69 900 | 491 484 | circa 9 800 | circa 2 minuti e mezzo |
| estratti da 800 parole | circa 39 700 | 447 132 | circa 8 900 | circa 2 minuti |

Nello stesso progetto, la lettura profonda di una fonte di 25 000 parole con verifica dei conti, fatta dal modello intermedio, è costata 283 497 token, circa 11 per parola.

Da queste misure discendono tre regole. La prima: un compito che consuma molti token ma non richiede giudizio fine va al modello più economico che lo sa fare, e il modello più capace si riserva alla parte che ne ha bisogno, come la verifica dei conti o la sintesi fra fonti. La scelta si fa per compito e non per sessione, e si misura invece di assumerla.

La seconda: il testo letto non è la voce di costo principale. Gli estratti del 43 per cento più corti hanno ridotto il costo solo del 9 per cento. Il grosso viene dai turni: ogni agente ha fatto circa 24 chiamate di strumento, cioè una lettura e una scrittura per scheda più gli elenchi, e ogni turno rimanda il contesto intero, comprese le istruzioni di progetto che ogni agente carica all'avvio. Ne segue che la leva più forte è ridurre i turni. Uno script prepara in un solo file gli estratti del lotto e le informazioni che servono, l'agente risponde con un solo testo strutturato, e un altro script scrive le schede. Questa leva è stata misurata il giorno stesso su un terzo lotto, e la misura ha corretto il modo in cui il costo va letto. Le chiamate di strumento sono scese da 118 a 13, ma il numero di token della notifica solo da 447 132 a 410 272, perché quel numero conta la cache scritta e l'uscita, non la cache letta. Le trascrizioni degli agenti danno la ripartizione.

| Lotto | Turni | Cache scritta | Cache letta | Uscita |
|---|---|---|---|---|
| estratti da 1500 parole | 61 | 418 003 | 4 942 017 | 37 710 |
| estratti da 800 parole | 51 | 355 293 | 3 754 050 | 37 344 |
| un pacchetto per agente | 19 | 336 792 | 1 031 208 | 29 421 |

La riduzione dei turni ha tagliato la cache letta di quasi cinque volte. Con i pesi del listino pubblico, 1,25 per la cache scritta, 0,1 per la cache letta e 5 per l'uscita del modello economico, il costo equivalente scende del 44 per cento circa: è un'inferenza sui pesi, e la quota di un abbonamento può pesare diversamente. La cache scritta resta invece quasi costante, circa 67 000 token per agente, perché è il contesto fisso che ogni agente scrive all'avvio. La regola che ne discende vale oltre questo caso: il numero di token di una notifica non è il costo, e due configurazioni si confrontano sulla ripartizione nelle trascrizioni. La leva successiva, ancora da misurare, è usare meno agenti con pacchetti più grandi, perché ogni agente in meno toglie il suo contesto fisso. Lo strumento `tools/scrivi-schede.py` del progetto d'origine, che scrive le schede dal JSON degli agenti, è il complemento di `estratti-lotto.py` per questa forma.

Misura aggiunta lo stesso giorno. Un quarto lotto da 50 schede, con 2 agenti da 25 estratti invece di 5 da 10, ha usato 10 turni, 181 144 token di cache scritta, 599 298 di cache letta e 18 760 di uscita. Con gli stessi pesi il costo equivalente è di circa 380 000, il 43 per cento in meno del lotto con 5 agenti, circa 7 600 per scheda. La leva dei pacchetti più grandi quindi funziona. Ha però un segnale da sorvegliare: nessuna scheda è stata giudicata di utilità nulla, contro 9-10 su 50 nei lotti precedenti. Prima di adottare pacchetti grandi come forma stabile si rilegge a campione una parte dei giudizi più alti.

La terza: il lavoro meccanico resta nel codice. La scelta dei documenti, l'esclusione dei documenti personali e il taglio degli estratti li fa `tools/estratti-lotto.py`, e il modello vede soltanto gli estratti. Anche la correzione dei campi mancanti, che un agente su cinque ha omesso, si fa da codice confrontando le schede con l'elenco del lotto.

## Che cosa ha dimostrato il primo lotto reale

Dieci elementi su un corpus di trecentosettantuno, undici minuti, una flotta secondaria. Tre esiti, e due sono lezioni.

**Il presidio ha dato il numero vero mentre il registro dichiarava il falso.** L'agente ha scritto `"stato": "completato"`, che nello schema non esiste: il vocabolario ammette `fatto`. Un presidio che consultasse il campo di stato avrebbe riportato **zero elementi conclusi**, perché quel valore gli è sconosciuto, mentre sul disco c'erano dieci artefatti validi. Guardando il disco ha riportato **dieci conclusi** e ha segnalato a parte la deviazione di vocabolario.

> È la dimostrazione pratica del principio: **la verifica sull'artefatto è robusta anche a un agente che usa parole diverse dalle tue**, mentre la verifica sullo stato dichiarato sbaglia in entrambe le direzioni, e il falso negativo è insidioso quanto il falso positivo perché porta a rifare lavoro già fatto.

**Il vocabolario va dato per esteso nel mandato.** Scrivere "metti stato fatto" non basta: l'agente sceglie un sinonimo ragionevole e lo schema si sporca. Il mandato elenca i valori ammessi, letteralmente, e dichiara che sono un insieme chiuso.

**L'approvazione a richiesta è incompatibile con il lavoro a lotti.** Con `approval_policy = "on-request"` l'agente si è fermato a ogni comando che scrive, in attesa di una persona. Su dieci elementi è un fastidio; su trecentosettantuno sarebbe una persona incatenata a un pulsante, che è l'opposto del motivo per cui il lavoro era stato spostato su un'altra flotta. Per i lotti si avvia con l'approvazione disattivata, così che i comandi dentro il perimetro passino e quelli fuori **falliscano** invece di chiedere. Chi approva concede anche persistenza a famiglie di comandi, quindi le esecuzioni successive sono meno interrotte, ma la prima resta presidiata.

## Classificare molti elementi piccoli su etichette chiuse

È un caso diverso dal corpus di documenti, e il pacchetto lo copre con uno strumento proprio. Gli elementi sono migliaia e piccoli, come le voci di una bibliografia o i file di un disco, e vanno assegnati a un insieme chiuso di categorie. Un artefatto per elemento qui sarebbe burocrazia. La forma giusta è un artefatto per lotto, cioè una mappa JSON `{chiave: {campo: [etichette]}}` scritta dall'agente su disco. La sua verifica può essere più forte di quella di `registro.py`: il contratto chiuso rende misurabili la completezza e la forma dell'esito, oltre alla sua presenza.

Il caso che l'ha insegnato è del 2026-10-05, in un progetto istanziato: una biblioteca di 8194 fonti da distribuire su un albero di 148 gruppi. Le misure che seguono vengono dai file del lavoro, e i token dalle notifiche di fine agente della piattaforma.

La sequenza ha quattro passi.
- Prima le regole deterministiche, e all'agente solo il residuo. Una tabella di cartelle, le parole chiave sul titolo e le stesse parole contate nel testo convertito hanno classificato l'82% delle voci, e all'agente ne sono rimaste 1513.
- Poi il mandato a contratto chiuso, nella forma riportata qui sotto.
- Poi il modello economico, in lotti paralleli.
- Infine `tools/valida-etichette.py` sull'esito di ogni lotto, prima di usarlo.

| Lotto | Voci | Estratto del testo | Mancanti | Etichette inventate | Vuote | Token per voce |
|---|---|---|---|---|---|---|
| 1 | 379 | no | 0 | 0 | 104 (27%) | 285 |
| 2 | 379 | no | 0 | 0 | 2 (1%) | 312 |
| 3 | 379 | no | 5 | 24 | 9 (2%) | 281 |
| 4 | 376 | no | 0 | 0 | 88 (23%) | 245 |
| 5, residuo del residuo | 173 | 500 caratteri | 0 | 0 | 0 | 630 |

Le lezioni sono cinque, e la prima è la più costosa da ignorare.

**Il resoconto dell'agente non è una misura.** L'agente del lotto 3 ha dichiarato di aver scritto 500 voci su un ingresso di 379, e il file ne conteneva 374. Si legge il file, non il messaggio.

**Lo stesso mandato dà esiti molto diversi.** Quattro agenti identici con istruzioni identiche hanno lasciato senza etichetta fra l'1% e il 27% delle voci. L'agente del lotto peggiore ha dichiarato di aver classificato "per corrispondenza di parole chiave": si è scritto uno script invece di giudicare, e la scorciatoia ha prodotto le vuote. Il tasso di vuote è quindi un segnale misurabile, e oltre una soglia il lotto si rilancia. Il mandato vieta la scorciatoia in modo esplicito. Nel caso osservato i lotti 1, 3 e 4 erano stati accettati a vista, e il danno è stato evitato solo perché i loro residui sono stati ripresi nella tornata successiva: l'esito va validato prima di unirlo, non dopo.

**Il contenuto vale il suo prezzo sul residuo.** Con le prime 500 lettere del testo, oltre a titolo, sede e cartella, il costo per voce è salito di 2,2 volte. Sulle 173 voci più difficili, cioè quelle che regole e prima tornata non avevano saputo classificare, le vuote sono scese a zero. Ne segue una politica a due passaggi: il titolo per la massa, l'estratto per il residuo.

**Le regole restano sovrane.** L'esito dell'agente si applica solo alle voci che le regole deterministiche non hanno assegnato. Ogni etichetta assegnata dall'agente porta nello stato intermedio il motivo `agente`, così che si riconosca e si corregga a mano senza rilanciare nulla.

**Il parallelismo ha compresso il tempo e non il costo.** Quattro lotti in parallelo hanno chiuso in circa cinque minuti, il tempo del lotto più lento, contro i circa dodici della somma dei loro tempi, misurati sulle notifiche di fine agente in 165, 285, 160 e 116 secondi, con lo stesso consumo, come prescrive la regola del pacchetto.

Il mandato, da copiare e adattare:

```text
Classifica ogni elemento di <ingresso.json> (campi: chiave, titolo, <altri>) usando SOLO
le etichette elencate in <etichette.json>, copiate esattamente. Giudica ogni elemento
uno per uno leggendone i campi: non scrivere programmi o regole per parole chiave.
Se un elemento non e' materiale pertinente usa <etichetta di scarto>; usa [] solo se e'
davvero impossibile giudicare. Scrivi con lo strumento di scrittura <uscita.json>, una
mappa {chiave: {campo: [etichette]}} con esattamente una voce per ogni chiave
dell'ingresso. Nessun altro file. Rispondi solo con il numero di chiavi scritte.
```

E la validazione, sull'esito di ogni lotto:

```text
python tools/valida-etichette.py --ingresso lotto-1.json --uscita esito-1.json --etichette etichette.json --campione 20 --scrivi unione.json
```

Se i dati vengono da un disco privato, ingresso, esito e unione stanno in una cartella ignorata da git, perché i titoli sono già un dato.

## Rapporto con le regole del sistema

Attua `rules/token-economy.md` sul caso del corpus grande, e non la duplica: la disclosure progressiva resta la riduzione del costo per elemento, questo pacchetto aggiunge la riduzione del **numero** di elementi e la sopravvivenza alla fine della finestra.

Obbedisce alla sezione 17 nominando il proprio presidio e dichiarando cosa non copre; alla sezione 19 non fidandosi dello stato dichiarato; alla sezione 20 componendosi con `doc-ingest` e `ccusage` invece di rifarli.

## Vincoli e onestà

Il presidio **non giudica la qualità** di un esito, e non può farlo. `valida-etichette.py` ne misura la completezza e la forma, cioè chiavi ed etichette, ma un'etichetta ammessa non è un'etichetta giusta: la giustezza resta affidata alla rilettura del campione.

Il registro **non impedisce** a un agente di lavorare fuori da esso: è un contratto, non una prigione. Se l'agente non lo aggiorna, il presidio se ne accorge alla passata successiva, non durante.

L'instradamento fra flotte **presuppone che esistano**, con identità separate e configurate. Su una macchina con una sola flotta la regola è inerte e il resto del pacchetto funziona comunque.

L'aritmetica in apertura è un **ordine di grandezza con assunto dichiarato**, non una misura: serve a decidere se il lavoro entra o no in una finestra, e va rifatta con il consumo reale del proprio progetto.
