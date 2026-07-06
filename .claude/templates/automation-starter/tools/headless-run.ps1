<#
.SYNOPSIS
  Invocazione headless generica di Claude Code, vincolata alla quota di abbonamento Team/Max.
.DESCRIPTION
  Esegue "claude -p" in modalita non interattiva per un task ricorrente del progetto (report di
  drift, controllo periodico, sintesi), scrivendo l'output in _notes/automation/, ignorato da
  git. Il pacchetto automation-starter resta vincolato all'uso incluso nei piani Team o Max: lo
  script si rifiuta di girare se ANTHROPIC_API_KEY e' impostata nell'ambiente, perche' quella
  variabile fa passare l'autenticazione della CLI dall'abbonamento alla fatturazione a consumo
  dell'API, anche se la sessione risulta gia' loggata via "claude login" con un account Team o
  Max. Commit e push restano sempre manuali: lo script non tocca mai git.
.PARAMETER Prompt
  Il prompt o l'istruzione da eseguire in modalita headless.
.PARAMETER PermissionMode
  plan (default, sola lettura), acceptEdits, o dontAsk. bypassPermissions non e' un valore
  ammesso da questo script: vietato su una macchina reale non containerizzata, vedi
  .claude/rules/security-permissions.md.
.PARAMETER MaxTurns
  Numero massimo di turni dell'agente. Default 8.
.EXAMPLE
  ./tools/headless-run.ps1 -Prompt "Esegui la skill sync-context e riassumi il drift" -PermissionMode plan
#>
param(
  [Parameter(Mandatory=$true)] [string]$Prompt,
  [ValidateSet("plan","acceptEdits","dontAsk")] [string]$PermissionMode = "plan",
  [int]$MaxTurns = 8
)

if ($env:ANTHROPIC_API_KEY) {
  Write-Error "ANTHROPIC_API_KEY e' impostata nell'ambiente. Il pacchetto automation-starter resta sull'uso incluso nell'abbonamento Team o Max: con quella variabile presente Claude Code fattura a consumo invece di usare la quota dell'abbonamento. Rimuovila (Remove-Item Env:\ANTHROPIC_API_KEY) e verifica il login con 'claude login'."
  exit 1
}

if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
  Write-Error "CLI 'claude' non trovata nel PATH."
  exit 1
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$outDir = Join-Path $projectRoot "_notes\automation"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$outFile = Join-Path $outDir "$stamp.json"

Write-Host "[$stamp] Esecuzione headless (permission-mode=$PermissionMode, max-turns=$MaxTurns)..."
& claude -p $Prompt --output-format json --permission-mode $PermissionMode --max-turns $MaxTurns | Out-File -FilePath $outFile -Encoding utf8

if ($LASTEXITCODE -eq 0) {
  Write-Host "Output salvato in _notes/automation/$stamp.json"
} else {
  Write-Error "La corsa headless e' terminata con codice $LASTEXITCODE. Vedi $outFile."
  exit $LASTEXITCODE
}
