# Schema della LLM Wiki

> Costituzione di questa wiki. Definisce i tipi di pagina, come si collegano, quando si aggiornano
> e come si gestiscono le contraddizioni. La skill `wiki-digest` segue questo schema a ogni
> ingestione. Questo file e' la fonte di verita del comportamento della wiki.

## Principio

La wiki non e' un archivio di documenti da cercare, ma una knowledge base gia sintetizzata e
collegata. Le fonti grezze stanno in `sources/`, immutabili; le pagine in `wiki/` sono il prodotto
compilato. La manutenzione, cioe sintetizzare, collegare e rilevare contraddizioni, e' delegata
all'LLM tramite `wiki-digest`, non fatta a mano.

## Tipi di pagina

`wiki/concepts/<concetto>.md` per i concetti e i modelli mentali. `wiki/entities/<entita>.md` per
persone, prodotti, aziende, tecnologie. `wiki/sources/<fonte>.md` per il riassunto di una singola
fonte ingerita. Ogni pagina ha un titolo, un sommario denso, i collegamenti alle pagine correlate e
i riferimenti alle fonti da cui deriva.

## Collegamenti

Le pagine si collegano tra loro con link markdown relativi, per esempio
`[replication](../concepts/replication.md)`. Ogni concetto cita le fonti che lo trattano e le altre
pagine con cui e' in relazione. Il valore della wiki sta nella densita dei collegamenti: una pagina
isolata vale poco.

## Quando aggiornare

A ogni ingestione di una nuova fonte, `wiki-digest` aggiorna le pagine esistenti toccate dal nuovo
contenuto, crea le pagine nuove per i concetti o le entita non ancora presenti, e aggiorna i
collegamenti reciproci. Non si rigenera la wiki da zero: si fanno modifiche mirate.

## Contraddizioni

Quando una nuova fonte contraddice una pagina esistente, non si sovrascrive in silenzio: si
registra la divergenza nella pagina, citando entrambe le fonti e la data, e si marca il punto come
da risolvere. Una conoscenza superata si aggiorna dichiarando cosa la supera, non cancellandola
senza traccia.

## Stile

Sommari densi, voce da praticante ("usa X quando Y", non "la fonte dice X"), mai testo grezzo
copiato: sempre sintesi ed estrazione di segnale. Le pagine si scrivono per essere lette sia da un
LLM sia da un umano, dense e senza ridondanza, coerentemente con la regola di stile del sistema.

## Regola sulle fonti

`sources/` e' append-only: una fonte ingerita non si modifica e non si cancella. Se una fonte va
corretta, si aggiunge una nuova versione e lo si annota nel `log.md`. Questo tiene la wiki
ricostruibile dalle fonti.
