# Template istanziabili del sistema di progetto

> Questi file sono gli scheletri canonici dell'anatomia descritta in `PROJECT-SYSTEM.md`
> (sezioni 2, 4, 10, 12). Non sono lo stato di un progetto reale: sono modelli da istanziare in
> un progetto nuovo o esistente. La skill `init-project-system` li copia nella posizione finale
> e li compila, sostituendo i segnaposto. Non vanno mai letti come fonte di verità di un
> progetto: la fonte di verità di un progetto è la sua `memory/index.md` istanziata.

## Registro dei pacchetti opzionali

`PACKAGES.md` è il registro dei pacchetti opzionali che il sistema sa offrire (`latex`, `diagrams`,
`code-context`, e i futuri `knowledge-wiki` e `book-to-skill`), con per ciascuno il trigger che dice
quando proporlo. La skill `init-project-system` lo consulta al gate dei pacchetti, sia in
inizializzazione sia in allineamento, e propone solo quelli pertinenti, sempre su conferma esplicita.
A differenza degli altri template, `PACKAGES.md` non si istanzia nella radice del progetto: resta qui
come riferimento del bundle.

## Mappa di istanziazione

Anatomia sempre creata. La colonna git indica se il file istanziato è tracciato o ignorato.

```
templates/CLAUDE.md            ->  <radice>/CLAUDE.md                    (tracciato)
templates/CLAUDE.local.md      ->  <radice>/CLAUDE.local.md             (ignorato)
templates/gitignore.snippet    ->  da unire al <radice>/.gitignore       (tracciato)
templates/settings.json        ->  <radice>/.claude/settings.json        (tracciato)
templates/memory/*.md          ->  <radice>/.claude/memory/*.md          (tracciato)
templates/context/*.md         ->  <radice>/.claude/context/*.md         (tracciato)
templates/_notes/*.md          ->  <radice>/_notes/*.md                  (ignorato; solo dopo che _notes e ignorato)
```

Anatomia di radice opzionale: README pubblico per GitHub, da istanziare su gate esplicito.

```
templates/README-project.md    ->  <radice>/README.md                    (tracciato, opzionale)
```

Anatomia di radice opzionale: template pubblico delle variabili d'ambiente, da istanziare se il
progetto usa variabili d'ambiente o server MCP con token. Dichiara quali variabili servono, senza
valori reali: la copia compilata `.env` resta locale, ignorata dallo snippet di `.gitignore` e
negata in lettura all'agente dal `settings.json` di baseline.

```
templates/env.example          ->  <radice>/.env.example                 (tracciato, opzionale)
```

Anatomia di radice opzionale, da istanziare solo se il progetto integra un servizio esterno
tramite un server MCP. Vive nella radice del progetto, accanto a `.claude`, mai sotto `.claude`,
perché Claude Code scopre i server MCP solo dal `.mcp.json` di radice, in formato `mcpServers`.

`templates/mcp.json` è già pronto per il server MCP consigliato, `code-context-provider-mcp`
(tree-sitter in WebAssembly, zero dipendenze native, licenza MIT), avviato via `npx`: dà
all'agente l'albero delle cartelle e i simboli del codice (funzioni, classi, import, export) ed è
particolarmente utile in allineamento, per mappare un progetto esistente di cui non si conosce la
struttura. Essendo un pacchetto pubblicato e avviato via `npx`, NON richiede una cartella `mcp/`,
che serve solo per un server implementato in proprio. Per usare un altro server si modifica
`.mcp.json` e solo in quel caso si crea `mcp/` con l'implementazione.

Del `.mcp.json` esistono due varianti pronte, perché `npx` si avvia in modo diverso secondo il
sistema operativo. Su Linux e macOS `npx` è un vero eseguibile e si usa la forma diretta
`"command": "npx"` di `templates/mcp.json`. Su Windows `npx` è uno script (`npx.cmd`), non un
eseguibile lanciabile direttamente, quindi si usa `templates/mcp.windows.json`, che lo avvia
tramite l'interprete dei comandi con `"command": "cmd"` e `"args": ["/c", "npx", ...]`. Il gate del
sistema operativo dell'inizializzazione istanzia in `.mcp.json` la variante giusta.

```
templates/mcp.json          ->  <radice>/.mcp.json   (Linux/macOS: code-context via npx diretto)
templates/mcp.windows.json  ->  <radice>/.mcp.json   (Windows: code-context via wrapper cmd /c)
                                 <radice>/mcp/<server>.js   (solo per un server MCP implementato in proprio)
```

Pacchetto opzionale per progetti LaTeX, da istanziare solo se il progetto produce un documento
LaTeX. Manifesto, script di setup/build, `.latexmkrc` e skill `latex-build`; la distribuzione TeX
(TinyTeX) resta esterna e non versionata. La mappa di istanziazione di dettaglio e le note stanno
in `templates/latex/README.md`.

```
templates/latex/               ->  scripts/, tex-packages.txt, .latexmkrc, .claude/skills/latex-build/
```

Pacchetto opzionale per una LLM Wiki, da istanziare nei progetti dove si accumula conoscenza
trasversale nel tempo e che non hanno gia una knowledge base nativa. Crea la cartella `knowledge/`
con `sources/` immutabile, `wiki/` compilata dall'LLM e lo schema `WIKI-SCHEMA.md`, piu la skill di
ingestione `wiki-digest`. La mappa di dettaglio e le note stanno in `templates/knowledge-wiki/README.md`.

```
templates/knowledge-wiki/  ->  knowledge/ (WIKI-SCHEMA.md, log.md, sources/, wiki/) e .claude/skills/wiki-digest/
```

Pacchetto opzionale per creare skill da libri o PDF tecnici, sul modello di book-to-skill. Installa
la skill `book-digest`, che digerisce un PDF in una skill-libro densa e interrogabile on-demand
sotto `.claude/skills/<slug>/`. Le skill-libro nascono locali al progetto e versionate; si possono
promuovere al contesto globale di Claude solo su conferma esplicita. Path opzionale verso la wiki: i
file capitolo possono finire in `knowledge/sources/books/<slug>/`. Dettaglio in
`templates/book-to-skill/README.md`.

```
templates/book-to-skill/  ->  .claude/skills/book-digest/ (la skill); le skill-libro <slug>/ le genera book-digest
```

Pacchetto opzionale per il riferimento alle opzioni di Claude Code con auto-aggiornamento dalla
guida community Cranot/claude-code-guide. Il documento distillato e lo stato sono tracciati, la
fonte grezza scaricata resta in `_notes/` ignorata; il workflow GitHub Actions e' un componente
opzionale nel pacchetto. La mappa di dettaglio e le note di onesta' sulla fonte stanno in
`templates/claude-code-handoff/README.md`.

```
templates/claude-code-handoff/  ->  .claude/context/claude-code-handoff.md, .claude/commands/refresh-handoff.md,
                                    tools/update-handoff.ps1|.sh (variante OS), .github/workflows/update-handoff.yml (opzionale)
```

Pacchetto opzionale dei profili di stack: un solo profilo per progetto, scelto al gate quando lo
stack e' riconosciuto dai manifest, istanziato come regola modulare normativa con nome stabile.
Complementare alla scheda descrittiva `STACK.md`. Dettaglio in `templates/stack-profiles/README.md`.

```
templates/stack-profiles/profiles/<profilo>.md  ->  .claude/rules/stack-profile.md
```

Pacchetto opzionale degli hook pronti all'uso, mai attivi dopo l'istanziazione: i file si copiano
ma non fanno nulla finche' i blocchi scelti non vengono copiati a mano nella sezione `hooks` del
`settings.json` del progetto, dal frammento della propria piattaforma. Dettaglio e note di
sicurezza in `templates/hooks-starter/README.md`.

```
templates/hooks-starter/hooks/  ->  .claude/hooks/ (variante OS .ps1 o .sh; attivazione manuale via settings.json)
```

Pacchetto opzionale delle skill di sviluppo, da scegliere una per una al gate: `test-generator` e
`mcp-tool-scaffold` non duplicano nulla, `code-review` e `security-review` si istanziano solo
dichiarando la sovrapposizione con le skill native omonime. Dettaglio e nota sul naming in
`templates/dev-skills/README.md`.

```
templates/dev-skills/skills/<skill>/  ->  .claude/skills/<skill>/
```

Pacchetto opzionale dei subagent di esempio, da scegliere uno per uno al gate: `code-reviewer`,
`security-auditor`, `debugger`, `explorer` (quest'ultimo duplica in parte l'agente nativo Explore,
la sovrapposizione si dichiara).

```
templates/agents/<agente>.md  ->  .claude/agents/<agente>.md
```

Pacchetto opzionale per la resa dei diagrammi, da istanziare se il progetto contiene diagrammi
Mermaid sotto `.claude/context/diagrams/`. Lo script rende i `.mmd` nei corrispondenti `.svg`
riusando il browser Chromium-based di sistema (Edge o Chrome), senza scaricare un Chromium di
Puppeteer, cosi ogni progetto e autonomo nella generazione.

```
templates/tools/render-diagrams.mjs ->  <radice>/tools/render-diagrams.mjs   (tracciato, opzionale)
templates/tools/README.md           ->  <radice>/tools/README.md             (tracciato, opzionale)
```

Strumento per i passi manuali e visivi, da istanziare nel progetto quando lo sviluppo richiede riscontri visivi che l'agente non puo osservare. Restituisce l'immagine piu recente nella cartella di cattura di Screenpresso, perche l'agente legga lo screenshot appena fatto dall'utente. Si abbina alla regola `rules/manual-screenshots.md`, gia presente sotto `.claude/rules/` e copiata con essa.

```
templates/tools/latest-screenshot.ps1 ->  <radice>/tools/latest-screenshot.ps1  (tracciato, opzionale)
```

Strumenti di igiene dell'account, non del progetto: agiscono sulla home dell'account Claude Code, non sul repository. Non si istanziano nella radice del progetto; restano nel bundle e si invocano da li, e `session-end-wipe.ps1` si installa nella home dell'account. Vedi PROJECT-SYSTEM.md sezione 15.

```
templates/tools/check-account-hygiene.ps1 ->  si esegue dal bundle al Passo 0   (verifica, non istanziato)
templates/tools/session-end-wipe.ps1      ->  <CLAUDE_CONFIG_DIR>/hooks/session-end-wipe.ps1   (installato per-account)
```

## Ancoraggio al primo commit

In un progetto greenfield non esiste ancora un commit quando l'anatomia viene creata, perché il
primo commit è un'operazione manuale dell'utente. In quel caso i campi commit del frontmatter di
riconciliazione e il commit di riferimento in `memory/index.md` si istanziano con il segnaposto
esplicito `PENDING-FIRST-COMMIT`. Subito dopo il primo commit reale, la skill `sync-context`
sostituisce ogni `PENDING-FIRST-COMMIT` con l'hash di `HEAD`, ancorando da lì in poi il drift al
codice come in un progetto nato col sistema.

## Segnaposto

I segnaposto sono racchiusi tra parentesi angolari, ad esempio `<nome progetto>`,
`<hash del commit corrente>`, `<YYYY-MM-DD>`. Vanno sostituiti con valori reali al momento
dell'istanziazione. Le schede di `context/` si creano con struttura e frontmatter e si popolano
leggendo il codice attuale, mai con contenuto inventato in fase di init.
