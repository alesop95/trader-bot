# Integrazioni di ricerca per progetto

Questo runbook si usa dal gate dei pacchetti quando il progetto richiede ricerca scientifica o tecnica. Le decisioni `openalex`, `paperqa2` e `feynman` sono indipendenti da `academic-researcher` e tra loro. Registra per ciascuna sì, no o non ora nel work log o nelle decisioni del progetto; un sì identifica anche il topic/corpus e l'ambiente in cui il tool sarà usato. Nessuna credenziale va in file tracciati.

| Opzione | Serve per | Costo e limite da spiegare prima della scelta |
|---|---|---|
| OpenAlex MCP ufficiale | Scoprire lavori, recuperare metadati, citazioni e risolvere riferimenti | Connessione MCP remota, login OpenAlex e budget API personale; i metadati non provano il contenuto di un claim |
| PaperQA2 | Interrogare un corpus locale di PDF e altri documenti con risposte ancorate a passaggi | Python 3.11+, modello compatibile LiteLLM, indicizzazione e chiamate ai servizi di metadati; controllare i passaggi citati |
| Feynman | Eseguire ricerca, deep research e audit paper/codice con una CLI autonoma | Installazione e provider separati, uso di servizi esterni e telemetria predefinita; verificare gli output prima di promuoverli nel brief |

## OpenAlex: collegamento a Claude Code e Codex

Il server ufficiale usa `https://mcp.openalex.org/mcp` via HTTP. Se il progetto usa Claude Code, aggiungi questa voce al `mcpServers` del `.mcp.json` in radice, preservando gli altri server:

```json
{
  "mcpServers": {
    "openalex": {
      "type": "http",
      "url": "https://mcp.openalex.org/mcp"
    }
  }
}
```

In alternativa, dalla radice del progetto `claude mcp add --transport http --scope project openalex https://mcp.openalex.org/mcp` scrive la stessa configurazione condivisa. Se il progetto usa Codex, aggiungi a `.codex/config.toml` del progetto affidabile:

```toml
[mcp_servers.openalex]
url = "https://mcp.openalex.org/mcp"
```

Apri il client, completa il login OAuth nello store privato (`/mcp` in Claude Code; `codex mcp login openalex` in Codex se richiesto), poi verifica con `search_works` su una query breve e `get_work` su un DOI noto. Conserva nel topic la query OQL canonica restituita dal server, data e identificatori; usa `resolve_references` per controllare riferimenti, quindi `citation-tracker` per decidere lo stato della fonte. Se `academix` o `semantic-scholar-mcp` coprono già la ricerca del progetto, presenta sovrapposizione e budget prima di aggiungere un altro MCP. Non mettere token in `.mcp.json`, `.codex/config.toml` o nei documenti.

## PaperQA2: corpus locale

Verifica Python 3.11+ e crea un ambiente virtuale del progetto, per esempio con `python -m venv .venv`, aggiungendo `.venv/` al `.gitignore`. Installa la distribuzione PyPI con `python -m pip install "paper-qa>=5"` nell'ambiente attivato, poi annota la versione esatta con `python -m pip show paper-qa`; la CLI installata è `pqa`. Configura un modello LiteLLM compatibile e le sue credenziali nel livello privato del progetto oppure un modello locale. Definisci una cartella esplicita di documenti e avvia `pqa ask '<domanda>'` da quella cartella. Imposta `PQA_HOME` su una directory di cache privata e ignorata del progetto se l'indice non deve vivere in `~/.pqa/`; registra il percorso della cache e la versione del corpus. `pqa --help` e `pqa view` mostrano le opzioni effettive della versione installata. Per corpus grandi valuta le chiavi dei servizi di metadati indicate dal progetto upstream, conservandole fuori da git.

Il risultato di `pqa ask` alimenta `deep-paper-reading` e `senior-researcher` come indice di passaggi pertinenti: apri i documenti originali, verifica pagina e contesto, registra gli ID in `sources.md`, poi fai passare le citazioni bibliografiche da `citation-tracker`. Il tool non costituisce da solo una verifica indipendente dei claim o delle retrazioni.

## Feynman: ricerca e audit

Installa la CLI dalla [release ufficiale](https://github.com/Companion-Inc/feynman/releases) o dal pacchetto npm `@companion-ai/feynman` secondo le istruzioni della versione scelta e annota versione e metodo. Con npm, verifica Node.js almeno 22.22.0 e installa una versione scelta esplicitamente (`npm install -g @companion-ai/feynman@VERSIONE`); l'installer standalone include il runtime. Esegui `feynman setup` per configurare il provider nel suo store privato. Se la telemetria non è desiderata, imposta `FEYNMAN_TELEMETRY=off` nell'ambiente di esecuzione e verifica con `feynman status`. L'installazione delle sole skill Feynman non fornisce la CLI, il runtime o l'autenticazione.

Con `senior-researcher`, prova su un topic delimitato `feynman lit '<topic>'` o `feynman deepresearch '<topic>'`; usa `feynman audit '<paper>'` per confrontare paper e artefatti quando pertinente. Registra comando, versione, provider/modello, data, URL e output. Importa i risultati in `sources.md` come candidati e verifica paper, repository e passaggi originali prima della sintesi. Per un primo uso scegli un corpus pubblico e confronta un campione di claim con controllo manuale, come indicato in [RICOGNIZIONE-FEYNMAN.md](RICOGNIZIONE-FEYNMAN.md).

## Fonti operative

- [OpenAlex MCP ufficiale](https://github.com/ourresearch/openalex-mcp-server) e [configurazione MCP di Claude Code](https://code.claude.com/docs/en/mcp).
- [Configurazione di progetto Codex](https://learn.chatgpt.com/docs/config-file/config-basic) e [MCP in Codex](https://learn.chatgpt.com/docs/extend/mcp).
- [PaperQA2: installazione, CLI e indice](https://github.com/Future-House/paper-qa).
- [Feynman: installazione, setup e telemetria](https://github.com/Companion-Inc/feynman).
