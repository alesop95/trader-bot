<#
.SYNOPSIS
  Consumo di token di TUTTE le radici dei due agenti da terminale, in un colpo.

.DESCRIPTION
  Il problema che risolve e' banale e costoso: il consumo di un piano si guarda
  una radice alla volta, e con sei radici su due agenti nessuno lo fa mai. Il
  risultato e' che si lavora su una flotta satura mentre un'altra e' ferma, che
  e' precisamente lo spreco che il setup multi-account esiste per evitare.

  Sola lettura. Non chiama nessun servizio esterno: legge i file di sessione che
  i due agenti tengono gia' sul disco, tramite `ccusage`, che li interpreta senza
  inviare nulla altrove. Applicazione del principio per cui prima di costruire
  strumentazione si guarda che cosa il sistema produce gia'.

  ATTENZIONE alla lettura del risultato, perche' e' il punto in cui si sbaglia:
  la colonna in valuta e' NOZIONALE, cioe' quanto quei token costerebbero a
  tariffa a consumo. Su un piano in abbonamento non si paga: serve come
  indicatore di valore, non come spesa. Le colonne che contano sono quelle dei
  token, e fra queste `Cache Read` e' contesto riletto, non lavoro nuovo.

.PARAMETER Giorni
  Finestra in giorni. Default 1, cioe' oggi.

.PARAMETER Dettaglio
  Mostra il rapporto completo di ccusage invece del solo riepilogo per radice.

.PARAMETER Json
  Emette il riepilogo come JSON, per usarlo da un altro strumento.

.EXAMPLE
  .\scripts\Consumo-Agenti.ps1
.EXAMPLE
  .\scripts\Consumo-Agenti.ps1 -Giorni 7
.EXAMPLE
  .\scripts\Consumo-Agenti.ps1 -Json

.NOTES
  Scheda: docs\10_CODEX_CLI_E_WORKSPACE_OPENAI.md
  Richiede Node (per `npx ccusage`). Nessuna installazione permanente.
#>
[CmdletBinding()]
param(
  [int]$Giorni = 1,
  [switch]$Dettaglio,
  [switch]$Json
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Trova($prefisso) {
  @(Get-ChildItem -LiteralPath $env:USERPROFILE -Directory -Filter "$prefisso*" -ErrorAction SilentlyContinue |
    Sort-Object Name)
}

$radici = @()
foreach ($d in (Trova '.claude-account')) { $radici += [pscustomobject]@{ Agente = 'Claude'; Nome = $d.Name; Percorso = $d.FullName } }
foreach ($d in (Trova '.codex-account')) { $radici += [pscustomobject]@{ Agente = 'Codex'; Nome = $d.Name; Percorso = $d.FullName } }

# Le radici di default dei due agenti: non hanno numero ma consumano quota, e
# dimenticarle e' il modo piu' facile di non capire dove sono finiti i token.
foreach ($coppia in @(@('Claude', '.claude'), @('Codex', '.codex'))) {
  $p = Join-Path $env:USERPROFILE $coppia[1]
  if (Test-Path -LiteralPath $p) {
    $radici += [pscustomobject]@{ Agente = $coppia[0]; Nome = $coppia[1] + ' (default)'; Percorso = $p }
  }
}

if ($radici.Count -eq 0) {
  Write-Host 'Nessuna radice di agente trovata nel profilo utente.' -ForegroundColor Yellow
  exit 1
}

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
  Write-Host 'Node non disponibile: ccusage non puo essere eseguito.' -ForegroundColor Red
  exit 1
}

# Cartella vuota usata per isolare una flotta dall'altra durante la lettura.
# Non basta che esista: deve AVERE LA FORMA di una radice di agente, altrimenti
# ccusage non restituisce zero, fallisce. Si creano quindi le sottocartelle che
# le due flotte si aspettano, vuote.
$vuoto = Join-Path $env:TEMP 'consumo-agenti-vuoto'
foreach ($sub in @('', 'projects', 'sessions')) {
  $q = if ($sub) { Join-Path $vuoto $sub } else { $vuoto }
  if (-not (Test-Path -LiteralPath $q)) { New-Item -ItemType Directory -Path $q -Force | Out-Null }
}

$da = (Get-Date).AddDays(-([Math]::Max($Giorni, 1) - 1)).ToString('yyyyMMdd')

Write-Host ''
Write-Host ("=== Consumo agenti, dal {0} ({1} giorni) ===" -f $da, $Giorni) -ForegroundColor Cyan
Write-Host ''

$righe = @()
foreach ($r in $radici) {
  # Ogni radice si interroga da sola: ccusage legge i propri file di sessione
  # nella cartella indicata dalla variabile d'ambiente dell'agente.
  # L'altra variabile punta a una cartella VUOTA ma ESISTENTE, non a un nome
  # inventato: ccusage su un percorso inesistente fallisce del tutto invece di
  # restituire zero, e l'errore si presenta come "nessun dato" indistinguibile
  # da un consumo nullo.
  $vecchioClaude = $env:CLAUDE_CONFIG_DIR
  $vecchioCodex = $env:CODEX_HOME
  if ($r.Agente -eq 'Claude') { $env:CLAUDE_CONFIG_DIR = $r.Percorso; $env:CODEX_HOME = $vuoto }
  else { $env:CODEX_HOME = $r.Percorso; $env:CLAUDE_CONFIG_DIR = $vuoto }

  $totale = 0
  try {
    $out = & npx --yes ccusage@latest daily --since $da --json 2>$null | Out-String
    if ($out -and $out.Trim().StartsWith('{')) {
      $j = $out | ConvertFrom-Json
      if ($j.PSObject.Properties.Name -contains 'daily') {
        foreach ($g in $j.daily) {
          foreach ($campo in @('inputTokens', 'outputTokens', 'cacheCreationTokens', 'cacheReadTokens')) {
            if ($g.PSObject.Properties.Name -contains $campo) { $totale += [int64]$g.$campo }
          }
        }
      }
    }
  }
  catch { $totale = -1 }

  $env:CLAUDE_CONFIG_DIR = $vecchioClaude
  $env:CODEX_HOME = $vecchioCodex

  $righe += [pscustomobject]@{
    Agente = $r.Agente
    Radice = $r.Nome
    Token  = $totale
  }
}

if ($Json) {
  $righe | ConvertTo-Json -Depth 3
  exit 0
}

$righe | Format-Table -AutoSize

$perAgente = @($righe | Where-Object { $_.Token -gt 0 } | Group-Object Agente |
  ForEach-Object { [pscustomobject]@{ Agente = $_.Name; Token = ($_.Group | Measure-Object Token -Sum).Sum } })

if ($perAgente) {
  Write-Host 'Per flotta:' -ForegroundColor Cyan
  $perAgente | Format-Table -AutoSize
  if ($perAgente.Count -ge 2) {
    $max = ($perAgente | Sort-Object Token -Descending)[0]
    $min = ($perAgente | Sort-Object Token)[0]
    if ($min.Token -gt 0 -and $max.Token / [double]$min.Token -gt 5) {
      Write-Host ("Squilibrio: {0} consuma {1:N0}x rispetto a {2}." -f $max.Agente, ($max.Token / [double]$min.Token), $min.Agente) -ForegroundColor Yellow
      Write-Host 'Il serbatoio fermo e la leva che aumenta il lavoro svolto senza avvicinare un limite.' -ForegroundColor Yellow
    }
  }
}

Write-Host ''
Write-Host 'Nota di lettura: la valuta in ccusage e NOZIONALE, non e una spesa su un' -ForegroundColor DarkGray
Write-Host 'piano in abbonamento. Cache Read e contesto riletto, non lavoro nuovo.' -ForegroundColor DarkGray
if ($Dettaglio) {
  Write-Host ''
  Write-Host '=== rapporto completo, tutte le radici insieme ===' -ForegroundColor Cyan
  & npx --yes ccusage@latest daily --since $da
}
Write-Host ''
