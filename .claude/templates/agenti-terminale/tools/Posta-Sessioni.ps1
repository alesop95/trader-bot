# Punto comune ai launcher: nessun protocollo privato dei due agenti.
function Prepara-PostaSessioni([string]$Agente, [int]$Account, [string]$Progetto, [string]$Posta) {
  $tool = Join-Path $PSScriptRoot 'posta-sessioni.py'
  if (-not (Test-Path -LiteralPath $tool)) { throw "Manca la cassetta comune: $tool" }
  if (-not $Posta) { $Posta = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..\_notes\posta-sessioni')) }
  $Posta = [IO.Path]::GetFullPath($Posta)
  $nome = '{0}-account{1}-{2}' -f $Agente, $Account, ([guid]::NewGuid().ToString('N'))
  $registrazione = & python $tool --root $Posta registra --nome $nome --agente $Agente --progetto $Progetto
  if ($LASTEXITCODE -ne 0) { throw "Registrazione nella cassetta fallita: $registrazione" }
  $env:PROJECT_AGENT_MAILBOX_ROOT = $Posta
  $env:PROJECT_AGENT_MAILBOX_ID = $nome
  $env:PROJECT_AGENT_MAILBOX_TOOL = $tool
  $env:PROJECT_TEMPLATE_ROOT = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..'))
  # Stato in ingresso e lezioni in uscita, visibili a ogni avvio dei due agenti.
  $statoTemplate = Join-Path $env:PROJECT_TEMPLATE_ROOT '.claude/templates/tools/stato-template.py'
  if (Test-Path -LiteralPath $statoTemplate) {
    & python $statoTemplate --progetto $Progetto --template $env:PROJECT_TEMPLATE_ROOT | ForEach-Object { Write-Host $_ }
  }
  $lezioniTemplate = Join-Path $env:PROJECT_TEMPLATE_ROOT '.claude/templates/tools/lezioni-template.py'
  if (Test-Path -LiteralPath $lezioniTemplate) {
    & python $lezioniTemplate --radice $Progetto controlla | ForEach-Object { Write-Host $_ }
  }
  Write-Host "Posta comune = $Posta; partecipante $nome" -ForegroundColor Cyan
  Write-Host 'Gli agenti leggono la cassetta a inizio sessione e a ogni giro; nessuna notifica push.' -ForegroundColor DarkGray
  return $Posta
}
