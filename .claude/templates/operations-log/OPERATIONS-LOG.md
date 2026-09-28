# Registro dei microstep

> Tracciamento cronologico degli interventi, un microstep per voce. Ogni voce dichiara che cosa è stato fatto, a che cosa serve, come è stato verificato e con quale esito. La verifica è la parte che conta: un microstep senza esito verificato resta aperto, e la colonna dell'esito non contiene mai una previsione.

## Convenzione

Ogni microstep ha un identificativo progressivo nella forma `MS-NNN`, una data, un titolo, il perimetro dei file toccati, la dichiarazione del legame con lo scopo del progetto, il comando o l'osservazione con cui è stato verificato, e l'esito. Gli stati possibili sono `fatto` quando la verifica è passata, `bloccato` quando la verifica non è eseguibile per una dipendenza esterna, e `aperto` quando il lavoro è iniziato e non concluso. Un microstep bloccato dichiara sempre da che cosa dipende.

Le voci si aggiungono in ordine cronologico crescente, così che il registro si legga come una storia. Non si riscrive una voce passata: se un intervento successivo la corregge, si aggiunge una voce nuova che dichiara di superarla.

## Il legame con lo scopo del progetto

Ogni microstep dichiara in apertura, subito dopo il perimetro, a quale fase o obiettivo del progetto serve e che cosa dipenda da esso. È una frase e non una sezione. Quando l'intervento non serve alcuna fase lo dichiara apertamente, perché un legame inventato è peggio di un legame assente: fa credere che tutto sia giustificato e toglie valore alle giustificazioni vere.

La regola esiste perché un registro di interventi operativi tende a diventare illeggibile come cronaca di sistemistica. Chi lo legge dall'inizio incontra configurazioni, strumenti e diagnosi, e perde di vista il prodotto; la dichiarazione del legame è ciò che tiene insieme il come e il perché.

## Perché non si riscrive, e perché questo non fa perdere pezzi

La regola di non riscrivere una voce passata è la ragione per cui il registro conserva anche gli errori, e va capita nel verso giusto perché la sua formulazione ingenua suggerisce il contrario. Non significa che una affermazione sbagliata resti in piedi: significa che resta leggibile insieme a quella che la corregge, cosicché chi legge veda non soltanto la conclusione giusta ma anche come ci si è arrivati e che cosa si era creduto prima. Un registro che si corregge in silenzio racconta un lavoro senza errori, che non è mai esistito, e chi lo eredita ripete gli errori che nessuno ha scritto.

La regola ha però un difetto, e la sua correzione è l'indice qui sotto. In un registro che cresce in avanti, una voce superata non sa di esserlo: chi legge la voce vecchia e si ferma là non ha modo di sapere che una voce successiva la smentisce. Aggiungere un rimando dentro la voce vecchia sarebbe una riscrittura; aggiungere un indice a parte non lo è, ed è quindi la forma compatibile con la regola. L'indice va aggiornato ogni volta che una voce ne supera una precedente, e questo è parte della convenzione e non un lavoro facoltativo.

### Indice delle voci superate

| Voce superata | Superata da | Su che cosa |
|---|---|---|
| - | - | nessuna, finché non accade |

## Forma di una voce

Quanto segue è il modello da copiare, non una voce reale. Si tolgono le parentesi angolari insieme al testo che contengono.

### MS-001 - &lt;titolo che dichiara il fatto e non l'intenzione&gt;

Perimetro: &lt;i file o i sistemi toccati, con precisione sufficiente a rifare il lavoro&gt;.

Legame con il progetto: &lt;a quale fase o obiettivo serve, e che cosa dipende da questo intervento; se non serve alcuna fase, dirlo&gt;.

&lt;Il corpo della voce: che cosa è stato fatto e perché in quella forma e non in un'altra. Qui vanno gli errori commessi con la loro causa, le inferenze poi smentite ritirate esplicitamente, e i comandi eseguiti con il loro output reale quando l'output insegna qualcosa.&gt;

Verificato con: &lt;il comando, la lettura o l'osservazione che prova l'esito, con il risultato osservato e non atteso&gt;.

Esito: &lt;fatto, bloccato con la dipendenza dichiarata, oppure aperto&gt;.
