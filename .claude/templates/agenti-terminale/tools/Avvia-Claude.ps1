# Launcher Claude con la stessa cassetta e stato progetto usati da Codex.
[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][ValidateRange(1,99)][int]$Account,
  [string]$Progetto=(Get-Location).Path,
  [string]$Posta,
  [switch]$NoPosta,
  [Parameter(ValueFromRemainingArguments=$true)][string[]]$Resto
)
$ErrorActionPreference='Stop'
$radice=Join-Path $env:USERPROFILE ".claude-account$Account"
if (-not (Test-Path -LiteralPath $radice)) { throw "Radice Claude assente: $radice" }
if (-not (Get-Command claude -ErrorAction SilentlyContinue)) { throw 'claude assente dal PATH' }
$Progetto=(Resolve-Path -LiteralPath $Progetto).Path
$env:CLAUDE_CONFIG_DIR=$radice
$precedente=Get-Location
try {
  Set-Location -LiteralPath $Progetto
  $extra=@()
  if (-not $NoPosta) {
    . (Join-Path $PSScriptRoot 'Posta-Sessioni.ps1')
    $cassetta=Prepara-PostaSessioni 'claude' $Account $Progetto $Posta
    $extra+=@('--add-dir',$cassetta)
  }
  & claude @extra @Resto
}
finally {
  Set-Location -LiteralPath $precedente.Path
  # La pulizia Claude rimane nell'hook SessionEnd installato sulle sue radici.
  Remove-Item Env:PROJECT_AGENT_MAILBOX_ROOT,Env:PROJECT_AGENT_MAILBOX_ID,Env:PROJECT_AGENT_MAILBOX_TOOL,Env:PROJECT_TEMPLATE_ROOT -ErrorAction SilentlyContinue
}
