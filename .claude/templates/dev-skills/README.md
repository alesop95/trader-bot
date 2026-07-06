# Pacchetto dev-skills

> Pacchetto opzionale del sistema di progetto. Fornisce quattro skill di sviluppo pronte da istanziare sotto `.claude/skills/` del progetto: `test-generator` per generare test seguendo il framework e i pattern gia' presenti, `mcp-tool-scaffold` per scaffoldare tool di un server MCP[^1] con descrizioni orientate all'LLM, e le due skill di revisione `code-review` e `security-review`. Le skill si scelgono una per una al gate: istanziarle tutte e quattro non e' il default. Deriva dal bundle di template generato dall'utente a partire dalla guida community `Cranot/claude-code-guide`.

## Sovrapposizione dichiarata con le capacita' native

Le due skill di revisione duplicano deliberatamente capacita' che esistono gia' su due piani, e l'onesta' del catalogo impone di dichiararlo al gate. Sul piano dello strumento, le versioni recenti di Claude Code portano skill native `/code-review` e `/security-review`, piu' evolute di queste (verifica adversariale dei finding, livelli di effort): una skill di progetto con lo stesso nome le mette in ombra nel progetto. Sul piano del template, il pacchetto `subagent-template` fornisce gli agenti `code-reviewer` e `security-auditor`, che coprono la stessa esigenza in contesto isolato. Le due skill di questo pacchetto restano utili in tre casi: quando si vuole un processo di review personalizzato e versionato col progetto, che i membri del team ricevono da un clone indipendentemente dalla versione della loro CLI; quando si lavora con versioni della CLI prive delle skill native; e quando si vuole che la review giri nel contesto principale invece che in un subagent. Se nessuno di questi casi si applica, al gate si istanziano solo `test-generator` e `mcp-tool-scaffold`, che non duplicano nulla.

## Le quattro skill

`test-generator` genera test per codice nuovo o esistente rilevando il framework e i pattern del progetto invece di imporne di propri: analizza il target, individua runner, convenzioni di naming e helper condivisi, genera happy path, edge case ed errori, ed esegue la suite per confermare l'esito. `mcp-tool-scaffold` scaffolda un nuovo tool per un server MCP in TypeScript con la disciplina del profilo `ts-mcp`: contratto prima del codice, validazione degli input, errori strutturati, descrizioni scritte per il modello che le legge. `code-review` esegue una revisione strutturata su qualita', correttezza, performance, sicurezza e test, riportando i finding per severita' senza modificare il codice. `security-review` esegue un audit difensivo su autenticazione, validazione degli input, protezione dei dati, dipendenze e configurazione, anch'esso in sola analisi.

## Mappa di istanziazione

```
templates/dev-skills/skills/test-generator/SKILL.md      ->  <radice>/.claude/skills/test-generator/SKILL.md      (tracciato)
templates/dev-skills/skills/mcp-tool-scaffold/SKILL.md   ->  <radice>/.claude/skills/mcp-tool-scaffold/SKILL.md   (tracciato)
templates/dev-skills/skills/code-review/SKILL.md         ->  <radice>/.claude/skills/code-review/SKILL.md         (tracciato, vedi nota naming)
templates/dev-skills/skills/security-review/SKILL.md     ->  <radice>/.claude/skills/security-review/SKILL.md     (tracciato, vedi nota naming)
```

Nota sul naming: istanziare `code-review` o `security-review` con questi nomi mette in ombra le skill native omonime dentro il progetto, ed e' una scelta da fare a ragion veduta al gate. Chi vuole tenere disponibili entrambe le versioni istanzia le skill di progetto con un nome distinto, per esempio `project-code-review`, aggiornando il campo `name` del frontmatter oltre al nome della cartella.

## Come si usa

Le skill si attivano da sole quando la richiesta corrisponde alla loro description, oppure si invocano esplicitamente: `/test-generator` sul modulo da coprire, `/mcp-tool-scaffold` con il contratto del tool da creare, `/code-review` sul diff corrente o su file specifici, `/security-review` sul modulo da auditare. Tutte e quattro rispettano i vincoli del sistema: le due di review non modificano mai il codice, `test-generator` non introduce un framework di test nuovo se ne esiste gia' uno, e nessuna esegue operazioni git.

## Verificato dal vivo (pilota 2026-07-02)

`test-generator` e `mcp-tool-scaffold` sono stati esercitati per davvero, via corsa headless (`automation-starter`) su un piccolo server MCP TypeScript, non solo istanziati. Entrambi hanno prodotto codice corretto e coerente con `stack-profile.md`: `test-generator` ha aggiunto quattro casi reali su una funzione esistente, tutti verdi; `mcp-tool-scaffold` ha scaffoldato un secondo tool MCP completo (validazione zod, naming snake_case, errore strutturato), codice che compila e i cui test preesistenti restano verdi, anche se la corsa non e' arrivata a scrivere i test del nuovo tool prima di esaurire i turni assegnati (vedi il vincolo su `-MaxTurns` nel README di `automation-starter`). `code-review` e `security-review` non sono state esercitate in questo pilota: la sovrapposizione dichiarata con `/code-review` e `/security-review` native le rende a priorita' piu' bassa per un secondo giro di validazione.

## Riferimenti e crediti

Le quattro skill derivano dal bundle di template generato dall'utente a partire dalla guida community `Cranot/claude-code-guide` (https://github.com/Cranot/claude-code-guide), adattate alle regole e ai vincoli di questo sistema; `mcp-tool-scaffold` incorpora le best practice del pattern mcp-builder citato nel bundle. I crediti completi sono nella sezione "Riferimenti e strumenti open source" del `README.md` di radice del template.

[^1]: *MCP*, Model Context Protocol - protocollo per collegare a Claude server esterni che espongono strumenti e dati; un server MCP espone tool con nome, schema di input e description.
