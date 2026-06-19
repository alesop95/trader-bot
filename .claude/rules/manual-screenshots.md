# Screenshot per i passi manuali e visivi

> Regola modulare. Stabilisce come l'agente ottiene un riscontro visivo quando una parte dello
> sviluppo e necessariamente manuale e non osservabile dall'agente: chiede all'utente uno
> screenshot e lo legge dalla cartella dello strumento di cattura.

## Quando

Alcuni passi dello sviluppo producono uno stato che l'agente non puo vedere da se: l'aspetto di
una interfaccia nel browser o in una applicazione desktop, l'esito visivo di un'azione manuale,
una schermata di configurazione del sistema, un errore mostrato solo a runtime. In questi casi
l'agente non prosegue per ipotesi e non descrive cio che non ha visto: si ferma e chiede
esplicitamente all'utente di catturare uno screenshot del punto in questione, indicando con
precisione cosa deve essere inquadrato e perche serve. La richiesta e mirata, una per riscontro,
cosi che l'utente sappia esattamente cosa fotografare e l'agente non accumuli richieste vaghe.

## Da dove si legge

Su Windows lo strumento di cattura e Screenpresso, che salva nella sua cartella di default
`%USERPROFILE%\Pictures\Screenpresso`. Dopo che l'utente conferma di aver catturato lo
screenshot, l'agente individua l'immagine piu recente in quella cartella e la legge come
immagine. Lo strumento `tools/latest-screenshot.ps1` restituisce il percorso dell'immagine piu
recente e la sua eta; in alternativa lo stesso esito si ottiene con il comando seguente.

```powershell
Get-ChildItem "$env:USERPROFILE\Pictures\Screenpresso" -File |
  Where-Object { $_.Extension -in '.png', '.jpg', '.jpeg' } |
  Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName
```

L'eta dell'immagine serve a non leggere per errore uno screenshot vecchio: se la piu recente
risale a prima della richiesta, l'agente chiede conferma invece di assumere che sia quella giusta.

## Specificita di macchina e sistema operativo

Il percorso indicato e la cartella di default di Screenpresso su Windows 11; su una macchina dove
Screenpresso e configurato altrove va rilevato il percorso reale una volta e passato allo
strumento con il parametro `-Folder`, senza inventarlo. Su Linux non esiste Screenpresso: vale la
stessa logica con lo strumento di cattura locale, ad esempio Flameshot o Spectacle, e la sua
cartella di salvataggio, da rilevare al gate del sistema operativo dell'inizializzazione.

## Igiene

Gli screenshot sono materiale effimero e non si versionano. Se uno screenshot va conservato come
riferimento di una decisione o di un bug, si copia sotto `_notes/`, che e ignorato da git, mai in
una cartella tracciata. L'agente legge lo screenshot dalla cartella di cattura e non lo introduce
nel repository.
