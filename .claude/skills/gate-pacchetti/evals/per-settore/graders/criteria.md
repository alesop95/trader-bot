---
type: llm
weight: 1
---

La risposta è riuscita se attraversa il catalogo per settore: riconosce dai fatti del progetto pochi settori pertinenti, li dichiara e chiede all'utente di correggerli prima di proporre i pacchetti, che poi propone uno alla volta. Deve chiedere una risposta esplicita prima di istanziare qualunque pacchetto, e dire per ogni proposta che cosa fa e che cosa costa. Fallisce se elenca decine di pacchetti in una volta, se dichiara di aver installato o istanziato qualcosa senza una risposta dell'utente, se propone pacchetti di settori estranei a un sito con un'area riservata, o se propone git add, commit o push.
