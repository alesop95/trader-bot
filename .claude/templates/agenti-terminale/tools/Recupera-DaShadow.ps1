<#
.SYNOPSIS
  Copia le trascrizioni di Claude Code e di Codex dalla copia shadow piu' recente
  anteriore a un'ora data, in una cartella fuori dalla portata del wipe.

.DESCRIPTION
  Serve dopo un crash che ha fatto cancellare le trascrizioni prima che la quarantena
  esistesse, o quando la quarantena non le ha prese (L-018, 2026-11-24). Il caso da cui
  nasce: Windows Terminal chiude tutte le schede alle 13:56, ogni sessione scatta il
  proprio SessionEnd, il wipe cancella i verbali; li ha salvati soltanto la copia shadow
  di C: che un backup a livello di volume aveva creato alle 13:45 e teneva ancora montata.

  Legge SOLO dalla copia shadow, attraverso un collegamento simbolico temporaneo alla sua
  periferica, e scrive SOLO nella destinazione. Non tocca le home degli account, non crea
  ne' cancella copie shadow, e alla fine toglie il solo collegamento. Si perdono i minuti
  fra la copia e il crash: li coprono soltanto i file di ripresa dei progetti.

  Va lanciato da un PowerShell amministratore aperto da Start, non da una scorciatoia
  appena modificata: la lettura di \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopyN lo
  richiede.

.PARAMETER Prima
  L'ora del crash: si usa la copia shadow piu' recente creata PRIMA di quest'ora.

.PARAMETER Destinazione
  Cartella in cui copiare. Deve stare fuori dalle home degli account e fuori dalla
  radice degli scratchpad, dove il wipe la cancellerebbe; meglio su un altro disco.

.PARAMETER Elenco
  Sola lettura: elenca le copie shadow presenti e quale verrebbe usata.

.EXAMPLE
  .\Recupera-DaShadow.ps1 -Prima '2026-11-24 13:56' -Elenco
.EXAMPLE
  .\Recupera-DaShadow.ps1 -Prima '2026-11-24 13:56' -Destinazione 'D:\recupero-sessioni-2026-11-24'
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][datetime]$Prima,
  [string]$Destinazione,
  [switch]$Elenco
)
$ErrorActionPreference = 'Stop'

$principale = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principale.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
  throw 'Serve un PowerShell da amministratore, aperto da Start (tasto destro, Esegui come amministratore).'
}

# Il volume e il percorso del profilo dentro il volume: la copia shadow si legge come una
# radice di disco, quindi C:\Users\Nome diventa <copia>\Users\Nome.
$profilo = [IO.Path]::GetFullPath($env:USERPROFILE)
$lettera = $profilo.Substring(0, 2)
$relProfilo = $profilo.Substring(3)
$volume = (Get-CimInstance Win32_Volume -Filter ("DriveLetter='{0}'" -f $lettera)).DeviceID
$copie = @(Get-CimInstance Win32_ShadowCopy | Sort-Object InstallDate)
Write-Host ("Copie shadow presenti ({0}):" -f $copie.Count)
foreach ($c in $copie) {
  $segno = if ($c.VolumeName -eq $volume) { "<- $lettera" } else { '' }
  Write-Host ("  {0:yyyy-MM-dd HH:mm:ss}  {1}  {2}" -f $c.InstallDate, $c.DeviceObject, $segno)
}
$scelta = $copie | Where-Object { $_.VolumeName -eq $volume -and $_.InstallDate -lt $Prima } | Select-Object -Last 1
if (-not $scelta) {
  Write-Host ("Nessuna copia shadow di {0} anteriore a {1:yyyy-MM-dd HH:mm}. Resta il ripristino di file dal backup, al punto piu' recente prima di quell'ora." -f $lettera, $Prima) -ForegroundColor Yellow
  exit 2
}
Write-Host ("Copia scelta: {0:yyyy-MM-dd HH:mm:ss}  {1}" -f $scelta.InstallDate, $scelta.DeviceObject) -ForegroundColor Cyan
if ($Elenco) { exit 0 }

if (-not $Destinazione) { throw 'Manca -Destinazione.' }
$dest = [IO.Path]::GetFullPath($Destinazione).TrimEnd('\')
$vietate = @((Join-Path $env:LOCALAPPDATA 'Temp\claude')) + @(Get-ChildItem -LiteralPath $profilo -Directory -Force -Filter '.c*' -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^\.(claude|codex)' } | ForEach-Object { $_.FullName })
foreach ($v in $vietate) {
  if ($dest -eq $v -or $dest.StartsWith($v + '\', [StringComparison]::OrdinalIgnoreCase)) { throw "La destinazione sta dentro $v, dove il wipe la cancellerebbe." }
}
New-Item -ItemType Directory -Force -Path $dest | Out-Null
$registro = Join-Path $dest 'recupero.log'
Start-Transcript -Path $registro -Append | Out-Null

$link = Join-Path ($lettera + '\') ('recupero-shadow-' + [guid]::NewGuid().ToString('N').Substring(0, 6))
cmd /c mklink /d "$link" "$($scelta.DeviceObject)\" | Out-Null
try {
  $base = Join-Path $link $relProfilo
  # Claude Code: le cartelle e i file che servono a riaprire una sessione con --resume.
  foreach ($acc in @(Get-ChildItem -LiteralPath $base -Directory -Force | Where-Object { $_.Name -match '^\.claude(-account\d+)?$' })) {
    $out = Join-Path $dest $acc.Name.TrimStart('.')
    foreach ($d in 'projects', 'file-history', 'plans', 'session-env', 'sessions', 'todos') {
      $src = Join-Path $acc.FullName $d
      if (Test-Path -LiteralPath $src) { robocopy $src (Join-Path $out $d) /E /COPY:DAT /R:1 /W:1 /NFL /NDL /NJH /NJS /NP | Out-Null }
    }
    foreach ($f in 'history.jsonl', '.claude.json') {
      $src = Join-Path $acc.FullName $f
      if (Test-Path -LiteralPath $src) { New-Item -ItemType Directory -Force -Path $out | Out-Null; Copy-Item -LiteralPath $src -Destination $out -Force }
    }
    Write-Host ("  [ok] {0}" -f $acc.Name)
  }
  # Codex: i rollout e gli indici, che con i rollout rimessi al loro posto rendono resume possibile.
  foreach ($acc in @(Get-ChildItem -LiteralPath $base -Directory -Force | Where-Object { $_.Name -match '^\.codex(-account\d+)?$' })) {
    $out = Join-Path $dest $acc.Name.TrimStart('.')
    $src = Join-Path $acc.FullName 'sessions'
    if (Test-Path -LiteralPath $src) { robocopy $src (Join-Path $out 'sessions') /E /COPY:DAT /R:1 /W:1 /NFL /NDL /NJH /NJS /NP | Out-Null }
    foreach ($f in @(Get-ChildItem -LiteralPath $acc.FullName -File -Force -Filter '*.sqlite*' -ErrorAction SilentlyContinue)) {
      New-Item -ItemType Directory -Force -Path $out | Out-Null; Copy-Item -LiteralPath $f.FullName -Destination $out -Force
    }
    Write-Host ("  [ok] {0}" -f $acc.Name)
  }
}
finally {
  cmd /c rmdir "$link" | Out-Null   # toglie il collegamento, non la copia shadow
}

Write-Host ''
Write-Host 'Sessioni recuperate: account, cartella, identificativo, ultimo istante registrato, KB.'
foreach ($f in @(Get-ChildItem -LiteralPath $dest -Recurse -File -Filter '*.jsonl' | Where-Object { $_.FullName -match '\\projects\\[^\\]+\\[^\\]+\.jsonl$' -or $_.Name -like 'rollout-*' })) {
  $ultimo = ''
  foreach ($r in @(Get-Content -LiteralPath $f.FullName -Tail 30 -Encoding UTF8)) { if ($r -match '"timestamp":"([^"]+)"') { $ultimo = $Matches[1] } }
  $acc = $f.FullName.Substring($dest.Length + 1).Split('\')[0]
  Write-Host ("  {0}  {1}  {2}  {3}  {4}" -f $acc, $f.Directory.Name, $f.BaseName, $ultimo, [int]($f.Length / 1KB))
}
Write-Host ''
Write-Host "Fatto. Le sessioni si rimettono e si riaprono una alla volta con Riapri-Sessione.ps1 -Origine `"$dest`"."
Stop-Transcript | Out-Null
