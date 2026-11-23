# Potenziamento

## A che cosa serve questa pagina

I capitoli del filone danno metodi e criteri; su un caso reale diventano utili quando li si alimenta con i dati dell'impresa. Questa pagina indica quali dati servono per ciascuna area, quali tipi di strumenti aiutano a raccoglierli e usarli, e come tenerli separati dalla teoria in modo che chi legge distingua sempre il metodo del corso, i fatti dell'impresa e le proposte aggiuntive.

## Dati che rafforzano il filone

### Processi del personale (capitoli 01 e 02)

- Organico per ruolo, anzianità, età e costo, per vedere dove mancano successori e dove si concentrano i rischi di uscita.
- Indicatori di reclutamento: candidature per posizione, provenienza per canale, tempo di copertura, tasso di accettazione delle offerte, quota di assunti da segnalazione interna, conversione degli stage in contratti [L07, M016].
- Uscite nel primo anno e motivi dichiarati nei colloqui di uscita, per giudicare la selezione a valle [L07].
- Risultati delle indagini di clima anonime, con le azioni decise dopo ciascuna [L07].
- Schede di valutazione degli ultimi due o tre anni, per vedere la distribuzione dei punteggi e scoprire appiattimento, indulgenza o severità [M028].
- Profili di competenza esistenti e descrizioni dei ruoli, da confrontare con la strategia in corso.

### Leadership, feedback e delega (capitoli 03 e 04)

- Mappa dei collaboratori diretti di ogni responsabile con il livello di sviluppo stimato sui compiti principali; va aggiornata a ogni cambio di compito.
- Esiti di questionari a 360 gradi, quando esistono [M031].
- Registro delle deleghe in corso: chi, che cosa, con quale autorità, con quali verifiche.
- Osservazioni di comportamento raccolte durante l'anno, con data e fatto, che alimentano feedback e valutazione.

### Processi e pensiero snello (capitolo 05)

- Mappa dello stato attuale dei processi principali, con tempi di ciclo, tempi di attesa e tempo di attraversamento misurati sul posto.
- Tempi di setup per macchina e per famiglia di prodotto, misurati dall'ultimo pezzo buono al primo pezzo buono [L28].
- Livelli di scorta, consumi medi e tempi di approvvigionamento per articolo, per applicare la regola della scorta [L28].
- Disponibilità, prestazione e qualità per impianto, per calcolare l'efficienza complessiva [L28].
- Scarti, rilavorazioni e reclami classificati per causa.
- Esiti degli audit 5S nel tempo [L28].
- Margine per cliente, per decidere su quali clienti investire tempo e su quali no; il calcolo spetta ad `analisi-economica-controllo` [L27].

### Tempo e produttività (capitolo 06)

- Registro di due settimane delle ore della direzione per attività, da classificare nei quattro quadranti e da incrociare con i risultati (analisi di Pareto) [L30, M097].
- Numero, durata e partecipanti delle riunioni ricorrenti, con le decisioni prodotte.
- Registro dei pomodori, con stime, consuntivi e interruzioni, per chi adotta la tecnica [M099].
- Ore lavorate e risultato prodotto, per seguire la produttività aziendale [L30].

## Tipi di strumenti

- Sistemi di gestione del personale: anagrafica, organigramma, valutazioni e piani di sviluppo in un solo archivio; utili soprattutto per la griglia prestazione-potenziale e per i piani di successione.
- Gestori di candidature: tracciano le ricerche dal profilo all'assunzione e restituiscono gli indicatori di reclutamento.
- Strumenti di indagine e questionario: per indagini di clima anonime e raccolte a 360 gradi.
- Strumenti di disegno di processi e mappe del flusso del valore: per rappresentare stato attuale e futuro in forma condivisa.
- Lavagne kanban digitali: per rendere visibile il lavoro in corso negli uffici e limitarne la quantità.
- Sistemi di raccolta dati di produzione a bordo macchina: per tempi di fermo, setup ed efficienza complessiva.
- Timer, liste di attività e calendari condivisi: per la tecnica del pomodoro, il time-boxing e la protezione del secondo quadrante in agenda.
- Fogli di calcolo: restano lo strumento di partenza per schede di valutazione pesate, calcolo delle scorte, analisi di Pareto del tempo.

## Come tenere separati dati, strumenti e teoria

- I metodi del corso restano citati nei capitoli con il loro rimando; i dati dell'impresa si scrivono in documenti di lavoro a parte, con la fonte e la data di ciascun valore.
- I numeri dei capitoli marcati come illustrativi non si usano come riferimento per un'impresa reale; vanno sostituiti con i dati raccolti.
- I risultati di test di personalità o di comportamento si trattano come indizi da verificare con l'osservazione, mai come diagnosi, coerentemente con quanto il corso chiede in selezione [L08].
- I dati sulle persone (valutazioni, profili, esiti di colloqui) sono riservati: nelle analisi si aggregano per ruolo o per gruppo e non si nominano individui (integrazione della skill).
- Gli strumenti esterni si citano solo in questa pagina; nei capitoli si descrive il metodo, non il prodotto.
- Ogni integrazione della skill resta marcata come tale anche quando viene adattata al caso.

## Strumenti open source

Gli strumenti che seguono sono esterni al corso: servono ad applicare il filone, non ne fanno parte. Licenze, stato e indirizzi sono stati verificati il 2026-11-23; prima di adottarne uno si rilegge la licenza nel repository, perché può cambiare.

| Strumento | Licenza | A che cosa serve | URL |
|---|---|---|---|
| Frappe HR | GPL-3.0 | Gestione del personale con competenze, cicli di valutazione delle prestazioni e presenze | https://github.com/frappe/hrms |
| OrangeHRM | GPL-3.0 | Gestione del personale consolidata, con valutazioni e processi HR | https://github.com/orangehrm/orangehrm |
| OpenCATS | MPL-2.0 e licenza CATS 1.1a | Selezione: tracciamento dei candidati lungo il processo di ricerca | https://github.com/opencats/OpenCATS |
| Kanboard | MIT | Kanban essenziale per rendere visibile il flusso di lavoro e limitare il lavoro in corso | https://github.com/kanboard/kanboard |
| Wekan | MIT | Kanban collaborativo installabile in proprio, senza telemetria | https://github.com/wekan/wekan |
| Super Productivity | MIT | Pianificazione del lavoro personale e misura del tempo, anche senza connessione | https://github.com/super-productivity/super-productivity |

Avvertenze: OpenCATS ha un doppio regime di licenza, e la parte originale impone vincoli su marchio e servizi in outsourcing, da leggere prima dell'uso. Per la mappa del flusso del valore non esiste un software open source dedicato: si disegna con diagrams.net (vedi `scenari-modelli-business`). I dati sulle persone sono dati personali: l'installazione in proprio non esonera dalle regole sulla loro protezione.
