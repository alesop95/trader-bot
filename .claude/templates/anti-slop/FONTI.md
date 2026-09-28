# Registro delle fonti: segni del testo e delle interfacce generate

> Registro delle fonti su cui poggiano la guida `GUIDA.md` di questo pacchetto, i due strumenti `tools/lint-prosa.py` e `tools/lint-ui.py`, la sezione sui segni della prosa in `.claude/rules/interaction-style.md` e la regola `rules/design-non-generico.md`. Ogni affermazione della guida che non viene da una misura propria rimanda a una voce di questo registro con la sua sigla fra parentesi quadre. La voce `S1` è la fonte visiva da cui il lavoro è partito; le voci `F` sono fonti pubblicate.

## Metodo

Le fonti pubblicate sono state lette il 2026-09-23 da due ricerche delegate, con il mandato di non scrivere nulla a memoria e di riportare solo ciò che risultava dal corpo della pagina recuperata. Dove il recupero ordinario falliva, la pagina è stata scaricata dal terminale e il corpo verificato, secondo `.claude/skills/fonti-non-recuperabili/RIFERIMENTO.md`; le voci interessate lo dichiarano. Le citazioni sono letterali, brevi e in lingua originale. Due voci, F06 e F07, sono state lette attraverso un'estrazione automatica della pagina e non riga per riga, e lo dichiarano nei limiti: il loro elenco di pattern non è garantito completo.

Le misure fatte in proprio non stanno qui ma nella guida, ciascuna con la data e il perimetro su cui è stata presa, secondo la regola sull'onestà del contenuto.

## Fonte visiva di partenza

### S1 - 14 Signs That Scream "AI Slop"

Carosello di quattordici schede illustrate, portato dall'utente come quattordici schermate catturate il 2026-09-23 e lette dalla cartella dello strumento di cattura. Autore e piattaforma di pubblicazione: non determinabili dalle schermate, che non riportano firma né indirizzo. Licenza: non nota. Le schermate restano fuori dal repository secondo `.claude/rules/manual-screenshots.md`.

Contenuto: otto segni di interfaccia, cioè sfondo crema con testo nero e pulsanti ambra, tutto in tre passi, una parola del titolo in corsivo serif, l'etichetta sopra ogni titolo, card dentro card, le icone scontate, elementi estranei al prodotto aggiunti perché fanno scena, lo stesso layout su slide diverse; e sei segni di prosa, cioè paragrafi e frasi della stessa misura, "Experts say" al posto della fonte nominata, "It's not just X, not even Z, but Y", tutto a gruppi di tre, gergo forzato per sembrare scritto da una persona, oltre alla scheda di copertina.

Limiti. Il carosello indica i segni e non ne dà la causa né le fonti. Ogni segno entra nella guida solo con una fonte primaria, oppure con la dichiarazione esplicita che nessuna fonte letta lo conferma: è il caso del gergo forzato e della finta finestra di terminale.

## Prosa

### F01 - Wikipedia:Signs of AI writing

Organizzazione: comunità di Wikipedia, WikiProject AI Cleanup. Indirizzo: https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing, letto anche nel testo sorgente. Revisione: ultima modifica registrata il 2026-09-21 alle 14:31:59 UTC. Licenza: Creative Commons Attribution-ShareAlike 4.0 International. Consultata il 2026-09-23, letta.

Autorevole su: il catalogo, mantenuto dalla comunità con esempi reali, dei tratti stilistici associati ai testi generati.

Affermazioni. Attribuzione vaga (WP:AIWEASEL): "AI chatbots tend to attribute opinions or claims to some vague authority", pratica che la pagina chiama "weasel wording" dopo un trattino lungo che qui non si riproduce, con parole da sorvegliare come "Experts argue", "Observers have cited", "Industry reports", "Some critics argue". Parallelismo negativo (WP:AIPARALLEL), in tre forme: "Not just X, but also Y", "Not X, but Y", "Y rather than X". Regola del tre (WP:RO3): "LLMs overuse the rule of three", usata "to make superficial analyses appear more comprehensive". Lessico (WP:AIVOCAB): fra le parole da sorvegliare `delve`, `tapestry`, `testament`, `pivotal`, `underscore`, `boasts`, `bolstered`, `crucial`, `emphasizing`, `enduring`, `enhance`, `fostering`, `garner`, `highlight`, `interplay`, `intricate`, `key`, `landscape`, `meticulous`, `robust`, `showcase`, `valuable`, `vibrant`, `align with`, `additionally`, raggruppate per generazione di modelli; "the word delve was famously overused by ChatGPT in 2023 and early 2024, but became less frequent later in 2024, then dropped off sharply in 2025". Trattino lungo: usato più dei testi non professionali dello stesso genere, spesso circondato da spazi, segno "most useful when taken in combination with other indicators, not by itself"; la pagina riporta uno studio del luglio 2026 secondo cui fra i modelli contemporanei solo Claude lo usa più degli scrittori professionisti.

Limiti dichiarati. "Do not solely rely on AI content detection tools", che "have non-trivial error rates"; il giudizio umano nel distinguere un testo generato è, secondo uno studio del 2025 citato dalla pagina, "no better than random chance"; e la scrittura umana, influenzata dai modelli, sta diventando più simile alla loro.

Usata in: guida, P2, P3, P4, P6 e la nota sul trattino lungo; `lint-prosa.py`, elenco del lessico e schemi di P2 e P3.

### F02 - humanizer

Autore: utente GitHub blader. Indirizzi: https://github.com/blader/humanizer e https://raw.githubusercontent.com/blader/humanizer/main/SKILL.md. Data: non dichiarata. Licenza: MIT. Consultata il 2026-09-23, letta.

Autorevole su: la traduzione del catalogo di F01 in una procedura di riscrittura per un agente.

Affermazioni. "Wikipedia: Signs of AI writing is the source for the pattern list"; venticinque pattern in cinque sezioni, dalla messa in scena al posto dell'affermazione ai residui della chat.

Limiti. Nessun limite metodologico dichiarato; la sua affidabilità dipende da F01.

Usata in: guida, sezione sull'uso insieme alle skill esterne; catalogo `PACKAGES.md`, voce `humanizer`.

### F03 - Perplexity and Burstiness: What is it?

Autore: Edward Tian, GPTZero. Indirizzo: https://gptzero.me/news/perplexity-and-burstiness-what-is-it/. Data dichiarata: 1 marzo 2023. Licenza: non dichiarata. Consultata il 2026-09-23, letta.

Autorevole su: la definizione originale delle due misure come usate da un rilevatore commerciale.

Affermazioni. La variabilità, *burstiness*, è "A measure of how much writing patterns and text perplexities vary over the entire document"; la scrittura umana varia, un modello mantiene un livello costante.

Limiti dichiarati. "a person could easily write an AI-like sentence by accident"; un aggiornamento nella pagina stessa dichiara che dall'autunno 2023 il rilevatore non si basa più soltanto su queste due misure.

Usata in: guida, P1 e la premessa sui limiti dei rilevatori.

### F04 - Delving into LLM-assisted writing in biomedical publications through excess vocabulary

Autori: Dmitry Kobak, Rita González-Márquez, Emőke-Ágnes Horvát, Jan Lause. Indirizzo: https://arxiv.org/abs/2406.07016. Versioni: v1 dell'11 giugno 2024, con il titolo "Delving into ChatGPT usage in academic writing through excess vocabulary"; v5 del 3 luglio 2025, pubblicata su Science Advances 11(27), DOI 10.1126/sciadv.adt3813. Licenza: non verificata. Consultata il 2026-09-23, letta nella pagina dell'abstract.

Autorevole su: la misura quantitativa più ampia dell'eccesso di vocabolario di stile dopo la diffusione dei modelli.

Affermazioni. "we study vocabulary changes in over 15 million biomedical abstracts from 2010-2024 indexed by PubMed"; "at least 13.5% of 2024 abstracts were processed with LLMs", fino al 40% in alcuni sottoinsiemi.

Limiti. Il metodo produce un limite inferiore su un corpus, non un giudizio sul singolo testo; il titolo è cambiato fra le versioni.

Usata in: guida, P6.

### F05 - GPT detectors are biased against non-native English writers

Autori: Weixin Liang, Mert Yuksekgonul, Yining Mao, Eric Wu, James Zou. Indirizzo: https://arxiv.org/abs/2304.02819. Versioni: v1 del 6 aprile 2023, v3 del 10 luglio 2023. Licenza: non verificata. Consultata il 2026-09-23, letta nella pagina dell'abstract.

Autorevole su: i falsi positivi sistematici dei rilevatori su chi scrive in una lingua non propria.

Affermazioni. "these detectors consistently misclassify non-native English writing samples as AI-generated"; gli autori mettono in guardia contro l'uso dei rilevatori "in evaluative or educational settings".

Usata in: guida, premessa sui limiti; i due strumenti, scelta di un codice di uscita zero salvo `--gate`.

## Interfacce

### F06 - frontend-design, skill ufficiale di Anthropic

Organizzazione: Anthropic. Indirizzo: https://raw.githubusercontent.com/anthropics/skills/main/skills/frontend-design/SKILL.md, licenza verificata nel file LICENSE.txt della stessa cartella. Data: non dichiarata. Licenza: Apache 2.0. Consultata il 2026-09-23, letta attraverso un'estrazione automatica.

Autorevole su: i cliché visivi che il fornitore del modello stesso indica da evitare.

Affermazioni. "a warm cream background (near #F4F1EA) with a high-contrast serif display and a terracotta or warm-clay accent (often near #D97757)"; "content chopped into identical rounded cards, one border-radius on everything regardless of hierarchy, the same soft grey shadow (rgba(0,0,0,.1))"; "tracked-out ALL-CAPS eyebrow label above every heading"; "Accenting just a single word or phrase in a headline, like putting one word in italic/bold".

Limiti. Lettura mediata da un'estrazione automatica: l'elenco dei pattern non è garantito completo.

Usata in: guida, U1, U3, U4, U5; `lint-ui.py`, valori di riferimento della palette.

### F07 - Prompting for frontend aesthetics

Autore: Prithvi Rajasekaran, Anthropic, Claude Cookbook. Indirizzo: https://platform.claude.com/cookbook/coding-prompting-for-frontend-aesthetics. Data dichiarata: 21 ottobre 2025. Licenza: non dichiarata. Consultata il 2026-09-23, letta attraverso un'estrazione automatica.

Autorevole su: la causa del fenomeno e le raccomandazioni del fornitore per evitarlo.

Affermazioni. "You tend to converge toward generic, 'on distribution' outputs. In frontend design, this creates what users call the 'AI slop' aesthetic"; fra i caratteri abusati Inter, Roboto, Arial, i caratteri di sistema e Space Grotesk; "purple gradients on white backgrounds"; "Predictable layouts and component patterns"; "Cookie-cutter design that lacks context-specific character".

Limiti. Lettura mediata; non è confermato che la pagina nomini esplicitamente la sezione in tre passi.

Usata in: guida, U1, U7, U8, U10.

### F08 - taste-skill

Autore: Leonxlnx. Indirizzi: https://raw.githubusercontent.com/Leonxlnx/taste-skill/main/skills/taste-skill/SKILL.md e il README del repository; un primo percorso tentato ha restituito HTTP 404 ed è stato sostituito dopo aver trovato la struttura reale. Data: non dichiarata. Licenza: MIT, 2026. Consultata il 2026-09-23, letta.

Autorevole su: un catalogo indipendente e più granulare dei tratti generici nel frontend.

Affermazioni. Bandita "the generic 'three identical cards horizontally' feature row"; Fraunces e Instrument Serif indicati come "the two LLM-favorite display serifs"; le etichette sopra le sezioni ammesse al massimo una ogni tre; bandita la palette crema con ottone, argilla e testo espresso scuro, con valori come #f5f1ea e #b08947.

Limiti. Letta la sola variante principale fra le diverse del repository.

Usata in: guida, U1, U2, U3, U4; `lint-ui.py`, U4 e U10.

### F09 - Icon Usability

Autore: Aurora Harley, Nielsen Norman Group. Indirizzo: https://www.nngroup.com/articles/icon-usability/. Data dichiarata: 27 luglio 2014. Licenza: non dichiarata. Consultata il 2026-09-23, letta.

Affermazioni. "a user's understanding of an icon is based on previous experience"; l'etichetta testuale deve restare visibile senza interazione.

Usata in: guida, U6.

### F10 - Cards: UI-Component Definition

Autore: Page Laubheimer, Nielsen Norman Group. Indirizzo: https://www.nngroup.com/articles/cards-component/. Data dichiarata: 6 novembre 2016. Licenza: non dichiarata. Consultata il 2026-09-23, letta.

Affermazioni. "Cards work best for collections of heterogeneous items"; le card sono "less scannable than lists"; mettere su card separate elementi dello stesso tipo "is not necessary".

Usata in: guida, U5 e U8.

### F11 - 7 Practical Tips for Cheating at Design

Autori: Adam Wathan e Steve Schoger, Refactoring UI. Indirizzo: https://medium.com/refactoring-ui/7-practical-tips-for-cheating-at-design-40c736799886; il recupero ordinario ha restituito HTTP 403 e la pagina è stata scaricata dal terminale e verificata sul corpo. Data dichiarata: 20 febbraio 2018. Licenza: copyright di The UI Company Inc. Consultata il 2026-09-23, letta.

Affermazioni. "When you need to create separation between two elements, try to resist immediately reaching for a border"; troppi bordi rendono il disegno "busy and cluttered"; le ombre delimitano un elemento in modo più discreto; con uno sfondo diverso il bordo spesso non serve.

Usata in: guida, U5.

### F12 - Understanding Success Criterion 1.4.3: Contrast (Minimum)

Organizzazione: W3C Web Accessibility Initiative. Indirizzo: https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html. Data: non dichiarata. Licenza: non verificata. Consultata il 2026-09-23, letta.

Affermazioni. "The visual presentation of text and images of text has a contrast ratio of at least 4.5:1"; per il testo grande "at least 3:1"; non hanno requisiti il testo decorativo e i logotipi.

Limiti. Il criterio riguarda il testo sul suo sfondo; il contrasto di un componente rispetto alla pagina ricade nel criterio 1.4.11, non letto e quindi non usato dagli strumenti.

Usata in: guida, U1; `lint-ui.py`, U9. La formula della luminanza relativa che lo strumento applica è quella della definizione WCAG, che non è stata riletta in questa sessione: la prova interna ne verifica il caso estremo, bianco su nero uguale a 21:1.
