# Pacchetto stratega-impresa

> Pacchetto opzionale del sistema di progetto. Installa una famiglia di sette skill che fanno ragionare Claude come uno stratega d'impresa senior: una skill d'ingresso con il metodo per attraversare un caso, dalla diagnosi alla roadmap di trasformazione, e sei filoni tematici con teoria, schemi decisionali e strumenti. Si offre al gate dei pacchetti (vedi ../PACKAGES.md) ai progetti che trattano strategia, pianificazione, controllo di gestione o trasformazione di un'impresa.

<!-- readme-summary: sette skill per ragionare da stratega d'impresa, dalla diagnosi alla roadmap -->

Valori della macchina d'origine: nessuno. Il pacchetto è fatto di soli file Markdown, senza percorsi, alias, chiavi o configurazioni da rileggere sulla macchina che lo riceve.

## Da dove viene il contenuto

La teoria è quella di un corso executive di strategia e management d'impresa frequentato dal proprietario del template: lezioni registrate e materiali didattici, trascritti e distillati in locale, poi riscritti con parole nostre e anonimizzati. Nessun nome di persona, azienda o ente compare nei file. I rimandi fra quadre, come `[L12]` per una lezione o `[M037]` per un materiale, sono identificativi neutri: la corrispondenza con le fonti reali resta privata.

Ogni file distingue tre provenienze: ciò che viene dal corso porta il rimando; ciò che la skill aggiunge di suo è marcato come integrazione della skill; dati e strumenti esterni stanno nei file `potenziamento.md`, separati dalla teoria.

## Cosa produce

```
skills/
├── stratega-impresa/              ingresso: ciclo del caso, modelli mentali, instradamento
│   ├── SKILL.md
│   └── metodo-roadmap.md          roadmap di trasformazione in sei mosse, con esempio fittizio
├── scenari-modelli-business/      trend, scenari, concorrenza, modelli di business
├── pianificazione-strategica/      obiettivi, matrici, piano industriale, budget, reporting
├── analisi-economica-controllo/   bilancio, KPI, margini, varianze, decisioni di breve, DCF
├── mercato-vendite/               go to market, vendite B2B, digitale, negoziazione, export
├── processi-persone/              HR, competenze, leadership, feedback, lean, tempo
└── strategia-azione/              simulazione d'impresa ed esecuzione della strategia
```

Ogni filone ha la stessa forma: `SKILL.md` con modelli mentali e indice, `capitoli/NN-<tema>.md` caricati solo quando servono, `glossario.md`, `schemi-decisionali.md` con tabelle di scelta e liste di controllo, `potenziamento.md` con i dati e gli strumenti open source che rafforzano il filone.

## Mappa di istanziazione

```
templates/stratega-impresa/skills/<skill>/  ->  <radice>/.claude/skills/<skill>/  (tracciato)
```

Si installano tutte e sette insieme: la skill d'ingresso instrada verso i filoni per nome di cartella. Un progetto che vuole un solo filone può installare quello e la skill d'ingresso.

## Come si usa

- Un caso completo: invocare `stratega-impresa` con la domanda e i dati disponibili; la skill fa la diagnosi e carica i filoni necessari.
- Una domanda di dettaglio: invocare direttamente il filone, per esempio `analisi-economica-controllo` per una scelta di make or buy.
- Una roadmap di trasformazione: `stratega-impresa`, che segue `metodo-roadmap.md`.

## Come potenziare un filone

Ogni filone si potenzia da solo, senza toccare gli altri. Il posto è il suo `potenziamento.md`: dati del progetto, dataset pubblici, strumenti open source. Una regola tiene pulito il pacchetto: la teoria nei capitoli resta quella del corso e dell'integrazione dichiarata, mentre ciò che arriva da fuori si cita con la sua fonte e non riscrive i capitoli. Uno strumento con URL entra nel registro delle fonti a monte del template.
