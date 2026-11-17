# Pacchetto opzionale: superpowers

> La mappa fra le quindici skill di `obra/superpowers` e ciò che questo sistema ha già: che cosa aggiungono, dove dicono il contrario di una regola del progetto, quanto pesano all'avvio. Non contiene copie delle skill: si installano come plugin dalla fonte, e si aggiornano da lì.

<!-- readme-summary: mappa fra le skill di superpowers e il sistema, con i punti in cui prevale la regola del progetto e il peso all'avvio -->

## Che cosa è, letto alla fonte

Il repository è github:obra/superpowers , licenza MIT, versione v7.0.2 del 2026-11-03. Il 2026-11-16 un subagent ne ha letto README, albero dei file e hook attraverso l'API di GitHub; chi scrive non ha riletto i file. Contiene quindici skill, nessun comando e nessun agente proprio, e un solo hook, all'apertura della sessione.

Il proprietario lo indica come molto utile e lo vuole al centro del modo di lavorare. La ragione si vede dall'elenco: è un metodo intero, che va dalla domanda iniziale al ramo chiuso, e ogni passo è una skill che l'agente invoca da sé.

## Installazione

In Claude Code, dal marketplace ufficiale:

```
/plugin install superpowers@claude-plugins-official
```

Oppure dal marketplace dell'autore, due comandi in ordine:

```
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
```

In Codex CLI il README indica `/plugins`, la ricerca di `superpowers` e «Install Plugin»; da riga di comando, provato il 2026-11-16 con codex-cli 0.166.0, è `codex plugin add superpowers@openai-curated-remote`. Su una macchina con più radici di account lo porta in tutte `Installa-Plugin.ps1` del pacchetto `agenti-terminale`. L'installazione è per account e non per progetto: nel progetto entra soltanto la riga che dichiara che il plugin è in uso, in `.claude/pacchetti-istanza.json` e nel `CLAUDE.md`.

## Quanto pesa all'avvio

L'hook `SessionStart`, con matcher `startup|clear|compact`, inietta il testo della skill `using-superpowers`: il file pesa 3.192 byte e con l'involucro l'iniezione è stimata in circa 3.400 caratteri, a ogni avvio, a ogni azzeramento e a ogni compattazione. È una stima dalla dimensione del file, non una misura sull'uscita dell'hook. A questo si aggiungono le descrizioni delle quindici skill, che il client carica come quelle di ogni skill. Su un progetto che ha lavorato per scendere a settantamila caratteri di avvio il costo va guardato prima di installare, con `/context`.

Quel testo impone di cercare e invocare una skill prima di ogni risposta, comprese le domande di chiarimento. È ciò che rende il metodo affidabile, ed è anche ciò che lo fa prevalere, nell'attenzione dell'agente, su istruzioni scritte con meno enfasi: i punti della sezione «Dove prevale la regola del progetto» vanno quindi scritti nel `CLAUDE.md` del progetto e non lasciati a questa pagina.

## La mappa

| Skill di superpowers | Che cosa fa | Che cosa il sistema ha già | Esito |
|---|---|---|---|
| `brainstorming` | Prima di ogni lavoro creativo fa domande per capire l'intento, rilegge ciò che ha capito e scrive un documento di design | Le sessioni di interrogazione di `matt-pocock-skills`; la skill `crea-agente` per il solo caso degli agenti | Aggiunge: il sistema non ha un passo obbligato di domande prima di costruire |
| `writing-plans` | Da una specifica a un piano di compiti da due a cinque minuti, con percorsi esatti e verifiche | `micro-passi`, `roadmap` | Si sovrappone a `micro-passi`; il piano di superpowers è più fine e porta il codice |
| `executing-plans` | Esegue il piano nella sessione, con una revisione alla fine | Nessun equivalente diretto | Aggiunge |
| `subagent-driven-development` | Un subagent nuovo per compito, con revisione in due stadi dopo ciascuno | `lavoro-a-lotti` per i corpus, `instradamento-modelli` per il modello | Aggiunge il ciclo per compito; consuma molto, vedi sotto |
| `dispatching-parallel-agents` | Più agenti per compiti indipendenti senza stato condiviso | La regola sulla delega in `token-economy.md` | Si sovrappone |
| `test-driven-development` | Ciclo rosso, verde, rifattorizzazione; scarta il codice scritto prima della prova | `prove-che-misurano`, che chiede se la prova misura il difetto | Complementari: una dà l'ordine, l'altra giudica la prova |
| `systematic-debugging` | Quattro fasi sulla causa radice | I sei errori d'indagine di `prove-che-misurano` e `recupero-dei-fatti.md` | Complementari |
| `verification-before-completion` | Prima di dire finito si eseguono le verifiche e se ne legge l'esito | `chiudi -SoloControlli`, la regola sull'onestà del lavoro fatto | Si sovrappone |
| `requesting-code-review`, `receiving-code-review` | Revisione contro il piano fra un compito e l'altro; come rispondere ai rilievi | `dev-skills`, l'agente `code-reviewer`, la revisione nativa | Si sovrappone |
| `using-git-worktrees` | Crea un albero di lavoro isolato su un ramo nuovo | La skill `alberi-di-lavoro` | Attenzione, vedi sotto |
| `finishing-a-development-branch` | A lavoro concluso propone unione, richiesta di unione, tenere o scartare, e pulisce l'albero | `chiudi`, versionamento manuale | Contrasta, vedi sotto |
| `writing-skills` | Come scrivere e collaudare una skill | La sezione «Come estendere il sistema» del README | Complementari |
| `diagnosing-superpowers`, `using-superpowers` | Diagnosi di una sessione andata male; introduzione iniettata all'avvio | Niente | Proprie del plugin |

## Dove prevale la regola del progetto

Tre punti, da scrivere nel `CLAUDE.md` del progetto che installa il plugin.

Il versionamento resta manuale. Un piano di superpowers può prevedere un commit a ogni compito e la skill di chiusura del ramo propone unione e richiesta di unione: nel sistema `git add`, commit e push sono del proprietario, e una milestone si chiude con `chiudi`. Che le skill committino da sé non è stato osservato in una corsa: è ciò che il loro scopo dichiarato lascia attendere, e va guardato alla prima sessione.

La memoria vale per il ramo. Un albero di lavoro creato da `using-git-worktrees` porta la memoria versionata del ramo da cui nasce, e scriverla lì produce il difetto che la skill `alberi-di-lavoro` descrive: prima di lavorare in un albero nuovo si legge quella.

I subagent consumano dalla stessa finestra del piano. Lo sviluppo guidato da subagent apre un agente per compito e due revisioni dopo ciascuno: con il pacchetto `instradamento-modelli` conviene mettere in tabella i tipi di agente meccanici e impostare la riserva settimanale, così che il ciclo si fermi prima di esaurire la settimana.

## Come resta aggiornato

Il repository è nel registro delle fonti a monte del template, che lo interroga a ogni apertura di sessione e segnala una versione nuova: a quel punto si rilegge questa mappa. La copia installata la aggiorna il gestore dei plugin del client, per account, con `/plugin marketplace update` seguito dall'aggiornamento del plugin; se l'aggiornamento automatico dei marketplace sia attivo per difetto non è stato verificato qui.

## Che cosa non è stato fatto

Il plugin è stato installato il 2026-11-16 sulle radici di account della macchina di sviluppo, nella versione 7.0.2 per Claude Code e 7.0.1 per Codex, e non è ancora stato usato su un compito. La mappa confronta le descrizioni lette a monte con i pacchetti del sistema, non due corse sullo stesso compito: la prova che manca è un compito vero svolto una volta con `micro-passi` e una con il ciclo di superpowers, misurando consumo ed esito.
