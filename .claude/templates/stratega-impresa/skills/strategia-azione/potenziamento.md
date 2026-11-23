# Potenziamento

## A che cosa serve questa pagina

Il filone ha poche fonti del corso e due capitoli interamente integrativi. Questa pagina indica quali dati e quali tipi di strumenti lo rendono più utile su un caso reale, e come tenerli separati dalla teoria in modo che chi legge sappia sempre che cosa viene dal corso e che cosa no.

## Dati che rafforzano il filone

- Parametri reali dell'impresa per il simulatore: elasticità al prezzo stimata da listini e volumi storici, capacità per linea, ore per unità, assenteismo, turnover, tasso di scarto, tasso di chiamate in garanzia, costo medio di riparazione. Sostituiscono i coefficienti illustrativi del capitolo 2 e le ipotesi del capitolo 4.
- Serie storiche di due o tre anni di consuntivi e delle decisioni prese, per calibrare il modello (capitolo 4).
- Indicatori macroeconomici del settore e del paese (crescita, inflazione, tassi), che nel simulatore muovono la domanda di base [M103].
- Il budget, la previsione aggiornata e il rapporto mensile dell'impresa, per agganciare obiettivi trimestrali e segnali di arresto (capitolo 3).
- I verbali delle revisioni, per vedere a posteriori quali segnali erano arrivati e quando.

## Tipi di strumenti

- Motori di system dynamics: per modelli con molti ritardi, periodi brevi e analisi di sensibilità estese. Sono motori, non giochi: il modello dell'impresa va scritto.
- Librerie di modelli ad agenti: per simulare mercati con molti concorrenti o clienti eterogenei, quando la concorrenza conta più delle dinamiche interne.
- Simulazioni didattiche di filiera: per mostrare in aula l'amplificazione degli ordini.
- Gestori di obiettivi e progetti: per registrare obiettivi e risultati chiave, titolari e revisioni periodiche.
- Fogli di calcolo: restano lo strumento di partenza per il primo modello e per gli esercizi con il gruppo di direzione.

## Come tenere separati dati, strumenti e teoria

- Le regole del simulatore del corso (capitolo 2) restano citate con il loro rimando; i parametri dell'impresa si scrivono in un foglio di ipotesi a parte, con la fonte di ciascun valore.
- I risultati di un modello si presentano come esiti di uno scenario, non come previsioni né come teoria del corso.
- Gli strumenti esterni si citano solo in questa pagina; nei capitoli si descrive il metodo, non il prodotto.
- Ogni integrazione della skill resta marcata come tale anche quando viene adattata al caso.

## Strumenti open source

Gli strumenti che seguono sono esterni al corso; licenze, stato e indirizzi sono stati verificati il 2026-11-23.

| Strumento | Licenza | A che cosa serve | URL |
|---|---|---|---|
| PySD | MIT | Motore di system dynamics in Python; importa modelli scritti in Vensim e Stella. È un motore: il modello va costruito | https://github.com/SDXorg/pysd |
| BPTK-Py | MIT | System dynamics e modelli ad agenti, con simulatori interattivi per manager. Motore, non gioco; progetto piccolo (39 stelle), maturità da valutare | https://github.com/transentis/bptk_py |
| Mesa | Apache-2.0 | Modelli ad agenti per simulare mercati e concorrenza | https://github.com/mesa/mesa |
| supply-chain-simulation | CC0-1.0 | Simulazione didattica dell'effetto bullwhip. Nicchia, un solo autore, maturità bassa | https://github.com/jncohen/supply-chain-simulation |
| Leantime | AGPL-3.0 | Progetti orientati agli obiettivi, OKR e roadmap per PMI; utile per l'esecuzione e le revisioni periodiche | https://github.com/Leantime/leantime |
| OpenProject | GPL-3.0, modello open core | Portafoglio progetti, roadmap, OKR; alcune funzioni sono nell'edizione commerciale | https://github.com/opf/openproject |
| Operately | Apache-2.0, con cartella ee commerciale | Obiettivi, progetti e KPI con aggiornamenti periodici; open core, progetto ancora giovane | https://github.com/operately/operately |
| okr-tracker | MIT | Tracciamento di OKR e KPI per team; richiede un backend Firebase, comunità piccola | https://github.com/oslokommune/okr-tracker |
| numpy-financial | BSD-3-Clause | Funzioni finanziarie in Python (VAN, TIR, rate, flussi) per i fogli di cassa del simulatore | https://github.com/numpy/numpy-financial |
| Apache Superset | Apache-2.0 | Cruscotti di budget e di piano per la pagina sugli obiettivi del rapporto mensile | https://github.com/apache/superset |

Avvertenze. Non esiste un business game open source maturo: PySD e BPTK-Py sono motori di simulazione e richiedono di scrivere il modello dell'impresa, come descritto nel capitolo 4. OpenProject e Operately seguono un modello open core, con parti a pagamento. supply-chain-simulation e okr-tracker hanno maturità bassa e vanno usati per prove o per l'aula, non come sistemi di produzione.
