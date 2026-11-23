# Potenziamento

## Principio di separazione

La teoria di questo filone (capitoli, glossario, schemi) resta stabile e porta i rimandi al corso. Dati e strumenti cambiano nel tempo e vanno tenuti fuori dai capitoli: in una cartella di lavoro del caso, con data di raccolta e fonte indicate. Quando un dato esterno entra in un'analisi, la risposta deve dire da dove viene e quando è stato raccolto, distinto dai criteri del corso. Nessun numero esterno va scritto nei capitoli come se fosse teoria.

## Dati che rafforzano il filone

| Capitolo | Dati utili | Uso |
|---|---|---|
| 01 Megatrend | Serie statistiche pubbliche su demografia, consumi, adozione digitale, energia ed emissioni; rapporti di settore | Stimare tempi e intensità dei trend, costruire scenari alternativi |
| 01 Sostenibilità | Fattori di emissione, consumi energetici e idrici di prodotto, rating ESG | Rendere misurabili gli obiettivi ed evitare dichiarazioni vaghe |
| 02 Concorrenza | Quote di spesa per categoria di bisogno, dati di canale, prezzi rilevati | Mappare i concorrenti per funzione d'uso e seguire il declino dei canali |
| 02 Rischio | Bilanci depositati dei concorrenti e dei clienti, indicatori di credito | Riconoscere segnali finanziari di crisi |
| 03 Beneficio | Distinte di costo dei clienti, dati di scarto e fermo macchina | Calcolare il profitto generato al cliente e fissare il prezzo sul valore |
| 04 Relazione | Transazioni per cliente, date di acquisizione e abbandono, reclami, sondaggi di raccomandazione | Calcolare valore nel tempo, tasso di fedeltà, segmentazione |
| 05 Tecnologia | Inventario dei dati personali trattati, registri delle decisioni automatiche, studi di ciclo di vita | Controllo etico e di conformità |

## Tipi di strumenti

- Fogli di calcolo o notebook per i calcoli ripetibili del filone: valore del cliente nel tempo, tasso di fedeltà, punto di pareggio, valore attualizzato, matrice redditività per soddisfazione.
- Strumenti di raccolta di dati statistici pubblici, con citazione della serie e della data.
- Strumenti di visualizzazione con controlli sugli assi, per evitare le distorsioni descritte nel capitolo 02.
- Strumenti di mappatura del percorso del cliente e delle tele di modello di business.
- Strumenti di analisi testuale su recensioni e reclami, per leggere la soddisfazione oltre il punteggio numerico.
- Strumenti di valutazione del ciclo di vita e di calcolo delle emissioni.
- Strumenti di verifica dei bias e di anonimizzazione dei dati prima di qualunque analisi sui clienti.

## Regole d'uso

- I dati dei clienti si trattano in forma aggregata e minima, coerentemente con il capitolo 05.
- Ogni calcolo riporta le ipotesi (durata della relazione, tasso di sconto, costo orario) in modo che si possano cambiare.
- Le stime da strumenti esterni si presentano come scenari, mai come previsioni puntuali.
- Se un dato esterno contraddice un criterio del corso, si segnala il conflitto invece di scegliere in silenzio.

## Strumenti open source

Gli strumenti che seguono sono esterni al corso: servono ad applicare il filone, non ne fanno parte. Licenze, stato e indirizzi sono stati verificati il 2026-11-23; prima di adottarne uno si rilegge la licenza nel repository, perché può cambiare.

| Strumento | Licenza | A che cosa serve | URL |
|---|---|---|---|
| diagrams.net (draw.io) | Apache-2.0 | Disegnare il canvas del modello di business, mappe PESTEL e SWOT, mappe del flusso del valore, con modelli riutilizzabili | https://github.com/jgraph/drawio |
| Excalidraw | MIT | Lavagna collaborativa per i workshop su canvas, SWOT e PESTEL | https://github.com/excalidraw/excalidraw |
| Prophet | MIT | Previsione di serie storiche con stagionalità, per lo scenario base di domanda e ricavi da cui far partire le varianti | https://github.com/meta/prophet |
| PyCIB | AGPL-3.0 | Analisi di impatto incrociato per costruire scenari coerenti fra loro; progetto di nicchia, da usare per studio | https://github.com/ag-ross/PyCIB |

Avvertenze: non esiste oggi un software open source maturo dedicato al canvas del modello di business, e la lavagna o il diagramma restano la via pratica. Il canvas del modello di business è distribuito con licenza Creative Commons, mentre quello della proposta di valore è protetto dal suo editore: si usa citandolo, senza ridistribuirne il modello grafico.
