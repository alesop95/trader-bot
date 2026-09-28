# Protocollo R&D per benchmark e test

Questo riferimento distilla il metodo della guida operativa e degli audit statistici del benchmark IntraLino, esaminati durante la costruzione del pacchetto. I numeri e i dati del progetto di origine non sono trasferibili ad altri workload: si riusa il disegno sperimentale, non i risultati.

## Prima della raccolta

Formula ogni claim come contrasto misurabile. Dichiara popolazione dei task, condizioni e baseline, unità indipendente, metrica primaria, differenza minima utile o precisione obiettivo, campione, repliche, randomizzazione o bilanciamento dell'ordine, regole su errori e valori mancanti, trattamento degli outlier e confronti secondari. Congela il protocollo con data/versione prima di guardare i risultati finali. Usa un pilota per stimare variabilità e dimensionare il test; non contare repliche dello stesso task come nuovi task indipendenti. Se non puoi stimare la precisione necessaria, riduci l'ambito del claim.

Versiona dataset e ground truth con hash, provenienza, criteri di inclusione, eventuali diritti e data di validità. Se il task comprende retrieval o risposte generate, registra tutti i passaggi gold equivalenti, il contesto esatto visto dal modello, l'ordine dei passaggi e i casi senza risposta. Separa tuning, pilota e test finale per documento o tema quando varianti della stessa fonte potrebbero trapelare fra insiemi.

## Durante la raccolta

Conserva record grezzi immutabili e un manifest di run con versione del codice, modello e digest, parametri, hardware, carico, timestamp, seed, prompt, dataset e hash. Registra latenza end-to-end e componenti, throughput, errori e risorse pertinenti; per confronti energetici misura anche idle, carico e unità come Wh/richiesta. Un cambiamento simultaneo di modello, hardware o corpus impedisce di attribuire l'effetto a una sola causa. Misura baseline semplici e condizioni oracle quando aiutano a isolare retrieval, generazione e sistema.

Per giudizi umani, nascondi ai valutatori la condizione e il gold, randomizza l'ordine, conserva i giudizi individuali e documenta istruzioni, pilota, accordo e adjudicazione. Se un valutatore giudica più risposte della stessa domanda, il denominatore indipendente non diventa il numero di giudizi. Distingui fedeltà al contesto ricevuto da correttezza rispetto alla verità esterna.

## Analisi e comunicazione

Analizza differenze appaiate quando gli stessi task attraversano le condizioni. Ricampiona o modella l'unità indipendente e mantieni insieme le osservazioni raggruppate per task, valutatore o sessione secondo il disegno. Riporta n task, n run, n giudizi, missingness, distribuzioni, stime e intervalli; correggi i confronti secondari con una procedura dichiarata. Un risultato «non significativo» non dimostra equivalenza: per quella serve un margine dichiarato e un disegno adeguato. Mostra i limiti di generalizzazione quando il test è piccolo o sintetico.

Una figura o un claim quantitativo entra nel brief come risultato sostenuto soltanto se sono disponibili protocollo datato, dataset e gold versionati, record grezzi con hash, metrica e denominatore, ambiente, script riproducibile, incertezza e analisi di errori/mancanti. In mancanza di uno di questi elementi, etichettalo come osservazione esplorativa con il limite preciso. Per prestazioni di un sistema, il costo totale richiede un workload e un periodo dichiarati; token/s da soli non provano convenienza.
