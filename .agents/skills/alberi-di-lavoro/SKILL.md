---
name: alberi-di-lavoro
description: >
  Governa il caso in cui un progetto abbia più di un albero di lavoro git, cioè più cartelle
  agganciate allo stesso repository con git worktree, per tenere insieme produzione, test e
  una funzionalità in corso. Si carica quando `git worktree list` mostra più di un albero,
  quando si crea o si rimuove un albero, quando si apre una sessione in un albero che non è
  quello principale, e quando si deve decidere da dove leggere o dove scrivere la memoria
  versionata del progetto. Stabilisce che la memoria versionata descrive la branch e non il
  progetto, come si diagnostica in dieci secondi un albero che sta leggendo la verità di
  un'altra branch, e perché copiarla o fonderla sono entrambe correzioni sbagliate.
---

<!-- generato da sync-codex-skills.py; non modificare -->

Leggere integralmente [`../../../.claude/skills/alberi-di-lavoro/SKILL.md`](../../../.claude/skills/alberi-di-lavoro/SKILL.md) e seguirne la procedura canonica. Risolvere i percorsi relativi dalla directory della skill canonica. Tradurre la sintassi o i nomi degli strumenti specifici di Claude negli equivalenti disponibili in Codex senza indebolire controlli, gate o limiti di autorizzazione.
