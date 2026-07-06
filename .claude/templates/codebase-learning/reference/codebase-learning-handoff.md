# Handoff — Sistema di "Code Learning" (solo tool gratuiti)

> Documento di riferimento del pacchetto `codebase-learning` (vedi `../README.md`). Integrato nel template il 2026-07-02 a partire dall'handoff originale dell'utente. È la fonte di verità per ogni scelta di stack MCP e di sequenza didattica della skill e del subagent del pacchetto: in caso di dubbio interpretativo si consulta questo documento prima di improvvisare.
>
> Data ricerca: luglio 2026. Verifica sempre versioni e disponibilità dei repo prima di installare — i progetti community cambiano rapidamente.

---

> Obiettivo: quando un progetto è finito di sviluppare, poter **essere guidati** (anche via Claude Code da terminale) nell'apprendimento della repository — capire i paradigmi dello stack, il software design puro, con spiegazioni ancorate a snippet di codice precisi.
>
> Questo file è un pacchetto integrabile "as-is" nel tuo template quando crei un progetto ex-novo. **Include solo strumenti gratuiti** (open source o con tier gratuito sufficiente all'uso). Copia le sezioni utili in `.claude/`, `.mcp.json` e nella tua documentazione di progetto.

---

## 0. Criterio di inclusione

Sono inclusi solo strumenti che rientrano in almeno una di queste categorie:
- **Open source con licenza permissiva** (MIT o simile), eseguibili in locale senza costi.
- **Servizio gratuito** con tier sufficiente per l'apprendimento di un progetto (con i limiti indicati esplicitamente).

Sono stati **esclusi o declassati** gli strumenti che richiedono piani a pagamento per il caso d'uso rilevante (es. indicizzazione di repo privati, LLM API a consumo obbligatorio). Vedi §7 per l'elenco degli esclusi e il motivo.

---

## 1. Modello mentale: 3 livelli di comprensione

Tre interfacce complementari, da combinare — non in alternativa:

| Livello | Domanda a cui risponde | Strumenti gratuiti |
|---|---|---|
| **Struttura** (grafo del codice) | "Chi chiama cosa? Dove è definito X? Impatto di un cambiamento?" | Serena, CodeGraph, codebase-memory-mcp, CodeGraphContext, GitNexus |
| **Comprensione** (architettura & narrativa) | "Cosa fa questo repo? Come funziona il flusso X? Quali sono le astrazioni centrali?" | Repomix, deepwiki-skill, DeepWiki MCP (repo pubblici) |
| **Riferimento** (docs dello stack) | "Come si usa questa versione di questo framework?" | Context7 (tier gratuito, repo pubblici) |

L'intuizione ricorrente in più fonti: un agente su una codebase sconosciuta brucia la maggior parte dei token *solo per orientarsi* (grep/glob/read a raffica) prima di iniziare a ragionare. Un grafo pre-indicizzato sposta questa fase in uno step offline, riducendo tool call e token.

---

## 2. Componenti gratuiti — schede sintetiche

### 2.1 Grafo strutturale del codice — 100% locale e gratuito

**Serena** — `oraios/serena` · MIT · gratis, nessuna API key
- MCP server LSP-powered: usa gli stessi language server di VS Code (gopls, clangd, ruby-lsp, ...) per navigazione a livello di **simbolo**, non testo. 20–40+ linguaggi.
- Tool tipo `find_symbol`, `find_references`, `insert_after_symbol`: l'agente non deve leggere interi file. Cache semantica dedicata.
- In un benchmark su ~36K righe di Java, un refactoring gestito con 4 subagent orchestrati contro le decine confuse del "vanilla Claude". Conviene **quando la codebase supera la ricerca testuale** (su script piccoli i tool nativi bastano).
- Install (Claude Code):
  ```bash
  uv tool install -p 3.13 serena-agent
  serena init
  claude mcp add --scope user serena -- serena start-mcp-server --context claude-code --project-from-cwd
  ```

**CodeGraph** — `colbymchenry/codegraph` · MIT · npm `@colbymchenry/codegraph` · gratis, 100% locale
- Knowledge graph pre-indicizzato che si auto-sincronizza sui cambi di codice. Backend tree-sitter + SQLite + FTS5.
- Progettato per Claude Code, Codex, Gemini, Cursor, OpenCode, ecc.
- Numeri (ri-validati 2026-06-02 su Opus 4.8): ~58% in meno di tool call, ~22% più veloce, file read ridotti a ~zero. Su Opus 4.8 il vantaggio è minore perché il baseline nativo è più efficiente — utile soprattutto su repo grandi.

**codebase-memory-mcp** — `DeusData/codebase-memory-mcp` · OSS · gratis, binario statico
- Singolo binario, zero dipendenze. Knowledge graph persistente via tree-sitter AST su 158 linguaggi (risoluzione tipi LSP ibrida per Python/TS/JS/PHP/C#/Go/C/C++/Java/Kotlin/Rust).
- 14 tool MCP; grafi di funzioni, classi, call chain, route HTTP, link cross-service.
- Paper (arXiv:2603.27277): su 31 repo reali → 83% answer quality vs 92% di un file-explorer, ma **10× meno token e 2.1× meno tool call**. `query_graph` (Cypher-like) e `trace_call_path` (tracing direzionale con profondità configurabile).

**CodeGraphContext** — `CodeGraphContext/CodeGraphContext` · OSS · gratis
- CLI + MCP server, 23 linguaggi. Backend flessibile: FalkorDB Lite (default), KuzuDB, Neo4j.
- `cgc watch` per aggiornamento live del grafo; bundle `.cgc` pre-indicizzati; wizard interattivo; visualizzazioni interattive del grafo.

**GitNexus** — MCP-native knowledge graph engine · OSS · gratis
- Ricerca ibrida per "processo", `detect_changes` (git-diff impact analysis con risk level pre-commit), `rename` multi-file guidato dal grafo (con dry-run), `cypher` per traversal custom, registry globale multi-repo in `~/.gitnexus/`.

> **Scelta pratica**: parti da **Serena** (semantica LSP, gratis, maturo). Aggiungi **CodeGraph** o **codebase-memory-mcp** se i progetti sono grandi e vuoi call-graph/impact analysis interrogabili. Sono tutti locali e gratuiti.

### 2.2 Comprensione architetturale & materiale di apprendimento — gratuito

**Repomix** — `repomix.com` · OSS · gratis, locale (flag `--mcp`)
- Impacchetta l'intera codebase (locale o remota) in un singolo file consolidato ottimizzato per l'AI: metriche, file tree, contenuto formattato. Tool `pack_codebase`, `pack_remote_repository`, più file-system tool con validazione di sicurezza.
- Ottimo come **primo step**: vista consistente e compressa dell'intero progetto senza preparazione manuale.

**deepwiki-skill** (Claude Code Skill) — `natsu1211/deepwiki-skill` · OSS · gratis
- Auto-genera documentazione **con citazioni precise** (numeri di riga). Pipeline: analyze → generate (subagent in parallelo) → validate (accuratezza dei riferimenti di riga). Casi d'uso: onboarding, modernizzazione legacy, docs OSS, audit. Richiede Python 3.12+ e Claude Code.
- Da preferire a PocketFlow per il tuo scopo: produce output ancorato al codice reale, non solo prosa introduttiva.

**DeepWiki MCP** — endpoint remoto ufficiale · gratis **solo per repo pubblici**
- Indicizza interi repo GitHub pubblici (codice, README, architettura, issue) e risponde a domande in linguaggio naturale ("dov'è implementato X", "come funziona il flusso di auth").
- Install (nessun install locale, transport HTTP):
  ```bash
  claude mcp add -s user -t http deepwiki https://mcp.deepwiki.com/mcp
  ```
- ⚠️ **Limite**: l'endpoint pubblico non indicizza repo privati per design. Per **codice proprietario non usarlo** — resta sui tool locali della §2.1. Esistono server DeepWiki self-hosted OSS (`regenrek/deepwiki-mcp`, `loganzechella/mcp-deepwiki-server`) ma restano legati a pagine deepwiki.com di repo già indicizzati pubblicamente.

### 2.3 Riferimento allo stack — gratuito con limiti

**Context7** — `upstash/context7` · MCP server MIT (open source), servizio hosted con tier gratuito
- Docs **version-specific** di librerie/framework (React 19, Pydantic v2, Next.js 15...) iniettate in contesto, per evitare API hallucinate. Complementare a DeepWiki.
- **Stato gratuità (verificato a gen 2026)**: funziona senza API key con limiti conservativi; il tier gratuito con account è stato ridotto a **1.000 chiamate API/mese** (con 20 bonus/giorno dopo il blocco). Sufficiente per l'apprendimento di un progetto se usato con parsimonia.
- ⚠️ **I repo privati sono a pagamento** (piani Pro/Enterprise). Per lo stack di un progetto proprietario, usa Context7 solo per le **docs pubbliche del framework**, non per parsare il tuo codice privato.
- Alternativa 100% gratuita senza chiamate esterne: affidarsi ai file di docs/versioni già presenti nel repo + al grafo Serena.

### 2.4 Interfaccia operativa (opzionale) — gratuito

**GitHub MCP Server** — `github/github-mcp-server` · ufficiale · gratis
- Interfaccia operativa in **read-only** per l'apprendimento: leggere file a un commit specifico, ispezionare issue/PR, analizzare workflow CI.
  ```bash
  docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN=<token> -e GITHUB_READ_ONLY=1 ghcr.io/github/github-mcp-server
  ```
- Composizione tipica: il grafo/DeepWiki spiega *dove* e *come*, il GitHub MCP legge il file esatto al commit esatto.

---

## 2bis. Tool community & open source (da Reddit / dev.to / GitHub)

Approfondimento sulle scoperte dalla community. Tutti gratuiti/OSS salvo dove indicato. Alcuni si sovrappongono ai precedenti: qui evidenzio quelli che aggiungono un pezzo mancante (repo map alla Aider, diagrammi Mermaid, doc generation locale con Ollama, plugin di mappatura con subagent).

### 2bis.1 Repo map "alla Aider" — struttura via PageRank + tree-sitter

Approccio nato in **Aider** (aider.chat): costruisce una mappa dell'intero repo estraendo definizioni/riferimenti dei simboli con **tree-sitter**, poi usa **PageRank** per rankare i simboli più importanti e comprimere la mappa nel budget di token. È l'idea alla base di "far capire la struttura senza leggere tutto". Battle-tested (Aider processa ~15B token/settimana con questo sistema).

**RepoMapper** — `pdavis68/RepoMapper` · OSS · gratis, locale
- Estrae il "Repo Map" di Aider come **CLI standalone + MCP server** (STDIO). Tree-sitter per il parsing, PageRank per il ranking, binary search per stare nel limite di token, caching persistente. Supporta Python, JS, TS, Java, C/C++, Go, Rust e altri.
- Utile come primo layer di orientamento leggerissimo, senza database:
  ```bash
  python repomap.py . --map-tokens 2048
  ```

### 2bis.2 Codebase memory locale con hooks

**RepoRecall** — `@proofofwork-agency/reporecall` (npm) · OSS
- Memoria di codebase locale per Claude Code: indicizzazione AST tree-sitter (22 linguaggi), ricerca ibrida keyword + vettoriale, traversal del call-graph, hooks + MCP. Inietta contesto rilevante in ~5 ms **prima** che Claude inizi a ragionare. Alternativa più "automatica" (via hook) rispetto a interrogare il grafo a mano.

**codebase-graph** (dal toolkit rohitg00) · OSS
- Code intelligence MCP server: parsing tree-sitter AST 42 linguaggi, knowledge graph su FalkorDB, alta qualità di ricerca (MRR ~0.944). Nella stessa famiglia di CodeGraphContext ma con backend a grafo.

### 2bis.3 Grafo + diagrammi Mermaid auto-generati

**GitNexus** (dettagli aggiuntivi) — OSS · gratis
- Oltre al grafo (già in §2.1): il tool `generate_map` **auto-genera diagrammi Mermaid dell'architettura** dal knowledge graph — utilissimo per l'onboarding/apprendimento. `detect_impact` produce una checklist strutturata di rischio pre-commit.
- Su **Claude Code** ha l'integrazione più profonda: MCP tools + 4 agent skill (Exploring, Debugging, Impact Analysis, Refactoring) + hook PreToolUse/PostToolUse + file `AGENTS.md`/`CLAUDE.md` auto-generati.
- Ha anche una **web UI 100% client-side** (gitnexus.vercel.app): trascini un repo o uno ZIP e ottieni un grafo interattivo (Sigma.js/WebGL), tutto in browser via WASM (tree-sitter WASM, embeddings in-browser). Zero upload a server esterni.

### 2bis.4 Documentazione ingegneristica generata in locale (LLM locale)

**KT Studio** — `abdulkareemtpm` (dev.to) · open source, local-first
- Scansiona il repo e genera documentazione ingegneristica end-to-end strutturata usando **modelli locali via Ollama** — nessuna API a pagamento, il codice non lascia la macchina. Roadmap: import da git, indicizzazione semantica vettoriale, rigenerazione incrementale, architecture diffing tra versioni. Adatto a codice proprietario.

**GitSummarize** — OSS · gratis (free to try)
- Trasforma un repo GitHub in un hub di documentazione: summary e docs automatici, pensato per codebase grandi. Community-backed, open source.

**ExplainGitHub** — free per repo pubblici (no signup)
- Esplorazione rapida di repo pubblici: summary, mappe visive, chat AI su funzioni/struttura/architettura. Utile per studiare progetti OSS di riferimento dello stesso stack — **non** per codice privato.

### 2bis.5 Doc/architettura sincronizzate col repo (self-hostable)

**repowise** — `repowise.dev` · **AGPL-3.0** · open source, self-hostable
- "Legge la codebase prima, il diagramma dopo": indicizza il codice in dependency graph, git intelligence, docs auto-generate, decision log (ADR), dead code detection — ed espone tutto via **MCP tools** (9 tool). Pensato contro il "doc rot": rigenera le docs dal repo e le tiene in sync ad ogni commit. Ha un MCP server pubblico + repo GitHub attivo.
- ⚠️ Licenza AGPL-3.0: permissiva per uso interno/self-host, ma con obblighi di condivisione del sorgente se offri il servizio a terzi in rete. Valuta per uso interno.

### 2bis.6 Plugin Claude Code per mappare la codebase con subagent

**cartographer** (da `jqueryscript/awesome-claude-code`) · plugin Claude Code
- Mappa e documenta codebase di **qualsiasi dimensione** usando subagent AI in parallelo — l'approccio "parallel subagents" adatto al tuo caso (delega la scansione a worker isolati e raccoglie solo il riassunto).

**Subagent nativi di Claude Code** (built-in) — gratis
- Claude Code ha già i subagent `Explore` (read-only, ottimizzato per cercare/analizzare codebase con livelli quick/medium/very thorough) e `Plan` (ricerca per il planning in read-only). Per l'apprendimento puro puoi appoggiarti a **Explore** senza installare nulla, tenendo i risultati fuori dalla conversazione principale.

**Cataloghi community da cui pescare subagent/skill pronti:**
- `VoltAgent/awesome-claude-code-subagents` — 150+ subagent specializzati, installabili come plugin marketplace.
- `0xfurai/claude-code-subagents` — 100+ subagent "expert" per stack/tool (python-expert, react-expert, prisma-expert...), da mettere in `~/.claude/agents/`.
- `rohitg00/awesome-claude-code-toolkit` e `GetBindu/awesome-claude-code-and-skills` — directory ampie di skill/hook/command/MCP.
- `jqueryscript/awesome-claude-code` — lista curata (contiene cartographer e altri plugin di mappatura/memoria).

> Nota metodologica: molti "tool AI" citati nelle liste 2026 (Cursor, Copilot X, DocuWriter, Google Code Wiki, GitBook, ecc.) sono commerciali o SaaS a pagamento per il caso d'uso rilevante; sono stati **volutamente esclusi**. Qui restano solo OSS/gratuiti coerenti col vincolo.

---

## 3. Stack consigliato (minimale → completo) — tutto gratuito

**Tier 1 — essenziale (100% locale, gratis, privacy-safe):**
- Serena (grafo semantico LSP)
- Repomix (snapshot consolidato del progetto)

**Tier 2 — repo grandi / call-graph interrogabile (locale, gratis):**
- + CodeGraph *oppure* codebase-memory-mcp (call chain, impact analysis)

**Tier 3 — materiale di apprendimento persistente + riferimento stack:**
- + deepwiki-skill (docs citate a riga, locale)
- + Context7 per le docs pubbliche dello stack (tier gratuito, con parsimonia)
- + DeepWiki MCP **solo se il repo è pubblico**

> Tier 1 e 2 girano **interamente in locale** senza inviare codice a servizi esterni — ideale per un progetto proprietario. DeepWiki pubblico e Context7 fanno chiamate esterne e non devono ricevere codice privato.

---

## 4. Artefatti da inserire nel template

### 4.1 `.mcp.json` (scope progetto, committabile) — solo tool locali gratuiti

```json
{
  "mcpServers": {
    "serena": {
      "command": "serena",
      "args": ["start-mcp-server", "--context", "claude-code", "--project-from-cwd"]
    },
    "repomix": {
      "command": "npx",
      "args": ["-y", "repomix", "--mcp"]
    }
  }
}
```

Aggiunte opzionali (commentabili a seconda del progetto):
```jsonc
// repo grande: call-graph interrogabile
"codegraph": { "command": "npx", "args": ["-y", "@colbymchenry/codegraph", "mcp"] }

// docs stack pubbliche (tier gratuito Context7; NON parsare codice privato)
"context7": { "command": "npx", "args": ["-y", "@upstash/context7-mcp@PINNED_VERSION"] }

// SOLO se il repo è pubblico
"deepwiki": { "type": "http", "url": "https://mcp.deepwiki.com/mcp" }
```
> Pinna sempre le versioni. Committare `.mcp.json` fa sì che chi clona veda il prompt di approvazione dei server.

### 4.2 `.claude/commands/learn-repo.md` (slash command `/learn-repo`)

```markdown
---
description: Guida interattiva all'apprendimento di questa repository
---
Sei un tutor tecnico. Il progetto è FINITO di sviluppare e devo IMPARARLO, non modificarlo.

Procedi in fasi, fermandoti dopo ognuna per farmi domande di verifica:

1. **Panoramica**: usa Repomix (o il file tree) per darmi lo stack, i moduli
   principali e il punto di ingresso. Identifica il paradigma architetturale
   dominante (layered, hexagonal, event-driven, MVC...).
2. **Astrazioni centrali**: usa Serena (find_symbol / find_references) per
   elencare le 5-8 astrazioni chiave e come si collegano. Per ognuna mostra
   uno SNIPPET PRECISO con path e range di righe.
3. **Flussi**: traccia 1-2 flussi end-to-end (es. una request dal controller
   al DB) citando i simboli reali del call graph.
4. **Design puro**: spiega i design pattern e i principi (SOLID, DI, ecc.)
   effettivamente usati, ancorando ogni affermazione a codice reale.
5. **Idiomi dello stack**: confronta l'uso del framework nel progetto con le
   best practice della versione in uso (Context7 solo per docs pubbliche).

Regole:
- Ogni affermazione tecnica DEVE puntare a codice reale (path:riga) o a docs pubbliche.
- Niente spiegazioni generiche scollegate dal codice.
- Non modificare mai i file. Solo lettura.
- Alla fine di ogni fase proponimi 2 domande per autovalutarmi.
```

### 4.3 `.claude/agents/code-tutor.md` (subagent dedicato)

```markdown
---
name: code-tutor
description: Tutor read-only che spiega la codebase con riferimenti precisi al codice
tools: Read, Grep, Glob, mcp__serena__*, mcp__repomix__*
---
Sei un tutor di software design. Obiettivo: farmi CAPIRE questa repository.
- Preferisci sempre i tool semantici (Serena) a grep/read a tappeto.
- Ogni concetto va illustrato con uno snippet reale (path + righe).
- Collega il codice ai paradigmi dello stack e ai principi di design.
- Non scrivi né modifichi codice. Read-only.
```

### 4.4 `docs/learning/` generato (output persistente, gratuito)

A fine progetto, genera docs citate a riga con **deepwiki-skill** (locale, gratis), poi affinale con il subagent `code-tutor` per aggiungere gli snippet mancanti. Nessun servizio esterno richiesto.

---

## 5. Workflow end-to-end (a progetto finito)

1. **Indicizza**: avvia Serena su cwd; opzionale CodeGraph/codebase-memory per il call graph.
2. **Snapshot**: Repomix genera la vista consolidata del progetto.
3. **Genera scheletro**: deepwiki-skill produce `docs/learning/*.md` con citazioni a riga.
4. **Sessione guidata**: `/learn-repo` (o il subagent `code-tutor`) ti accompagna fase per fase, con snippet reali dal grafo semantico.
5. **Persisti**: salvi il materiale arricchito nel repo così resta consultabile.

---

## 6. Sicurezza & privacy (checklist)

- I server MCP locali eseguono codice arbitrario: aggiungi solo sorgenti fidate e rivedi la config prima di avviarli.
- **Pinna le versioni** di ogni server MCP (evita `@latest` floating) — finding critico ricorrente negli audit.
- Usa **read-only** dove disponibile (GitHub MCP `GITHUB_READ_ONLY=1`).
- Per **codice proprietario**: resta su tool 100% locali (Serena, CodeGraph, codebase-memory, CodeGraphContext, GitNexus, Repomix su dir locale, deepwiki-skill). **Non** inviare codice privato a DeepWiki pubblico o a Context7.
- Non mettere segreti/token in `.mcp.json` committato; usa variabili d'ambiente.

---

## 7. Strumenti esclusi (a pagamento per il caso d'uso) e perché

| Strumento | Motivo esclusione | Sostituto gratuito |
|---|---|---|
| PocketFlow Tutorial-Codebase-Knowledge | Richiede una LLM API a consumo (es. Gemini API key) per generare i tutorial | deepwiki-skill (gira dentro Claude Code, nessuna API extra) |
| DeepWiki su repo privati / Devin MCP | Indicizzazione di codice privato solo a pagamento | Tool locali §2.1 + deepwiki-skill |
| Context7 su repo privati | Parsing di repo privati fatturato ($25/1M token) | Usare Context7 solo per docs pubbliche; per il codice affidarsi a Serena |
| Serena JetBrains backend | Tier a pagamento (refactoring avanzati) | Backend LSP gratuito di Serena |

> Nota su Context7: il tier gratuito esiste ma è limitato (1.000 chiamate/mese) e i repo privati sono a pagamento. È incluso in §2.3 solo per le **docs pubbliche dello stack**, non per il codice del progetto.

---

## 8. Tabella di sintesi — solo gratuiti

| Strumento | Ruolo | Locale | Licenza/Costo | Install |
|---|---|---|---|---|
| Serena | Grafo semantico LSP | ✅ | MIT · gratis | `uv tool install serena-agent` + `claude mcp add` |
| CodeGraph | Knowledge graph auto-sync | ✅ | MIT · gratis | `@colbymchenry/codegraph` |
| codebase-memory-mcp | Grafo AST 158 ling., binario | ✅ | OSS · gratis | binario statico |
| CodeGraphContext | Grafo + visualizzazioni | ✅ | OSS · gratis | CLI/wizard |
| GitNexus | Grafo + impact analysis | ✅ | OSS · gratis | MCP-native |
| Repomix | Snapshot consolidato | ✅ | OSS · gratis | `npx repomix --mcp` |
| deepwiki-skill | Docs citate a riga | ✅ | OSS · gratis | Claude Code Skill |
| RepoMapper | Repo map PageRank + tree-sitter | ✅ | OSS · gratis | `python repomap.py` / MCP |
| RepoRecall | Memoria codebase + hooks | ✅ | OSS · gratis | `@proofofwork-agency/reporecall` |
| KT Studio | Docs ingegneristiche via Ollama | ✅ | OSS · gratis | local-first |
| GitSummarize | Hub docs da repo | ✅ | OSS · gratis | OSS |
| repowise | Docs/grafo in sync col repo | ✅ | AGPL-3.0 · gratis | self-host + MCP |
| cartographer | Mappa codebase (parallel subagents) | ✅ | plugin CC · gratis | Claude Code plugin |
| Subagent Explore (built-in) | Ricerca/analisi read-only | ✅ | incluso · gratis | nativo Claude Code |
| DeepWiki MCP | Q&A architetturale (repo pubblici) | ❌ (HTTP) | Gratis (solo OSS pubblico) | `claude mcp add -t http` |
| ExplainGitHub | Esplorazione repo pubblici | ❌ | Free (solo pubblico) | web |
| Context7 | Docs stack version-specific (pubbliche) | ❌ | Tier gratuito (1k/mese) | `npx @upstash/context7-mcp` |
| GitHub MCP | Interfaccia operativa repo (read-only) | ✅/remoto | Ufficiale · gratis | Docker / hosted |

---

## 9. Fonti principali

- Serena: github.com/oraios/serena · mcp.directory/blog/serena-mcp-complete-guide-2026
- CodeGraph: github.com/colbymchenry/codegraph · tosea.ai/blog/codegraph-claude-code-cursor-guide-2026
- codebase-memory-mcp: github.com/DeusData/codebase-memory-mcp · arXiv:2603.27277
- CodeGraphContext: github.com/CodeGraphContext/CodeGraphContext
- GitNexus: marktechpost.com (24 apr 2026)
- Repomix MCP: repomix.com/guide/mcp-server
- DeepWiki MCP: mcp.directory/blog/deepwiki-mcp-complete-guide-2026
- deepwiki-skill: agent-skills.cc/skills/natsu1211-deepwiki-skill
- Context7 (licenza MIT + pricing free tier): github.com/upstash/context7 · context7.com/plans · blog.devgenius.io (gen 2026)
- GitHub MCP: github.com/github/github-mcp-server
- Claude Code MCP / subagents: code.claude.com/docs/en/mcp-quickstart · code.claude.com/docs/en/sub-agents
- Repo map Aider: aider.chat/2023/10/22/repomap.html · RepoMapper: github.com/pdavis68/RepoMapper
- RepoRecall / codebase-graph: github.com/rohitg00/awesome-claude-code-toolkit
- KT Studio: dev.to/abdulkareemtpm (feb 2026) · GitSummarize/ExplainGitHub: kdnuggets.com (5 free AI tools, mar 2026)
- repowise (AGPL-3.0): repowise.dev/blog/comparisons/best-architecture-documentation-tools
- cartographer + cataloghi: github.com/jqueryscript/awesome-claude-code · VoltAgent/awesome-claude-code-subagents · 0xfurai/claude-code-subagents · GetBindu/awesome-claude-code-and-skills
