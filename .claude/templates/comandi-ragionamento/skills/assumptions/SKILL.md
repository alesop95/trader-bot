---
name: assumptions
description: Tira fuori le assunzioni nascoste di un piano e segnala quelle che più probabilmente sono false.
argument-hint: "[su che cosa applicarlo]"
disable-model-invocation: true
---

# Assunzioni nascoste

Elenca ciò che l'oggetto di `$ARGUMENTS` dà per vero senza dirlo: sull'ambiente, sui dati, sulle persone, sui tempi, sui volumi, su ciò che un altro componente garantisce.

Per ciascuna scrivi da dove viene: verificata in questa sessione, letta in un file del progetto (quale), oppure soltanto supposta. Secondo `recupero-dei-fatti.md`, un'assunzione su com'è fatto il sistema si cerca prima nel repository.

Ordina per due criteri insieme: quanto è probabile che sia falsa, e quanto costa se lo è.

Per le prime tre indica la verifica più economica, cioè un comando, una domanda al proprietario o una lettura, e fermati lì: non verificare tutto senza che sia chiesto.

Se dopo il comando non c'è testo, l'oggetto è l'ultima cosa di cui si stava parlando: il piano, la proposta, il codice o il documento appena prodotti. Se non è chiaro quale, lo si chiede in una riga prima di cominciare.
