# Casi osservati dietro la regola sul recupero dei fatti

> Non si carica all'avvio. Serve a chi deve estendere la regola `recupero-dei-fatti.md` o rimetterla in discussione, non ad applicarla.

## I tre errori del 2026-10-23, nella stessa sessione

Il primo. Serviva sapere se certe porte in uscita, richieste da un fornitore di telefonia in cloud, fossero ammesse dal firewall. La ricerca è stata fatta dentro il solo documento del firewall, perché «le porte del firewall stanno nel documento del firewall». Non c'erano. Stavano nella scheda della telefonia, insieme alla data della verifica, all'esito e perfino all'elenco degli oggetti creati sull'apparato: il progetto lo sapeva da sette mesi. Una ricerca del numero di porta su tutto il corpus avrebbe risposto alla prima chiamata.

Il secondo. È stata scritta e consegnata al proprietario una domanda da porre al fornitore, che chiedeva se un apparato di riserva fosse installato e operativo. Il proprietario ha risposto che bastava guardare la topologia. Infatti l'inventario in formato dati conteneva l'apparato principale, quello di riserva e lo switch, con i collegamenti e le porte. La domanda è stata tolta. La ricerca precedente aveva guardato `docs/` e le schede di contesto, escludendo per abitudine la cartella dei dati.

Il terzo, il più istruttivo. Serviva sapere se l'indirizzo pubblico della sede cambiasse durante il subentro su una linea di riserva, perché da questo dipendeva una regola di filtro che poteva chiudere fuori l'amministrazione. La risposta è stata presa da un documento di continuità operativa che affermava l'esistenza di un affascio di linee e la stabilità dell'indirizzo. Il proprietario ha contestato: quell'affascio era un prodotto dell'operatore precedente, disdetto diciassette mesi prima, e la cronologia del progetto stesso ne registrava la disdetta. La riga successiva di quel documento diceva «Da aggiornare», ed era stata letta e sottopesata. La fonte giusta era il dump del firewall, che mostrava due sole interfacce di uscita e un gruppo logico con quella dismessa come primaria; e la conferma definitiva è arrivata dal portale del fornitore, che mostrava due apparati con un indirizzo virtuale condiviso.

## Che cosa hanno in comune

In tutti e tre i casi esisteva un token distintivo: un numero di porta, un modello di apparato, il nome di un prodotto. In tutti e tre la ricerca di quel token su tutto il corpus sarebbe costata una chiamata. In tutti e tre la conclusione sbagliata è arrivata fino al proprietario, che l'ha fermata; e la terza volta ha chiesto esplicitamente da dove venisse l'affermazione, che è il presidio che la regola prescrive.

Il terzo caso aggiunge la distinzione che la regola sulle classi di fonti non copre: il documento di continuità e il dump del firewall erano entrambi file tracciati dello stesso repository, quindi entrambi di classe A, e avevano lo stesso aspetto. Uno era la fotografia di una misura presa sull'apparato, l'altro un racconto scritto una volta e mai riletto.

## La misura del costo

Nella stessa giornata il proprietario ha fermato tre conclusioni sbagliate. Due di esse avrebbero prodotto un'azione: una domanda inutile a un fornitore, e una regola di filtro applicata su un presupposto falso che in caso di guasto della linea principale avrebbe tolto l'accesso amministrativo a una macchina esposta, proprio mentre la rete era già in avaria.

## I sei modi dell'indagine, e dove sono stati misurati

I casi che hanno prodotto la sezione sull'indagine vengono da due progetti istanziati e sono di ottobre 2026. Si riportano qui con le misure, perché la sezione della regola tiene la prescrizione e non l'episodio.

La premessa ricevuta: un'indagine durata tre giorni, condotta da due agenti che si correggevano a vicenda, poggiava su una frase dell'utente mai verificata, cioè che un certo materiale stesse su un certo supporto. Era falsa. Il sistema operativo conservava l'etichetta di ogni supporto mai montato in una chiave di registro leggibile in sola lettura anche a dispositivo scollegato, e la verifica costava una interrogazione sola.

Il dato ambiguo: su nove errori dichiarati da due sessioni indipendenti sullo stesso guasto, la maggioranza aveva la stessa forma, cioè un dato ambiguo interpretato dentro l'ipotesi già in testa invece che confrontato con le altre che lo spiegherebbero altrettanto bene. Due esempi dalla stessa indagine: un volume a zero byte letto come traccia fantasma del programma sotto esame era il supporto guasto, e un errore attribuito a un dispositivo per il suo numero di disco era di un altro, perché quel numero si riusa quando un supporto viene staccato.

Il silenzio di un registro: il log di installazione dei dispositivi registra installazioni e rimozioni, ma non lo scollegamento fisico di un dispositivo già installato, che il sottosistema gestisce senza lasciare righe. Chi lo interrogava per datare una rimozione trovava silenzio e lo leggeva come assenza del fatto.

Le due cause: due sessioni hanno agito sullo stesso guasto nello stesso minuto, un distacco fisico e una modifica al registro, ed entrambe si attribuivano lo sblocco. A ordinarle è stato un terzo evento indipendente datato al millisecondo, che cadeva fra le due.

La contesa: per mezza giornata l'indagine ha chiesto perché un programma non ottenesse la risorsa che chiedeva, e la risposta stava in chi la teneva e non la rilasciava.

La scadenza: tre chiamate di inventario del sottosistema di archiviazione non hanno un tempo massimo proprio e, per rispondere, enumerano tutti i dispositivi; un solo dispositivo guasto le blocca per sempre anche quando con la domanda non c'entra niente. Uno script che le usava in una guardia non è fallito, si è fermato: quarantadue minuti con zero CPU, zero I/O, nessuna riga di log e nessun codice di uscita, e l'unico modo di accorgersene era guardare l'elenco dei processi.
