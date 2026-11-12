# Sicurezza e permessi: i casi che non si presentano a ogni sessione

> Norma di riferimento della regola `.claude/rules/security-permissions.md`. Non si carica all'avvio di una sessione e non serve per applicare la regola: si carica quando si sta per usare `--dangerously-skip-permissions`, quando si valuta un contenitore o una macchina virtuale per una sessione autonoma, e quando si sta per avviare un Agent Team. Il contenuto è stato spostato qui il 10/11/2026, invariato, perché la regola sempre attiva aveva portato le istruzioni di un progetto istanziato oltre la propria soglia di guardia (L-025 di un progetto istanziato): una regola che vale solo in certe situazioni paga il proprio costo a ogni sessione di ogni progetto, e qui non lo paga.

## --dangerously-skip-permissions: quando e accettabile

Il consenso unanime di documentazione ufficiale e community e chiaro: questo flag non va mai usato su una macchina reale non containerizzata. In un container o VM completamente isolati e accettabile, a condizione che il container giri come utente non privilegiato (il flag si rifiuta di girare come root su Linux e macOS).

Tre comportamenti del flag che sorprendono spesso. Le chiamate ai tool MCP[^2] si auto-approvano insieme a tutto il resto: più server MCP con permessi di scrittura hai connessi, più ampio e il raggio d'azione in caso di prompt injection. Le regole `deny` esplicite nel `settings.json` continuano a bloccare anche in bypass. `--disallowedTools` funziona correttamente in bypass, mentre `--allowedTools` può essere ignorato: se si vuole limitare i tool disponibili in un container autonomo, usare il primo.

Per le sessioni autonome su macchina reale la modalità consigliata e *auto* oppure *dontAsk* con una lista `allow` ben costruita, non il bypass.

## Agent Teams sperimentali: avvertenza sui permessi

Gli Agent Teams sono una feature sperimentale (disabilitata di default, si attiva con la variabile di ambiente `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`) che permette a più agenti di lavorare in parallelo con comunicazione diretta tra pari, una task list condivisa e file locking. La caratteristica che richiede attenzione prima del lancio: i permessi del lead si propagano a tutti i teammate nel momento dello spawn. Se il lead parte con `bypassPermissions`, tutti i teammate lo ereditano. La postura dei permessi va quindi pianificata sul lead, con cura, prima di avviare il team, non corretta a posteriori.

I team non supervisionati per più di 10-15 minuti tendono a bloccarsi su prompt di permesso, a segnare task come completati prematuramente o a perdere lo scope del lavoro originale. Un check-in periodico sulla task list condivisa non è opzionale per i task lunghi.


[^1]: *MCP*, Model Context Protocol - standard che permette a un client AI di parlare con sistemi esterni (GitHub, database, browser) attraverso un'interfaccia comune; ogni server MCP espone tool, risorse e prompt che diventano disponibili all'agente.
