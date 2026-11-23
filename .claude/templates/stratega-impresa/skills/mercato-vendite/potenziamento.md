# Potenziamento

Questa sezione indica quali dati e quali tipi di strumenti rendono più solide le analisi del filone, e come tenerli separati dalla teoria del corso. La regola di base: i modelli dei capitoli dicono che cosa chiedere; i dati e gli strumenti dicono quanto vale, per questa impresa, oggi. Quando una risposta usa dati esterni o calcoli prodotti da uno strumento, va detto da dove vengono e con quale data, distinto dai rimandi al corso.

## Dati che rafforzano il filone

### Canali e go-to-market (capitolo 01)

- Dati di vendita per canale e per punto vendita: scontrino medio, rotazione, spazio a scaffale, conversione dei visitatori.
- Dati di comportamento online e offline dello stesso cliente, se un CRM o un programma fedeltà li collega.
- Listini e condizioni lungo la catena, per ricostruire margine di canale e potere di ciascun anello.
- Panel di consumo e dati della distribuzione sulle quote per formato di negozio.

### Rete e funnel (capitoli 02 e 03)

- Estrazione dal CRM: contatti per fonte, fasi, tempi di passaggio, opportunità perse e motivo.
- Anagrafica clienti con fatturato, margine, giorni medi di pagamento e insolvenze degli ultimi tre anni.
- Stima della spesa totale di categoria dei clienti principali, per calcolare la quota del cliente.
- Agenda e rapportini dei venditori, per misurare visite reali e capacità.
- Dati territoriali di potenziale (imprese per settore e area, popolazione, reddito) per il geomarketing.

### Marketing digitale (capitolo 04)

- Statistiche delle piattaforme pubblicitarie e social: copertura, CTR, CPM, CPC, conversioni.
- Analitica del sito: sorgenti di traffico, frequenza di rimbalzo, percorsi verso la conversione.
- Andamento delle ricerche per parola chiave e confronto fra temi nel tempo.
- Recensioni e discussioni pubbliche su prodotto e concorrenti.
- Dati di costo interni per CAC e CLV, raccolti in modo coerente nel tempo.

### Vendita e trattativa (capitolo 05)

- Registrazioni o note degli incontri, quando i clienti lo consentono, per verificare l'uso delle domande e l'equilibrio fra ascolto e presentazione.
- Esiti delle trattative con motivo di vittoria o di perdita.
- Risultati di questionari di stile comportamentale, letti come strumento di sviluppo e non di selezione.

### Internazionalizzazione (capitolo 06)

- Statistiche di commercio estero per codice doganale e paese.
- Indicatori macroeconomici e proiezioni di crescita delle istituzioni internazionali.
- Indici di rischio paese e di facilità di fare impresa.
- Tariffe doganali e requisiti normativi per prodotto e destinazione.
- Banche dati aziendali per liste di potenziali clienti e distributori, con dati di bilancio.
- Rating di credito delle controparti estere.

## Tipi di strumenti utili

- Fogli di calcolo con modelli riutilizzabili: punteggio pesato dei paesi, escalation del prezzo estero, dimensionamento della rete, confronto delle fonti di contatto, pareggio di un servizio.
- CRM e strumenti di automazione commerciale per tracciare il funnel e misurare conversioni e tempi.
- Piattaforme di analitica web e di gestione delle campagne, con funzioni di test A/B.
- Strumenti di pianificazione dei contenuti sui social.
- Sistemi informativi geografici per mappe di copertura e potenziale.
- Strumenti di analisi testuale per recensioni, forum e note di visita.
- Banche dati di commercio internazionale, di tariffe e di informazioni aziendali.

## Come tenerli separati dalla teoria

1. Il capitolo fornisce la domanda e il modello; lo strumento fornisce il numero. Nella risposta i due livelli restano distinti: "secondo il metodo del corso [L22] il criterio è la quota del cliente; dai dati del CRM al mese X la quota è Y".
2. Ogni dato esterno porta fonte e data di estrazione. I dati di mercato invecchiano in fretta.
3. Le soglie del corso (30 per cento di quota, 90 giorni, 20 per cento di concentrazione, rischio paese 4 su 7, 5 milioni di fatturato) sono regole pratiche; se i dati del settore suggeriscono valori diversi, lo si dice e si motiva lo scostamento.
4. I modelli di calcolo prodotti in sessione vanno salvati come file separati, non incollati dentro i capitoli della skill.
5. Gli esempi numerici illustrativi dei capitoli non si sostituiscono ai dati reali dell'impresa.

## Strumenti open source

Gli strumenti che seguono sono esterni al corso: servono ad applicare il filone, non ne fanno parte. Licenze, stato e indirizzi sono stati verificati il 2026-11-23; prima di adottarne uno si rilegge la licenza nel repository, perché può cambiare.

| Strumento | Licenza | A che cosa serve | URL |
|---|---|---|---|
| EspoCRM | AGPL-3.0 | CRM per clienti, opportunità e pipeline, estendibile | https://github.com/espocrm/espocrm |
| SuiteCRM | AGPL-3.0 | CRM maturo e personalizzabile per pipeline e campagne | https://github.com/SuiteCRM/SuiteCRM |
| Frappe CRM | AGPL-3.0 | CRM leggero, integrabile con un ERP della stessa famiglia | https://github.com/frappe/crm |
| Plausible | AGPL-3.0 | Analisi del traffico web senza cookie, con obiettivi e funnel di conversione | https://github.com/plausible/analytics |
| Umami | MIT | Analisi del traffico web rispettosa della privacy, con campagne, funnel e percorsi | https://github.com/umami-software/umami |
| Matomo | GPL-3.0 | Analisi del traffico web completa, con attribuzione; alcune funzioni sono estensioni a pagamento | https://github.com/matomo-org/matomo |
| comtradeapicall | MIT | Accesso in Python ai dati ufficiali sul commercio internazionale per l'analisi paese; serve una chiave di accesso | https://github.com/uncomtrade/comtradeapicall |
| wbgapi | MIT | Accesso in Python agli indicatori aperti di sviluppo economico (reddito, popolazione, struttura dell'economia) | https://github.com/tgherzog/wbgapi |
| world_trade_data | MIT | Dati su scambi e dazi, con indici di concentrazione e di penetrazione di mercato | https://github.com/mwouts/world_trade_data |

Avvertenze: le tre librerie per l'analisi paese sono client di banche dati pubbliche, e i dati hanno condizioni d'uso proprie, distinte dalla licenza del codice. Per l'attribuzione del marketing non esiste oggi uno strumento open source dedicato e maturo. Alcuni CRM recenti molto diffusi richiedono codice a licenza commerciale per l'uso in produzione e per questo non sono in tabella.
