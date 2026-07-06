# list-community-agents.ps1 - Elenca i subagent disponibili nelle fonti flat del catalogo.
#
# Legge .claude/agent-catalog/sources.json, interroga l'API GitHub (contenuti della cartella
# indicata da ciascuna fonte "flat") e stampa i nomi dei file .md disponibili, pronti da passare
# a fetch-community-agent.ps1. Le fonti "meta" non vengono elencate: si stampa solo un rimando
# a consultarle a mano.
#
# Uso:
#   .\tools\list-community-agents.ps1              # elenca tutte le fonti flat
#   .\tools\list-community-agents.ps1 -Source 0xfurai   # solo una fonte, per chiave
#
# L'API GitHub non autenticata ha un limite di 60 richieste/ora per IP: sufficiente per un uso
# occasionale, non per una corsa automatica frequente.

param(
    [string]$Source = "",
    [string]$ProjectRoot = ""
)

$ErrorActionPreference = "Stop"

if (-not $ProjectRoot) { $ProjectRoot = Split-Path -Parent $PSScriptRoot }
$SourcesPath = Join-Path $ProjectRoot ".claude\agent-catalog\sources.json"
if (-not (Test-Path $SourcesPath)) {
    Write-Host "ERRORE: non trovo $SourcesPath. Il pacchetto agent-catalog e' instanziato correttamente?"
    exit 1
}

$catalog = Get-Content $SourcesPath -Raw | ConvertFrom-Json
$sources = $catalog.sources
if ($Source) { $sources = $sources | Where-Object { $_.key -eq $Source } }
if (-not $sources -or $sources.Count -eq 0) {
    Write-Host "Nessuna fonte trovata per chiave '$Source'."
    exit 1
}

foreach ($src in $sources) {
    Write-Host ""
    Write-Host "=== $($src.key) ($($src.name), licenza $($src.license)) ===" -ForegroundColor Cyan
    if ($src.type -eq "meta") {
        Write-Host "Indice curato, non elencabile: consultare a mano https://github.com/$($src.repo)"
        continue
    }
    $url = "https://api.github.com/repos/$($src.repo)/contents/$($src.path)?ref=$($src.branch)"
    try {
        $items = Invoke-RestMethod -Uri $url -TimeoutSec 30 -Headers @{ "User-Agent" = "agent-catalog-script" }
    } catch {
        if ($_.Exception.Response -and $_.Exception.Response.StatusCode.value__ -eq 403) {
            Write-Host "ERRORE: limite di richieste GitHub non autenticate superato (60/ora per IP). Riprovare piu' tardi."
        } else {
            Write-Host "ERRORE: impossibile leggere $url ($($_.Exception.Message))."
        }
        continue
    }
    $files = $items | Where-Object { $_.type -eq "file" -and $_.name -like "*.md" } | Sort-Object name
    foreach ($f in $files) {
        Write-Host ("  {0}" -f ($f.name -replace '\.md$', ''))
    }
    Write-Host ("{0} agent disponibili." -f $files.Count)
}
