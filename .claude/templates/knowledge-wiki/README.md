# Pacchetto knowledge-wiki

> Pacchetto opzionale del sistema di progetto. Scaffolda una LLM Wiki nel progetto: input grezzo
> immutabile, pagine compilate dall'LLM, e uno schema che governa come la wiki opera. La
> manutenzione (sintesi, collegamenti, contraddizioni) la fa l'LLM tramite la skill di ingestione,
> non l'utente a mano. E' il pattern LLM Wiki (Karpathy). Si offre al gate dei pacchetti (vedi
> ../PACKAGES.md) ai progetti dove si accumula conoscenza trasversale nel tempo, e non si propone
> quando il progetto ha gia una propria knowledge base nativa.

## Mappa di istanziazione

L'istanziazione crea la cartella `knowledge/` nella radice del progetto e installa la skill di
ingestione sotto `.claude/skills/`. Le cartelle vuote si creano con un `.gitkeep` perche git le
tracci.

```
templates/knowledge-wiki/WIKI-SCHEMA.md       ->  <radice>/knowledge/WIKI-SCHEMA.md      (tracciato)
templates/knowledge-wiki/log.md               ->  <radice>/knowledge/log.md              (tracciato)
templates/knowledge-wiki/skills/wiki-digest/  ->  <radice>/.claude/skills/wiki-digest/   (tracciato)
(create vuote, con .gitkeep)                       <radice>/knowledge/sources/{books,articles,notes}/
                                                   <radice>/knowledge/wiki/{concepts,entities,sources}/
```

## I tre layer

`sources/` e' input immutabile e append-only: il registro grezzo di cio che si e' ingerito, mai
modificato a mano. `wiki/` e' il prodotto compilato dall'LLM: concetti, entita, riassunti per
fonte, con i collegamenti tra pagine. `WIKI-SCHEMA.md` e' la costituzione del sistema: dice quali
tipi di pagina esistono, come si linkano, quando si aggiornano e come si gestiscono le
contraddizioni.

## Ingestione

Si aggiunge una fonte mettendo il file in `sources/`, poi si invoca la skill `wiki-digest`: legge
il nuovo file, aggiorna o crea le pagine in `wiki/` secondo `WIKI-SCHEMA.md`, collega i concetti e
appende una voce a `log.md`. La skill e' a invocazione manuale: l'utente decide quando ingerire.

## Tracciamento git

`wiki/`, `WIKI-SCHEMA.md` e `log.md` sono tracciati, perche sono la conoscenza recuperabile da un
clone. `sources/` e' tracciato di default; le fonti sensibili o solo personali vanno invece in
`_notes/` o aggiunte al `.gitignore`, secondo il principio dei due livelli del sistema.

## Ponte con book-to-skill

L'output di book-to-skill (file di capitolo densi) puo essere copiato in `sources/books/<slug>/`:
la wiki lo ingerisce come fonte gia strutturata e ne cross-referenzia i concetti con il resto della
conoscenza. Lo skill resta operativo in sessione, la wiki costruisce conoscenza trasversale: non si
sovrappongono.

## Come si usa, passo per passo

1. Attivazione, una volta sola: al gate dei pacchetti, in init o allineamento, l'agente propone
   `knowledge-wiki` se pertinente. Accettando, vengono creati `knowledge/` (con `WIKI-SCHEMA.md`,
   `sources/`, `wiki/`, `log.md`) e la skill `wiki-digest`.
2. Aggiungi una fonte: metti un file in `knowledge/sources/`, per esempio
   `knowledge/sources/articles/<nome>.md`, oppure un PDF in `knowledge/sources/books/`. Non fai
   altro a mano: niente sintesi, niente collegamenti.
3. Ingerisci: invoca la skill `wiki-digest`. Legge la fonte nuova, crea o aggiorna le pagine in
   `wiki/` secondo `WIKI-SCHEMA.md`, le collega tra loro e appende una voce a `log.md`.
4. Nel tempo: ogni fonte nuova viene cross-referenziata con quelle gia presenti. La wiki cresce
   sola; tu non colleghi le pagine a mano.
5. Versiona: committi `knowledge/wiki/`, `WIKI-SCHEMA.md` e `log.md` (commit manuale). Le fonti
   sensibili restano fuori, in `_notes/` o nel `.gitignore`.

## Recap dei comandi

- Aggiungere una fonte: copia il file in `knowledge/sources/<categoria>/`.
- Ingerire le fonti nuove: invoca la skill `wiki-digest`.
- Consultare la wiki: apri le pagine in `knowledge/wiki/concepts/`, `entities/`, `sources/`.
- Storico delle ingestioni: `knowledge/log.md`.
- Versionare la conoscenza: `git add knowledge/ ; git commit` (operazione manuale dell'utente).

## Riferimenti e crediti

Questo pacchetto adatta il pattern LLM Wiki e si integra con book-to-skill. Fonti e strumenti
all'origine:

- LLM Wiki, pattern di Andrej Karpathy: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- Implementazione con Obsidian (Medium): https://alirezarezvani.medium.com/llm-wiki-skill-build-a-second-brain-with-claude-code-and-obsidian-2282752758c1
- book-to-skill, per pre-digerire un PDF tecnico in skill: https://github.com/virgiliojr94/book-to-skill
