---
name: mcp-tool-scaffold
description: Scaffolding di un nuovo tool per un server MCP in TypeScript (MCP SDK). Attiva su richieste come "aggiungi un tool MCP", "nuovo tool", "scaffold mcp".
---

# MCP tool scaffold (TypeScript)

Scaffoldi un nuovo tool per un server MCP esistente, con la disciplina del profilo di stack `ts-mcp` se istanziato nel progetto.

## Processo

1. Definisci il contratto prima del codice: nome in snake_case, description chiara e orientata all'uso, schema di input (zod o JSON Schema), forma dell'output. Mostra il contratto e chiedi conferma prima di generare.
2. Genera lo scheletro coerente con il pattern del server esistente: registrazione del tool, validazione dell'input prima dell'esecuzione, handler con gestione errori completa, risposta tipizzata. Nessuna eccezione non gestita deve poter uscire verso il client.
3. Scrivi le description per il modello che le legge: la description del tool e dei parametri e' cio' che un LLM usa per decidere se e come invocarlo, quindi dichiara cosa fa, quando usarlo e quali effetti collaterali ha, non solo cosa significa tecnicamente.
4. Genera i tre test minimi: input valido, input non valido, errore a runtime.

## Best practice

Errori strutturati e informativi, mai stack trace grezzi verso il client. Idempotenza dove possibile, ed effetti collaterali sempre dichiarati nella description. Il nome e lo schema di un tool pubblicato sono un contratto: cambiarli e' una breaking change da registrare in `memory/decisions.md`.
