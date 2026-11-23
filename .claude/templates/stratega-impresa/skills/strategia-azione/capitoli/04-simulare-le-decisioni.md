# Simulare le decisioni

> Integrazione della skill. Questo capitolo non viene dal corso. Il corso usa un simulatore già pronto per il business game; qui la skill spiega come costruirne uno piccolo per un'impresa specifica, con la logica della system dynamics o con un semplice foglio di calcolo. I rimandi fra quadre indicano solo dove il modello riusa le relazioni del simulatore del corso descritte nel capitolo 2 [M103, M104, M105, M106, M107]. Tutti i numeri sono illustrativi.

## Perché costruire un simulatore proprio

Un business game commerciale allena a decidere in generale; un simulatore costruito sulla propria impresa allena a decidere su quella. Il secondo ha due vantaggi. Costringe il gruppo di direzione a scrivere in forma esplicita le ipotesi su come funziona l'azienda (quanto risponde la domanda al prezzo, quanto tempo serve per assumere e formare, quanto pesa lo scarto), e spesso la discussione su queste ipotesi vale più della simulazione stessa. Inoltre permette di provare una scelta, per esempio un taglio di prezzo o una nuova linea, e di vederne gli effetti su più periodi prima di impegnare risorse vere.

Il limite va dichiarato subito: un modello piccolo semplifica, e le sue risposte sono buone quanto le ipotesi che contiene. Serve a capire la forma dei comportamenti (ritardi, oscillazioni, effetti collaterali), non a prevedere il numero esatto del prossimo anno.

## La logica della system dynamics in breve

La system dynamics descrive un'impresa con tre elementi.

- Stock: grandezze che si accumulano e si leggono in un istante. Esempi: scorta di materie prime, organico, capacità installata, cassa, clienti attivi, ordini in attesa.
- Flussi: grandezze per periodo che riempiono o svuotano gli stock. Esempi: acquisti e consumi, assunzioni e uscite, investimenti e ammortamenti, incassi e pagamenti.
- Cicli di retroazione: catene di cause che tornano sul punto di partenza. Un ciclo rinforzante amplifica (più clienti soddisfatti portano passaparola e quindi più clienti); un ciclo bilanciante tende a un equilibrio (più ordini in attesa allungano i tempi di consegna e quindi frenano i nuovi ordini).

A questi si aggiungono i ritardi: una decisione presa oggi produce effetti dopo uno o più periodi. Assumere richiede selezione e formazione; una nuova linea richiede installazione; un investimento in qualità riduce le chiamate in garanzia solo sui prodotti venduti dopo. I ritardi sono la causa più comune delle sorprese nella gestione: chi non li vede reagisce due volte allo stesso problema e produce oscillazioni.

## I cicli da modellare per primi

Per un'impresa manifatturiera piccola o media bastano cinque cicli. Ognuno si aggancia a relazioni già presenti nel simulatore del corso.

1. Domanda e prezzo (bilanciante). Un prezzo più basso aumenta i volumi, ma riduce il margine unitario; il margine totale ha un massimo. Il coefficiente del corso è 10 euro in meno per il 6% di volumi in più [M103, M104].
2. Domanda e capacità (bilanciante, con ritardo). Quando la domanda supera la capacità si accumulano ordini in attesa, i tempi di consegna si allungano, una parte dei clienti va altrove. Aumentare la capacità richiede tempo e porta ammortamenti per anni [M103, M105].
3. Qualità e costi (bilanciante, con ritardo). Più scarto significa più materiale consumato e meno pezzi buoni; più chiamate in garanzia significano più costi. Investire in personale qualità e in ricerca riduce entrambi, ma con un ritardo [M103, M104, M107].
4. Persone e produttività (rinforzante in negativo). Un turnover alto abbassa l'esperienza media, aumenta lo scarto e il carico sugli altri, che a loro volta lasciano; la formazione rompe il circolo [M106, M107].
5. Cassa e investimenti (bilanciante). Gli investimenti in capacità, qualità e pubblicità consumano cassa oggi e la restituiscono domani; se la cassa scende sotto una soglia, si tagliano proprio gli investimenti che avrebbero sostenuto i ricavi futuri.

Un sesto ciclo utile, se l'impresa ha più livelli di distribuzione, è l'amplificazione degli ordini lungo la filiera (effetto bullwhip): piccole variazioni della domanda finale diventano grandi oscillazioni negli ordini al produttore, perché ogni anello aggiunge scorte di sicurezza e reagisce con ritardo.

## Costruirlo con un foglio di calcolo

Per un primo modello il foglio di calcolo è sufficiente e ha il vantaggio che tutti lo sanno leggere. La struttura consigliata ha quattro fogli.

Foglio "ipotesi". Una cella per ogni parametro, con nome, valore, unità e fonte: crescita del PIL attesa, prezzo medio di mercato, elasticità al prezzo, effetto della pubblicità, capacità per linea, ore per unità, ore annue per persona, assenteismo, turnover, consumo per unità, tasso di scarto, tasso di chiamate, costo di riparazione, ritardi in periodi. Nessun numero va scritto altrove: le formule leggono solo da qui.

Foglio "decisioni". Una riga per periodo, una colonna per leva: prezzo, pubblicità, nuove linee, manutenzione straordinaria, assunzioni, acquisti, addetti qualità e ricerca. È l'unico foglio che i partecipanti modificano durante l'esercizio.

Foglio "motore". Una riga per periodo, con le colonne nell'ordine della catena del capitolo 2 [M103]: domanda di base, domanda dopo le leve, capacità disponibile, produzione (il minimo fra domanda più ordini in attesa e capacità), ordini persi, ore necessarie e personale, consumo effettivo di materiale, scorta, chiamate in garanzia, ricavi, costi variabili, margine di contribuzione, costi fissi e ammortamenti, risultato, cassa. Gli stock si calcolano sempre come valore del periodo precedente più entrate meno uscite: è questa regola a rendere il foglio un modello dinamico e non una tabella statica.

Foglio "cruscotto". Pochi indicatori per periodo, gli stessi del business game: rendimento del capitale, margine sulle vendite, quota di mercato, cassa generata [M102]. Due grafici bastano: andamento di domanda, capacità e produzione; andamento di risultato e cassa.

I ritardi si rendono con riferimenti a righe precedenti: se la formazione riduce lo scarto con un periodo di ritardo, la formula dello scarto al periodo t legge gli addetti qualità del periodo t - 1.

## Quando passare a uno strumento di system dynamics

Il foglio di calcolo regge finché i cicli sono pochi e i periodi sono anni o trimestri. Conviene passare a uno strumento dedicato quando servono periodi brevi (mesi o settimane) su orizzonti lunghi, quando i ritardi sono molti e si sovrappongono, quando si vogliono provare centinaia di combinazioni di parametri per capire quali contano di più, o quando il modello deve diventare un simulatore interattivo con cursori per persone che non toccano le formule. Gli strumenti aperti di questo tipo sono motori di calcolo: offrono stock, flussi e risolutori, ma il modello dell'impresa va scritto comunque. `potenziamento.md` elenca le opzioni verificate.

## Calibrare e verificare

Un modello non calibrato insegna cose sbagliate con sicurezza. Prima di usarlo in aula:

- Far girare il modello sugli ultimi due o tre anni reali, con le decisioni effettivamente prese, e confrontare i risultati con i consuntivi. Scarti grandi indicano un'ipotesi da rivedere.
- Provare condizioni estreme: prezzo nullo, pubblicità enorme, nessuna assunzione. Il modello deve dare risultati sensati (nessuna scorta negativa, nessuna produzione oltre la capacità).
- Cambiare un parametro alla volta del 20% in più e in meno e guardare quali muovono di più il risultato. Su quelli si concentra la raccolta di dati reali.
- Far leggere le ipotesi a chi lavora nelle aree: il capo produzione sa se due ore per unità sono realistiche meglio di qualsiasi modello.

## Usarlo per allenare il gruppo di direzione

Il simulatore rende il massimo in un esercizio strutturato, che riprende il ciclo per periodi del business game [M102, M118].

Preparazione. Si sceglie una decisione reale imminente (un aumento di listino, una nuova linea, un piano di assunzioni) e si costruisce lo scenario di partenza con i dati veri. Si fissano gli indicatori di giudizio.

Primo giro. Il gruppo di direzione, eventualmente diviso in due squadre con mandati diversi (per esempio una orientata alla crescita e una alla redditività), prende le decisioni per quattro-sei periodi, un periodo alla volta, vedendo i risultati dopo ciascuno.

Lettura. Si confrontano le traiettorie delle squadre e si chiede: dove ci siamo sorpresi? Le sorprese indicano ritardi o cicli che il gruppo non aveva in mente.

Shock. Si ripete con un evento imprevisto inserito a metà: un calo della domanda, un rincaro delle materie prime, un concorrente che taglia i prezzi. È la versione d'impresa della simulazione di crisi descritta nel capitolo 1, con il metodo dei quattro passi: capire il problema, contare le risorse, confrontare le opzioni, decidere su dati [L11].

Esito. Il risultato dell'esercizio non è la decisione giusta, che il modello non conosce, ma tre prodotti concreti: l'elenco delle ipotesi che il gruppo considera più incerte, da verificare con dati prima della scelta reale; le soglie che diventeranno segnali di arresto nell'esecuzione (capitolo 3); un accordo su quali indicatori anticipatori guardare nei primi mesi.

## Esempio illustrativo di scoperta

Un'azienda di componenti valuta un taglio di listino per crescere. Nel foglio, il primo anno mostra volumi in aumento e margine stabile. Al secondo anno la produzione tocca il tetto di capacità, gli ordini in attesa crescono, il turnover sale per gli straordinari, lo scarto passa dal 4% al 7% e le chiamate in garanzia aumentano sui prodotti venduti in quel periodo. Al terzo anno il margine è sotto quello di partenza, nonostante i volumi più alti. Nessuno di questi passaggi era nascosto; erano solo distribuiti su tre anni e su quattro aree, e la discussione in sala riunioni li guardava uno alla volta. La correzione emersa dall'esercizio è stata anticipare la manutenzione straordinaria e la formazione di sei mesi rispetto al taglio di prezzo, con un segnale di arresto sullo scarto.

## Errori tipici nella costruzione

- Modellare troppo. Trenta variabili rendono il modello illeggibile e non più credibile; si parte da cinque cicli e si aggiunge solo ciò che cambia le decisioni.
- Dimenticare i ritardi. Senza ritardi ogni leva funziona subito e il modello insegna una reattività che l'impresa non ha.
- Usare il modello come previsione. Il simulatore serve a confrontare strategie fra loro, non a fissare il budget.
- Tenere le ipotesi nascoste nelle formule. Ogni parametro deve stare nel foglio delle ipotesi, con la sua fonte.
- Farlo costruire solo a un analista. Il valore sta nella discussione sulle ipotesi; se il gruppo di direzione non partecipa, il modello non viene creduto.
