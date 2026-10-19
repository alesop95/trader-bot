# Pacchetto opzionale `cyber-lab`

<!-- readme-summary: laboratorio isolato e offline di macchine virtuali e container per studiare la valutazione difensiva dei propri sistemi, che un progetto istanziato tira su con un comando -->

> Tira su, dentro un progetto istanziato, un laboratorio isolato dove si impara a valutare e difendere i propri sistemi con gli strumenti del filone cybersecurity, senza toccare nessuna rete reale. Il laboratorio è una rete privata di container e macchine virtuali senza via d'uscita verso internet o verso la rete di casa, in cui vivono una console di scansione difensiva e dei bersagli di studio che l'utente fornisce. Settore del catalogo: «Sicurezza informatica e assessment». Stato: scaffold scritto il 2026-10-16, non ancora tirato su; il filone che lo motiva è `docs/filone-cybersecurity.md` del template, il percorso di studio `docs/filone-cybersecurity-percorso.md`.

## Il vincolo prima di tutto

Questo laboratorio esiste per imparare su sistemi propri e in un ambiente chiuso. Non si punta nessuno dei suoi strumenti verso una rete reale, aziendale o di terzi: una rete aziendale non è propria neanche quando ci si lavora, e serve l'autorizzazione scritta di chi la amministra. La rete del laboratorio è configurata senza instradamento verso l'esterno proprio perché questo vincolo non dipenda dalla memoria di chi la usa ma dalla forma dell'ambiente. Gli script si rifiutano di partire se trovano una configurazione che espone il laboratorio fuori dalla macchina.

## A chi serve e che cosa istanzia

A un progetto il cui obiettivo è imparare a fare valutazione di sicurezza, o a un progetto di macchina che vuole provare l'hardening e il rilevamento prima di applicarli alla macchina vera. Nel progetto che lo adotta scaffolda `cyber-lab/compose.yaml`, la definizione della rete isolata e dei servizi; `cyber-lab/cyber-lab.valori.esempio.sh`, i parametri da copiare in `cyber-lab.valori.sh` (ignorato da git) e compilare; `cyber-lab/tools/su.sh` e `cyber-lab/tools/giu.sh`, che tirano su e smontano il laboratorio con i controlli; e `cyber-lab/esercizi/`, un esercizio per funzione del NIST CSF 2.0, ciascuno con il rapporto da compilare.

Non scarica immagini e non le avvia da sé: la prima volta l'utente compila i valori, poi lancia `su.sh`, che prima verifica e solo dopo tira su. Le immagini sono fissate per digest nel file dei valori, senza tag mobili, come chiede la disciplina del template.

## Che cosa c'è dentro il laboratorio

Tre pezzi, su una rete Docker interna senza gateway verso l'esterno. La console di scansione difensiva, costruita dalle immagini ufficiali degli strumenti del censimento: la Greenbone Community Edition per la scansione ampia, e un contenitore leggero con Nmap, Nuclei e OSV-Scanner per le verifiche mirate e le dipendenze. La raccolta e la lettura, con Wazuh o un contenitore con Hayabusa e Chainsaw per esercitare la funzione Detect sui log che il laboratorio stesso produce. E i bersagli di studio, che l'utente fornisce: una macchina virtuale propria di cui vuole misurare l'hardening, oppure una delle immagini di addestramento pubblicate apposta per esercitarsi, che restano confinate nella rete interna. Il pacchetto non porta con sé immagini di bersaglio: indica dove dichiararle nei valori e lascia la scelta all'utente, perché un bersaglio di studio è una decisione sua e non un default.

## Come un progetto istanziato lo tira su

Il gate lo propone quando riconosce il settore della sicurezza. Alla conferma, scaffolda i file nel progetto e mostra questo recap. L'utente compila i valori con i digest delle immagini scelte e con i bersagli, poi:

```bash
cp cyber-lab/cyber-lab.valori.esempio.sh cyber-lab/cyber-lab.valori.sh
# si compila cyber-lab.valori.sh con i digest e i bersagli
bash cyber-lab/tools/su.sh      # verifica l'isolamento, poi tira su
# ... si lavora, si eseguono gli esercizi ...
bash cyber-lab/tools/giu.sh     # smonta e, con --pulisci, rimuove i volumi
```

`su.sh` si ferma se un servizio dichiara una porta pubblicata verso l'host, se la rete ha un instradamento verso l'esterno, se un'immagine è indicata con un tag mobile invece che per digest, o se il file dei valori manca. È lo stesso principio di preflight degli altri pacchetti di macchina: verifica e rendering prima, avvio dopo.

## Gli esercizi

Un esercizio per funzione del NIST CSF 2.0, nell'ordine del percorso di studio: Identify con l'inventario Nmap e una scansione Greenbone letta in priorità, Protect con l'hardening misurato prima e dopo, Detect con un evento prodotto nel laboratorio e letto con i log, Respond con la raccolta di artefatti. Ogni esercizio ha un rapporto da compilare che separa ciò che lo strumento dichiara da ciò che è stato verificato a mano, e i rapporti sono materiale di studio locale: non entrano nel repository perché descrivono le debolezze di macchine reali, e si anonimizzano con `anonymization` se vanno citati in un documento.

## Portare lo stesso studio su un'altra macchina

Tutto ciò che è specifico della macchina sta nel file dei valori: i digest delle immagini, i bersagli, i percorsi. Su un'altra macchina si copia il progetto, si installa Docker, si ricompila il file dei valori e si rilancia `su.sh`. Il laboratorio è lo stesso; cambiano solo i valori.

## Limiti dichiarati

Lo scaffold non è ancora stato tirato su: i digest nel file dei valori sono segnaposto e vanno riempiti con quelli reali delle immagini scelte, lette dal registry al momento dell'adozione. Finché non c'è una prova su una macchina, questo pacchetto è una specifica di laboratorio, non un ambiente collaudato. Su Windows il laboratorio gira dentro Docker Desktop su WSL2; su Linux direttamente su Docker. I limiti precisi di quell'infrastruttura, cioè la rete, i volumi e il fatto che Docker Desktop condivide la macchina virtuale WSL2, stanno in `docs/windows-docker-wsl-vs-linux.md` del template.
