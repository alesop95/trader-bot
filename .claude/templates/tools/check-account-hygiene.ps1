# ============================================================================
# check-account-hygiene.ps1
# Verifica (sola lettura, non modifica nulla) che l'ACCOUNT Claude Code ATTIVO
# rispetti l'igiene del magazzino nascosto richiesta dal sistema di progetto:
#   1. "autoMemoryEnabled": false        -> auto-memory nativa spenta
#   2. hook SessionEnd -> session-end-wipe -> wipe automatico a chiusura sessione
# Da eseguire al Passo 0 dell'inizializzazione/allineamento di un progetto.
# Vedi PROJECT-SYSTEM.md sezione 15.
# ============================================================================
$ErrorActionPreference = 'Stop'

$cfg = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $env:USERPROFILE '.claude' }
$settings = Join-Path $cfg 'settings.json'
Write-Output "Account attivo (CLAUDE_CONFIG_DIR): $cfg"

if (-not (Test-Path $settings)) { Write-Output "FAIL: settings.json non trovato in $cfg"; exit 1 }
$j = Get-Content -LiteralPath $settings -Raw | ConvertFrom-Json

$okMem = ($j.autoMemoryEnabled -eq $false)

$cmd = ''
try { $cmd = ($j.hooks.SessionEnd | ForEach-Object { $_.hooks } | ForEach-Object { $_.command }) -join "`n" } catch {}
$okHook = ($cmd -match 'session-end-wipe')

Write-Output ("[{0}] autoMemoryEnabled = false" -f ($(if ($okMem) { 'PASS' } else { 'FAIL' })))
Write-Output ("[{0}] hook SessionEnd -> session-end-wipe" -f ($(if ($okHook) { 'PASS' } else { 'FAIL' })))

if ($okMem -and $okHook) { Write-Output "`nOK: l'account attivo e' in regola."; exit 0 }

Write-Output "`nAZIONE RICHIESTA: l'account attivo NON e' in regola."
if (-not $okMem)  { Write-Output ' - aggiungi  "autoMemoryEnabled": false  al settings.json dell''account' }
if (-not $okHook) { Write-Output ' - installa session-end-wipe.ps1 nell''account e registra un hook SessionEnd che lo esegua' }
Write-Output '   (riferimenti: templates/tools/session-end-wipe.ps1 e PROJECT-SYSTEM.md sezione 15)'
exit 1
