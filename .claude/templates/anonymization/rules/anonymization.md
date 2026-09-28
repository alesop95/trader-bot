# Anonimizzazione della documentazione tecnica

> Regola modulare, da caricare sempre nei progetti che la istanziano. Vale per ogni contenuto scritto d'ora in avanti nei file tracciati. Da istanziare in `.claude/rules/anonymization.md` sostituendo i segnaposto tra parentesi angolari con i valori del progetto, e da estendere man mano che emergono categorie nuove.

## Quando questa regola serve, e quando non serve

Serve quando il repository è pubblico, oppure condiviso più largamente della cerchia che lo scrive, e la materia che documenta appartiene a qualcun altro: un'infrastruttura aziendale, un cliente, un fornitore, delle persone fisiche. Le due condizioni valgono insieme. Un repository pubblico che documenta soltanto codice proprio non ne ha bisogno; un repository privato che documenta l'infrastruttura di un cliente ne ha bisogno comunque, perché la cerchia di chi vi accede cambia nel tempo e la storia git conserva tutto.

La ragione per cui la regola è vincolante e non consigliata sta nella durata: ciò che entra in un file tracciato resta visibile anche dopo una correzione successiva, perché la storia git è consultabile finché non viene riscritta, e riscrivere una storia condivisa è un'operazione pianificata e non un rimedio a valle di una svista.

## Cosa si anonimizza sempre

Ogni indirizzo IP[^1] pubblico reale del soggetto documentato o dei suoi fornitori, ogni indirizzo IP privato reale di qualunque blocco, ogni indirizzo fisico[^2] di un apparato reale, e ogni nome proprio completo di una persona fisica, vanno sostituiti con un segnaposto prima di scrivere in un file tracciato.

## Dati amministrativi e commerciali: mai in un file tracciato

Vale a maggior ragione per ciò che non è tecnico, ed è la categoria che sfugge più facilmente perché arriva come dettaglio a corredo di un fatto vero. Non si scrivono mai importi contrattuali e canoni, prezzi di acquisto di hardware o licenze, percentuali di sconto negoziate, numeri di fattura, ordine o preventivo, numeri di linea telefonica o di interno, IBAN e altri dati bancari, partita IVA e codice fiscale di controparti, e termini contrattuali specifici quando rivelano condizioni economiche.

Il criterio che decide è semplice e va applicato senza eccezioni: il *fatto operativo* resta raccontabile, il *numero* no. Si scrive che è stato acquistato uno switch nuovo tramite un preventivo di un certo fornitore, non il prezzo né il numero del preventivo; si scrive che un canone è stato rinnovato, non il suo importo; si scrive che una linea è stata dismessa, non il suo numero.

## Cosa resta reale, e perché

I nomi delle organizzazioni, cioè del soggetto documentato e dei suoi fornitori: sono nomi di persona giuridica e non dati personali, e tipicamente il repository dichiara comunque nel proprio titolo di che cosa si occupa. Le caselle di posta funzionali non personali. Il nome e la casella dell'autore dei commit, che coincidono con i metadati visibili su ogni commit della storia, quindi anonimizzarli nella prosa non avrebbe alcun effetto protettivo. Gli indirizzi citati come minaccia nota, che sono dati pubblici sull'attaccante e non informazioni del soggetto documentato.

Resta reale, con un'eccezione da dichiarare esplicitamente nel testo ogni volta che si usa, il nome di un oggetto di configurazione letterale già presente su un apparato reale, per esempio una regola di firewall che contiene un nome proprio nel proprio nome tecnico. La ragione è operativa: un segnaposto renderebbe quell'oggetto introvabile a chi deve agire sull'interfaccia dell'apparato, e una procedura che non si può eseguire non protegge nessuno.

## Convenzione dei segnaposto

Gli indirizzi pubblici si sostituiscono con gli intervalli riservati alla documentazione da RFC 5737, cioè `203.0.113.0/24`, `198.51.100.0/24` e `192.0.2.0/24`, che non sono instradabili su Internet reale.

Gli indirizzi privati si spostano su un blocco privato *diverso* da quello reale, mantenendo invariati gli ottetti che portano significato, tipicamente quello che identifica il segmento e quello che identifica il ruolo dell'host, così la documentazione resta leggibile e coerente con se stessa. L'esempio che si scrive nella regola istanziata non deve mai essere la mappatura vera, altrimenti la regola pubblica proprio la corrispondenza che esiste per nascondere.

Gli indirizzi fisici diventano una serie progressiva su un prefisso convenuto. Le persone diventano `Persona-A`, `Persona-B` in ordine di prima apparizione nel documento corrente, oppure un'etichetta di ruolo quando il ruolo è più informativo del nome, per esempio `Referente-<Fornitore>-1` o `Collaboratore-Esterno-1`. I luoghi con nome proprio diventano `<Tipo>-N`.

## Dove vive la mappatura, ed è il file più sensibile del progetto

La traduzione da segnaposto a valore reale non si scrive mai in un file tracciato: vive nel layer privato del progetto, per default `_notes/.anonymization-map.md`, ignorato da git, e si estende riusando lo stesso segnaposto quando la stessa persona o lo stesso indirizzo ricompaiono altrove.

Va detto perché quel file merita più attenzione di ogni altro: è l'unico che rende reversibile ogni altra anonimizzazione. Nel progetto in cui questa regola è nata, il riscontro più grave di tutto il primo audit non era un indirizzo né un nome, ma una voce di registro che pubblicava la corrispondenza fra un segnaposto e la persona reale. Un singolo accoppiamento pubblicato vale più di cento valori nascosti.

## Il controllo automatico, e perché non basta la buona volontà

Lo strumento `tools/Test-Anonymization.py` di questo pacchetto passa i file del repository e riporta indirizzi reali, indirizzi fisici reali, nomi propri di persona, caselle di posta personali, importi, numeri di telefono, IBAN, partite IVA e i segreti letterali già noti. Esce con codice diverso da zero se trova qualcosa nelle categorie bloccanti, e va eseguito prima di ogni commit che tocchi documentazione.

```
python tools/Test-Anonymization.py
python tools/Test-Anonymization.py --tutti    # include il layer privato, non bloccante
```

Lo script è versionato e non contiene nessun valore reale: ciò che deve cercare vive nel file dei pattern del layer privato, la cui forma è dichiarata in `patterns.example.json`. Se quel file manca, lo script si ferma e lo dichiara invece di restituire un esito verde che non ha calcolato. Quando cresce la mappa dei segnaposto cresce anche il file dei pattern: sono due facce dello stesso dato.

La ragione per cui il controllo esiste, e va usato invece che ricordato, è un numero. Il primo audit nel progetto di origine ha trovato centoquarantotto riscontri su ottantanove file tracciati, di cui una trentina erano valori reali veri: indirizzi cablati dentro gli script, indirizzi fisici di apparati dentro gli script di scrittura, indirizzi pubblici di macchine virtuali, caselle di posta personali, importi contrattuali, e la voce di registro citata sopra. Nessuno di quei residui era stato introdotto di proposito, e nessuno apparteneva alla sessione che li ha scoperti.

Ne discende la regola operativa: il controllo si fa sull'*intero perimetro*, non sui soli file toccati dalla sessione. Un residuo non si introduce, si eredita, e restare puliti sui propri file non dice niente sul repository.

## Il perimetro del controllo, e perché non è l'insieme dei file tracciati

Il perimetro predefinito è ciò che sta per essere pubblicato, cioè i file tracciati più quelli non tracciati e non ignorati, che sono esattamente i candidati al prossimo commit. I riscontri di entrambi i gruppi sono bloccanti, perché entrambi i gruppi finiscono in pubblico, e quelli del secondo gruppo vengono marcati a video con un avviso esplicito.

Questa definizione nasce da un difetto misurato, e vale la pena conoscerlo perché è controintuitivo. Definire il perimetro come l'insieme dei file tracciati sembra la scelta naturale ed è sbagliata: un file nuovo, scritto e non ancora aggiunto all'indice, resta invisibile al controllo proprio nel momento in cui serve guardarlo, cioè prima di pubblicarlo. Nel progetto di origine tre file nuovi sono passati puliti per fortuna e non per verifica, e il difetto è stato scoperto per caso qualche giorno dopo.

Con `--tutti` entrano anche i file *ignorati*, cioè il layer narrativo locale e gli output degli strumenti. Quei file contengono valori reali per costruzione e per decisione, ed è il motivo per cui git li ignora. I loro riscontri vengono perciò elencati a parte, aggregati per file, e *non sono bloccanti*. La distinzione non è una comodità: nel progetto di origine la misura dice 10.844 riscontri nel layer privato contro zero bloccanti nel perimetro pubblico, e fra i file più densi c'è proprio la mappa dei segnaposto, che per definizione contiene tutti i valori reali. Se quei riscontri fossero bloccanti il controllo fallirebbe per il solo fatto di esistere, e un controllo che fallisce sempre smette di essere letto.

Ne discende la proprietà che rende il perimetro corretto senza manutenzione: un percorso del layer privato diventa un problema nell'istante in cui viene tracciato, e in quel momento non compare più fra i riscontri privati ma fra i bloccanti, con la marca di file non tracciato. Il controllo cambia da solo la propria valutazione quando cambia lo stato del file, e nessuno deve ricordarsi di aggiornare una lista.

## Due cose che lo strumento non può fare, e restano umane

Non distingue un falso positivo da una fuga quando il valore è ambiguo, per esempio un numero di versione che somiglia a un indirizzo: quei riscontri finiscono nelle categorie non bloccanti e vanno guardati uno per uno.

E non conosce il contesto: un nome dentro una ragione sociale legale è ammesso, lo stesso nome in una frase narrativa no, e la lista delle eccezioni di contesto va tenuta aggiornata a mano nel file dei pattern e tenuta *corta*, perché più è lunga meno il controllo dice.

## Cosa fare quando si trova un valore reale già pubblicato

Non si riscrive la storia git da soli. La riscrittura di una storia condivisa è un'operazione pianificata, con backup e comunicazione preventiva se esistono altri collaboratori, mai un'azione improvvisata a valle di una singola sessione.

La sequenza corretta è segnalare il valore trovato, aggiungerlo alla mappa privata, correggerlo nel file tracciato corrente, e annotare la necessità di una pulizia della storia come lavoro a parte. Conviene tenere nel layer privato anche un file di sostituzioni pronto per quella pulizia, così che quando arriverà il momento non si debba ricostruire l'elenco: si accumula mano a mano, ed è l'unico modo per non pagare due volte lo stesso lavoro.

[^1]: *IP*, Internet Protocol - il numero che identifica un'interfaccia di rete; quelli privati sono validi solo dentro una rete locale, quelli pubblici sono raggiungibili da Internet.

[^2]: *Indirizzo fisico*, o MAC, Media Access Control - identificatore assegnato in fabbrica a un'interfaccia di rete, che identifica un apparato specifico in modo più stabile di un indirizzo IP.
