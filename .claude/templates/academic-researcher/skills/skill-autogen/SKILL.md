---
name: skill-autogen
description: >
  Quando un topic disciplinare specialistico ricorre attraverso piu' paper o piu' sessioni di
  ricerca, propone la creazione di una nuova skill dedicata per quel topic invece di reinserire
  lo stesso contesto ogni volta, seguendo il formato di skill-creator. Dispone gia' di un'euristica
  di ricorrenza di default e di un prompt di proposta usabili da subito. PARZIALMENTE STUB: la
  soglia numerica esatta resta regolabile all'attivazione, per non generare sprawl di skill poco
  mantenibili su progetti con volumi di ricerca molto diversi.
disable-model-invocation: true
---

## Stato: parzialmente stub

Il documento di riferimento descrive questa capacita' come stadio 6 della pipeline (sezione 9 punto 6) e come obiettivo esplicito del progetto (sezione 1 punto 4, sezione 8), ma segnala anche un vincolo che impedisce di renderla automatica senza calibrazione: una nuova skill si crea solo quando un topic e' ricorrente e specialistico attraverso piu' sessioni, non per ogni singola query di ricerca (sezione 17). Cosa conti come "ricorrente" dipende dal volume di ricerca del progetto specifico, non e' un numero fisso che il documento definisca. L'euristica sotto fissa un default sensato per partire subito; resta regolabile senza cambiare il resto del flusso.

## Cosa e' gia' fissato

Lo strumento di generazione e' `skill-creator`, gia' disponibile come skill di esempio in ambiente Claude Code, che segue le best practice Anthropic di frontmatter, trigger description e progressive disclosure. Il pattern community citato come riferimento aggiuntivo e' `Skiller` (InternScience), che trasforma log di conversazione o requisiti in linguaggio naturale in pacchetti skill conformi. Prima di proporre una nuova skill, va sempre verificato che il topic non sia gia' coperto da una skill esistente nel progetto.

## Euristica di ricorrenza di default

Un topic diventa candidato a una skill dedicata quando compare come soggetto centrale, non come menzione di passaggio, in almeno due paper distinti gia' passati da `deep-paper-reading`, oppure in almeno due sessioni di ricerca distinte, e nessuna skill esistente in `.claude/skills/` lo copre gia'. Questa soglia (due occorrenze) e' un default di partenza, non un numero fissato dal documento di riferimento: su un progetto a volume di ricerca molto alto puo' generare proposte troppo frequenti e va alzata a tre o piu'; su un progetto piccolo puo' restare a due.

## Il prompt di proposta

Questo prompt e' elaborato per questo pacchetto, non estratto dal metodo esterno gia' citato nelle altre skill (quello screenshot, account `@techwith.ram`, non copre l'auto-generazione di skill): ne riprende pero' lo spirito di fondo, cioe' costruire una volta una struttura permanente per un argomento invece di reintrodurne il contesto ogni volta, lo stesso principio dietro il progetto-per-topic dello step "Permanent Home" gia' usato in `research-scoping`. Quando l'euristica sopra scatta, si presenta questa proposta all'utente prima di creare qualunque file.

```
ROLE
You are proposing a new specialized skill for this project.

TASK
The topic "[TOPIC]" has now appeared as a central subject in at least two distinct [papers / sessions] within this project. Before creating anything, present this proposal to the user for confirmation.

1. Topic: state it in one sentence.
2. Evidence of recurrence: list the papers or sessions where it appeared as a central topic (quote the source, not just a paraphrase).
3. Why a dedicated skill helps: what context would otherwise need to be reintroduced every time this topic comes up.
4. Overlap check: confirm no existing skill in .claude/skills/ already covers this topic, and list what was checked.
5. Proposed skill name and one-line trigger description, following skill-creator's frontmatter conventions.
6. Ask explicitly: "Do you want me to create this skill now with skill-creator?" — do not create it without an explicit yes.
```

## Cosa fare con la risposta dell'utente

Solo su conferma esplicita si invoca `skill-creator` con il nome e la descrizione proposti al punto 5. Un rifiuto, o un "non ancora", si registra come tale e non si ripropone la stessa skill alla prossima singola occorrenza del topic: si riattiva l'euristica solo se il topic continua a ricorrere oltre la soglia gia' raggiunta.

## Come completare la calibrazione di dominio

All'attivazione, si concorda con l'utente se la soglia di due occorrenze va alzata in base al volume di ricerca atteso del progetto, e si registra la soglia scelta in `research-vault/scope.md` cosi' che resti coerente tra sessioni diverse invece di essere ridecisa ogni volta.
