---
name: build-roadmap
description: >
  Crea o aggiorna LEARNER_PROFILE.md alla radice del progetto: raccoglie topic, obiettivo,
  categoria pedagogica, livello di partenza, tempo disponibile, profilo cognitivo opt-in e
  preferenze di stile, poi costruisce o aggiorna la roadmap del topic secondo il template
  pedagogico della categoria inferita. Invocata da /profile alla prima sessione o quando il
  learner vuole cambiare topic o aggiornare le proprie preferenze.
disable-model-invocation: true
---

## Premessa

Questa skill copre l'onboarding di sessione (sezione 6) e la scelta del template pedagogico per categoria (sezione 4) di `.claude/context/learning-agent-reference.md`, che resta la fonte di verità per il contenuto delle domande e dei tre template. Non eroga alcuna lezione: produce lo stato e la roadmap entro cui `learn-topic` e `review-session` operano.

## Domande da porre all'utente

Se non già chiarite in conversazione o già presenti in `LEARNER_PROFILE.md`, la skill pone esplicitamente, idealmente con opzioni a bottoni piuttosto che testo libero quando lo strumento di domanda a scelta lo consente, le seguenti domande prima di procedere, senza assumere risposte di default.

Qual è il topic e l'obiettivo dichiarato, per esempio "React per lavoro" o "spagnolo conversazionale per un viaggio". Qual è la categoria del topic: lingua straniera, linguaggio o framework di programmazione, o materia concettuale; se l'inferenza automatica dal topic dichiarato non è chiara, la domanda va posta esplicitamente invece di indovinare, perché la categoria determina quale dei tre template pedagogici della sezione 4 si applica. Qual è il livello di partenza: principiante, intermedio o avanzato. Quanto tempo ha a disposizione il learner per sessione e con quale frequenza, perché guida la dimensione dei chunk e il ritmo di ripasso. Il learner segnala, su base opt-in, ADHD, spettro autistico, dislessia o nessun adattamento particolare: questa domanda si pone con il linguaggio neutro della sezione 5 del riferimento, chiarendo che non è una domanda clinica ma un'indicazione didattica che il learner può cambiare in qualsiasi momento. Quali preferenze di stile ha: visivo, testuale, hands-on, e se esistono interessi speciali da usare come lente per gli esempi. Infine, se un knowledge-base MCP o un Anki MCP sono già connessi al progetto, o se il learner vuole indicare dei file locali come knowledge base in loro assenza.

## Costruzione della roadmap

Una volta nota la categoria, la roadmap si costruisce secondo il template corrispondente della sezione 4 del riferimento, non con uno schema unico. Per una lingua straniera la roadmap è un elenco di unità tematiche (vocabolario di base, frasi di sopravvivenza, tempi verbali, conversazione) senza dipendenze rigide tra loro, dove l'ordine segue la frequenza d'uso più che la difficoltà. Per un linguaggio o framework di programmazione la roadmap è a dipendenze strette: ogni modulo dichiara esplicitamente quali moduli precedenti presuppone, sul modello osservato in curricula a sequenza rigida, e `learn-topic` non eroga un modulo se i suoi prerequisiti non risultano completati in `LEARNER_PROFILE.md`. Per una materia concettuale la roadmap privilegia la costruzione di intuizione e pattern prima della memorizzazione dei fatti, con più percorsi di soluzione ammessi invece di una sequenza obbligata.

La roadmap prodotta si registra in `LEARNER_PROFILE.md` come lista di moduli o unità con un identificatore stabile, così che il campo `progress.roadmap_module` possa riferirsi a un modulo preciso invece che a un numero che perde significato se la roadmap viene ricostruita.

## Output

Scrive o aggiorna `LEARNER_PROFILE.md` alla radice del progetto, nel formato descritto dal template in `../../LEARNER_PROFILE.md` di questo pacchetto: i campi `topic`, `category`, `level`, `session_minutes`, `cadence`, `cognitive_profile`, `style`, `special_interests` dalle risposte raccolte, i campi `kb_mcp` e `anki_mcp` con il nome del server connesso o `none`, e la roadmap del topic come sezione separata. Se il file esiste già e la skill viene invocata per aggiornare solo alcune preferenze, modifica in luogo solo i campi cambiati: non rigenera l'intero file e non tocca il campo `progress`, che è di competenza esclusiva di `tutor`.

## Vincoli

Non inferisce mai la categoria pedagogica in modo silenzioso quando il topic è ambiguo: chiede. Non genera roadmap di dimensione arbitraria senza aver raccolto tempo disponibile e cadenza, perché sono quei due valori a determinare la dimensione dei chunk secondo i modificatori della sezione 5, per esempio chunk più piccoli e più numerosi se è dichiarato ADHD. Non esegue `git add`, `commit` o `push`: le operazioni git restano all'utente.
