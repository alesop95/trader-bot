# Pacchetto claude-code-handoff

> Pacchetto opzionale del sistema di progetto. Installa nel progetto un documento di handoff che elenca in modo esaustivo le opzioni, i flag CLI[^1], i comandi di sessione e le configurazioni di Claude Code, e il meccanismo che lo tiene allineato nel tempo alla sua fonte upstream. La fonte e' la guida community `Cranot/claude-code-guide`, che si auto-aggiorna circa ogni due giorni contro le release ufficiali della CLI: lo script di aggiornamento confronta la versione upstream con quella tracciata localmente, scarica la guida grezza quando cambia, e ri-distilla il documento di handoff mantenendone struttura e stile. Deriva dal bundle di template generato dall'utente a partire da quella guida e dalle docs ufficiali `code.claude.com/docs`; e' il primo pacchetto del catalogo il cui oggetto e' lo strumento Claude Code stesso, non il progetto.

## Cosa risolve

La CLI di Claude Code evolve rapidamente: flag nuovi, comandi slash nuovi, modalita' di permesso riviste. La conoscenza che l'agente ha di se stesso si ferma al suo addestramento, e la documentazione ufficiale va riletta ogni volta da capo. Il documento di handoff colma questo divario tenendo dentro il progetto un riferimento denso e sempre consultabile delle capacita' dello strumento, cosi che all'avvio di un progetto, o quando si valuta una configurazione (permessi, MCP[^2], hook, subagent), l'agente e l'utente abbiano l'elenco delle opzioni disponibili senza riscoprirle ogni volta. Il meccanismo di auto-aggiornamento evita che il riferimento invecchi in silenzio: la versione upstream e' tracciata in un piccolo file di stato versionato, e il confronto e' a costo zero finche' la fonte non cambia.

## I tre livelli del meccanismo

Il primo livello e' il documento distillato, `.claude/context/claude-code-handoff.md`, tracciato: e' l'unico livello che entra in contesto, denso e organizzato in sezioni numerate stabili. Il secondo livello e' la guida grezza upstream, salvata in `_notes/upstream/claude-code-guide.md`, ignorata da git: e' voluminosa, serve solo come fonte della ri-distillazione e come riferimento di consultazione puntuale, e si rigenera scaricandola. Il terzo livello e' il file di stato `.claude/handoff-state.json`, tracciato: registra la versione upstream distillata e la data, cosi che chiunque cloni il repository sappia a quale release della guida il documento e' allineato. Questa ripartizione segue i due livelli documentali del sistema: il distillato e lo stato sono conoscenza recuperabile e vanno nei commit, la fonte grezza e' materiale transitorio e resta fuori.

## Mappa di istanziazione

```
templates/claude-code-handoff/HANDOFF-CLAUDE-CODE.md        ->  <radice>/.claude/context/claude-code-handoff.md    (tracciato)
templates/claude-code-handoff/commands/refresh-handoff.md   ->  <radice>/.claude/commands/refresh-handoff.md       (tracciato)
templates/claude-code-handoff/tools/update-handoff.ps1      ->  <radice>/tools/update-handoff.ps1                  (tracciato; Windows)
templates/claude-code-handoff/tools/update-handoff.sh       ->  <radice>/tools/update-handoff.sh                   (tracciato; Linux/macOS, chmod +x)
templates/claude-code-handoff/workflows/update-handoff.yml  ->  <radice>/.github/workflows/update-handoff.yml      (tracciato, opzionale)
(generato dallo script alla prima corsa)                        <radice>/.claude/handoff-state.json                 (tracciato)
(generato dallo script alla prima corsa)                        <radice>/_notes/upstream/claude-code-guide.md       (ignorato)
```

Il gate del sistema operativo dell'inizializzazione istanzia la variante di script giusta; istanziarle entrambe e' innocuo e utile nei progetti che vivono su piu' macchine. Il workflow GitHub Actions e' un componente opzionale nel componente: si istanzia solo se il progetto vive su GitHub e si vuole l'aggiornamento anche senza una macchina locale che lanci lo script, e richiede il secret `ANTHROPIC_API_KEY` per la ri-distillazione nel runner.

## Come si usa, passo per passo

1. Attivazione al gate: si istanziano il documento di handoff, il comando `/refresh-handoff` e lo script nella variante del sistema operativo. Il documento parte gia' popolato con la distillazione corrente del template; la prima corsa dello script lo allinea alla versione upstream del momento.
2. Aggiornamento manuale: `./tools/update-handoff.ps1` su Windows oppure `./tools/update-handoff.sh` su Linux. Senza argomenti lo script confronta le versioni e non fa nulla se non c'e' niente di nuovo; con `-Force`/`--force` riscarica e rigenera comunque; con `-Check`/`--check` verifica soltanto, uscendo con codice 10 se un aggiornamento e' disponibile.
3. Ri-distillazione: se la CLI `claude` e' installata, lo script la invoca in print mode per rigenerare il documento distillato dalla fonte appena scaricata. Altrimenti lascia la fonte grezza in `_notes/upstream/` e segnala di aprire il progetto ed eseguire `/refresh-handoff`, che fa la stessa cosa dentro la sessione.
4. Pianificazione: chi vuole l'automazione locale registra lo script in un task scheduler (Windows) o in un cron (Linux) ogni due giorni; chi vuole l'automazione remota istanzia il workflow GitHub Actions, che apre una pull request quando la fonte cambia.
5. Dopo ogni rigenerazione si rivede il diff del documento distillato prima di committarlo, come per ogni file tracciato: commit e push restano manuali dell'utente.

## Rapporto con le regole del sistema

Il documento di handoff non sostituisce le regole del template ma le complementa su un piano diverso: `rules/security-permissions.md` resta la fonte normativa sulle modalita' di permesso e sul sandboxing, `rules/token-economy.md` sulle pratiche di igiene del contesto, e l'handoff e' il riferimento enciclopedico delle opzioni dello strumento, con puntatori a quelle regole nei punti di contatto. In caso di divergenza tra handoff e regole, vincono le regole, che sono la scelta deliberata del sistema; l'handoff registra cio' che lo strumento offre, non cio' che il progetto ha deciso di usare.

## Vincoli e onesta'

La CLI cambia piu' in fretta di qualsiasi distillazione: ogni voce del documento va verificata con `claude --help` e `/help` prima di farvi affidamento in uno script, e il documento stesso lo dichiara in testa. La ri-distillazione automatica e' una corsa LLM[^3] e consuma token; il confronto di versione invece e' una richiesta HTTP e non consuma nulla, quindi lo script si puo' lanciare spesso senza costo. Il workflow GitHub Actions senza il secret `ANTHROPIC_API_KEY` non apre pull request inutili: si limita a registrare nel log che un aggiornamento e' disponibile.

Un secondo punto di onesta' riguarda la fonte stessa. L'auto-aggiornamento upstream e' reale e verificato: la storia dei commit mostra aggiornamenti automatici marcati "Automated update from official sources" a cadenza di circa due giorni, e il file `.update-state.json` ne traccia release e ultimo controllo. Ma un updater esterno puo' fermarsi, ed e' gia' successo: alla verifica del 2026-07-02 l'ultimo controllo automatico upstream risultava del 2026-02-11 (release v2.1.39), circa quattro mesi e mezzo prima. Per questo gli script non si fidano ciecamente: leggono anche il campo `last_check` upstream e, se risulta piu' vecchio di quattordici giorni, avvisano che la fonte e' in stallo e che "versione allineata" non significa "informazione aggiornata". In quel regime l'handoff si integra a mano da `claude --help` e dalle docs ufficiali, e la nota di stallo si riporta nel frontmatter del documento distillato.

Terzo punto, trovato dal vivo nel secondo giro di validazione (2026-07-02): la variante `update-handoff.sh` aveva l'estrazione dei campi JSON silenziosamente rotta. Il pattern `sed -E 's/.*:[[:space:]]*"?([^"]*)"?.*/\1/'` e' greedy sull'ultimo `:` della riga, e un timestamp ISO come `2026-02-11T02:03:51Z` contiene altri due punti (nelle ore/minuti/secondi): il risultato era il timestamp troncato a `51Z`, che falliva silenziosamente il parsing di `date -d` e disattivava senza avviso l'intero rilevamento dello stallo, proprio la funzione di sicurezza che questa sezione descrive. La variante PowerShell non ne soffriva perche' usa `[datetime]::Parse`, non una regex. Corretto ancorando il pattern all'inizio riga (`^"[^"]+"[[:space:]]*:...`), cosi' il primo `:` incontrato e' sempre quello dopo la chiave.

## Recap dei comandi

- Verificare se c'e' un aggiornamento: `./tools/update-handoff.ps1 -Check` (Windows) o `./tools/update-handoff.sh --check` (Linux).
- Aggiornare se serve: stesso comando senza flag; forzare con `-Force`/`--force`.
- Ri-distillare dentro la sessione: `/refresh-handoff`.
- Consultare il riferimento: aprire `.claude/context/claude-code-handoff.md`.

## Riferimenti e crediti

La fonte upstream e' `Cranot/claude-code-guide` (https://github.com/Cranot/claude-code-guide), guida community auto-aggiornante alle funzionalita' di Claude Code, integrata con le docs ufficiali `code.claude.com/docs`. Il pacchetto deriva dal bundle di template generato dall'utente a partire da quella guida; i crediti completi sono nella sezione "Riferimenti e strumenti open source" del `README.md` di radice del template.

[^1]: *CLI*, Command Line Interface - interfaccia a riga di comando; qui l'eseguibile `claude` con i suoi flag di avvio.
[^2]: *MCP*, Model Context Protocol - protocollo per collegare a Claude server esterni che espongono strumenti e dati.
[^3]: *LLM*, Large Language Model - modello linguistico di grandi dimensioni; una corsa LLM e' un'invocazione del modello, che consuma token.
