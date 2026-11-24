---
name: progetti-su-vm
description: >
  Stabilisce dove si sviluppa un'applicazione che gira su una macchina virtuale o su un server
  raggiungibile via SSH, e come si porta quella macchina a una base di sicurezza misurata. Si
  carica quando il progetto gira su una VM o su un server, quando si sviluppa o si sta per
  sviluppare direttamente sulla macchina remota, quando si sposta lo sviluppo dalla macchina
  alla postazione, quando si rilascia sulla macchina, quando si aggiungono client ammessi o un
  nome da raggiungere, e quando si irrobustisce la macchina (SSH, firewall, aggiornamenti,
  riavvii, desktop, registri). Non installa niente da sé e non tocca accessi remoti senza un
  ritorno automatico armato.
---

## Che cosa fa questa skill

La norma sta per intero in `RIFERIMENTO.md`, accanto a questo file, e va letta prima di operare. Dice tre cose. La prima è che un'applicazione che gira su una macchina remota si sviluppa in una cartella dedicata sulla postazione, e la macchina riceve il codice per `git pull` come copia di esercizio. La seconda è la ricetta per spostare lì un progetto che oggi si sviluppa sulla macchina. La terza è il metodo con cui la macchina si misura contro una base di sicurezza e si corregge un requisito alla volta, senza mai chiudersi fuori.

## Dove stanno le cose di questa postazione

Il template non contiene indirizzi, nomi di macchine né percorsi di una rete, perché arriva in progetti diversi, su reti diverse. Dove stanno la cartella dei progetti, gli strumenti comuni di irrobustimento e il documento del flusso di lavoro lo dice un file della macchina, `~/.progetti-su-vm.json`, che non sta in nessun repository:

```json
{
  "cartella_progetti": "<radice in cui ogni progetto ha la sua cartella>",
  "strumenti_sicurezza": "<cartella con base-vm.sh e gli interventi generici>",
  "documento_flusso": "<documento del flusso di sviluppo e di rilascio sulle VM>"
}
```

Se il file manca, lo si dice all'utente e si chiedono i tre valori; non li si indovina.

## Procedura minima

Si legge `RIFERIMENTO.md` e il file della macchina. Si riconosce in quale dei casi si è: progetto nuovo su una macchina, sviluppo trovato sulla macchina remota, rilascio, client nuovo o nome nuovo, irrobustimento. Si applica la sezione corrispondente, leggendo dagli strumenti comuni lo script e il README invece di riscriverli. Prima di toccare SSH o firewall si censisce chi usa la macchina e si arma il ritorno automatico; prima di dichiarare chiuso un intervento si rimisura.
