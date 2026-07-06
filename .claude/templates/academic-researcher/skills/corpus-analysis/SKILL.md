---
name: corpus-analysis
description: >
  Applica una o piu delle dieci modalita della Corpus Analysis Suite a un corpus di paper gia
  caricati nella conversazione corrente: Intake Protocol, Contradiction Finder, Citation Chain,
  Gap Scanner, Methodology Audit, Master Synthesis, Assumption Killer, Knowledge Map Builder, So
  What Test, e Canon Update per quando arriva un paper nuovo dopo che il corpus e' gia' stato
  analizzato. Non cerca nuovi paper, quello e' compito di literature-search, e non attinge a
  conoscenza esterna del modello: lavora solo sui paper gia' forniti nella conversazione. Usare
  quando l'utente chiede di analizzare, confrontare, sintetizzare o mappare un insieme di paper
  gia' condivisi, per nome della modalita' o per intento equivalente.
disable-model-invocation: true
---

## Premessa

Questa skill trascrive fedelmente i nove prompt della Corpus Analysis Suite documentati nella sezione 10 di `research-vault/reference/claude-ricercatore-universitario-completo.md`, che resta la fonte di verita' in caso di ambiguita' interpretativa per quelle nove modalita'. La decima modalita', Canon Update, non fa parte di quel documento: proviene da un metodo a piu' step condiviso dall'utente tramite screenshot di un post pubblico (account `@techwith.ram`), aggiunto qui perche' opera esattamente sullo stesso materiale (un corpus gia' caricato) delle altre nove, non su una ricerca di paper nuovi. Ogni modalita' assume che i paper siano gia' stati caricati o forniti nella conversazione corrente: se il corpus non e' ancora stato tracciato dalla skill `citation-tracker`, invocarla prima, cosi' le citazioni generate da queste modalita' si riferiscono solo a paper nello stato verificata, come richiesto dalla regola `no-uncited-claims`.

## Come si sceglie la modalita'

L'utente puo' chiedere una modalita' per nome (per esempio "fai il Gap Scanner su questi paper") oppure descrivere l'intento in linguaggio naturale, nel qual caso la modalita' piu' vicina si sceglie dalla tabella seguente.

| Modalita' | Cosa produce |
|---|---|
| 1. The Intake Protocol | Tabella autore/anno/claim, 2-5 cluster tematici, contraddizioni dirette flaggate |
| 2. The Contradiction Finder | Tabella di 5-10 contraddizioni con causa radice del disaccordo |
| 3. The Citation Chain | Storia intellettuale dei 3 concetti piu' ricorrenti: origine, sfida, raffinamento, stato attuale |
| 4. The Gap Scanner | 5 gap di ricerca ranked, con causa, paper piu' vicino e percorso di risoluzione |
| 5. The Methodology Audit | Classificazione metodologica, sintesi delle tendenze, metodologia piu' debole |
| 6. The Master Synthesis | Sintesi in 400 parole: consenso, dibattiti attivi, evidenza piu' forte, domanda aperta chiave |
| 7. The Assumption Killer | 5-8 assunzioni condivise mai testate, con rischio e conseguenza |
| 8. The Knowledge Map Builder | Outline strutturato: claim centrale, pilastri, zone contese, domande di frontiera, reading list |
| 9. The So What Test | Sintesi divulgativa in 3 punti: provato, ignoto, perche' conta |
| 10. The Canon Update | Confronto strutturato di un paper nuovo contro il corpus gia' analizzato: claim vs evidenza, risultato vs canone, cosa cambia davvero |

Ordine consigliato su un corpus nuovo, quando l'utente non ne chiede una specifica: 1, poi 5, 2, 3, 4, 7, 8, 6, e infine 9 come chiusura divulgativa. La modalita' 10 non entra in questo ordine iniziale: si usa solo in un momento successivo, quando un paper nuovo si aggiunge a un corpus gia' passato almeno dall'Intake Protocol.

## I nove prompt, testo integrale

Ogni prompt va eseguito cosi' come scritto, senza parafrasi: sono gia' collaudati e la loro formulazione precisa (numero di elementi richiesti, formato tabellare, vincoli di lunghezza) fa parte del risultato atteso.

### 1. The Intake Protocol

```
I'm going to share [NUMBER] papers on [TOPIC]. Before I ask any questions, please do the following:

1. List every paper in a table with columns: Author(s) | Year | Core Claim (one sentence, ≤20 words). If a paper has no explicit thesis, infer the central argument from its conclusions.

2. Group the papers into 2-5 clusters based on shared theoretical assumptions or frameworks. Name each cluster and briefly explain (1-2 sentences) what unites the papers within it.

3. Flag any direct contradictions between papers — where two or more authors make mutually exclusive claims about the same phenomenon. List each as: Paper A vs. Paper B — contested claim.

Do not summarize each paper individually. Focus only on the three tasks above.
```

### 2. The Contradiction Finder

```
Across all uploaded papers, identify the most significant points where two or more authors make claims that directly contradict each other.

Only include genuine contradictions — mutually exclusive claims on the same issue. Exclude cases of mere difference in emphasis or scope.

Present your findings as a table with the following columns:
| Contested Claim | Position A (Paper, Year) | Position B (Paper, Year) | Root Cause of Disagreement |

For Root Cause, choose from: methodology, dataset, time period, definition of terms, or other (explain). Aim for 5-10 contradictions. If fewer exist, list all you find.
```

### 3. The Citation Chain

```
From the uploaded papers, identify the 3 concepts that appear most frequently across multiple papers (referenced by name, debated, or built upon).

For each concept, trace its intellectual history using only the evidence in the uploaded papers:

Concept Name:
- Origin: Who first introduced or defined it (within this set)?
- Challenge: Which paper(s) questioned or challenged it, and how?
- Refinement: Which paper(s) modified or extended it, and how?
- Current Status: Settled, contested, or still evolving — based on this literature?

Present each concept as a structured outline. If a concept lacks a clear challenger or refinement in these papers, state that explicitly rather than guessing.
```

### 4. The Gap Scanner

```
Based only on the uploaded papers, identify the 5 most significant research gaps that these papers collectively acknowledge, imply, or fail to address.

For each gap:
- Gap: [State the unanswered question clearly in 1-2 sentences] Why it exists: Choose from — methodological barrier, lack of data, topic too niche, assumed but untested, or ethical/logistical constraint. Explain briefly.
- Closest paper: Which uploaded paper came closest to addressing it, and where did it fall short?
- Path to resolution: What would be needed to close this gap (methodology, data, resources, etc.)?

Rank the 5 gaps from most to least significant, and briefly explain your ranking criterion (e.g., theoretical importance, practical impact, feasibility of resolution).

If fewer than 5 genuine gaps exist, list all you can identify and explain why the set is limited.
```

### 5. The Methodology Audit

```
Compare the research methodologies used across all uploaded papers.

Step 1 — Classification Table
- Create a table: Paper (Author, Year) | Methodology Type | Data Source | Sample Size (if stated) | Key Limitation Noted by Authors. Use the methodology type that best fits each paper. Don't force papers into the categories below — add new categories as needed: Suggested types: Survey, Experiment (RCT), Quasi-experiment, Simulation, Meta-analysis, Case study, Computational/ML, Literature review, Ethnography, Secondary data analysis.

Step 2 — Synthesis
- Which methodology type appears most frequently? Suggest why based on the papers' stated rationale.
- Which methodology is absent or rare despite being relevant to the research questions?

Step 3 — Weakest Methodology
- Identify the paper whose methodology is most vulnerable to criticism. Evaluate using these criteria: sample size adequacy, control for confounds, replicability, and transparency of reporting. State which criterion it fails most clearly.
```

### 6. The Master Synthesis

```
Using the uploaded papers as your only source, write a synthesis of this body of literature. Do NOT summarize individual papers. Instead, write across the entire literature:

1. Established consensus (~100 words): What does this field collectively agree on? Cite at least 2 papers that support each claim you make here.

2. Active debates (~100 words): What do researchers in this field meaningfully disagree about? Name the disagreeing positions without naming individual papers.

3. Strongest evidence (~100 words): What claims in this literature are supported by the most consistent, replicated, or methodologically robust evidence?

4. The key open question (~80 words): End with the single most important unanswered question in this field — the one whose resolution would most change the others.

Total: 400 words maximum. No hedging phrases like "it seems" or "some argue." State clearly.

If the papers lack sufficient consensus to populate a section, say so explicitly.
```

### 7. The Assumption Killer

```
From the uploaded papers, identify the 5-8 most consequential assumptions that the majority of these papers share but never explicitly test, justify, or acknowledge as assumptions.

Focus on assumptions that are:
(a) foundational to the conclusions drawn, and
(b) plausibly false or context-dependent.

For each assumption:
- Assumption: [State it as a declarative claim, e.g., "X causes Y under all conditions"] Shared by: Name 2-3 papers that rely on it most heavily.
- Risk level: Rate as Low / Medium / High based on how much the literature would be undermined if the assumption is false.
- Consequence: Explain what would change — would conclusions need revision (low impact), key findings be invalidated (medium), or the entire research paradigm collapse (high)?

Rank assumptions from most to least consequential.
```

### 8. The Knowledge Map Builder

```
Based only on the uploaded papers, create a structured knowledge map of this literature. Present it as a clean outline (no prose paragraphs).

KNOWLEDGE MAP

1. Central Claim: The single proposition that most of this field's work tries to support, challenge, or refine. If no single claim unifies the field, name 2 competing centres instead.

2. Supporting Pillars (3-5): Well-established sub-claims with strong evidentiary support across multiple papers.
For each: [Claim] — supported by: [Paper 1], [Paper 2]

3. Contested Zones (2-3): Areas of genuine, active disagreement. For each: [Issue] — [Position A] vs. [Position B]

4. Frontier Questions (1-2): Questions this literature raises but cannot yet answer. State as explicit questions.

5. Newcomer Reading List (3 papers): For each paper, state: [Author, Year] — why a newcomer should read this first.
Selection criterion: foundational to understanding the field, not just most cited.
```

### 9. The 'So What' Test

```
Summarize this entire body of research for a smart non-expert who has never read any of it. Respond in exactly three numbered points. Each point should be 2-3 sentences maximum.

Write as if speaking to an intelligent person with no domain knowledge.

1. What has been proven: The strongest, most reliable finding from this literature — stated as a direct claim with no hedging. No "suggests" or "may indicate."

2. What is still unknown: The most significant thing this field has not yet figured out — stated honestly, without minimizing the uncertainty.

3. Why it matters: The single most important real-world implication. If no direct application exists, state the biggest theoretical consequence instead.

Rules: No jargon. No citations. No qualifications that weaken the core point.

If you cannot make a statement confidently based on the papers, say so — don't fabricate certainty.
```

### 10. The Canon Update

Si esegue quando un paper nuovo viene caricato nel progetto dopo che il corpus esistente e' gia' stato analizzato con una o piu' delle nove modalita' precedenti: confronta il nuovo arrivato contro il canone gia' stabilito, invece di analizzarlo isolatamente.

```
Using ONLY the documents in this project, and following the quote-first sourcing rules in the project instructions:

ROLE — You are a research assistant covering [FIELD / TOPIC].
TASK — Analyse the new paper I just uploaded, comparing it to the canon and prior findings already in this project. Quote the source first (with paper title), then interpret. Answer the core questions:

SECTION 1 — CLAIM VS EVIDENCE
- What does the paper claim to contribute?          → exact quote
- What did the authors actually show?                → exact quote from results
- Strong / Mixed / Weak — quantify where possible
- Is the contribution new, or a relabel of prior work?
- Is the claim supported by data, or mostly framing?
End with: short judgment on how much to trust this result.

SECTION 2 — RESULT VS THE CANON (for each key result)
- This paper's finding (quote source)
- The prior consensus in the project (quote source)
- Agreement, extension, or contradiction
- What it signals for the field
- Whether it survives the project's skeptic memo

SECTION 3 — WHAT ACTUALLY CHANGED?
- What does this genuinely add?
- What does it overturn?
- What is newly possible (method, data, benchmark)?
- What did NOT change despite the paper's framing?

FINAL SUMMARY
- Evidence quality: Strong / Mixed / Weak
- Novelty: High / Incremental / Recycled
- Field impact vs the hype: Bigger / Same / Smaller
```

La riga "the project's skeptic memo" nella Sezione 2 presuppone che il paper o l'idea di riferimento del canone sia gia' passato dal memo Skeptic's Teardown di `deep-paper-reading`: se non lo e' ancora, quel controllo si salta esplicitamente invece di inventare un esito. Ripetere l'Intake Protocol (modalita' 1) sull'intero corpus ampliato resta comunque raccomandato dopo alcuni Canon Update accumulati, per aggiornare cluster e contraddizioni sul corpus nella sua forma corrente.

## Vincoli non negoziabili

Tutte e dieci le modalita' dicono esplicitamente di basarsi solo sui paper caricati o allegati: questo vincolo va rispettato alla lettera, coerentemente con la regola `no-uncited-claims` del pacchetto. Nessuna modalita' attinge a conoscenza generale del modello per completare un punto lasciato incompleto dal corpus fornito, nemmeno quando sembrerebbe utile. Le modalita' 2, 6, 7, 8 e 10 chiedono esplicitamente di citare paper a supporto di ogni claim: quelle citazioni devono riferirsi solo a paper nello stato verificata secondo `citation-tracker`. Se l'utente carica paper nuovi durante la sessione, si ri-esegue almeno l'Intake Protocol prima di riusare le altre modalita', per aggiornare cluster e contraddizioni sul corpus ampliato; la modalita' 10 e' l'alternativa mirata quando serve solo confrontare il singolo paper nuovo contro il canone, senza rifare l'Intake Protocol ogni volta.
