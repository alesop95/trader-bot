---
name: init-project-system
description: >
  Inizializza in un progetto il sistema di contesto, documentazione e version control
  descritto in .claude/PROJECT-SYSTEM.md. Prima verifica quale account Claude Code e attivo
  sulla macchina (setup multi-account via CLAUDE_CONFIG_DIR) e chiede conferma se ne risulta
  piu di uno; poi chiede quale identita git usare per i futuri commit e a quale repository
  GitHub agganciare il remoto, configurandola a livello locale (vedi rules/git-identity-and-repo.md).
  Infine esegue il runbook di inizializzazione passo per passo, fermandosi a chiedere conferma
  dove un'azione tocca il version control o e difficilmente reversibile. Non esegue mai
  git add/commit/push: li gestisce l'utente.
disable-model-invocation: true
---

## Contesto git (best-effort, pre-iniettato)

!`git status --short`
!`git branch --show-current`
!`git log -1 --format="%h %ad %s" --date=short`

Se la cartella non è ancora un repository git, questi comandi stampano un errore "not a git
repository": va letto come modalità greenfield senza repo, in cui i Passi 0.5 eseguiranno
`git init`. I comandi sono singoli e portabili (niente `||`, `echo` o redirezioni specifiche di
shell) per passare il controllo permessi su Windows e Unix.

## Premessa

Questa skill installa il sistema descritto in `.claude/PROJECT-SYSTEM.md`, che e la fonte di
verita della procedura. Se quel file non e presente nella radice del progetto o sotto
`.claude/`, fermarsi e avvisare l'utente: il sistema non puo essere installato senza il file
portabile, che va copiato dal progetto di riferimento. Non duplicare qui il contenuto del
runbook: leggerlo e applicarlo.

## Modalita: greenfield o allineamento

Prima di eseguire i passi, determinare la modalita. Se `.claude/` e la memoria non esistono e il
repo e nuovo o quasi vuoto, si procede in modalita greenfield con i passi sotto. Se invece il
progetto ha gia codice e una storia git, si opera in modalita allineamento: non si scaffolda da
zero, si segue la sezione "Adozione su un progetto esistente" di `.claude/PROJECT-SYSTEM.md`, che
rileva cosa esiste gia, lo mappa contro l'anatomia canonica, ricostruisce la memoria dalla storia
senza inventare, e dota le schede esistenti di frontmatter invece di duplicarle. In entrambe le
modalita valgono i Passi 0 e 0.5 (account Claude e identita git) e il vincolo di non committare
mai. In modalita allineamento non sovrascrivere nulla in silenzio: proporre e allineare poche
schede alla volta, chiedendo conferma su ogni passo che tocca il version control.

## Passo 0 — Verifica dell'account Claude Code attivo (multi-account)

Questo passo precede ogni altra azione, perche il resto del lavoro va svolto con l'account
giusto e perche su questa classe di macchine sono configurati piu profili isolati tramite la
variabile d'ambiente `CLAUDE_CONFIG_DIR` (un profilo per directory di configurazione). La
variabile viene letta solo all'avvio del processo: una sessione gia in corso non puo cambiare
account da sola. Questa skill quindi rileva e indirizza, ma non commuta l'account.

Eseguire, tramite il tool PowerShell, i comandi seguenti e presentare l'esito all'utente.

```powershell
"=== Account attivo in QUESTA sessione (process) ==="
$env:CLAUDE_CONFIG_DIR
"=== Default permanente a livello utente (VS Code, claude nudo) ==="
[System.Environment]::GetEnvironmentVariable("CLAUDE_CONFIG_DIR","User")
"=== Profili di configurazione presenti sulla macchina ==="
Get-ChildItem "$env:USERPROFILE" -Directory -Filter ".claude*" | Select-Object -ExpandProperty Name
```

Interpretazione dell'esito e azione:

1. Contare le directory `.claude*` trovate. Ognuna e un profilo Claude Code isolato (credenziali,
   cronologia, impostazioni). La presenza della directory predefinita `.claude` accanto a una o
   piu `.claude-accountN` va segnalata come possibile profilo residuo, perche puo confondere la
   diagnosi.
2. Identificare l'account attivo in questa sessione dal valore di `$env:CLAUDE_CONFIG_DIR` di
   processo. Mappatura nota su questa macchina, da trattare come riferimento e non come dato
   universale: `.claude-account1` corrisponde ad asopranzi@intrawelt.com (default di VS Code e
   del comando `claude` nudo), `.claude-account2` corrisponde a info@intrawelt.com. Su una
   macchina diversa cambiano i nomi utente e le associazioni: in tal caso riportare solo i
   percorsi rilevati senza inventare le email.
3. Se esiste un solo profilo, dichiarare quale account e in uso e proseguire al Passo 1.
4. Se esistono piu profili, chiedere all'utente con quale account intende inizializzare il
   progetto, mostrando quello attualmente attivo. Se l'utente indica un account diverso da
   quello attivo, NON proseguire: spiegare che il cambio richiede di rilanciare Claude Code con
   la funzione del profilo desiderato (ad esempio `claude-account2` in un nuovo terminale,
   oppure modificando la variabile utente e riavviando VS Code), perche la variabile e letta
   solo all'avvio del processo. Proseguire solo quando l'account attivo coincide con quello
   voluto.

## Passo 0.5 — Selezione dell'identita git e del remote

Subito dopo l'account Claude, e prima del runbook, decidere con quale identita git verranno
firmati i commit e a quale repository GitHub agganciare il remoto. Identita git e account
Claude sono cose distinte: la prima e la coppia user.name/user.email piu la chiave SSH, la
seconda e il profilo di configurazione di Claude Code. Il dettaglio autoritativo della
procedura, dei profili disponibili e del caso repo con README e in `rules/git-identity-and-repo.md`.

Eseguire, tramite tool, la rilevazione dei profili e dello stato corrente.

```powershell
"=== Alias host SSH definiti ==="
Get-Content "$env:USERPROFILE\.ssh\config" | Select-String "^Host "
"=== Identita git locale di questo repo (se gia inizializzato) ==="
git config --local user.name; git config --local user.email; git config --local remote.origin.url
"=== Protezione globale ==="
git config --global user.useConfigOnly
```

Azione:

1. Presentare i profili ricavati dagli alias SSH e chiedere all'utente quale identita usare per
   questo progetto (ad esempio lavoro via alias `github-corp`, oppure personale via
   `github-personal`) e, se il repo va creato o riagganciato, il nome owner/repo di
   destinazione.
2. Impostare l'identita a livello locale del repo, mai globale: `git config --local user.name`,
   `git config --local user.email`, e su Windows `git config --local core.sshCommand` verso
   l'OpenSSH di sistema. Collegare il remoto con l'alias scelto, ad esempio
   `git remote add origin git@github-personal:<owner>/<repo>.git`. Su Linux omettere
   `core.sshCommand`.
3. Se `user.useConfigOnly` globale non e impostata, proporre di abilitarla
   (`git config --global user.useConfigOnly true`) per impedire commit con l'identita
   sbagliata; essendo globale, eseguirla solo su conferma esplicita.
4. Verificare con `git config --local --list` filtrato su `user.`, `remote.`, `core.ssh`.
5. Non eseguire commit ne push. Indicare all'utente i comandi manuali del primo commit/push e,
   se il repo remoto ha gia un README o una licenza, il `git pull origin main --rebase` prima
   del push, come da regola.

## Template canonici

Se esiste la cartella `.claude/templates/`, gli scheletri dell'anatomia sono già pronti e vanno
istanziati invece di ricostruirli a memoria: si copiano nella loro posizione finale secondo la
mappa in `templates/README.md` e si sostituiscono i segnaposto tra parentesi angolari (nome
progetto, hash del commit corrente, branch, data) con i valori reali. I file di `_notes/` si
istanziano solo dopo aver confermato che `_notes/` è ignorato. Le schede di `context/` si copiano
con struttura e frontmatter e si popolano leggendo il codice nei passi successivi, mai con
contenuto inventato. Se la cartella `templates/` non è presente, ricostruire l'anatomia dalla
descrizione di `.claude/PROJECT-SYSTEM.md`.

Oltre all'anatomia sotto `.claude`, i template coprono anche i file di radice del progetto,
fratelli di `.claude`: `CLAUDE.md` tracciato, `CLAUDE.local.md` ignorato come stub di override
personali, e, solo se il progetto integra un servizio esterno tramite un server MCP, `.mcp.json`
istanziato dal template opzionale e la cartella `mcp/` con l'implementazione del server, entrambi
tracciati e in radice, mai sotto `.claude`. Senza integrazione MCP questi ultimi non si creano.

I `templates/` possono inoltre contenere pacchetti opzionali di framework, riconoscibili come
sottocartelle con un proprio `README.md` di istanziazione (attualmente `templates/latex/` per
l'ambiente di build LaTeX). Non si attivano d'ufficio: si offrono con una domanda esplicita allo
startup, esattamente come l'MCP (vedi Passo 4).

## Passi 1-8 — Runbook di inizializzazione

Leggere la sezione "Comando di inizializzazione" di `.claude/PROJECT-SYSTEM.md` ed eseguirne i
passi nell'ordine indicato, applicando anche le sezioni richiamate (anatomia di `.claude`,
mappa ibrida tracciato/ignorato, igiene del version control). Dove esistono i template canonici,
istanziarli invece di rigenerare il contenuto. In sintesi operativa, i passi sono i seguenti, ma
il dettaglio autoritativo resta nel file.

1. Verifica del version control: scansione di file tracciati e storia alla ricerca di segreti
   (chiavi private, stringhe di connessione con credenziali, password SMTP, token di firma,
   service account) e di file indicizzati per errore. Riportare gli esiti senza committare.
2. Predisposizione del `.gitignore` con le esclusioni del livello privato: almeno `_notes/`,
   `CLAUDE.local.md`, `.claude/settings.local.json`, i `.docx` grezzi con eventuali eccezioni
   curate, e le cartelle scratch `.tmp-docx-*`.
3. Creazione dell'anatomia di `.claude` nella forma minima: `settings.json`, le cartelle
   `commands`, `rules`, `skills`, `agents`, la cartella `memory` con `index.md`, `progress.md`,
   `decisions.md`, e la cartella `context` con `STACK.md`, `design-and-security.md`,
   `deployment.md`, `dev-testing.md`, `current-work.md`, `roadmap.md` e la sottocartella
   `diagrams`.
4. Creazione o aggiornamento di `CLAUDE.md` nella radice perche indicizzi esplicitamente i file
   satellite e contenga la procedura di ripresa, piu lo stub di `CLAUDE.local.md` ignorato per
   gli override personali. Sull'MCP chiedere sempre esplicitamente all'utente, sia in greenfield
   sia in allineamento, se vuole configurare un server MCP, offrendo di crearlo ora o di
   rimandarlo come promemoria; non assumere mai. In caso affermativo istanziare in radice
   `.mcp.json` e la cartella `mcp/`, mai sotto `.claude`, e se un `.mcp.json` esiste gia mostrare
   la differenza invece di sovrascrivere.
   Con la stessa logica del gate MCP, per ciascun pacchetto opzionale di framework presente in
   `.claude/templates/` (sottocartella con un proprio `README.md`, attualmente `templates/latex/`)
   chiedere esplicitamente se attivarlo, offrendo di istanziarlo ora o di rimandarlo come
   promemoria; non assumere mai. Per LaTeX la domanda e' particolarmente pertinente se il progetto
   contiene file `.tex`. In caso affermativo istanziare il pacchetto secondo il suo `README.md`
   (per `latex/`: `scripts/`, `tex-packages.txt` e `.latexmkrc` in radice, e la skill `latex-build`
   sotto `.claude/skills/`), abilitare nel `.gitignore` il blocco di artefatti del framework (per
   LaTeX il blocco LaTeX dello snippet) e adattare il manifesto al preambolo reale; se un file di
   destinazione esiste gia, mostrare la differenza invece di sovrascrivere. In caso negativo,
   lasciare un promemoria esplicito che il pacchetto resta istanziabile in seguito dal template.
5. Creazione di `_notes` con `DIARIO.md`, `RESOCONTO.md`, `TEST-CHECKLIST.md`, solo dopo aver
   confermato che `_notes` e ignorato.
6. Installazione delle skill del motore di riconciliazione e del flusso git, ciascuna come
   `SKILL.md` nella propria cartella sotto `.claude/skills`.
7. Popolamento delle schede di `context` con il solo frontmatter di riconciliazione ancorato al
   commit corrente, senza inventare contenuto: il contenuto si scrive nei passi successivi
   leggendo il codice. Su un greenfield appena inizializzato non c'e ancora un commit, perche il
   primo commit lo fa l'utente dopo l'init: in quel caso lasciare `generated-from-commit` e
   `last-verified-commit` a un segnaposto esplicito come `PENDING-FIRST-COMMIT`, riportare lo
   stesso segnaposto come commit di riferimento in `memory/index.md`, e ancorarli al primo commit
   reale subito dopo, eseguendo la skill `sync-context` che li porta a `HEAD`.
8. Prima voce in `memory/progress.md` che registra l'inizializzazione e la data, e snapshot
   iniziale in `memory/index.md`.

Quando si parte da uno stack noto, in questo passo si possono installare skill gia predisposte
per quel framework o per la piattaforma di deploy, invece di ricostruirle.

## Note operative

Fermarsi a chiedere conferma prima di azioni difficilmente reversibili o che toccano il version
control. Non eseguire mai `git add`, `commit` o `push`: prepara i file e lascia all'utente le
operazioni git. Non popolare le schede con contenuto dedotto in fase di init. Se il progetto e
gia parzialmente inizializzato, allineare invece di sovrascrivere, segnalando cosa esiste gia.
