---
name: research-scoping
description: >
  Definisce lo scope di un nuovo filone di ricerca prima di cercare o leggere alcun paper: domanda
  di ricerca, dominio disciplinare, tipo di revisione (sistematica o narrativa), orizzonte
  temporale, lingue accettate, e le scelte architetturali che dipendono dal contesto specifico
  dell'utente (libreria Zotero esistente o da zero, output LaTeX o Word, livello di autonomia,
  abbonamenti istituzionali disponibili). Usare all'inizio di un nuovo topic di ricerca, prima di
  invocare literature-search, e ogni volta che il progetto viene integrato in un contesto piu'
  ampio con altri pacchetti gia' presenti.
disable-model-invocation: true
---

## Premessa

Questa skill copre lo stadio 1 della pipeline a stadi (sezione 9, punto 1) e le domande di gate della sezione 18 di `research-vault/reference/claude-ricercatore-universitario-completo.md`. Non produce ricerca: produce lo scope entro cui la ricerca successiva (skill `literature-search`) e le altre skill del pacchetto operano.

## Domande da porre all'utente

Se non gia' chiarite in conversazione, la skill pone esplicitamente le seguenti domande prima di procedere, senza assumere risposte di default.

Qual e' il dominio disciplinare della ricerca, per calibrare quali database privilegiare (PubMed per biomedicina, DBLP per informatica, e cosi' via). Esiste gia' una libreria Zotero o JabRef da collegare, o si parte ex novo. Il progetto deve produrre output in LaTeX/Overleaf o in Word, perche' questo cambia quale MCP Zotero conviene attivare (vedi `../PACKAGES.md`, riga `zotero-mcp`). Quale livello di autonomia desidera l'utente: Claude propone sempre e aspetta conferma, oppure puo' procedere automaticamente su ricerca e verifica e chiedere conferma solo prima di scrivere il testo finale. Le nove modalita' di `corpus-analysis` vanno esposte come comandi espliciti o richiamate implicitamente quando Claude riconosce l'intento. A quali abbonamenti istituzionali a pagamento ha accesso l'utente, perche' determina quali fonti a pagamento configurare per prime. Se questo pacchetto va integrato in un progetto piu' ampio gia' esistente, quali altri pacchetti o moduli sono gia' presenti, per evitare sovrapposizioni con gestori di citazioni o skill di scrittura gia' definiti altrove.

## Il prompt di scoping

Oltre alle domande di gate, la skill definisce con l'utente la domanda di ricerca vera e propria, seguendo lo schema dello stadio 1: la domanda di ricerca in una frase, il tipo di revisione attesa (systematic review, narrative review, o esplorazione libera), l'orizzonte temporale delle fonti accettate, e le lingue accettate per i paper.

## Istruzioni custom da incollare nel progetto Claude

Quando lo scope si materializza in un progetto dedicato di Claude.ai (una cartella "Progetti" per topic, secondo il pattern condiviso dall'utente via screenshot, account `@techwith.ram`, non parte del documento di riferimento originale del pacchetto), queste istruzioni custom vanno incollate nelle impostazioni del progetto una sola volta, sostituendo `[FIELD / TOPIC]` con il dominio disciplinare raccolto in questo stesso gate. Rendono operativo a livello di progetto lo stesso principio quote-first gia' imposto dalla regola `no-uncited-claims`, cosi' che ogni conversazione futura in quel progetto lo rispetti senza doverlo ripetere ogni volta.

```
ROLE
You are a research assistant covering [FIELD / TOPIC].

CRITICAL RULES — FOLLOW THESE IN EVERY RESPONSE

1. SOURCE DISCIPLINE
   - Use ONLY the papers uploaded to this project as your evidence base.
   - For every finding, number, or method you cite, you MUST first provide
     the exact quote from the source, including the paper title and the
     section/page where it appears.
   - Format: [Paper Title, Section/Page]: "exact quote" → then your claim.
   - If you cannot find a supporting quote in the uploaded papers,
     do NOT make the claim. State: "Not found in uploaded papers."
   - Never use general knowledge or assumptions to fill gaps.

2. EVIDENCE QUALITY
   - Prioritise the strongest, most recent evidence available.
   - When findings conflict, surface the disagreement — don't pick one.
   - Flag status explicitly: "(preprint — not yet peer reviewed)".

3. TRANSPARENCY
   - If a question cannot be answered from the papers, say so clearly.
   - Mark any inference or interpretation as: (inferred from [source]).
   - Never present inferences as established findings.

4. STRUCTURE
   - Use clear section headers.
   - Keep paragraphs short.
   - Define jargon on first use — plain English.
```

Il vincolo "solo dai paper caricati" imposto qui si applica dentro le conversazioni del progetto, dove Claude non ha modo di distinguere una fonte verificata da `citation-tracker` da un semplice upload dell'utente: resta comunque `citation-tracker`, non queste istruzioni custom, il meccanismo che decide se una fonte puo' entrare nel testo finale o nel `.bib`. Le due regole non sono in conflitto, coprono livelli diversi: questa e' la disciplina di citazione dentro una singola conversazione, quella e' la tripartizione verificata/da verificare/scartata a livello di intero progetto.

## Output

Le risposte si registrano in `research-vault/scope.md` (creato alla prima invocazione se assente), con una sezione per la domanda di ricerca e una tabella con le risposte alle domande di gate. Se il progetto usa gia' `.claude/context/current-work.md` per la feature attiva, lo scope vi si aggiunge come sezione dedicata invece di duplicare il file. Questo documento e' quello che `literature-search` e le altre skill leggono per sapere come operare in questo progetto specifico, invece di richiedere le stesse domande ogni volta.
