# Anonimizzazione: i casi osservati

> Norma del pacchetto `anonymization`. Non si carica all'avvio di una sessione e non serve per applicare la regola: raccoglie i casi, con le misure e le date, che giustificano le prescrizioni di `rules/anonymization.md`. La divisione esiste perché quella regola è sempre attiva in ogni progetto che la istanzia e concorre al budget degli instruction file, mentre un caso osservato si legge una volta sola, quando si vuole capire perché una prescrizione è scritta così. Si istanzia in `.claude/norme/anonymization.md`.

## La visibilità si stabilisce prima della prima riga

Il 2026-10-27, in un progetto istanziato: un percorso aziendale completo è finito come valore predefinito di un parametro in uno script e da lì in un repository pubblico. L'errore non è stato scrivere quel percorso, comodo e innocuo in locale, ma non aver mai chiesto dove sarebbe finito.

## Il perimetro non è l'insieme dei file tracciati

Il difetto che ha fissato la definizione è controintuitivo. Definire il perimetro come l'insieme dei file tracciati sembra naturale, e lascia fuori il file nuovo, scritto e non ancora aggiunto all'indice, proprio nel momento in cui serve guardarlo. Nel progetto di origine tre file nuovi sono passati puliti per fortuna e non per verifica, e il difetto è stato scoperto per caso qualche giorno dopo.

## Perché i riscontri del layer privato non bloccano

Nel progetto di origine la misura dice 10.844 riscontri nel layer privato contro zero bloccanti nel perimetro pubblico, e fra i file più densi c'è proprio la mappa dei segnaposto, che per definizione contiene tutti i valori reali. È la ragione per cui quei riscontri si elencano a parte invece di fermare il commit.

## La convenzione esce dove qualcuno la spiega

Il 2026-10-26, in un progetto istanziato: due righe del registro di lavoro di un *secondo* repository pubblico dichiaravano la corrispondenza fra la classe di indirizzi reali di una rete e la classe di segnaposto che la sostituiva, nominando il repository dove la mappatura viveva. Quelle due righe rendevano reversibili quattrocentosessantuno occorrenze nel repository protetto, mentre il controllo restituiva zero riscontri bloccanti, correttamente, perché ciò che era uscito non era un valore ma la regola.

## Un verde misura i pattern, non il repository

Nel progetto di origine, dopo un controllo verde, una lettura integrale per categorie chiuse ha trovato circa millecento riscontri: clienti, identificativi amministrativi, nomi di battesimo, indirizzi scritti con separatori diversi dal punto e documenti interi di altri progetti, nessuno dei quali aveva un pattern. Sulle parole brevi, il 2026-10-28 la voce `EMOVI` dell'elenco dei nomi propri ha prodotto due riscontri bloccanti dentro la parola inglese «removing» del testo di una skill, fermando un commit senza che niente fosse uscito.
