# Il recupero dei fatti: si cerca il token, non il file che sembra contenerlo

> Regola modulare, da caricare sempre. Governa il momento in cui l'agente deve affermare qualcosa sul sistema su cui lavora: dove cerca il fatto prima di affermarlo, e quale artefatto crede quando due si contraddicono. Nasce il 2026-10-23 da tre errori commessi nella stessa sessione di un progetto istanziato, tutti con lo stesso meccanismo e tutti fermati dal proprietario. I casi osservati stanno in `.claude/norme/recupero-dei-fatti.md`: quel file non si carica all'avvio e non serve per applicare la regola, serve a chi deve estenderla o rimetterla in discussione.

## Il meccanismo da non ripetere

Quando serve un fatto sul sistema, la tentazione è dedurre quale documento lo contenga e cercare lì. In un progetto con molti documenti sembra la mossa efficiente ed è invece la più fragile, perché i fatti non stanno dove la tassonomia dice che dovrebbero: le porte aperte sul firewall per un servizio possono stare nella scheda di quel servizio e non in quella del firewall, l'inventario degli apparati può vivere in un file di dati e non in una scheda di prosa, e un'affermazione sulla connettività può stare in un documento di continuità operativa vecchio di un anno.

Il conto è asimmetrico, ed è la ragione per cui la regola esiste. Una ricerca su tutto il corpus costa una chiamata; una conclusione sbagliata costa una raccomandazione sbagliata, che qualcuno deve poi fermare.

## Le tre prescrizioni

Se la domanda contiene un token distintivo, cioè un numero di porta, un modello di apparato, un indirizzo, un identificatore, il nome di un prodotto o di un fornitore, si cerca **quel token su tutto il corpus tracciato** prima di qualunque ragionamento su dove possa stare. Un token distintivo è una stringa quasi unica: la ricerca è insieme banale e quasi esaustiva.

La ricerca comprende i **dati strutturati** e non solo la prosa. L'inventario autorevole vive spesso in un file JSON o in un foglio generato, che nessuna ricerca per concetti raggiunge e che una ricerca limitata a `docs/` non vede.

Dentro il repository gli artefatti **non hanno pari autorità**, e questa è la parte che si dimentica. Alcuni sono registrazioni di una misura: il dump di un apparato, un inventario generato, lo snapshot di una fonte viva, l'uscita di uno strumento. Altri sono racconti: un piano, una scheda di governance, un documento di continuità. Per una domanda sulla configurazione attuale la registrazione batte il racconto, e un racconto che nessuna registrazione corrobora va trattato come candidato all'obsolescenza, tanto più se descrive un accordo con un fornitore o un contratto, perché quelli cambiano senza che nessuno rilegga il documento che li descriveva.

## Perché non basta la regola sulle classi di fonti

Dove il progetto ha una regola sulle fonti, quella distingue il repository dal mondo esterno e dice che il repository è autorevole su ciò che il progetto sa, non su com'è il sistema adesso. Questa regola aggiunge la distinzione **interna** al repository, che lì non c'è: fra due file tracciati, entrambi di classe A, uno può essere la fotografia di una misura e l'altro una narrazione invecchiata, e hanno lo stesso aspetto.

## Quando il fatto va cercato in un guasto

Un'indagine su qualcosa che non funziona è lo stesso problema visto da vicino, e sbaglia in sei modi che si riconoscono prima di commetterli. Vengono da due indagini lunghe in progetti istanziati, condotte da agenti che si correggevano a vicenda e sbagliavano lo stesso, che è la ragione per cui stanno scritte invece di essere lasciate all'attenzione.

Il primo è la premessa ricevuta. Un'indagine di tre giorni è stata costruita sopra una frase detta dall'utente e mai messa in discussione, cioè che un certo materiale stesse su un certo supporto; era sbagliata, e il sistema operativo aveva registrato il dato giusto fin dall'inizio, leggibile in sola lettura al costo di una interrogazione. Una premessa non diventa più solida perché tutto il resto le si è appoggiato sopra: le premesse di partenza si verificano per prime, e per prime fra tutte quelle per cui esiste una fonte autoritativa a costo quasi nullo.

Il secondo è il dato ambiguo letto dentro l'ipotesi corrente, ed è il più frequente: su nove errori dichiarati da due sessioni indipendenti, la maggioranza aveva quella forma. Non si corregge con più prudenza, perché la prudenza non cambia la lettura. Si corregge con una domanda fissa, da porre davanti a ogni dato ambiguo prima di usarlo: che cos'altro produrrebbe esattamente questa osservazione?

Il terzo è concludere da un silenzio. Un registro tace anche su ciò che non si impegna a registrare, e chi lo interroga per datare un evento che quel registro non copre trova silenzio e lo legge come assenza del fatto. Un log è una promessa su che cosa registra, e la promessa si legge prima dei dati.

Il quarto è ordinare due cause con un argomento. Quando due interventi ravvicinati rivendicano lo stesso effetto, la plausibilità non li ordina: li ordina un terzo evento che non sia nessuno dei due, datato alla risoluzione più fine disponibile, che cada fra i due e ne escluda uno.

Il quinto è guardare dalla parte di chi fallisce. Davanti a una contesa su una risorsa, che sia una lettera di unità, una porta, un lock o un nome di file, la domanda produttiva non è perché il richiedente fallisce ma chi la detiene e perché non la rilascia: il richiedente vede solo il proprio fallimento, il detentore ha tutto il contesto.

Il sesto è confondere una scadenza con una risposta. Una chiamata di inventario che dovrebbe essere istantanea e invece si appende dice che il guasto sta in ciò che sta enumerando, non nel soggetto dell'indagine; va quindi eseguita dietro un tetto di tempo, e la scadenza si tratta come esito a sé, perché non lo so non è assente e non è pieno, e confonderli manda a cercare il guasto nel posto sbagliato.

## Il presidio

Quando si consegna al proprietario un numero o un'affermazione su com'è fatto il sistema, si dice da dove viene: quale file, e se è una misura registrata o un racconto. Un'affermazione senza provenienza dichiarata è un'affermazione che nessuno può fermare, e nei tre casi che hanno prodotto questa regola è stata fermata ogni volta che la provenienza è stata chiesta.
