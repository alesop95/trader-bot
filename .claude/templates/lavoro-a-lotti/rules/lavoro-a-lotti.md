# Lavoro a lotti su un corpus grande

> Regola modulare del pacchetto `lavoro-a-lotti`. Si carica quando il progetto ha un lavoro che tocca molti elementi. Dichiara il proprio presidio, come prescrive la sezione 17 del sistema di progetto.

## Quando si applica

Un lavoro ha la forma di **mappatura più aggregazione** quando esiste un insieme di elementi indipendenti su cui va svolta la stessa operazione, e poi un passaggio che ne mette insieme gli esiti. Parsing di molti file, studio preparatorio a un refactoring, ingestione di un corpus.

Se il prodotto fra numero di elementi e costo di uno sta comodamente in una finestra di sessione, **questa regola non si applica**: si fa il lavoro e basta. Il registro su dieci elementi è burocrazia.

## Le quattro leve, in ordine

**Togliere elementi** è la prima e vale più di tutte le altre insieme, perché cambia l'ordine di grandezza invece della costante. Estrazione, normalizzazione, filtro e deduplicazione sono deterministici e non devono vedere un modello. Solo ciò che richiede giudizio passa a un agente.

**Rendere il lavoro riprendibile** viene subito dopo. Un lavoro che riparte da capo quando la finestra finisce non si conclude mai.

**Instradare su serbatoi indipendenti**, dove esistono più flotte di agenti con quote separate: la mappatura ripetitiva alla flotta secondaria, l'aggregazione e le decisioni alla principale.

**Parallelizzare** è l'ultima, e va capita per quello che è: **non riduce i token, riduce il tempo**. La quota si consuma proporzionalmente alla concorrenza, quindi il parallelismo avvicina il limite invece di allontanarlo. Si usa quando serve il risultato prima, non quando si teme di esaurire la finestra.

## Il contratto

Ogni elemento ha una riga nel registro, e **ogni elemento concluso lascia un artefatto**. Un esito che vive solo nella conversazione resta irrecuperabile alla chiusura della sessione e invisibile al presidio, quindi non conta come concluso.

La flotta che mappa non conosce l'aggregazione e scrive solo il proprio artefatto. La flotta che aggrega **non rilegge gli elementi grezzi**: legge gli artefatti. È il firewall di contesto applicato fra processi invece che dentro uno.

## Il presidio

`tools/registro.py stato <registro>` verifica **gli artefatti, non gli stati dichiarati**, e segnala le discordanze. Si esegue prima di ogni ripresa e dopo ogni lotto.

La ragione è la sezione 19 del sistema: lo stato lo scrive l'agente che deve superare il controllo, quindi un controllo che lo consulta non controlla nulla. Il presidio consulta il disco.

**Che cosa non copre**, dichiarato perché crederlo più ampio è peggio che non averlo: distingue la presenza dall'assenza, non il buono dal mediocre. Un artefatto valido non è un artefatto corretto. La qualità resta da guardare a mano, su un campione.

**Le discordanze non si sistemano in silenzio.** Un elemento dichiarato concluso senza artefatto prova che il mandato non ha funzionato, e va capito prima di rilanciare, altrimenti si ripresenta identico sul lotto successivo.

## Prima di cominciare, tre domande

Quanti elementi, e quanto costa uno **misurato** e non assunto.

Quanti richiedono davvero giudizio: se la risposta è "tutti", quasi sempre la parte deterministica non è stata cercata.

Esiste un artefatto per elemento: se no, il lavoro non è verificabile, e va ridisegnato prima di essere avviato.
