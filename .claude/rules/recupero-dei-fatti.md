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

Un'indagine su qualcosa che non funziona e' lo stesso problema visto da vicino, e sbaglia in sei modi che si riconoscono prima di commetterli: la premessa ricevuta e mai verificata, il dato ambiguo letto dentro l'ipotesi corrente, il silenzio di un registro scambiato per assenza del fatto, due cause ordinate per plausibilita' invece che da un testimone, la domanda posta a chi fallisce invece che a chi detiene la risorsa, e la scadenza di un tempo massimo scambiata per una risposta. Ciascuno con il caso che l'ha prodotto sta nel riferimento della skill `prove-che-misurano`, che si carica quando si indaga un guasto; qui resta il fatto che sono sei e che hanno un nome, perche' un rimando a una cosa senza nome non si segue.

## Il presidio

Quando si consegna al proprietario un numero o un'affermazione su com'è fatto il sistema, si dice da dove viene: quale file, e se è una misura registrata o un racconto. Un'affermazione senza provenienza dichiarata è un'affermazione che nessuno può fermare, e nei tre casi che hanno prodotto questa regola è stata fermata ogni volta che la provenienza è stata chiesta.
