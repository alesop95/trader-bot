# update-handoff.ps1 - Auto-aggiornamento dell'handoff Claude Code (variante Windows).
#
# Confronta la versione della guida upstream (Cranot/claude-code-guide, auto-aggiornata
# ~ogni 2 giorni) con quella tracciata in .claude/handoff-state.json. Se e' cambiata:
#   1. scarica la guida grezza in _notes/upstream/claude-code-guide.md (ignorato da git);
#   2. aggiorna il file di stato (tracciato);
#   3. se la CLI `claude` e' installata, ri-distilla .claude/context/claude-code-handoff.md;
#      altrimenti segnala di eseguire /refresh-handoff dentro la sessione.
#
# Uso:
#   .\tools\update-handoff.ps1            # check + aggiorna se serve
#   .\tools\update-handoff.ps1 -Check     # solo verifica: exit 10 se c'e' un aggiornamento
#   .\tools\update-handoff.ps1 -Force     # riscarica e rigenera comunque
#   .\tools\update-handoff.ps1 -NoDistill # scarica e aggiorna lo stato, senza corsa LLM
#
# Exit code: 0 = allineato o aggiornato; 10 = aggiornamento disponibile (-Check); 1 = errore.
# Il commit dei file rigenerati resta manuale dell'utente.

param(
    [switch]$Check,
    [switch]$Force,
    [switch]$NoDistill,
    [string]$ProjectRoot = ""
)

$ErrorActionPreference = "Stop"

function Write-Log([string]$Message) {
    Write-Host ("[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message)
}

if (-not $ProjectRoot) { $ProjectRoot = Split-Path -Parent $PSScriptRoot }
$StatePath   = Join-Path $ProjectRoot ".claude\handoff-state.json"
$HandoffPath = Join-Path $ProjectRoot ".claude\context\claude-code-handoff.md"
$RawDir      = Join-Path $ProjectRoot "_notes\upstream"
$RawPath     = Join-Path $RawDir "claude-code-guide.md"

$Repo        = "Cranot/claude-code-guide"
$RawBase     = "https://raw.githubusercontent.com/$Repo/main"

# --- Versione locale tracciata ---
$localVersion = ""
if (Test-Path $StatePath) {
    try { $localVersion = (Get-Content $StatePath -Raw | ConvertFrom-Json).upstream_release } catch {}
}

# --- Versione upstream ---
$upstreamVersion = ""
$upstreamLastCheck = ""
try {
    $upstreamState = Invoke-RestMethod -Uri "$RawBase/.update-state.json" -TimeoutSec 30
    if ($upstreamState.last_release) { $upstreamVersion = [string]$upstreamState.last_release }
    if ($upstreamState.last_check) { $upstreamLastCheck = [string]$upstreamState.last_check }
} catch {
    Write-Log "Avviso: stato upstream non leggibile ($($_.Exception.Message)). Procedo solo con -Force."
}

# --- Rilevamento stallo della fonte: se l'updater upstream non gira da >14 giorni, la guida
# --- stessa e' vecchia e "versione allineata" NON significa "informazione aggiornata".
$StaleDays = 14
if ($upstreamLastCheck) {
    try {
        $checkDate = [datetime]::Parse($upstreamLastCheck, [System.Globalization.CultureInfo]::InvariantCulture, [System.Globalization.DateTimeStyles]::AdjustToUniversal)
        $ageDays = [int]((Get-Date).ToUniversalTime() - $checkDate).TotalDays
        if ($ageDays -gt $StaleDays) {
            Write-Log "ATTENZIONE: la fonte upstream risulta ferma da $ageDays giorni (ultimo check upstream: $upstreamLastCheck)."
            Write-Log "La guida potrebbe non riflettere le release recenti di Claude Code: integrare con 'claude --help' e le docs ufficiali."
        }
    } catch {}
}

Write-Log ("Versione locale: '{0}' | upstream: '{1}'" -f $localVersion, $upstreamVersion)

# --- Decisione ---
if (-not $Force -and $upstreamVersion -and ($upstreamVersion -eq $localVersion)) {
    Write-Log "Nessun aggiornamento: versione $upstreamVersion gia' distillata."
    exit 0
}
if ($Check) {
    if (-not $upstreamVersion -and -not $Force) {
        Write-Log "Stato upstream non disponibile: impossibile verificare."
        exit 1
    }
    Write-Log ("Aggiornamento disponibile: {0} (locale: '{1}')." -f $upstreamVersion, $localVersion)
    exit 10
}

# --- Scarica la guida grezza ---
Write-Log "Scarico la guida upstream..."
$tmpFile = Join-Path ([System.IO.Path]::GetTempPath()) ("claude-code-guide-{0}.md" -f [guid]::NewGuid())
try {
    Invoke-WebRequest -Uri "$RawBase/README.md" -OutFile $tmpFile -TimeoutSec 60 -UseBasicParsing
} catch {
    Write-Log "ERRORE: download della guida fallito ($($_.Exception.Message)). Riprovare piu' tardi."
    exit 1
}
if (-not (Test-Path $tmpFile) -or (Get-Item $tmpFile).Length -lt 1024) {
    Write-Log "ERRORE: la guida scaricata e' vuota o troppo piccola."
    exit 1
}

New-Item -ItemType Directory -Force -Path $RawDir | Out-Null
$header = @(
    "<!-- Fonte grezza scaricata automaticamente da github.com/$Repo -->",
    ("<!-- Versione upstream: {0} - {1} -->" -f $upstreamVersion, (Get-Date -Format "yyyy-MM-dd HH:mm:ss")),
    "<!-- NON modificare a mano: rigenerato da tools/update-handoff.ps1. Ignorato da git (_notes/). -->",
    ""
) -join "`n"
$body = Get-Content $tmpFile -Raw
Set-Content -Path $RawPath -Value ($header + $body) -Encoding utf8
Remove-Item $tmpFile -Force
Write-Log "Guida grezza salvata in _notes/upstream/claude-code-guide.md"

# --- Aggiorna lo stato tracciato ---
$state = [ordered]@{
    upstream_release = $upstreamVersion
    last_update      = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssK")
    source           = "github.com/$Repo"
}
$stateDir = Split-Path -Parent $StatePath
New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
Set-Content -Path $StatePath -Value ($state | ConvertTo-Json) -Encoding utf8
Write-Log "Stato aggiornato in .claude/handoff-state.json"

# --- Ri-distillazione (corsa LLM, consuma token) ---
if ($NoDistill) {
    Write-Log "Ri-distillazione saltata (-NoDistill): eseguire /refresh-handoff dentro Claude Code."
    exit 0
}
$claudeCmd = Get-Command claude -ErrorAction SilentlyContinue
if ($null -eq $claudeCmd) {
    Write-Log "CLI claude non trovata: aprire il progetto con 'claude' ed eseguire /refresh-handoff."
    exit 0
}

Write-Log "CLI claude trovata: ri-distillo l'handoff (consuma token)..."
$prompt = "Leggi _notes/upstream/claude-code-guide.md (guida Claude Code upstream, versione $upstreamVersion) e rigenera .claude/context/claude-code-handoff.md seguendo la procedura del comando .claude/commands/refresh-handoff.md: stessa struttura in sezioni 0-13, sezioni 0 e 13 invariate, marcatori OFFICIAL/COMMUNITY/NEW, frontmatter aggiornato (upstream-release: $upstreamVersion, distilled-date: oggi). Aggiorna solo i contenuti cambiati upstream. Scrivi il file, poi elenca in 3-5 punti cosa e' cambiato."
& $claudeCmd.Source -p $prompt --max-turns 12 --permission-mode acceptEdits
if ($LASTEXITCODE -eq 0) {
    Write-Log "Handoff ri-distillato. Rivedere il diff prima del commit (manuale)."
} else {
    Write-Log "Ri-distillazione fallita (exit $LASTEXITCODE): usare /refresh-handoff dentro Claude Code."
}

Write-Log ("Fatto. Versione upstream tracciata: {0}" -f $upstreamVersion)
exit 0
