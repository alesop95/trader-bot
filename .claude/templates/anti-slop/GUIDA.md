# Guida ai segni del testo e delle interfacce generate

> Documento tecnico-didattico del pacchetto `anti-slop`. Descrive quattordici segni ricorrenti dei contenuti generati da un modello, sei nella prosa e otto nelle interfacce, e per ciascuno dice che cosa è, perché si produce, come lo riconoscono gli strumenti del pacchetto e che cosa si scrive o si disegna al suo posto. Le sigle fra parentesi quadre rimandano al registro `FONTI.md`. I codici P e U sono quelli che stampano `tools/lint-prosa.py` e `tools/lint-ui.py`.

## Da dove viene l'elenco, e che cosa non dimostra

L'elenco nasce da un carosello di quattordici schede, "14 Signs That Scream AI Slop", che l'utente ha portato come esempio di ciò che il template non deve produrre [S1]. Il carosello indica i segni ma non ne spiega la causa né cita fonti, quindi ciascun segno è stato riscontrato su fonti primarie prima di entrare qui: il catalogo della comunità di Wikipedia per la prosa [F01], la skill ufficiale di Anthropic per le interfacce [F06] e la guida di Anthropic al prompting estetico [F07], con il sostegno di studi e di linee guida di usabilità dove esistono. Un segno che nessuna fonte conferma lo dice nella propria voce.

Una premessa vale per tutto il documento, e la dichiarano le fonti stesse. I rilevatori automatici di testo generato hanno tassi d'errore non trascurabili [F01], sono distorti contro chi scrive in una lingua che non è la propria [F05], e il fornitore che aveva reso popolare la misura della variabilità ha smesso di affidarsi soltanto a quella [F03]. Anche il giudizio umano, secondo la sezione sulle avvertenze della pagina di Wikipedia, non distingue un testo generato da uno umano meglio del caso [F01]. Da qui la scelta degli strumenti del pacchetto: cercano segni osservabili, ciascuno con la sua ragione, e restituiscono un elenco da rileggere. Nessuna uscita dice "questo testo è generato", e un segno isolato vale poco; la stessa pagina lo scrive del trattino lungo, utile "in combination with other indicators, not by itself" [F01].

C'è poi un motivo per cui questi segni contano anche quando il testo lo ha scritto una persona: sono i punti in cui la forma ha preso il posto del contenuto. Un'autorità senza nome non si verifica, una triade riempie lo spazio di un argomento che ne aveva due, una card dentro una card aggiunge un bordo senza aggiungere una gerarchia. Toglierli migliora il testo per chi legge, qualunque sia l'origine.

## La forma delle voci

Ogni segno ha gli stessi campi. *Che cosa è* lo descrive. *Perché si produce* ne dà la causa dove una fonte la dichiara. *Come si riconosce* dice quale codice dello strumento lo trova e con quale soglia. *Che cosa si fa invece* è la parte che conta. *Prima e dopo* mostra un esempio breve.

## Prosa

### P1, paragrafi e frasi della stessa misura

**Che cosa è.** Paragrafi quasi uguali per lunghezza, fatti di frasi quasi uguali fra loro, come nell'esempio del carosello dove due paragrafi di quattro frasi si somigliano al punto di sembrare stampati con lo stesso stampo [S1].

**Perché si produce.** La misura corrispondente si chiama variabilità, *burstiness*: quanto variano nel documento la struttura e la prevedibilità delle frasi [F03]. La scrittura umana varia molto, un modello produce una regolarità costante [F03].

**Come si riconosce.** P1. Sul singolo paragrafo questo segno non discrimina, e lo si è misurato: il 2026-09-23 il paragrafo generato del carosello aveva una variazione delle lunghezze delle frasi di 0,18, e paragrafi scritti a mano nel template stavano fra 0,11 e 0,22. Discrimina invece la quota di paragrafi uniformi nel documento: al massimo 0,20 nei file del template che si possono misurare, 1,00 nel campione. Lo strumento segnala quindi il documento in cui almeno il sessanta per cento dei paragrafi misurabili è uniforme, e i documenti con quattro o più paragrafi di misura quasi identica. Il campione di calibrazione è piccolo, e la soglia va rivista quando se ne avranno altri.

**Che cosa si fa invece.** Si lascia che la lunghezza segua il contenuto. Un'idea semplice sta in una frase corta. Una condizione con due eccezioni ha bisogno di una frase lunga, e va bene così.

**Prima e dopo.** "Il sistema salva i dati. Il sistema controlla i dati. Il sistema invia i dati." diventa "Il sistema salva i dati, li controlla prima di inviarli e, se il controllo fallisce, li trattiene finché qualcuno non guarda."

### P2, l'autorità senza nome

**Che cosa è.** "Gli esperti ritengono", "studi dimostrano", "i ricercatori hanno scoperto", senza dire quali esperti, quale studio, quale ricerca [S1].

**Perché si produce.** Wikipedia lo cataloga come *weasel wording*: i modelli "tend to attribute opinions or claims to some vague authority", con parole da sorvegliare come "Experts argue", "Observers have cited", "Industry reports" [F01].

**Come si riconosce.** P2 cerca le formule italiane e inglesi di attribuzione generica e le segnala solo se nella stessa frase manca un rimando, cioè un collegamento, una nota, un anno fra parentesi, una sigla di fonte.

**Che cosa si fa invece.** Si nomina la fonte, oppure si toglie l'attribuzione e si dice la cosa in prima persona, assumendosene la responsabilità. Se la fonte non c'è, l'affermazione è un'inferenza e va marcata come tale secondo la regola sull'onestà del contenuto.

**Prima e dopo.** "Studi dimostrano che il 67% degli utenti è d'accordo" diventa "Nel sondaggio di marzo sui 212 clienti attivi, 142 hanno risposto di sì", con il rimando al sondaggio.

### P3, il parallelismo negativo

**Che cosa è.** "Non si tratta di risparmiare tempo, si tratta di cambiare il modo di lavorare", "Non è X: è Y", "It's not just X, it's Y" [S1].

**Perché si produce.** Wikipedia lo registra come *negative parallelism* in tre forme, "Not just X, but also Y", "Not X, but Y" e "Y rather than X" [F01]. La figura costruisce un contrasto con un'opinione che nessuno aveva espresso, e fa sembrare profonda un'affermazione semplice.

**Come si riconosce.** P3 cerca le forme negative contrapposte in italiano e in inglese. Il correlativo "non solo... ma anche", che in italiano è ordinario, si segnala solo quando torna tre volte nello stesso file.

**Che cosa si fa invece.** Si afferma direttamente. Il contrasto si tiene quando qualcuno ha davvero sostenuto la tesi opposta, e allora conviene nominarlo.

**Prima e dopo.** "Non è una questione di strumenti: è una questione di metodo" diventa "Il problema è il metodo: con lo stesso strumento, due gruppi hanno ottenuto risultati opposti."

**Una nota su questo template.** La prima corsa di P3 sugli stessi file di sistema ha trovato quattordici occorrenze della forma "non è X: è Y" in sei file, alcune scritte nella stessa giornata in cui è nato questo pacchetto. Il segno era dentro il sistema che lo descrive. Una revisione dello stesso giorno ha riscritto in forma affermativa tutte le occorrenze nel template, comprese quelle emerse dopo aver ripristinato gli accenti scritti con l'apostrofo, che il rilevatore non vedeva: a revisione conclusa P3 non segnala niente in nessun file del template.

### P4, tutto in tre

**Che cosa è.** "Veloce. Semplice. Potente.", "Pianifica, costruisci, cresci", e documenti in cui quasi ogni elenco ha tre voci [S1].

**Perché si produce.** "LLMs overuse the rule of three", dal gruppo di aggettivi alla serie di tre frasi brevi, e la usano "to make superficial analyses appear more comprehensive" [F01].

**Come si riconosce.** P4 segnala tre frasi di una o due parole di fila, e i documenti in cui almeno il settanta per cento di sei o più elenchi ha tre elementi. Misurata il 2026-09-23 sui file di sistema del template, cioè le regole sotto `.claude/rules/`, `PROJECT-SYSTEM.md`, `README.md`, `GUIDA-USO.md` e `CASE-STUDIES.md`, la seconda condizione scatta in sette file; in `PROJECT-SYSTEM.md` gli elenchi di tre erano 37 su 49. La revisione ha riscritto le triadi retoriche e ha lasciato quelle che elencano tre cose reali, come le tre primitive di un server MCP o tre cause distinte, e in `PROJECT-SYSTEM.md` il conto è sceso a 33 su 44: la soglia resta superata, e va bene così, perché lo scopo è la prosa e non il numero. Lo strumento riconosce come elenco una serie di voci di una o due parole separate da virgole e chiuse da una congiunzione, e scambia ancora per elenco qualche proposizione breve: la quota va letta come ordine di grandezza.

**Che cosa si fa invece.** Si contano le cose che ci sono davvero. Se sono due, si scrivono due; se sono cinque, cinque.

**Prima e dopo.** "Più veloce, più sicuro, più semplice" diventa "Più veloce del trenta per cento sulla stessa macchina", se la sicurezza e la semplicità non sono state misurate.

### P5, il gergo messo lì per sembrare umani

**Che cosa è.** "Tbh", "kinda", "lol", "fr" in un testo che non è una chat, per dare un tono spontaneo che il resto del testo non ha [S1].

**Perché si produce.** Il carosello lo descrive come tentativo di far sembrare umano un testo generato [S1]. Nessuna delle fonti lette lo cataloga con questo nome; resta un segno riportato dalla fonte visiva e non confermato da una fonte primaria.

**Come si riconosce.** P5, con un elenco breve di abbreviazioni e intercalari da chat in inglese e in italiano.

**Che cosa si fa invece.** Si scrive nel registro del destinatario. Un registro informale va bene quando è quello del testo intero, e non come spezia.

### P6, il lessico di maniera

**Che cosa è.** Parole che i testi generati usano molto più dei testi umani dello stesso genere: in inglese "delve", "tapestry", "testament", "pivotal", "underscore", "showcase", "meticulous" e altre [F01].

**Perché si produce.** Uno studio su oltre quindici milioni di abstract biomedici ha misurato un aumento improvviso di certe parole di stile dopo la comparsa dei modelli linguistici, e ne ha dedotto che almeno il 13,5% degli abstract del 2024 è passato da un modello [F04]. La pagina di Wikipedia raggruppa queste parole per generazione di modelli e avverte che il segnale invecchia: "delve" è crollata nel 2025 [F01].

**Come si riconosce.** P6 segnala a ogni occorrenza le parole distintive, e le parole comuni come "crucial", "key", "robust" solo quando la loro densità supera otto per mille parole, perché un testo tecnico le usa legittimamente. Gli equivalenti italiani, come "gioca un ruolo cruciale" o "nel panorama attuale", sono proposti per analogia e non misurati da nessuna fonte: lo strumento li marca come indizi deboli.

**Che cosa si fa invece.** Si sceglie la parola più precisa disponibile. "Svolge un ruolo cruciale" dice meno di qualunque verbo che descriva il ruolo.

**Aggiornamento.** L'elenco va rivisto a ogni aggiornamento della pagina di Wikipedia, perché le parole cambiano con i modelli [F01].

### Un segno che il template presidia già: il trattino lungo

La pagina di Wikipedia osserva che i testi generati usano il trattino lungo più dei testi non professionali dello stesso genere, spesso circondato da spazi, e riporta uno studio del luglio 2026 secondo cui fra i modelli contemporanei solo Claude lo usa più degli scrittori professionisti [F01]. La regola `interaction-style.md` lo vieta già e `fix-dashes.py` del pacchetto `fix-typography` lo verifica, quindi `lint-prosa.py` non lo duplica.

## Interfacce

### U1, sfondo crema, testo nero, accento ambra

**Che cosa è.** Uno sfondo chiaro e caldo, testo quasi nero e pulsanti ambra, arancio o terracotta [S1].

**Perché si produce.** La skill ufficiale di Anthropic per il frontend nomina come cliché "a warm cream background (near #F4F1EA) with a high-contrast serif display and a terracotta or warm-clay accent (often near #D97757)" [F06]; la guida di Anthropic al prompting spiega che senza indicazioni il modello converge su scelte "on distribution", e che questo produce l'estetica che gli utenti chiamano "AI slop" [F07]. Anche `taste-skill` bandisce la palette crema con ottone e argilla [F08].

**Come si riconosce.** U1, a livello di progetto: uno sfondo chiaro caldo e un accento caldo saturo nello stesso insieme di file, nei valori esadecimali o nelle classi di utilità.

**Che cosa si fa invece.** Si parte dal marchio o dal contenuto. Se il marchio è davvero caldo, la scelta si scrive nella documentazione del progetto con la sua ragione, e smette di essere un default.

**Contrasto.** Il testo bianco su un ambra come `#f59e0b` ha un rapporto di contrasto di circa 2,15:1, e su un terracotta come `#D97757` di circa 3,12:1, entrambi sotto il 4,5:1 che il criterio WCAG 1.4.3 richiede per il testo normale [F12]. Il testo nero sullo stesso ambra arriva a circa 9,78:1. U9 misura questo rapporto dove testo e sfondo sono dichiarati nella stessa regola.

### U2, la sezione in tre passi

**Che cosa è.** "Come funziona" in tre passi numerati 01, 02, 03, con tre icone e tre verbi [S1].

**Perché si produce.** È la regola del tre applicata al layout [F01], e `taste-skill` bandisce come generica "the generic 'three identical cards horizontally' feature row" [F08].

**Come si riconosce.** U2: un titolo come "come funziona" o "how it works" insieme ai tre marcatori numerati.

**Che cosa si fa invece.** Si mostra il processo reale, con il numero di passi che ha. Se il processo non ha passi, la sezione non serve.

### U3, una parola del titolo in corsivo serif

**Che cosa è.** Un titolo in cui una sola parola è in corsivo, grande, in un carattere serif da titolo [S1].

**Perché si produce.** La skill di Anthropic cita "Accenting just a single word or phrase in a headline, like putting one word in italic/bold" [F06]; `taste-skill` indica Fraunces e Instrument Serif come "the two LLM-favorite display serifs" [F08].

**Come si riconosce.** U3: un h1 o h2 che contiene un elemento em o i, o una classe italic, oppure uno span che isola una parte breve del titolo, cioè la stessa enfasi ottenuta con un colore invece che con il corsivo. U10 segnala i caratteri indicati dalle fonti.

**Che cosa si fa invece.** Si costruisce la gerarchia con la dimensione e il peso dell'intero titolo. Un'enfasi interna si usa quando quella parola è davvero il punto, e allora raramente è in un titolo.

### U4, l'etichetta minuscola sopra ogni titolo

**Che cosa è.** Un'etichetta in maiuscolo spaziato, "IL NOSTRO APPROCCIO", sopra ogni titolo, anche dove non aggiunge niente [S1].

**Perché si produce.** La skill di Anthropic la nomina come "tracked-out ALL-CAPS eyebrow label above every heading" [F06]; `taste-skill` ne ammette al massimo una ogni tre sezioni [F08].

**Come si riconosce.** U4: più di un'etichetta maiuscola spaziata ogni tre titoli nello stesso file, riconosciuta sia dalle classi di utilità sia da una regola CSS del file con maiuscolo e spaziatura delle lettere; nel secondo caso contano solo gli elementi seguiti subito da un titolo, perché un badge o una didascalia maiuscola non sono etichette sopra un titolo.

**Che cosa si fa invece.** Si toglie l'etichetta e si lascia che il titolo dica da solo di che cosa parla la sezione. Si tiene dove orienta davvero, per esempio la categoria di un articolo in un elenco misto.

### U5, card dentro card

**Che cosa è.** Contenitori con bordo, raggio e ombra annidati uno nell'altro, tre livelli per mostrare un numero [S1].

**Perché si produce.** La skill di Anthropic nomina "content chopped into identical rounded cards, one border-radius on everything regardless of hierarchy, the same soft grey shadow" [F06]. La letteratura di usabilità spiega perché è un difetto e non solo un gusto: le card servono per "collections of heterogeneous items" e sono "less scannable than lists" [F10], e per separare due elementi conviene resistere alla tentazione del bordo, perché troppi bordi rendono il disegno "busy and cluttered" [F11].

**Come si riconosce.** U5: tre o più contenitori a card uno dentro l'altro, riconosciuti dal nome della classe o dalla combinazione di raggio con bordo o ombra.

**Che cosa si fa invece.** Si separa con lo spazio, con uno sfondo diverso o con un'ombra leggera, uno strumento alla volta [F11]. Una card si usa per un elemento di una collezione eterogenea, e un livello basta.

### U6, le icone scontate

**Che cosa è.** Il fulmine per "veloce", lo scudo per "sicuro", il grafico a barre per "analisi", il puzzle per "integrazioni", la cuffia per "supporto" [S1].

**Perché si produce.** Sono le associazioni più frequenti, quindi le più probabili. La ricerca di usabilità aggiunge che la comprensione di un'icona "is based on previous experience", e che un'icona senza etichetta visibile è ambigua [F09].

**Come si riconosce.** U6: quattro o più icone di quel gruppo importate nello stesso file dalle librerie più comuni.

**Che cosa si fa invece.** Si chiede che cosa l'icona aggiunga al testo accanto. Se non aggiunge niente, si toglie; se serve, si sceglie un'icona che dica qualcosa del prodotto e si tiene l'etichetta visibile [F09].

### U7, la decorazione che non riguarda il prodotto

**Che cosa è.** Elementi aggiunti perché fanno scena: la finta finestra di terminale con "Initializing..." in un'applicazione di produttività che non ha una riga di comando [S1].

**Perché si produce.** La guida di Anthropic nomina "Cookie-cutter design that lacks context-specific character" [F07]. Il caso specifico della finta finestra non è catalogato da nessuna fonte letta; resta un segno riportato dalla fonte visiva.

**Come si riconosce.** U7 riconosce solo il caso più riconoscibile, i tre pallini colorati di una finestra finta, e lo segnala come domanda: serve al prodotto?

**Che cosa si fa invece.** Ogni elemento della pagina deve rispondere a una domanda dell'utente. Se non ne trova una, va via.

### U8, lo stesso layout in ogni sezione

**Che cosa è.** Sezioni o slide diverse con la stessa struttura: titolo, riga di supporto, immagine, pulsante [S1].

**Perché si produce.** La guida di Anthropic nomina "Predictable layouts and component patterns" [F07].

**Come si riconosce.** U8 confronta lo scheletro dei primi tag interni di ogni sezione e segnala tre o più sezioni con la stessa struttura. Una classe comune non basta, perché è normale pratica CSS. Sulle pagine HTML del template stesso il controllo trova una pagina di catalogo con undici sezioni identiche: lì la ripetizione è corretta, perché i dati sono omogenei, e la risposta giusta è scriverlo. L'altra pagina aveva invece palette crema e ambra, una frase del titolo isolata e colorata e un'etichetta sopra ogni titolo, ed è stata ridisegnata; la misura del contrasto ha trovato nella palette vecchia due coppie sotto la soglia WCAG, le note a piè a 2,88:1 e le date in ambra a 3,64:1.

**Che cosa si fa invece.** Si lascia che la struttura segua il contenuto di ciascuna sezione. Dove i dati sono davvero omogenei, una tabella o un elenco servono meglio di una serie di card [F10].

## Come si usa, in scrittura e in revisione

In scrittura vale la regola: la prosa segue `interaction-style.md`, che ora nomina i sei segni della prosa, e un'interfaccia segue `design-non-generico.md`, che il pacchetto istanzia nei progetti con frontend. In revisione si lanciano i due strumenti sui file cambiati e si rilegge ciò che segnalano. Nessuno dei due corregge da sé, per una ragione precisa: ogni segno ha una sostituzione che dipende dal contenuto, e una sostituzione meccanica produrrebbe un segno nuovo al posto di quello vecchio.

Le due skill esterne del catalogo restano complementari. `humanizer` riscrive un testo applicando il catalogo di Wikipedia [F02], `taste-skill` guida la generazione di un'interfaccia [F08]; questo pacchetto si limita a misurare, e spiega che cosa ha misurato. Si usano insieme: prima si genera o si riscrive con una delle due, poi si verifica con gli strumenti di qui.
