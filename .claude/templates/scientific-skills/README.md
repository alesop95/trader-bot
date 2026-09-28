# scientific-skills

> Pacchetto opzionale del sistema di progetto. Dà accesso alla raccolta `K-Dense-AI/scientific-agent-skills`, che è la più grande libreria di skill scientifiche pubblicata per lo standard aperto Agent Skills, senza installarne nemmeno una d'ufficio. Il pacchetto non è un installatore, perché un installatore esiste già a monte ed è migliore di qualunque cosa si scriverebbe qui: è la vista che manca per decidere quale skill prendere, e la procedura per prenderla senza saltare i tre controlli che la raccolta stessa chiede di fare.

## Che cosa è la raccolta

Centosessantasei skill, licenza del repository MIT, descritte in un articolo su arXiv con identificativo 2609.00065. Coprono bioinformatica e genomica, chemoinformatica e scoperta di farmaci, proteomica, ricerca clinica, imaging medico, apprendimento automatico, scienza dei materiali, fisica e astronomia, geospaziale, automazione di laboratorio, comunicazione scientifica e metodologia della ricerca, e portano accesso a oltre cento fra basi di dati pubbliche e servizi. Funzionano con qualunque agente che supporti lo standard, Claude Code compreso, e il repository è anche un pacchetto plugin valido.

Il punto che conta per un sistema come questo non è la dimensione ma la natura: non sono strumenti, sono conoscenza procedurale. Una skill su una libreria scientifica non aggiunge una capacità che l'agente non avrebbe, perché l'agente può già installare e usare qualunque pacchetto Python; aggiunge la documentazione curata e gli esempi verificati che rendono quel lavoro più affidabile. La raccolta lo dichiara esplicitamente, ed è una dichiarazione onesta che vale ripetere al gate, perché cambia la domanda da "mi serve questa capacità" a "faccio abbastanza spesso questo lavoro perché valga tenerne la procedura scritta".

## Che cosa istanzia

Due file, da copiare nel progetto ospite.

`tools/mappa-skill-scientifiche.py` va in `tools/`. Legge una copia locale della raccolta e produce la mappa: ogni skill con il suo autore, la sua licenza, se porti programmi eseguibili, che cosa fa, e se un pacchetto di questo sistema copra già quel terreno. Python 3, sola libreria standard, nessun segnaposto da sostituire tranne, quando il catalogo del progetto cambia, la tabella delle sovrapposizioni che vive dentro il file.

`MAPPA-SKILL-SCIENTIFICHE.md` è la mappa già generata, e si copia dove il progetto tiene i propri documenti. Non si scrive a mano e non si corregge a mano: si rigenera, ed è la ragione per cui porta in testa la riga che lo dice.

Va aggiunta una riga al `.gitignore` del progetto, perché la copia locale della raccolta è materiale di terzi e non entra nel repository.

```
.tmp-skills/
```

Va inoltre dichiarata una esclusione per la mappa generata, dove il progetto usi il pacchetto `fix-typography`: il documento riporta verbatim le descrizioni inglesi delle skill a monte, quindi porta i trattini lunghi di chi le ha scritte, e normalizzarli falserebbe una citazione oltre a essere disfatto dalla rigenerazione successiva. È lo stesso caso, e la stessa eccezione, del documento di riferimento copiato da fonte esterna nel pacchetto `academic-researcher`. L'esclusione si scrive in `tools/dashes-exclude.txt`, che pretende il motivo accanto al percorso.

E una voce di permesso, come per gli altri pacchetti che portano strumenti.

```
Bash(python tools/mappa-skill-scientifiche.py:*)
```

## Perché il pacchetto non installa nulla

Perché `gh skill install` lo fa già, e meglio. Prende una skill per volta, la mette nella cartella giusta per l'host in uso, registra la provenienza per la tracciabilità della catena di fornitura, e con `--pin` la blocca a un tag o a un commit invece di inseguire un ramo. Sono esattamente le tre proprietà che uno script scritto qui avrebbe dovuto reimplementare, e la regola del catalogo dice di non duplicare una funzione che il ferro sottostante offre già.

```
gh skill install K-Dense-AI/scientific-agent-skills scanpy
gh skill install K-Dense-AI/scientific-agent-skills --pin v2.68.0
gh skill update --all
```

Il comando è in anteprima e la sua interfaccia può cambiare: se un giorno cambia, cambia una riga di questo README, che è meno di quanto costerebbe mantenere un installatore proprio. Chi non usa `gh` ha le altre due vie che la raccolta documenta, cioè l'installatore comune degli Agent Skills e il caricamento come pacchetto plugin; la mappa che questo pacchetto produce serve allo stesso modo, perché parla di quali skill prendere e non di come.

## I tre controlli, e perché sono meccanici

L'avviso di sicurezza della raccolta dice tre cose, e le dice con una franchezza che merita di essere presa sul serio invece che scorsa: non installarle tutte, leggere il file di una skill prima di prenderla, e sapere che le skill contribuite da terzi non hanno avuto la stessa revisione di quelle della casa, perché il gruppo che mantiene la raccolta è piccolo e i contributi crescono. Aggiunge che le skill possono eseguire codice arbitrario, installare pacchetti, fare richieste di rete e modificare file, e che una skill scritta male o malevola può indirizzare un agente verso comportamenti dannosi.

Tutti e tre quei criteri sono verificabili guardando i file, e il programma di questo pacchetto li guarda. Sull'istanza letta al momento della scrittura di questo README, i numeri che ne escono sono questi, e sono il genere di cosa che nessuno scopre leggendo un elenco in prosa.

Centotrentasei skill sono della casa e trenta di altri autori, fra cui i quattro strumenti documentali di Anthropic, vendorati dalla raccolta con credito esplicito. Centosei portano una cartella di programmi eseguibili, cioè la maggioranza, ed è la classe per cui la raccolta suggerisce di passare uno scanner prima di installare. Cinque hanno licenza proprietaria e una è a uso non commerciale, dentro una raccolta il cui repository si presenta come MIT: la differenza non si nota finché non serve, e allora è tardi. Quattro non dichiarano alcuna licenza.

Lo scanner che la raccolta stessa indica si esegue sulla cartella della skill prima di installarla.

```
uv pip install cisco-ai-skill-scanner
skill-scanner scan .tmp-skills/skills/<nome> --use-behavioral
```

La procedura che ne discende, e che questo pacchetto considera la sua parte normativa, è in quattro passi. Si guarda la mappa e si sceglie una skill sola, quella che risponde a un lavoro che il progetto fa davvero e ripetutamente. Si legge il suo `SKILL.md` nella copia locale, per intero, perché è il documento che dirà all'agente che cosa fare. Se porta programmi eseguibili, o se l'autore non è la casa, le si passa lo scanner. E la si installa bloccata a una versione, mai inseguendo un ramo, perché una skill che cambia da sola cambia il comportamento dell'agente senza che nessuno abbia deciso niente.

## Le ventisette che questo sistema copre già

La mappa le marca una per una, ed è la parte che vale di più al gate perché è l'unica che non si potrebbe leggere a monte. Il terreno condiviso è quasi tutto nella comunicazione scientifica e nella gestione documentale: le skill di ricerca della letteratura, di gestione delle citazioni e di valutazione dei lavori toccano ciò che i pacchetti `academic-researcher`, `academix`, `semantic-scholar-mcp`, `refchecker-mcp`, `paperqa2` e `arxiv-cli` già fanno; quelle di lettura dei formati documentali toccano `doc-ingest` e `docx-to-docs`; i poster e i modelli di conferenza toccano `latex`; i diagrammi toccano `diagrams`; e la visualizzazione tocca la skill nativa di questo strumento.

La regola di scelta è quella generale del catalogo: dove il progetto ha già la capacità, la skill non si propone come duplicato, e al massimo si propone di allineare ciò che c'è. Il caso interessante è il contrario, ed è la ragione per cui la tabella esiste in entrambe le direzioni: un progetto scientifico che parta da qui potrebbe voler prendere la catena di là e non attivare `academic-researcher`, e la decisione va presa una volta e scritta, perché due sistemi di gestione delle citazioni che convivono producono due bibliografie che divergono.

## Al gate

Si propone a un progetto il cui dominio sia scientifico, e la domanda giusta non è "vuoi le skill scientifiche" ma "di quale settore si occupa questo progetto", perché la risposta seleziona quasi sempre una sola riga della tabella dei settori e rende la scelta piccola invece che enorme. A un progetto di sviluppo software non si propone: le skill di libreria valgono se si fa analisi di dati scientifici, non se si scrive un servizio.

Un caso intermedio merita una menzione perché è frequente e si perde: un progetto che non sia scientifico ma che produca documenti tecnici trova nella sezione della comunicazione scientifica alcune skill utili in sé, per esempio quelle sui poster e sulle presentazioni senza macro. Si offrono per quelle, dicendo che vengono da una raccolta scientifica, invece di offrire la raccolta intera.

Quando il pacchetto si attiva, il recap d'uso da mostrare è il clone parziale, la generazione della mappa, e la regola delle quattro mosse della sezione precedente. Senza quest'ultima il pacchetto si riduce a un elenco, e un elenco di centosessantasei voci invita esattamente al comportamento che l'avviso di sicurezza chiede di evitare.

## Rigenerare la mappa, e vedere che cosa è cambiato a monte

```
git clone --depth 1 --filter=blob:none --sparse https://github.com/K-Dense-AI/scientific-agent-skills.git .tmp-skills
git -C .tmp-skills sparse-checkout set skills
python tools/mappa-skill-scientifiche.py --da .tmp-skills --out docs/MAPPA-SKILL-SCIENTIFICHE.md
```

Il clone parziale prende i testi e non gli allegati, e pesa una trentina di megabyte contro i duecento e più dell'archivio completo. Per aggiornarlo si esegue `git -C .tmp-skills pull` e si rigenera: il diff del file prodotto dice che cosa è cambiato, quali skill sono nate e quali hanno cambiato licenza o autore. È la stessa strategia di confronto a costo zero del pacchetto `claude-code-handoff`, ed è il motivo per cui la mappa è un file generato e versionato invece di una lettura da rifare ogni volta.

Per guardare una porzione senza rigenerare niente c'è il filtro a schermo.

```
python tools/mappa-skill-scientifiche.py --da .tmp-skills --settore genomics
```

## Collaudo

```
python tools/mappa-skill-scientifiche.py --self-test
```

Tredici controlli contro un albero sintetico e senza rete. Coprono la lettura del frontmatter, e in particolare il caso che falserebbe tutto in silenzio, cioè lo stesso autore scritto una volta con le virgolette e una senza, che senza normalizzazione diventa due autori e sposta il conteggio su cui poggia il gate; il riconoscimento di una licenza proprietaria annegata in una frase; la riduzione alla stessa forma delle grafie diverse della stessa licenza; il rilevamento dei programmi eseguibili dalla forma della cartella; la lettura dei settori dal README a monte con la dichiarazione esplicita dello scarto fra quanto dichiarano e quanto c'è; e la barra verticale dentro una descrizione, che senza protezione spezzerebbe la tabella Markdown prodotta senza che nessuno se ne accorga finché non la si guarda resa.
