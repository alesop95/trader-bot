# chiudi-sessione.ps1 - Chiusura di sessione in un comando solo (variante Windows).
#
# Lega in un ordine fisso i passi che a fine sessione si facevano a mano uno per uno, e che
# invertiti producono danni diversi: i controlli prima del commit, il commit prima
# dell'impronta, l'impronta prima del wipe. Si lancia dal proprio terminale DOPO aver chiuso
# Claude Code, perche' il wipe finale lavora sui file di sessione che Claude riscrive finche' e'
# aperto.
#
#   1. stato: branch, file cambiati, diff in forma riassuntiva, senza pager;
#   2. controlli: trova da solo quelli istanziati nel progetto e li esegue tutti; se uno fallisce
#      si ferma prima del commit;
#   3. commit e push: il messaggio viene da -Messaggio, oppure da _notes/COMMIT-MSG.txt che
#      l'agente prepara a fine lavoro, oppure si chiede; poi chiede conferma, salvo -Si;
#   4. verifica che il push sia arrivato, cioe' che HEAD coincida con il ramo remoto;
#   5. registra l'impronta di ripresa con verifica-ripresa.py --registra;
#   6. wipe: esegue session-end-wipe.ps1 di ogni account che ne ha uno installato; dal
#      2026-10-09 il wipe toglie da se' cio' che appartiene a sessioni chiuse e conserva quelle
#      aperte, quindi si esegue anche con altre sessioni vive. In coda stampa con
#      stato-magazzino.ps1 che cosa resta in ogni account e quali sessioni lo trattengono.
#
# Commit e push restano un gesto dell'utente: e' l'utente a lanciare lo script e a confermare
# dopo aver visto file e messaggio. L'agente, Claude Code o Codex, prepara il messaggio, non lo usa.
#
# Lo script non ha regole proprie: esegue quelle del progetto, e dove esiste gia' un presidio lo
# lascia lavorare invece di duplicarlo.
#   - git-commands-format.md, contesto dichiarato: cartella, ramo e stato si stampano prima di
#     tutto; con HEAD staccato ci si ferma.
#   - skill identita-git (RIFERIMENTO.md): senza user.name e user.email locali ci si ferma prima del commit,
#     e l'identita' con cui si firmera' si stampa accanto al messaggio.
#   - git-commands-format.md, messaggio di commit: una riga sola, nessuna attribuzione a un agente,
#     al massimo 72 caratteri. Lo fa rispettare l'hook .githooks/commit-msg, che vale per ogni
#     commit e non solo per quelli di questo script; qui si passa soltanto la prima riga.
#   - PROJECT-SYSTEM.md sezione 12: l'impronta si registra dopo il commit, e qui solo dopo che il
#     remoto l'ha ricevuto.
#
# Uso:
#   .\tools\chiudi-sessione.ps1                         tutto, con conferma
#   .\tools\chiudi-sessione.ps1 -Messaggio "Testo"      messaggio esplicito
#   .\tools\chiudi-sessione.ps1 -Si                     senza conferma
#   .\tools\chiudi-sessione.ps1 -SoloControlli          stato e controlli, nient'altro
#   .\tools\chiudi-sessione.ps1 -NoWipe                 salta il wipe
#   .\tools\chiudi-sessione.ps1 -NoPush                 committa ma non pusha; l'impronta si registra sul commit locale
#   .\tools\chiudi-sessione.ps1 -Account account2       wipe del solo .claude-account2
#
# Nel template lo script vive in .claude\templates\tools\ e riconosce da solo di essere nel
# bundle, dove i controlli prendono le opzioni --bundle e --includi-modelli.

param(
    [string]$Messaggio = "",
    [switch]$Si,
    [switch]$SoloControlli,
    [switch]$NoWipe,
    [switch]$NoPush,
    [string]$Account = "",
    [string]$Radice = "",
    [switch]$Autotest
)

$ErrorActionPreference = "Continue"

# Gli argomenti del controllo delle lezioni, sempre come array. Un if che restituisce un array di
# un solo elemento lo consegna come stringa, e lo splat di una stringa non passa l'argomento: nei
# progetti il controllo non girava, trovato il 2026-10-20 da tre progetti istanziati.
function Argomenti-Lezioni([bool]$bundle) {
    if ($bundle) { return , @("raccogli", "--solo-locali") }
    return , @("controlla")
}

if ($Autotest) {
    $rossi = 0
    function Caso([string]$nome, [bool]$ok) { if ($ok) { Write-Host "ok   $nome" } else { $script:rossi++; Write-Host "ROSSO $nome" } }
    $p = Argomenti-Lezioni $false; $t = Argomenti-Lezioni $true
    Caso "nel progetto gli argomenti delle lezioni restano un array di un elemento" ($p -is [array] -and $p.Count -eq 1 -and $p[0] -eq "controlla")
    Caso "nel template restano due argomenti" ($t -is [array] -and $t.Count -eq 2)
    $lez = Join-Path $PSScriptRoot "lezioni-template.py"
    if (Test-Path $lez) {
        $out = (& python $lez --radice ([System.IO.Path]::GetTempPath()) @p 2>&1 | Out-String)
        Caso "lo splat consegna a lezioni-template un comando che riconosce" ($out -match "lezioni-template:")
    }
    # Controllo statico, sul sorgente: il controllo Codex deve avere la stessa condizione con cui la
    # passata genera gli adattatori, altrimenti ogni progetto senza Codex si ferma qui.
    $src = Get-Content $PSCommandPath -Raw
    Caso "il controllo Codex gira solo dove esiste .agents\skills" ($src -match 'sync-codex-skills\.py";[^\r\n]*serve = "\.agents\\skills"')
    $tutti = Join-Path $PSScriptRoot "allinea-tutti.ps1"
    if (Test-Path $tutti) { Caso "la passata usa la stessa condizione" ((Get-Content $tutti -Raw) -match "Esiste \`$prj '\.agents/skills'") }
    Write-Host ""; Write-Host "$(if ($rossi) { 'ROSSO' } else { 'verde' }): $rossi casi falliti"
    exit $(if ($rossi) { 1 } else { 0 })
}

function Titolo([string]$t) { Write-Host ""; Write-Host "== $t" -ForegroundColor Cyan }
function Ok([string]$t) { Write-Host "   ok  $t" -ForegroundColor Green }
$script:avvisi = 0
function Ko([string]$t) { $script:avvisi++; Write-Host "   KO  $t" -ForegroundColor Red }
function Nota([string]$t) { Write-Host "   $t" -ForegroundColor DarkGray }

# Radice del repository: quella indicata, altrimenti quella che contiene lo script, cosi' il
# comando funziona da qualunque cartella sia aperto il terminale.
# git scrive il percorso in UTF-8: senza questa impostazione PowerShell 5.1 lo decodifica con la
# codifica OEM e un accento nel nome della cartella diventa un percorso inesistente (2026-10-12).
if (-not $Radice) { $codificaPrec = [Console]::OutputEncoding; [Console]::OutputEncoding = [Text.Encoding]::UTF8; try { $Radice = (& git -C $PSScriptRoot rev-parse --show-toplevel 2>$null) } finally { [Console]::OutputEncoding = $codificaPrec } }
if (-not $Radice) { Write-Host "Non trovo il repository: passare -Radice." -ForegroundColor Red; exit 2 }
Set-Location $Radice
# Il bundle si riconosce da due file insieme. PACKAGES.md da solo non basta: la procedura di
# allineamento importa l'intera cartella .claude\templates\ in ogni progetto, e un progetto
# allineato veniva preso per il bundle, con i controlli e le opzioni riservati al template che
# su un progetto falliscono. PROMPT-nuovo-progetto.md vive solo nel bundle e non si importa mai.
$bundle = (Test-Path ".claude\templates\PACKAGES.md") -and (Test-Path ".claude\PROMPT-nuovo-progetto.md")

# Stessa ricerca a cascata degli hook di sessione: nel progetto gli strumenti stanno in tools\,
# nel template sotto .claude\templates\.
# In un progetto si eseguono soltanto i controlli istanziati in tools\: le copie dei modelli sotto
# .claude\templates\ sono pacchetti non ancora adottati, e lanciarli come controlli del progetto
# fermerebbe il commit per strumenti che nessuno ha scelto.
$cartelle = if ($bundle) { @("tools", ".claude\templates\tools", ".claude\templates\md-unwrap\tools",
              ".claude\templates\readme-sync\tools", ".claude\templates\fix-typography\tools",
              ".claude\templates\verifica-link\tools") } else { @("tools", "scripts") }
function Trova([string]$nome) {
    foreach ($c in $cartelle) { $p = Join-Path $c $nome; if (Test-Path $p) { return $p } }
    return $null
}

$python = $null
# Si prova un import e non basta Get-Command: l'alias del Microsoft Store risponde a
# Get-Command e poi non esegue niente.
foreach ($c in @("python", "python3", "py")) {
    if (Get-Command $c -ErrorAction SilentlyContinue) {
        & $c -c "import sys" 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { $python = $c; break }
    }
}

# ---------------------------------------------------------------------------------------------
Titolo "Stato"
# symbolic-ref e non rev-parse: funziona anche su un repository appena creato, senza commit, e
# fallisce proprio quando HEAD e' staccato, che e' il caso da intercettare prima del commit.
$ramo = (& git symbolic-ref --short -q HEAD)
if (-not $ramo) {
    Write-Host "HEAD staccato: nessun ramo in uscita. Passare a un ramo (git switch <ramo>) e rilanciare; niente e' stato committato." -ForegroundColor Red
    exit 1
}
$haOrigin = @(& git remote) -contains "origin"
Nota "repository: $Radice"
Nota "ramo: $ramo$(if ($bundle) { '   (bundle del template)' })"
if (-not $haOrigin) { Write-Host "   attenzione: nessun remoto 'origin': si committa in locale e il push si salta" -ForegroundColor Yellow }
$cambi = @(& git status --porcelain)
if ($cambi.Count -eq 0) {
    Nota "albero pulito: niente da committare"
} else {
    & git --no-pager status --short
    if (& git rev-parse -q --verify HEAD) { & git --no-pager diff --stat HEAD }
}

# Anche il nome storico con il trattino basso, che riprendi e verifica-ripresa accettano gia': un
# progetto che lo usa lo aveva cambiato a mano in questa riga, e la propagazione lo sovrascriveva.
$resume = "_notes\RESUME-PROMPT.md"
if (-not (Test-Path $resume) -and (Test-Path "_notes\RESUME_PROMPT.md")) { $resume = "_notes\RESUME_PROMPT.md" }
if (Test-Path $resume) {
    if ((Get-Item $resume).LastWriteTime.Date -lt (Get-Date).Date) {
        Write-Host "   attenzione: $resume non e' stato aggiornato oggi; l'impronta dira' che git e' noto, non dove eravamo" -ForegroundColor Yellow
    }
}

# ---------------------------------------------------------------------------------------------
Titolo "Controlli"
$b = if ($bundle) { @("--bundle") } else { @() }
$m = if ($bundle) { @("--includi-modelli") } else { @() }
$o = if ($bundle) { @("--oracle", "require") } else { @() }
$controlli = @(
    @{ n = "md-unwrap.py";            a = @("--check", "--only-tracked") + $o + @(".") },
    @{ n = "sync-readme.py";          a = @("--check") + $b; serve = "README.md" },
    @{ n = "lint-md-commands.py";     a = @(".") },
    # Pacchetto anonymization: il suo README lo istanzia in tools oppure in scripts.
    @{ n = "Test-Anonymization.py";   a = @("--quiet") },
    # Le prove della regola documenti-personali, dal 2026-10-07: i riconoscitori di IBAN e carte,
    # e l'esclusione dei documenti personali, dove doc-ingest e' istanziato. Nel bundle le lancia
    # test-documenti-personali.py, perche' i pacchetti stanno in cartelle che qui non si percorrono.
    @{ n = "Test-Anonymization.py";   a = @("--autotest") },
    @{ n = "doc-ingest.py";           a = @("--autotest") },
    @{ n = "lint-doc-references.py";  a = @("--solo-vivi") + $b },
    @{ n = "check-eol.py";            a = @(".") },
    @{ n = "misura-istruzioni.py";    a = @() },
    @{ n = "verifica-schede.py";      a = @(); serve = ".claude\context" },
    @{ n = "lint-didattica.py";       a = @(); serve = ".claude\context\studio-didattico-master.md" },
    @{ n = "fix-accents.py";          a = @("--check") + $m + @(".") },
    @{ n = "fix-dashes.py";           a = @("--check") + $m + @(".") },
    @{ n = "fix-missing-accents.py";  a = @("--check") + $m + @(".") },
    # Solo dove il progetto ha scelto Codex, cioe' dove .agents\skills esiste: la stessa condizione
    # con cui la passata genera gli adattatori. Con condizioni diverse ogni progetto senza Codex
    # si fermava qui (lezione di un progetto istanziato, 2026-10-20).
    @{ n = "sync-codex-skills.py";    a = @("--project-root", ".", "--check"); serve = ".agents\skills" },
    # Pacchetto verifica-link: istanziato se c'e' la sua configurazione; senza rete, perche' un
    # controllo prima del commit non deve dipendere dalla rete. Nel bundle girano le sole prove.
    @{ n = "verifica-link-progetto.py"; a = @("--check", "--senza-rete"); serve = "tools\verifica-link-progetto.json" },
    @{ n = "check-copie-modelli.py";  a = @(); solobundle = $true },
    @{ n = "check-catalogo.py";       a = @(); solobundle = $true },
    @{ n = "check-raggiungibilita.py"; a = @(); solobundle = $true },
    # Dal 2026-10-19: i controlli di qualita' che un progetto adotta valgono anche sulle copie del
    # template, quindi il template li tiene a zero sui propri strumenti (PROJECT-SYSTEM.md, sez. 16).
    @{ n = "lint-strumenti.py";       a = @(); solobundle = $true },
    @{ n = "test-tipografia.py";      a = @(); solobundle = $true },
    @{ n = "test-documenti-personali.py"; a = @(); solobundle = $true },
    # Dal 2026-10-20: il controllo delle fonti a monte e i segni della retrospettiva.
    @{ n = "fonti-a-monte.py";        a = @("--autotest"); solobundle = $true },
    @{ n = "retro-segnali.py";        a = @("--autotest"); solobundle = $true },
    @{ n = "lint-cultura.py";         a = @("--autotest"); solobundle = $true },
    @{ n = "verifica-link-progetto.py"; a = @("--prova"); solobundle = $true }
)

$falliti = @()
if (-not $python) {
    Ko "Python non trovato: nessun controllo eseguibile"
    $falliti += "python"
} else {
    foreach ($c in $controlli) {
        if ($c.solobundle -and -not $bundle) { continue }
        if ($c.serve -and -not (Test-Path $c.serve)) { continue }
        $p = Trova $c.n
        if (-not $p) { continue }
        $uscita = & $python $p @($c.a) 2>&1
        if ($LASTEXITCODE -eq 0) {
            Ok $c.n
        } else {
            Ko "$($c.n) (uscita $LASTEXITCODE)"
            $uscita | Select-Object -Last 15 | ForEach-Object { Write-Host "       $_" }
            $falliti += $c.n
        }
    }
}

# Le prove interne degli script PowerShell della passata, nel solo template: fino al 2026-10-20
# esistevano ma nessun controllo le lanciava, e tre difetti di quei giorni erano passati con loro
# verdi e mai eseguite.
if ($bundle -and $falliti.Count -eq 0) {
    foreach ($s in "allinea-tutti.ps1", "chiudi-allineamento.ps1", "chiudi-sessione.ps1") {
        $p = Join-Path ".claude\templates\tools" $s
        if (-not (Test-Path $p)) { continue }
        $uscita = & powershell -NoProfile -ExecutionPolicy Bypass -File $p -Autotest 2>&1
        if ($LASTEXITCODE -eq 0) { Ok "$s -Autotest" } else {
            Ko "$s -Autotest (uscita $LASTEXITCODE)"
            $uscita | Select-Object -Last 8 | ForEach-Object { Write-Host "       $_" }
            $falliti += $s
        }
    }
}

# Le lezioni verso il template, dal 2026-10-19: avvisano e non fermano il commit, perche' una
# lezione non ancora risalita non lo rende sbagliato. Nel progetto si vede che cosa il progetto
# deve al template; nel template, il debito di tutti i progetti, prima della prossima funzionalita'.
$lezioni = ".claude\templates\tools\lezioni-template.py"
if ($python -and (Test-Path $lezioni)) {
    # Nel template solo i progetti locali: la raccolta completa, VM comprese, si fa all'apertura
    # della sessione. Il 2026-10-20 la lettura via SSH ha tenuto ferma una chiusura.
    $argLez = Argomenti-Lezioni ([bool]$bundle)
    $uscitaLez = & $python $lezioni @argLez 2>&1
    $righe = @($uscitaLez | Where-Object { "$_".Trim() })
    if ($bundle) { $righe = @($righe | Select-Object -Last 3) }
    if ($righe.Count -gt 0) { Titolo "Lezioni per il template"; $righe | ForEach-Object { Write-Host "   $_" } }
}

# Le fonti a monte, dal 2026-10-20: nel template un repository citato e non censito ferma il
# commit, cosi' registro e schede entrano insieme; nel progetto il censimento avvisa e basta.
$fonti = ".claude\templates\tools\fonti-a-monte.py"
if ($python -and (Test-Path $fonti)) {
    $uscitaF = & $python $fonti censisci --check 2>&1
    $codiceF = $LASTEXITCODE
    $righeF = @($uscitaF | Where-Object { "$_".Trim() -and "$_" -notmatch '^censimento: 0 nuovi, 0 tolti' })
    if ($righeF.Count -gt 0) { Titolo "Fonti a monte"; $righeF | ForEach-Object { Write-Host "   $_" } }
    if ($codiceF -ne 0) { $falliti += "fonti-a-monte.py" }
}

# Le conversioni PowerShell che dipendono dalla cultura di sistema, dal 2026-10-20 (lezione di un
# progetto istanziato): nel template fermano il commit, nel progetto avvisano.
$cultura = ".claude\templates\tools\lint-cultura.py"
if ($python -and (Test-Path $cultura)) {
    $uscitaC = & $python $cultura . 2>&1
    $codiceC = $LASTEXITCODE
    $righeC = @($uscitaC | Where-Object { "$_".Trim() -and "$_" -notmatch '^lint-cultura: nessuna' })
    if ($righeC.Count -gt 0) { Titolo "Cultura nelle conversioni"; $righeC | Select-Object -Last 12 | ForEach-Object { Write-Host "   $_" } }
    if ($codiceC -ne 0) { $falliti += "lint-cultura.py" }
}

if ($falliti.Count -gt 0) {
    Write-Host ""
    Write-Host "Controlli falliti: $($falliti -join ', '). Mi fermo prima del commit." -ForegroundColor Red
    exit 1
}
if ($SoloControlli) { Write-Host ""; Write-Host "Controlli verdi." -ForegroundColor Green; exit 0 }

# ---------------------------------------------------------------------------------------------
$fileMsg = "_notes\COMMIT-MSG.txt"
if ($cambi.Count -gt 0) {
    Titolo "Commit"
    if (-not $Messaggio -and (Test-Path $fileMsg)) {
        $Messaggio = ((Get-Content $fileMsg -Encoding UTF8 | Where-Object { $_.Trim() }) | Select-Object -First 1)
        if ($Messaggio) { Nota "messaggio preparato dall'agente in $fileMsg" }
    }
    if (-not $Messaggio) { $Messaggio = Read-Host "   Messaggio di commit" }
    $Messaggio = "$Messaggio".Trim()
    if (-not $Messaggio) { Write-Host "Messaggio vuoto: mi fermo." -ForegroundColor Red; exit 1 }
    $nome = (& git config --local user.name); $email = (& git config --local user.email)
    if (-not $nome -or -not $email) {
        Write-Host "Identita' git locale non impostata (skill identita-git): impostare user.name e user.email del repository e rilanciare." -ForegroundColor Red
        exit 1
    }
    Write-Host "   $($cambi.Count) file  ->  `"$Messaggio`""
    Write-Host "   autore: $nome <$email>"

    if (-not $Si) {
        $azione = if ($NoPush) { "Committo tutto, senza push," } else { "Committo tutto e pusho" }
        $r = Read-Host "   $azione su '$ramo'? [s/N]"
        if ($r -notmatch '^(s|si|y|yes)$') { Write-Host "Annullato: niente e' stato committato." -ForegroundColor Yellow; exit 1 }
    }

    & git add -A
    if ($LASTEXITCODE -ne 0) { Write-Host "Stage fallito: niente e' stato committato." -ForegroundColor Red; exit 1 }
    & git commit -m $Messaggio
    if ($LASTEXITCODE -ne 0) { Write-Host "Commit rifiutato (hook o errore): correggere e rilanciare." -ForegroundColor Red; exit 1 }
    if (Test-Path $fileMsg) { Remove-Item $fileMsg -Force }
}

# ---------------------------------------------------------------------------------------------
Titolo "Push"
# -NoPush (2026-10-16, da un progetto istanziato): quando un push ha un costo da rimandare, per
# esempio un monte di minuti di CI quasi finito, la chiusura si faceva a mano commit per commit
# perche' questo script pusha sempre. Il commit resta locale e l'impronta lo registra: la ripresa
# confronta HEAD e albero di lavoro, non il remoto.
if ($NoPush) {
    Nota "push saltato su richiesta (-NoPush): il commit resta locale su '$ramo'"
} elseif (-not $haOrigin) {
    Nota "nessun remoto 'origin': push saltato, il commit resta locale"
} elseif (-not (& git rev-parse -q --verify HEAD)) {
    Nota "nessun commit sul ramo: niente da pushare"
} else {
    # Destinazione esplicita: un upstream diverso da origin non deve deviare la chiusura.
    # Un timeout SSH o un rifiuto remoto transitorio possono far fallire il push.
    # La chiusura ritenta fino a tre volte e si ferma se il remoto resta indietro.
    $attese = @(5, 15)
    for ($t = 1; $t -le 3; $t++) {
        & git push -u origin "HEAD:refs/heads/$ramo"
        if ($LASTEXITCODE -eq 0) { break }
        if ($t -eq 3) { Write-Host "Push fallito: l'impronta non si registra finche' il remoto non e' allineato." -ForegroundColor Red; exit 1 }
        Nota ("push non riuscito, ritento fra {0} secondi (tentativo {1} di 3)" -f $attese[$t - 1], ($t + 1))
        Start-Sleep -Seconds $attese[$t - 1]
    }
    $locale = (& git rev-parse HEAD)
    $refRemota = (& git ls-remote --exit-code origin "refs/heads/$ramo")
    if ($LASTEXITCODE -ne 0 -or -not $refRemota) { Ko "verifica del ramo remoto fallita"; exit 1 }
    $suRemoto = ($refRemota -split '\s+')[0]
    if ($locale -ne $suRemoto) { Ko "HEAD $locale diverso dal remoto $suRemoto"; exit 1 }
    Ok "HEAD e remoto coincidono su '$ramo' ($($locale.Substring(0,7)))"
}

# ---------------------------------------------------------------------------------------------
# Sul template, una modifica a .claude/ si propaga ai progetti solo con la passata di
# allinea-tutti: lo si ricorda qui, dopo il push, invece di affidarlo alla memoria.
if ($bundle) {
    $ps = Trova "passata-in-sospeso.py"
    if ($ps -and $python) {
        Titolo "Propagazione ai progetti"
        & $python $ps | ForEach-Object { Write-Host "   $_" }
    }
}

# ---------------------------------------------------------------------------------------------
Titolo "Impronta di ripresa"
$vr = Trova "verifica-ripresa.py"
if ($vr -and $python) {
    & $python $vr --radice $Radice --registra
    if ($LASTEXITCODE -eq 0) { Ok "impronta registrata" } else { Ko "verifica-ripresa.py --registra (uscita $LASTEXITCODE)" }
} else {
    Nota "verifica-ripresa.py non istanziato: passo saltato"
}

# ---------------------------------------------------------------------------------------------
# Uscita finale: 0 se tutto e' andato, 3 se il commit e' fatto ma un passo successivo ha dato KO,
# cosi' un falso "completata" non nasconde un'impronta non registrata.
function Fine([string]$extra) {
    Write-Host ""
    if ($script:avvisi -gt 0) { Write-Host "Chiusura completata con $($script:avvisi) avvisi (KO sopra)$extra." -ForegroundColor Yellow; exit 3 }
    Write-Host "Chiusura completata$extra." -ForegroundColor Green; exit 0
}
if ($NoWipe) { Fine ", wipe saltato su richiesta" }
Titolo "Wipe del magazzino nascosto"

# Una sessione Claude Code aperta riscrive i propri file dopo il wipe e ne vanificherebbe una
# parte, e gli store per-account li condividono tutte le sessioni dello stesso account. Si
# guardano quindi solo i processi della CLI e dell'estensione per editor; l'app desktop ha
# un'altra cartella e non conta.
$aperte = @(Get-Process -Name claude -ErrorAction SilentlyContinue | Where-Object { $_.Path -and $_.Path -notmatch '\\WindowsApps\\' })
$script = @(Get-ChildItem $env:USERPROFILE -Directory -Filter ".claude*" -Force -ErrorAction SilentlyContinue |
    Where-Object { -not $Account -or $_.Name -eq ".claude-$Account" -or $_.Name -eq $Account } |
    ForEach-Object { Join-Path $_.FullName "hooks\session-end-wipe.ps1" } | Where-Object { Test-Path $_ })

if ($script.Count -eq 0) {
    Nota "nessuno script di wipe installato negli account: passo saltato"
} else {
    if ($aperte.Count -gt 0) {
        Write-Host "   $($aperte.Count) processi Claude Code ancora aperti (CLI o editor): il wipe conserva le loro sessioni e toglie tutte le altre. Una copia del wipe anteriore al 2026-10-09 invece rimanda tutto." -ForegroundColor Yellow
    }
    foreach ($s in $script) {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $s
        if ($LASTEXITCODE -eq 0) { Ok $s } else { Ko "$s (uscita $LASTEXITCODE)" }
    }
}

# Che cosa resta dopo il wipe, o dopo il suo rinvio: senza questo resoconto un rinvio si
# leggeva solo nel diario dell'account, che nessuno apre. Lo strumento e' in sola lettura;
# si cerca accanto a questo script e, in un progetto che non lo ha, nelle home degli account.
$stato = @((Join-Path $PSScriptRoot 'stato-magazzino.ps1')) +
    @(Get-ChildItem $env:USERPROFILE -Directory -Filter ".claude*" -Force -ErrorAction SilentlyContinue |
      ForEach-Object { Join-Path $_.FullName "hooks\stato-magazzino.ps1" }) |
    Where-Object { Test-Path $_ } | Select-Object -First 1
if ($stato) { & powershell -NoProfile -ExecutionPolicy Bypass -File $stato }
else { Nota "stato-magazzino.ps1 non trovato: resoconto dei residui saltato" }

Fine ""
