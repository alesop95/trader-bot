# Domanda, capacità e costi nella simulazione

> Nota sulle fonti. Le regole numeriche vengono dalle slide che presentano le variabili del simulatore [M103, M104, M105, M106, M107]. Le slide danno i coefficienti ma non dicono sempre come si combinano fra loro: dove la skill sceglie un'ipotesi (per esempio effetti moltiplicativi invece che additivi) lo segnala. L'esempio numerico è illustrativo e non riproduce dati del corso.

## La catena delle decisioni

Il simulatore del corso segue una catena che conviene tenere a mente anche nell'impresa reale [M103]: prima si stima la domanda a partire dall'economia e dalle leve commerciali, poi si pianifica la produzione dentro la capacità disponibile, poi si dimensionano personale e materie prime, infine si calcolano costi generali, oneri finanziari e imposte, tenendo d'occhio il quadro macroeconomico (crescita del prodotto interno, tassi d'interesse, inflazione). Ogni anello dipende dal precedente: un errore sulla domanda si propaga a tutto il resto.

## Domanda corrente

La domanda di partenza di un periodo è quella del periodo prima, fatta crescere al ritmo del prodotto interno lordo [M103, M104, M106, M107]:

`domanda corrente = domanda del periodo precedente × (1 + crescita del PIL)`

Se il prodotto interno scende, la domanda di base scende con lui. Uno degli errori segnalati è ignorare un PIL negativo nelle scelte di prezzo e di produzione [M105]. Sulla domanda di base agiscono poi le leve della squadra e le mosse dei concorrenti [M104].

## Le leve commerciali e le loro elasticità

Le slide danno tre coefficienti.

| Leva | Effetto sui volumi | Fonte |
|---|---|---|
| Prezzo: 10 euro sotto il prezzo medio di mercato | +6% | [M103] |
| Prezzo: 10 euro sopra il prezzo medio di mercato | -6% | [M104] |
| Pubblicità: 500.000 euro in più | +4% | [M104, M105, M107] |
| Commissioni di vendita: 3 punti in più | +10% | [M105] |

Le relazioni si leggono come sensibilità: dicono quanto rispondono i clienti, non se conviene muovere la leva. La convenienza dipende dal margine unitario. I criteri delle slide vanno nella stessa direzione: con PIL in crescita alzare i prezzi con prudenza, per non perdere volumi; spingere la pubblicità solo se i margini lo consentono [M106]. Le domande che le slide pongono sono il bilanciamento fra prezzo più basso e margine, e fra spesa pubblicitaria e crescita delle vendite [M103, M105, M107].

Le slide non dicono se più leve mosse insieme si sommano o si moltiplicano; l'esempio sotto le moltiplica, che per variazioni piccole dà quasi lo stesso risultato (integrazione della skill).

## Capacità produttiva

La capacità dipende dal numero di linee di assemblaggio e dalla capacità di ciascuna [M103]. Si aumenta in due modi [M104, M105, M106, M107]:

- nuove linee, con un investimento che poi si ammortizza: le slide indicano un ammortamento annuo pari al 10% del costo delle linee [M103];
- manutenzione straordinaria, che costa 200.000 euro per ogni 20% di capacità in più, con un tasso di manutenzione che non può superare il 40% [M105].

Il criterio è prudente: espandere solo quando serve, perché ogni linea in più porta ammortamenti per anni [M103], e ricorrere alla manutenzione straordinaria solo se la capacità esistente non basta [M106]. Gli errori opposti sono espandere senza verificare la redditività nel tempo [M103] e dimenticare che la manutenzione straordinaria cambia la capacità disponibile [M106]. Quando la capacità è il vincolo, le decisioni di produzione vengono prima delle altre [M107]: inutile spingere la domanda oltre ciò che si può consegnare.

## Ore di lavoro e personale

Il fabbisogno di persone si ricava dalle ore [M106, M107]:

1. ore necessarie = volume da produrre × tempo di assemblaggio per unità;
2. ore disponibili per lavoratore = giorni lavorativi × ore al giorno, al netto dell'assenteismo;
3. lavoratori necessari = ore necessarie ÷ ore disponibili per lavoratore;
4. assunzioni = differenza con l'organico attuale, più le uscite attese per rotazione del personale.

Il quarto passo è quello che si dimentica: chi non mette in conto il turnover si trova sotto organico a metà periodo [M106]. Le slide collegano il turnover alla formazione: se la rotazione è alta conviene investire in formazione, e sottovalutarne l'effetto su turnover e produttività è un errore ricorrente [M107].

## Materie prime e scarto

Il consumo teorico si ricava dalla produzione e dalla distinta base; quello effettivo lo supera del tasso di scarto [M103, M104, M105, M107]:

`consumo effettivo = consumo teorico × (1 + tasso di scarto)`

Con uno scarto del 30% serve il 30% di materiale in più del teorico [M103]. Il simulatore impone anche una scorta minima di 20.000 unità di materie prime; scendere sotto la soglia ferma la produzione [M103]. Gli acquisti non pianificati costano di più [M106, M107], e i materiali indicano un aggravio del 20% [M102]. Lo scarto, inoltre, consuma capacità: più pezzi scartati significano meno pezzi buoni dalla stessa linea [M105]. Il criterio operativo è netto: oltre il 5% di scarto si investe in personale dedicato alla qualità [M107].

## Costi di garanzia e ricerca

I costi di garanzia dipendono dal tasso di chiamate, cioè da quanto spesso i prodotti tornano per riparazione, e dal costo unitario di riparazione [M104, M107]. La formula delle slide è [M107]:

`costi di garanzia = tasso di chiamate × costo di riparazione per unità × 50% del volume`

La leva per ridurli è la ricerca e sviluppo: ogni 5 addetti in più riducono il tasso di chiamate di 5, senza scendere sotto il 5% [M104]. Un tasso sopra il 15% porta costi aggiuntivi [M105]. Il costo unitario di riparazione si ottiene dividendo il totale speso per le unità riparate [M104].

Due punti restano ambigui nelle slide. La riduzione "del 5%" può essere letta come cinque punti percentuali o come un calo relativo; il pavimento al 5% fa pensare ai punti. Il fattore del 50% del volume non è spiegato: può indicare che solo metà del venduto è ancora in garanzia. L'esempio mostra entrambe le letture del primo punto.

## Un esempio numerico illustrativo

Tutti i valori di partenza sono inventati; i coefficienti sono quelli delle slide.

Domanda. Domanda del periodo precedente 100.000 unità, PIL +2%: domanda corrente 102.000. La squadra prezza 10 euro sotto la media (+6%) e aggiunge 500.000 euro di pubblicità (+4%). Con effetti moltiplicativi: 102.000 × 1,06 × 1,04 ≈ 112.445 unità.

Prezzo e margine. Con prezzo medio 250 euro e costo variabile 150 euro il margine unitario è 100 euro. Tagliando 10 euro scende a 90; con il 6% di volumi in più il margine totale passa da 100 a 90 × 1,06 = 95,4 per ogni 100 unità di partenza. Il taglio conviene solo se il margine unitario iniziale è sotto circa 177 euro, cioè quando (m - 10) × 1,06 ≥ m. Con margini alti il taglio di prezzo distrugge valore.

Pubblicità. Il 4% su 108.120 unità vale circa 4.325 unità; a 90 euro di margine sono circa 389.000 euro, meno dei 500.000 spesi. In questo caso la pubblicità da sola non si ripaga nel periodo.

Capacità. Due linee da 50.000 unità danno 100.000: non bastano. Una manutenzione straordinaria da 200.000 euro porta la capacità a 120.000, sufficiente.

Personale. Tempo di assemblaggio 2 ore per unità: servono 224.890 ore. Un lavoratore ha 220 giorni × 8 ore = 1.760 ore, che con il 5% di assenteismo diventano 1.672. Servono 224.890 ÷ 1.672 ≈ 135 persone. Con 125 in organico e 10 uscite attese per turnover, le assunzioni sono 20.

Materie prime. Tre componenti per prodotto: 337.335 teorici; con scarto all'8% diventano circa 364.322. Con scorta iniziale di 50.000 e scorta minima di 20.000, l'acquisto pianificato è 364.322 + 20.000 - 50.000 = 334.322 componenti. Lo scarto supera il 5%: la regola chiede personale qualità.

Garanzia. Tasso di chiamate 12%, riparazione 80 euro: 0,12 × 80 × 0,5 × 112.445 ≈ 539.700 euro. Con 5 addetti in più alla ricerca, letti come cinque punti in meno, il tasso va al 7% e il costo scende a circa 314.800 euro, un risparmio di circa 225.000 euro da confrontare con il costo dei cinque addetti. Letto come calo relativo, il tasso va all'11,4% e il risparmio è di circa 27.000 euro: la decisione cambia secondo la lettura, quindi in un gioco reale va chiarita con chi lo conduce.

## Due voci da verificare

Le slide riportano imposte al 33% "sui ricavi" [M103]: nella realtà le imposte sul reddito si calcolano sull'utile, e un'aliquota sui ricavi produrrebbe perdite quasi certe; è probabile un'imprecisione della sintesi, da verificare sulle regole del gioco (integrazione della skill). Le slide propongono infine due domande che restano aperte: se investire in ricerca su un prodotto nuovo o difendere la capacità esistente [M105], e se convenga partecipare a una gara pubblica confrontando costo di produzione esterna e prezzo necessario per vincerla [M106]. Entrambe si risolvono con l'analisi dei margini, per cui si rimanda ad `analisi-economica-controllo`.
