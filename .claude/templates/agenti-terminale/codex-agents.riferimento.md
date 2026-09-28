# Istruzioni di macchina per Codex

> **File di riferimento, versionato.** Copiato in ogni radice `<PROFILO_UTENTE>\.codex-account<N>\AGENTS.md` da `scripts\Installa-Codex.ps1`. Non modificarlo nella radice: le modifiche si fanno qui e si ridistribuiscono con `Installa-Codex.ps1 -Forza`, altrimenti le radici divergono in silenzio.

Questo file è letto da Codex all'inizio di ogni sessione su questa radice, e vale quindi per **qualunque progetto** vi si apra. Contiene la disciplina di macchina e di account. Le regole del singolo progetto stanno nel progetto.

## Dove vive tutto il resto

Questa radice contiene **solo lo stato di Codex**: credenziali, configurazione, sessioni. Non contiene strumenti, e non deve contenerne.

Strumenti, documentazione e procedure vivono nel **template** del sistema di progetto, nel pacchetto `agenti-terminale`, che è la fonte di verità e l'unica cosa che sopravvive a una formattazione:

| Cosa | Dove |
|---|---|
| Installazione e ricostruzione da zero | `templates/agenti-terminale/tools/Installa-Agenti.ps1` |
| Avvio su radice isolata, con pulizia all'uscita | `.claude/templates/agenti-terminale/tools/Avvia-Codex.ps1` |
| Wipe selettivo degli store | `.claude/templates/agenti-terminale/tools/Pulisci-Codex.ps1` |
| Comandi brevi di shell | `.claude/templates/agenti-terminale/tools/Installa-Comandi.ps1` |
| Consumo di tutte le radici | `.claude/templates/agenti-terminale/tools/Consumo-Agenti.ps1` |
| Configurazione di riferimento | `.claude/templates/agenti-terminale/codex-config.riferimento.toml` |
| Questo file | `.claude/templates/agenti-terminale/codex-agents.riferimento.md` |

Il repository di **macchina** conserva invece ciò che riguarda solo questo computer: la fotografia del suo stato, i valori compilati, e un punto d'ingresso sottile che chiama la catena del template con i parametri di questa macchina.

Una radice si **ricostruisce** da lì, non si copia da un'altra macchina. Le credenziali non si trasportano: si rifà un login.

## Come si avvia una sessione

Sempre da `scripts\Avvia-Codex.ps1 -Account <N>`, mai digitando `codex` a mano. Il motivo non è comodità: se `CODEX_HOME` non è impostata Codex **ricade in silenzio sulla radice di default** e vi scrive le credenziali dichiarando successo. Il launcher verifica la radice prima di eseguire.

## Memoria

**L'unica memoria legittima è quella versionata dentro la cartella di progetto.** La memoria nascosta dell'agente è disattivata in configurazione, e va lasciata disattivata: una memoria per utente, non ispezionabile e fuori dal repository, non è una variante di quel principio ma la sua negazione.

Se un progetto ha una propria memoria documentale, si legge quella, e la si aggiorna lì. Niente di ciò che deve sopravvivere alla sessione vive qui dentro.

## Perimetro di esecuzione

`approval_policy = "on-request"` e `sandbox_mode = "workspace-write"`: le operazioni sicure sono ammesse, quelle verso l'esterno restano manuali.

**Commit, push e deploy non sono mai automatici.** L'agente prepara i file, l'utente esegue. Vale su ogni progetto di questa macchina, senza eccezioni.

## Segreti e dati identificanti

Non si scrivono mai dentro un file tracciato: né credenziali, né chiavi API, né indirizzi di posta, né identificativi di organizzazione. Nei file tracciati si usano segnaposto fra parentesi angolari; la mappatura reale vive nel livello privato del progetto, ignorato da git.

Prima di proporre un commit su un repository **pubblico**, si verifica che nessun file tracciato contenga identificativi reali. Il livello di memoria è tracciato quanto i documenti, e va sottoposto allo stesso controllo: è il posto in cui è più facile dimenticarsene.
