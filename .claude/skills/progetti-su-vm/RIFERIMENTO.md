# Progetti che girano su una macchina remota

> Riferimento normativo della skill `progetti-su-vm`. Nasce da due progetti istanziati, nel novembre 2026: lo spostamento di un'applicazione web che si sviluppava direttamente sulla propria VM, e l'irrobustimento di due VM Linux contro una base di sicurezza comune. Tutto ciò che segue è stato osservato su quelle macchine; i percorsi concreti della postazione stanno nel file della macchina descritto in `SKILL.md`.

## La regola

Un'applicazione che gira su una VM o su un server si sviluppa in una cartella dedicata sulla postazione, sotto la cartella dei progetti dichiarata nel file della macchina, con il nome del progetto. La cartella è un clone del repository con la stessa storia e lo stesso remoto: lì si scrive, si committa e si spinge, e da lì si lanciano via SSH i comandi sulla macchina.

La macchina è una copia di esercizio. Riceve il codice per `git pull` e lo esegue; non vi si scrive codice e non vi nasce nessun commit. Le credenziali dell'applicazione restano solo sulla macchina, in un file ignorato da git; nella cartella della postazione c'è un file di esempio con le sole chiavi. Accanto al codice, sulla macchina, stanno soltanto i file di esercizio ignorati: ambiente virtuale, credenziali, build, registri, file prodotti dall'applicazione. Note, documenti di studio, campioni e backup stanno nelle note private della cartella della postazione.

Il motivo è che la sorgente di lavoro deve stare dove ci sono il template, gli strumenti e le copie di salvataggio della postazione, e la macchina di esercizio deve restare piccola, prevedibile e ripristinabile. Lo sviluppo diretto su una macchina remota produce l'opposto: un albero con modifiche mai committate, note private mescolate al codice, credenziali scritte nei sorgenti, script di manutenzione pericolosi lasciati sulla scrivania.

## Come si dispone il repository

Produzione sul ramo `main` e staging sul ramo `develop`, sulla macchina di solito come due cartelle dello stesso repository, la seconda come *worktree*. Configurazioni e script della macchina stanno in una cartella `deploy/` del repository: server block del proxy, unit di systemd, script di rilascio e di accesso, ciascuno con il proprio ritorno indietro scritto in testa. Uno script che gira sulla macchina Linux ma è scritto sulla postazione Windows si fissa a fine riga LF in `.gitattributes`.

Il ciclo di rilascio: si lavora su `develop` e si spinge; la cartella di staging esegue `git pull`, si ricompila ciò che serve e si prova da un client autorizzato con dati reali; si fa confluire `develop` in `main` sulla postazione e si spinge; la cartella di produzione esegue `git pull` dopo un tag dello stato che funziona, e si riavvia il servizio. Il ritorno indietro è un reset a quel tag seguito dagli stessi passi. Una risposta 200 del servizio non prova che l'applicazione funzioni: la prova è un'operazione vera sullo staging.

## Come si sposta un progetto che oggi si sviluppa sulla macchina

| Passo | Che cosa | Attenzione |
|---|---|---|
| 1 | Verificare sulla macchina che rami e remoto siano allineati, senza commit non spinti | un commit solo locale si perderebbe |
| 2 | Clonare nella cartella della postazione con l'alias SSH e l'identità di lavoro, con tutti i rami | stessa storia, stesso remoto |
| 3 | Riportare le modifiche non committate della macchina (patch e file non tracciati) e i file ignorati che servono: note, campioni, preferenze locali | credenziali escluse, se il proprietario non decide altrimenti |
| 4 | Riordinare il repository, se serve, con `git mv`, e togliere il codice mai eseguito in un commit chiaro | i file salvati in CRLF nel repository si lasciano com'erano, altrimenti gli spostamenti diventano riscritture e la storia non si segue più |
| 5 | Commit e push dalla postazione | il controllo delle identità del template gira prima del commit |
| 6 | Sulla macchina: tag dello stato di partenza, `git stash -u` delle modifiche locali, `git pull`, spostamento dei file ignorati nelle cartelle nuove con uno script una tantum che reinstalla i servizi e verifica che rispondano | gli ambienti virtuali Python hanno shebang assoluti da aggiornare dopo uno spostamento |
| 7 | Una prova reale sullo staging | |
| 8 | Nel template: la cartella della macchina passa da `remoti-approvati.txt` a `esclusi.txt` come copia di esercizio; la cartella della postazione la trova la passata dei progetti locali | `allinea-tutti.ps1 -Solo <progetto>` |
| 9 | Pulizia della macchina: note, campioni e backup portati sulla postazione con verifica delle impronte, poi tolti | un file che dal nome contiene credenziali non si apre e non si sposta: si segnala |
| 10 | Irrobustimento, sezione seguente | prima il censimento di chi usa la macchina |

La cartella di lavoro di una sessione non si può cancellare finché la sessione è aperta: se lo spostamento parte da una cartella vecchia sulla postazione, la si cancella dopo aver chiuso la sessione.

## Irrobustimento della macchina

Si misura prima di toccare: lo script di ricognizione degli strumenti comuni legge e non modifica, stampa una riga per requisito e in fondo il numero degli scarti. La misura completa vuole `sudo`; senza, i requisiti di SSH, firewall, AppArmor e auditd risultano vuoti e non vanno letti come scarti. Si lancia prima e dopo ogni intervento e l'uscita datata si conserva nelle note private.

Il primo intervento, quando `sudo` chiede una password, è un utente personale di amministrazione con `sudo` senza password, raggiungibile solo a chiave, creato una volta dal proprietario con la password; da lì in avanti gli interventi passano da quell'utente.

Prima di toccare SSH o firewall si censisce chi usa la macchina: accessi SSH riusciti degli ultimi 30 giorni con utente, metodo e origine, client dei registri del servizio, sorveglianza, backup. Poi si tiene aperta una sessione di riserva, si arma sulla macchina un ritorno automatico a pochi minuti (`systemd-run --on-active=10min` che rimette la configurazione di prima), si applica, si prova con connessioni nuove, e solo allora si disarma. Un ritorno a tempo non reinstalla pacchetti: per la rimozione di pacchetti la protezione è un'altra, sotto.

Si interviene un requisito alla volta, con la misura prima e dopo e con la verifica che il servizio risponda. Un rischio che il proprietario decide di tenere si scrive sulla macchina in `/etc/base-sicurezza/accettati`, una riga `id<TAB>motivo`, e la ricognizione lo conta a parte.

Quattro difetti osservati, che valgono per ogni macchina. Il firewall ufw, a ogni attivazione e a ogni reload, applica il proprio `/etc/ufw/sysctl.conf`, che rimette `log_martians` a 0 e annulla in silenzio i parametri di rete messi in `/etc/sysctl.d/`: lo si allinea prima di attivare e dopo il firewall si rimisurano i parametri del kernel. Sulle macchine installate dall'immagine desktop la rete è gestita da NetworkManager, che arriva con il desktop: togliere il desktop con la pulizia automatica delle dipendenze può togliere la rete, quindi si marcano a mano i pacchetti vitali, si simula la rimozione, ci si ferma se l'elenco ne contiene uno, e dopo si prova un riavvio. Uno script lanciato con l'uscita filtrata da `tail` nasconde il proprio codice d'errore, e con `set -euo pipefail` un comando che fallisce all'inizio lo fa uscire senza output, così sembra riuscito: si controlla `PIPESTATUS` o l'esito che lo script stampa alla fine. Un file che documenta il ritorno indietro si nomina per esecuzione, mai con un nome fisso, o la seconda esecuzione cancella l'elenco della prima.

## Client che devono raggiungere il servizio

Un client nuovo va ammesso su due livelli, il proxy e il firewall della macchina, e lo script di accesso del repository li aggiorna insieme, compreso il file delle regole che lo script comune del firewall rilegge. Se il servizio si apre con un nome non presente nel DNS, la voce si aggiunge al file hosts dei client con uno script distribuito dallo strumento di gestione dei PC. Lo script è idempotente e scrive la copia di sicurezza e il proprio registro in una cartella dati del sistema, non accanto al file hosts, perché su alcuni PC quella cartella non accetta file nuovi. Non chiama `exit` quando è incollato in un terminale remoto, che altrimenti si chiude prima che si legga l'esito.
