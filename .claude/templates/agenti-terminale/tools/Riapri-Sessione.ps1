<#
.SYNOPSIS
  Rimette UNA trascrizione recuperata nel suo account e riapre subito la sessione.

.DESCRIPTION
  L'origine e' una cartella prodotta da Recupera-DaShadow.ps1 oppure una cartella della
  quarantena scritta dal wipe, %USERPROFILE%\quarantena-sessioni\<data>\<ora>-<account>.
  In entrambe una trascrizione sta al percorso relativo che aveva nell'account, sotto una
  cartella che porta il nome dell'account: claude-account2\projects\<slug>\<id>.jsonl per
  Claude Code, codex-account1\sessions\aaaa\mm\gg\rollout-...-<id>.jsonl per Codex.

  Una sessione alla volta, e la si rimette e la si riapre nello stesso gesto: il wipe
  conserva soltanto le sessioni aperte, quindi una trascrizione rimessa e lasciata li'
  sparisce alla prima chiusura di un'altra sessione dello stesso account (L-018,
  2026-11-24). Non sovrascrive mai un file gia' presente nell'account.

  La cartella del progetto si legge dalla trascrizione (campo cwd), l'account dal nome
  della cartella. La sessione si riapre con Avvia-Claude.ps1 o Avvia-Codex.ps1 accanto a
  questo script, cosi' che giri con la stessa radice di account, la cassetta e le pulizie.

.PARAMETER Origine
  Cartella da cui leggere. Senza -Id elenca le sessioni che contiene.

.PARAMETER Id
  Identificativo della sessione, intero o un suo prefisso di almeno otto caratteri.

.PARAMETER SoloRimetti
  Rimette la trascrizione e stampa il comando di riapertura, senza lanciarlo.

.EXAMPLE
  .\Riapri-Sessione.ps1 -Origine "$env:USERPROFILE\quarantena-sessioni\2026-11-24"
.EXAMPLE
  .\Riapri-Sessione.ps1 -Origine 'D:\recupero-sessioni-2026-11-24' -Id 0bb14c67
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$Origine,
  [string]$Id,
  [switch]$SoloRimetti
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $Origine)) { throw "Origine inesistente: $Origine" }
$Origine = (Resolve-Path -LiteralPath $Origine).Path.TrimEnd('\')

# L'account dalla cartella che contiene projects\ o sessions\: 'claude-account2',
# '153012-claude-account2' della quarantena, 'codex-account1', oppure 'claude' e 'codex'
# per le home di default.
function Get-Account($cartella) {
  if ($cartella -match '(?:^|-)(claude|codex)(?:-account(\d+))?$') {
    return [pscustomobject]@{ Agente = $Matches[1]; Numero = $(if ($Matches[2]) { [int]$Matches[2] } else { 0 }); Home = $(if ($Matches[2]) { ".$($Matches[1])-account$($Matches[2])" } else { ".$($Matches[1])" }) }
  }
  return $null
}
function Get-Cwd($file) {
  foreach ($r in @(Get-Content -LiteralPath $file -TotalCount 60 -Encoding UTF8 -ErrorAction SilentlyContinue)) {
    if ($r -match '"cwd"\s*:\s*"((?:[^"\\]|\\.)*)"') { return ($Matches[1] -replace '\\\\', '\') }
  }
  return $null
}

$sessioni = @()
foreach ($f in @(Get-ChildItem -LiteralPath $Origine -Recurse -File -Filter '*.jsonl')) {
  $rel = $f.FullName.Substring($Origine.Length).TrimStart('\')
  $parti = $rel.Split('\')
  $i = [Array]::IndexOf($parti, 'projects'); $tipo = 'claude'
  if ($i -lt 0) { $i = [Array]::IndexOf($parti, 'sessions'); $tipo = 'codex' }
  if ($i -lt 1) { continue }
  # Claude: projects\<slug>\<id>.jsonl, non i sottoagenti; Codex: sessions\...\rollout-*.jsonl.
  if ($tipo -eq 'claude' -and ($parti.Count - $i) -ne 3) { continue }
  if ($tipo -eq 'codex' -and $f.Name -notlike 'rollout-*') { continue }
  $acc = Get-Account $parti[$i - 1]
  if (-not $acc -or $acc.Agente -ne $tipo) { continue }
  $sid = if ($f.BaseName -match '([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})$') { $Matches[1] } else { $f.BaseName }
  $sessioni += [pscustomobject]@{
    Id = $sid; Account = $acc; File = $f.FullName
    Rel = ($parti[$i..($parti.Count - 1)] -join '\'); Cwd = (Get-Cwd $f.FullName); Data = $f.LastWriteTime; KB = [int]($f.Length / 1KB)
  }
}

if (-not $Id) {
  Write-Host ("Sessioni in {0}:" -f $Origine)
  foreach ($s in ($sessioni | Sort-Object Data)) { Write-Host ("  {0}  {1,-16}  {2:yyyy-MM-dd HH:mm}  {3,7} KB  {4}" -f $s.Id, $s.Account.Home.TrimStart('.'), $s.Data, $s.KB, $s.Cwd) }
  Write-Host 'Si riapre una sessione con -Id <identificativo>.'
  exit 0
}
if ($Id.Length -lt 8) { throw 'Un prefisso di identificativo deve avere almeno otto caratteri.' }
$trovate = @($sessioni | Where-Object { $_.Id.StartsWith($Id, [StringComparison]::OrdinalIgnoreCase) })
if ($trovate.Count -ne 1) { throw ("{0} sessioni corrispondono a '{1}': serve un identificativo univoco." -f $trovate.Count, $Id) }
$s = $trovate[0]
if (-not $s.Cwd -or -not (Test-Path -LiteralPath $s.Cwd)) { throw ("Cartella del progetto non leggibile dalla trascrizione o inesistente: '{0}'." -f $s.Cwd) }

$homeAcc = Join-Path $env:USERPROFILE $s.Account.Home
if (-not (Test-Path -LiteralPath $homeAcc)) { throw "Home dell'account inesistente: $homeAcc" }
$dest = Join-Path $homeAcc $s.Rel
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dest) | Out-Null
if (Test-Path -LiteralPath $dest) { Write-Host "[gia' presente] $dest, non lo sovrascrivo" }
else { Copy-Item -LiteralPath $s.File -Destination $dest; Write-Host "[ok] rimesso $dest" }
if ($s.Account.Agente -eq 'claude') {
  # La cartella <id>\ accanto alla trascrizione: sottoagenti e risultati degli strumenti.
  $dirSrc = Join-Path (Split-Path -Parent $s.File) $s.Id
  $dirDst = Join-Path (Split-Path -Parent $dest) $s.Id
  if ((Test-Path -LiteralPath $dirSrc) -and -not (Test-Path -LiteralPath $dirDst)) { Copy-Item -LiteralPath $dirSrc -Destination $dirDst -Recurse; Write-Host '[ok] rimessi sottoagenti e risultati della sessione' }
}

$lanciatore = Join-Path $PSScriptRoot $(if ($s.Account.Agente -eq 'claude') { 'Avvia-Claude.ps1' } else { 'Avvia-Codex.ps1' })
$numero = $s.Account.Numero
$ripresa = if ($s.Account.Agente -eq 'claude') { @('--resume', $s.Id) } else { @('resume', $s.Id) }
$mostra = if ($numero) { 'powershell -NoProfile -ExecutionPolicy Bypass -File "{0}" -Account {1} -Progetto "{2}" {3}' -f ($lanciatore -replace '\\', '/'), $numero, ($s.Cwd -replace '\\', '/'), ($ripresa -join ' ') }
         else { 'cd "{0}"; {1} {2}' -f ($s.Cwd -replace '\\', '/'), $s.Account.Agente, ($ripresa -join ' ') }
if ($SoloRimetti) {
  Write-Host 'Per riaprirla, in una finestra PowerShell normale nuova, subito: il wipe conserva solo le sessioni aperte.'
  Write-Host $mostra
  exit 0
}
Write-Host ("Riapro {0} in {1}" -f $s.Id, $s.Cwd)
# Per nome e non per posizione: nei due lanciatori il primo parametro posizionale libero e'
# -Posta, che altrimenti si prenderebbe 'resume'.
if ($numero) { & $lanciatore -Account $numero -Progetto $s.Cwd -Resto $ripresa }
else {
  Set-Location -LiteralPath $s.Cwd
  if ($s.Account.Agente -eq 'claude') { & claude @ripresa } else { & codex @ripresa }
}
