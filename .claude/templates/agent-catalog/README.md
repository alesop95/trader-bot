# Pacchetto agent-catalog

> Pacchetto opzionale del sistema di progetto. Installa un meccanismo per pescare a richiesta, uno alla volta, subagent gia' scritti da fonti community che li distribuiscono come semplici file Markdown senza un manifest di plugin installabile, e per controllare con la stessa strategia a costo zero del pacchetto `claude-code-handoff` se quelle fonti hanno ricevuto nuovi commit da quando le si e' guardate l'ultima volta. La fonte principale, e l'unica integrata come "flat" al momento dell'introduzione del pacchetto, e' `0xfurai/claude-code-subagents`; l'indice curato `hesreallyhim/awesome-claude-code` e' tracciato come fonte "meta" per scoprire nuove fonti nel tempo, senza essere esso stesso elencabile o scaricabile.

## Cosa risolve

Scrivere un subagent specializzato da zero, un file Markdown con frontmatter YAML che ne fissa nome, modello e strumenti disponibili, richiede tempo anche quando il ruolo che serve, per esempio un esperto di un framework specifico, e' gia' stato scritto e pubblicato da qualcun altro nella community. Il pacchetto `subagent-template', gia' nel catalogo, copre il caso dei quattro agenti generici piu' comuni (`code-reviewer`, `security-auditor`, `debugger`, `explorer`); `agent-catalog` copre il caso complementare, quando serve un agente iper-specifico per uno stack o un tool preciso, di cui esistono gia' collezioni intere pubblicate dalla community. Il problema che il pacchetto risolve non e' "dove trovare questi agenti", ma "come pescarne uno alla volta senza scaricare l'intera collezione, e come sapere se la fonte da cui li si e' presi ha avuto novita' da allora".

## Perche' 0xfurai e non le altre fonti trovate

La ricerca condotta per questo pacchetto ha esaminato diverse collezioni community di subagent Claude Code, e la scelta di quale integrare come fonte "flat" fetchable e quale no segue un criterio tecnico preciso, non di sola popolarita'.

`0xfurai/claude-code-subagents` (949 stelle, licenza MIT, 138 agenti in `agents/*.md`) distribuisce ogni agente come file indipendente in una cartella piatta, senza alcun manifest di plugin: il proprio stesso README invita a copiare i file uno a uno in `~/.claude/agents/`. E' esattamente il caso per cui serve un meccanismo di fetch mirato: non esiste un modo nativo di Claude Code per installare "solo l'agente react-expert" da questo repository, e scaricare tutti i 138 file per usarne uno sarebbe rumore puro nel progetto.

`wshobson/agents` (37,4k stelle, licenza MIT, 194 agent) e `VoltAgent/awesome-claude-code-subagents` (22,7k stelle, licenza MIT, 154+ agent) sono invece entrambi organizzati come marketplace di plugin nativi Claude Code, con un `.claude-plugin/marketplace.json` che raggruppa gli agenti in unita' installabili singolarmente (per dominio o categoria). Per questi due repository il meccanismo corretto non e' il fetch grezzo di questo pacchetto ma il comando nativo `/plugin marketplace add`, esattamente come gia' avviene nel catalogo per `code-simplifier` e `ponytail`: costruire uno script di fetch parallelo duplicherebbe una funzionalita' che Claude Code offre gia' in modo piu' robusto (il plugin marketplace gestisce da solo versioning e aggiornamento). Le due righe di catalogo corrispondenti sono descritte piu' sotto, in `PACKAGES.md`, non in questo pacchetto.

`hesreallyhim/awesome-claude-code` (47,8k stelle, licenza non dichiarata dal repository, campo GitHub `NOASSERTION`) e' una lista curata di riferimenti ad altri repository, non una fonte diretta di agenti: e' tracciata come fonte di tipo `meta` in `sources.json`, cosi' che lo script di controllo aggiornamento segnali quando e' cambiata (indicando che vale la pena riaprirla e guardare se sono comparse fonti nuove), senza che gli script di elenco o fetch tentino di interpretarne il contenuto.

Altre collezioni esaminate e non integrate, con la ragione della scelta dichiarata invece di taciuta: `contains-studio/agents` (12,4k stelle) organizza gli agenti per ruolo di prodotto/studio invece che per stack tecnico, un taglio complementare interessante, ma non dichiara alcuna licenza nel repository e mostra attivita' di commit molto bassa, due condizioni che sconsigliano di costruirci sopra un meccanismo di fetch automatico prima di una verifica piu' approfondita; `rohitg00/awesome-claude-code-toolkit` e `jeremylongshore/claude-code-plugins-plus-skills` dichiarano volumi molto ampi di skill e agenti (rispettivamente "400.000+ skill" tramite un marketplace esterno non verificato indipendentemente, e 2.810 skill in parte auto-generate da API REST), ma la qualita' media dei singoli pacchetti non e' stata verificata caso per caso: restano candidati da rivalutare, non fonti integrate.

## Mappa di istanziazione

```
templates/agent-catalog/sources.json                              ->  <radice>/.claude/agent-catalog/sources.json           (tracciato)
templates/agent-catalog/commands/list-community-agents.md         ->  <radice>/.claude/commands/list-community-agents.md    (tracciato)
templates/agent-catalog/commands/fetch-community-agent.md         ->  <radice>/.claude/commands/fetch-community-agent.md    (tracciato)
templates/agent-catalog/commands/check-agent-sources.md           ->  <radice>/.claude/commands/check-agent-sources.md      (tracciato)
templates/agent-catalog/tools/list-community-agents.ps1           ->  <radice>/tools/list-community-agents.ps1              (tracciato; Windows)
templates/agent-catalog/tools/list-community-agents.sh            ->  <radice>/tools/list-community-agents.sh               (tracciato; Linux/macOS, chmod +x)
templates/agent-catalog/tools/fetch-community-agent.ps1           ->  <radice>/tools/fetch-community-agent.ps1              (tracciato; Windows)
templates/agent-catalog/tools/fetch-community-agent.sh            ->  <radice>/tools/fetch-community-agent.sh               (tracciato; Linux/macOS, chmod +x)
templates/agent-catalog/tools/check-agent-sources.ps1             ->  <radice>/tools/check-agent-sources.ps1                (tracciato; Windows)
templates/agent-catalog/tools/check-agent-sources.sh              ->  <radice>/tools/check-agent-sources.sh                 (tracciato; Linux/macOS, chmod +x)
(generato dallo script alla prima corsa)                               <radice>/.claude/agent-catalog/state.json            (tracciato)
(generato dal comando fetch, una voce per agente scaricato)            <radice>/.claude/agents/<agente>.md                  (tracciato)
```

Il gate del sistema operativo dell'inizializzazione istanzia la variante di script giusta; istanziarle entrambe e' innocuo nei progetti che vivono su piu' macchine. Aggiungere una nuova fonte flat in futuro richiede solo una voce in piu' in `sources.json`: nessuno script va toccato.

## Come si usa, passo per passo

1. Attivazione al gate: si istanziano `sources.json`, i tre comandi e gli script nella variante del sistema operativo. Non viene generato nulla dentro `.claude/agents/` finche' non si fa un fetch esplicito.
2. Esplorazione: `/list-community-agents` (o direttamente `./tools/list-community-agents.ps1`/`.sh`) elenca gli agenti disponibili nella fonte `0xfurai`, opzionalmente filtrata per chiave.
3. Fetch mirato: `/fetch-community-agent 0xfurai react-expert` (o lo script equivalente) scarica il singolo file in `.claude/agents/react-expert.md` e registra fonte, commit sha al momento del download e data in `.claude/agent-catalog/state.json`. Un fetch verso un file gia' presente si rifiuta senza `-Force`/`--force`, per non sovrascrivere in silenzio un agente che il progetto ha gia' personalizzato.
4. Revisione: il file scaricato e' testo di terze parti, non verificato dal sistema di progetto. Va letto prima di fidarsene, e in particolare va rivisto il campo `model` del frontmatter, che nella fonte `0xfurai` e' spesso fissato a uno snapshot specifico (per esempio `claude-sonnet-4-20250514`) che puo' non essere piu' il modello che il progetto usa di default.
5. Controllo periodico: `/check-agent-sources` (o lo script equivalente) confronta l'ultimo commit di ciascuna fonte con quello registrato l'ultima volta, segnala se c'e' novita' e, di default, aggiorna lo stato tracciato dopo aver riportato l'esito; `-Check`/`--check` verifica soltanto, uscendo con codice 10 se c'e' un aggiornamento disponibile, senza scrivere nulla.

## Rapporto con le regole del sistema

Un agente scaricato da questo pacchetto entra a tutti gli effetti in `.claude/agents/` del progetto e da quel momento e' un agente di progetto come uno qualsiasi degli altri: si applicano le stesse convenzioni di `subagent-template` (frontmatter YAML con nome, modello, strumenti) e la stessa disciplina di revisione che si userebbe per un agente scritto a mano. Il pacchetto non modifica il contenuto scaricato: la fedelta' alla fonte e' deliberata, perche' il valore del fetch e' prendere esattamente cio' che la community ha scritto, non una parafrasi.

## Vincoli e onesta'

L'API GitHub non autenticata usata da tutti e tre gli script ha un limite di 60 richieste all'ora per indirizzo IP: sufficiente per un uso occasionale di esplorazione e fetch, non per una corsa automatica frequente o per elencare piu' fonti in rapida successione. Ogni file scaricato e' contenuto di terze parti non curato dal sistema di progetto: la correttezza tecnica, l'assenza di istruzioni malevole e l'aggiornamento del campo `model` restano responsabilita' di chi lo scarica e lo revisiona prima dell'uso.

A differenza del pacchetto `claude-code-handoff`, nessuna delle fonti di questo pacchetto si auto-aggiorna a una cadenza nota: la nozione di "stallo" qui e' quella della verifica locale, non della fonte. Lo script di controllo segnala quando una fonte non viene controllata da piu' di trenta giorni, ma questo non implica che la fonte stessa sia ferma, solo che nessuno ha ancora guardato se e' cambiata. Il meccanismo di confronto (uno sha di commit contro quello registrato l'ultima volta) e' stato esercitato dal vivo due volte: al momento dell'integrazione, in isolamento, su entrambe le varianti PowerShell e POSIX, incluso il fetch reale di un file (`react-expert.md`) e il rifiuto corretto di sovrascriverlo senza `-Force`/`--force`; e di nuovo nel pilota del 2026-07-02, questa volta dentro un vero progetto ospite (list, fetch di `typescript-expert.md`, check), con esito pulito e nessun nuovo bug trovato. Resta non osservato l'effettivo comportamento dopo trenta giorni di mancato controllo (la segnalazione di stallo della verifica locale), perche' nessuna delle due corse e' durata abbastanza a lungo da attraversare quella soglia.

## Recap dei comandi

- Vedere cosa c'e' in una fonte: `/list-community-agents 0xfurai` oppure `./tools/list-community-agents.ps1 -Source 0xfurai` / `./tools/list-community-agents.sh 0xfurai`.
- Scaricare un agente: `/fetch-community-agent 0xfurai <nome>` oppure `./tools/fetch-community-agent.ps1 -Source 0xfurai -Agent <nome>` / `./tools/fetch-community-agent.sh 0xfurai <nome>`.
- Controllare se le fonti hanno novita': `/check-agent-sources` oppure `./tools/check-agent-sources.ps1 -Check` / `./tools/check-agent-sources.sh --check`.

## Riferimenti e crediti

- `0xfurai/claude-code-subagents`, fonte flat integrata, 138 subagent per stack/framework, licenza MIT: https://github.com/0xfurai/claude-code-subagents
- `hesreallyhim/awesome-claude-code`, indice curato tracciato come fonte meta per la scoperta di nuove fonti, licenza non dichiarata dal repository: https://github.com/hesreallyhim/awesome-claude-code
- `wshobson/agents`, marketplace di plugin nativo con 194 agent, non integrato qui perche' si installa con `/plugin marketplace add` invece che con il fetch di questo pacchetto (licenza MIT): https://github.com/wshobson/agents
- `VoltAgent/awesome-claude-code-subagents`, marketplace di plugin nativo con 154+ agent per 10 categorie, stesso motivo di esclusione di `wshobson/agents` (licenza MIT): https://github.com/VoltAgent/awesome-claude-code-subagents
- `contains-studio/agents`, collezione per ruolo di prodotto/studio invece che per stack tecnico, valutata e non integrata per licenza non dichiarata e bassa attivita' di commit: https://github.com/contains-studio/agents
- I crediti completi, con licenze e note di verifica, sono anche nella sezione "Riferimenti e strumenti open source" del `README.md` di radice del template.
