---
name: separazione-ambienti
description: >
  Conduce il gate della separazione fra test e produzione: riconosce dai fatti del progetto
  e della macchina il modello già in uso o i vincoli che orientano la scelta, lo dichiara,
  pone le domande della regola separazione-ambienti.md e propone una combinazione del
  catalogo, una forma per asse, spiegando per ciascuna proposta che cosa significa sceglierla
  rispetto alle alternative, che cosa richiede, che cosa costa e come fallisce, con le fonti.
  Registra la scelta o il rinvio e istanzia la guida nel progetto. Si esegue in
  inizializzazione, a ogni tornata di allineamento e quando cambia il modo di provare o
  rilasciare. Non modifica infrastruttura né configurazione senza una risposta esplicita e
  non esegue mai git add, commit o push.
disable-model-invocation: true
---

## Contesto del progetto (best-effort, pre-iniettato)

!`git log -1 --format="%h %ad %s" --date=short` !`git branch -a --format="%(refname:short)"` !`git worktree list`

## Che cosa fa questa skill, e che cosa non fa

La norma `.claude/skills/separazione-ambienti/RIFERIMENTO.md` stabilisce che non esiste un modo di default di separare test e produzione e che la scelta si fa con l'utente. Questa skill è la procedura con cui quella scelta avviene davvero nella conversazione, e il suo scopo è duplice: che l'utente scelga la forma adatta al proprio progetto, e che capisca che cosa ha scelto. Il secondo scopo non è un contorno del primo. Una scelta subita senza capirla verrà rifatta al primo incidente, e una scelta capita permette di riconoscere, fra sei mesi, quando il presupposto su cui poggiava è cambiato.

La conoscenza non sta qui. Il catalogo e il gate stanno nella regola, le spiegazioni nella guida `.claude/templates/separazione-ambienti/GUIDA.md`, le fonti nel registro `FONTI.md` accanto a essa. La skill legge la sezione pertinente della guida prima di spiegare una forma e ne riporta il contenuto in sintesi, con le sigle delle fonti, invece di spiegarla a memoria: così ciò che l'utente sente e ciò che trova sul disco dopo è la stessa cosa, e se le due divergono ha ragione la guida.

## Passo 1 - Raccogliere i fatti prima di fare domande

Si guarda che cosa il progetto dice di sé prima di chiedergli qualcosa, perché un modello già in uso si riconosce e non si inventa, e perché ogni domanda che i file potevano risparmiare consuma l'attenzione che serve per quelle che contano. Si leggono i file di composizione e i loro override, le configurazioni del proxy presenti nel repository, le pipeline sotto le cartelle di integrazione continua, i file d'esempio delle variabili d'ambiente, i file di progetto delle piattaforme gestite, e le branch remote pre-iniettate sopra. Se esiste già una scheda `context/deployment.md` o una voce ADR sulla separazione, si legge per prima: in allineamento la decisione precedente è il punto di partenza.

Se il progetto gira su una macchina raggiungibile e l'utente lo chiede, si osserva anche l'esercizio in sola lettura: i progetti di composizione attivi, i volumi, le porte in ascolto e su quale indirizzo. Non si scrive nulla sulla macchina di esercizio e non si leggono i valori dei segreti, solo i nomi delle variabili.

## Passo 2 - Dichiarare che cosa si è riconosciuto

Prima di qualunque domanda si dichiara, in poche righe, che cosa i fatti dicono, con la sigla per asse dove la forma si riconosce e con "non determinabile dai file" dove non si riconosce. Per ogni sigla si dice da quale fatto viene, cioè quale file o quale branch, perché l'utente deve poter correggere il riconoscimento e non solo accettarlo.

```
Riconosciuto dai file:
  R  R2 a richiesta   da docker-compose.test.yml con name: fisso e porte proprie
  P  P1               una sola branch stabile, rami di lavoro fusi con richiesta
  D  non determinabile dai file
  L  L1               un solo albero di lavoro
Non riconosciuto: dove gira la produzione.
```

Si dicono anche, subito, i rischi trasversali della regola che la forma riconosciuta non esclude, con che cosa li presidia oggi o con la constatazione che nulla li presidia. È spesso la parte più utile del gate in allineamento, perché il modello c'è già e funziona, e i suoi punti deboli nessuno li ha mai scritti.

## Passo 3 - Le domande, solo quelle che i fatti non hanno risolto

La regola elenca sei domande: dove gira la produzione, quante persone e quanti stati del codice insieme, quante macchine e quanta memoria, se ci sono utenti reali, dati sensibili o un fornitore di identità esterno, se per provare servono i dati reali, con che frequenza si rilascia e se c'è una pipeline. Si pongono solo quelle a cui il Passo 1 non ha risposto, e si pongono tutte insieme, perché le risposte si condizionano a vicenda. Una risposta "non lo so ancora" è legittima e va registrata come tale: su quell'asse la scelta si rinvia.

## Passo 4 - Proporre e spiegare, un asse per volta

Per ogni asse si propone una forma, legata ai fatti e alle risposte e non alla tabella della regola in astratto, e la si spiega leggendo la sua sezione nella guida. La spiegazione ha sempre la stessa forma, perché due proposte si confrontino:

- che cosa è, in una frase;
- che cosa significa sceglierla invece della forma vicina più plausibile per questo progetto, cioè che cosa si guadagna e che cosa si paga, dal campo "Che cosa significa sceglierla" della guida;
- che cosa richiede che esista prima, e se nel progetto esiste;
- come fallisce, con il caso osservato o la fonte;
- le sigle delle fonti su cui poggia la spiegazione.

Si nomina sempre almeno un'alternativa, anche quando la proposta sembra ovvia, perché capire una scelta significa sapere a che cosa si è rinunciato. Se l'utente chiede di approfondire una forma, si legge per intero la sua sezione della guida e se ne mostra l'estratto annotato. Una forma che la guida marca come sconsigliata, oggi P3, si propone solo se il progetto la usa già, dichiarando la fonte che la sconsiglia e la via d'uscita. Una pratica marcata come non ancora osservata si propone solo quando i fatti ne soddisfano i prerequisiti, e dicendo che non è ancora stata vista funzionare in un progetto di questo sistema.

Si accetta come esito un sì, un no con un'altra forma, o un rinvio. Non si propone mai di cambiare un modello in esercizio senza che l'utente l'abbia chiesto: in allineamento il gate documenta e presidia, e la migrazione a un'altra forma è una decisione a parte, con il suo piano.

## Passo 5 - Registrare nello stesso giro di lavoro

L'esito si scrive subito, secondo `chat-non-e-memoria.md`, in due posti. Nella sezione "Modello di separazione" di `context/deployment.md`: la sigla per asse, lo stato in esercizio o previsto di ciascun ambiente, il fatto che decide, i rischi da presidiare con il presidio di ciascuno. E in una voce di `memory/decisions.md` costruita dallo scheletro `esempi/adr-separazione-ambienti.md` del pacchetto, con le alternative considerate e le sigle delle fonti. Un rinvio si registra con la stessa forma e con la domanda rimasta aperta, perché un gate non registrato verrà riproposto identico alla tornata successiva. Per `memory/` vale il vincolo generale: si propone il delta e lo si applica su conferma, salvo che l'utente abbia già chiesto l'aggiornamento in forma generale.

## Passo 6 - Portare nel progetto la guida, e dire come si usa

Se la scelta è fatta, si istanzia il pacchetto secondo il suo README: guida e registro delle fonti interi sotto `docs/separazione-ambienti/`, gli esempi solo se corrispondono alla forma scelta e adattati al progetto. Se la combinazione comprende L2, si applica anche la norma `skills/alberi-di-lavoro/RIFERIMENTO.md` e si predispone la tabella degli alberi nella scheda. Se comprende P2, si aggiunge allo snapshot `memory/index.md` la riga degli ambienti.

Poi si chiude con il recap d'uso, breve e concreto: i comandi con cui si accende, si prova, si promuove e si torna indietro nella forma scelta, presi dall'estratto annotato della guida e adattati al progetto, e la regola che presidia il rischio principale. Una forma scelta di cui non si conoscono i comandi è una forma che non verrà seguita.

## Riesecuzione, che è il caso normale

A ogni allineamento la skill riparte dal Passo 1 con la decisione precedente in mano, e dichiara che cosa è cambiato: se i fatti riconosciuti sono ancora quelli dell'ADR, se il progetto ha nuovi ambienti o ne ha persi, se un ambiente previsto è entrato in esercizio, se il catalogo ha forme nuove o se una pratica prima non osservata è stata promossa. Si chiede soltanto dove il presupposto della scelta è cambiato; il resto si conferma mostrando la decisione in una riga.

## Vincoli

La skill legge e propone. Non modifica file di composizione, configurazioni del proxy, pipeline o macchine di esercizio senza una risposta esplicita, non legge mai valori di segreti, e non esegue `git add`, commit o push, che restano manuali dell'utente secondo `git-commands-format.md`.
