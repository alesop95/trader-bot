# Profilo di stack: TypeScript/Node + MCP server

> Regola modulare istanziata dal pacchetto `stack-profiles` come `stack-profile.md`. Prescrive le convenzioni con cui si scrive il codice di questo stack; la descrizione dello stack reale del progetto resta nella scheda `context/STACK.md`. Adattare i comandi al package manager e agli strumenti reali del progetto alla prima istanziazione.

## Stile del linguaggio

TypeScript in strict mode. Vietato l'`any` implicito: si preferiscono tipi espliciti e, dove il tipo non e' noto al confine, `unknown` seguito da narrowing. Moduli ESM, con le estensioni negli import dove il target le richiede. Gli errori non si lanciano mai come stringhe: si usano classi Error tipizzate oppure un Result-type, e il fallimento e' sempre un valore gestibile, mai un'eccezione anonima.

## Disciplina dei tool MCP

Ogni tool del server ha nome in snake_case e una description orientata al consumo da parte di un LLM, perche' la description e' cio' che il modello legge per decidere se e come usare il tool: va scritta per quel lettore, non solo per un umano. Gli input si validano con zod, o con uno JSON Schema equivalente, prima dell'esecuzione. Gli handler non lasciano mai uscire un'eccezione non gestita verso il client: gli errori sono strutturati e informativi, mai stack trace grezzi. Gli effetti collaterali di un tool si dichiarano nella sua description, e dove possibile i tool si progettano idempotenti. Ogni tool ha almeno tre test: input valido, input non valido, errore a runtime.

## Comandi tipici

Da adattare al package manager reale del progetto.

```
npm run dev        # sviluppo (o: tsx watch src/index.ts)
npm test           # test (tipicamente vitest)
tsc --noEmit       # typecheck
npm run build      # build (tsup o tsc)
```

## Prima di committare

Typecheck e test verdi, diff rivisto, nessun secret in stage. Il commit resta manuale dell'utente, secondo la regola generale del sistema.
