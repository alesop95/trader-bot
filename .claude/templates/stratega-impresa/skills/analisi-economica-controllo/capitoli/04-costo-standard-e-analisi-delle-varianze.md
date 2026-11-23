# 04. Costo standard e analisi delle varianze

Il controllo di gestione confronta ciò che doveva succedere con ciò che è successo e spiega la differenza. Il corso lo fa su due fronti: le varianze industriali, che confrontano costo standard e costo effettivo di produzione, e le varianze commerciali, che scompongono lo scarto dei ricavi dal budget in volume, prezzo e mix [L11, L12, M037, M039]. Questo capitolo dà le formule, un esempio per ciascuna e le regole di lettura.

## Budget, previsioni aggiornate, scostamenti

Il budget traduce gli obiettivi strategici in un piano annuale delle grandezze economiche e delle risorse, e serve da metro per il monitoraggio [L11]. Il corso inserisce il budget in una sequenza a tre livelli: piano strategico a tre-cinque anni, budget annuale con obiettivi operativi, previsioni trimestrali o mensili che si aggiornano con le condizioni [M037]. Il forecast è la previsione rivista in corso d'anno; un modello usato in aula è il "6+6", in cui i dati dei primi sei mesi alimentano la stima dei sei successivi [L13].

Due regole ricorrono. Il budget non è la strategia, e confonderli porta a ragionare solo sull'anno [L11]. Le previsioni vanno aggiornate quando cambia il contesto (crisi energetica, inflazione, tensioni internazionali), altrimenti si lavora su obiettivi superati [L11]. L'analisi di scostamento è lo strumento che collega le due cose: confronta reale e previsto, individua le cause, propone correzioni [L13, M123].

Il corso aggiunge una nota sul clima: l'analisi delle varianze serve a capire le cause, non a cercare colpevoli [L12]. Attribuire responsabilità individuali prima di aver scomposto il dato è un errore tipico [L12].

## Il costo standard

Il costo standard è il costo unitario che un prodotto dovrebbe avere in condizioni operative normali; è sempre una stima a priori delle risorse da impiegare [M044, M037]. Si usa per prodotti ripetitivi e si fissa partendo da analisi tecniche e da scelte strategiche (materiali, processi, volumi attesi), non copiando la media storica [L13].

Il corso insiste su questo punto: uno standard costruito su dati storici presi senza analisi genera varianze che nessuno sa governare [L13]. Lo standard va aggiornato quando cambiano processi o materiali [L13]. Va invece valutato con attenzione quando la varianza nasce da fattori esterni come l'inflazione delle materie prime: si rivede lo standard e si lavora fra reparti per recuperare il costo, senza fingere che il problema sia di efficienza interna [L13].

Per ogni prodotto lo standard si costruisce per componenti [M037]:

| Componente | Standard di quantità | Standard di prezzo |
|---|---|---|
| Materiali | kg, pezzi per unità | euro per kg o per pezzo |
| Manodopera diretta | ore per unità | tariffa oraria |
| Costi generali di produzione | base di ripartizione per unità (ore macchina, ore lavoro) | coefficiente per unità di base |

## Varianze industriali

La varianza totale di un fattore è la differenza tra costo effettivo e costo standard ammesso per la produzione effettiva. Si scompone in una parte dovuta al prezzo e una dovuta alla quantità [M037, M044]. Convenzione usata qui: valore positivo = sfavorevole, negativo = favorevole (la convenzione va sempre dichiarata, perché i manuali la usano in entrambi i sensi).

Il corso chiede di analizzare prezzo e quantità separatamente, perché rimandano a responsabili diversi: il prezzo agli acquisti, la quantità alla produzione [M037]. Un costo effettivo inferiore allo standard è una varianza favorevole [M037].

### Materiali

Formule (formulazione standard, integrazione della skill per i simboli):

- Varianza prezzo = (prezzo effettivo - prezzo standard) × quantità effettiva impiegata.
- Varianza quantità (o di impiego) = (quantità effettiva - quantità standard per la produzione effettiva) × prezzo standard.
- Varianza totale = costo effettivo - costo standard = varianza prezzo + varianza quantità.
- Quantità standard ammessa = produzione effettiva × consumo standard per unità: lo standard si ricalcola sui volumi reali, non su quelli di budget.

Esempio illustrativo. Standard: 2 kg per unità a 5 euro al kg, cioè 10 euro per unità. Produzione effettiva 1.000 unità, impiegati 2.100 kg pagati 4,80 euro al kg.

- Costo effettivo: 2.100 × 4,80 = 10.080.
- Costo standard ammesso: 1.000 × 2 × 5 = 10.000.
- Varianza totale: +80 (sfavorevole).
- Varianza prezzo: (4,80 - 5,00) × 2.100 = -420 (favorevole).
- Varianza quantità: (2.100 - 2.000) × 5 = +500 (sfavorevole).

Lettura: gli acquisti hanno spuntato un prezzo migliore, ma la produzione ha consumato il 5% di materiale in più. Prima domanda da porsi: il materiale meno caro è di qualità inferiore e ha causato più scarti? Se sì, il risparmio sul prezzo è illusorio. Il corso porta il caso opposto: un'azienda che sostituisce un materiale costoso con uno equivalente più economico, senza perdite di funzione, ottiene una varianza favorevole strutturale e la incorpora nel nuovo standard [L13].

### Manodopera diretta

Formule (integrazione della skill):

- Varianza tariffa = (tariffa effettiva - tariffa standard) × ore effettive.
- Varianza efficienza = (ore effettive - ore standard per la produzione effettiva) × tariffa standard.

Esempio illustrativo. Standard: 0,5 ore per unità a 20 euro l'ora. Produzione 1.000 unità, ore effettive 540 a 21 euro.

- Costo effettivo: 540 × 21 = 11.340.
- Costo standard ammesso: 500 × 20 = 10.000.
- Varianza tariffa: (21 - 20) × 540 = +540.
- Varianza efficienza: (540 - 500) × 20 = +800.
- Totale: +1.340, tutto sfavorevole.

Il corso segnala come errore sottovalutare le varianze di efficienza [M037]: sono quelle che rivelano problemi di processo, fermi macchina, formazione insufficiente.

### Costi generali di produzione

Per i costi generali la scomposizione classica separa una varianza di spesa (si è speso più o meno del previsto) da una di volume o di efficienza (la base di ripartizione è stata usata più o meno del previsto). Il corso cita il tema nell'esempio di un produttore di gadget che analizza le varianze di ogni fattore produttivo, costi generali compresi [M037], ma le schede non danno formule: la skill le tratta come integrazione e consiglia di applicarle solo dove i costi generali sono rilevanti.

### Procedura mensile

La sequenza delle lezioni [L13, M123]:

1. Definire il costo standard per i prodotti ripetitivi.
2. Rilevare ogni mese i costi effettivi.
3. Calcolare le varianze per fattore e per causa.
4. Cercare la causa operativa (materiali, efficienza, tariffe, prezzi esterni).
5. Agire, e se la causa è strutturale aggiornare lo standard.

## Varianze commerciali: volume, prezzo, mix

Quando i ricavi o i margini si discostano dal budget, il corso scompone lo scarto in tre effetti [L12, M037, M039]:

- Effetto volume: si è venduto più o meno in quantità totale.
- Effetto mix: è cambiata la composizione delle vendite fra prodotti con prezzi o margini diversi.
- Effetto prezzo: si è venduto a prezzi diversi da quelli previsti.

Formule (formulazione standard, integrazione della skill per la notazione), con Q quantità, P prezzo, b budget, e effettivo, i il singolo prodotto:

- Effetto prezzo = Σ (Pe,i - Pb,i) × Qe,i.
- Effetto volume = (Q totale effettiva - Q totale budget) × prezzo medio di budget al mix di budget.
- Effetto mix = Σ (Qe,i - Q totale effettiva × quota di budget del prodotto i) × Pb,i.
- La somma dei tre effetti è lo scarto totale dei ricavi.

Esempio illustrativo con due prodotti.

| | Q budget | P budget | Q effettiva | P effettivo |
|---|---|---|---|---|
| Prodotto A | 600 | 100 | 700 | 95 |
| Prodotto B | 400 | 150 | 200 | 150 |
| Totale | 1.000 | | 900 | |

- Ricavi di budget: 60.000 + 60.000 = 120.000. Ricavi effettivi: 66.500 + 30.000 = 96.500. Scarto totale: -23.500.
- Prezzo medio di budget: 120.000 / 1.000 = 120.
- Effetto prezzo: (95 - 100) × 700 = -3.500.
- Effetto volume: (900 - 1.000) × 120 = -12.000.
- Effetto mix: A (700 - 540) × 100 = +16.000; B (200 - 360) × 150 = -24.000; totale -8.000.
- Verifica: -3.500 - 12.000 - 8.000 = -23.500.

Lettura: metà dello scarto è volume, un terzo è mix (si è venduto di più il prodotto meno caro), il resto è sconto su A. Le azioni sono diverse per ciascun effetto: sul volume si lavora con la rete commerciale, sul mix con incentivi orientati ai prodotti a margine più alto, sul prezzo con la politica di sconto.

Nota (integrazione della skill): la stessa scomposizione si può fare sul margine di contribuzione invece che sui ricavi, sostituendo il prezzo con il margine unitario. Per decidere conviene la versione sul margine: un mix che sposta vendite verso prodotti più cari ma meno redditizi migliora i ricavi e peggiora l'utile.

### Regole di lettura del corso

- Scomporre prima di giudicare: un calo delle vendite può essere tutto volume, e allora prezzo e mix non vanno toccati [L12].
- Se le vendite effettive sono molto sotto il budget, partire dall'effetto volume [M039].
- Se la composizione delle vendite cambia molto, guardare il mix prima di modificare la strategia [M039, M037].
- Non confondere mix e volume [M039]: un effetto mix favorevole può compensare un calo di quantità, e un aumento di prezzo può migliorare il margine anche con meno pezzi [M039].
- Trasformare la scomposizione in una narrazione e poi in azioni [L12].

## La trappola del prezzo e del volume

Il corso dedica attenzione a un caso frequente: un'azienda manifatturiera di medie dimensioni vede calare i volumi e taglia i prezzi per recuperarli. Se il recupero non arriva, subisce un doppio danno: cala il numero di pezzi e cala il margine di ciascuno [L12]. Il criterio è evitare sconti aggressivi se non accompagnati da misure che compensino la perdita di prezzo unitario, e verificare prima il peso delle materie prime, specie se stanno aumentando [L12].

Il calcolo che chiarisce il rischio è sviluppato nel capitolo 05 (volume necessario per compensare uno sconto).

## Esempi di diagnosi dal corso

- Un'azienda che consuma molta carta perde margine per i rincari di carta ed energia: la risposta passa per un monitoraggio dei costi e una politica di magazzino più flessibile verso fornitori volatili [L12].
- Un'azienda con fatturato dimezzato in quattro anni aveva aumentato il personale diretto senza ridurlo con i ricavi; anche una rete di negozi aveva aumentato del 21% il personale mentre il fatturato calava [L12]. Regola: se i ricavi scendono, i variabili devono scendere in proporzione e i fissi vanno contenuti [L12].
- Un produttore di gadget scompone il proprio scarto di costo in materiali, manodopera e costi generali, e per ciascuno separa prezzo e quantità prima di cercare le cause [M037].
- Per stimare l'energia elettrica futura si parte dai consumi storici e dai contratti in scadenza; non prevedere il rinnovo a prezzi più alti è un errore citato [L12].

Le schede sono ricche sulla logica, povere di formule esplicite per le varianze: le formule riportate sono integrazioni della skill, coerenti con la scomposizione prezzo-quantità e volume-prezzo-mix descritta dal corso.
