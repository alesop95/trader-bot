# check-agent-sources.ps1 - Controlla se le fonti del catalogo hanno nuovi commit upstream.
#
# Stessa strategia a costo zero di tools/update-handoff.ps1: confronta l'ultimo commit del branch
# di ciascuna fonte (una richiesta HTTP) con lo sha registrato in .claude/agent-catalog/state.json
# l'ultima volta che si e' controllato. A differenza dell'handoff, qui non c'e' una fonte che si
# auto-aggiorna a cadenza nota: "controllato di recente" non implica "nessuna novita'", significa
# solo che non si e' ancora guardato. Per questo lo stallo qui e' della verifica locale, non della
# fonte: se non si controlla da piu' di 30 giorni lo script lo segnala, cosa diversa dal caso
# dell'handoff dove e' l'updater upstream stesso a poter fermarsi.
#
# Uso:
#   .\tools\check-agent-sources.ps1            # controlla tutte le fonti e aggiorna lo stato
#   .\tools\check-agent-sources.ps1 -Check     # solo verifica, non scrive stato; exit 10 se c'e' novita'
#
# Exit code: 0 = nessuna fonte con novita' (o stato aggiornato); 10 = novita' disponibili (-Check); 1 = errore.

param(
    [switch]$Check,
    [string]$ProjectRoot = ""
)

$ErrorActionPreference = "Stop"
function Write-Log([string]$Message) { Write-Host ("[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message) }

if (-not $ProjectRoot) { $ProjectRoot = Split-Path -Parent $PSScriptRoot }
$SourcesPath = Join-Path $ProjectRoot ".claude\agent-catalog\sources.json"
$StatePath   = Join-Path $ProjectRoot ".claude\agent-catalog\state.json"
$StaleDays   = 30

if (-not (Test-Path $SourcesPath)) {
    Write-Log "ERRORE: non trovo $SourcesPath. Il pacchetto agent-catalog e' instanziato correttamente?"
    exit 1
}
$catalog = Get-Content $SourcesPath -Raw | ConvertFrom-Json

$state = [ordered]@{ sources = @{}; fetch_log = @() }
if (Test-Path $StatePath) {
    try {
        $existing = Get-Content $StatePath -Raw | ConvertFrom-Json
        if ($existing.sources) { $existing.sources.PSObject.Properties | ForEach-Object { $state.sources[$_.Name] = $_.Value } }
        if ($existing.fetch_log) { $state.fetch_log = @($existing.fetch_log) }
    } catch {}
}

$anyUpdate = $false
foreach ($src in $catalog.sources) {
    $known = $state.sources[$src.key]
    $lastSha = $null; $lastChecked = $null
    if ($known) { $lastSha = $known.last_known_sha; $lastChecked = $known.last_checked_at }

    try {
        $commitInfo = Invoke-RestMethod -Uri "https://api.github.com/repos/$($src.repo)/commits/$($src.branch)" -TimeoutSec 20 -Headers @{ "User-Agent" = "agent-catalog-script" }
        $currentSha = $commitInfo.sha
    } catch {
        Write-Log ("[{0}] ERRORE: impossibile leggere l'ultimo commit ({1})." -f $src.key, $_.Exception.Message)
        continue
    }

    if ($lastChecked) {
        try {
            $ageDays = [int]((Get-Date).ToUniversalTime() - [datetime]::Parse($lastChecked, [System.Globalization.CultureInfo]::InvariantCulture, [System.Globalization.DateTimeStyles]::AdjustToUniversal)).TotalDays
            if ($ageDays -gt $StaleDays) {
                Write-Log ("[{0}] ATTENZIONE: non controllato da {1} giorni (ultimo controllo: {2})." -f $src.key, $ageDays, $lastChecked)
            }
        } catch {}
    }

    if (-not $lastSha) {
        Write-Log ("[{0}] Nessuno stato precedente: prima registrazione, sha {1}." -f $src.key, $currentSha.Substring(0,7))
    } elseif ($lastSha -ne $currentSha) {
        Write-Log ("[{0}] AGGIORNAMENTO DISPONIBILE: {1} -> {2}. Rivedere con list-community-agents.ps1 -Source {0}." -f $src.key, $lastSha.Substring(0,7), $currentSha.Substring(0,7))
        $anyUpdate = $true
    } else {
        Write-Log ("[{0}] Nessuna novita' (sha {1})." -f $src.key, $currentSha.Substring(0,7))
    }

    if (-not $Check) {
        $state.sources[$src.key] = [ordered]@{
            last_known_sha  = $currentSha
            last_checked_at = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssK")
        }
    }
}

if (-not $Check) {
    $stateDir = Split-Path -Parent $StatePath
    New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
    Set-Content -Path $StatePath -Value ($state | ConvertTo-Json -Depth 6) -Encoding utf8
    Write-Log "Stato aggiornato in .claude/agent-catalog/state.json"
}

if ($Check -and $anyUpdate) { exit 10 }
exit 0
