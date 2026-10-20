---
name: retrospettiva
description: >
  Rilegge la sessione in corso alla ricerca dei punti in cui l'agente ha arrancato, e per
  ciascuno propone una correzione dell'ambiente di lavoro, non del codice: un controllo
  automatico, un puntatore nell'indice, una regola chiarita o un'istruzione da togliere.
  Si lancia a mano alla fine di una sessione faticosa, prima di chiudere, perché il wipe
  cancella la trascrizione. Propone soltanto: non modifica niente finché l'utente non
  sceglie, e non esegue mai git add, commit o push.
disable-model-invocation: true
---

## Che cosa fa, e da dove viene

La skill è l'adattamento di `retro` della raccolta `mattpocock/skills`, licenza MIT, fatto il 2026-10-20. L'idea di partenza è la stessa: guardare come è stato fatto il lavoro invece di che cosa è stato prodotto, e chiedersi che cosa nell'ambiente ha permesso a un errore di accadere, così che la sessione successiva non lo ripeta. Cambiano le sedi in cui le correzioni atterrano, che qui esistono già, e il canale con cui una correzione utile a più progetti risale al template.

Vale solo per la sessione in cui si lancia. Non è una memoria fra sessioni: ciò che sopravvive sono le correzioni scelte, scritte nei file del progetto. Una sessione liscia non ha niente da insegnare, e lanciarla lì produce consigli che nessuno ha chiesto.

## Passo 1 - Contare, prima di giudicare

```
python .claude/templates/tools/retro-segnali.py --json _notes/retrospettiva/segnali.json
```

Lo strumento legge la trascrizione della sessione più recente del progetto e conta, senza modello, i segni di fatica: comandi falliti, chiamate negate, file letti più volte, ricerche ripetute, risultati voluminosi, correzioni e interruzioni dell'utente, ciascuno con il turno e un estratto. Se dice che la trascrizione non esiste, la sessione è già stata cancellata dal wipe e la retrospettiva non si può fare: lo si dice, senza ricostruire a memoria.

I segni sono indizi, non riscontri. Un file riletto tre volte può essere un file che si stava modificando; una frase con un «no» può essere una risposta e non una correzione. Si scartano quelli che rileggendo il momento non mostrano un attrito, e si aggiungono quelli che lo strumento non vede ma la sessione ricorda, purché si possa indicare il turno.

## Passo 2 - Classificare ogni attrito nella sua sede

Per ogni attrito confermato si chiede che cosa avrebbe evitato quel momento, e la risposta cade in una delle sedi che il sistema ha già. Si cerca prima se la correzione esiste e non è collegata: un controllo scritto e non lanciato da `chiudi`, una norma che esiste e che l'indice del `CLAUDE.md` non nomina. In quel caso il riscontro è collegarla, non scriverne un'altra.

| Che cosa è successo | Dove va la correzione |
|---|---|
| Un errore che una regola fissa avrebbe preso: uno schema di testo, un percorso, un formato, un comando | Un controllo deterministico fra quelli di `chiudi-sessione`, oppure in `.githooks/pre-commit.d/`, con un `--autotest` che cade se il difetto torna. È la sede preferita, perché un controllo può fallire e una frase no |
| L'agente ha cercato a lungo un file o un'informazione, o non ha caricato una norma che esisteva | Un puntatore nell'indice delle norme caricate su richiesta del `CLAUDE.md`, oppure la descrizione della skill che doveva scattare, scritta con le parole con cui la situazione si è presentata |
| Un errore di giudizio, che nessun controllo può decidere | La regola pertinente in `.claude/rules/`, con il caso che la giustifica in `.claude/norme/` |
| Un'istruzione dei file sempre caricati che in sessione non ha cambiato niente, o che è stata contraddetta senza danno | Toglierla. `misura-istruzioni.py` dice quanto pesava |
| Una chiamata costosa per ciò che ha restituito | Lo strumento si restringe, oppure la regola `token-economy.md` riceve il caso |
| Un'informazione che l'agente non poteva raggiungere | Un accesso in sola lettura, un registro scritto su file, un comando che la espone |

## Passo 3 - Proporre, e fermarsi

Si presentano le proposte in ordine di gravità, cioè di quanto lavoro l'attrito è costato e di quanto è probabile che si ripeta. Ogni proposta porta il turno da cui nasce, la sede e la modifica concreta; una proposta che non si riesce ad ancorare a un turno non si presenta, perché è il consiglio generico che una retrospettiva tende a inventare per riempire le categorie. Se gli attriti confermati sono zero, lo si dice in una riga ed è un esito valido.

Poi ci si ferma. Nessun file si modifica prima che l'utente scelga quali proposte fare.

## Passo 4 - Fare le correzioni scelte

Le correzioni scelte si fanno come ogni altro lavoro del progetto: un controllo nuovo si prova reintroducendo il difetto, secondo la skill `prove-che-misurano`, e la memoria si aggiorna nello stesso giro. In un progetto istanziato, una correzione che passa le due domande della sezione 16 di `.claude/PROJECT-SYSTEM.md`, cioè che resta vera tolti i nomi propri e non è già nella testa di chi lavora bene, diventa anche una lezione per il template.

```
python .claude/templates/tools/lezioni-template.py nuova "titolo" --testo "che cosa è successo, al turno N, e quale controllo lo evita"
```

Il template la raccoglie da sé alla sua prossima apertura. Nel template stesso la correzione si fa direttamente. Il file `_notes/retrospettiva/segnali.json` resta nelle note, che non si versionano.
