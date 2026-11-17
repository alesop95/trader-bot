<#
.SYNOPSIS
  Porta in tutte le radici dei due agenti i valori scelti per la macchina:
  la riserva dei subagent e i plugin da avere installati. Idempotente.

.DESCRIPTION
  I due installatori ricostruiscono le radici; questo script vi riporta sopra
  due scelte del proprietario che altrimenti andrebbero rifatte a mano radice
  per radice, e che dopo una formattazione nessuno ricorderebbe:

    - la riserva, cioe' la percentuale del limite del piano oltre la quale i
      subagent non partono piu'. La scrive `riserva-agenti.py imposta`, con la
      stessa forma per Claude Code e per Codex;
    - i plugin, installati per account con il gestore del rispettivo client.
      Un plugin gia' presente non si reinstalla.

  I valori NON stanno nel template, perche' sono della macchina: stanno in un
  file JSON del repository di macchina, della forma

    {
      "riserva": { "settimanale": 80, "cinqueOre": 0, "azione": "nega" },
      "plugin": {
        "claude": ["superpowers@claude-plugins-official"],
        "codex":  ["superpowers@openai-curated-remote"]
      }
    }

  Le credenziali non si toccano. Un plugin si installa anche su una radice non
  autenticata, se il gestore del client lo consente; se fallisce lo si dichiara
  e si prosegue con le altre radici.

.PARAMETER Valori
  Percorso del file dei valori. Se manca, lo script non fa nulla e lo dice.

.PARAMETER Verifica
  Sola lettura: dice che cosa manca, non scrive e non installa.

.EXAMPLE
  .\Installa-Plugin.ps1 -Valori .\scripts\agenti-macchina.json -Verifica
.EXAMPLE
  .\Installa-Plugin.ps1 -Valori .\scripts\agenti-macchina.json
#>
[CmdletBinding()]
param(
  [string]$Valori,
  [int[]]$Claude,
  [int[]]$Codex,
  [switch]$Verifica
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Nota($t, $c) { Write-Host $t -ForegroundColor $c }

if (-not $Valori -or -not (Test-Path -LiteralPath $Valori)) {
  Nota '  nessun file di valori di macchina indicato: riserva e plugin restano come sono.' 'DarkGray'
  exit 0
}
try { $dati = Get-Content -LiteralPath $Valori -Raw -Encoding UTF8 | ConvertFrom-Json }
catch {
  Nota ("  {0}: JSON non valido, niente applicato." -f $Valori) 'Red'
  exit 1
}

function Radici($prefisso, $scelte) {
  $tutte = @(Get-ChildItem -LiteralPath $env:USERPROFILE -Directory -Filter "$prefisso*" -ErrorAction SilentlyContinue |
    Where-Object { $_.Name.Substring($prefisso.Length) -match '^\d+$' } | Sort-Object Name)
  if ($scelte -and $scelte.Count -gt 0) {
    $tutte = @($tutte | Where-Object { $scelte -contains [int]$_.Name.Substring($prefisso.Length) })
  }
  return $tutte
}

function Proprieta($oggetto, $nome) {
  if ($null -ne $oggetto -and $oggetto.PSObject.Properties.Name -contains $nome) { return $oggetto.$nome }
  return $null
}

# --- riserva ----------------------------------------------------------------
$riserva = Proprieta $dati 'riserva'
$strumento = Join-Path $PSScriptRoot 'riserva-agenti.py'
if ($riserva -and (Test-Path -LiteralPath $strumento) -and (Get-Command python -ErrorAction SilentlyContinue)) {
  $settimanale = Proprieta $riserva 'settimanale'
  $cinque = Proprieta $riserva 'cinqueOre'
  $azione = Proprieta $riserva 'azione'
  if ($null -eq $settimanale) { $settimanale = 0 }
  if ($null -eq $cinque) { $cinque = 0 }
  if (-not $azione) { $azione = 'nega' }
  if ($Verifica) {
    Nota ("  riserva voluta: settimanale {0}%, cinque ore {1}%, azione {2}. Stato:" -f $settimanale, $cinque, $azione) 'White'
    & python $strumento stato | ForEach-Object { Nota ("    {0}" -f $_) 'DarkGray' }
  }
  else {
    & python $strumento imposta --settimanale $settimanale --cinque-ore $cinque --azione $azione | ForEach-Object { Nota ("  riserva, {0}" -f $_) 'Green' }
  }
}
elseif ($riserva) {
  Nota '  riserva non applicata: manca python oppure riserva-agenti.py.' 'DarkYellow'
}

# --- plugin -----------------------------------------------------------------
function Presente-Claude($radice, $plugin) {
  $f = Join-Path $radice 'plugins\installed_plugins.json'
  if (-not (Test-Path -LiteralPath $f)) { return $false }
  try { $j = Get-Content -LiteralPath $f -Raw -Encoding UTF8 | ConvertFrom-Json } catch { return $false }
  $p = Proprieta $j 'plugins'
  return ($null -ne $p -and $p.PSObject.Properties.Name -contains $plugin)
}

function Presente-Codex($radice, $plugin) {
  $nome, $mercato = $plugin -split '@', 2
  if (-not $mercato) { return $false }
  return (Test-Path -LiteralPath (Join-Path $radice ("plugins\cache\{0}\{1}" -f $mercato, $nome)))
}

function Applica($agente, $prefisso, $scelte, $elenco, $variabile, $comando, $argomentiBase) {
  if (-not $elenco) { return }
  if (-not (Get-Command $comando -ErrorAction SilentlyContinue)) {
    Nota ("  {0}: comando {1} non trovato, plugin non installati." -f $agente, $comando) 'DarkYellow'
    return
  }
  foreach ($r in (Radici $prefisso $scelte)) {
    foreach ($plugin in @($elenco)) {
      $presente = if ($agente -eq 'Claude') { Presente-Claude $r.FullName $plugin } else { Presente-Codex $r.FullName $plugin }
      if ($presente) { Nota ("  {0}: {1} presente" -f $r.Name, $plugin) 'DarkGray'; continue }
      if ($Verifica) { Nota ("  {0}: {1} MANCA" -f $r.Name, $plugin) 'Yellow'; continue }
      $prima = [Environment]::GetEnvironmentVariable($variabile, 'Process')
      try {
        [Environment]::SetEnvironmentVariable($variabile, $r.FullName, 'Process')
        $tutti = @($argomentiBase) + @($plugin)
        & $comando @tutti | Out-Null
        if ($LASTEXITCODE -eq 0) { Nota ("  {0}: {1} installato" -f $r.Name, $plugin) 'Green' }
        else { Nota ("  {0}: {1} NON installato, il gestore ha risposto con codice {2}" -f $r.Name, $plugin, $LASTEXITCODE) 'Red' }
      }
      catch { Nota ("  {0}: {1} NON installato: {2}" -f $r.Name, $plugin, $_.Exception.Message) 'Red' }
      finally { [Environment]::SetEnvironmentVariable($variabile, $prima, 'Process') }
    }
  }
}

$plugin = Proprieta $dati 'plugin'
if ($plugin) {
  Applica 'Claude' '.claude-account' $Claude (Proprieta $plugin 'claude') 'CLAUDE_CONFIG_DIR' 'claude' @('plugin', 'install', '--scope', 'user')
  Applica 'Codex' '.codex-account' $Codex (Proprieta $plugin 'codex') 'CODEX_HOME' 'codex' @('plugin', 'add')
}
