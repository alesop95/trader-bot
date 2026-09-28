# Pacchetto academic-researcher

> Pacchetto opzionale del sistema di progetto per Claude Code e Codex. Organizza scoping del topic, ricerca della letteratura, lettura profonda dei paper, tracciamento tripartito delle fonti (verificata, da verificare, scartata), analisi di un corpus già caricato, sincronizzazione di un file `.bib` tra Zotero e JabRef, ricerca tecnica e protocolli di benchmark. Il modulo `references/claude-ricercatore-universitario-completo.md` resta la fonte per la catena bibliografica originale; `senior-researcher` e il suo protocollo R&D sono un'estensione del template. Si offre al gate dei pacchetti (vedi `../PACKAGES.md`) ai progetti di ricerca accademica, stato dell'arte tecnico o benchmark; se il progetto ha già un sistema bibliografico equivalente, si allinea quello esistente.

## Cosa è concreto e cosa è stub

Non tutte le nove skill che compongono il pacchetto hanno lo stesso livello di completezza, ed è importante saperlo prima di attivarle: la trasparenza su questo punto è un requisito di onestà del contenuto del template, non un dettaglio implementativo. Cinque skill hanno un corpo operativo completo perché il documento di riferimento, o un metodo esterno condiviso dall'utente e attribuito come tale, ne fissa il comportamento in modo concreto: `corpus-analysis` (le dieci modalità collaudate, nove dalla sezione 10 del documento di riferimento e la decima, Canon Update, da un metodo esterno attribuito nel file stesso), `citation-tracker` (la tripartizione verificata/da verificare/scartata, sezione 7), `bib-sync` (il flusso Zotero-JabRef, sezione 3), `research-scoping` (le domande di gate della sezione 18, più un blocco di istruzioni custom di progetto da fonte esterna attribuita), `literature-search` (il percorso via MCP della sezione 5, più un percorso via Extended Thinking e Research Mode da fonte esterna attribuita, senza dipendenza da alcun MCP). `senior-researcher` aggiunge un workflow operativo per topic, fonti tecniche non bibliografiche, matrice claim-prova e protocollo di benchmark; il suo uso con Feynman resta opzionale e da collaudare. Le altre tre skill sono parzialmente stub: dispongono già di un prompt o di un'euristica di default usabile da subito, ma lasciano esplicitamente aperta una calibrazione specifica del dominio o dell'ambiente che solo l'attivazione in un progetto reale può fissare. `deep-paper-reading` ha già i due memo di lettura Steelman e Skeptic, mentre il parsing strutturato via GROBID/PaperQA2 resta da definire. `gap-analysis` ha già un prompt di verdetto a tre valori con argomentazione a doppio taglio, mentre la soglia che separa "condizionale" da "promettente" resta da tarare sul dominio disciplinare. `skill-autogen` ha già un'euristica di ricorrenza di default (due occorrenze) e un prompt di proposta, mentre il numero esatto di occorrenze resta regolabile sul volume di ricerca del progetto. Completare del tutto queste tre parti senza conoscere il contesto reale del progetto avrebbe significato inventare un comportamento non verificato; le parti aggiunte da fonte esterna (screenshot di un post pubblico, account `@techwith.ram`, non parte del documento di riferimento originale) sono marcate come tali nei rispettivi `SKILL.md`, con l'efficacia dichiarata dalla fonte e non verificata indipendentemente da questo template, mentre i prompt di `gap-analysis` e `skill-autogen` sono elaborati per questo pacchetto e non provengono da quella fonte esterna, che non copre né la valutazione di direzioni di ricerca né l'auto-generazione di skill.

## Mappa di istanziazione

```
templates/academic-researcher/rules/no-uncited-claims.md          ->  <radice>/.claude/rules/no-uncited-claims.md               (tracciato)
templates/academic-researcher/skills/corpus-analysis/              ->  <radice>/.claude/skills/corpus-analysis/                  (tracciato)
templates/academic-researcher/skills/citation-tracker/              ->  <radice>/.claude/skills/citation-tracker/                 (tracciato)
templates/academic-researcher/skills/bib-sync/                      ->  <radice>/.claude/skills/bib-sync/                         (tracciato)
templates/academic-researcher/skills/research-scoping/              ->  <radice>/.claude/skills/research-scoping/                 (tracciato)
templates/academic-researcher/skills/literature-search/             ->  <radice>/.claude/skills/literature-search/                (tracciato)
templates/academic-researcher/skills/senior-researcher/             ->  <radice>/.claude/skills/senior-researcher/                (tracciato)
templates/academic-researcher/skills/deep-paper-reading/            ->  <radice>/.claude/skills/deep-paper-reading/               (tracciato, parzialmente stub)
templates/academic-researcher/skills/gap-analysis/                  ->  <radice>/.claude/skills/gap-analysis/                     (tracciato, parzialmente stub)
templates/academic-researcher/skills/skill-autogen/                 ->  <radice>/.claude/skills/skill-autogen/                    (tracciato, parzialmente stub)
templates/academic-researcher/references/claude-ricercatore-universitario-completo.md -> <radice>/research-vault/reference/claude-ricercatore-universitario-completo.md (tracciato)
(creato vuoto alla prima sincronizzazione)                           <radice>/research-vault/bibliography.bib                     (tracciato)
(creato alla prima invocazione di research-scoping)                  <radice>/research-vault/scope.md                             (tracciato)
(creato alla prima invocazione di citation-tracker)                  <radice>/research-vault/tracked-sources.md                   (tracciato)
```

Il documento di riferimento si instanzia dentro `research-vault/` invece che restare nella cartella del template, così che ogni skill lo raggiunga con lo stesso percorso relativo (`research-vault/reference/...`) indipendentemente da dove il pacchetto viene attivato, e così che un collega che clona il repository lo trovi accanto ai dati bibliografici che descrive.

La skill `senior-researcher` porta con sé `references/benchmark.md`. La ricognizione [Feynman e tool aperti](RICOGNIZIONE-FEYNMAN.md) documenta la scelta di integrazione nel template; nei progetti istanziati il workflow resta autosufficiente senza copiarla.

## MCP server e tool esterni collegati

Il pacchetto non installa da solo MCP o CLI: la scelta resta al gate dei pacchetti, con `research-scoping` che registra le preferenze in `research-vault/scope.md`. Il catalogo `../PACKAGES.md` elenca separatamente i server `zotero-mcp`, `academix`, `semantic-scholar-mcp`, `refchecker-mcp`, OpenAlex ufficiale e i tool `arxiv-cli`, GROBID, PaperQA2 e Feynman. OpenAlex, PaperQA2 e Feynman si propongono individualmente in avvio e allineamento per i progetti di ricerca; una risposta su `academic-researcher` non decide per loro. [INTEGRAZIONI-TOOL.md](INTEGRAZIONI-TOOL.md) contiene configurazione per progetto, prerequisiti e verifica per Claude Code e Codex. Le skill `citation-tracker` e `bib-sync` hanno un percorso manuale quando i rispettivi MCP non sono connessi.

## Come si usa, passo per passo

1. Attivazione, al gate dei pacchetti in init o allineamento: si crea l'anatomia sopra, con `research-vault/reference/` già popolato dal documento di riferimento.
2. Si invoca `research-scoping`: definisce la domanda di ricerca e raccoglie le risposte alle domande di gate (dominio disciplinare, libreria Zotero esistente o meno, output LaTeX o Word, livello di autonomia, abbonamenti istituzionali). L'esito va in `research-vault/scope.md`.
3. Sulla base dello scope, il gate chiede separatamente se attivare OpenAlex, PaperQA2 e Feynman, poi considera gli altri MCP e tool esterni pertinenti (`zotero-mcp`, `academix`, `semantic-scholar-mcp`, `refchecker-mcp`, `arxiv-cli`, GROBID). Segue [il runbook](INTEGRAZIONI-TOOL.md) per i tre nuovi tool e rispetta il limite di 3-4 MCP nuovi per sessione già fissato in `../PACKAGES.md`.
4. Si tara la calibrazione di dominio ancora aperta in tre skill (la soglia condizionale/promettente di `gap-analysis`, la soglia di ricorrenza di `skill-autogen`, l'orchestrazione GROBID/PaperQA2 di `deep-paper-reading`) alla luce delle scelte appena fatte, seguendo la sezione "Come completarla" di ciascun `SKILL.md`; tutte e nove le skill sono già operative da subito con i loro default, `literature-search` in particolare con o senza MCP connessi.
5. Da qui in avanti il ciclo è quello descritto nella sezione 14 del documento di riferimento: `literature-search` produce candidati, `citation-tracker` li verifica, `bib-sync` li sincronizza in Zotero e nel `.bib`, `deep-paper-reading` legge in profondità i paper verificati, `corpus-analysis` applica le dieci modalità al sottoinsieme verificato e caricato in conversazione, `gap-analysis` produce i verdetti sulle direzioni di ricerca, e `skill-autogen` propone nuove skill quando un topic diventa ricorrente. Per una ricerca per topic che includa anche fonti tecniche o un benchmark, `senior-researcher` orchestra il ciclo e produce `scope.md`, `sources.md` e `brief.md` in `research-vault/<slug-topic>/`.
6. Prima di ogni consegna o sottomissione, `research-vault/bibliography.bib` va aperto e validato in JabRef: nessuna skill del pacchetto lo considera mai definitivo da sola.

## Recap dei comandi

- Definire lo scope di un nuovo topic: invoca la skill `research-scoping`.
- Condurre una ricerca tecnica o scientifica con brief e prove: invoca `senior-researcher` su un topic.
- Verificare una fonte: invoca la skill `citation-tracker`.
- Sincronizzare Zotero e il `.bib`: invoca la skill `bib-sync`.
- Analizzare un corpus già caricato: invoca la skill `corpus-analysis`, per nome di modalità (per esempio "fai il Gap Scanner") o per intento.
- Consultare l'architettura completa e le raccomandazioni originali: apri `research-vault/reference/claude-ricercatore-universitario-completo.md`.
- Versionare l'avanzamento della ricerca: `git add research-vault/ .claude/skills/ .claude/rules/no-uncited-claims.md` seguito da commit (operazione manuale dell'utente).

## Riferimenti e crediti

Il documento di riferimento cita l'ecosistema alla base della catena bibliografica; i crediti completi sono nella sezione "Riferimenti e strumenti open source" del `README.md` di radice e nel catalogo `../PACKAGES.md`. I tre tool aggiunti al gate sono [OpenAlex MCP ufficiale](https://github.com/ourresearch/openalex-mcp-server) (MIT), [PaperQA2](https://github.com/Future-House/paper-qa) (Apache-2.0) e [Feynman](https://github.com/Companion-Inc/feynman) (MIT); gli altri componenti comprendono Zotero, Better BibTeX, JabRef, i MCP bibliografici comunitari, GROBID e `arxiv-cli`.
