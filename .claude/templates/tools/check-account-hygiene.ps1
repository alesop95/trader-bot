# ============================================================================
# check-account-hygiene.ps1
# Verifica (sola lettura, non modifica nulla) che l'ACCOUNT Claude Code ATTIVO
# rispetti l'igiene del magazzino nascosto richiesta dal sistema di progetto:
#   1. "autoMemoryEnabled": false          -> auto-memory nativa spenta
#   2. hook SessionEnd -> session-end-wipe -> wipe automatico a chiusura sessione
#   3. lo script di wipe installato e configurato per QUESTA macchina
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

# --- 3. lo script di wipe installato parla di QUESTA macchina ----------------
# Un hook registrato non basta: lo script puo essere il template non compilato, oppure
# una copia presa da un'altra macchina, con prefissi che qui non corrispondono a niente.
# In quel secondo caso l'insieme dei progetti preservati e vuoto e il wipe, se le sue
# guardie non lo fermassero, cancellerebbe l'intero magazzino. Il controllo e in sola
# lettura: invoca lo script installato in modo -List, che non rimuove nulla.
$okCfg = $false
$cfgNote = ''
$wipe = Join-Path $cfg 'hooks\session-end-wipe.ps1'
if (-not (Test-Path -LiteralPath $wipe)) {
  $m = [regex]::Match($cmd, '[^"'' ]*session-end-wipe\.ps1')
  $wipe = if ($m.Success) { $m.Value } else { '' }
}
if (-not $okHook) { $cfgNote = 'hook assente, niente da verificare' }
elseif (-not $wipe -or -not (Test-Path -LiteralPath $wipe)) { $cfgNote = "script di wipe non trovato nell'account" }
else {
  $src = Get-Content -LiteralPath $wipe -Raw
  if ($src -match '(?m)^\$keepPrefixes\s*=\s*@\(''<') {
    $cfgNote = "il template e installato ma NON compilato: keepPrefixes e ancora il segnaposto"
  }
  else {
    $listing = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $wipe -List 2>&1 | Out-String
    $m = [regex]::Match($listing, 'Totale (\d+), preservati (\d+)')
    if (-not $m.Success) {
      $cfgNote = "lo script installato non risponde a -List: e una versione precedente, priva delle guardie"
    }
    else {
      $totale = [int]$m.Groups[1].Value
      $preservati = [int]$m.Groups[2].Value
      $derogaVuoto = $src -match '(?m)^\$allowEmptyKeep\s*=\s*\$true'
      if ($totale -gt 0 -and $preservati -eq 0 -and -not $derogaVuoto) {
        $cfgNote = "nessuno dei $totale slug presenti corrisponde ai prefissi configurati: la configurazione e di un'altra macchina"
      }
      else {
        $okCfg = $true
        $cfgNote = "$preservati slug preservati su $totale"
      }
    }
  }
}

Write-Output ("[{0}] autoMemoryEnabled = false" -f ($(if ($okMem) { 'PASS' } else { 'FAIL' })))
Write-Output ("[{0}] hook SessionEnd -> session-end-wipe" -f ($(if ($okHook) { 'PASS' } else { 'FAIL' })))
Write-Output ("[{0}] wipe configurato per questa macchina ({1})" -f ($(if ($okCfg) { 'PASS' } else { 'FAIL' })), $cfgNote)

if ($okMem -and $okHook -and $okCfg) { Write-Output "`nOK: l'account attivo e' in regola."; exit 0 }

Write-Output "`nAZIONE RICHIESTA: l'account attivo NON e' in regola."
if (-not $okMem)  { Write-Output ' - aggiungi  "autoMemoryEnabled": false  al settings.json dell''account' }
if (-not $okHook) { Write-Output ' - installa session-end-wipe.ps1 nell''account e registra un hook SessionEnd che lo esegua' }
if (-not $okCfg -and $okHook) { Write-Output "   - compila keepPrefixes nello script installato: eseguirlo con -List elenca gli slug presenti, senza rimuovere niente" }
Write-Output '   (riferimenti: templates/tools/session-end-wipe.ps1 e PROJECT-SYSTEM.md sezione 15)'
exit 1
