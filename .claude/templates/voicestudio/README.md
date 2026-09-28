# voicestudio

> Pacchetto opzionale del sistema di progetto. Porta dentro il progetto il riconoscimento vocale e la sintesi vocale in locale, appoggiandosi a VoiceStudio, che è una applicazione esterna e resta tale: il pacchetto non la contiene e non la installa, ne descrive l'allestimento, ne fissa i due punti di contatto con il sistema di progetto e istanzia lo strumento che li usa.

## Che problema risolve, e perché non è quello che sembra

Il problema che questo pacchetto risolve non è "generare voce", che è una capacità cercata da chi produce audio e ignorata da tutti gli altri. È il rovescio, e riguarda ogni progetto che raccolga fonti: la norma `.claude/skills/fonti-non-recuperabili/RIFERIMENTO.md` prescrive che per una fonte video la forma utile non sia il video ma la sua trascrizione, e indica due vie, i sottotitoli automatici dove esistono e il riconoscimento vocale dove non esistono. Della prima via il sistema aveva già lo strumento, cioè `vtt-to-text.py` del pacchetto `community-sources`; della seconda aveva soltanto la frase "costa molto più tempo", che è il modo in cui una prescrizione si trasforma in una fonte catalogata come non letta.

VoiceStudio chiude quella seconda via in locale. Gira sulla macchina, non manda l'audio a nessun servizio, non richiede un account e dichiara di coprire seicentoquarantasei lingue. Ne segue che la trascrizione smette di essere una decisione di bilancio e torna a essere un passo della procedura, ed è per questo che il pacchetto esiste nel catalogo di un sistema che non si occupa di audio.

La capacità di produrre voce resta e va offerta a chi serve, cioè a chi fa audiolibri, doppiaggio o dettatura. Ma non è la ragione per cui questo pacchetto si propone di default a un progetto che raccoglie fonti, e confondere i due casi porta a offrirlo agli uni e non agli altri.

## Che cosa istanzia

Un file, `tools/trascrivi.py`, da copiare in `tools/` del progetto ospite. Python 3 e sola libreria standard, nessun segnaposto da sostituire. Prende un file audio o video, ne ottiene il testo dal servizio locale, e lo scrive sotto `_notes/fonti/` con la convenzione di nome che la regola sulle fonti prescrive, cioè la data seguita da una parola che identifica la fonte.

Davanti al testo scrive la provenienza, e questa è la parte che vale spiegare invece di lasciar scoprire: da dove viene il file, quale servizio e quale modello lo hanno trascritto, quando, e la dichiarazione esplicita che si tratta di testo prodotto da riconoscimento vocale e non riletto. Le prime tre righe servono perché una trascrizione da sola non dice da dove viene, e a distanza di un mese nessuno ricorda se quel testo fosse un video, una riunione o un promemoria. La riga sul modello serve per una ragione meno ovvia: due modelli diversi producono due trascrizioni diverse dello stesso audio, e senza saperlo un confronto fra due trascrizioni misura il modello invece del contenuto. L'ultima riga serve perché una trascrizione automatica si cita male: i nomi propri e i numeri sono esattamente ciò che il riconoscimento sbaglia, e sono esattamente ciò per cui si cita una fonte tecnica.

Restano due voci di permesso da aggiungere a mano nel progetto ospite, come per gli altri pacchetti che portano strumenti.

```
Bash(python tools/trascrivi.py:*)
```

## Allestimento, una volta sola

VoiceStudio si scarica dalla pagina dei rilasci del progetto e ha una guida per sistema operativo, oltre a una immagine Docker. È scritto in Python con una interfaccia Electron, usa l'accelerazione hardware dove c'è, CUDA su schede NVIDIA e MLX su Apple Silicon, e funziona anche a sola CPU pagando in tempo. Il primo avvio scarica il modello, che è dell'ordine dei due gigabyte: va fatto prima della prima trascrizione, perché altrimenti quel trasferimento avviene dentro il tempo di attesa della prima richiesta e la fa sembrare bloccata.

Una volta aperta l'applicazione, il servizio ascolta sulla macchina e non serve avviare nient'altro. Che risponda si verifica prima di trascrivere, e non dopo, con il comando che interroga il documento di scoperta.

```
python tools/trascrivi.py --stato
```

La distinzione che quel comando produce è l'unica che conti quando qualcosa non funziona: separa "il servizio non c'è" da "il file non va bene", che altrimenti arrivano entrambe come lo stesso errore alla stessa chiamata, e mandano a cercare nel posto sbagliato.

## Uso

```
python tools/trascrivi.py riunione.m4a --nome riunione-tecnica
python tools/trascrivi.py intervista.mp4 --nome intervista-autore --lingua it
python tools/trascrivi.py audio.wav --nome fonte --forza
```

La lingua si può dichiarare oppure lasciare rilevare. Dichiararla conviene quando la si conosce: su un audio breve o rumoroso il rilevamento sbaglia, e una trascrizione fatta nella lingua sbagliata non produce un errore ma un testo plausibile e inventato, che è il modo peggiore di fallire. Una seconda corsa sullo stesso file non sovrascrive, perché di norma è una distrazione; per rifarla davvero si passa `--forza`.

L'attesa predefinita è larga perché un'ora di audio su una macchina senza acceleratore ne chiede parecchia, e un'attesa stretta trasformerebbe una trascrizione lenta in un guasto apparente.

## Il server MCP, e la sola cosa da configurare prima di collegarlo

VoiceStudio espone anche un server MCP montato sul proprio servizio, che dà a una sessione i tool per sintetizzare parlato, clonare una voce, trascrivere e elencare le voci disponibili. È la via giusta quando la voce serve dentro il lavoro, cioè quando la sessione deve produrre o leggere audio come parte del compito, e non quando serve trascrivere una fonte, caso in cui lo strumento di questo pacchetto costa meno e lascia una traccia su disco.

Un dettaglio della sua configurazione non è un dettaglio e va deciso prima di collegarlo, perché riguarda direttamente la regola sull'economia del contesto. Per difetto il server restituisce l'audio generato dentro la risposta, codificato in base64: un frammento breve sfiora già i limiti di un risultato, e un paragrafo di narrazione li supera, quindi una sessione che generi parlato si riempie di byte che non sono informazione per nessuno. La configurazione da scegliere è quella che scrive il file su disco e restituisce il percorso, cioè la variabile `OMNIVOICE_MCP_OUTPUT_MODE` portata a `files`, con `OMNIVOICE_MCP_BASE_PATH` a indicare la cartella. Quest'ultima, oltre che il posto dove scrivere, è il confine di sicurezza del server, cioè l'unica area da cui accetta di leggere i file che gli vengono passati per percorso, e senza di essa gli argomenti di percorso vengono rifiutati.

Il trasporto non è autenticato, quindi l'indirizzo resta sulla macchina. Esporlo su una rete, anche solo di casa, richiede di sapere che chiunque vi si trovi può far generare audio e leggere ciò che sta dentro il confine configurato.

## Licenza, e il vincolo che non è tecnico

VoiceStudio è distribuito sotto AGPL-3.0, che è una licenza con obblighi reali per chi la usa dentro un servizio offerto in rete: non è un dettaglio da rimandare al legale del progetto se il progetto è un servizio. I modelli hanno licenze proprie, distinte da quella dell'applicazione, e vanno guardate prima di un uso commerciale invece che dopo.

Il vincolo più importante, però, non è di licenza. La clonazione di una voce si fa con il permesso di chi quella voce ce l'ha, e la frase vale anche quando la voce è di una persona nota, anche quando il risultato resta privato, e anche quando serve solo per una prova. Un progetto che istanzia questo pacchetto e produce voci clonate registra da chi ha avuto il permesso, con la stessa serietà con cui registra le proprie fonti.

## Collaudo

Lo strumento porta le proprie prove, che girano contro un trasporto finto e senza rete.

```
python tools/trascrivi.py --self-test
```

Diciannove controlli, che coprono la costruzione della richiesta multipart e il fatto che un campo non dichiarato non vi entri, la convenzione del nome in uscita e la presenza della provenienza prima del testo, il rifiuto della seconda corsa e il suo scavalco esplicito, e la famiglia di guasti che rende utile uno strumento come questo invece di una riga di `curl`: un rifiuto del servizio letto come tale, un errore consegnato con un codice di successo che non passa per una trascrizione, una risposta vuota che non viene scambiata per la trascrizione di un silenzio, e un altro servizio in ascolto sulla stessa porta che non viene scambiato per questo.

Quelle prove dicono che questo programma costruisce bene la richiesta e interpreta bene la risposta. Non dicono che il servizio funzioni, che è una proprietà del servizio e si verifica con `--stato` su una macchina dove gira davvero. La distinzione va tenuta, perché una suite verde su un trasporto finto è esattamente il genere di copertura che la norma `skills/prove-che-misurano/RIFERIMENTO.md` invita a non confondere con la prova che il risultato arrivi a destinazione.

## Quando questo pacchetto non serve

Non serve dove i sottotitoli automatici esistono già, perché scaricarli e ripulirli costa secondi contro i minuti del riconoscimento, e la qualità è la stessa o migliore: la catena corretta resta quella di `vtt-to-text.py`. Non serve a un progetto che non raccolga fonti parlate e non produca audio, e in quel caso proporlo significa far installare un'applicazione di parecchi gigabyte per una capacità che nessuno userà. E non sostituisce la lettura: una trascrizione di un'ora di parlato è un documento lungo che va comunque condensato, e la disciplina per farlo è quella della disclosure progressiva della regola sull'economia del contesto, non una lettura integrale.
