# gancio-globale

<!-- readme-summary: un presidio pre-commit valido per ogni repository della macchina, compresi quelli che non esistono ancora, con core.hooksPath globale invece di un'installazione per progetto -->

> **Valori della macchina che lo ha prodotto:** nessuno. Questo pacchetto non contiene percorsi, alias, nomi di chiave né identità: usa soltanto `$HOME` e due file che la macchina ricevente crea per sé. È una scelta deliberata, perché il difetto che il pacchetto esiste per prevenire è esattamente un file di configurazione che descriveva una macchina e che è stato copiato su altre.

Un presidio pre-commit che vale per **ogni repository della macchina**, compresi quelli che non esistono ancora, attivato una volta sola e senza alcuna installazione per progetto.

## Il problema che risolve

Un hook git vive in `.git/hooks`, che non è versionato e non si propaga. La risposta consueta è versionare gli hook in `.githooks/` e far impostare a ogni progetto `core.hooksPath`. Funziona, e ha un difetto che si vede solo contando: **l'installazione resta un gesto per progetto**, quindi la copertura è sempre parziale e manca proprio dove serve, cioè nei repository nati dopo che la regola è stata scritta.

Il caso che ha prodotto questo pacchetto, in un progetto istanziato: un controllo che impediva a un'identità di finire nei file versionati esisteva da sei giorni, era corretto, era documentato, ed era installato in **sei repository su cinquantacinque**. In uno dei quarantanove scoperti un dato che quel controllo avrebbe fermato stava, già pubblicato, da quattro mesi. Non era mancata la regola: era mancata l'installazione, quarantanove volte, in silenzio.

## Il meccanismo

`core.hooksPath` si può impostare **nella configurazione globale**, e allora vale per ogni repository che non ne dichiari una propria. È una riga, e da quel momento non c'è più niente da installare da nessuna parte.

```sh
mkdir -p ~/.githooks
cp templates/gancio-globale/hooks/pre-commit ~/.githooks/pre-commit
chmod +x ~/.githooks/pre-commit
git config --global core.hooksPath ~/.githooks
```

Si annulla con `git config --global --unset core.hooksPath`, e nessun repository se ne accorge.

## Le tre cose da sapere prima di adottarlo

**Un `core.hooksPath` locale vince su quello globale.** Non è un difetto: è la precedenza normale della configurazione git, ed è quella che permette a un progetto di avere una catena di hook propria. La conseguenza pratica, però, è che i repository con hook propri **non ricevono** il gancio globale, e sono proprio i più curati. Si collegano aggiungendo in fondo al loro `pre-commit` una riga che delega, e che resta allineata da sola perché non duplica niente:

```sh
"$HOME/.githooks/pre-commit" || exit 1
```

Vale identica per un progetto che usa husky, dove il file è `.husky/pre-commit`.

**Gira su ogni commit di ogni repository della macchina**, compresi quelli usa e getta e quelli di altri. Deve quindi essere veloce, non avere stato, non scrivere nulla e non aprire connessioni; e deve essere *difensivo*, cioè lasciar passare quando non può lavorare invece di bloccare. Il modello qui accanto esce con 0 se non trova git o l'interprete: la scelta opposta renderebbe impossibile committare su una macchina mal configurata, che è un modo sicuro di far disattivare il presidio a chi lo subisce.

**Il controllo che il gancio invoca va cercato in un posto solo.** Se ogni progetto ne ha una copia, il gancio ne eseguirà una diversa a ogni repository, e la più vecchia guarderà meno cose di quante creda chi la lancia. Il modello cerca prima la copia del template, il cui percorso legge da `~/.config/template-claude-path.txt` - un file della macchina, creato da chi installa, contenente una riga sola - e solo come ripiego quella del progetto.

## Che cosa ci si attacca

Il modello invoca `test-identita-personali.py --stage`, ma il pacchetto non riguarda quel controllo: riguarda **il modo di renderne universale uno qualunque**. Ci si attacca bene tutto ciò che è veloce, deterministico, in sola lettura e con un codice di uscita: ricerca di credenziali, dati identificanti, convenzioni sui messaggi, dimensione dei file. Non ci si attacca nulla che richieda rete, che impieghi secondi, o che possa cambiare i file in stage: un hook che modifica ciò che stai per committare produce commit che nessuno ha scritto.

Sul codice di uscita vale una distinzione che conviene adottare anche altrove: **0 vuol dire ho guardato e va bene, 1 ho guardato e ho trovato, 2 non ho potuto guardare.** Il terzo caso non è un successo, e un presidio che lo tratta come tale si dichiara verde proprio nelle condizioni in cui è cieco. Il modello traduce il 2 in un rifiuto con un messaggio che dice che cosa manca.

## Prova che è attivo

La verifica non è leggere la configurazione, è vedere il gancio rifiutare. In una cartella usa e getta:

```sh
git init prova && cd prova
git config --local user.email "prova@esempio.invalid"
git config --local user.name "Prova"
printf 'contenuto che il controllo deve respingere\n' > x.txt
git add x.txt
git commit -m prova     # deve fermarsi, e dire perché
```

Se passa, il gancio non sta girando: controlla che `core.hooksPath` sia impostato a livello globale, che il file sia eseguibile, e che il repository di prova non abbia un `core.hooksPath` proprio.
