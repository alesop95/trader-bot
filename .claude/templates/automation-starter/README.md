# Pacchetto automation-starter

> Pacchetto opzionale del sistema di progetto, separato e alternativo rispetto a
> `claude-code-handoff`. Copre i livelli headless e routine di Claude Code, cioe' l'esecuzione
> non interattiva di un prompt e la sua messa su schedulazione periodica, restando
> deliberatamente dentro l'uso incluso nei piani Team o Max: nessun componente di questo
> pacchetto e' pensato per funzionare, ne' viene proposto come funzionante, tramite una chiave
> `ANTHROPIC_API_KEY` a fatturazione a consumo. Dove `claude-code-handoff` usa quella chiave nel
> proprio workflow GitHub Actions per una pipeline specifica di ridistillazione, questo pacchetto
> resta generico e autentica sempre o via login locale dell'abbonamento (`claude login`) o via
> token di abbonamento (`claude setup-token`), mai via API a pagamento.

## Cosa risolve

L'anatomia del sistema descritta in `PROJECT-SYSTEM.md` copre memoria, regole, skill, agent, MCP
e hook come scelte opzionali gia' scaffoldabili all'inizializzazione, ma non offre un modo
generico per eseguire un prompt o una skill del progetto fuori da una sessione interattiva, ne'
per metterlo su una cadenza ricorrente. Questo pacchetto colma quel vuoto per i progetti che
vogliono un task automatico, per esempio un controllo periodico del drift delle schede di
`context/`, un promemoria, un report ricorrente, senza pero' accettare la fatturazione a consumo
dell'API come prerequisito. E' un'estrazione generica del pattern gia' dimostrato da
`claude-code-handoff`, riscritta per restare dentro la quota di abbonamento invece che legata a
quella singola pipeline.

## Le tre vie

La prima via e' locale: lo script `headless-run.ps1`/`.sh` invoca `claude -p` sulla macchina
dell'utente, autenticato dal login interattivo gia' fatto con `claude login`. Non richiede alcun
secret ne' alcuna chiave: usa la stessa sessione di abbonamento con cui si lavora in modo
interattivo. E' la via piu' semplice e quella con il rapporto costo-complessita' migliore, ma
richiede che la macchina sia accesa nel momento in cui la routine deve girare; per la
schedulazione stessa serve un pianificatore del sistema operativo esterno al pacchetto, Task
Scheduler su Windows o cron su Linux e macOS, documentato piu' sotto.

La seconda via e' un workflow GitHub Actions, `automation-routine.yml`, per i progetti che
vivono su GitHub e vogliono la routine anche senza una macchina locale accesa. Autentica con la
variabile `CLAUDE_CODE_OAUTH_TOKEN`, un token generato una tantum con il comando `claude
setup-token` da un account con piano Team o Max: quel token e' legato all'account personale e la
corsa consuma la quota dell'abbonamento, non la fatturazione a consumo dell'API[^1]. Richiede
inoltre che la Claude GitHub App sia installata sul repository perche' il token possa leggere e
scrivere sul checkout.

La terza via non richiede alcuna istanziazione: sono le routine cloud native di Claude Code
stesso, quelle esposte dalla skill `/schedule` disponibile in sessione, l'equivalente diretto del
livello 10 dell'infografica come capacita' gia' del prodotto, sullo stesso piano di `/compact` o
`/clear` per i livelli 1 e 3. E' l'opzione a minor attrito quando basta schedulare un prompt
senza toccare il repository ne' aprire pull request. Un punto da segnalare come non ancora
verificato in questo pacchetto: i limiti di quota e la cadenza minima consentita per le routine
cloud native sul piano specifico dell'utente restano da controllare direttamente con `/schedule`
o con la documentazione ufficiale del proprio account prima di farvi affidamento, perche' non e'
stato possibile confermarli con una fonte esterna al momento della stesura di questo README.

## Mappa di istanziazione

```
templates/automation-starter/tools/headless-run.ps1                   ->  <radice>/tools/headless-run.ps1                         (tracciato; Windows)
templates/automation-starter/tools/headless-run.sh                    ->  <radice>/tools/headless-run.sh                          (tracciato; Linux/macOS, chmod +x)
templates/automation-starter/workflows/automation-routine.yml         ->  <radice>/.github/workflows/automation-routine.yml       (tracciato, opzionale)
templates/automation-starter/workflows/automation-routine-prompt.txt  ->  <radice>/.github/automation-routine-prompt.txt          (tracciato, opzionale)
(generato a ogni corsa)                                                    <radice>/_notes/automation/<timestamp>.json              (ignorato)
```

Il gate del sistema operativo dell'inizializzazione istanzia la variante di script giusta;
istanziarle entrambe e' innocuo nei progetti che vivono su piu' macchine. Il workflow GitHub
Actions e il suo file di prompt sono un componente opzionale nel componente, distinto dallo
script locale: si istanziano solo se il progetto vive su GitHub e si vuole la seconda via.

## Come si usa, passo per passo

1. Verificare l'autenticazione locale con `claude login` (piano Team o Max) prima di ogni uso:
   lo script si rifiuta di girare se trova `ANTHROPIC_API_KEY` nell'ambiente, proprio per
   impedire che la corsa scivoli senza accorgersene sulla fatturazione a consumo.
2. Corsa locale singola: `./tools/headless-run.ps1 -Prompt "<prompt>"` su Windows oppure
   `./tools/headless-run.sh "<prompt>"` su Linux/macOS. Il default e' `--permission-mode plan`,
   sola lettura: per un task che deve anche scrivere file si passa esplicitamente
   `-PermissionMode acceptEdits` (PowerShell) o `--permission-mode acceptEdits` (bash), mai
   `bypassPermissions`, che questo script rifiuta per costruzione.
3. Pianificazione locale: chi vuole la ricorrenza senza GitHub Actions registra lo script nel
   proprio pianificatore di sistema. Su Windows, da un terminale con i permessi opportuni:
   `schtasks /create /tn "AutomationStarter" /tr "powershell -NoProfile -File C:\percorso\tools\headless-run.ps1 -Prompt 'Esegui sync-context'" /sc weekly /d MON /st 06:00`.
   Su Linux o macOS, una riga di crontab: `0 6 * * 1 cd /percorso/progetto && ./tools/headless-run.sh "Esegui sync-context" >> _notes/automation/cron.log 2>&1`.
   In entrambi i casi la registrazione nel pianificatore del sistema operativo resta un'azione
   manuale dell'utente: il pacchetto non la esegue da solo.
4. Automazione remota: chi preferisce non tenere una macchina accesa genera il token con `claude
   setup-token`, lo registra come secret `CLAUDE_CODE_OAUTH_TOKEN` del repository, personalizza
   `automation-routine-prompt.txt` con l'istruzione della routine, e istanzia il workflow. La
   cadenza di default e' settimanale; si modifica il campo `cron` del file secondo necessita'.
5. Routine cloud native: in alternativa alle prime due vie, si usa direttamente `/schedule`
   dentro una sessione per registrare la stessa routine come capacita' nativa del prodotto, senza
   toccare il repository.
6. Ogni corsa locale produce un file in `_notes/automation/`, ignorato da git, da consultare per
   verificare l'esito. Ogni corsa via GitHub Actions apre una pull request da rivedere prima del
   merge: commit e push restano manuali anche in automazione, nessuna corsa headless scrive mai
   direttamente su un branch condiviso.

## Rapporto con le regole del sistema

Il vincolo di non commettere mai direttamente da un'automazione discende dalla stessa regola
generale del sistema per cui commit e push restano manuali dell'utente: la seconda via rispetta
questo vincolo aprendo sempre una pull request, mai un push diretto. Il default
`--permission-mode plan` e il rifiuto di `bypassPermissions` seguono la raccomandazione di
`.claude/rules/security-permissions.md` per le sessioni autonome su macchina reale, che indica
`dontAsk` con una whitelist costruita ad hoc o l'`acceptEdits` esplicito come vie preferibili al
bypass totale. Il pacchetto non introduce una whitelist propria in `settings.json`: chi attiva la
seconda o la terza via e vuole restringere ulteriormente i permessi della corsa costruisce quella
whitelist nel proprio `settings.json`, come descritto nella stessa regola.

## Vincoli e onesta'

Il vincolo dichiarato di questo pacchetto, restare dentro l'uso incluso nei piani Team o Max, e'
imposto per costruzione solo nella prima via: lo script locale controlla `ANTHROPIC_API_KEY` e si
ferma se la trova. Nella seconda via il vincolo e' documentale, non tecnico: il workflow verifica
che il secret `CLAUDE_CODE_OAUTH_TOKEN` sia presente e si ferma se manca, ma non puo' impedire che
qualcuno rinomini quel secret facendolo puntare a una chiave API invece che a un token di
abbonamento, quindi la responsabilita' di non farlo resta di chi configura il secret. Il
meccanismo dell'autenticazione via token di abbonamento su GitHub Actions, incluso il comando
`claude setup-token` e la necessita' della Claude GitHub App, e' confermato dalla documentazione
ufficiale del progetto `anthropics/claude-code-action` al momento della stesura di questo
README[^1]; i limiti di quota effettivi dell'abbonamento sotto uso ricorrente restano governati
dal piano dell'utente e vanno verificati sul proprio account, non assunti da questo documento. La
terza via, le routine cloud native, e' segnalata nella sezione precedente come non verificata nei
suoi limiti specifici: va controllata direttamente prima di farvi affidamento per un task
importante.

Attrito osservato dal vivo (pilota 2026-07-02): la prima corsa di `headless-run` su una cartella
che Claude Code non ha ancora aperto interattivamente stampa "Ignoring N permissions.allow
entries... this workspace has not been trusted", perche' il dialogo di trust del workspace non e'
mai stato accettato per quella directory. La corsa prosegue comunque con i permessi di base (non
si blocca), ma ignora la allowlist personalizzata del progetto finche' il workspace non risulta
fidato: aprire una volta il progetto in modo interattivo con `claude` e accettare il dialogo, oppure
impostare `projects["<percorso>"].hasTrustDialogAccepted: true` nel file di configurazione
dell'account, prima di affidarsi a una allowlist su una macchina o un progetto mai visti prima.

Due limiti piu' seri, trovati nel secondo giro di validazione (2026-07-02), riguardano la scelta di `-PermissionMode` per task che devono davvero eseguire qualcosa, non solo rispondere. Primo: `-PermissionMode plan` puo' bloccarsi in modo permanente quando il compito assegnato spinge il modello a pianificare un'azione multi-passo, per esempio delegare a un subagent con il tool `Agent`. In sessione interattiva il piano si chiude con `ExitPlanMode` su conferma dell'utente; in una corsa headless quel tool "esiste ma non e' abilitato in questo contesto", quindi la corsa termina con un piano scritto su disco e nessuna azione eseguita, consumando comunque token e tempo pieno. `plan` resta adatto solo a compiti di sola lettura/risposta diretta (come l'esempio nel recap sotto); per un compito che deve produrre un effetto reale (scrivere file, eseguire una skill che delega a un subagent) serve `acceptEdits` o `dontAsk` con una allowlist. Secondo: anche con `acceptEdits`, i comandi Bash non pre-autorizzati restano negati in assenza di un umano che approvi, e un compito che ha bisogno di verificare qualcosa via shell (per esempio la versione di una dipendenza appena aggiunta) puo' insistere piu' volte sullo stesso comando negato, consumando turni utili senza avanzare: se il compito e' non banale conviene alzare `-MaxTurns` oltre il default di 8 e, se possibile, pre-autorizzare in `settings.json` i comandi di sola lettura che la corsa prevedibilmente user'a.

## Recap dei comandi

- Corsa locale singola: `./tools/headless-run.sh "<prompt>"` (default sola lettura).
- Corsa locale con modifiche: `./tools/headless-run.sh "<prompt>" --permission-mode acceptEdits`.
- Generare il token per GitHub Actions: `claude setup-token`.
- Verificare la routine cloud nativa: `/schedule` dentro la sessione.

## Riferimenti e crediti

Il meccanismo del token di abbonamento per GitHub Actions e' documentato dal progetto ufficiale
`anthropics/claude-code-action` (https://github.com/anthropics/claude-code-action). Questo
pacchetto e' originale al template: non deriva dal bundle Cranot come `claude-code-handoff` o
`hooks-starter`, ma dall'analisi dei dieci livelli di uso di Claude Code svolta in una sessione di
questo stesso progetto, con il vincolo esplicito dell'utente di restare dentro l'uso incluso
nell'abbonamento.

[^1]: *OAuth*, Open Authorization - protocollo di autorizzazione con cui la CLI ottiene un token
di accesso legato all'account senza esporne la password; `claude setup-token` genera un token di
questo tipo, di lunga durata, che GitHub Actions usa al posto di una chiave API.
