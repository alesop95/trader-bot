# fetch-community-agent.ps1 - Scarica un singolo subagent da una fonte flat del catalogo.
#
# Scarica <fonte>/<file>.md via raw.githubusercontent.com dentro .claude/agents/ del progetto e
# registra la provenienza (fonte, commit sha al momento del fetch, data) in
# .claude/agent-catalog/state.json, cosi' resta tracciabile da dove viene ogni agente pescato.
# Non modifica il contenuto del file: il frontmatter YAML (incluso il campo "model", spesso
# fissato dalla fonte a uno snapshot specifico) va rivisto a mano dopo il fetch.
#
# Uso:
#   .\tools\fetch-community-agent.ps1 -Source 0xfurai -Agent react-expert
#   .\tools\fetch-community-agent.ps1 -Source 0xfurai -Agent react-expert -Force   # sovrascrive se gia' presente
#   .\tools\fetch-community-agent.ps1 -Source 0xfurai -Agent react-expert -Out .claude\agents\react-expert.md
#
# Exit code: 0 = scaricato; 1 = errore (fonte/file non trovato, download fallito, gia' presente senza -Force).

param(
    [Parameter(Mandatory = $true)][string]$Source,
    [Parameter(Mandatory = $true)][string]$Agent,
    [switch]$Force,
    [string]$Out = "",
    [string]$ProjectRoot = ""
)

$ErrorActionPreference = "Stop"
function Write-Log([string]$Message) { Write-Host ("[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message) }

if (-not $ProjectRoot) { $ProjectRoot = Split-Path -Parent $PSScriptRoot }
$SourcesPath = Join-Path $ProjectRoot ".claude\agent-catalog\sources.json"
$StatePath   = Join-Path $ProjectRoot ".claude\agent-catalog\state.json"
if (-not (Test-Path $SourcesPath)) {
    Write-Log "ERRORE: non trovo $SourcesPath. Il pacchetto agent-catalog e' instanziato correttamente?"
    exit 1
}

$catalog = Get-Content $SourcesPath -Raw | ConvertFrom-Json
$src = $catalog.sources | Where-Object { $_.key -eq $Source } | Select-Object -First 1
if (-not $src) {
    Write-Log "ERRORE: fonte '$Source' non trovata in sources.json."
    exit 1
}
if ($src.type -eq "meta") {
    Write-Log "ERRORE: '$Source' e' un indice curato (meta), non ha file da scaricare. Consultare https://github.com/$($src.repo)."
    exit 1
}

$agentFile = $Agent -replace '\.md$', ''
$agentFile = "$agentFile.md"

if (-not $Out) { $Out = Join-Path $ProjectRoot ".claude\agents\$agentFile" }
if ((Test-Path $Out) -and -not $Force) {
    Write-Log "ERRORE: $Out esiste gia'. Usare -Force per sovrascrivere."
    exit 1
}

$rawUrl = "https://raw.githubusercontent.com/$($src.repo)/$($src.branch)/$($src.path)/$agentFile"
Write-Log "Scarico $rawUrl ..."
try {
    $content = Invoke-RestMethod -Uri $rawUrl -TimeoutSec 30 -Headers @{ "User-Agent" = "agent-catalog-script" }
} catch {
    Write-Log "ERRORE: download fallito ($($_.Exception.Message)). Verificare il nome esatto con list-community-agents.ps1."
    exit 1
}

$outDir = Split-Path -Parent $Out
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
Set-Content -Path $Out -Value $content -Encoding utf8 -NoNewline
Write-Log "Salvato in $Out"

# --- Sha del commit corrente sulla fonte, per tracciabilita' del fetch ---
$commitSha = ""
try {
    $commitInfo = Invoke-RestMethod -Uri "https://api.github.com/repos/$($src.repo)/commits/$($src.branch)" -TimeoutSec 20 -Headers @{ "User-Agent" = "agent-catalog-script" }
    $commitSha = $commitInfo.sha
} catch {}

# --- Registra la provenienza nello stato tracciato ---
$state = [ordered]@{ sources = @{}; fetch_log = @() }
if (Test-Path $StatePath) {
    try {
        $existing = Get-Content $StatePath -Raw | ConvertFrom-Json
        if ($existing.sources) { $existing.sources.PSObject.Properties | ForEach-Object { $state.sources[$_.Name] = $_.Value } }
        if ($existing.fetch_log) { $state.fetch_log = @($existing.fetch_log) }
    } catch {}
}
$state.fetch_log += [ordered]@{
    file        = $agentFile
    source      = $Source
    commit_sha  = $commitSha
    fetched_at  = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssK")
}
$stateDir = Split-Path -Parent $StatePath
New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
Set-Content -Path $StatePath -Value ($state | ConvertTo-Json -Depth 6) -Encoding utf8
Write-Log "Provenienza registrata in .claude/agent-catalog/state.json"
Write-Log "Rivedere il campo 'model' nel frontmatter prima dell'uso: la fonte puo' fissare uno snapshot di modello non piu' corrente."
exit 0
