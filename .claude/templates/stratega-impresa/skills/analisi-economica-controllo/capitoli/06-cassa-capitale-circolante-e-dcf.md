# 06. Cassa, capitale circolante e DCF

Il filo che attraversa tutto il filone è che profitto e cassa sono due cose diverse [L12, L14, M042, M044]. Questo capitolo spiega perché divergono, come si misura la generazione di cassa con il rendiconto finanziario, come il capitale circolante la assorbe o la libera, e come si valutano gli investimenti con i flussi attualizzati. Chiude con la diagnosi di un'azienda in crisi, che mette insieme tutti gli strumenti del filone.

## Perché utile e cassa divergono

Il conto economico registra ricavi e costi quando maturano, non quando si incassano o si pagano [L12, L14]. Le differenze nascono da quattro fonti principali:

- Crediti verso clienti: una vendita a credito è ricavo oggi e cassa domani, o mai se il cliente non paga [L12].
- Magazzino: produrre per scorta assorbe cassa per materiali e lavoro senza generare incassi [L12]. Il corso cita un'azienda che vede crescere le scorte, le registra correttamente come variazione positiva delle rimanenze nel conto economico, e resta senza liquidità [L14].
- Debiti verso fornitori: pagare più tardi trattiene cassa; anticipare i pagamenti la consuma [L14].
- Investimenti: un macchinario esce di cassa tutto subito, mentre il conto economico ne registra solo l'ammortamento annuo [L12, L14].

Il corso chiede di dare priorità alla liquidità rispetto al solo risultato contabile, sia nell'analisi sia nelle decisioni di acquisto [L12, L14, M037]. Un'azienda può avere un conto economico positivo e non generare cassa per crediti non incassati e magazzino fermo [L12]. Un partecipante racconta di aver investito in scorte che non sono diventate vendite, con il risultato di ridurre la propria liquidità [L12].

## Il rendiconto finanziario

Il rendiconto finanziario è il prospetto obbligatorio che spiega da dove viene e dove va la cassa, collegando il conto economico all'attività operativa, agli investimenti e ai finanziamenti [L14].

Correzione (integrazione della skill): una scheda descrive il rendiconto come documento che "mostra la variazione del patrimonio netto". Quella è un'altra tabella del bilancio; il rendiconto spiega la variazione delle disponibilità liquide.

Struttura del metodo indiretto (integrazione della skill sulla forma, coerente con le tre aree citate dal corso [L14]):

1. Utile netto.
2. Più ammortamenti e accantonamenti (costi che non escono di cassa).
3. Meno aumento dei crediti verso clienti, meno aumento delle rimanenze, più aumento dei debiti verso fornitori (e viceversa per le diminuzioni).
4. Uguale flusso di cassa operativo.
5. Meno investimenti (capex), più disinvestimenti.
6. Uguale flusso di cassa disponibile.
7. Più o meno nuovi finanziamenti, rimborsi, dividendi, aumenti di capitale.
8. Uguale variazione della cassa.

Esempio illustrativo (migliaia di euro): utile 300, ammortamenti 200, crediti in aumento di 400, scorte in aumento di 250, debiti verso fornitori in aumento di 150.

- Flusso operativo: 300 + 200 - 400 - 250 + 150 = 0.
- Investimenti in un nuovo impianto: 500.
- Flusso disponibile: -500, da coprire con debito o capitale.

Un'azienda in utile di 300 deve chiedere 500 alla banca: è il tipo di sorpresa che il corso vuole evitare quando chiede di non confondere utile e liquidità [L09, L14]. Il corso indica anche come errore trascurare l'effetto immediato del capex sulla cassa [L12].

## Capitale circolante e ciclo di cassa

Il capitale circolante netto, nella definizione del corso, è attività correnti meno passività correnti [L12, M037]. Per la gestione conviene la versione operativa: crediti commerciali più rimanenze meno debiti verso fornitori (integrazione della skill). È il capitale che l'attività quotidiana tiene immobilizzato, e cresce con le vendite se i tempi non cambiano.

Le leve sono quelle del capitolo 02: giorni di incasso (DSO), giorni di pagamento (DPO), rotazione delle scorte [L10, L14, M042, M044]. Il corso chiede di controllare i tempi di pagamento di clienti e fornitori e di monitorare il magazzino per non immobilizzare capitale [L12].

### Ciclo di conversione della cassa (integrazione della skill)

Formula: ciclo di cassa = giorni di magazzino + DSO - DPO.

Esempio illustrativo: 60 giorni di magazzino, 75 di incasso, 50 di pagamento, ciclo di 85 giorni. Con ricavi di 3,65 milioni l'anno, cioè 10.000 euro al giorno, ogni giorno di ciclo vale circa 10.000 euro di capitale bloccato (approssimazione su base ricavi). Ridurre il DSO di 15 giorni libera circa 150.000 euro di cassa senza toccare il conto economico.

Il corso propone un modello per leggere il ciclo finanziario [L14]: identificare le fonti di cassa (vendite, prestiti), valutare gli impieghi (acquisti, investimenti), analizzare l'effetto delle scelte di finanziamento (leasing, anticipo fatture). Segnala come errore ignorare le tensioni che nascono dai ritardi con i fornitori [L14], e invita a chiedersi quali indici di circolante siano critici nel proprio settore [M042].

### Profitto contro cassa in una decisione di acquisto

Il materiale del corso usa un caso semplice: ordinare 1.000 o 1.200 unità di materiale, sapendo che sopra le 1.200 il fornitore concede uno sconto del 10% [M037, M042, M044]. Il conto economico migliora con 1.200 unità, la cassa peggiora per il magazzino in più.

Ricostruzione illustrativa dei numeri: prezzo pieno 10 euro, fabbisogno del periodo 1.000 unità.

- Ordine da 1.000: esborso 10.000, costo nel conto economico 10.000.
- Ordine da 1.200 a 9 euro: esborso 10.800, costo delle 1.000 consumate 9.000, 200 unità restano a magazzino per 1.800.
- Effetto: utile del periodo +1.000, cassa -800.

Quale scelta sia giusta dipende dalla tensione di liquidità e dal tempo in cui le 200 unità si consumeranno. Il corso usa il caso per mostrare il conflitto, non per indicare una risposta unica [M037].

## Investimenti e DCF

Gli investimenti in beni durevoli (CAPEX) generano benefici su più anni e si contabilizzano con l'ammortamento [L14]. La loro valutazione non si fa sul risultato di un anno ma sui flussi di cassa dell'intera vita, attualizzati [L14, M037, M042].

### Valore attuale netto (VAN, o NPV)

Formula: VAN = -I0 + Σ FCt / (1 + r)^t, con I0 investimento iniziale, FCt flusso di cassa dell'anno t, r tasso di attualizzazione [M037, M042, M044].

Procedura del corso [L14, M042, M044]:

1. Prevedere i flussi di cassa annui generati dall'investimento.
2. Scegliere un tasso di sconto (negli esempi del corso il 4%).
3. Attualizzare e sommare i flussi.
4. Confrontare la somma con l'investimento: si accetta se il VAN è positivo.

Esempio illustrativo: investimento 100.000 euro, flussi di 30.000 euro per quattro anni, tasso 4%.

| Anno | Flusso | Fattore 1/(1,04)^t | Valore attuale |
|---|---|---|---|
| 1 | 30.000 | 0,9615 | 28.846 |
| 2 | 30.000 | 0,9246 | 27.737 |
| 3 | 30.000 | 0,8890 | 26.670 |
| 4 | 30.000 | 0,8548 | 25.644 |
| Somma | | | 108.897 |

VAN = 108.897 - 100.000 = +8.897: l'investimento conviene. Allo stesso flusso, con un tasso del 10% la somma attualizzata scende a circa 95.096 e il VAN diventa -4.904. Il tasso cambia la decisione, quindi va scelto con cura.

Integrazioni della skill sul tasso e sugli indicatori collegati:

- Il tasso di attualizzazione dovrebbe riflettere il costo del capitale dell'azienda e il rischio del progetto, non solo il tasso di interesse bancario; il 4% degli esempi del corso è un valore didattico.
- Il tasso interno di rendimento (TIR) è il tasso a cui il VAN si annulla; nell'esempio è circa 7,7%.
- Il periodo di recupero (payback) è il tempo in cui i flussi cumulati ripagano l'investimento: qui 100.000 / 30.000 = 3,3 anni. È facile da comunicare ma ignora il valore del tempo e i flussi successivi.
- I flussi da attualizzare sono di cassa, non utili: includono le variazioni di capitale circolante che il progetto richiede e escludono l'ammortamento, che non è un'uscita.

### Errori tipici sugli investimenti

- Valutare l'investimento sul profitto contabile dell'anno invece che sui flussi pluriennali [L14].
- Sottovalutare fissi e ammortamenti nei flussi futuri [L14].
- Sottovalutare il peso a lungo termine di investimenti che non rendono [L14].
- Misurare il ritorno senza considerare l'intero ciclo di vita del prodotto [L14].

## Diagnosi di un'azienda in crisi

Il corso presenta un caso di crisi economica e finanziaria: un'azienda agricola con più divisioni, perdite crescenti e debito in aumento [M040]. La procedura indicata ha tre tempi [M040]:

1. Verificare i dati economici e finanziari.
2. Preparare per l'imprenditore una relazione sintetica.
3. Analizzare in dettaglio i conti per divisione e la parte patrimoniale.

Criteri dal caso [M040]: confrontare le divisioni per trovare le più efficienti e quelle che generano le perdite; intervenire sui costi dove i margini calano; dare priorità alla riduzione del debito e degli oneri finanziari. Errori da evitare: guardare l'azienda solo nel complesso senza separare le divisioni, trascurare il peso dei fissi sul margine operativo, saltare l'analisi dei flussi di cassa [M040].

La skill applica a un caso di crisi questa sequenza: conto economico gestionale per divisione (capitolo 03), margini di secondo livello per decidere su chiusure (capitolo 05), rendiconto e ciclo di cassa per capire quanto tempo resta (questo capitolo), indici di liquidità e costo del debito per la trattativa con le banche (capitolo 02).

## Domande guida

- Quanta cassa genera la gestione corrente, prima degli investimenti? [L14]
- Quanto capitale è fermo in crediti e scorte, e quanti giorni di ciclo si possono recuperare? [L12, L14]
- L'aumento delle scorte è voluto o subito? [L14]
- Come si migliora la liquidità senza ridurre la capacità produttiva? [L14]
- Qual è il ritorno attualizzato di questo investimento su tutta la sua vita? [L14]

Le schede sono ricche sul principio "profitto non è cassa" e sulla procedura DCF; sono povere sulla struttura del rendiconto e sul ciclo di cassa, che qui sono integrazioni della skill.
