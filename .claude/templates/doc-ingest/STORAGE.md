# Conservazione compatta delle cache locali

La scelta del formato dipende dal contenuto e dai lettori che lo usano. Questo pacchetto misura il peso effettivo e verifica il recupero prima di sostituire una rappresentazione derivata. Il risultato è il più piccolo fra i codec provati, non una pretesa di ottimo universale. La compressione conserva il documento e non attesta la sua lettura.

## Strategia per tipo di dato

| Dato | Conservazione | Controllo |
|---|---|---|
| Fonti originali, PDF, audio, video e originali Office | Byte e formato originali; nessuna ricodifica distruttiva o riduzione di risoluzione | Identità della fonte e hash conservati dal progetto |
| Memoria, codice e documenti attivi versionati | Testo UTF-8 leggibile per ricerca, diff e revisione | Controlli Git e documentali del progetto |
| Mirror di testo generati | Con `--compression auto`, minimo fra testo semplice, gzip livello 9, BZip2 livello 9 e XZ livello 9 estremo | Decodifica identica, pubblicazione atomica, verifica su disco e successivo ritiro delle sole varianti dello stesso mirror |
| Cache di testo già consumate da programmi che richiedono nomi precisi | Su Windows/NTFS, compressione trasparente LZX con `cache-storage.py ntfs`; percorso e byte esposti restano identici | SHA256 prima e dopo per ogni file, byte memorizzati misurati con l'API Windows |
| PNG derivati già referenziati | Comando `png`: ricompressione dei soli raster esattamente grigi, mantenendo nome, pixel RGBA e metadati DPI | Confronto di tutti i pixel e dei metadati; hash prima e dopo nel rapporto. Colore, animazioni e metadati non gestiti rimangono invariati |
| Nuovi raster di lettura generati | API `save_smallest_lossless`: minimo fra PNG ottimizzato, PNG grigio solo se equivalente e WebP senza perdita, se disponibile | Dimensioni e tutti i pixel RGBA identici, compresi RGB trasparenti; manifesto con formato effettivo e hash dei pixel |

I rendering intermedi si producono in una cartella temporanea del progetto, un gruppo di pagine alla volta, e si ritirano quando il foglio risultante è verificato. Si conserva il manifesto necessario a rigenerarli. Le cache non devono moltiplicare originali, fogli e pagine singole senza un uso dichiarato. Questa disciplina non autorizza cancellazioni generiche, eliminazione di originali o creazione di backup aggiuntivi: i backup seguono il mandato già in vigore nel progetto.

## Testo compresso e compatibilità

L'ingestione mantiene `plain` come comportamento storico. La scelta esplicita `auto` abilita il confronto dei codec; `gzip`, `bzip2` e `xz` restringono il confronto a quel codec e al testo semplice, che resta vincitore se la compressione ingrandisce il file. `_INDEX.md` resta leggibile e riporta il percorso effettivo. Il manifest rimane JSON leggibile e riusa gli hash delle fonti. La migrazione di un mirror invariato usa il testo già estratto, senza richiamare il convertitore.

```bash
python tools/doc-ingest.py percorso/corpus --out _notes/.tmp-doc-cache --compression auto
python tools/doc-ingest.py --read-cache _notes/.tmp-doc-cache/documento.pdf.md.bz2
python tools/cache-storage.py read _notes/.tmp-doc-cache/documento.pdf.md.xz --first 20 --last 80
```

Il suffisso del mirror dipende dal risultato e si legge nell'indice. La lettura di gzip, BZip2 e XZ è in streaming e non scrive una copia estratta. Programmi esterni che aprono direttamente i vecchi `.md` devono essere adattati al suffisso o usare `plain`; la compressione trasparente è l'alternativa per mantenere i percorsi esistenti. Un file corrotto o varianti con contenuti discordanti producono un errore e non vengono interpretati come cache assente.

La libreria standard di Python fornisce i tre codec. XZ al livello estremo può richiedere molta più memoria degli altri: la documentazione Python indica fino a circa 800 MiB per il livello 9. Il confronto viene eseguito in sequenza; si può scegliere `bzip2` o `gzip` quando quel costo non è compatibile con la macchina. Nessuna installazione o uso di GPU viene avviato dal pacchetto.

## Cache esistenti e misure fisiche

Il comando senza `--apply` misura soltanto. La radice deve essere una cartella di cache interna al progetto, senza attraversamenti di link o junction. La compressione NTFS seleziona file di testo derivati da almeno 4 KiB; esclude database, PDF, immagini e sottocartelle di backup/originali. Il comando PNG va puntato soltanto alle immagini di cache generate, mai a una raccolta di fonti. I rapporti stanno nel progetto e vengono a loro volta salvati nel formato verificato più piccolo.

```powershell
python tools/cache-storage.py ntfs --project-root . --cache _notes/99-cache --report _notes/compressione-testo.json
python tools/cache-storage.py ntfs --project-root . --cache _notes/99-cache --report _notes/compressione-testo.json --apply
python tools/cache-storage.py png --project-root . --cache _notes/99-cache/render --report _notes/compressione-png.json --apply
```

LZX è uno strato del filesystem Windows, distinto dai formati portabili `.gz`, `.bz2` e `.xz`: l'accesso diretto a quel volume da altri sistemi richiede una valutazione separata. Una copia eseguita con la normale lettura dei file su Windows conserva i byte logici verificati. `compact` non modifica impostazioni globali o CompactOS. Il comando registra gli errori e non li trasforma in successo.

## Prove e perimetro

La suite `test_cache_storage.py` esercita compressione effettiva, lettura dei file prodotti, migrazione incrementale senza nuova conversione, corruzione, varianti discordanti, confini delle scritture, conservazione di colore/trasparenza e ricompressione PNG con DPI. Richiede Pillow per i casi raster; l'uso del solo testo richiede Python con la propria libreria standard. Il test storico delle esclusioni personali rimane separato. I dati sintetici coprono la correttezza; peso e tempo si misurano anche su file reali del progetto, conservando il rapporto privato con il campione e il suo criterio di selezione.

```bash
python .claude/templates/doc-ingest/test_cache_storage.py
python .claude/templates/doc-ingest/doc-ingest.py --autotest
```

Riferimenti primari: [codec della libreria standard Python](https://docs.python.org/3/library/lzma.html), [parametri di PNG e WebP in Pillow](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html), [compressione NTFS con compact](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/compact). Il campione reale che ha motivato il metodo è descritto nel caso di studio del template; i nomi delle fonti e i percorsi privati rimangono nel progetto d'origine.
