---
name: craft-apps
description: >
  Prima di produrre o modificare un documento, una presentazione, un PDF, un'immagine, una
  grafica vettoriale, un'interfaccia, un foglio di calcolo, un audio, un video o un disegno
  CAD, e prima di scrivere uno script o installare una libreria per farlo, verifica in locale
  se le applicazioni Craft della suite ArtCraft sono installate e, se ci sono, le usa: sono
  open source, girano sulla macchina senza account, senza rete e senza consumare token, e
  hanno una riga di comando scriptabile. Copre la ricetta dal Markdown al documento o alle
  slide con il design system del progetto, l'estrazione e l'OCR di molti PDF, e la scelta fra
  riga di comando e server MCP, che ha un costo di contesto. Non installa niente da sé e non
  collega niente senza dirlo.
---

# Lavorare su un artefatto con le applicazioni Craft, in locale

Il principio è *local-first*, ed è una scelta del proprietario del 2026-10-19: quando il lavoro chiede un artefatto, si guarda prima che cosa c'è sulla macchina. Le applicazioni Craft sono tredici programmi open source, con licenza MIT o Apache-2.0 a scelta, dell'organizzazione GitHub `storytold`, e ciascuno ha accanto un binario `<app>-cli` che lavora senza finestra. Girano senza account e senza rete: PdfCraft e FigCraft lo dichiarano esplicitamente nei loro README, e per le altre nessun README lega l'uso a un accesso. I crediti a pagamento del sito getartcraft.com riguardano lo studio AI di generazione di immagini e video, che è un prodotto separato; il launcher che chiede di creare un account non è necessario, perché ogni applicazione si installa anche dai rilasci di GitHub, con l'impronta verificata. Fonti e date nel README del pacchetto `.claude/templates/craft-apps/`.

Serve quando il risultato è un file che oggi si produrrebbe aprendo a mano un programma di grafica, di video, di audio, di impaginazione, di ufficio o di PDF, oppure scrivendo uno script con una libreria che fa la stessa cosa. Non serve quando il file va soltanto letto come fonte: per quello valgono gli strumenti di lettura già presenti nel progetto, che costano meno.

Gli strumenti stanno in `.claude/templates/craft-apps/tools/`, che arriva in ogni progetto con l'allineamento; se il progetto li ha istanziati sotto `tools/`, valgono quelli. Nei comandi qui sotto `T` sta per quella cartella.

## Passo 1 - Verificare in locale che cosa c'è

```
python T/craft-apps.py rileva
```

Non usa la rete: per ogni applicazione dice versione installata e percorso del binario, su Windows sotto `Program Files` o nella cartella portabile, su Linux nel tarball, in `/usr`, in `/opt`. Esce con 0 se ne trova almeno una. Se quella che serve c'è, si usa quella, e si dichiara all'utente con versione e percorso. Se manca, si passa al passo 4 e non si ripiega in silenzio su uno script o su un servizio esterno: il punto è proprio non uscire dalla macchina senza che il proprietario lo sappia.

## Passo 2 - Nominare l'artefatto, poi l'applicazione

Si parte dal file e non dall'applicazione, perché la scelta sbagliata più comune è prendere il programma di cui si è sentito parlare invece di quello che apre quel formato.

| Artefatto | Applicazione | Binario |
|---|---|---|
| Documento di testo: DOCX, ODT, RTF, PDF, HTML, Markdown, TeX | WordCraft | `wordcraft-cli` |
| Presentazione, diapositive, temi, forme, tabelle, grafici | DeckCraft | `deckcraft-cli` |
| PDF: testo, pagine, segnalibri, moduli, OCR, oscuramento, firme, PDF/A | PdfCraft | `pdfcraft-cli` |
| Immagine raster, PSD, PNG, JPEG, TIFF, WebP, EXR | PhotoCraft | `photocraft-cli` |
| Grafica vettoriale, SVG, tracciati, ricolorazione, vettorializzazione | VectorCraft | `vectorcraft-cli` |
| Interfaccia, prototipo, mockup, esportazione in PNG, SVG, PDF | FigCraft | `figcraft-cli` |
| Impaginato, pagine, posizionamento di immagini, pubblicazione | DesignCraft | `designcraft-cli` |
| Foglio di calcolo, intervalli, formule, grafici, tabelle | GridCraft | `gridcraft-cli` |
| Animazione Lottie, motion graphics, effetti, fotogrammi chiave | EffectCraft | `effectcraft-cli` |
| Montaggio video, sequenze, importazione di media, rendering | FilmCraft | `filmcraft-cli` |
| Fotografia raw, sviluppo non distruttivo, libreria, preset | LightCraft | `lightcraft-cli` |
| Audio, sessioni, importazione, missaggio, esportazione | SoundCraft | `soundcraft-cli` |
| Disegno CAD, entità, quote | CADCraft | `cadcraft-cli` |

Se nessuna riga corrisponde, lo si dice invece di forzare la più vicina. Ogni binario elenca i propri comandi, con `<app>-cli commands`, e ne spiega uno, con `describe` o `--help`.

## Passo 3 - La ricetta dei documenti e delle slide

Il contenuto si scrive in Markdown, che resta la fonte versionabile e leggibile in un diff; si converte con l'applicazione installata; gli si applica il design del progetto. Lo fa uno strumento, per una ragione pratica: i comandi delle CLI Craft prendono parametri JSON, e Windows PowerShell 5.1 toglie le virgolette doppie dagli argomenti di un eseguibile, quindi un comando scritto a mano nel terminale arriva rotto.

```
python T/craft-documento.py documento relazione.md --out relazione.pdf --stile stile.json
python T/craft-documento.py slide sintesi.md --out sintesi.pptx --stile stile.json
python T/craft-documento.py riferimento --stile stile.json --out modello.docx
```

Il documento passa da WordCraft, verso docx, pdf, odt, rtf, html o tex. Le slide passano da DeckCraft: ogni titolo del Markdown diventa una diapositiva e ogni voce di elenco un punto, verso pptx o pdf. Il file di stile è il ponte con il design system: pochi valori, cioè font dei titoli, del testo e del codice, colore dei titoli e del testo, dimensioni per stile e colori del tema delle slide. Il design non si sceglie per abitudine ma dal repository, regola del proprietario del 2026-10-19, e `--stile auto` la applica: vale prima `.claude/craft-stile.json` del progetto, se il progetto ne ha scelto uno; altrimenti l'identità git del repository, per cui un dominio di posta dichiarato aziendale in `~/.craft-apps/stili-per-identita.json`, che sta sulla macchina e non in un repository, prende il suo design aziendale, e ogni altra identità prende il design privato `templates/craft-apps/stili/privato-tecnico-sobrio.json`, scelto quel giorno: documentazione da senior engineer, titoli in Inter, testo in Georgia, un solo accento blu ardesia, codice in Consolas. Lo strumento dice quale stile ha preso e perché. `--riferimento modello.docx` copia gli stili da un documento esistente, ma i valori del file di stile si applicano comunque, perché in WordCraft il font del corpo vive nel tema e la copia degli stili non lo porta. <!-- ref-assente -->

Prima di consegnare, l'artefatto si guarda: `wordcraft-cli render doc.docx pagina.png` e `deckcraft-cli render slide.pptx --all cartella` producono le immagini da leggere. Le applicazioni sono in alpha, e un comando che esce con 0 non prova che abbia fatto ciò che si chiedeva: in WordCraft 0.8.0 tre nomi sbagliati della chiave del font sono accettati e ignorati senza errore, ed è emerso solo aprendo `word/styles.xml`. `craft-documento.py --collaudo` rifà la prova sui byte dei file prodotti.

## Passo 4 - Se l'applicazione manca

Non si installa di propria iniziativa. Si chiede a GitHub lo stato di quella sola applicazione, che dice versione disponibile e peso del file per questa macchina, e si riporta all'utente con il comando per prenderla.

```
python T/craft-apps.py stato <app>
python T/craft-apps.py installa <app>
```

L'installazione parla solo con GitHub, verifica l'impronta SHA-256 pubblicata dal rilascio e non chiede né account né privilegi di amministratore: su Windows lo zip portabile sotto `%LOCALAPPDATA%\CraftApps`, su Linux il tarball sotto `~/.local/share/craft-apps`, che a differenza dell'AppImage espone il binario `-cli`. Chi vuole l'installazione di sistema chiede `--canale msi`, `deb` o `rpm`, e il comando privilegiato viene stampato perché lo esegua l'utente. Quasi sempre serve un'applicazione sola, e averle tutte costerebbe centinaia di megabyte per niente. Se GitHub risponde che la quota delle richieste anonime è esaurita, lo strumento lo dice e indica `GITHUB_TOKEN`.

## Passo 5 - Riga di comando o server MCP

Se il lavoro è a passo unico e si sa già che cosa fare, si usa la riga di comando: convertire, estrarre testo, rendere una pagina, applicare una lista di comandi con `run`. Costa zero token di dichiarazione e lascia l'esito in poche righe. È il caso più frequente, e va provato per primo.

Si collega il server MCP soltanto quando il lavoro è esplorativo, cioè quando bisogna guardare la struttura di un documento, provare un valore e correggerlo in giro chiuso. Il costo si misura prima di decidere, il collegamento si genera e non si scrive a mano, perché la parte che si sbaglia è il confinamento, e si dice all'utente quanto costerà e quali cartelle diventeranno il perimetro: mai la radice del disco, mai una cartella personale.

```
python T/craft-mcp.py elenca --conta
python T/craft-mcp.py genera <app> --scrittura <cartella del progetto> --per claude --scrivi
python T/craft-mcp.py controlla
```

Un server dichiarato in `.mcp.json` non entra in vigore a metà sessione: resta in attesa di approvazione fino alla sessione successiva, quindi per il lavoro di adesso si resta sulla riga di comando. Finito il lavoro lo si spegne, togliendo la voce oppure elencandola in `disabledMcpjsonServers` dentro `.claude/settings.local.json`. <!-- ref-assente -->

## Il vincolo che non si negozia

Prima di puntare una di queste applicazioni a una cartella, si guarda che cosa contiene. PdfCraft con l'OCR su una cartella di documenti dell'utente è esattamente la situazione della regola `documenti-personali.md`: un contratto, una busta paga o un documento d'identità non si aprono senza una richiesta espressa per quei documenti. Vale anche per ciò che le applicazioni lasciano dietro di sé, cioè le copie di autosalvataggio e la cache dei fotogrammi, che stanno fuori da ogni radice di confinamento: il README del pacchetto dice dove, e `craft-mcp.py controlla` lo segnala.

## Quando il lavoro è finito

Si dichiara che cosa è stato prodotto, con quale applicazione e quale versione, e se si è passati dalla riga di comando o dal server. La fonte Markdown e il file di stile restano nel progetto, così l'artefatto si rigenera invece di ritoccarsi a mano, **finché l'artefatto non viene modificato da una persona**; quando l'artefatto ha un formato nativo, per esempio un `.deckcraft`, si conserva anche l'esportazione in un formato che si legge altrove.

## Quando l'artefatto smette di essere generato

Salita il 2026-10-26 da un progetto istanziato (L-014), e corregge il paragrafo precedente nel solo caso in cui vale. La regola «si rigenera invece di ritoccarsi a mano» presuppone un autore solo. Nel momento in cui il proprietario apre l'artefatto e lo modifica, quel file ha due autori e resta uno solo, e rigenerarlo cancella le sue revisioni in silenzio: il file esiste, ha la data giusta, e nessun errore segnala la perdita. È una corsa che la persona perde sempre, perché il generatore riscrive l'intero file mentre lei ne cambia tre frasi.

Nel caso osservato un documento di decisione è stato generato, poi rivisto dal proprietario in un elaboratore di testi, poi rigenerato quattro volte per aggiungervi contenuto; le revisioni lette e trascritte una volta sono sopravvissute, quelle successive sono andate perdute e non erano recuperabili, perché la cartella non era né versionata né sincronizzata e il programma non aveva conservato una copia di salvataggio.

Ne discendono tre prescrizioni. Un artefatto diventa del proprietario nel momento in cui lui lo modifica, e da quel momento si tocca **solo sul posto**, cambiando il singolo punto richiesto con uno strumento che fallisce rumorosamente se l'ancora non individua esattamente un elemento, e prendendo una copia di salvataggio prima. Finché l'artefatto resta generato, va detto esplicitamente che rigenerarlo cancella le modifiche a mano, e va scritto nell'artefatto stesso, perché chi lo apre non ha modo di dedurlo. E se servono davvero entrambe le vie, la sorgente e l'uscita sono due file distinti con nomi diversi: il generatore produce, la persona rivede sulla sorgente o su una copia che nessuno sovrascrive.

Quando un'uscita secondaria si ricava da un artefatto diventato del proprietario, per esempio una pagina web dal documento che lui edita, la si genera **da quell'artefatto** e non dalla sorgente parallela, altrimenti le due divergono alla prima revisione.
