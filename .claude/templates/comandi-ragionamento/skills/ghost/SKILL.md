---
name: ghost
description: Scrive un testo che si legge come scritto da una persona, senza i segni tipici del testo generato.
argument-hint: "[su che cosa applicarlo]"
disable-model-invocation: true
---

# Scrittura senza segni

Scrivi o riscrivi il testo di `$ARGUMENTS` evitando i segni con cui si riconosce un testo generato, che sono elencati nella sezione «I segni del testo generato» di `.claude/rules/interaction-style.md`: l'autorità senza nome, il parallelismo negativo, il gruppo di tre per abitudine, le frasi tutte della stessa misura, il gergo da chat, le parole di maniera.

Lavora sul contenuto prima che sulla forma: una frase vaga non migliora cambiandone le parole, migliora dicendo la cosa precisa. Conserva la voce e il registro del testo di partenza, se c'è.

Dove il progetto ha istanziato il pacchetto `anti-slop`, passa il risultato a `tools/lint-prosa.py` e correggi a mano ciò che segnala.

Lo scopo è un testo migliore, non ingannare qualcuno sull'origine: se a chi legge è dovuta la trasparenza sull'uso di un modello, il comando non la toglie.

Se dopo il comando non c'è testo, l'oggetto è l'ultima cosa di cui si stava parlando: il piano, la proposta, il codice o il documento appena prodotti. Se non è chiaro quale, lo si chiede in una riga prima di cominciare.
