---
name: prove-che-misurano
description: >
  Stabilisce se una prova automatica misuri davvero il difetto che dice di misurare, invece
  di essere verde perché non lo esercita. Si carica quando si scrive o si valuta un test,
  quando si chiude un difetto e si aggiunge la prova che lo copre, quando una verifica
  manuale smentisce una suite verde, quando si sta per aggiungere una guardia o
  un'esclusione a uno strumento, quando si scrive una sequenza di verifica manuale, e
  quando si sta per dichiarare completo un intervento il cui scopo era un effetto
  misurabile. Copre anche il caso in cui una decisione dipenda da una proprietà dei dati
  reali, che nessuna prova su dati costruiti può vedere. Non prescrive framework né
  linguaggi.
---

## Che cosa fa questa skill

La norma sta per intero in `RIFERIMENTO.md`, accanto a questo file, e va letta prima di operare: qui c'è solo la porta d'ingresso, non il contenuto. La norma raccoglie le forme, tutte osservate in progetti istanziati da questo template e nessuna dedotta, in cui una prova passa senza misurare niente, e stabilisce il controllo che le distingue.

La domanda che la norma pone, e che va posta prima di considerare chiusa una correzione, è una sola: se il difetto tornasse, questa prova cadrebbe?

## Quando si carica

Si carica scrivendo o valutando una prova, chiudendo un difetto, e in cinque momenti in cui il rischio è alto e non sembra: quando una verifica manuale trova un difetto che la suite non aveva visto, perché quello è un difetto della suite oltre che del codice; quando si aggiunge una guardia, un'esclusione o un elenco di eccezioni, perché vale per loro la stessa domanda che si pone a una prova; quando si scrive una sequenza di verifica manuale, perché il passo che porta l'informazione va marcato o verrà saltato; quando si sta per dichiarare completo un intervento il cui scopo era ridurre un costo o un tempo, perché senza misura prima e dopo la parola completo toglie a chiunque il motivo di tornare a controllare; e quando una decisione dipende da quanti record reali abbiano un certo campo, perché quella è una misura e non una prova.

## Procedura minima

Si legge `RIFERIMENTO.md`, si individua la sezione che corrisponde al caso in mano, e si applica il controllo che descrive. Il controllo centrale, la verifica di non vacuità, si esegue così: scritta la correzione e la sua prova, si rimette il difetto nel codice, si esegue la suite, si osserva quali prove cadono, poi si ripristina il file e si verifica il ripristino con uno strumento invece che a memoria. Se non cade niente, la prova è vacua e va riscritta prima di andare avanti.

La copia da cui ripristinare deve esistere prima della prima mutazione, e va verificata invece che presunta: una sequenza di mutazioni che fallisce la copia in silenzio somma i difetti nel file e rende inutili tutti i risultati successivi al primo.

## Vincoli

La skill è di sola lettura sul giudizio: non decide da sé che una prova sia sufficiente, applica il controllo e riporta l'esito. Non esegue `git add`, commit o push, che restano manuali dell'utente secondo `git-commands-format.md`. Ciò che si misura si scrive su disco nello stesso giro di lavoro, secondo `chat-non-e-memoria.md`, con accanto il perimetro della misura.
