param([string]$Template = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path)

$ErrorActionPreference = 'Stop'
$dir = Join-Path ([IO.Path]::GetTempPath()) ('prova-temporanei-' + [guid]::NewGuid())
$codexRoot = Join-Path $dir '.codex-account77'
$claudeRoot = Join-Path $dir '.claude'
$tmpClaude = Join-Path $dir 'tmp-claude'
$oldProfile = $env:USERPROFILE
$activeId = 'aaaaaaaa-1111-2222-3333-444444444444'
$closedId = 'bbbbbbbb-1111-2222-3333-444444444444'
$codex = Join-Path $Template '.claude\templates\agenti-terminale\tools\Pulisci-Codex.ps1'
$claude = Join-Path $Template '.claude\templates\tools\session-end-wipe.ps1'

function Scrivi-Prova($path) {
  New-Item -ItemType Directory -Path (Split-Path -Parent $path) -Force | Out-Null
  [IO.File]::WriteAllText($path, 'prova')
  (Get-Item -LiteralPath $path).LastWriteTime = (Get-Date).AddYears(-2)
}
function Verifica($condition, $message) {
  if (-not $condition) { throw $message }
}
function Esegui-Prova($script, $argomenti) {
  & powershell -NoProfile -ExecutionPolicy Bypass -File $script @argomenti | Out-Host
  Verifica ($LASTEXITCODE -eq 0) "Fallito: $script ($LASTEXITCODE)"
}

try {
  $env:USERPROFILE = $dir
  $imgViva = Join-Path $codexRoot "generated_images\$activeId\viva.png"
  $imgChiusa = Join-Path $codexRoot "generated_images\$closedId\chiusa.png"
  $tmpCodex = Join-Path $codexRoot 'tmp\arg0\fixture.txt'
  $viz = Join-Path $codexRoot 'visualizations\2026\fixture.html'
  $auth = Join-Path $codexRoot 'auth.json'
  $stato = Join-Path $codexRoot 'state_5.sqlite'
  $fuori = Join-Path $dir 'Documenti\consegnata.png'
  $lock = Join-Path $codexRoot "thread-writer-locks\$activeId.lock"
  foreach ($p in @((Join-Path $codexRoot 'config.toml'),$auth,$stato,$imgViva,$imgChiusa,$tmpCodex,$viz,$fuori,$lock)) { Scrivi-Prova $p }
  $handle = [IO.File]::Open($lock, 'Open', 'ReadWrite', 'ReadWrite')
  try {
    $handle.Lock(0,1)
    Esegui-Prova $codex @('-Account','77','-SoloTemporanei','-DryRun')
    Verifica (Test-Path -LiteralPath $imgChiusa) 'Dry run Codex ha cancellato un file'
    Esegui-Prova $codex @('-Account','77','-SoloTemporanei')
    Verifica (-not (Test-Path -LiteralPath $imgChiusa)) 'Immagine chiusa ancora nello store'
    Verifica (Test-Path -LiteralPath $imgViva) 'Immagine viva cancellata'
    Verifica (Test-Path -LiteralPath $tmpCodex) 'File condiviso cancellato durante un thread vivo'
  }
  finally { $handle.Dispose() }

  $link = Join-Path $codexRoot 'generated_images\link'
  New-Item -ItemType Junction -Path $link -Target (Split-Path -Parent $fuori) | Out-Null
  Esegui-Prova $codex @('-Account','77','-SoloTemporanei')
  foreach ($p in @($imgViva,$tmpCodex,$viz)) { Verifica (-not (Test-Path -LiteralPath $p)) "Residuo Codex: $p" }
  foreach ($p in @($auth,$stato,$fuori,$link)) { Verifica (Test-Path -LiteralPath $p) "Cancellazione fuori perimetro: $p" }
  [IO.Directory]::Delete($link, $false)

  $paste = Join-Path $claudeRoot 'paste-cache\fixture.txt'
  $scratch = Join-Path $tmpClaude 'D--progetto\fixture.txt'
  $chron = Join-Path $claudeRoot "projects\D--progetto\$closedId.jsonl"
  $history = Join-Path $claudeRoot 'history.jsonl'
  $settings = Join-Path $claudeRoot 'settings.json'
  foreach ($p in @($paste,$scratch,$chron,$history,$settings)) { Scrivi-Prova $p }
  (Get-Item -LiteralPath (Split-Path -Parent $scratch)).LastWriteTime = (Get-Date).AddYears(-2)
  $claudeArgs = @('-BaseProva',$claudeRoot,'-TempProva',$tmpClaude,'-SoloTemporanei')
  Esegui-Prova $claude ($claudeArgs + '-DryRun')
  Verifica (Test-Path -LiteralPath $paste) 'Dry run Claude ha cancellato un file'
  Esegui-Prova $claude $claudeArgs
  foreach ($p in @($paste,$scratch)) { Verifica (-not (Test-Path -LiteralPath $p)) "Residuo Claude: $p" }
  foreach ($p in @($chron,$history,$settings)) { Verifica (Test-Path -LiteralPath $p) "Cancellazione fuori perimetro: $p" }
  Write-Host 'Temporanei degli agenti: prove superate.'
}
finally {
  $env:USERPROFILE = $oldProfile
  if ($link -and (Test-Path -LiteralPath $link)) { [IO.Directory]::Delete($link, $false) }
  if ([IO.Path]::GetFullPath($dir).StartsWith([IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\') + '\', 'OrdinalIgnoreCase')) {
    Remove-Item -LiteralPath $dir -Recurse -Force -ErrorAction SilentlyContinue
  }
}
