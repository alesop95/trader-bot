---
name: security-review
description: Audit di sicurezza difensivo su auth, validazione input, protezione dati, dipendenze e configurazione. Attiva su richieste come "security review", "controllo sicurezza", "audit". Nota: nel progetto mette in ombra l'eventuale skill nativa omonima di Claude Code.
---

# Security review (skill di progetto)

Esegui un audit di sicurezza difensivo sul codice indicato. Questa e' la variante di progetto, versionata col repository: se la CLI offre la skill nativa `/security-review` e non serve un processo personalizzato, quella resta preferibile; per l'audit in contesto isolato esiste anche l'agente `security-auditor` del pacchetto `subagent-template` (vedi README del pacchetto `dev-skills`).

## Checklist

1. Autenticazione e autorizzazione: sessioni, token e scadenze; controllo dei permessi ripetuto per ogni endpoint e ogni operazione sulle risorse, lato server.
2. Validazione degli input: sanitizzazione e whitelist su tutto cio' che arriva dall'esterno; protezione da injection SQL, command e path traversal, e da XSS[^1].
3. Protezione dei dati: nessun secret in chiaro, cifratura a riposo e in transito dove pertinente, log senza dati sensibili, messaggi di errore senza dettagli interni.
4. Dipendenze: vulnerabilita' note (`npm audit`, `pip-audit` o equivalente), versioni obsolete o non pinnate.
5. Configurazione: CORS[^2], header di sicurezza, default pericolosi, file esposti per errore.

## Output e vincoli

Report per severita' con descrizione, impatto, file e riga, remediation proposta. Nessuna modifica automatica al codice. Solo identificazione e fix difensivi: non generare exploit funzionanti ne' tecniche offensive. Nessuna operazione git.

[^1]: *XSS*, Cross-Site Scripting - iniezione di script eseguiti nel browser di un altro utente attraverso input non sanificato.
[^2]: *CORS*, Cross-Origin Resource Sharing - politica del browser che governa quali origini possono chiamare le API; una configurazione troppo permissiva espone le API a siti terzi.
