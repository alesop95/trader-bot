# ============================================================================
# claude-incognito.ps1
# Avvia una sessione Claude Code EFFIMERA: redirige HOME e le cartelle XDG su una
# directory temporanea e azzera CLAUDE_CONFIG_DIR, cosi la sessione non legge ne
# scrive nell'account reale (credenziali, cronologia, configurazione) e parte
# vergine. A fine sessione la temp viene rimossa.
# Complementa session-end-wipe: quello pulisce dopo, questo non scrive nemmeno.
# Tecnica basata sulla specifica XDG Base Directory piu la redirezione di HOME.
#
# Uso:
#   powershell -NoProfile -ExecutionPolicy Bypass -File claude-incognito.ps1 -ProjectDir "E:\mio-progetto"
# ============================================================================
param([string]$ProjectDir = ".")
$tmp = Join-Path $env:TEMP ("claude-incognito-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $tmp, "$tmp\.config", "$tmp\.cache" | Out-Null
$env:HOME = $tmp
$env:XDG_CONFIG_HOME = "$tmp\.config"
$env:XDG_CACHE_HOME = "$tmp\.cache"
Remove-Item Env:\CLAUDE_CONFIG_DIR -ErrorAction SilentlyContinue
Write-Output "Sessione incognito in: $tmp"
Set-Location $ProjectDir
try { claude } finally {
  Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
  Write-Output "Temp incognito rimossa: $tmp"
}
