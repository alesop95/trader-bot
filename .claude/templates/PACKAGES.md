# Pacchetti opzionali del sistema di progetto

> Registro dei pacchetti opzionali che l'agente puo proporre quando inizializza o allinea un
> progetto. Non e' un elenco di cose da installare sempre: ogni voce si offre con un gate
> esplicito, in base al tipo di progetto, e si istanzia solo su conferma dell'utente. La skill
> `init-project-system` e i due prompt consultano questo file per sapere cosa proporre.

## Come si usa

Al Passo 4 dell'inizializzazione e durante l'allineamento, l'agente legge questo registro, valuta
quali pacchetti sono pertinenti al progetto secondo la colonna "quando offrirlo", e li propone uno
per uno con una domanda esplicita, offrendo di istanziarli ora o di rimandarli come promemoria.
Non assume mai: anche un pacchetto pertinente si attiva solo se l'utente accetta. Un pacchetto gia
presente nel progetto non si reinstalla: se ne mostra la differenza e si chiede come procedere.
Allo stesso modo, se il progetto fornisce gia quella capacita in proprio (per esempio implementa
gia una propria knowledge base o un proprio sistema di grafo), il pacchetto non si propone come
duplicato: al massimo si propone di allineare l'implementazione esistente allo standard.
Quando un pacchetto viene attivato, l'agente mostra subito un recap d'uso, cioe i comandi e il
flusso essenziali presi dal README del pacchetto, cosi l'utente sa come usarlo da subito.

## Catalogo

| Pacchetto | Cosa fa | Quando offrirlo | Cosa istanzia | Note |
|---|---|---|---|---|
| `latex` | Ambiente di build LaTeX: manifesto pacchetti, script setup/build, skill `latex-build` | Il progetto contiene o produrra file `.tex` | `templates/latex/` in `scripts/`, `tex-packages.txt`, `.latexmkrc`, `.claude/skills/latex-build/` | Script `.ps1` e `.sh`; la distribuzione TeX resta esterna e non versionata |
| `diagrams` | Resa dei diagrammi Mermaid `.mmd` in `.svg` riusando il browser di sistema | Il progetto ha o avra diagrammi sotto `.claude/context/diagrams/` | `templates/tools/render-diagrams.mjs` in `tools/render-diagrams.mjs` | Richiede Node e un browser Chromium-based (Edge o Chrome) |
| `code-context` (MCP) | Server MCP tree-sitter che da struttura cartelle e simboli del codice | In allineamento di un progetto esistente, per far mappare all'agente la struttura del codice e popolare le schede | `.mcp.json` in radice, dalla variante OS (`templates/mcp.json` o `templates/mcp.windows.json`) | Avviato via `npx`, zero dipendenze native; nessuna cartella `mcp/` |
| `knowledge-wiki` | LLM Wiki: `sources/` immutabile, `wiki/` compilata dall'LLM, schema `WIKI-SCHEMA.md`, skill `wiki-digest` | Progetti dove si accumula conoscenza trasversale nel tempo, se non gia coperta da una knowledge base nativa | `templates/knowledge-wiki/` in `knowledge/` (`WIKI-SCHEMA.md`, `sources/`, `wiki/`, `log.md`) e `.claude/skills/wiki-digest/` | Pattern Karpathy; vedi knowledge-systems-analysis |
| `book-to-skill` | PDF tecnico in skill pre-digerita on-demand, via la skill `book-digest` | Progetti con libri o PDF tecnici di riferimento | `templates/book-to-skill/` in `.claude/skills/book-digest/`; le skill-libro `<slug>/` le genera `book-digest`, locali per default, globali solo su conferma | Pattern book-to-skill; ponte opzionale verso `knowledge-wiki` (path A/B) |
| `caveman` | Riduce ~65% dei token di output facendo rispondere l'agente in modo telegrafico, senza toccare il ragionamento | Sessioni operative o coding output-heavy; NON quando il progetto produce documentazione o prosa | Tool esterno di sessione, installato su conferma (skill/plugin Claude Code); nessun file nel progetto | Vedi `rules/token-economy.md`; repo juliusbrussee/caveman |
| `graphify` | Grafo di conoscenza dell'intero progetto, codice e documenti: relazioni, community, nodi centrali e report di insight, con visualizzazione interattiva | Capire in modo olistico un progetto grande o sconosciuto, o una collezione di documenti; complementare a `code-context` (simboli) e a `knowledge-wiki` (pagine curate) | Tool esterno: `uv tool install graphifyy` o `pipx install graphifyy`, poi `graphify install`; si usa con `/graphify .` | MIT; codice via tree-sitter locale, documenti via LLM (consuma token); repo safishamsi/graphify |
| `humanizer` | Skill che rimuove i segni di scrittura AI dal testo: frasi riempitive, regola del tre, trattini lunghi e grassetto in eccesso, hedging, tono promozionale (33 pattern, con audit finale) | Progetti che producono prosa o testo (blog, libro, documentazione) | Skill esterna: si clona in `.claude/skills/humanizer/` (locale al progetto, preferito; globale solo su conferma); si usa con `/humanizer <testo>` | MIT; complementa la regola `interaction-style`; repo blader/humanizer |
| `taste-skill` | Skill di design-taste: migliora layout, tipografia, spaziatura e motion delle interfacce generate, per evitare UI dall'aspetto generico-AI | Progetti con frontend o UI | Skill esterna: `npx skills add https://github.com/Leonxlnx/taste-skill` | MIT; repo Leonxlnx/taste-skill |

Le ultime due righe sono segnaposto: i pacchetti `knowledge-wiki` e `book-to-skill` verranno
definiti nelle fasi successive. Restano elencati qui perche il registro sia il punto unico in cui
si vede cosa il sistema sa offrire.

## Aggiungere un pacchetto

Un nuovo pacchetto si aggiunge con una riga in questo catalogo e, se e' a cartella, con una
sottocartella sotto `templates/` che contiene un proprio `README.md` di istanziazione, sul modello
di `templates/latex/`. La colonna "quando offrirlo" deve indicare un trigger concreto, cosi che il
gate sappia quando proporlo senza assumere. I pacchetti che non sono cartelle, come `diagrams` e
`code-context`, vivono come voci del catalogo e puntano ai file gia presenti sotto `templates/`.

Il percorso completo per estendere il sistema, dalla ricerca dello strumento alla voce di catalogo
fino alla validazione come case-study, e' descritto nella sezione "Come estendere il sistema" del
`README.md` di radice.
