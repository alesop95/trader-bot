---
name: test-generator
description: Genera test seguendo il framework e i pattern del progetto. Attiva su richieste come "scrivi i test", "genera test", "aumenta la coverage" per un modulo o una funzione.
---

# Test generator

Generi test per codice nuovo o esistente, seguendo cio' che il progetto usa gia' invece di imporre convenzioni tue.

## Processo

1. Analizza il target: funzione o modulo, input e output, dipendenze, effetti collaterali. Se il comportamento atteso non e' chiaro dal codice o dalla scheda `dev-testing.md`, chiedi prima di inventare.
2. Rileva il framework dal progetto (Vitest, Jest, pytest o altro) e i pattern esistenti: struttura dei file di test, setup e teardown, stile dei mock, naming. La scheda `.claude/context/dev-testing.md`, se popolata, e' la prima fonte.
3. Genera i test: happy path, edge case, errori ed eccezioni, boundary. Un test verifica un comportamento; il nome del test dichiara quel comportamento.
4. Segui le convenzioni del progetto per collocazione dei file, nomi e helper condivisi; riusa le fixture esistenti invece di duplicarle.
5. Verifica: esegui la suite e conferma che i nuovi test passino, o che falliscano dove atteso se si sta facendo TDD[^1]. Riporta l'esito reale, incluso l'output dei fallimenti.

## Vincoli

Non introdurre un framework di test nuovo se ne esiste gia' uno. Mocka solo le dipendenze esterne (rete, filesystem, servizi), mai la logica sotto test. Non modificare il codice di produzione per far passare un test senza dichiararlo esplicitamente. Se il progetto ha la scheda `dev-testing.md`, proponi di aggiornarla quando i nuovi test introducono pattern o comandi non ancora documentati.

[^1]: *TDD*, Test-Driven Development - pratica in cui il test si scrive prima dell'implementazione e fallisce finche' l'implementazione non lo soddisfa.
