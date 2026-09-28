# Interfacce che non somigliano al default di un modello

> Regola modulare del pacchetto `anti-slop`, da istanziare sotto `.claude/rules/` nei progetti che hanno un frontend o producono pagine HTML. Vale ogni volta che l'agente genera o modifica un'interfaccia. Il catalogo dei tratti, con il perché e le fonti, sta nella guida `docs/anti-slop/GUIDA.md`; qui c'è ciò che si fa.

## Il principio

Senza indicazioni un modello converge sulle scelte più frequenti nel materiale da cui ha imparato, e il risultato ha un aspetto riconoscibile che la documentazione del fornitore stesso chiama estetica "AI slop" [F07]. Nessuno di quei tratti è sbagliato in sé. Il difetto è che arrivano per inerzia, senza una ragione legata al prodotto, e chi guarda la pagina lo percepisce anche senza saperlo nominare. La regola quindi non vieta un colore o un carattere: chiede che ogni scelta visiva abbia una ragione scritta, e che i default elencati sotto non compaiano senza.

## Che cosa non si fa senza una ragione scritta

La palette di sfondo crema, testo quasi nero e accento ambra, arancio o terracotta, che la skill di Anthropic cita con i suoi valori tipici [F06]. I caratteri Inter, Roboto, Arial e Space Grotesk come scelta principale, e i serif da titolo che le fonti indicano come preferiti dai modelli [F07] [F08]. Una sola parola del titolo in corsivo o in grassetto [F06]. Un'etichetta maiuscola spaziata sopra ogni titolo: se ne usa al massimo una ogni tre sezioni, e solo dove orienta [F06] [F08]. La sezione "come funziona" in tre passi numerati, e la fila di tre card identiche [F08]. Card dentro card, e un unico raggio e un'unica ombra su tutto a prescindere dalla gerarchia [F06]. Le icone di repertorio al posto di un'informazione, e le icone senza etichetta visibile [F09]. Elementi decorativi che non rispondono a una domanda dell'utente, come la finta finestra di terminale in un prodotto che non ha una riga di comando. La stessa struttura ripetuta in ogni sezione, quando il contenuto delle sezioni è diverso [F07].

La ragione, quando c'è, si scrive nella documentazione di design del progetto o nella scheda `context/design-and-security.md`: "sfondo crema perché è il colore del marchio dal 2019" è una ragione, "sembra pulito" no.

## Che cosa si fa invece

Si parte dal contenuto e dal marchio, non dal componente. La gerarchia si costruisce con dimensione, peso e spazio prima che con bordi e contenitori: per separare due elementi si prova prima lo spazio, poi uno sfondo diverso, poi un'ombra leggera, uno strumento alla volta [F11]. Le card si usano per una collezione di elementi eterogenei, e un livello basta; per elementi omogenei servono meglio una lista o una tabella [F10]. Un'icona si tiene se aggiunge qualcosa al testo accanto, e con l'etichetta visibile [F09]. Il numero dei passi, delle card e delle colonne è quello del contenuto.

## Il vincolo che non ammette eccezioni

Il testo rispetta il contrasto minimo di 4,5:1 sul proprio sfondo, 3:1 se è testo grande, secondo il criterio WCAG 1.4.3 [F12]. È l'unico punto normativo di questa regola, e l'accento ambra è il caso in cui si viola più spesso: il testo bianco su `#f59e0b` sta intorno a 2,15:1.

## Il presidio

Prima di consegnare un'interfaccia si esegue lo strumento del pacchetto sui file cambiati, e si rilegge ogni segnalazione.

```
python tools/lint-ui.py <cartella del frontend>
```

Lo strumento legge i sorgenti e non il rendering, e segnala scelte da motivare, non errori, salvo il contrasto. Una segnalazione si chiude in due modi: cambiando la scelta, o scrivendone la ragione. Chiuderla ignorandola è ciò che la regola esiste per impedire. Le sigle fra parentesi quadre rimandano a `docs/anti-slop/FONTI.md`.
