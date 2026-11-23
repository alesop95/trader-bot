# Schemi decisionali

## Regole di scelta di breve periodo

Ipotesi comune: capacità e struttura dei costi fissi date, orizzonte entro l'anno. I dettagli e gli esempi numerici sono nel capitolo 05.

| Decisione | Dati che servono | Regola | Costi da escludere | Errore tipico | Fonti |
|---|---|---|---|---|---|
| Ordine speciale | Prezzo e quantità dell'ordine, costi variabili unitari, provvigioni sul totale, fissi specifici dell'ordine, capacità libera | Accettare se ricavo incrementale - costi variabili - fissi specifici > 0; con capacità satura sottrarre anche il margine delle vendite perse (integrazione della skill) | Fissi comuni non eliminabili | Provvigione calcolata su un pezzo invece che sul totale; dimenticare il noleggio o l'attrezzaggio dedicato | [L13, L14, M043, M044] |
| Make or buy | Prezzo del fornitore e costi accessori, costi variabili interni, fissi eliminabili, uso alternativo della capacità | Produrre se costi variabili interni + fissi eliminabili < costo d'acquisto; aggiungere a favore dell'acquisto il margine ottenibile con la capacità liberata (integrazione della skill) | Fissi indifferenti, quote di costi comuni da full costing | Confrontare il prezzo esterno con il costo pieno interno | [L13, L14, M037, M042, M043] |
| Eliminazione di una linea | Margine di contribuzione della linea, fissi eliminabili, effetti sulle vendite di altre linee | Eliminare se margine di contribuzione < fissi eliminabili, cioè se il margine di secondo livello è negativo; tenere se positivo anche quando a costo pieno la linea è in perdita | Fissi comuni ripartiti | Decidere sul risultato a costo pieno; ignorare che i fissi comuni restano e si spostano sulle altre linee | [L12, L13, M038, M041, M043] |
| Risorsa scarsa | Margine unitario di ogni prodotto, consumo unitario della risorsa vincolante, domanda massima | Ordinare per margine per unità di risorsa scarsa e saturare la risorsa dal primo prodotto, nei limiti della domanda | Fissi (non cambiano con il mix) | Ordinare per margine unitario o per prezzo | [L13, M042, M044] |
| Sconto per recuperare volumi | Prezzo, costo variabile, volume attuale, sconto ipotizzato | Volume necessario = margine totale attuale / nuovo margine unitario; procedere solo se è realistico (integrazione della skill sulla formula) | Fissi | Scontare senza calcolare il volume di compensazione e senza guardare i rincari delle materie | [L12] |
| Acquisto in lotto con sconto | Fabbisogno, sconto, costo di tenere scorta, tensione di cassa | Confrontare guadagno economico e cassa immobilizzata; decidere in base alla liquidità disponibile | Nessuno | Guardare solo il risparmio sul conto economico | [M037, M042, M044] |

## Formule di riferimento

| Grandezza | Formula | Capitolo |
|---|---|---|
| Margine di contribuzione unitario | prezzo - costo variabile unitario | 03 |
| Margine di contribuzione % | margine totale / ricavi × 100 | 03 |
| Punto di pareggio in quantità | costi fissi / margine unitario | 03 |
| Punto di pareggio in fatturato | costi fissi / margine % (integrazione della skill) | 03 |
| Margine di sicurezza | (vendite - vendite di pareggio) / vendite (integrazione della skill) | 03 |
| Leva operativa | margine di contribuzione / risultato operativo (integrazione della skill) | 03 |
| Varianza prezzo materiali | (prezzo effettivo - standard) × quantità effettiva | 04 |
| Varianza quantità materiali | (quantità effettiva - standard ammessa) × prezzo standard | 04 |
| Effetto prezzo vendite | Σ (prezzo effettivo - budget) × quantità effettiva | 04 |
| Effetto volume vendite | (quantità totale effettiva - budget) × prezzo medio di budget | 04 |
| Effetto mix vendite | Σ (quantità effettiva - quantità totale effettiva × quota di budget) × prezzo di budget | 04 |
| Test acido | (liquidità immediate + differite) / passivo corrente | 02 |
| Liquidità corrente | attivo corrente / passivo corrente (integrazione della skill) | 02 |
| ROE | utile netto / patrimonio netto | 02 |
| ROI | risultato operativo / capitale investito = ROS × rotazione | 02 |
| ROS | risultato operativo / ricavi | 02 |
| Rotazione capitale investito | ricavi / capitale investito | 02 |
| Costo del debito | oneri finanziari / debiti onerosi | 02 |
| DSO | crediti verso clienti / (ricavi × (1 + IVA)) × 365 | 02 |
| DPO | debiti verso fornitori / (acquisti × (1 + IVA)) × 365 | 02 |
| Giorni di magazzino | rimanenze / costo del venduto × 365 | 02 |
| Ciclo di cassa | giorni di magazzino + DSO - DPO (integrazione della skill) | 06 |
| VAN | -investimento + Σ flusso_t / (1 + r)^t | 06 |

## Lista di controllo prima di una decisione di breve

- Ho separato costi fissi e variabili con un criterio esplicito? [L11]
- Ho tolto i costi indifferenti e i fissi non eliminabili? [L13, M043]
- Le provvigioni e gli altri costi a percentuale sono calcolati sul totale? [L14]
- La capacità è libera o satura? Se satura, quale margine perdo? [L13]
- C'è una risorsa che vincola? Ho ordinato per margine per unità di quella risorsa? [L13]
- Che effetto ha la scelta sulla cassa nei prossimi mesi? [L12, M037]
- Che effetto ha nel lungo periodo su clienti, listino, competenze? [M042]

## Lista di controllo per la lettura di un bilancio

- Ho almeno tre esercizi? [L09]
- Stato patrimoniale riclassificato con confine a dodici mesi? [L10]
- Conto economico gestionale con margine di contribuzione, EBIT, oneri finanziari separati? [L09, L10]
- Patrimonio netto in calo nonostante fatturato in crescita? Perdite o distribuzioni? [L09]
- Crediti e scorte crescono più dei ricavi? [L10, L12]
- Test acido sotto 1? [L10]
- ROI sopra o sotto il costo del debito? [L10]

## Domande da porsi davanti a uno scostamento

- Lo scarto è di volume, di prezzo o di mix? [L12, M039]
- Nei costi: prezzo pagato o quantità impiegata? [M037]
- La causa è interna (efficienza, processo) o esterna (inflazione, contratti)? [L13]
- Se è strutturale, lo standard va aggiornato? [L13]
- Quale azione ne segue, e chi ne è responsabile? [L12, M050]

## Errori tipici, in sintesi

- Utile scambiato per cassa [L09, L14].
- Ammortamenti o fissi dentro il margine di contribuzione [L09, M038].
- Decisioni di chiusura prese sul costo pieno [L13].
- Varianze lette in aggregato senza scomposizione [L12].
- Indici letti in valore assoluto o su un solo anno [L10].
- IVA dimenticata nei giorni di incasso e pagamento [L10].
- KPI senza legame con gli obiettivi [L14, M124].
- Previsioni non aggiornate quando il contesto cambia [L11].
