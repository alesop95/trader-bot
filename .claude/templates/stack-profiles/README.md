# Pacchetto stack-profiles

> Pacchetto opzionale del sistema di progetto. Fornisce profili di regole gia' scritti per gli stack ricorrenti, da istanziare come regola modulare `.claude/rules/stack-profile.md` al momento dell'inizializzazione o dell'allineamento, quando il gate riconosce lo stack del progetto. Un profilo fissa le convenzioni di stile, i comandi tipici e i controlli pre-commit di quello stack, cosi che un progetto nuovo parta con le convenzioni giuste invece di scriverle a mano da zero e di riscoprirle a ogni progetto. Deriva dal bundle di template generato dall'utente a partire dalla guida community `Cranot/claude-code-guide`.

## Rapporto con STACK.md e con le regole esistenti

Il profilo e la scheda `context/STACK.md` rispondono a due domande diverse e non si sovrappongono. La scheda descrive lo stack che il progetto ha, con i flussi di codice reali e il frontmatter di riconciliazione che la ancora ai commit: e' descrittiva e si popola leggendo il codice. Il profilo prescrive le convenzioni con cui si scrive il codice di quello stack: e' normativo, non porta frontmatter di riconciliazione perche' non descrive file del progetto, e cambia solo quando cambiano le convenzioni, non quando cambia il codice. Il profilo si affianca alle regole trasversali gia' presenti (`interaction-style`, `token-economy`, `security-permissions`), che valgono per qualunque stack; in caso di conflitto tra profilo e regole trasversali vincono le seconde.

## I profili disponibili

Il profilo `ts-mcp` copre TypeScript/Node con sviluppo di server MCP[^1]: strict mode, ESM[^2], errori tipizzati, e la disciplina dei tool MCP orientati al consumo da parte di un LLM. Il profilo `python` copre scripting, data e RAG[^3]: ambienti con `uv` o venv, type hints, ruff e pytest. Il profilo `react` copre frontend e dashboard: componenti funzionali, gestione esplicita di loading ed errori, accessibilita', test di comportamento. Il profilo `n8n` copre l'automazione a workflow: JSON versionati come artefatti, credenziali fuori dai workflow, documentazione dei trigger. Il profilo `generico` e' il fallback esplicito: nessuna convenzione di stack imposta, si seguono e si documentano quelle rilevate nel codebase.

## Mappa di istanziazione

```
templates/stack-profiles/profiles/<profilo>.md  ->  <radice>/.claude/rules/stack-profile.md   (tracciato)
```

Si istanzia un solo profilo per progetto, quello dello stack principale; il file istanziato prende sempre il nome `stack-profile.md`, cosi che il `CLAUDE.md` e le altre regole possano riferirlo con un percorso stabile. In un monorepo con piu' stack conviene istanziare il profilo dello stack dominante e annotare le convenzioni degli stack secondari nella scheda `STACK.md`, oppure, se davvero servono due profili completi, istanziare il secondo come `stack-profile-<nome>.md` dichiarandolo nel `CLAUDE.md`. Il profilo istanziato e' un punto di partenza, non un contratto immutabile: si adatta al progetto man mano che le convenzioni reali emergono, e le personalizzazioni sopravvivono perche' il file vive nel repository del progetto, non nel template.

## Come si usa, passo per passo

1. Al gate dei pacchetti l'agente riconosce lo stack dai manifest presenti (`package.json`, `pyproject.toml`, cartelle `nodes/` di n8n, dipendenze React) e propone il profilo corrispondente; se nessuno corrisponde propone `generico` oppure niente.
2. Su conferma, il profilo scelto si copia in `.claude/rules/stack-profile.md` e si compila dove il testo indica di adattare, per esempio il package manager reale del progetto.
3. Il profilo viene caricato come ogni regola modulare e vincola le sessioni successive; la scheda `STACK.md` resta il posto dove descrivere lo stack reale.
4. Quando le convenzioni del progetto divergono dal profilo, si aggiorna il file istanziato e, se la divergenza e' una decisione architetturale, la si registra in `memory/decisions.md`.

## Aggiungere un profilo nuovo

Un profilo nuovo si aggiunge creando `profiles/<nome>.md` in questo pacchetto, con la stessa struttura dei profili esistenti: convenzioni di stile, comandi tipici da adattare, controlli pre-commit. La riga di catalogo in `../PACKAGES.md` non cambia, perche' il pacchetto e' uno solo; va invece aggiornato questo README, che elenca i profili disponibili.

## Riferimenti e crediti

I cinque profili derivano dal bundle di template generato dall'utente a partire dalla guida community `Cranot/claude-code-guide` (https://github.com/Cranot/claude-code-guide), adattati allo stile delle regole di questo sistema. I crediti completi sono nella sezione "Riferimenti e strumenti open source" del `README.md` di radice del template.

[^1]: *MCP*, Model Context Protocol - protocollo per collegare a Claude server esterni che espongono strumenti e dati.
[^2]: *ESM*, ECMAScript Modules - sistema di moduli nativo di JavaScript, con `import` ed `export`, alternativo al vecchio CommonJS.
[^3]: *RAG*, Retrieval-Augmented Generation - architettura in cui il modello genera risposte a partire da contenuto recuperato da una base di conoscenza.
