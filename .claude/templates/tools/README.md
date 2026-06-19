# tools

## render-diagrams.mjs

Rende i diagrammi Mermaid di `.claude/context/diagrams/*.mmd` nei corrispondenti `.svg`, riusando il browser Chromium-based gia installato sul sistema (Edge o Chrome). Non scarica il Chromium di Puppeteer: il download e disattivato e si punta al browser locale, cosi la generazione resta snella e ogni progetto e autonomo.

Uso:

```
node tools/render-diagrams.mjs
```

Per rendere una cartella diversa:

```
node tools/render-diagrams.mjs <cartella>
```

Prerequisiti: Node e un browser Edge o Chrome. Alla prima esecuzione `npx` scarica i soli script di mermaid-cli, mai un browser. Se l'autorilevamento del browser fallisce, forzalo con la variabile d'ambiente `PUPPETEER_EXECUTABLE_PATH` puntata all'eseguibile di Edge o Chrome.

I `.svg` prodotti sono versionati accanto ai `.mmd` sorgente, secondo l'anatomia canonica del sistema di progetto.

## check-account-hygiene.ps1

Verifica, in sola lettura, che l'account Claude Code attivo rispetti l'igiene del magazzino nascosto richiesta dal sistema: `autoMemoryEnabled: false` e un hook `SessionEnd` che esegue `session-end-wipe`. Si esegue al Passo 0 dell'inizializzazione o dell'allineamento di un progetto, e non modifica nulla: stampa un report PASS/FAIL e, se l'account non e' in regola, indica cosa aggiungere. Vedi PROJECT-SYSTEM.md sezione 15.

```
powershell -NoProfile -ExecutionPolicy Bypass -File .claude/templates/tools/check-account-hygiene.ps1
```

Determina l'account attivo da `CLAUDE_CONFIG_DIR`, con fallback su `%USERPROFILE%\.claude`, e ne legge il `settings.json`. Esce con codice 0 se l'account e' in regola, 1 altrimenti. Su Linux la variante equivalente e `check-account-hygiene.sh` (`bash .claude/templates/tools/check-account-hygiene.sh`), che legge il JSON con `python3` e, in sua mancanza, ricade su un controllo testuale.

## session-end-wipe.ps1

Template del wipe del magazzino nascosto, da installare per-account, non per-progetto. Si copia in `<CLAUDE_CONFIG_DIR>\hooks\session-end-wipe.ps1`, si sostituisce il segnaposto `<CLAUDE_CONFIG_DIR>` col path della home dell'account, e si registra come hook `SessionEnd` nel `settings.json` dell'account. A ogni chiusura di sessione ripulisce i transcript e la memoria nascosta dei progetti non preservati e gli store per-account effimeri, lasciando intatti i progetti il cui slug corrisponde al prefisso da preservare, la configurazione, il login, le skill e i plugin. Il prefisso dipende dalla macchina: su questa macchina i progetti di sviluppo stanno sotto `D:`, quindi `D--*`, ma su un'altra macchina va impostato di conseguenza. Su Linux la variante equivalente e `session-end-wipe.sh`, registrata con un hook il cui comando e `bash "<CLAUDE_CONFIG_DIR>/hooks/session-end-wipe.sh"`. La procedura completa e le sue varianti sono in PROJECT-SYSTEM.md sezione 15.

## latest-screenshot.ps1

Restituisce il percorso dell'immagine piu recente nella cartella di cattura di Screenpresso e la sua eta in secondi, perche l'agente legga lo screenshot appena catturato dall'utente per un passo manuale e visivo dello sviluppo. Si usa insieme alla regola `.claude/rules/manual-screenshots.md`, che stabilisce quando l'agente deve chiedere uno screenshot.

```
powershell -NoProfile -ExecutionPolicy Bypass -File tools/latest-screenshot.ps1
```

Cartella di default `%USERPROFILE%\Pictures\Screenpresso`, sovrascrivibile con `-Folder`. Con `-MaxAgeSeconds N` pretende che l'immagine piu recente sia stata salvata da meno di N secondi, per non leggere per errore uno screenshot vecchio. Esce 0 se trova un'immagine valida, 1 altrimenti.

## claude-incognito.ps1 / claude-incognito.sh

Avvia una sessione Claude Code effimera: redirige `HOME` e le cartelle XDG su una directory temporanea e azzera `CLAUDE_CONFIG_DIR`, cosi la sessione non legge ne scrive nell'account reale e parte vergine; la temp si rimuove alla chiusura. Complementa `session-end-wipe` (quello pulisce dopo, questo non scrive nemmeno) ed e' utile per lavorare su materiale sensibile.

```
powershell -NoProfile -ExecutionPolicy Bypass -File tools/claude-incognito.ps1 -ProjectDir "<percorso>"
```

Su Linux la variante e `claude-incognito.sh` (`bash claude-incognito.sh <percorso>`). La tecnica si basa sulla specifica XDG Base Directory piu la redirezione di `HOME`; vedi PROJECT-SYSTEM.md sezione 15.
