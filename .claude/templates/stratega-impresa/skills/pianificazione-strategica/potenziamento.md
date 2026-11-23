# Potenziamento

## A che cosa serve questa sezione

La teoria del filone dice come pensare il piano; i dati e gli strumenti rendono il piano verificabile. Questa pagina elenca che cosa conviene avere a disposizione quando si applica la sotto-skill a un caso reale, e come tenerlo distinto dalla teoria del corso. Le indicazioni sono integrazioni della skill, salvo dove portano un rimando.

## Dati che rafforzano il filone

| Uso | Dato | Dove entra |
|---|---|---|
| Ancorare gli obiettivi di crescita | Dimensione e crescita del mercato di riferimento, quote dei principali concorrenti | Test contro l'effetto bonsai, matrice BCG (capitoli 02, 03) |
| Costruire scenari | Serie storiche di prezzi delle materie prime, cambi, tassi, indicatori congiunturali | Scenari esterni estremi (capitolo 03) |
| Ricostruire il passato | Bilanci degli ultimi tre-cinque anni dell'impresa e di alcuni concorrenti comparabili | Primo blocco del piano industriale (capitolo 04) |
| Valutare investimenti | Costo del capitale, tassi di finanziamento disponibili, vita utile degli impianti | Attualizzazione dei flussi (capitolo 04) |
| Chiudere lo stato patrimoniale | Giorni medi di incasso, giacenza e pagamento effettivi degli ultimi due anni | Fabbisogno di debito (capitolo 05) |
| Scegliere il mix | Margine di contribuzione e ore di produzione per prodotto | Priorità di vendita (capitolo 05) |
| Alimentare il report | Consuntivi mensili per centro di responsabilità, ordini, portafoglio, cassa | Quattro finestre (capitolo 06) |

## Tipi di strumenti utili

- Lavagne collaborative digitali per le fasi di esplorazione e di priorità, come quelle usate nei laboratori del corso [L05, L06].
- Fogli di calcolo condivisi in cloud con moduli di caricamento uguali per tutti i reparti, per il budget collaborativo [L15, L16].
- Un modello di piano finanziario integrato (conto economico, stato patrimoniale, rendiconto finanziario) in cui il debito è la variabile di chiusura.
- Strumenti di analisi di sensibilità e di simulazione per la fase "che cosa succede se" [M120, M013].
- Strumenti di visualizzazione che supportano grafici a proiettile, mappe di calore e piccoli multipli [L16].
- Un registro delle iniziative del piano con responsabile, stato e scadenze, collegato al report mensile.

## Come tenere separati dati e teoria

- I numeri dell'impresa dell'utente vanno in file di lavoro propri, non dentro i capitoli della skill.
- Ogni stima usata nel piano porta la sua fonte e la data; se è un'ipotesi, lo dice.
- I risultati prodotti da uno strumento (per esempio un VAN o un fabbisogno di debito) si riportano come risultato di calcolo, con le ipotesi, e non come raccomandazione del corso.
- Quando i dati contraddicono un criterio del corso, si segnala la contraddizione invece di piegare il criterio.

## Strumenti open source

Gli strumenti che seguono sono esterni al corso: servono ad applicare il filone, non ne fanno parte. Licenze, stato e indirizzi sono stati verificati il 2026-11-23; prima di adottarne uno si rilegge la licenza nel repository, perché può cambiare.

| Strumento | Licenza | A che cosa serve | URL |
|---|---|---|---|
| Leantime | AGPL-3.0 | Gestione dei progetti orientata agli obiettivi, con OKR e roadmap, pensata per piccole e medie imprese | https://github.com/Leantime/leantime |
| OpenProject | GPL-3.0 | Portafoglio progetti, roadmap e tracciamento degli obiettivi; esiste un'edizione commerciale | https://github.com/opf/openproject |
| Operately | Apache-2.0 | Collega obiettivi, progetti e indicatori con aggiornamenti periodici; una parte del codice ha licenza commerciale, progetto giovane | https://github.com/operately/operately |
| okr-tracker | MIT | Tracciamento di OKR e KPI per team; richiede un servizio di backend esterno | https://github.com/oslokommune/okr-tracker |
| numpy-financial | BSD-3-Clause | VAN, TIR e flussi per il modello finanziario pluriennale del piano industriale | https://github.com/numpy/numpy-financial |
| Apache Superset | Apache-2.0 | Cruscotti di confronto fra piano, budget e consuntivo | https://github.com/apache/superset |

Avvertenze: non esiste oggi uno strumento open source maturo e attivo per la balanced scorecard o la mappa strategica; i progetti dedicati sono fermi da anni. Il piano industriale resta un foglio di calcolo ben strutturato, eventualmente affiancato dalle librerie di calcolo finanziario.
