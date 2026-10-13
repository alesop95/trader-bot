---
name: craft-apps
description: >
  Porta un artefatto visivo o documentale dentro il lavoro della sessione usando le
  applicazioni Craft installate sulla macchina, scegliendo fra riga di comando e server MCP
  secondo la forma del lavoro invece che per abitudine. Si carica quando serve modificare,
  ispezionare, convertire o rendere un'immagine, un PSD, un file vettoriale, un'animazione
  Lottie o un progetto di motion graphics, un PDF, un impaginato, un documento di testo, un
  foglio di calcolo, una presentazione, un disegno CAD, un file audio o un montaggio video;
  quando serve estrarre o cercare il testo di molti PDF, riconoscerne il testo con l'OCR,
  oscurarne una parte o toglierne le informazioni nascoste; quando una figura di una
  pubblicazione va prodotta o ritoccata; e quando si deve decidere se collegare uno di questi
  server MCP a una sessione, perché quella decisione ha un costo di contesto che va speso
  sapendo. Non installa niente da sé e non collega niente senza dirlo.
---

# Lavorare su un artefatto con le applicazioni Craft

## Quando questa skill serve davvero, e quando no

Serve quando il risultato che l'utente chiede è un file che oggi si produrrebbe aprendo a mano un programma di grafica, di video, di audio, di impaginazione o di PDF. Non serve quando il file va soltanto letto come fonte: per quello valgono gli strumenti di lettura già presenti nel progetto, che costano meno. La distinzione è fra consumare un artefatto e produrne o modificarne uno.

## Passo 1 - Nominare l'artefatto, poi l'applicazione

Si parte dal file e non dall'applicazione, perché la scelta sbagliata più comune è prendere il programma di cui si è sentito parlare invece di quello che apre quel formato. La corrispondenza è questa.

| Artefatto | Applicazione | Binario |
|---|---|---|
| Immagine raster, PSD, PNG, JPEG, TIFF, WebP, EXR | PhotoCraft | `photocraft-cli` |
| Grafica vettoriale, SVG, tracciati, ricolorazione, vettorializzazione | VectorCraft | `vectorcraft-cli` |
| Animazione Lottie, motion graphics, effetti, composizioni, fotogrammi chiave | EffectCraft | `effectcraft-cli` |
| Montaggio video, sequenze, importazione di media, rendering | FilmCraft | `filmcraft-cli` |
| Fotografia raw, sviluppo non distruttivo, libreria, preset | LightCraft | `lightcraft-cli` |
| PDF: testo, pagine, segnalibri, moduli, OCR, oscuramento, firme, PDF/A | PdfCraft | `pdfcraft-cli` |
| Impaginato, pagine, posizionamento di immagini, pubblicazione | DesignCraft | `designcraft-cli` |
| Documento di testo, DOCX | WordCraft | `wordcraft-cli` |
| Audio, sessioni, importazione, missaggio, esportazione | SoundCraft | `soundcraft-cli` |
| Presentazione, diapositive, forme, tabelle, grafici | DeckCraft | `deckcraft-cli` |
| Disegno CAD, entità, quote | CADCraft | `cadcraft-cli` |
| Foglio di calcolo, intervalli, formule, grafici, tabelle | GridCraft | `gridcraft-cli` |

Se nessuna riga corrisponde, lo si dice invece di forzare la più vicina: la suite non copre tutto, e per molti domini esiste uno strumento specializzato che il progetto già usa.

## Passo 2 - Chiedere a GitHub quella sola applicazione

Non si presume che la suite sia installata, e non si pretende che lo sia: quasi sempre serve un'applicazione sola, e averle tutte costerebbe quasi seicento megabyte per niente. Lo stato di quella sola si chiede sul momento.

```
python tools/craft-apps.py stato <app>
```

Il comando interroga i rilasci di GitHub e risponde con quattro cose per questa macchina: la versione installata se c'è, l'ultima pubblicata, il peso del file che servirebbe per questo sistema, questa architettura e questo canale, e l'esito. Il peso viene dal rilascio e non da una tabella, perché la domanda che segue sempre a «non installata» è quanto costa averla, e una cifra ricordata invecchia a ogni versione.

Se manca, non si installa di propria iniziativa. Si riporta all'utente la versione, il peso misurato e il comando per prendere quella sola applicazione, e si aspetta la sua risposta, perché installare aggiunge un programma alla sua macchina.

```
python tools/craft-apps.py installa <app>
```

Il canale predefinito non chiede privilegi di amministratore: su Windows lo zip portabile sotto `%LOCALAPPDATA%\CraftApps`, su Linux il tarball sotto `~/.local/share/craft-apps`. Su Linux il tarball è preferito all'AppImage per una ragione che riguarda proprio questa skill: l'AppImage tiene il binario `<app>-cli` dentro di sé, quindi l'agente non lo trova e il collegamento MCP non si può generare, mentre il tarball espone `bin/<app>` e `bin/<app>-cli` affiancati. Chi vuole l'installazione di sistema chiede `--canale msi`, `deb` o `rpm`, e il comando privilegiato viene stampato perché lo esegua l'utente.

Se GitHub risponde che la quota delle richieste anonime è esaurita, lo strumento lo dice e indica `GITHUB_TOKEN`; non si inventa una versione né si procede alla cieca. Se la macchina è senza rete, si dice che lo stato non è verificabile adesso e si lavora con ciò che è già installato, oppure si rimanda.

## Passo 3 - Scegliere la via, che è la decisione che costa

La domanda non è quale via sia più potente ma quale forma abbia il lavoro, e la risposta decide quanto contesto si spende.

Se il lavoro è a passo unico e si sa già che cosa fare, si usa la riga di comando. Convertire, estrarre testo, rendere un fotogramma, applicare una lista di azioni a una cartella, esportare: tutto questo è un comando che nasce e muore, costa zero token di dichiarazione e lascia l'esito in un riepilogo di poche righe. È il caso più frequente, e va provato per primo.

Si collega il server MCP soltanto quando il lavoro è esplorativo, cioè quando bisogna guardare la struttura di un documento, provare un valore, rivedere il risultato e correggerlo in giro chiuso. Lì il server ripaga il suo costo, perché evita decine di avvii di processo e tiene lo stato aperto. Il costo si misura prima di decidere, non dopo.

```
python tools/craft-mcp.py elenca --conta
```

## Passo 4 - Collegare, confinando, e dichiarando il costo

Il collegamento si genera e non si scrive a mano, perché la parte che si sbaglia è sempre il confinamento.

```
python tools/craft-mcp.py genera <app> --scrittura <cartella del progetto> --per claude --scrivi
python tools/craft-mcp.py controlla
```

Prima di generarlo si dice all'utente quanto costerà quel server in contesto, con il numero misurato al passo precedente, e si nominano le cartelle che diventeranno il perimetro. Un server Craft si collega a una cartella del progetto, mai alla radice del disco e mai a una cartella personale dell'utente.

Il collegamento non entra in vigore a metà sessione: un server dichiarato in `.mcp.json` resta in attesa di approvazione e non viene connesso finché la sessione successiva non lo approva. Lo si dice all'utente invece di lasciarglielo scoprire, e per il lavoro di adesso si resta sulla riga di comando.

## Passo 5 - Spegnere quando il lavoro è finito

Un server che resta collegato continua a costare in ogni sessione successiva, comprese quelle che non toccano artefatti. Finito il lavoro si toglie la voce da `.mcp.json`, oppure la si lascia dichiarata e la si elenca in `disabledMcpjsonServers` dentro `.claude/settings.local.json`: un server disabilitato resta scritto, pronto da riaccendere, e non viene connesso. È la forma preferibile in un progetto che tocca artefatti ogni tanto, perché conserva la configurazione confinata già verificata invece di farla riscrivere ogni volta.

## Il vincolo che non si negozia

Prima di puntare una di queste applicazioni a una cartella, si guarda che cosa contiene. PdfCraft con l'OCR su una cartella di documenti dell'utente è esattamente la situazione della regola `documenti-personali.md`: un contratto, una busta paga o un documento d'identità non si aprono senza una richiesta espressa per quei documenti, e il nome del file serve a riconoscerli ed escluderli, non a decidere di leggerli. Vale anche per ciò che le applicazioni lasciano dietro di sé, cioè le copie di autosalvataggio e la cache dei fotogrammi renderizzati, che stanno fuori da ogni radice di confinamento e fuori da ogni repository: lo studio del pacchetto dice dove, e `craft-mcp.py controlla` segnala `--autosave` proprio per questo.

## Quando il lavoro è finito

Si dichiara che cosa è stato prodotto, con quale applicazione e quale versione, e se si è passati dalla riga di comando o dal server. Un artefatto generato da un'applicazione in alpha si guarda prima di considerarlo buono, e quando l'artefatto ha un formato nativo, per esempio un `.ecproj`, si conserva anche l'esportazione in un formato che si legge altrove.
