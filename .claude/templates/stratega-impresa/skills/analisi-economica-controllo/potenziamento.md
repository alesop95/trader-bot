# Potenziamento

Questa pagina dice quali dati e quali tipi di strumenti rendono la sotto-skill più utile su un caso reale, e come tenerli separati dalla teoria dei capitoli.

## Dati che rafforzano il filone

- Bilanci di almeno tre esercizi, con nota integrativa: servono per tendenze, riclassificazione e indici. La nota integrativa chiarisce scadenze dei debiti, fondi e criteri di ammortamento.
- Bilancio di verifica o piano dei conti con saldi: permette di ricostruire il conto economico gestionale con la classificazione fissi e variabili invece di stimarla.
- Distinte base e cicli di lavoro: sono la base dei costi standard per materiali e ore.
- Vendite per prodotto, cliente e area con quantità e prezzi: necessarie per la scomposizione volume, prezzo e mix.
- Scadenzari di clienti e fornitori e valorizzazione del magazzino per articolo: alimentano DSO, DPO, rotazioni e ciclo di cassa.
- Capacità per reparto e tempi unitari: servono per individuare il collo di bottiglia.
- Budget e forecast dell'anno: il termine di confronto di ogni scostamento.
- Medie di settore per gli indici, quando disponibili: danno un metro esterno alle soglie, che altrimenti restano generiche.

## Tipi di strumenti

- Fogli di calcolo con modelli separati per riclassificazione, margini, pareggio, varianze e VAN: permettono di mostrare formula e numeri a ogni passo.
- Librerie di calcolo numerico e finanziario per attualizzazioni, TIR e analisi di sensibilità.
- Strumenti di programmazione lineare per il mix di produzione quando i vincoli sono più di uno.
- Strumenti di visualizzazione per grafici a cascata, serie storiche e cruscotti.
- Software gestionali e di contabilità analitica, da cui estrarre i dati invece di ricostruirli a mano.

## Come tenere separati dati e teoria

- I capitoli contengono metodo, regole e esempi illustrativi; i dati dell'azienda dell'utente stanno in file di lavoro a parte, mai dentro la skill.
- Ogni calcolo su dati reali dichiara la fonte del dato (bilancio, estrazione gestionale, stima) e le ipotesi di classificazione usate.
- Le soglie che vengono da medie di settore si citano come dato esterno, con l'anno di riferimento, e non si confondono con le regole del corso.
- Le correzioni a dati incoerenti si annotano nel file di lavoro, non si applicano in silenzio.
- Gli strumenti producono numeri; la lettura e la raccomandazione restano nel ragionamento della skill, con i rimandi ai capitoli.

## Strumenti open source

Gli strumenti che seguono sono esterni al corso: servono ad applicare il filone, non ne fanno parte. Licenze, stato e indirizzi sono stati verificati il 2026-11-23; prima di adottarne uno si rilegge la licenza nel repository, perché può cambiare.

| Strumento | Licenza | A che cosa serve | URL |
|---|---|---|---|
| FinanceToolkit | MIT | Indici di bilancio, DCF e metriche di valutazione in Python, con le formule a vista | https://github.com/JerBouma/FinanceToolkit |
| numpy-financial | BSD-3-Clause | VAN, TIR, rate e flussi per i calcoli d'investimento in Python | https://github.com/numpy/numpy-financial |
| ERPNext | GPL-3.0 | ERP per PMI con contabilità generale e centri di costo, base dati per il controllo di gestione | https://github.com/frappe/erpnext |
| Odoo Community | LGPL-3.0 | ERP modulare con contabilità e analitica; l'edizione Enterprise è a pagamento e non open source | https://github.com/odoo/odoo |
| Dolibarr | GPL-3.0 | ERP leggero per piccole imprese: fatture, ordini, contabilità | https://github.com/Dolibarr/dolibarr |
| Apache Superset | Apache-2.0 | Cruscotti di KPI e reporting sugli scostamenti, interamente open source | https://github.com/apache/superset |
| Metabase | AGPL-3.0 | Cruscotti di KPI semplici da usare anche per chi non è tecnico; le funzioni enterprise hanno licenza commerciale | https://github.com/metabase/metabase |

Avvertenze: Odoo e Metabase sono open core, quindi alcune funzioni avanzate sono a pagamento. Un ERP dà i dati, non l'analisi: la riclassificazione e le varianze descritte nei capitoli restano lavoro dello stratega, che sui dati dell'ERP diventa ripetibile.
