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
#   6. wipe: esegue session-end-wipe.ps1 di ogni account che ne ha uno installato, ma solo se
#      nessuna sessione Claude Code da terminale o da editor e' ancora aperta.
#
# Commit e push restano un gesto dell'utente: e' l'utente a lanciare lo script e a confermare
# dopo aver visto file e messaggio. L'agente, Claude Code o Codex, prepara il messaggio, non lo usa.
#
# Lo script non ha regole proprie: esegue quelle del progetto, e dove esiste gia' un presidio lo
# lascia lavorare invece di duplicarlo.
#   - git-commands-format.md, contesto dichiarato: cartella, ramo e stato si stampano prima di
#     tutto; con HEAD staccato ci si ferma.
#   - git-identity-and-repo.md: senza user.name e user.email locali ci si ferma prima del commit,
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
#   .\tools\chiudi-sessione.ps1 -Account account2       wipe del solo .claude-account2
#
# Nel template lo script vive in .claude\templates\tools\ e riconosce da solo di essere nel
# bundle, dove i controlli prendono le opzioni --bundle e --includi-modelli.

param(
    [string]$Messaggio = "",
    [switch]$Si,
    [switch]$SoloControlli,
    [switch]$NoWipe,
    [string]$Account = "",
    [string]$Radice = ""
)

$ErrorActionPreference = "Continue"

function Titolo([string]$t) { Write-Host ""; Write-Host "== $t" -ForegroundColor Cyan }
function Ok([string]$t) { Write-Host "   ok  $t" -ForegroundColor Green }
$script:avvisi = 0
function Ko([string]$t) { $script:avvisi++; Write-Host "   KO  $t" -ForegroundColor Red }
function Nota([string]$t) { Write-Host "   $t" -ForegroundColor DarkGray }

# Radice del repository: quella indicata, altrimenti quella che contiene lo script, cosi' il
# comando funziona da qualunque cartella sia aperto il terminale.
if (-not $Radice) { $Radice = (& git -C $PSScriptRoot rev-parse --show-toplevel 2>$null) }
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
              ".claude\templates\readme-sync\tools", ".claude\templates\fix-typography\tools") } else { @("tools") }
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

$resume = "_notes\RESUME-PROMPT.md"
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
    @{ n = "md-unwrap.py";            a = @("--check") + $o + @(".") },
    @{ n = "sync-readme.py";          a = @("--check") + $b; serve = "README.md" },
    @{ n = "lint-md-commands.py";     a = @(".") },
    @{ n = "lint-doc-references.py";  a = @("--solo-vivi") + $b },
    @{ n = "check-eol.py";            a = @(".") },
    @{ n = "misura-istruzioni.py";    a = @() },
    @{ n = "fix-accents.py";          a = @("--check") + $m + @(".") },
    @{ n = "fix-dashes.py";           a = @("--check") + $m + @(".") },
    @{ n = "fix-missing-accents.py";  a = @("--check") + $m + @(".") },
    @{ n = "sync-codex-skills.py";    a = @("--project-root", ".", "--check"); serve = ".claude\skills" },
    @{ n = "check-copie-modelli.py";  a = @(); solobundle = $true },
    @{ n = "check-catalogo.py";       a = @(); solobundle = $true },
    @{ n = "check-raggiungibilita.py"; a = @(); solobundle = $true },
    @{ n = "test-tipografia.py";      a = @(); solobundle = $true }
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
        Write-Host "Identita' git locale non impostata (git-identity-and-repo.md): impostare user.name e user.email del repository e rilanciare." -ForegroundColor Red
        exit 1
    }
    Write-Host "   $($cambi.Count) file  ->  `"$Messaggio`""
    Write-Host "   autore: $nome <$email>"

    if (-not $Si) {
        $r = Read-Host "   Committo tutto e pusho su '$ramo'? [s/N]"
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
if (-not $haOrigin) {
    Nota "nessun remoto 'origin': push saltato, il commit resta locale"
} elseif (-not (& git rev-parse -q --verify HEAD)) {
    Nota "nessun commit sul ramo: niente da pushare"
} else {
    # Destinazione esplicita: un upstream diverso da origin non deve deviare la chiusura.
    & git push -u origin "HEAD:refs/heads/$ramo"
    if ($LASTEXITCODE -ne 0) { Write-Host "Push fallito: l'impronta non si registra finche' il remoto non e' allineato." -ForegroundColor Red; exit 1 }
    $locale = (& git rev-parse HEAD)
    $refRemota = (& git ls-remote --exit-code origin "refs/heads/$ramo")
    if ($LASTEXITCODE -ne 0 -or -not $refRemota) { Ko "verifica del ramo remoto fallita"; exit 1 }
    $suRemoto = ($refRemota -split '\s+')[0]
    if ($locale -ne $suRemoto) { Ko "HEAD $locale diverso dal remoto $suRemoto"; exit 1 }
    Ok "HEAD e remoto coincidono su '$ramo' ($($locale.Substring(0,7)))"
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
} elseif ($aperte.Count -gt 0) {
    Write-Host "   $($aperte.Count) processi Claude Code ancora aperti (CLI o editor): wipe rimandato. Chiuderli e lanciare:" -ForegroundColor Yellow
    $script | ForEach-Object { Write-Host "   powershell -NoProfile -ExecutionPolicy Bypass -File `"$_`"" }
} else {
    foreach ($s in $script) {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $s
        if ($LASTEXITCODE -eq 0) { Ok $s } else { Ko "$s (uscita $LASTEXITCODE)" }
    }
}

Fine ""
