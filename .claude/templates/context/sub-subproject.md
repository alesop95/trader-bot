---
generated-from-commit: <hash del commit di prima scrittura>
generated-from-branch: <branch>
generated-date: <YYYY-MM-DD>
covers-paths:
  - <nome-cartella-del-sottoprogetto>/
last-verified-commit: <hash dell'ultima verifica o aggiornamento>
stato: <non iniziato / in attesa di decisione / attivo / attivo, bloccato su <cosa> / concluso>
---

# Sottoprogetto: <nome leggibile>

Lo stato canonico di questo track è questo file, insieme alla riga che lo riguarda in `memory/index.md`. Se il sottoprogetto ha un handoff con una sezione di ripresa, quella resta come storico e questa scheda ha la precedenza.

Obiettivo: <una o due frasi>

## Dove siamo

<lo stato attuale in un paragrafo, senza ricopiare l'handoff: l'handoff è conoscenza, questa scheda è stato>

## Prossimo passo concreto

<una azione sola, eseguibile, con il suo criterio di successo se ne ha uno>

## Decisioni aperte

<cosa non è ancora deciso e perché non è decidibile adesso; se è una decisione formale, il rimando all'ADR>

## Evidenze e materiale locale

<dove vivono i file non versionati che questo track produce o consuma>

<!--
Istruzioni per l'uso, da cancellare all'istanziazione.

Il covers-paths si scrive come prefisso di cartella con lo slash finale, non come glob. Il confronto di sync-context è un pathspec git, dove la semantica dei wildcard non coincide con quella di .gitignore, e il prefisso di cartella è la forma più semplice e identica fra Windows e POSIX.

La scheda sta sotto le trenta righe. Se ti accorgi di stare copiando un paragrafo dall'handoff dentro la scheda, stai violando la divisione di competenza: l'handoff è procedura, troubleshooting, fonti e log; la scheda è dove siamo, cosa viene dopo, cosa è aperto.

Dopo aver creato la scheda vanno aggiornati quattro posti, e il quarto è quello che si dimentica. I primi tre sono la tabella di verifica in memory/index.md, il blocco del punto di ripresa nello stesso file, e la tabella dei track in context/current-work.md. Il quarto è il covers-paths delle schede trasversali che parlano del nuovo track, cioè STACK, dev-testing, design-and-security, roadmap e current-work: una scheda che descrive un'area senza dichiararla fra i percorsi coperti è un punto cieco permanente, perché sync-context non segnalerà mai un drift su un'area che nessuno dichiara di coprire, e la scheda resta indefinitamente verde mentre invecchia.
-->
