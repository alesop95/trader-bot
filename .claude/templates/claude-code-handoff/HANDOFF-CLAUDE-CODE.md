---
upstream-source: github.com/Cranot/claude-code-guide
upstream-release: <versione upstream, aggiornata dallo script o alla prima corsa>
distilled-date: <YYYY-MM-DD di distillazione>
---

# Handoff Claude Code: riferimento delle opzioni dello strumento

> Riferimento enciclopedico delle opzioni, dei flag CLI, dei comandi di sessione e delle configurazioni di Claude Code, distillato dalla guida community `Cranot/claude-code-guide` (auto-aggiornata contro le release ufficiali) e dalle docs ufficiali `code.claude.com/docs`. Serve a orientare l'agente e l'utente sulle capacita' dello strumento, non sul progetto: le scelte normative del progetto vivono nelle regole sotto `.claude/rules/` e, in caso di divergenza, vincono le regole. Le voci sono marcate `[OFFICIAL]` se documentate ufficialmente, `[COMMUNITY]` se pattern consolidati della community, `[NEW]` se recenti. La CLI cambia spesso: verificare sempre flag e comandi con `claude --help` e `/help` prima di farvi affidamento. Si rigenera con `/refresh-handoff` o con `tools/update-handoff.ps1`/`.sh`; la struttura in sezioni numerate va mantenuta stabile a ogni rigenerazione.

## 0. Come si colloca nel sistema di progetto

In questo template l'avvio di un progetto non passa da questo documento ma dai due prompt fissi, `PROMPT-nuovo-progetto.md` per un progetto nuovo e `PROMPT-allinea-progetto-esistente.md` per uno esistente, che eseguono la skill `init-project-system` e il gate dei pacchetti di `templates/PACKAGES.md`. Questo documento si consulta durante quel flusso, e in qualsiasi momento successivo, quando serve sapere quali opzioni lo strumento offre: quale flag CLI esiste per un'esigenza, quali modalita' di permesso sono disponibili, come si collega un server MCP, cosa puo' fare un hook. I punti di contatto con le regole del sistema sono indicati sezione per sezione.

## 1. Avvio e sessioni [OFFICIAL]

```bash
claude                      # sessione interattiva
claude -p "task"            # print mode: non interattivo, stampa ed esce
claude --continue           # continua l'ultima sessione
claude --resume <id|nome>   # riprende una sessione specifica
claude --fork-session       # nuovo ID invece di riusare l'originale
claude --from-pr <pr>       # riprende la sessione legata a una PR GitHub [NEW]
claude --remote "task"      # crea una sessione web su claude.ai (piani abbonamento)
claude --teleport           # riporta una sessione web nel terminale locale
```

Comandi di sessione principali, da usare dentro la sessione.

```
/help            /exit            /clear           /compact [istruzioni]
/rewind          /rename <nome>   /resume [nome]   /export
/copy            /usage           /stats           /cost
/context         /status          /doctor          /debug
```

Su `/compact` e `/context` vale la disciplina di `rules/token-economy.md`: compattare proattivamente al 40-60% di contesto, con istruzioni esplicite su cosa preservare.

## 2. Modello, permessi e modalita' (flag CLI) [OFFICIAL]

```bash
# Modello e agenti
claude --model <sonnet|opus|haiku|nome-completo>
claude --fallback-model <name>          # fallback se il default e' sovraccarico (print mode)
claude --agent <name>                   # usa un subagent custom
claude --agents '<json>'                # definisce subagent al volo

# Permessi e tool
claude --tools "Bash,Read,Edit"         # limita i tool built-in ("" li disabilita tutti)
claude --allowedTools "Bash(git:*)"     # eseguono senza prompt
claude --disallowedTools "Edit"         # rimossi dal contesto
claude --permission-mode plan           # parte in modalita' plan
claude --dangerously-skip-permissions   # salta TUTTI i prompt: solo in container isolati

# Prompt di sistema
claude --system-prompt "..."            # sostituisce il system prompt
claude --append-system-prompt "..."     # lo estende
claude --system-prompt-file <path>      # da file (solo print mode)

# Budget e limiti (print mode, utile in CI/CD)
claude --max-budget-usd 5.00
claude --max-turns 3
claude --json-schema '<schema>'         # output JSON validato [NEW]

# Directory e config
claude --add-dir ../apps ../lib
claude --settings ./settings.json
claude --mcp-config ./mcp.json  --strict-mcp-config
claude --setting-sources user,project   # sorgenti di config [NEW]

# Integrazioni
claude --ide                            # connessione automatica all'IDE
claude --chrome / --no-chrome           # integrazione browser
claude --teammate-mode <in-process|tmux|auto>   # Agent Teams [NEW]

# Setup e manutenzione
claude --init          # esegue i Setup hooks e apre la sessione
claude --init-only     # esegue i Setup hooks ed esce
claude --maintenance   # hooks di manutenzione ed esce
```

Le regole di permesso hanno tre livelli, `allow`, `ask` e `deny`, e le regole a livello di contenuto vincono su quelle a livello di tool: `allow` su `Bash` piu' `ask` su `Bash(rm *)` significa Bash permesso ma `rm *` chiede conferma [NEW]. Le modalita' di esecuzione della sessione (default, acceptEdits, plan, dontAsk, auto, bypassPermissions), con i casi d'uso e i rischi di ciascuna, sono la materia di `rules/security-permissions.md`, che resta la fonte normativa del sistema.

## 3. CLAUDE.md e memoria persistente [COMMUNITY]

Il `CLAUDE.md` di radice e' letto automaticamente a ogni sessione ed e' il meccanismo principale di persistenza condivisa. In questo sistema la sua forma canonica e' quella di `templates/CLAUDE.md`: indice dei satelliti tracciati piu' procedura di ripresa, mai un contenitore di contenuto incorporato. La memoria e' a piu' livelli: `CLAUDE.md` di progetto, `CLAUDE.md` di sotto-cartella per i monorepo, e `~/.claude/CLAUDE.md` personale dell'account. Comandi correlati: `/init` genera uno scheletro (nel sistema si usa invece la skill `init-project-system`), `/memory` edita i file di memoria. La auto-memory nativa, che scrive fuori dal progetto, resta disattivata per default secondo la sezione 15 di `PROJECT-SYSTEM.md`.

## 4. Permessi di progetto in settings.json [OFFICIAL]

La configurazione dei permessi vive in `.claude/settings.json` (condivisa, versionata) e `.claude/settings.local.json` (personale, ignorata); la gestione interattiva passa da `/permissions` e `/config`. La baseline di questo sistema e' `templates/settings.json`: operazioni git irreversibili e lettura di file sensibili in `deny`, publish in `ask`, letture e ispezioni git in `allow`. I tool che non richiedono permesso sono Read, Grep, Glob, TodoWrite e Task; richiedono permesso Write, Edit, Bash, WebFetch e WebSearch.

## 5. Workspace multi-directory (monorepo e multi-repo) [OFFICIAL]

```bash
claude --add-dir ../backend ../frontend    # all'avvio
/add-dir ~/projects/shared-types           # durante la sessione
```

Utile per sincronizzare tipi tra progetti, type-check in parallelo e validazione cross-repo.

## 6. Modalita' di lavoro [OFFICIAL]

La Plan Mode (`/plan` o `--permission-mode plan`) mette la sessione in sola lettura ed e' la modalita' giusta per pianificare una feature complessa prima di toccare il codice; nel workflow di feature della sezione 9 di `PROJECT-SYSTEM.md` corrisponde alla fase di piano che precede l'implementazione. Il Thinking Mode estende il ragionamento e si attiva in linguaggio naturale ("think", "think hard") o da scorciatoia. Il Fast Mode (`/fast`) usa una variante piu' veloce del modello sui piani che lo offrono [NEW]. I Background Tasks lanciano comandi in background: `/bashes` o `/tasks` li elenca, `/kill <id>` li ferma, e l'agente viene notificato al termine.

## 7. MCP: collegare servizi esterni [OFFICIAL]

```bash
# HTTP remoto (servizi hosted)
claude mcp add --transport http <nome> <url>
claude mcp add --transport http <nome> <url> --header "Authorization: Bearer TOKEN"

# Stdio locale (pacchetti locali)
claude mcp add <nome> -- npx -y <pacchetto>
```

Lo scope e' locale per default, di progetto tramite il `.mcp.json` di radice condiviso via git, oppure utente in `~/.claude.json`. La gestione a runtime passa da `/mcp`, `/mcp enable <srv>`, `/mcp disable <srv>`, con OAuth[^1] via browser dentro `/mcp`. I tool MCP appaiono come `mcp__<server>__<tool>` e i prompt MCP diventano skill. In questo sistema il `.mcp.json` vive sempre nella radice, mai sotto `.claude` (sezione 2 di `PROJECT-SYSTEM.md`), i server si scelgono al gate dei pacchetti dal catalogo `templates/PACKAGES.md`, e valgono i limiti li' fissati: tre o quattro server nuovi al massimo per sessione, non piu' di sei connessi, preferenza per le implementazioni ufficiali dei vendor.

## 8. Skills: comportamenti riutilizzabili [OFFICIAL]

Le skill vivono in `.claude/skills/` (di progetto, condivise via git) o `~/.claude/skills/` (personali). Claude le auto-attiva in base alla richiesta, oppure si invocano con `/nome-skill`. Il frontmatter porta `description` e il controllo dell'invocazione (user-only o model-only); gli argomenti si ricevono con `$ARGUMENTS`, `$0`, `$1`, e i riferimenti a file con `@percorso`. I comandi `/skills` e `/commands` elencano cio' che e' disponibile. In questo sistema una skill si introduce solo per procedure complesse o ripetibili (sezione 1 di `PROJECT-SYSTEM.md`); esempi pronti sono nel pacchetto `dev-skills` del catalogo.

## 9. Subagent e Agent Teams [OFFICIAL]

I subagent sono agenti specializzati lanciati via tool Task, con contesto isolato e un insieme ristretto di tool; i custom si definiscono come file Markdown in `.claude/agents/` e si gestiscono con `/agents`. Servono per esplorazione, review e ricerca parallela senza sporcare il contesto principale; il pacchetto `subagent-template` del catalogo ne fornisce quattro pronti (code-reviewer, security-auditor, debugger, explorer). Gli Agent Teams [NEW] coordinano piu' agenti in parallelo (`--teammate-mode`): utili per task ampi e paralleli, da evitare per modifiche piccole e sequenziali, con l'avvertenza sulla propagazione dei permessi del lead descritta in `rules/security-permissions.md`.

## 10. Hooks: automazioni su eventi [OFFICIAL]

Gli hook sono script eseguiti su eventi (`PreToolUse`, `PostToolUse`, `SessionStart`, `SessionEnd`, `Setup` e altri), configurati nella sezione `hooks` di `settings.json`. Usi tipici: proteggere file sensibili, iniettare contesto a inizio sessione, scansionare i secret prima di un commit, imporre lint e test. La gestione e la diagnosi passano da `/hooks` e `claude --debug`. Regole di sicurezza: quotare le variabili, validare i path, usare path assoluti (la variabile `$CLAUDE_PROJECT_DIR` da' la radice del progetto). Le famiglie di hook utili a questo sistema sono descritte nella sezione 14 di `PROJECT-SYSTEM.md` e implementate pronte all'uso nel pacchetto `hooks-starter` del catalogo, mai attive di default.

## 11. Verifica del setup

Tre task di prova confermano che il setup funziona: chiedere di leggere la struttura del progetto e spiegare l'architettura, chiedere quali comandi sono disponibili, ed eseguire i test, che devono girare senza prompt se i permessi lo consentono. Il workflow di riferimento per una feature resta quello della sezione 9 di `PROJECT-SYSTEM.md`: esplorare, pianificare, implementare a passi, verificare, e lasciare il commit all'utente.

## 12. Note operative

Nelle sessioni lunghe si monitora il contesto con `/context` e si compatta proattivamente secondo `rules/token-economy.md`. In CI/CD[^2] la forma tipica e' `claude -p "..." --output-format json --max-budget-usd N --max-turns N`. Per l'automazione headless esiste l'SDK[^3] in TypeScript e Python. Sul fronte sicurezza: mai committare `.env`, bloccare in `settings.json` e, volendo, con l'hook `secret-scan` di `hooks-starter`; rivedere sempre le modifiche prima del deploy. La CLI evolve rapidamente: confermare flag e comandi con `claude --help` e `/help`.

## 13. Auto-aggiornamento di questo documento

La fonte upstream si auto-aggiorna circa ogni due giorni quando il suo updater e' in funzione; gli script del pacchetto rilevano anche lo stallo della fonte (campo `last_check` upstream piu' vecchio di quattordici giorni) e in quel caso avvisano che la guida stessa e' vecchia e che questo documento va integrato da `claude --help` e dalle docs ufficiali. Lo script `tools/update-handoff.ps1` (Windows) o `tools/update-handoff.sh` (Linux/macOS) confronta la versione upstream con quella nel file di stato `.claude/handoff-state.json`, scarica la guida grezza in `_notes/upstream/claude-code-guide.md` quando cambia, e ri-distilla questo documento con la CLI `claude` se disponibile; altrimenti si esegue `/refresh-handoff` dentro la sessione. Il flag `-Check`/`--check` verifica soltanto (exit 10 se c'e' un aggiornamento), `-Force`/`--force` rigenera comunque. Il workflow opzionale `.github/workflows/update-handoff.yml` fa lo stesso su GitHub Actions e apre una pull request quando la fonte cambia, se il secret `ANTHROPIC_API_KEY` e' configurato. A ogni rigenerazione la struttura in sezioni numerate di questo documento resta stabile, si aggiornano frontmatter e contenuti cambiati, e il diff si rivede prima del commit, che resta manuale.

[^1]: *OAuth*, Open Authorization - protocollo di autorizzazione con cui un server MCP remoto autentica l'utente via browser senza conservare la password.
[^2]: *CI/CD*, Continuous Integration / Continuous Delivery - pipeline automatiche di build, test e rilascio in cui Claude Code puo' girare in print mode.
[^3]: *SDK*, Software Development Kit - libreria per pilotare Claude Code da codice, senza terminale interattivo.
