<#
.SYNOPSIS
  Rileva da Windows se un modello locale (colibri) e' utilizzabile, entrando in WSL dove il modello deve girare.
.DESCRIPTION
  Su Windows il modello non gira in nativo: gira dentro WSL2. Questo wrapper trova la distribuzione WSL,
  vi traduce il percorso dello script di rilevamento e lo esegue li'. Sola lettura.
  Su Linux nativo non serve questo wrapper: si esegue direttamente tools/rileva.sh.
.PARAMETER Distro
  Nome della distribuzione WSL da usare. Se omesso, usa quella predefinita.
.PARAMETER Valori
  Percorso WSL del file dei valori del banco (es. /home/<utente>/llm-local.valori.sh), per usare percorsi non predefiniti.
#>
param(
  [string]$Distro = "",
  [string]$Valori = ""
)

$ErrorActionPreference = "Stop"

# Verifica che WSL esista.
$wsl = Get-Command wsl.exe -ErrorAction SilentlyContinue
if (-not $wsl) {
  Write-Host "WSL non e' installato. Su Windows il modello locale richiede WSL2 (vedi docs/windows-docker-wsl-vs-linux.md)."
  exit 1
}

# Distribuzione: quella passata, o la predefinita.
$distroArgs = @()
if ($Distro -ne "") { $distroArgs = @("-d", $Distro) }

# Percorso di questo script -> cartella tools -> rileva.sh, tradotto in percorso WSL.
$toolsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rilevaWin = Join-Path $toolsDir "rileva.sh"
if (-not (Test-Path $rilevaWin)) {
  Write-Host "Script rileva.sh non trovato accanto a questo wrapper: $rilevaWin"
  exit 1
}
$rilevaWsl = (& wsl.exe @distroArgs wslpath -u "$rilevaWin").Trim()

# Esegue il rilevamento dentro WSL, passando eventualmente il file dei valori.
$cmd = "bash '$rilevaWsl'"
if ($Valori -ne "") { $cmd += " '$Valori'" }
& wsl.exe @distroArgs bash -lc $cmd
exit $LASTEXITCODE
