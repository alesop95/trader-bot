# Template istanziabili del sistema di progetto

> Questi file sono gli scheletri canonici dell'anatomia descritta in `PROJECT-SYSTEM.md` (sezioni 2, 4, 10, 12). Non sono lo stato di un progetto reale: sono modelli da istanziare in un progetto nuovo o esistente. La skill `init-project-system` li copia nella posizione finale e li compila, sostituendo i segnaposto. Non vanno mai letti come fonte di verità di un progetto: la fonte di verità di un progetto è la sua `memory/index.md` istanziata.

## Registro dei pacchetti opzionali

`PACKAGES.md` è il registro delle voci opzionali che il sistema sa offrire, più di ottanta, diviso in dieci settori: fondamenta e igiene del progetto, scrittura e tipografia, fonti e corpus documentali, voce e trascrizione, domini scientifici, comprensione di una codebase, sviluppo e qualità del codice, apprendimento guidato, economia del contesto, orchestrazione e cataloghi di agenti. Ogni settore apre con la frase che dice a chi serve e che cosa chiedere per saperlo, e ogni riga porta il trigger concreto che dice quando proporre quel pacchetto.

La divisione per settore guida il gate: la skill `gate-pacchetti` riconosce dai fatti del progetto a quali settori appartenga, dichiara il riconoscimento e lo fa correggere, poi propone le voci pertinenti una per volta con funzione, ragione e costo. Si esegue in inizializzazione, a ogni tornata di allineamento e quando cambia l'obiettivo; `init-project-system` la invoca al Passo 4. Per i progetti di ricerca scientifica o tecnica chiede separatamente OpenAlex MCP, PaperQA2 e Feynman, con istruzioni in [academic-researcher/INTEGRAZIONI-TOOL.md](academic-researcher/INTEGRAZIONI-TOOL.md). `PACKAGES.md` resta nel bundle come riferimento e non si istanzia nella radice del progetto.

## Mappa di istanziazione

Anatomia sempre creata. La colonna git indica se il file istanziato è tracciato o ignorato.

```
templates/CLAUDE.md            ->  <radice>/CLAUDE.md                    (tracciato)
templates/AGENTS.md            ->  <radice>/AGENTS.md                    (tracciato)
templates/CLAUDE.local.md      ->  <radice>/CLAUDE.local.md             (ignorato)
templates/gitignore.snippet    ->  da unire al <radice>/.gitignore       (tracciato)
templates/settings.json        ->  <radice>/.claude/settings.json        (tracciato)
templates/memory/*.md          ->  <radice>/.claude/memory/*.md          (tracciato)
templates/context/*.md         ->  <radice>/.claude/context/*.md         (tracciato)
templates/context/sub-subproject.md ->  <radice>/.claude/context/<nome-sottoprogetto>.md  (tracciato, una copia per sottoprogetto)
templates/_notes/*.md          ->  <radice>/_notes/*.md                  (ignorato; solo dopo che _notes e ignorato)
templates/tools/sync-codex-skills.py -> <radice>/tools/sync-codex-skills.py (tracciato)
```

`AGENTS.md` non duplica `CLAUDE.md`: lo indica come fonte canonica e traduce soltanto il punto di ingresso per Codex. Lo strumento `sync-codex-skills.py` crea sotto `.agents/skills/` wrapper minimi per ogni skill canonica presente in `.claude/skills/`; nome, descrizione e policy di invocazione restano così scopribili nativamente da Codex, mentre il corpo della procedura continua a vivere in un solo file. Lo strumento si riesegue dopo ogni installazione, rimozione o modifica di una skill e si verifica con `--check`.

Una precisazione sulla riga delle schede di contesto, perché la forma con l'asterisco la nasconde: `sub-subproject.md` non è una scheda che si copia una volta con il proprio nome, ma un modello che si istanzia una volta per ogni sottoprogetto, rinominandolo con il nome di quello e compilandone il `covers-paths` con la sua cartella. Le istruzioni di istanziazione stanno dentro il modello, e comprendono il passo che si dimentica più spesso, cioè estendere il `covers-paths` delle schede trasversali alla cartella nuova: senza quel passo il motore di riconciliazione non guarda mai il sottoprogetto appena aggiunto.

Anatomia di radice opzionale: README pubblico per GitHub, da istanziare su gate esplicito.

```
templates/README-project.md    ->  <radice>/README.md                    (tracciato, opzionale)
```

Anatomia di radice opzionale: template pubblico delle variabili d'ambiente, da istanziare se il progetto usa variabili d'ambiente o server MCP con token. Dichiara quali variabili servono, senza valori reali: la copia compilata `.env` resta locale, ignorata dallo snippet di `.gitignore` e negata in lettura all'agente dal `settings.json` di baseline.

```
templates/env.example          ->  <radice>/.env.example                 (tracciato, opzionale)
```

Anatomia di radice opzionale, da istanziare solo se il progetto integra un servizio esterno tramite un server MCP. Vive nella radice del progetto, accanto a `.claude`, mai sotto `.claude`, perché Claude Code scopre i server MCP solo dal `.mcp.json` di radice, in formato `mcpServers`.

`templates/mcp.json` è già pronto per il server MCP consigliato, `code-context-provider-mcp` (tree-sitter in WebAssembly, zero dipendenze native, licenza MIT), avviato via `npx`: dà all'agente l'albero delle cartelle e i simboli del codice (funzioni, classi, import, export) ed è particolarmente utile in allineamento, per mappare un progetto esistente di cui non si conosce la struttura. Essendo un pacchetto pubblicato e avviato via `npx`, NON richiede una cartella `mcp/`, che serve solo per un server implementato in proprio. Per usare un altro server si modifica `.mcp.json` e solo in quel caso si crea `mcp/` con l'implementazione.

Del `.mcp.json` esistono due varianti pronte, perché `npx` si avvia in modo diverso secondo il sistema operativo. Su Linux e macOS `npx` è un vero eseguibile e si usa la forma diretta `"command": "npx"` di `templates/mcp.json`. Su Windows `npx` è uno script (`npx.cmd`), non un eseguibile lanciabile direttamente, quindi si usa `templates/mcp.windows.json`, che lo avvia tramite l'interprete dei comandi con `"command": "cmd"` e `"args": ["/c", "npx", ...]`. Il gate del sistema operativo dell'inizializzazione istanzia in `.mcp.json` la variante giusta.

```
templates/mcp.json          ->  <radice>/.mcp.json   (Linux/macOS: code-context via npx diretto)
templates/mcp.windows.json  ->  <radice>/.mcp.json   (Windows: code-context via wrapper cmd /c)
                                 <radice>/mcp/<server>.js   (solo per un server MCP implementato in proprio)
```

Pacchetto opzionale per progetti LaTeX, da istanziare solo se il progetto produce un documento LaTeX. Manifesto, script di setup/build, `.latexmkrc` e skill `latex-build`; la distribuzione TeX (TinyTeX) resta esterna e non versionata. La mappa di istanziazione di dettaglio e le note stanno in `templates/latex/README.md`.

```
templates/latex/               ->  scripts/, tex-packages.txt, .latexmkrc, .claude/skills/latex-build/
```

Pacchetto opzionale per una LLM Wiki, da istanziare nei progetti dove si accumula conoscenza trasversale nel tempo e che non hanno già una knowledge base nativa. Crea la cartella `knowledge/` con `sources/` immutabile, `wiki/` compilata dall'LLM e lo schema `WIKI-SCHEMA.md`, più la skill di ingestione `wiki-digest`. La mappa di dettaglio e le note stanno in `templates/knowledge-wiki/README.md`.

```
templates/knowledge-wiki/  ->  knowledge/ (WIKI-SCHEMA.md, log.md, sources/, wiki/) e .claude/skills/wiki-digest/
```

Pacchetto opzionale per creare skill da libri o PDF tecnici, sul modello di book-to-skill. Installa la skill `book-digest`, che digerisce un PDF in una skill-libro densa e interrogabile on-demand sotto `.claude/skills/<slug>/`. Le skill-libro nascono locali al progetto e versionate; si possono promuovere al contesto globale di Claude solo su conferma esplicita. Path opzionale verso la wiki: i file capitolo possono finire in `knowledge/sources/books/<slug>/`. Dettaglio in `templates/book-to-skill/README.md`.

```
templates/book-to-skill/  ->  .claude/skills/book-digest/ (la skill); le skill-libro <slug>/ le genera book-digest
```

Pacchetto opzionale per il riferimento alle opzioni di Claude Code con auto-aggiornamento dalla guida community Cranot/claude-code-guide. Il documento distillato e lo stato sono tracciati, la fonte grezza scaricata resta in `_notes/` ignorata; il workflow GitHub Actions è un componente opzionale nel pacchetto. La mappa di dettaglio e le note di onestà sulla fonte stanno in `templates/claude-code-handoff/README.md`.

```
templates/claude-code-handoff/  ->  .claude/context/claude-code-handoff.md, .claude/commands/refresh-handoff.md,
                                    tools/update-handoff.ps1|.sh (variante OS), .github/workflows/update-handoff.yml (opzionale)
```

Pacchetto opzionale dei profili di stack: un solo profilo per progetto, scelto al gate quando lo stack è riconosciuto dai manifest, istanziato come regola modulare normativa con nome stabile. Complementare alla scheda descrittiva `STACK.md`. Dettaglio in `templates/stack-profiles/README.md`.

```
templates/stack-profiles/profiles/<profilo>.md  ->  .claude/rules/stack-profile.md
```

Pacchetto opzionale degli hook pronti all'uso, mai attivi dopo l'istanziazione: i file si copiano ma non fanno nulla finché i blocchi scelti non vengono copiati a mano nella sezione `hooks` del `settings.json` del progetto, dal frammento della propria piattaforma. Dettaglio e note di sicurezza in `templates/hooks-starter/README.md`.

```
templates/hooks-starter/hooks/  ->  .claude/hooks/ (variante OS .ps1 o .sh; attivazione manuale via settings.json)
```

Pacchetto opzionale per un README pubblico che cresce nel tempo: una skill verifica e aggiorna la prosa contro codice e documentazione, mentre uno strumento deterministico genera l'indice navigabile e controlla i link locali. Nel repository del template genera anche l'inventario dei pacchetti dal catalogo. Dettaglio in `templates/readme-sync/README.md`.

```
templates/readme-sync/tools/sync-readme.py          ->  <radice>/tools/sync-readme.py
templates/readme-sync/skills/sync-readme/SKILL.md  ->  <radice>/.claude/skills/sync-readme/SKILL.md
templates/readme-sync/githooks/pre-commit           ->  <radice>/.githooks/pre-commit (opzionale, da attivare in git locale)
templates/readme-sync/githooks/commit-msg           ->  <radice>/.githooks/commit-msg (stessa attivazione)
```

Pacchetto opzionale delle skill di sviluppo, da scegliere una per una al gate: `test-generator` e `mcp-tool-scaffold` non duplicano nulla, `code-review` e `security-review` si istanziano solo dichiarando la sovrapposizione con le skill native omonime. Dettaglio e nota sul naming in `templates/dev-skills/README.md`.

```
templates/dev-skills/skills/<skill>/  ->  .claude/skills/<skill>/
```

Pacchetto opzionale dei subagent di esempio, da scegliere uno per uno al gate: `code-reviewer`, `security-auditor`, `debugger`, `explorer` (quest'ultimo duplica in parte l'agente nativo Explore, la sovrapposizione si dichiara).

```
templates/agents/<agente>.md  ->  .claude/agents/<agente>.md
```

Pacchetto opzionale per la resa dei diagrammi, da istanziare se il progetto contiene diagrammi Mermaid sotto `.claude/context/diagrams/`. Lo script rende i `.mmd` nei corrispondenti `.svg` riusando il browser Chromium-based di sistema (Edge o Chrome), senza scaricare un Chromium di Puppeteer, così ogni progetto e autonomo nella generazione.

```
templates/tools/render-diagrams.mjs ->  <radice>/tools/render-diagrams.mjs   (tracciato, opzionale)
templates/tools/README.md           ->  <radice>/tools/README.md             (tracciato, opzionale)
```

Strumento per i passi manuali e visivi, da istanziare nel progetto quando lo sviluppo richiede riscontri visivi che l'agente non può osservare. Restituisce l'immagine più recente nella cartella di cattura di Screenpresso, perché l'agente legga lo screenshot appena fatto dall'utente. Si abbina alla regola `rules/manual-screenshots.md`, già presente sotto `.claude/rules/` e copiata con essa.

```
templates/tools/latest-screenshot.ps1 ->  <radice>/tools/latest-screenshot.ps1  (tracciato, opzionale)
```

Strumenti di igiene dell'account, non del progetto: agiscono sulla home dell'account Claude Code, non sul repository. Non si istanziano nella radice del progetto; restano nel bundle e si invocano da li, mentre `session-end-wipe.ps1` e il suo companion `scrub-claude-json.js` si installano insieme nella home dell'account. Lo script di wipe non si installa mai così com'è: porta segnaposto al posto dei prefissi da preservare, e prima di compilarlo si elencano gli slug realmente presenti con il suo modo di sola lettura e si chiede all'utente quali radici tenere, perché quei prefissi dipendono dalla macchina e su Linux non hanno nemmeno la forma di una lettera di disco. Vedi PROJECT-SYSTEM.md sezione 15.

```
templates/tools/check-account-hygiene.ps1 ->  si esegue dal bundle al Passo 0   (verifica, non istanziato)
templates/tools/session-end-wipe.ps1      ->  <CLAUDE_CONFIG_DIR>/hooks/session-end-wipe.ps1   (installato per-account, da compilare)
templates/tools/scrub-claude-json.js      ->  <CLAUDE_CONFIG_DIR>/hooks/scrub-claude-json.js   (installato per-account)
```

Strumento di rilevazione dei profili SSH, anch'esso di macchina e non di progetto: si esegue dal bundle al Passo 0.5 per leggere gli alias verso GitHub realmente configurati, con le chiavi che selezionano e l'identità git corrente, così che il remoto si agganci a un profilo che esiste invece che a uno preso da un'altra installazione. Non ha varianti per sistema operativo, perché il formato di `ssh_config` non ne ha.

```
templates/tools/detect-ssh-profiles.py    ->  si esegue dal bundle al Passo 0.5  (rilevazione, non istanziato)
```

Strumento di verifica della ripresa, che invece e di progetto e si istanzia: confronta l'impronta registrata alla chiusura della sessione precedente con lo stato reale di git, e dice che cosa una sessione caduta a meta non ha scritto. La skill `riprendi` e la procedura che ne interpreta l'esito; l'impronta si registra come ultimo atto della sessione, dopo i commit dell'utente.

```
templates/tools/verifica-ripresa.py        ->  tools/verifica-ripresa.py   (tracciato)
templates/tools/chiudi-sessione.ps1        ->  tools/chiudi-sessione.ps1   (tracciato)
templates/tools/chiudi-sessione.sh         ->  tools/chiudi-sessione.sh    (tracciato)
templates/tools/installa-chiudi.sh          ->  uso dal bundle per il profilo Bash/Zsh (non istanziato)
templates/tools/lint-doc-references.py     ->  tools/lint-doc-references.py (tracciato)
```

`chiudi-sessione` lega in un comando la chiusura: controlli istanziati, commit con conferma dell'utente, push verificato, impronta di ripresa e wipe degli account quando nessuna sessione Claude Code è aperta. `lint-doc-references` trova nella documentazione i riferimenti a file che non esistono, dividendoli in categorie invece di ammucchiarli: un documento vivo che nomina un file assente va corretto, una voce datata che lo nomina era vera quel giorno e non si riscrive. Le radici che identificano un percorso si leggono da git e non si configurano.

Pacchetto opzionale per la trascrizione e la sintesi vocale in locale, appoggiato a VoiceStudio, che resta una applicazione esterna e non entra nel repository. Istanzia un solo strumento, senza segnaposto da sostituire, che scrive le trascrizioni sotto `_notes/fonti/` con la provenienza davanti al testo. La mappa di dettaglio, l'allestimento per sistema operativo e le note su licenza e consenso alla clonazione di una voce stanno in `templates/voicestudio/README.md`.

```
templates/voicestudio/tools/trascrivi.py  ->  tools/trascrivi.py
```

Pacchetto opzionale per la raccolta di skill scientifiche di K-Dense. Non installa skill: istanzia lo strumento che ne genera la mappa e la mappa già generata, che il progetto tiene dove tiene i propri documenti. Richiede una riga nel `.gitignore` per la copia locale della raccolta, che è materiale di terzi. La procedura in quattro mosse per prendere una skill e i numeri misurati sulla raccolta stanno in `templates/scientific-skills/README.md`.

```
templates/scientific-skills/tools/mappa-skill-scientifiche.py  ->  tools/mappa-skill-scientifiche.py
templates/scientific-skills/MAPPA-SKILL-SCIENTIFICHE.md        ->  docs/MAPPA-SKILL-SCIENTIFICHE.md (o dove il progetto tiene i documenti)
                                                                   .tmp-skills/ nel .gitignore
```

Pacchetto opzionale di sola guida alla scelta, che non istanzia file nel progetto: le skill si prendono a monte, come plugin gestito oppure come file copiati, e la scelta fra le due vie dipende da quali skill si prendono, perché tre di esse vanno adattate ai percorsi di questo sistema. La mappa in tre gruppi, cioè i buchi reali, le duplicazioni e ciò che va adattato, sta in `templates/matt-pocock-skills/README.md`.

```
templates/matt-pocock-skills/README.md  ->  nessun file istanziato: e' la guida alla scelta
```

## Ancoraggio al primo commit

In un progetto greenfield non esiste ancora un commit quando l'anatomia viene creata, perché il primo commit è un'operazione manuale dell'utente. In quel caso i campi commit del frontmatter di riconciliazione e il commit di riferimento in `memory/index.md` si istanziano con il segnaposto esplicito `PENDING-FIRST-COMMIT`. Subito dopo il primo commit reale, la skill `sync-context` sostituisce ogni `PENDING-FIRST-COMMIT` con l'hash di `HEAD`, ancorando da lì in poi il drift al codice come in un progetto nato col sistema.

## Segnaposto

I segnaposto sono racchiusi tra parentesi angolari, ad esempio `<nome progetto>`, `<hash del commit corrente>`, `<YYYY-MM-DD>`. Vanno sostituiti con valori reali al momento dell'istanziazione. Le schede di `context/` si creano con struttura e frontmatter e si popolano leggendo il codice attuale, mai con contenuto inventato in fase di init.
