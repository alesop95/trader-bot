# Bonifica della storia di un repository già pubblicato

<!-- readme-summary: la procedura completa per togliere un dato dalla storia di un repository già pubblicato, dalla ricognizione al biglietto all'assistenza -->

> **Valori della macchina che lo ha prodotto:** nessuno. Percorsi, alias e nomi di repository sono segnaposto fra parentesi angolari e vanno sostituiti con i propri.

Lo strumento del pacchetto trova un dato che non doveva entrare. Questo documento dice che cosa fare **dopo**, quando quel dato è già stato pubblicato: a quel punto toglierlo dai file è il primo passo di cinque, e da solo non ottiene niente.

## Quando si fa, e quando non si fa

Si riscrive una storia quando un dato è finito **dove il suo proprietario non ha scelto di pubblicarlo**: una credenziale, un percorso riservato, l'indirizzo di una persona dentro i repository di un'organizzazione, dati che identificano l'infrastruttura di terzi.

Non si riscrive per rendere uniforme a posteriori un'attribuzione legittima là dove sta, per esempio l'indirizzo con cui qualcuno ha scelto di firmare i propri commit nei propri repository. La distinzione non è fra dato segreto e dato pubblico: è fra un dato che sta nel posto sbagliato e uno che sta nel posto giusto e non piace più.

Il criterio va scritto e non lasciato al buon senso, perché il costo è asimmetrico. Ogni repository bonificato richiede una riscrittura, un push forzato e un biglietto all'assistenza, e non raggiunge comunque i fork e i cloni già fatti. Applicato per uniformità a decine di repository è un lavoro che nessuno finisce; applicato al caso giusto su pochi è un pomeriggio.

## 1. Ricognizione, su tre superfici

Una ricerca copre solo la superficie che interroga, e dichiarare pulito un repository avendone guardata una sola è un errore di metodo, non una svista. Le superfici sono tre, più i tag, e si guardano tutte.

```sh
git log --all -S '<stringa>' --oneline
git log --all --format=%B | grep -i '<stringa>'
git log --all --name-only --format= | sort -u | grep -i '<stringa>'
git tag -l -n99 | grep -i '<stringa>'
```

Prima di tutto, però, si stabilisce **se il repository è pubblico**, perché cambia la gravità di tutto il resto.

```sh
gh repo view <owner>/<repo> --json visibility -q .visibility
```

E si elencano **tutti** gli URL di push di tutti i remoti, non il solo `origin` di fetch: un repository può spingere su più destinazioni, e una bonifica che ne tratta una sola lascia la storia vecchia viva sull'altra.

```sh
git remote -v
git remote get-url --push --all origin
```

## 2. Una copia, fuori dalla cartella che si sta per riscrivere

```sh
git clone --mirror <percorso del repository> <percorso di una copia, su un altro disco>
```

Serve finché l'assistenza non ha risposto. Poi va cancellata, e non per lo spazio: quella copia è l'ultimo posto in cui il dato che si sta togliendo continua a esistere.

## 3. La riscrittura

Due forme, a seconda che il file vada tolto o soltanto corretto.

**Il file intero non deve esistere**, tipico di un documento di configurazione finito lì per sbaglio:

```sh
python <percorso di>/git_filter_repo.py --path '<percorso/del/file>' --invert-paths --force
```

**Il file serve, il dato no**, tipico di un registro o di una documentazione. Il file delle sostituzioni ha una regola per riga, nella forma `cercato==>sostituto`, e **non ammette righe di commento**:

```sh
python <percorso di>/git_filter_repo.py --replace-text <file delle sostituzioni> --force
```

I **messaggi di commit** si riscrivono con `--message-callback`, l'**autore** con `--mailmap`.

Se la bonifica finirà con una richiesta all'assistenza, la riscrittura va fatta con il flag `--sensitive-data-removal`, disponibile da `git-filter-repo` 2.47: è quello che produce il rapporto `NOTE: First Changed Commit(s)` e l'elenco degli oggetti LFS resi orfani, cioè esattamente i dati che la richiesta deve contenere. Senza quel flag vanno ricostruiti dopo, e se il clone usato per la riscrittura non esiste più non si ricostruiscono affatto.

Tre cose che sorprendono ogni volta:

- `filter-repo` **rimuove il remoto** `origin`, e lo dice in una riga che si legge dopo. Va riaggiunto prima di spingere.
- Il ramo può chiamarsi `master` e non `main`: il push fallisce con `src refspec main does not match any`, e la risposta è guardare `git branch`.
- Senza `--set-upstream` il ramo resta scollegato, e il push successivo si lamenta che non esiste un upstream.

```sh
git remote add origin git@<alias>:<owner>/<repo>.git
git push --force --set-upstream origin <ramo>
git push --force --tags
```

Su Windows `filter-repo` può ripetere all'infinito «Deletion of directory … failed. Should I try again?» su cartelle **già vuote**, perché l'antivirus o l'indicizzatore le tengono aperte un istante. Si risponde `n`: la riscrittura è già completa, e ciò che resta è spazzatura sul disco che un `git gc --prune=now` toglie più tardi.

## 4. Verifica, prima di dichiarare chiuso

Le stesse ricerche del punto 1, più l'allineamento con il remoto: i due comandi devono dare lo stesso oggetto.

```sh
git rev-parse HEAD
git ls-remote origin <ramo>
```

Se la bonifica riguardava un'identità, si controlla anche chi firma:

```sh
git log --all --format='%an <%ae>' | sort -u
```

## 5. Il biglietto all'assistenza, il passo che quasi tutti saltano

**Una riscrittura spinta non cancella niente dal lato della piattaforma.** I vecchi oggetti restano raggiungibili per SHA e nelle viste in cache, e i riferimenti delle pull request, `refs/pull/*`, sono un namespace **in sola lettura dal lato git**: quelli non li tocca nessuna riscrittura, per costruzione. Senza questa richiesta la bonifica è apparente.

**Il criterio con cui l'assistenza decide non è la gravità apparente.** La documentazione lo dichiara: interviene solo quando il rischio **non può essere mitigato ruotando le credenziali esposte**, e il canale alternativo, la politica di rimozione delle informazioni private, si descrive come servizio eccezionale per contenuti ad alto rischio. Ne discende una cosa da sapere prima di scrivere: per una credenziale la richiesta ha buone probabilità, per un indirizzo di posta o un percorso interno può essere respinta nel merito, e su un piano senza assistenza inclusa viene chiusa da un assistente automatico prima ancora di essere letta. Si risponde nel thread dicendo che non è assistenza tecnica ma il passo finale della procedura documentata dalla piattaforma, e si chiede l'instradamento giusto. Se la risposta resta no, lo stato raggiunto dalla sola riscrittura non è poco: i vecchi commit non sono più raggiungibili da alcun ramo, tag o pull request, e restano accessibili solo a chi conosca già lo SHA esatto.

Il percorso nel modulo di contatto, che non è ovvio:

1. **Verificare con quale account si è collegati.** Una richiesta vale per l'account che la manda: per i repository di un'organizzazione serve un'utenza che vi abbia i permessi, e alla pagina di scelta dell'account si seleziona **l'organizzazione**, non l'utenza personale.
2. *What do you need help with?* → **Repositories**.
3. *What can we help you with?* → **Repository features**, poi *Which repository features* → **Branches**. **Non** `Deletes`: quella voce apre un modulo sulla cancellazione del repository intero, con il campo dell'URL «da cancellare» e una conferma irreversibile. È la cosa sbagliata, e sembra quella giusta.
4. *URL del repository*: il campo ne accetta **uno**, gli altri si elencano nel corpo.
5. *Continue to create a ticket*, e **non** *Start a discussion*, che aprirebbe un thread pubblico con l'elenco dei repository e la ragione della bonifica.
6. *Type of Issue* → **General question or feature request**. L'altra voce è per errori, limiti dell'API e Actions.
7. Dopo l'invio, **aprire il biglietto e verificare che il corpo sia arrivato intero**: i moduli a più passaggi a volte troncano. Se fosse vuoto, una risposta nello stesso thread vale quanto il messaggio iniziale.

Il testo, da adattare:

```text
Subject: Purge cached views and unreachable objects after history rewrite

Hello,

we rewrote the history of the following repositories to remove content that
was committed by mistake:

  <owner>/<repo>
  ...

All branches and tags have been force-pushed and the current history is clean.
The old commits are no longer referenced by any branch or tag, but they are
still reachable by SHA.

Please dereference and garbage-collect the unreachable objects in these
repositories, and remove the cached views, so that the old commits are no
longer accessible by SHA or through the web interface. Please include any
pull request refs (refs/pull/*) if present.

Thank you.
```

Se un repository ha pull request aperte agganciate a vecchie teste di ramo, l'assistenza può chiedere di chiuderle prima: conviene verificarlo e dirlo nel biglietto invece di aspettare la domanda.

## 6. Il messaggio di commit non racconta la bonifica

Un messaggio di commit è contenuto pubblico quanto il codice. «Rimuove l'indirizzo X dalla documentazione» è un cartello che indica dove scavare nei commit precedenti, e per giunta ripubblica in chiaro, nel messaggio, il dato appena tolto dai file. Si descrive che cosa fa la modifica, non che cosa si stava togliendo.

## 7. Che cosa questa procedura non ottiene

I fork esistenti, i cloni già fatti e le cache di terzi non sono raggiungibili da nessuna richiesta. Se il dato era una credenziale, **la bonifica non la mette al sicuro: la si revoca e la si sostituisce**, e la riscrittura serve solo a non ripubblicarla. Per tutto il resto, riscrittura più biglietto sono il massimo ottenibile ed è ragionevole; ma è un massimo, non una garanzia, e la conclusione operativa è che un controllo prima del commit vale più di qualunque bonifica dopo.
