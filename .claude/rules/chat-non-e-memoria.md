# La chat non è memoria: tutto ciò che si scrive in sessione si scrive anche su disco

> Regola modulare, da caricare sempre. Nasce da una direttiva d'uso del 2026-09-09 in un progetto istanziato da questo template, ed è generale: non riguarda lo stile della risposta, che è materia di `interaction-style.md`, ma la sua persistenza.

## Il principio

Ciò che l'agente scrive in chat non esiste per il progetto. Una sessione finisce, una compattazione riscrive, un crash cade a metà di un commit: ogni misura, ogni correzione e ogni decisione che viva soltanto nella risposta è già perduta nel momento in cui viene scritta. La regola è quindi che nessun contenuto sostanziale resti nella sola conversazione, e che l'aggiornamento dei file avvenga nel medesimo giro di lavoro in cui il contenuto nasce, non alla fine della sessione quando il contesto è pieno e l'attenzione bassa.

Ne segue una prescrizione operativa semplice. Se una risposta contiene un numero misurato, quel numero va anche in un documento generato o in una nota autorata. Se contiene una correzione a un'affermazione precedente, la correzione va nel work log e, se cambia lo stato, nella scheda o nell'indice. Se contiene una decisione dell'utente, va nel registro delle decisioni come ADR. Se contiene un lavoro rimandato, una verifica aperta o del materiale atteso, va nel registro delle pendenze. E se contiene una fonte con ciò su cui è autorevole, va nel registro delle fonti.

## Che cosa non conta come persistenza

Non basta che il contenuto sia deducibile da un file: deve esservi scritto. Una misura che sta soltanto nell'output di uno strumento non è persistita, perché nessuno rilancia uno strumento per ricordare un numero; va nel documento che quello strumento genera. Un ragionamento che sta soltanto nel messaggio dell'agente non è persistito nemmeno quando è corretto, e la prova è che la sessione successiva lo rifarebbe da capo con esito magari diverso.

Non conta neppure un aggiornamento differito. La direttiva dice di aggiornare ogni volta, e la ragione è che il debito di scrittura si comporta come il debito di lettura: cresce in silenzio e si paga quando conviene meno. Un giro di lavoro che produce un risultato e non lo scrive lascia il progetto in uno stato in cui la chat e il disco divergono, che è precisamente lo stato che un sistema di memoria esiste per evitare.

## La memoria si aggiorna da sola, il versionamento resta umano

L'aggiornamento di `memory/` e `context/` è automatico e avviene a ogni giro di chat sostanziale, senza che l'utente debba chiederlo: work log, snapshot `memory/index.md`, registro delle decisioni, registro delle pendenze e schede toccate dal lavoro si scrivono nel medesimo giro in cui il contenuto nasce, esattamente come i documenti di conoscenza. Una versione precedente di questa regola chiedeva all'agente di proporre il delta e di applicarlo solo su richiesta; la direttiva d'uso del 2026-09-24 l'ha superata, perché in pratica la richiesta non arrivava a ogni giro e la memoria restava indietro rispetto alla chat, cioè nello stato che questa regola esiste per impedire.

Il controllo umano non sparisce, si sposta dove è efficace: sul diff e sul commit. L'agente scrive, l'utente rilegge con `git diff` e decide che cosa versionare, perché `git add`, commit e push restano manuali. Una scrittura sbagliata in memoria si scarta prima del commit con lo stesso gesto con cui si scarta una modifica al codice. Restano esclusi dall'automatismo soltanto i giri puramente conversazionali, che non producono misure, decisioni, correzioni, pendenze o fonti.

## Il presidio

Alla fine di ogni giro di lavoro sostanziale l'agente dichiara, in una riga, quali file ha scritto. È il modo in cui la regola si verifica invece di essere solo dichiarata: se quella riga non c'è, il contenuto è rimasto in chat.

Il presidio ha una seconda parte, nata da una direttiva d'uso del 2026-09-10 in un progetto istanziato: alla fine di ogni giro sostanziale si riscrive anche `_notes/RESUME-PROMPT.md`, che è l'iniezione con cui la sessione successiva riparte esattamente da dove questa si è fermata, e non soltanto alla chiusura della sessione. La ragione è la stessa della prima parte e vale anche quando tutto il resto è stato scritto correttamente: lo stato di avanzamento sta sparso fra indice, pendenze, decisioni e materiali su disco, e ricomporlo costa una lettura lunga a chi riprende; una sessione che cade a metà, poi, non arriva mai alla chiusura. Un file che lo ricompone non duplica quei documenti se dichiara di essere volatile e rimanda a essi per la conoscenza durevole, ed è il patto che quel file dichiara in testa.
