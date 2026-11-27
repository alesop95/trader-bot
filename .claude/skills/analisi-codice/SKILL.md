---
name: analisi-codice
description: >
  Quando l'utente chiede a che cosa serve un oggetto di un sistema software (un campo, un metodo,
  un gruppo, una regola di accesso, una vista), perché un utente vede o non vede qualcosa, o dove
  è usata una cosa nel codice, conduce un'analisi d'impatto su più livelli: scarica i repository
  che compongono il sistema, mappa ogni occorrenza dei termini con link permanente a riga e commit
  introduttivo, scrive un'analisi tecnica e operativa per livelli (dati, logica, sicurezza,
  interfaccia) con difetti e commit, e genera pagine con il design system del progetto e sezioni
  comprimibili. Una ricerca per domanda, in ricerche/<nome>.
---

# Analisi del codice su più livelli

Il pacchetto è `.claude/templates/analisi-codice/`: il suo `README.md` spiega strumenti, configurazione e limiti, e va letto alla prima ricerca del progetto. Gli strumenti si lanciano dalla radice del progetto per percorso, senza copiarli; qui sotto `T` sta per `.claude/templates/analisi-codice/tools`.

## Prima ricerca del progetto

Si scrive `analisi-codice.json` nella radice dal modello `analisi-codice.esempio.json`, ricavando composizione e repository dal sistema reale e non a memoria: se il sistema si costruisce da un Dockerfile, quello è il file di composizione. Si aggiunge `sorgenti/` a `.gitignore`, perché contiene codice di altri. Si dichiara il design system in `_notes/.tema.txt`, con il percorso che le istruzioni di account o di progetto indicano. Poi si scaricano i sorgenti con `python T/sorgenti.py`, aggiungendo `--con` per le famiglie facoltative che la domanda tocca, e si legge il riepilogo: i repository non accessibili restano fuori dal perimetro e l'analisi lo dichiara.

## Il ciclo di una ricerca

Si apre la ricerca con `python T/ricerca.py nuova <nome> --titolo "..." --domanda "..." --termini a,b,c`, dove i termini sono i nomi tecnici: campi, metodi, id XML di regole, gruppi e viste, nomi di tabella. Si produce la mappa con `python T/ricerca.py mappa <nome>` e la si legge riga per riga, non solo nei totali. I termini collegati che la mappa suggerisce in fondo si aggiungono a `ricerca.json` se rilevanti, e si rigenera la mappa finché non emergono simboli nuovi. Per ogni termine si scrive in `ricerca.json`, nella chiave `impatti`, che cosa cambia per chi usa il sistema: la mappa lo mostra in un riquadro sopra le occorrenze del termine, e senza di esso la pagina non si genera.

Si scrive `analisi.md` partendo dal codice letto, non dalla mappa sola. La mappa non è una pagina a sé: entra nella pagina dell'analisi come sezione «Mappa delle occorrenze», prima delle Note. L'analisi ha sempre queste parti, ciascuna come titolo `##`: risposta alla domanda, impatto operativo con chi è toccato, che cosa vede o può fare e da quale riga viene, perimetro con i commit dei sorgenti, architettura per livelli con un `###` per livello, flussi con i diritti con cui gira ogni passo, tutti gli usi degli oggetti coinvolti, difetti con un `###` per difetto e il commit che l'ha introdotto, storia dei commit, indicazioni operative, verifiche da fare sul sistema in esercizio, note con le sigle. Ogni affermazione sul codice porta il link a file e riga al commit del manifesto, preso dalla mappa; ogni difetto porta il commit dato da `git blame` sulla riga, non dal messaggio di commit; ciò che è dedotto dal codice e non osservato si scrive come tale.

Si chiude con `python T/ricerca.py genera <nome>`, che esegue i controlli e rifiuta di generare se uno fallisce: prosa su una riga per paragrafo, link verificati sui cloni locali (file presente, riga dentro il file, commit nella storia), trattini, accenti, segni del testo generato e giro chiuso fra testo e pagina. Poi rigenera l'indice delle ricerche e, se configurata, la cartella sul Desktop. La pagina `analisi.html` si consegna con il suo percorso.

## Che cosa non si fa

Non si afferma "compare solo in" senza dire su quali sorgenti si è cercato. Non si cita una riga senza il link fissato a un commit, perché un link al ramo cambia sotto chi lo legge. Non si apre il contenuto di chiavi, credenziali o file di accesso che i repository del sistema contengono: se ne dichiara la presenza nella sezione sulla sicurezza e basta.
