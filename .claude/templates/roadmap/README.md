# roadmap

> Pacchetto opzionale. La lista di che cosa resta da fare, rigenerata dallo stato corrente invece che tenuta a mano, con una resa pronta da stampare. Istanziazione e razionale.

## Il problema che risolve

In un progetto che vive per mesi la domanda "che cosa resta da fare" non ha quasi mai una risposta sola. La risposta sta sparsa fra il registro cronologico, che racconta che cosa è successo, il registro delle decisioni, che racconta perché, il punto di ripresa, che racconta dove si era arrivati, e una eventuale mappa dello stato, che è l'unico dei quattro a provarci davvero. Sono tutti documenti scritti a mano, quindi hanno tutti lo stesso destino: invecchiano in silenzio, perché chi chiude un lavoro non rilegge il documento che lo dichiarava aperto.

Il difetto non è ipotetico ed è misurabile. Nel progetto da cui questo pacchetto è stato estratto, un difetto tipografico è rimasto elencato fra i difetti noti aperti in due file di memoria per due mesi e mezzo dopo essere diventato inapplicabile, perché il testo che lo conteneva era stato spostato in un altro repository. Nessuno aveva sbagliato a scrivere: semplicemente la lista non aveva alcun modo di accorgersi che il mondo era cambiato sotto di essa.

La risposta è la stessa che il sistema adotta altrove per gli artefatti generati, cioè separare ciò che una macchina non può dedurre da ciò che deve misurare a ogni esecuzione. Il giudizio umano, quale lavoro resta e perché, vive in un file dati versionato. Lo stato, cioè il commit di riferimento, la distanza delle schede da HEAD, l'esito dei controlli e la raggiungibilità dei link, non vive da nessuna parte: si misura quando serve.

## Che cosa istanzia

Tre file, nessuna dipendenza oltre a Python, PyYAML e git.

```
templates/roadmap/tools/roadmap.py                 in  tools/roadmap.py
templates/roadmap/tools/roadmap-items.example.yml  in  tools/roadmap-items.yml
templates/roadmap/skills/roadmap/SKILL.md          in  .claude/skills/roadmap/SKILL.md
```

Lo strumento non conosce il progetto che lo ospita: i controlli da eseguire, il comando di verifica dei link e la cartella delle schede si dichiarano nel file dati, e lo strumento si limita a eseguirli e a leggerne il codice di uscita. Un progetto che non dichiara nulla ottiene la sola lista delle voci, che è già il novanta per cento del valore.

L'unico adattamento obbligatorio è il file dati: si copia l'esempio, si scrive il titolo, si dichiarano i controlli che il progetto ha davvero, e si sostituiscono le due voci di esempio con quelle vere. La skill si istanzia com'è, salvo il percorso dei derivati se il progetto non usa `build/`.

## Le due idee che lo rendono utile

La prima è l'ordinamento per costo e non per importanza. I quattro livelli vanno dal lavoro che si chiude in minuti senza decidere niente a quello che non si chiude affatto dentro questo repository. Una lista ordinata per gravità si legge e non si usa, perché la prima voce richiede una settimana; una lista ordinata per costo si apre in cima e si chiude qualcosa, e quello che resta in fondo resta lì con la sua ragione dichiarata invece che per dimenticanza.

La seconda sono le sonde, ed è la parte che impedisce alla lista di mentire. Una voce può dichiarare come la macchina stabilisce da sola se è ancora aperta: la presenza o l'assenza di una stringa in un file, oppure l'esito di uno dei controlli dichiarati. Le voci che una sonda smentisce finiscono in una sezione a parte, "chiuse dalla misura", invece di sparire: sparire sarebbe una decisione, e la decisione di togliere una voce dal file dati resta di chi conferma che il lavoro è davvero finito.

Il limite va dichiarato perché è strutturale e nessuna quantità di codice lo toglie. Una sonda copre soltanto il lavoro che ha una traccia testuale, e la maggior parte del lavoro non ce l'ha: una traduzione mancante, una decisione sospesa, una pagina da riscrivere non lasciano una stringa che sparisce. La sonda si mette dove il difetto è meccanico, cioè esattamente dove una lista tenuta a mano resta sbagliata più a lungo, perché un difetto meccanico è anche quello che nessuno rilegge.

## Come si usa

```
python tools/roadmap.py                        # riepilogo a schermo
python tools/roadmap.py --link-check           # aggiunge la verifica dei link, va in rete
python tools/roadmap.py --format md --write    # Markdown nella cartella dei derivati
python tools/roadmap.py --format html --write  # pagina da stampare
python tools/roadmap.py --format json          # stato ispezionabile, per un altro strumento
python tools/roadmap.py --check                # exit 1 se resta aperta una voce di livello 0
```

La resa HTML è pensata per la carta: A4, serif, margini di quattordici millimetri, nessuna voce spezzata fra due pagine, link non sottolineati in stampa. Si apre nel browser e si stampa con la funzione di stampa, che legge il foglio di stile dedicato. L'uscita vive nella cartella dei derivati, che è ignorata da git: è un artefatto e si rigenera, non si versiona, ed è la ragione per cui questo pacchetto non scrive mai in un file tracciato.

La forma `--check` esiste per un hook o per un controllo prima di un commit: fallisce finché resta aperto del lavoro che costa minuti, che è la soglia sotto la quale non c'è una scusa.

## Quando non offrirlo

Non si offre a un progetto breve, dove l'elenco delle cose da fare sta nella testa di chi lo scrive e un file in più è solo un file in più. Non si offre a un progetto che non ha ancora un registro cronologico e un punto di ripresa, perché il valore di questo pacchetto sta nel non duplicarli e in un progetto senza memoria non c'è niente da non duplicare: lì la domanda precedente è se servano quelli.

Va invece distinto da `timeline-progetto`, con cui è complementare e non alternativo. Quella guarda indietro e racconta la storia tecnica di ciò che è stato fatto, generandola dalle stesse fonti di memoria; questo guarda avanti e dice che cosa manca, prendendolo da un file che quelle fonti non contengono. Un progetto può volerli entrambi, e nessuno dei due legge l'altro.

## Rapporto con gli altri controlli

Non sostituisce nessuno dei controlli che esegue: li raccoglie. Un progetto che ha già `sync-context`, `alignment` o una batteria di controlli in un hook continua a usarli come prima, e questo pacchetto ne mostra l'esito accanto al lavoro che resta, così che la domanda "che cosa faccio adesso" trovi in un posto solo sia i difetti di convenzione sia le voci di merito. La differenza di ruolo è netta e vale enunciarla: quei controlli dicono se qualcosa è rotto adesso, questo dice che cosa non è stato ancora fatto, e le due cose non si deducono l'una dall'altra.

## Provenienza

Estratto il 2026-09-22 da un progetto istanziato da questo template, dove è nato da una richiesta diretta dell'utente, cioè avere una lista pulita e puntuale di che cosa fare in ogni punto del progetto, e dalla constatazione immediata che una lista scritta quel giorno sarebbe stata falsa entro la settimana. La generalizzazione ha richiesto una sola modifica sostanziale rispetto alla prima versione, cioè rendere dichiarativi i controlli invece di chiamare per nome gli strumenti di quel progetto, più il rilievo che un comando di shell invocato da Python su Windows non risolve la shell che si crede: la prima versione chiamava `bash` e otteneva quella di WSL, con percorsi e interprete diversi da quelli di Git Bash, e la verifica dei link tornava silenziosamente a zero invece di fallire.
