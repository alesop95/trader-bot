<# Riapplica le connessioni di progetto autorizzate su questa macchina. #>
[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][ValidateSet('claude', 'codex')][string]$Agente,
  [Parameter(Mandatory = $true)][int[]]$Account,
  [switch]$Verifica
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$registro = Join-Path $env:LOCALAPPDATA 'agenti-terminale\progetti.json'
if (-not (Test-Path -LiteralPath $registro)) { return }
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  throw 'Il registro progetti MCP richiede Python 3.11 o successivo.'
}
$argomenti = @('-B', (Join-Path $PSScriptRoot 'configura-progetti.py'), '--registry', $registro,
  '--agent', $Agente, '--account') + @($Account | ForEach-Object { [string]$_ })
if ($Verifica) { $argomenti += '--verify' }
& python @argomenti
if ($LASTEXITCODE -ne 0) { throw 'Riconciliazione dei progetti MCP non riuscita: controllare il registro privato.' }
