---
description: >
  Rigenera la roadmap operativa del progetto allo stato corrente, fondendo le voci aperte di
  tools/roadmap-items.yml con lo stato misurato dal vivo (commit, distanza delle schede da HEAD,
  esito dei controlli dichiarati, raggiungibilita dei link). Produce anche una pagina pronta da
  stampare. Usare quando serve sapere che cosa resta da fare, a inizio sessione o prima di
  decidere su che cosa lavorare.
---

## Roadmap allo stato corrente

!`python tools/roadmap.py`

## Che cosa hai davanti

La lista qui sopra è un derivato, rigenerato a ogni invocazione, e nessuno la scrive a mano. Le voci, cioè il giudizio su quale lavoro resti e perché, vivono in `tools/roadmap-items.yml` ed è l'unico file che si modifica a mano. Tutto il resto, cioè il commit di riferimento, la distanza delle schede da HEAD, l'esito dei controlli che il progetto dichiara e la raggiungibilità dei link, viene misurato sul momento da `tools/roadmap.py`.

Le voci sono ordinate per costo crescente e non per importanza. Il livello 0 si chiude in minuti e non richiede alcuna decisione, il livello 1 richiede tempo ma nessuna decisione di contenuto, il livello 2 richiede una decisione dell'utente, il livello 3 è lavoro che non si chiude dentro questo repository e va portato in una sessione sul repository che lo ospita. La scelta dell'ordinamento è deliberata: una lista ordinata per gravità si legge e non si usa, perché la prima voce richiede una settimana.

La sezione finale, "chiuse dalla misura", elenca le voci che una sonda ha dichiarato non più aperte. Una sonda è un controllo automatico dichiarato nel file dati: la presenza o l'assenza di una stringa in un file, oppure l'esito di uno dei controlli. Serve a impedire che la lista dichiari aperto un lavoro già fatto. Una voce chiusa dalla misura non sparisce da sola: va tolta dal file dati quando qualcuno conferma che il lavoro è davvero finito, perché sparire sarebbe una decisione e la decisione resta di chi verifica.

Il limite da conoscere prima di fidarsi troppo delle sonde: coprono il solo lavoro che ha una traccia testuale. Una traduzione mancante, una decisione sospesa o una pagina da riscrivere non lasciano una stringa che sparisce, quindi restano aperte finché una persona non le chiude a mano.

## Come si usa

Per la sola lista a schermo basta questa skill. Per gli altri usi si invoca lo strumento direttamente.

```
python tools/roadmap.py                        # riepilogo a schermo, come qui sopra
python tools/roadmap.py --link-check           # aggiunge la verifica dei link dichiarata
python tools/roadmap.py --format md --write    # Markdown nella cartella dei derivati
python tools/roadmap.py --format html --write  # pagina da stampare
python tools/roadmap.py --format json          # stato ispezionabile, per un altro strumento
python tools/roadmap.py --check                # exit 1 se resta aperta una voce di livello 0
```

La verifica dei link è esclusa dall'esecuzione di default perché va in rete e costa tempo: si aggiunge con `--link-check` quando serve davvero. Il comando che la esegue è dichiarato nel file dati per piattaforma, e se il progetto non ne dichiara uno la riga corrispondente lo dice invece di tacere.

## Per stamparla

La resa HTML è pensata per la carta: A4, serif, margini di quattordici millimetri, nessuna voce spezzata a metà fra due pagine, link non sottolineati in stampa. Si genera con `python tools/roadmap.py --format html --write`, si apre il file che il comando nomina, e si stampa dal browser con la funzione di stampa, che legge il foglio di stile dedicato. Il file vive nella cartella dei derivati, ignorata da git: è un artefatto e si rigenera, non si versiona.

## Dove finisce questa lista e dove comincia la memoria

Questa skill non scrive in alcun file tracciato e non aggiorna le schede. Quando una voce viene davvero chiusa, le due cose da fare sono toglierla da `tools/roadmap-items.yml` e aggiornare a mano il documento di memoria che la citava. Vale la regola generale del sistema: l'agente non scrive nei file di memoria e di contesto senza richiesta esplicita.
