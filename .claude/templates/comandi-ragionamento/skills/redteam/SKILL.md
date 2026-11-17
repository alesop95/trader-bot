---
name: redteam
description: Prova a rompere un piano, un codice o un documento: casi limite, punti ciechi, modi di abusarne.
argument-hint: "[su che cosa applicarlo]"
disable-model-invocation: true
---

# Squadra rossa

Mettiti dalla parte di chi vuole che l'oggetto di `$ARGUMENTS` fallisca, per errore o di proposito, e cerca dove cede.

Guarda in quest'ordine: gli ingressi che nessuno ha previsto (vuoto, enorme, malformato, duplicato, fuori ordine), gli stati intermedi (interruzione a metà, due esecuzioni insieme, ripetizione), le dipendenze (assenti, lente, che rispondono il falso), i permessi e i dati che escono, e chi può usarlo in un modo che l'autore non voleva.

Per ogni cedimento scrivi l'ingresso o lo stato concreto che lo produce e l'effetto, non una categoria. Un cedimento che non sai riprodurre lo dichiari come sospetto.

Ordina per danno e dai la correzione più piccola per i primi tre. Sul codice del progetto, dove una prova automatica può dimostrare il cedimento, proponila, e ricorda che la norma sulle prove sta nella skill `prove-che-misurano`.

Questo comando attacca il lavoro proprio, su sistemi propri: non è un mandato per provare sistemi di altri.

Se dopo il comando non c'è testo, l'oggetto è l'ultima cosa di cui si stava parlando: il piano, la proposta, il codice o il documento appena prodotti. Se non è chiaro quale, lo si chiede in una riga prima di cominciare.
