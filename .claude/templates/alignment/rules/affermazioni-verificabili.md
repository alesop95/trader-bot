# Affermazioni verificabili, scadenze dichiarate e domande aperte

> Regola modulare, da caricare sempre nei progetti che istanziano il pacchetto `alignment`. Definisce il vincolo su ciò che si scrive nei file tracciati, e il presidio che lo rende un controllo invece di un proposito.

## Il vincolo

Ogni affermazione dei file tracciati deve avere una verifica meccanica, una scadenza dichiarata dopo la quale torna automaticamente a stato non verificata, oppure una marcatura esplicita di non verificabile con scritte accanto la domanda da porre e la persona a cui porla. Non esiste un quarto caso: un'affermazione senza nessuna delle tre è un'affermazione che invecchierà in silenzio.

## Perché esiste, e perché non basta la buona volontà

Un'affermazione scritta in un documento non ha alcun legame con la realtà che descrive: nasce vera, e il momento in cui smette di esserlo non lascia traccia da nessuna parte. Ne segue che il rischio non è la contraddizione, che si vede leggendo, ma l'obsolescenza silenziosa, cioè una scheda che descrive correttamente lo stato di tre settimane fa e non dichiara di essere vecchia. Nel progetto reale da cui questa regola è estratta se ne sono misurate tre in una sola mattina, e nessuna era visibile a un lettore attento: una copia di backup fuori sede ferma da sei settimane che ogni documento dava per esistente, una scheda dello stack che elencava cinque script su ventuno, e una pendenza che dichiarava scaduta una cadenza invece rispettata.

Il difetto non è la disattenzione, ed è importante non trattarlo come tale, perché un difetto attribuito alla disattenzione si rimedia con un promemoria e i promemoria scadono. Le uniche correzioni che restano vengono da un confronto deterministico fra un'affermazione e una misura.

## Le tre forme ammesse, con il posto in cui vive ciascuna

La verifica meccanica è un invariante calcolato sul repository, e vive nel codice dello strumento perché è strutturale: gli script presenti e non citati nella scheda dello stack, le decisioni richiamate e non definite, il frontmatter di una scheda che non copre l'ultima modifica del suo contenuto, l'unicità dei numeri di un registro. Un invariante non si configura, si scrive.

La scadenza dichiarata è un fatto del progetto, e vive nel registro tracciato accanto al preavviso e alla conseguenza. La conseguenza va scritta insieme alla data, perché una data senza la sua ricaduta non fa agire nessuno: è la differenza fra "il 22 novembre scade una licenza" e "il 22 novembre la fonte con cui verifichiamo le porte smette di rispondere".

La marcatura di non verificabile è la forma più facile da scrivere male. Non basta annotare che una cosa è incerta: va scritta la domanda esatta, adesso, e il ruolo della persona che può rispondere. Fra due mesi nessuno ricostruirà che cosa andava chiesto, e un'incertezza senza la sua domanda resta un'incertezza per sempre.

## Il presidio

Lo strumento `Test-Allineamento.py` valuta il registro e gli invarianti a ogni avvio di sessione, tramite un hook. È rumoroso e non blocca, e la scelta è deliberata: un controllo che fallisce sempre smette di essere letto, e questo gira ogni volta. Distingue perciò nel codice di uscita il giallo dal rosso, dove il giallo è un'affermazione che sta invecchiando e il rosso è qualcosa di già rotto.

Ne discende una pratica sullo scrivere gli avvisi, che vale oltre questo strumento. Un'eccezione decisa da una persona va dichiarata nel posto dove il controllo la legge, con la sua ragione accanto, e il controllo la conta a parte: un'eccezione dichiarata resta visibile come eccezione, un'eccezione subita diventa rumore. E un invariante che segnala il comportamento corretto va riscritto, non tollerato: è accaduto due volte con il confronto sul frontmatter, e la seconda versione segnalava le sessioni che avevano rispettato la regola, cioè insegnava a ignorare il controllo proprio a chi lo stava usando bene.

## Il campo di firma delle schede, e la distinzione che lo rende sostenibile

Il campo `last-verified-commit` dichiara a quale commit la scheda è stata riletta e trovata vera. Scriverci un hash che non corrisponde a una rilettura reale è una bugia messa esattamente nel posto in cui il progetto va a cercare la verità, quindi il bump non si fa in blocco: si bumpa la scheda che si è effettivamente riletta, e le altre restano indietro dichiarando su cosa.

Il valore da scrivere è l'ultima modifica di contenuto della scheda, non il commit in cui si scrive il bump. Un commit che tocca il solo campo di firma è la firma della scheda, e trattarlo come una sua modifica rende l'allineamento irraggiungibile per costruzione. Il controllo verifica infatti per discendenza e non per uguaglianza, così che una scheda riletta immutata a una data successiva possa portare l'hash in avanti e restare verde.
