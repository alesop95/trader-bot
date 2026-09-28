---
name: init-project-system
description: >
  Inizializza in un progetto il sistema di contesto, documentazione e version control
  descritto in .claude/PROJECT-SYSTEM.md. Prima verifica quale account Claude Code e attivo
  sulla macchina (setup multi-account via CLAUDE_CONFIG_DIR) e chiede conferma se ne risulta
  più di uno; poi chiede quale identità git usare per i futuri commit e a quale repository
  GitHub agganciare il remoto, configurandola a livello locale (vedi rules/git-identity-and-repo.md).
  Infine esegue il runbook di inizializzazione passo per passo, fermandosi a chiedere conferma
  dove un'azione tocca il version control o e difficilmente reversibile. Non esegue mai
  git add/commit/push: li gestisce l'utente.
disable-model-invocation: true
---

## Contesto git (best-effort, pre-iniettato)

!`git status --short` !`git branch --show-current` !`git log -1 --format="%h %ad %s" --date=short`

Se la cartella non è ancora un repository git, questi comandi stampano un errore "not a git repository": va letto come modalità greenfield senza repo, in cui i Passi 0.5 eseguiranno `git init`. I comandi sono singoli e portabili (niente `||`, `echo` o redirezioni specifiche di shell) per passare il controllo permessi su Windows e Unix.

## Premessa

Questa skill installa il sistema descritto in `.claude/PROJECT-SYSTEM.md`, che è la fonte di verità della procedura. Se quel file non è presente nella radice del progetto o sotto `.claude/`, fermarsi e avvisare l'utente: il sistema non può essere installato senza il file portabile, che va copiato dal progetto di riferimento. Non duplicare qui il contenuto del runbook: leggerlo e applicarlo.

## Modalità: greenfield o allineamento

Prima di eseguire i passi, determinare la modalità. Se `.claude/` e la memoria non esistono e il repo e nuovo o quasi vuoto, si procede in modalità greenfield con i passi sotto. Se invece il progetto ha già codice e una storia git, si opera in modalità allineamento: non si scaffolda da zero, si segue la sezione "Adozione su un progetto esistente" di `.claude/PROJECT-SYSTEM.md`, che rileva cosa esiste già, lo mappa contro l'anatomia canonica, ricostruisce la memoria dalla storia senza inventare, e dota le schede esistenti di frontmatter invece di duplicarle. In entrambe le modalità valgono i Passi 0 e 0.5 (account Claude e identità git) e il vincolo di non committare mai. In modalità allineamento non sovrascrivere nulla in silenzio: proporre e allineare poche schede alla volta, chiedendo conferma su ogni passo che tocca il version control.

## Passo 0 - Verifica dell'account Claude Code attivo (multi-account)

Questo passo precede ogni altra azione, perché il resto del lavoro va svolto con l'account giusto e perché su questa classe di macchine sono configurati più profili isolati tramite la variabile d'ambiente `CLAUDE_CONFIG_DIR` (un profilo per directory di configurazione). La variabile viene letta solo all'avvio del processo: una sessione già in corso non può cambiare account da sola. Questa skill quindi rileva e indirizza, ma non commuta l'account.

Prima dei comandi, chiedere se si sviluppa su Windows o su Linux, perché da questo dipendono la variante degli strumenti di igiene, la sintassi degli hook, gli script di setup e build, e il forzare o meno `core.sshCommand`. La risposta non si deduce dalla piattaforma su cui gira la sessione senza dirlo: la si dichiara, e da quel momento si usa una sola variante.

Su Windows, eseguire tramite il tool PowerShell i comandi seguenti e presentare l'esito all'utente.

```powershell
"=== Account attivo in QUESTA sessione (process) ==="
$env:CLAUDE_CONFIG_DIR
"=== Default permanente a livello utente (VS Code, claude nudo) ==="
[System.Environment]::GetEnvironmentVariable("CLAUDE_CONFIG_DIR","User")
"=== Profili di configurazione presenti sulla macchina ==="
Get-ChildItem "$env:USERPROFILE" -Directory -Filter ".claude*" | Select-Object -ExpandProperty Name
```

Su Linux, gli stessi tre dati si ottengono così.

```bash
echo "=== Account attivo in QUESTA sessione ==="; echo "${CLAUDE_CONFIG_DIR:-(non impostata: si usa ~/.claude)}"
echo "=== Profili di configurazione presenti sulla macchina ==="; ls -d "$HOME"/.claude* 2>/dev/null
```

Interpretazione dell'esito e azione:

1. Contare le directory `.claude*` trovate. Ognuna e un profilo Claude Code isolato (credenziali, cronologia, impostazioni). La presenza della directory predefinita `.claude` accanto a una o più `.claude-accountN` va segnalata come possibile profilo residuo, perché può confondere la diagnosi.
2. Identificare l'account attivo in questa sessione dal valore di processo di `CLAUDE_CONFIG_DIR`. Il binding fra una directory e un account non si deduce mai dal nome della directory: si legge con `/status` o dal campo `emailAddress` di `<dir>/.claude.json`, e va riletto a ogni sessione, perché al rinnovo di un token scaduto Claude può ri-vincolare in modo silenzioso una directory all'account attivo nel browser su claude.ai (meccanismo descritto in `git-identity-and-repo.md`, sezione sul re-auth silenzioso). Dove una macchina adotti una numerazione, per esempio `.claude-account1` e `.claude-account2`, quella è una convenzione locale: riportare i percorsi rilevati e le email lette, senza inventare associazioni.
3. Se esiste un solo profilo, dichiarare quale account e in uso e proseguire al punto 5.
4. Se esistono più profili, chiedere all'utente con quale account intende inizializzare il progetto, mostrando quello attualmente attivo. Se l'utente indica un account diverso da quello attivo, NON proseguire: spiegare che il cambio richiede di rilanciare Claude Code con quella directory di configurazione, perché la variabile e letta solo all'avvio del processo. Proseguire solo quando l'account attivo coincide con quello voluto.
5. Eseguire il check di igiene dell'account nella variante del sistema dichiarato, `templates/tools/check-account-hygiene.ps1` su Windows e `.sh` su Linux. Verifica che l'account abbia `autoMemoryEnabled: false`, l'hook `SessionEnd` di wipe, e che lo script di wipe installato sia configurato per questa macchina e non per un'altra.
6. Se il terzo controllo risulta FAIL, non correggerlo per conto proprio. Elencare gli slug realmente presenti eseguendo lo script di wipe in sola lettura, `-List` su Windows e `--list` su Linux, e chiedere all'utente quali radici di sviluppo vadano preservate, mostrandogli l'elenco: su una macchina diversa da quella dove il template è stato scritto i prefissi non sono `D--` ed `E--`, e su Linux non hanno nemmeno quella forma, perché gli slug derivano dal percorso assoluto. Solo dopo la risposta si scrivono i prefissi nello script installato, si prova con `-DryRun` oppure `--dry-run`, e si registra l'hook, mai senza conferma sul `settings.json` dell'account.

## Passo 0.5 - Selezione dell'identità git e del remote

Subito dopo l'account Claude, e prima del runbook, decidere con quale identità git verranno firmati i commit e a quale repository GitHub agganciare il remoto. Identità git e account Claude sono cose distinte: la prima e la coppia user.name/user.email più la chiave SSH, la seconda e il profilo di configurazione di Claude Code. Il dettaglio autoritativo della procedura, dei profili disponibili e del caso repo con README e in `rules/git-identity-and-repo.md`.

La rilevazione si fa leggendo la configurazione SSH reale della macchina, mai citando alias a memoria: gli alias sono una convenzione della singola installazione e su una macchina diversa hanno altri nomi e selezionano altre chiavi, con percorsi diversi. Lo strumento è lo stesso su Windows e su Linux, perché il formato di `ssh_config` lo è.

```
python .claude/templates/tools/detect-ssh-profiles.py --repo .
```

Stampa gli alias verso `github.com` con la chiave che ciascuno seleziona e se quel file esiste, le chiavi presenti in `~/.ssh` che nessun alias richiama, gli eventuali blocchi `Match` non interpretati, l'identità git globale con `user.useConfigOnly`, e identità locale, remoto e `core.sshCommand` del repository. Esce con codice diverso da zero se non trova alcun alias verso GitHub.

Azione:

1. Presentare all'utente gli alias trovati così come sono stati letti, senza attribuire a nessuno un'identità: il nome di un blocco `Host` è una mnemonica di chi ha configurato quella macchina e non dice per chi è. Se un alias ha la chiave mancante, dirlo prima di proporlo. Se il rilevamento non trova alcun alias, fermarsi e spiegare che il profilo va creato prima di proseguire, senza generarne uno di iniziativa.
2. Chiedere, in una sola domanda e senza lasciare niente al caso, tutti i valori che serviranno: quale alias usare, quale `user.name` e quale `user.email` firmeranno i commit di questo progetto, e quale sia l'owner GitHub e il nome del repository di destinazione. Su una macchina che non è quella dove il template è stato scritto, questa domanda si pone anche quando gli alias sembrano familiari.
3. Impostare l'identità a livello locale del repo, mai globale: `git config --local user.name`, `git config --local user.email`, e su Windows `git config --local core.sshCommand` verso l'OpenSSH di sistema. Collegare il remoto con l'alias scelto, nella forma `git remote add origin git@<alias>:<owner>/<repo>.git`. Su Linux omettere `core.sshCommand`.
4. Se `user.useConfigOnly` globale non è impostata, proporre di abilitarla (`git config --global user.useConfigOnly true`) per impedire commit con l'identità sbagliata; essendo globale, eseguirla solo su conferma esplicita.
5. Verificare rilanciando lo strumento con `--repo .`, che rilegge identità locale, remoto e `core.sshCommand` in un colpo solo, e confermare la raggiungibilità del profilo con `ssh -T git@<alias>`, confrontando l'utente che GitHub dichiara di riconoscere con l'owner del remoto appena impostato.
6. Non eseguire commit ne push. Indicare all'utente i comandi manuali del primo commit/push e, se il repo remoto ha già un README o una licenza, il `git pull origin main --rebase` prima del push, come da regola.

## Template canonici

Se esiste la cartella `.claude/templates/`, gli scheletri dell'anatomia sono già pronti e vanno istanziati invece di ricostruirli a memoria: si copiano nella loro posizione finale secondo la mappa in `templates/README.md` e si sostituiscono i segnaposto tra parentesi angolari (nome progetto, hash del commit corrente, branch, data) con i valori reali. I file di `_notes/` si istanziano solo dopo aver confermato che `_notes/` è ignorato. Le schede di `context/` si copiano con struttura e frontmatter e si popolano leggendo il codice nei passi successivi, mai con contenuto inventato. Se la cartella `templates/` non è presente, ricostruire l'anatomia dalla descrizione di `.claude/PROJECT-SYSTEM.md`.

Oltre all'anatomia sotto `.claude`, i template coprono anche i file di radice del progetto, fratelli di `.claude`: `CLAUDE.md` tracciato come fonte canonica delle istruzioni condivise, `AGENTS.md` tracciato come punto di ingresso nativo di Codex, `CLAUDE.local.md` ignorato come stub di override personali, e, solo se il progetto integra un servizio esterno tramite un server MCP, `.mcp.json` istanziato dal template opzionale e la cartella `mcp/` con l'implementazione del server, entrambi tracciati e in radice, mai sotto `.claude`. `AGENTS.md` resta un ponte sottile e non duplica le regole. Senza integrazione MCP gli ultimi due elementi non si creano.

I `templates/` contengono inoltre i pacchetti opzionali, riconoscibili come sottocartelle con un proprio `README.md` di istanziazione. Non si attivano d'ufficio e non si scelgono a occhio: si attraversano con la skill `gate-pacchetti`, che li propone per settore e uno per volta, con la stessa logica di conferma esplicita del gate MCP (vedi Passo 4).

## Passi 1-8 - Runbook di inizializzazione

Leggere la sezione "Comando di inizializzazione" di `.claude/PROJECT-SYSTEM.md` ed eseguirne i passi nell'ordine indicato, applicando anche le sezioni richiamate (anatomia di `.claude`, mappa ibrida tracciato/ignorato, igiene del version control). Dove esistono i template canonici, istanziarli invece di rigenerare il contenuto. In sintesi operativa, i passi sono i seguenti, ma il dettaglio autoritativo resta nel file.

1. Verifica del version control: scansione di file tracciati e storia alla ricerca di segreti (chiavi private, stringhe di connessione con credenziali, password SMTP, token di firma, service account) e di file indicizzati per errore. Riportare gli esiti senza committare.
2. Predisposizione del `.gitignore` con le esclusioni del livello privato: almeno `_notes/`, `CLAUDE.local.md`, `.claude/settings.local.json`, i `.docx` grezzi con eventuali eccezioni curate, e le cartelle scratch `.tmp-doc-*` (coprono anche la cache del pacchetto `doc-ingest`).
3. Creazione dell'anatomia di `.claude` nella forma minima: `settings.json`, le cartelle `commands`, `rules`, `skills`, `agents`, la cartella `memory` con `index.md`, `progress.md`, `decisions.md`, e la cartella `context` con `STACK.md`, `design-and-security.md`, `deployment.md`, `dev-testing.md`, `current-work.md`, `roadmap.md` e la sottocartella `diagrams`. Sulla cartella `rules` vale il budget della sezione 24 di `PROJECT-SYSTEM.md`, e va rispettato dalla prima riga invece che sanato dopo: ogni `.md` che finisce lì viene caricato a ogni avvio di sessione e concorre al limite della piattaforma, quindi vi si copiano le sole regole la cui applicabilità non dipende da una scelta di configurazione del progetto, mentre una norma situazionale si istanzia come `RIFERIMENTO.md` della propria skill con la riga di innesco nell'indice del `CLAUDE.md`. Si installa contestualmente `tools/misura-istruzioni.py` e, dove il progetto adotta l'hook pre-commit, il passo `instruction-budget`, e si lancia la misura una volta prima di chiudere l'inizializzazione, così che il progetto nasca con il numero dichiarato invece di scoprirlo al primo avviso.
4. Creazione o aggiornamento di `CLAUDE.md` nella radice perché indicizzi esplicitamente i file satellite e contenga la procedura di ripresa, creazione o aggiornamento del ponte `AGENTS.md` dal template canonico, più lo stub di `CLAUDE.local.md` ignorato per gli override personali. Sull'MCP chiedere sempre esplicitamente all'utente, sia in greenfield sia in allineamento, se vuole configurare un server MCP, offrendo di crearlo ora o di rimandarlo come promemoria; non assumere mai. In allineamento il server consigliato e `code-context-provider-mcp`, già pronto in `templates/mcp.json`, che via `npx` espone struttura e simboli del codice per mappare un progetto esistente. In caso affermativo istanziare in radice `.mcp.json` dal template della variante del sistema operativo (`templates/mcp.json` su Linux/macOS, `templates/mcp.windows.json` su Windows; per un server avviato via `npx` non serve la cartella `mcp/`, che riguarda solo i server implementati in proprio), mai sotto `.claude`, e se un `.mcp.json` esiste già mostrare la differenza invece di sovrascrivere. Per i pacchetti opzionali non improvvisare un gate qui: invocare la skill `gate-pacchetti`, che è la procedura autoritativa e legge il registro `.claude/templates/PACKAGES.md`. Il registro contiene più di ottanta voci divise in dieci settori, e la skill li attraversa per settore invece che per riga: raccoglie prima i fatti del progetto, dichiara quali settori ha riconosciuto e da che cosa, li fa correggere dall'utente, e propone poi i soli pacchetti dei settori riconosciuti, uno per volta, ciascuno con che cosa fa, perché a questo progetto potrebbe servire, legandolo a un fatto raccolto e non al trigger generico, e che cosa costa, contando fra i costi anche le capacità che duplicherebbe. Quando riconosce ricerca scientifica o tecnica, chiede esplicitamente e separatamente per OpenAlex MCP, PaperQA2 e Feynman seguendo `templates/academic-researcher/INTEGRAZIONI-TOOL.md`; l'attivazione di `academic-researcher` non implica le tre scelte. Non assume mai, e un pacchetto già presente non si reinstalla ma se ne mostra la differenza. Su un sì istanzia seguendo il `README.md` del pacchetto e mostra subito il recap d'uso; su un no registra il rifiuto come promemoria esplicito, perché un rifiuto non registrato verrà riproposto identico alla tornata successiva. Il gate si riesegue a ogni tornata di allineamento, non una volta sola, perché il catalogo cresce e il progetto diventa qualcosa che all'inizio non era. Con la stessa logica, e con la stessa regola di registrare anche i rinvii, invocare la skill `separazione-ambienti` per il gate della separazione fra test e produzione, secondo la norma `.claude/skills/separazione-ambienti/RIFERIMENTO.md`: la skill dichiara prima i fatti osservati nel repository e nella macchina, pone le sole domande che i fatti non risolvono, e per ogni asse propone una forma spiegando, dalla guida del pacchetto `separazione-ambienti`, che cosa significa sceglierla rispetto alle alternative, che cosa richiede, che cosa costa e come fallisce, con le fonti. Non si raccomanda mai un modello per default, e in allineamento un modello già in uso si riconosce e si documenta invece di sostituirlo. L'esito va nella sezione "Modello di separazione" di `context/deployment.md` e in una voce ADR di `memory/decisions.md`, e guida e registro delle fonti si istanziano sotto `docs/separazione-ambienti/`; se la scelta comprende più alberi di lavoro si applica anche `.claude/skills/alberi-di-lavoro/RIFERIMENTO.md`. Con la stessa logica, chiedere esplicitamente se creare un `README.md` pubblico per la repository GitHub, istanziandolo dal template `templates/README-project.md` se presente; se no, lasciare un promemoria esplicito. Il `README.md` è tracciato in git, vive in radice accanto a `CLAUDE.md`, ed è destinato ai visitatori della repository (non al team interno che usa `CLAUDE.md`). Il suo contenuto riflette stack, workflow e stato del progetto nella misura in cui è condivisibile pubblicamente. Non assumere: chiedere sempre.
5. Creazione di `_notes` con `DIARIO.md`, `RESOCONTO.md`, `TEST-CHECKLIST.md`, solo dopo aver confermato che `_notes` e ignorato.
6. Installazione delle skill del motore di riconciliazione e del flusso git, ciascuna come `SKILL.md` nella propria cartella sotto `.claude/skills`, insieme alle quattro che portano una norma caricata su richiesta con il proprio `RIFERIMENTO.md`, cioè `prove-che-misurano`, `fonti-non-recuperabili`, `alberi-di-lavoro` e `separazione-ambienti`: sono norme e non capacità facoltative, e ciascuna acquista una riga di innesco nell'indice del `CLAUDE.md` che nomina la situazione con le parole con cui si presenta. Istanziare anche `templates/tools/sync-codex-skills.py` in `tools/`, eseguirlo per generare i wrapper sotto `.agents/skills/` e verificare subito con `python tools/sync-codex-skills.py --check`. Ogni successiva installazione o modifica di una skill canonica ripete sincronizzazione e controllo.
7. Popolamento delle schede di `context` con il solo frontmatter di riconciliazione ancorato al commit corrente, senza inventare contenuto: il contenuto si scrive nei passi successivi leggendo il codice. Su un greenfield appena inizializzato non c'è ancora un commit, perché il primo commit lo fa l'utente dopo l'init: in quel caso lasciare `generated-from-commit` e `last-verified-commit` a un segnaposto esplicito come `PENDING-FIRST-COMMIT`, riportare lo stesso segnaposto come commit di riferimento in `memory/index.md`, e ancorarli al primo commit reale subito dopo, eseguendo la skill `sync-context` che li porta a `HEAD`.
8. Prima voce in `memory/progress.md` che registra l'inizializzazione e la data, e snapshot iniziale in `memory/index.md`.

Quando si parte da uno stack noto, in questo passo si possono installare skill già predisposte per quel framework o per la piattaforma di deploy, invece di ricostruirle.

## Note operative

Fermarsi a chiedere conferma prima di azioni difficilmente reversibili o che toccano il version control. Non eseguire mai `git add`, `commit` o `push`: prepara i file e lascia all'utente le operazioni git. Non popolare le schede con contenuto dedotto in fase di init. Se il progetto e già parzialmente inizializzato, allineare invece di sovrascrivere, segnalando cosa esiste già.
