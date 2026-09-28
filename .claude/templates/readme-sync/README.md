# Pacchetto opzionale: readme-sync

<!-- readme-summary: indice, pacchetti e link del README aggiornati da fonti verificabili -->

Un README pubblico serve a chi arriva dal clone: deve spiegare il progetto, offrire percorsi brevi per orientarsi e non promettere file o pacchetti che non esistono. Il pacchetto separa le parti verificabili automaticamente dalla prosa, che richiede ancora una lettura del codice e una decisione editoriale.

## Che cosa istanzia

| Fonte del pacchetto | Nel progetto |
|---|---|
| `tools/sync-readme.py` | `tools/sync-readme.py` |
| `skills/sync-readme/SKILL.md` | `.claude/skills/sync-readme/SKILL.md` |
| `githooks/pre-commit` | `.githooks/pre-commit` |
| `githooks/commit-msg` | `.githooks/commit-msg` |

La skill va esposta a Codex tramite il normale `sync-codex-skills.py`. In questo repository il programma è usato direttamente dalla sua fonte sotto `.claude/templates/readme-sync/tools/`; il codice resta uno solo.

## Che cosa aggiorna

Il programma inserisce e rigenera il blocco `sync-readme:toc` a partire dai titoli `##` del README. L'indice offre quattro accessi rapidi e un elenco completo comprimibile con ancore GitHub. Verifica che i link locali puntino a file presenti e che le ancore interne esistano. Un secondo passaggio non cambia il file; formato di fine riga, BOM e newline finale restano quelli originali.

Solo nel repository del template, con `--bundle`, rigenera anche il blocco `sync-readme:packages`: legge le voci e i settori di `.claude/templates/PACKAGES.md`, include ogni pacchetto a cartella con README e misura i conteggi. Le descrizioni brevi restano quelle curate nel blocco esistente; per un pacchetto nuovo si aggiunge al suo README `<!-- readme-summary: descrizione breve -->`. Se la descrizione manca, il programma si ferma invece di inventarla. Le voci del catalogo senza cartella sono strumenti o servizi esterni e non entrano nell'indice dei README.

## Come si usa

In un progetto che ha adottato il pacchetto:

```bash
python tools/sync-readme.py --write
python tools/sync-readme.py --check
```

Nel repository del template:

```bash
python .claude/templates/readme-sync/tools/sync-readme.py --write --bundle
python .claude/templates/readme-sync/tools/sync-readme.py --check --bundle
```

`--check` è il modo predefinito: non scrive e restituisce 1 se i blocchi generati sono indietro, 2 se mancano file, link o metadati richiesti. È adatto a un controllo prima dei comandi git o in CI. `--write` aggiorna solo i blocchi marcati e non committa; dopo l'esecuzione si rilegge il diff.

Per coprire anche i commit manuali si copia l'hook in `.githooks/pre-commit`, lo si rende eseguibile su POSIX e si imposta una volta `git config --local core.hooksPath .githooks`. Il file dell'hook è versionato, la scelta di usarlo vive nella configurazione git locale del clone. Prima del commit l'hook esegue `--write`, poi ferma il commit se il README è cambiato o differisce dalla versione in stage: l'utente rivede il diff e lo aggiunge manualmente. L'hook non esegue `git add`, commit o push. Se il pacchetto non è installato, non fa nulla. Nel repository del template lo stesso hook usa il sorgente del pacchetto e il modo `--bundle`. Git ammette un solo file `pre-commit`, quindi l'hook, dopo il proprio controllo, esegue in ordine gli script della cartella `.githooks/pre-commit.d/`: è il punto in cui altri pacchetti aggiungono un passo senza modificare questo file. Uno script che esce diverso da zero ferma il commit, uno che vuole soltanto avvisare esce zero. Gli script si eseguono con `sh` e non per bit di esecuzione, perché su Windows quel bit non viaggia con il clone. Accanto a `pre-commit` si copia `commit-msg`, che attua la sezione sul messaggio di commit della regola `git-commands-format.md`: rifiuta le attribuzioni a un agente, cioè righe `Co-Authored-By` e firme generate, e un oggetto oltre i 72 caratteri, per ogni commit, che parta a mano, da `chiudi-sessione` o da un agente.

## La parte che resta editoriale

Un programma non può sapere se una modifica allo stack renda falsa una frase del README. La skill `sync-readme` confronta il README con codice, documentazione canonica, catalogo e diff recenti; aggiorna la prosa necessaria, poi invoca il programma per indice e inventario. Il controllo automatico rende visibile il drift meccanico e impedisce link rotti, ma non certifica che ogni affermazione sia vera. Il README resta una presentazione pubblica del progetto, quindi dati privati e identificativi reali restano fuori.

## Quando offrirlo

Si offre a un progetto con README pubblico che cresce nel tempo, soprattutto se ha molte sezioni, pacchetti o documenti collegati. Per un README di poche righe il controllo aggiungerebbe più struttura di quella che serve. Non crea un README in un progetto che ha scelto di non averlo: l'adozione del README resta il gate esplicito dello standard.
