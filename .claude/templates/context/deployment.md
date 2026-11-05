---
generated-from-commit: <hash del commit di prima scrittura>
generated-from-branch: <branch>
generated-date: <YYYY-MM-DD>
covers-paths:
  - <glob delle aree descritte, es. infra/**, .github/**>
last-verified-commit: <hash dell'ultima verifica o aggiornamento>
---

# Deployment

> Popolare leggendo la configurazione reale di infrastruttura e CI. Commit, push e deploy restano operazioni manuali dell'utente.

## Modello di separazione fra test e produzione

> Scelto al gate dell'inizializzazione o dell'allineamento fra i modelli del catalogo `.claude/skills/separazione-ambienti/RIFERIMENTO.md`, e registrato anche come ADR in `memory/decisions.md`. Non si deduce: se il gate non è stato fatto, la sezione lo dice.

- Modello: <una sigla per asse dal catalogo, per esempio R2 a richiesta, P1, D0, L1>
- Stato: <in esercizio / previsto e non ancora creato, per ciascun ambiente>
- Scelto il: <YYYY-MM-DD>, ADR: <ADR-NNN>
- Perché questo e non gli altri: <il fatto del progetto che lo decide>
- Rischi da presidiare: <quelli del modello scelto e i rischi trasversali del catalogo che il modello non esclude, con il presidio di ciascuno>

## Livelli

<descrizione dei livelli test/staging e produzione, hosting, domini>

## Alberi di lavoro

> Da compilare solo se il progetto tiene gli ambienti in alberi di lavoro separati (`git worktree`), secondo la norma `.claude/skills/alberi-di-lavoro/RIFERIMENTO.md`. Con un albero solo la sezione si rimuove.

| Percorso assoluto | Branch | Ambiente | Porta | Note |
|---|---|---|---|---|
| <percorso> | <main> | <produzione> | <porta> | <albero da non toccare durante il lavoro> |
| <percorso> | <staging> | <test> | <porta> | <base dati e `.env` propri> |

Albero autorevole per la memoria: `<percorso assoluto>` (branch `<branch più avanti>`). La memoria sotto `.claude/memory/` si legge da quell'albero per percorso assoluto e non si copia né si fonde negli altri; le decisioni prese altrove si registrano lì. La riga si aggiorna quando un'altra branch passa avanti, per esempio dopo una fusione.

## Comandi

<comandi di build, di rilascio e di rollback, con il contesto in cui si eseguono>

## Accesso dell'agente agli ambienti

<Per ciascun ambiente indicare chi esegue letture e modifiche, quali operazioni sono autorizzate e quale riferimento del progetto governa gli accessi privilegiati. L'esistenza di una chiave o di un alias non concede un permesso al runtime. Se l'agente non può accedere, prepara comandi con macchina, directory, ramo e perimetro espliciti; l'utente li esegue e restituisce l'esito.>

Ogni misura di produzione dichiara se è stata raccolta nel giro corrente oppure ripresa da una verifica precedente, con data e perimetro. Un'autorizzazione permanente dipende da una decisione esplicita del proprietario e da una regola nelle impostazioni dei permessi del client, verificata nel suo ambito; una frase nella scheda non la rende attiva e non supera un rifiuto della modalità di approvazione.

## Variabili d'ambiente e segreti

<elenco delle variabili richieste e dove sono gestite; i valori non si committano mai>

## Deroghe temporanee e revoca

<Ogni deroga apre nello stesso giro una voce del registro delle pendenze: motivo, effetti che richiedono gestione manuale, responsabile, condizione o scadenza di revoca e verifica che ne dimostri la chiusura. Una modalità provvisoria non diventa una scelta permanente per assenza di un richiamo. Nessuna deroga modifica da sola i permessi del runtime o autorizza un rilascio.>
