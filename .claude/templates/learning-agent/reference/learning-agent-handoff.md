# Handoff: Modulo "Learning Agent" per template di progetto Claude

> Documento di riferimento del pacchetto `learning-agent` (vedi `../README.md`). Integrato nel template il 2026-07-01 a partire dall'handoff originale dell'utente. È la fonte di verità per ogni scelta pedagogica e architetturale delle skill e degli agenti del pacchetto: in caso di dubbio interpretativo si consulta questo documento prima di improvvisare.
>
> Data ricerca: luglio 2026. Verifica sempre versioni e disponibilità dei repo prima di installare — i progetti community cambiano rapidamente.

---

## 0. Come usare questo file

Questo è un handoff di integrazione, non un tutorial. Alla creazione di un nuovo progetto dal template, copia le sezioni pertinenti in `.claude/` e in `CLAUDE.md`. L'ordine consigliato di lettura: architettura (§1) → stack tool/MCP (§2) → agenti e skill (§3) → pedagogia contestuale (§4) → adattamento neurodivergente (§5) → onboarding di sessione (§6) → checklist di setup (§7).

---

## 1. Architettura complessiva

Tre livelli disaccoppiati, così puoi sostituire ogni pezzo senza toccare gli altri:

1. **Knowledge base (ingestione + retrieval)** — dove finiscono i tuoi .docx/.pdf/libri. Esposta come MCP server locale interrogabile. Qui riusi le tue tecniche esistenti di parsing token-efficient a monte dell'indicizzazione.
2. **Motore di memoria dell'apprendimento (spaced repetition)** — traccia cosa hai imparato, cosa è "due", cosa fatichi a ricordare. Anki via MCP è lo standard de facto locale.
3. **Livello di orchestrazione (agenti/skill)** — il "tutor" che pianifica la roadmap, spiega, interroga, adatta stile e tecniche. Vive in `.claude/` come skill + subagent + slash command.

```
File (.docx/.pdf/libri)
   │  parsing token-efficient (tuo)
   ▼
[1] Knowledge Base MCP  ──query──►  [3] Orchestrazione (Tutor Agent)  ◄──review/schedule──►  [2] Anki MCP
                                          │
                                    profilo learner + roadmap + tecniche contestuali
```

Il livello 3 è l'unico obbligatorio per partire: puoi iniziare con la sola orchestrazione + file locali, e aggiungere KB-MCP e Anki quando serve.

---

## 2. Stack di tool e MCP server (locali, community)

### 2.1 Knowledge base / RAG locale

- **knowledge-mcp** (olafgeibig) — MCP server che è una knowledge base locale con RAG ibrido vettoriale + grafo basato su LightRAG. Ingesta PDF, testo, Markdown, DOCX, fa chunking, estrae entità/relazioni e costruisce sia knowledge graph sia embedding. Espone la ricerca via FastMCP a client MCP (Claude Desktop, IDE). Richiede Python 3.12 e `uv`. È il candidato più forte per "libri e documenti come base di apprendimento" perché il grafo aiuta con topic strutturati (es. dipendenze concettuali di React). Repo: `github.com/olafgeibig/knowledge-mcp`.
- **Local Knowledge RAG MCP** (patakuti) — ricerca semantica su documenti locali con embedding vettoriali; supporta più provider di embedding (OpenAI, Ollama, OpenAI-compatible). Adatto se vuoi restare 100% locale con Ollama.
- **mcp-local-rag** (nkapila6) — RAG "primitivo" che gira interamente in locale, senza API key; pensato più per web search locale che per document store, ma include Agent Skills che insegnano a Claude a usarne i tool. Utile come fallback per colmare lacune della KB con ricerca fresca.
- **DigitalOcean Knowledge Bases + MCP** — opzione gestita (non locale) se un domani vuoi hostare la KB fuori dalla macchina. Da tenere come alternativa, non come default.

**Nota sull'integrazione con il tuo parsing.** Il tuo pipeline di parsing token-efficient va *a monte* dell'ingestione: produci Markdown pulito/chunked e dai in pasto quello a knowledge-mcp invece dei PDF grezzi. Questo evita di pagare due volte in token (parsing + re-chunking) e ti lascia il controllo su come i libri vengono spezzati (per capitolo, per concetto, per lezione).

### 2.2 Spaced repetition / memoria

- **anki-mcp-server** (ankimcp, `ankimcp.ai`) — il più completo. Gira in locale, nessuna telemetria; fa da proxy tra l'AI e il plugin AnkiConnect locale. Permette creazione/modifica note al volo, gestione deck, e sessioni di review conversazionali ("Aiutami a ripassare il mazzo di spagnolo"). Distingue tool di *review* da tool di *editing/gestione* deck.
- **mcp-ankiconnect** (samefarrar, su PyPI) — minimale ma solido: `num_cards_due_today`, `get_due_cards`, `submit_reviews` (rating wrong/hard/good/easy). Install via `uv run --with mcp-ankiconnect mcp-ankiconnect`. Ottimo se vuoi solo il loop di ripasso senza feature extra.
- **@arielbk/anki-mcp** (npm) e **scorzeth/anki-mcp-server** — alternative TypeScript; il primo supporta generazione cloze/da-PDF e paginazione per non saturare la context window.

Prerequisito comune: Anki desktop + add-on **AnkiConnect** (plugin id `2055492159`). Su macOS disabilita AppSleep per Anki per evitare lentezza.

### 2.3 Orchestrazione (Claude Code)

- **Skills** — file Markdown con frontmatter YAML che caricano istruzioni solo quando invocati (costo token quasi nullo finché non servono). Il posto giusto per le "playbook" pedagogiche.
- **Subagents** — istanze isolate con context window propria; l'output verboso (lettura file, retrieval) resta isolato e torna solo il riassunto. Ideali per delegare l'ingestione/retrieval pesante e tenere pulita la sessione principale.
- **Slash commands** — entry a singolo file con autocomplete `/...` in terminale; buoni per innescare pipeline (es. `/learn`, `/review`, `/roadmap`).
- **Agent Teams** (sperimentale, disattivo di default via `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`) — più istanze che si coordinano tra loro. Usare solo se vuoi tutor "multipli" che si sfidano (es. spiegatore + esaminatore + revisore). Costa molti più token: non è il default consigliato.
- **Compilazione MCP → Skill** — tecnica citata dalla community per ridurre il consumo token dei tool MCP dell'80-98% impacchettandoli come skill. Da valutare una volta stabilizzati i tuoi MCP.

Repo/community utili: `wshobson/agents` (marketplace multi-harness di plugin/agent/skill), `awesome-claude-code-agents`, la directory ufficiale plugin di Anthropic, e `knowledge-work-plugins` (plugin per knowledge worker in Cowork/Code).

---

## 3. Agenti e skill del modulo (specifica implementata)

Struttura adottata dal pacchetto `learning-agent` (vedi `../README.md` per la mappa di istanziazione completa):

```
.claude/
  agents/
    tutor.md              # orchestratore pedagogico (subagent principale)
    kb-retriever.md       # subagent: interroga la KB, ritorna solo estratti rilevanti
    examiner.md           # subagent: genera domande di active recall e valuta risposte
  skills/
    learn-topic/SKILL.md  # playbook: pianifica roadmap + eroga lezione
    review-session/SKILL.md  # playbook: sessione spaced repetition via Anki MCP
    build-roadmap/SKILL.md   # playbook: costruisce/aggiorna la roadmap
  commands/
    learn.md              # /learn <topic>
    review.md              # /review
    profile.md              # /profile  → onboarding/aggiornamento profilo learner
CLAUDE.md                 # regole globali + puntatore al profilo learner
LEARNER_PROFILE.md        # stato del learner (topic, livello, profilo cognitivo, progressi)
```

### 3.1 `tutor.md` (subagent orchestratore)
Ruolo: legge `LEARNER_PROFILE.md`, decide se è momento di nuova lezione o di ripasso (interroga Anki MCP per i "due"), sceglie la tecnica contestuale (§4) e l'adattamento (§5), delega il retrieval a `kb-retriever` e la verifica a `examiner`. Non deve mai spiegare da memoria ciò che è nella KB: cita sempre gli estratti recuperati.

### 3.2 `kb-retriever.md` (subagent)
Ruolo: unico autorizzato a chiamare il KB-MCP. Ritorna estratti minimi e pertinenti + riferimenti (capitolo/pagina), mai il documento intero. Tiene la context window principale pulita.

### 3.3 `examiner.md` (subagent)
Ruolo: genera prompt di *active recall* (non riconoscimento), valuta le risposte, e propone card Anki per gli errori. Applica il testing effect: prima interroga, poi dà feedback.

### 3.4 Slash command minimi
- `/profile` → crea o aggiorna `LEARNER_PROFILE.md` (vedi §6 per le domande di onboarding, da porre con il tool a bottoni).
- `/learn <topic>` → se manca la roadmap la costruisce, poi eroga la prossima unità.
- `/review` → apre una sessione di ripasso guidata sui "due" di Anki.

---

## 4. Pedagogia contestuale: la tecnica si adatta al dominio

Principio guida: **spaced repetition + active recall (testing effect)** sono la base trasversale valida ovunque — rivedere a intervalli crescenti batte il cramming (fino a ~200% di ritenzione a lungo termine a parità di tempo di studio), e auto-interrogarsi batte la rilettura passiva (Roediger & Karpicke, 2006). Ma *cosa* si mette nelle card e *come* si struttura la pratica cambia radicalmente per dominio.

Un limite noto da codificare nell'agente: la ritenzione di un item isolato **non** implica saperlo applicare in contesto. Quindi le review devono includere task di produzione/applicazione, non solo richiamo di definizioni.

### 4.1 Lingua straniera (es. spagnolo)
- Unità di memoria: vocaboli, frasi, pattern di parole, pronuncia, regole grammaticali — molto materiale ad alto tasso di memorizzazione, terreno ideale per SRS.
- Regola pratica classica: meglio 10 esposizioni distribuite su 10 giorni che 100 nello stesso giorno.
- Card: cloze, coppie L2→L1 e L1→L2, audio se disponibile, frasi in contesto (non parole isolate).
- Pratica applicativa: produzione di frasi, mini-conversazioni, review "conversation-derived" (l'agente estrae da una conversazione libera gli errori e genera ripasso mirato, poi verifica con un mastery check).
- Gamification/motivazione (punti, streak) funziona bene qui.

### 4.2 Linguaggio di programmazione (es. React)
- Non è memorizzazione lessicale: è **comprensione compositiva** con dipendenze (non impari gli Hook prima dello stato/rendering).
- Roadmap a dipendenze strette: ogni modulo assume la padronanza dei precedenti (modello osservato in curricula tipo cc-self-train: sequenza rigida che costruisce comprensione compositiva).
- Ciclo dominante: **mini-lezione → pratica hands-on immediata a bassa pressione**. La spiegazione senza subito scrivere codice non attecchisce.
- Card/recall: non "cos'è useEffect" ma "dato questo bug, cosa manca nell'array di dipendenze?"; ricostruzione di snippet da memoria; spiegare il codice ad alta voce (self-explanation).
- Skill di supporto tipo *explain-code*: analogia dalla vita quotidiana → diagramma (anche ASCII) del flusso → walkthrough passo-passo. Codificalo nell'`examiner`/`tutor`.
- SRS qui si applica a pattern e API, non a sintassi banale che il tooling completa da solo.

### 4.3 Materia concettuale/matematica
- Costruire number sense / pattern e strategie visive prima della memorizzazione dei fatti.
- Flessibilità cognitiva > procedura rigida; molti percorsi di soluzione.

**Regola per l'agente:** in `build-roadmap` scegli il template pedagogico in base alla categoria del topic (lingua | programmazione | concettuale), non un unico schema.

---

## 5. Adattamento per profili neurodivergenti (ADHD, spettro autistico, dislessia)

All'apertura di sessione, se il learner segnala (o ha nel profilo) ADHD, disturbo dello spettro autistico, dislessia o altro, l'agente adatta **roadmap, stile e tecniche**. Non è diagnosi né consiglio clinico: sono adattamenti didattici opt-in dichiarati dall'utente.

Principio comune: **nessun approccio unico**; personalizzazione, pacing flessibile, approcci basati sui punti di forza e sugli interessi speciali. Dai sempre "permesso di sperimentare": ciò che funziona un mese può cambiare.

### 5.1 ADHD
- **Chunking**: unità piccole e finite; una sezione o un paragrafo alla volta, non un capitolo intero.
- **Pomodoro** (es. 25/5, ~30 min max a blocco) con pause di movimento; l'attività fisica migliora focus e cognizione.
- **Supporto alle funzioni esecutive**: checklist, whiteboard/tracker visibile, scadenze esplicite per scaricare la working memory.
- **Novità e sistemi personalizzati**: variare formato mantiene l'engagement; *body doubling* (studiare "in presenza" di qualcuno — l'agente può fare da presenza) aiuta l'avvio.
- Feedback immediato e frequente; obiettivi brevi e visibili.

### 5.2 Spettro autistico
- **Struttura e routine prevedibili**: stessa forma di sessione ogni volta, agenda esplicita all'inizio.
- **Interessi speciali come lente**: aggancia il topic all'interesse (es. spiegare gli state di React tramite un dominio che l'utente ama).
- **Ambiente sensoriale**: output sobrio, evita sovraccarico (poco colore lampeggiante, niente muri di testo); consenti pacing personale.
- **Istruzioni esplicite e letterali**: evita ambiguità, metafore poco chiare o sottintesi; enuncia i passi.

### 5.3 Dislessia e altre variazioni
- **Multi-sensoriale**: immagini, diagrammi, color coding; text-to-speech per materiali lunghi.
- Ridurre il carico reading-heavy; valorizzare problem-solving creativo.

### 5.4 Trasversali (utili a tutti)
- Apprendimento visivo: mind mapping, organizzatori grafici, diagrammi come "scaffolding" e ancora tangibile.
- Apprendimento attivo: insegnare a qualcun altro (feynman), flashcard, esperimenti hands-on.
- Feedback immediato e adattamento continuo del piano all'energia/interesse del momento.

**Come codificarlo:** nel `LEARNER_PROFILE.md` salva un blocco `cognitive_profile` con flag e preferenze; il `tutor` legge quel blocco e applica i modificatori sopra a dimensione delle unità, formato output, ritmo, e tipo di verifica.

---

## 6. Onboarding di sessione (profilo learner)

Alla prima sessione (o con `/profile`), l'agente raccoglie — idealmente con opzioni a bottoni, non testo libero — almeno:

1. **Topic e obiettivo** (es. "React per lavoro", "spagnolo conversazionale per viaggio").
2. **Categoria** (auto-inferita: lingua | programmazione | concettuale) → sceglie il template pedagogico (§4).
3. **Livello di partenza** (principiante / intermedio / avanzato).
4. **Tempo disponibile** per sessione e frequenza (guida la lunghezza dei chunk e lo scheduling SRS).
5. **Profilo cognitivo opt-in**: eventuali ADHD / spettro autistico / dislessia / nessuno → attiva i modificatori §5.
6. **Preferenze di stile**: visivo / testuale / hands-on; interessi speciali da usare come lente.

Esempio di blocco salvato in `LEARNER_PROFILE.md`:

```yaml
topic: "React"
category: programming
level: beginner
session_minutes: 30
cadence: "3x/week"
cognitive_profile:
  adhd: true
  autism: false
  dyslexia: false
style: [visual, hands_on]
special_interests: ["videogiochi retro"]
progress:
  roadmap_module: 2
  anki_deck: "react_core"
```

L'agente rilegge e aggiorna questo file a ogni sessione; è la fonte di verità dello stato di apprendimento.

---

## 7. Checklist di setup (nuovo progetto)

1. `[ ]` Copia lo scheletro `.claude/` (§3) nel nuovo progetto e adatta i puntatori in `CLAUDE.md`.
2. `[ ]` Scegli e installa **un** KB-MCP (default: `knowledge-mcp` con LightRAG; alternativa 100% locale: patakuti + Ollama). Registralo nel client MCP.
3. `[ ]` Collega il tuo pipeline di parsing token-efficient a monte dell'ingestione (produci Markdown chunked → ingest).
4. `[ ]` Installa Anki + AnkiConnect + un Anki-MCP (default: `anki-mcp-server`; minimale: `mcp-ankiconnect`). Su macOS disattiva AppSleep.
5. `[ ]` Implementa i tre subagent (`tutor`, `kb-retriever`, `examiner`) e i tre command (`/profile`, `/learn`, `/review`).
6. `[ ]` Implementa `build-roadmap` con i tre template pedagogici (§4) e i modificatori neurodivergenti (§5).
7. `[ ]` Testa il loop end-to-end: `/profile` → `/learn` (retrieval + lezione + recall) → card generate → `/review` sui "due".
8. `[ ]` (Opzionale) Valuta la compilazione MCP→Skill per ridurre i token, e Agent Teams solo se vuoi tutor multi-ruolo.

---

## 8. Rischi e note

- **Deriva dei repo community**: verifica manutenzione/versioni prima di dipenderci; alcuni Anki-MCP richiedono versioni minime di AnkiConnect.
- **Token**: retrieval e review possono gonfiare la context; isola sempre nei subagent e chiedi estratti minimi con riferimenti, mai documenti interi.
- **Ambito clinico**: gli adattamenti §5 sono opt-in e didattici; l'agente non diagnostica e, se emergono difficoltà che vanno oltre lo studio, suggerisce con garbo il supporto di una figura appropriata.
- **Copyright dei libri**: la KB è per uso personale di studio; l'agente cita estratti brevi e rimanda alla fonte, non riproduce interi capitoli in output.
- **Item vs applicazione**: ricorda nel design che ricordare ≠ saper applicare; includi sempre task di produzione nelle review.

---

## 9. Riferimenti principali

- knowledge-mcp (LightRAG): github.com/olafgeibig/knowledge-mcp
- Local Knowledge RAG MCP: lobehub.com/mcp/patakuti-local-knowledge-rag-mcp
- mcp-local-rag: github.com/nkapila6/mcp-local-rag
- anki-mcp-server: github.com/ankimcp/anki-mcp-server — ankimcp.ai
- mcp-ankiconnect: pypi.org/project/mcp-ankiconnect
- Claude Code — subagents/skills/hooks/agent teams: code.claude.com/docs
- wshobson/agents (marketplace): github.com/wshobson/agents
- cc-self-train (curriculum a dipendenze, pedagogia): arxiv.org/html/2604.17460v1
- Evidenze active recall / spaced repetition: Roediger & Karpicke (2006); Khan Academy "Learn to Learn"
- Strategie neurodivergenti: additudemag.com, sachscenter.com, neurolaunch.com, clickvieweducation.com
