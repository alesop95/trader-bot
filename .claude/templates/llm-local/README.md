# Pacchetto opzionale `llm-local`

<!-- readme-summary: offload del lavoro meccanico a un modello locale su CPU con colibri, con rilevamento dell'ambiente, runner a lotti riprendibile e banchi di velocità e correttezza -->

> Sposta il lavoro meccanico a lotti su un modello linguistico locale, su CPU e senza scheda grafica, servito da colibri, così non costa token di un agente a pagamento. Dà tre cose: un rilevamento che dice se la macchina è pronta e, su Windows, che si passa da WSL; un runner che manda un lotto al modello locale e ne raccoglie gli esiti, riprendibile e componibile con `lavoro-a-lotti`; e due banchi che misurano velocità e correttezza. A cosa serve, in quali compiti e fasi di progetto, e quali progetti ne giovano, sta in `docs/offload-modello-locale.md` del template. Settore del catalogo: «Modelli locali e inferenza». Il filone con le misure è `docs/filone-llm-locali-senza-gpu.md`.

## A chi serve

A un progetto che vuole scaricare dal conto dei token il lavoro meccanico, cioè cercare, estrarre, classificare, convertire e contare su molti elementi, mandandolo a un modello locale che costa corrente invece che token. E a un progetto che deve elaborare materiale che non può uscire dalla macchina o lavorare senza rete. Non serve a chi vuole un sostituto della conversazione principale: quella resta sul modello capace, perché un modello su CPU di casa non regge i passi su cui si appoggia il passo successivo, che la regola `token-economy.md` vieta di delegare.

## Che cosa istanzia

Nel progetto che lo adotta scaffolda cinque strumenti e un file di parametri. Il rilevamento, `tools/rileva.sh` e su Windows l'involucro `tools/Rileva-ModelloLocale.ps1` che entra in WSL, dice in sola lettura se l'ambiente è adatto, se colibri è compilato, quali modelli sono presenti e se l'endpoint è in ascolto. Il runner di offload, `tools/offload-lotto.py`, manda un lotto di compiti al modello locale e ne scrive gli esiti su disco, saltando quelli già fatti. I due banchi, `tools/bench-colibri.sh` per la velocità e `tools/bench-correttezza.py` con `fixtures/` per la correttezza, misurano se un modello conviene. Il file `llm-local.valori.esempio.sh` si copia in `llm-local.valori.sh`, ignorato da git, e si compila con i percorsi reali. Non scarica modelli e non installa colibri: sono passi espliciti, perché un modello pesa decine o centinaia di gigabyte e l'installazione tocca la macchina.

## Verificare se è pronto, e mandare un lotto

Il primo gesto è il rilevamento. Su Windows, dalla radice del progetto, `powershell -File .claude/templates/llm-local/tools/Rileva-ModelloLocale.ps1`; su Linux, `bash tools/rileva.sh`. Dice che cosa manca e, se tutto c'è, che un modello è utilizzabile. Poi si avvia il servizio con `coli serve` e si manda il lotto, un JSONL con una riga per elemento, ciascuna con un `id` e un `prompt`:

```bash
python3 tools/offload-lotto.py --base-url http://127.0.0.1:8000/v1 --model <id> \
  --ingresso lotto.jsonl --uscita esiti.jsonl --max-tokens 64
```

Gli esiti sono un JSONL che conserva l'elemento e la risposta grezza, non una decisione presa: la verifica a valle resta di chi li usa, perché nemmeno un buon modello locale è esatto sempre. Il lavoro è riprendibile, quindi una corsa interrotta riparte dove si era fermata, ed è la stessa forma del pacchetto `lavoro-a-lotti`, con cui si compone.

## Perché colibri e perché misurare

colibri tiene su disco la parte a esperti di un modello e la legge quando serve, quindi un modello enorme parte anche con poca RAM. Ne segue che la RAM non decide se il modello gira ma quanto spesso il motore torna al disco, cioè la velocità, e questo si vede solo misurando sulla macchina vera. Il banco prende lo stesso modello con due tetti di RAM diversi e registra, per ciascuno, le parole al secondo in decodifica, la memoria massima e i byte letti dal disco.

La scelta dei modelli con cui si misura dipende dalla domanda. Per decidere fra due tagli di RAM si prende un modello piccolo, che dice se il taglio basso regge il lavoro quotidiano, e un modello grande misurato dall'autore proprio a quei tagli, che dice che cosa si guadagna salendo. La spiegazione estesa, con i due modelli scelti per il collaudo su questa macchina, sta in `C:/colibri-models/LEGGIMI.md` sulla macchina di sviluppo e nel filone.

## Come si limita la RAM senza toglierla alla macchina

Non si cambia la RAM fisica e non si cambia il tetto globale di WSL, che fermerebbe anche altro. Il limite si dà a colibri con il suo parametro `--ram`, che è ciò con cui il motore dimensiona la cache degli esperti. Una lezione misurata il 2026-10-19 ha corretto la prima versione del banco, che imponeva il limite dall'esterno con un gruppo di controllo stretto: quel limite non riduce la cache, la sopprime, perché colibri non lo legge come budget e il gruppo di controllo gli impedisce di allocarla, lasciandola vuota e falsando la prova. Il banco usa quindi `--ram` come limite vero e tiene il gruppo di controllo `systemd-run --user --scope -p MemoryMax=...` solo come muro di sicurezza qualche gigabyte sopra il budget, non come limite. Il dettaglio sta in `docs/filone-llm-locali-senza-gpu.md` del template.

## Recap d'uso

Prerequisiti: colibri compilato (su Linux `gcc`, `make`, OpenMP e `git`), un modello già scaricato in una cartella su disco veloce, e, dentro WSL, il modello fuori da `/mnt/c`. Poi si copia il file dei valori e si lancia il banco una volta per tetto di RAM.

```bash
cp llm-local.valori.esempio.sh llm-local.valori.sh
# si compila llm-local.valori.sh con i percorsi reali
bash tools/bench-colibri.sh --valori llm-local.valori.sh --modello qwen36 --ram 16G
bash tools/bench-colibri.sh --valori llm-local.valori.sh --modello qwen36 --ram 32G
```

Ogni corsa scrive una riga nella cartella delle misure indicata dai valori, con data, modello, tetto, parole al secondo, memoria massima e byte letti. Il confronto fra le righe a 16 e a 32 è la risposta.

## Portare lo stesso studio su un'altra macchina

Il banco non ha dentro nessun percorso né nessun numero di questa macchina: tutto sta nel file dei valori. Su un'altra macchina si installa colibri, si scarica il modello, si copia il file dei valori e lo si ricompila con i percorsi di là, e si rilancia. L'esito vale per la CPU e il disco di quella macchina, e il banco lo registra accanto alla misura, perché una velocità senza l'hardware su cui è stata presa non si confronta.

## La misura che conta davvero

La velocità è metà della risposta. L'altra metà è se il lavoro meccanico esce corretto da un modello piccolo: un banco che misurasse solo le parole al secondo direbbe che il modello è veloce, non che è utile. La prova che chiude il filone prende un lotto reale e verificabile, per esempio classificare un insieme di file su etichette chiuse di cui si conosce già la risposta giusta, lo manda al modello locale e conta quante risposte sono esatte. Un modello che macina veloce ma sbaglia una classificazione su cinque non scarica lavoro da Claude: lo sposta soltanto, e la correzione costa più del risparmio. Questo secondo banco va accanto a `bench-colibri.sh` e usa lo stesso servizio locale.

## Come misura, e che cosa è confermato

Il banco non reinventa la misura: tiene il server `coli serve` sotto il tetto di RAM con il gruppo di controllo, e lo interroga con l'harness ufficiale del repository, `c/tools/benchmark_http_serving.py`, che produce un rapporto con token, durata e tempo al primo token. L'endpoint è compatibile con quello di OpenAI, e colibri ne espone anche uno compatibile con quello di Anthropic: confermato alla fonte il 2026-10-16 in `docs/api.md` del repository clonato. È questo che rende reale l'offload del lavoro meccanico, perché uno script interroga il modello locale come interrogherebbe un'API in cloud.

## Stato del collaudo

La catena è stata provata per intero il 2026-10-19 su una macchina Windows con WSL, su CPU e senza scheda grafica, con due modelli di taglia opposta. I due banchi funzionano: `bench-colibri.sh` avvia `coli serve` sotto il gruppo di controllo e lo misura con l'harness ufficiale; `bench-correttezza.py` interroga l'endpoint con un lotto di dodici classificazioni a risposta nota. Il modello piccolo, OLMoE, è veloce ma inutile: 15,7 token al secondo e correttezza del 16,7 per cento. Il modello grande, Qwen3-Coder-30B-A3B, è lento ma affidabile: circa 1,9 token al secondo e correttezza del 91,7 per cento. Qwen3.6-35B-A3B, provato come alternativa, fa meglio su entrambi: 100 per cento di correttezza e 2,81 token al secondo, ed è il modello di riferimento consigliato. Il runner `offload-lotto.py` è stato provato dal vivo sullo stesso modello: elabora un lotto e, rilanciato, salta gli elementi già fatti, cioè è riprendibile come promette. Il pacchetto è quindi validato, e con esso la risposta: l'offload del lavoro meccanico su un modello locale è realizzabile con un modello adeguato, per lavoro a lotti e non interattivo, con un controllo di correttezza a valle. Sulla RAM la misura è conclusa: a 16 e a 32 GB la velocità è uguale anche su carico vario, perché su questa CPU il collo di bottiglia è il calcolo e non il disco, quindi 16 GB bastano. Il dettaglio, con la spiegazione dei termini, sta in `docs/filone-llm-locali-senza-gpu.md` del template.

## Limiti dichiarati

La pipeline è provata, ma nessun modello adatto all'offload reale è ancora stato validato: finché un modello non supera la correttezza che il progetto richiede, questo pacchetto dà gli strumenti per misurare, non un modello pronto da usare. Perché la misura dentro WSL non sia falsata dal filesystem lento e dal tetto di RAM dinamico, vale quanto scritto in `docs/windows-docker-wsl-vs-linux.md` del template. Perché la misura dentro WSL non sia falsata dal filesystem lento e dal tetto di RAM dinamico, vale quanto scritto in `docs/windows-docker-wsl-vs-linux.md` del template.
