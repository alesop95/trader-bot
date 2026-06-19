# Pacchetto book-to-skill

> Pacchetto opzionale del sistema di progetto. Trasforma un PDF o documento tecnico denso in una
> skill pre-digerita e interrogabile on-demand, sul modello di book-to-skill. Si offre al gate dei
> pacchetti (vedi ../PACKAGES.md) ai progetti che hanno libri o PDF tecnici di riferimento.

## La scelta: locale per default, globale solo su conferma

In riferimento al repo book-to-skill, adottiamo la capacita di creare skill da un subset di libri
ma non la rendiamo globale a Claude per default. Ogni progetto puo aver bisogno di libri specifici,
quindi le skill-libro nascono dentro il progetto, sotto `.claude/skills/<slug>/`, versionate e
trasportate dal repo. Si puo comunque promuovere una skill-libro al contesto globale di Claude
(`~/.claude/skills/<slug>/`), ma solo su conferma esplicita dell'utente e tracciando la scelta. Il
default e locale; il globale e una scelta cosciente e registrata, per i libri di riferimento usati
in piu progetti.

## Cosa produce

La skill `book-digest`, dato un PDF o documento tecnico, genera in `.claude/skills/<slug>/`:

```
.claude/skills/<slug>/
├── SKILL.md          modelli mentali principali + indice dei capitoli
├── chapters/         un file per capitolo, caricato on-demand
│   └── ch01-*.md
├── glossary.md       termini chiave con riferimenti ai capitoli
├── patterns.md       tecniche, algoritmi, design pattern
└── cheatsheet.md     tabelle decisionali e regole di riferimento rapido
```

I capitoli non si caricano finche non servono: la skill resta densa e a basso costo di contesto.

## Il doppio path

La stessa skill-libro digerita ha due usi non esclusivi.

Path A, skill operativa: gli agenti la usano in sessione, per esempio `/<slug> replication`, e
ricevono la sintesi densa dell'argomento senza rileggere il PDF. E' un tool di produzione.

Path B, verso la wiki: se il progetto ha il pacchetto `knowledge-wiki`, i file capitolo si copiano
in `knowledge/sources/books/<slug>/` e `wiki-digest` li ingerisce, cross-referenziando i concetti
del libro con il resto della conoscenza accumulata. I due path coesistono sullo stesso libro.

## Mappa di istanziazione

```
templates/book-to-skill/skills/book-digest/  ->  <radice>/.claude/skills/book-digest/  (tracciato)
```

La skill `book-digest` e' l'unico file installato dal pacchetto. Le skill-libro vere e proprie
(`<slug>/`) le genera `book-digest` quando la lanci su un PDF, e nascono sotto `.claude/skills/` del
progetto.

## Recap dei comandi

- Digerire un libro: invoca la skill `book-digest` indicando il PDF e uno slug.
- Usare la skill-libro (path A): `/<slug> <argomento>` in sessione.
- Alimentare la wiki (path B): copia `.claude/skills/<slug>/chapters/`, `glossary.md`, `patterns.md`
  in `knowledge/sources/books/<slug>/` e invoca `wiki-digest`.
- Promuovere al globale (solo su conferma): copia `.claude/skills/<slug>/` in
  `~/.claude/skills/<slug>/` e registra la promozione.
- Versionare: committi `.claude/skills/<slug>/` (commit manuale dell'utente).

## Riferimenti e crediti

- book-to-skill, di cui questo pacchetto adatta il pattern: https://github.com/virgiliojr94/book-to-skill
- Pattern LLM Wiki, per il path B: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
