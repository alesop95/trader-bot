# Perché ogni microstep serve al progetto: la catena che lega il registro allo scopo

> Modello di pagina di raccordo, da istanziare soltanto in un progetto che abbia già molte voci di registro prive della dichiarazione del legame con lo scopo. In un progetto nuovo non serve, perché quella dichiarazione la porta ogni voce. Il testo fra parentesi angolari va sostituito con il contenuto del progetto; il resto è impianto e può restare com'è.

## Perché questa pagina esiste, e perché non si è corretto il registro

La lacuna va nominata invece di essere aggirata: fino alla voce &lt;MS-NNN&gt; le voci di questo registro spiegano il perché tecnico dell'intervento, cioè perché quel comando e non un altro, e non il perché di progetto, cioè che cosa dell'obiettivo dipenda da quell'intervento. Chi legge il registro dall'inizio incontra configurazioni, strumenti e diagnosi, e può legittimamente chiedersi dove sia finito il prodotto.

La correzione non poteva però essere la riscrittura delle voci passate, per due ragioni. La prima è che la convenzione del registro lo vieta esplicitamente. La seconda è che una riscrittura fatta a posteriori produrrebbe un documento che sembra essere sempre stato completo, che è lo stesso difetto per cui si ritira una inferenza invece di cancellarla.

La forma corretta è quindi additiva: il legame si fornisce qui, una volta, per blocchi omogenei, e si rende obbligatorio d'ora in avanti nella convenzione del registro.

## La catena, dall'obiettivo agli strumenti

&lt;Si percorre la catena all'indietro, dall'obiettivo del progetto fino al lavoro che sembra più lontano da esso, perché è in quel verso che si capisce perché quel lavoro esiste. Ogni anello è una implicazione: l'obiettivo richiede X, X richiede Y, Y richiede lo strumento Z, e la manutenzione di Z è quindi condizione di eseguibilità e non un lavoro che ha sostituito il progetto.&gt;

## La mappa per blocchi

La mappa è per blocchi omogenei e non voce per voce, perché molti microstep servono lo stesso scopo e ripeterlo per ciascuno sarebbe rumore. Per ogni blocco si dichiara a che cosa serve e che cosa sarebbe impossibile senza di esso.

&lt;Un paragrafo per blocco, nella forma: nome del blocco, intervallo indicativo delle voci, fase o obiettivo servito, e che cosa sarebbe impossibile senza quel blocco.&gt;

&lt;Almeno un blocco, in un progetto reale, non serve alcuna fase: tipicamente l'igiene documentale e la manutenzione degli strumenti. Va dichiarato come tale, perché è la voce che rende onesta tutta la mappa: se ogni blocco risultasse giustificato, la mappa non starebbe misurando nulla.&gt;

## La convenzione, valida dai microstep successivi

Dal &lt;data&gt; ogni microstep nuovo dichiara in apertura, subito dopo il perimetro, a che cosa serve e che cosa dipenda da esso. La forma è una frase, non una sezione, e quando l'intervento non serve alcuna fase lo dichiara. La convenzione è scritta anche nella sezione `Convenzione` del registro, così che chi scrive una voce nuova la trovi dove la cerca invece che in questa pagina.
