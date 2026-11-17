---
name: premortem
description: Dà per fallito il piano fra qualche mese e risale alle cause più probabili, prima di cominciare.
argument-hint: "[su che cosa applicarlo]"
disable-model-invocation: true
---

# Autopsia anticipata

Immagina che il piano di `$ARGUMENTS` sia stato attuato e che fra sei mesi sia fallito. Non chiederti se fallirà: è fallito, e va spiegato perché.

Scrivi le storie di fallimento più plausibili, da cinque a otto, ciascuna in due righe: che cosa è andato storto e quale segnale c'era già oggi. Copri cause diverse: tecniche, di tempo, di persone, di dipendenze esterne, di cose date per scontate.

Per ciascuna stima probabilità e danno a parole (alta, media, bassa) e di' se si può prevenire, attenuare o soltanto accorgersene presto.

Chiudi con le modifiche al piano che ne discendono, al massimo cinque, e con i segnali da sorvegliare. Se il progetto ha un registro delle pendenze, i segnali vanno lì.

Se dopo il comando non c'è testo, l'oggetto è l'ultima cosa di cui si stava parlando: il piano, la proposta, il codice o il documento appena prodotti. Se non è chiaro quale, lo si chiede in una riga prima di cominciare.
