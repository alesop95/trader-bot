# Studio didattico master - come e perché <nome progetto> è stato costruito

> Documento didattico principale ed evolutivo. Cresce a ogni modifica di codice significativa, e il suo scopo è far capire, rileggendolo, come il progetto è stato costruito e perché, mettendo sempre a confronto due cose: com'era stata scritta la prima stesura e come è stata migliorata. L'enfasi sta nella contrapposizione, perché è lì che si impara: non basta vedere il codice buono, serve vedere accanto quello che sostituisce e capire che cosa lo rendeva fragile.
>
> Come si legge. Questo file è l'indice narrativo e il confronto ad alto livello: si legge per il quadro e per il perché. Ogni voce rimanda a una scheda di dettaglio `<prefisso>-NN-<slug>.md` nella stessa cartella, che entra nel codice riga per riga.
>
> Come si aggiorna. A ogni refactor o scelta di qualità non ovvia si aggiunge qui una voce con la struttura fissa in quattro parti, in fondo e senza toccare le voci precedenti, e si crea la scheda di dettaglio corrispondente. Il work-log `.claude/memory/progress.md` resta il registro sintetico dei fatti; questo file è il racconto del perché. I due non si sostituiscono: il fatto sopravvive al ragionamento che lo ha prodotto, ed è il ragionamento che si perde per primo.
>
> Il numero di una voce non si riusa mai, nemmeno quando una scheda viene superata: una scheda superata si marca come tale e resta, perché il rimando che qualcuno ha scritto altrove deve continuare a puntare a qualcosa.

## Indice delle voci

1. <titolo della prima voce, nella forma "dall'approccio ingenuo a quello adottato">

---

## 1. <titolo della voce>

Contesto. <perché si è intervenuti, in una manciata di righe, senza ripetere lo stato che le schede tecniche già descrivono. Dice qual era la situazione e quale domanda si è posta, non che cosa si è fatto.>

Com'era e perché era fragile. <la forma precedente del codice o della decisione, descritta con precisione e senza condiscendenza verso chi l'aveva scritta: quasi sempre era la scelta ragionevole con le informazioni di allora. La fragilità va nominata come proprietà strutturale e non come errore di battitura, perché è la struttura a produrre la classe di difetti, e va detto in che modo si manifestava: un difetto silenzioso, un costo pagato da chi non ne beneficia, una modifica che obbliga a ricordarsi di toccare altri punti.>

Il salto e perché è meglio. <la forma nuova, il principio generale che la guida, e la ragione per cui quel principio regge dove l'altro cedeva. Qui va anche la misura, dove esiste: quanto è sceso un tempo, un peso, un numero di chiamate. E va detta la differenza di mentalità fra le due forme in una frase sola, perché è quella che si porta via chi legge.>

Dove leggere il dettaglio: `<prefisso>-NN-<slug>.md`.

---
