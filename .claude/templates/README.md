# Template istanziabili del sistema di progetto

> Questi file sono gli scheletri canonici dell'anatomia descritta in `PROJECT-SYSTEM.md`
> (sezioni 2, 4, 10, 12). Non sono lo stato di un progetto reale: sono modelli da istanziare in
> un progetto nuovo o esistente. La skill `init-project-system` li copia nella posizione finale
> e li compila, sostituendo i segnaposto. Non vanno mai letti come fonte di verità di un
> progetto: la fonte di verità di un progetto è la sua `memory/index.md` istanziata.

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

Anatomia di radice opzionale, da istanziare solo se il progetto integra un servizio esterno
tramite un server MCP. Vive nella radice del progetto, accanto a `.claude`, mai sotto `.claude`,
perché Claude Code scopre i server MCP solo dal `.mcp.json` di radice.

```
templates/mcp.json             ->  <radice>/.mcp.json                    (tracciato, opzionale)
                                    <radice>/mcp/<server>.js              (implementazione del server, tracciata, opzionale)
```

Pacchetto opzionale per progetti LaTeX, da istanziare solo se il progetto produce un documento
LaTeX. Manifesto, script di setup/build, `.latexmkrc` e skill `latex-build`; la distribuzione TeX
(TinyTeX) resta esterna e non versionata. La mappa di istanziazione di dettaglio e le note stanno
in `templates/latex/README.md`.

```
templates/latex/               ->  scripts/, tex-packages.txt, .latexmkrc, .claude/skills/latex-build/
```

Pacchetto opzionale per la resa dei diagrammi, da istanziare se il progetto contiene diagrammi
Mermaid sotto `.claude/context/diagrams/`. Lo script rende i `.mmd` nei corrispondenti `.svg`
riusando il browser Chromium-based di sistema (Edge o Chrome), senza scaricare un Chromium di
Puppeteer, cosi ogni progetto e autonomo nella generazione.

```
templates/tools/render-diagrams.mjs ->  <radice>/tools/render-diagrams.mjs   (tracciato, opzionale)
templates/tools/README.md           ->  <radice>/tools/README.md             (tracciato, opzionale)
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
