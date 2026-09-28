<#
.SYNOPSIS
  Installa Codex CLI e ricostruisce le radici multi-account da zero.

.DESCRIPTION
  E' lo script che rende il setup multi-account riproducibile 1:1 dopo una
  formattazione. Tutto cio' che serve sta nel repository: questo script piu'
  codex-config.riferimento.toml. Nulla va copiato dalla macchina precedente.

  Cosa ricostruisce automaticamente:
    - l'installazione di Codex CLI, se assente;
    - le N radici <PROFILO_UTENTE>\.codex-account<N>;
    - il config.toml di ciascuna, dalla copia di riferimento versionata.

  Cosa NON ricostruisce, deliberatamente:
    - auth.json, cioe' le credenziali. Non e' un limite ma la scelta corretta:
      una credenziale copiata da una macchina all'altra e' una credenziale che
      si e' propagata fuori dal proprio custode. Si rifa' un login per radice.

  Lo script e' idempotente: rieseguirlo non sovrascrive un config.toml gia'
  presente se non glielo si chiede con -Forza, e non tocca mai auth.json.

.PARAMETER Radici
  Quante radici creare. Default 3.

.PARAMETER Verifica
  Sola lettura: non installa e non crea nulla, stampa solo il quadro.

.PARAMETER Forza
  Riscrive i config.toml esistenti dalla copia di riferimento. Da usare quando
  la copia di riferimento cambia e le radici vanno riallineate.

.EXAMPLE
  .\scripts\Installa-Codex.ps1 -Verifica
.EXAMPLE
  .\scripts\Installa-Codex.ps1 -Radici 3
.EXAMPLE
  .\scripts\Installa-Codex.ps1 -Radici 3 -Forza

.NOTES
  Scheda di riferimento: docs\10_CODEX_CLI_E_WORKSPACE_OPENAI.md
#>
[CmdletBinding()]
param(
  # Elenco dei numeri di radice, non un conteggio: cosi' si puo' agire su un
  # sottoinsieme (es. -Account 2,5) e i due installatori hanno la stessa firma.
  # `-Radici` resta accettato come alias per non rompere comandi gia' scritti.
  [Alias('Radici')]
  [ValidateRange(1, 99)]
  [int[]]$Account = @(1, 2, 3),

  [switch]$Verifica,

  [switch]$Forza
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repo = Split-Path -Parent $PSScriptRoot
$riferimento = Join-Path $repo 'codex-config.riferimento.toml'
$riferimentoAgents = Join-Path $repo 'codex-agents.riferimento.md'

function Scrivi($testo, $colore) {
  Write-Host $testo -ForegroundColor $colore
}

Scrivi '' 'Gray'
Scrivi '=== Installa-Codex ===' 'Cyan'
if ($Verifica) { Scrivi 'Modo: SOLA LETTURA, nessuna modifica.' 'Yellow' }

# --- Guardia: la copia di riferimento esiste --------------------------------
# Senza di essa le radici nascerebbero con i default di Codex invece che con il
# perimetro deciso, e la differenza non e' visibile a occhio.
if (-not (Test-Path -LiteralPath $riferimento)) {
  Scrivi "MANCA la copia di riferimento: $riferimento" 'Red'
  Scrivi 'Senza di essa le radici userebbero i default di Codex. Interrotto.' 'Red'
  exit 1
}

# --- Passo 1: Node ----------------------------------------------------------
$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) {
  Scrivi 'Node.js non trovato. Installalo (versione 22 o superiore) e rilancia.' 'Red'
  exit 1
}
Scrivi ("Node.js         {0}" -f (& node -v)) 'Green'

# --- Passo 2: Codex ---------------------------------------------------------
$codex = Get-Command codex -ErrorAction SilentlyContinue
if ($codex) {
  Scrivi ("Codex CLI       {0}" -f (& codex --version)) 'Green'
}
elseif ($Verifica) {
  Scrivi 'Codex CLI       ASSENTE (in sola lettura non lo installo)' 'Yellow'
}
else {
  Scrivi 'Codex CLI assente: installo con npm...' 'Cyan'
  & npm install -g '@openai/codex'
  if ($LASTEXITCODE -ne 0) {
    Scrivi 'Installazione fallita. Interrotto.' 'Red'
    exit 1
  }
  $codex = Get-Command codex -ErrorAction SilentlyContinue
  if ($codex) { Scrivi ("Codex CLI       {0} (appena installato)" -f (& codex --version)) 'Green' }
}

# --- Passo 3: le radici -----------------------------------------------------
Scrivi '' 'Gray'
$quadro = @()
foreach ($n in ($Account | Sort-Object -Unique)) {
  $radice = Join-Path $env:USERPROFILE ".codex-account$n"
  $config = Join-Path $radice 'config.toml'
  $auth = Join-Path $radice 'auth.json'
  $azione = 'gia a posto'

  if (-not (Test-Path -LiteralPath $radice)) {
    if ($Verifica) { $azione = 'da creare' }
    else {
      New-Item -ItemType Directory -Path $radice -Force | Out-Null
      $azione = 'radice creata'
    }
  }

  $serveConfig = (-not (Test-Path -LiteralPath $config)) -or $Forza
  if ($serveConfig) {
    if ($Verifica) {
      if (Test-Path -LiteralPath $config) { $azione = 'config da riallineare' }
      else { $azione = 'config da scrivere' }
    }
    else {
      Copy-Item -LiteralPath $riferimento -Destination $config -Force
      if ($azione -eq 'radice creata') { $azione = 'radice + config creati' }
      else { $azione = 'config riallineato' }
    }
  }

  # AGENTS.md: puntatore al repository, non copia degli strumenti. Codex lo legge
  # all'inizio di ogni sessione su questa radice, quindi il puntatore fa un lavoro
  # utile invece di essere solo un promemoria per un umano di passaggio.
  $agents = Join-Path $radice 'AGENTS.md'
  $serveAgents = (-not (Test-Path -LiteralPath $agents)) -or $Forza
  if ($serveAgents -and (Test-Path -LiteralPath $riferimentoAgents)) {
    if ($Verifica) {
      if ($azione -eq 'gia a posto') { $azione = 'AGENTS.md da scrivere' }
    }
    else {
      Copy-Item -LiteralPath $riferimentoAgents -Destination $agents -Force
      if ($azione -eq 'gia a posto') { $azione = 'AGENTS.md scritto' }
      else { $azione = $azione + ' + AGENTS.md' }
    }
  }

  # auth.json non viene mai toccato, ne' creato ne' rimosso ne' copiato.
  $haAuth = Test-Path -LiteralPath $auth
  $statoLogin = 'DA FARE'
  if ($haAuth) { $statoLogin = 'presente' }

  $quadro += [pscustomobject]@{
    Radice = ".codex-account$n"
    Config = (Test-Path -LiteralPath $config)
    Agents = (Test-Path -LiteralPath $agents)
    Login  = $statoLogin
    Azione = $azione
  }
}

$quadro | Format-Table -AutoSize

# --- Passo 4: cosa resta da fare a mano -------------------------------------
$daLoggare = @($quadro | Where-Object { $_.Login -eq 'DA FARE' })
if ($daLoggare.Count -gt 0) {
  Scrivi 'Login ancora da fare (uno alla volta):' 'Yellow'
  foreach ($r in $daLoggare) {
    $n = $r.Radice -replace '\D', ''
    Scrivi ("  .\scripts\Avvia-Codex.ps1 -Account {0} -Resto login" -f $n) 'White'
  }
  Scrivi '' 'Gray'
  Scrivi 'IMPORTANTE: apri una finestra PRIVATA del browser prima di ogni login.' 'Yellow'
  Scrivi 'Il flusso OAuth riusa la sessione aperta e registrerebbe due volte lo' 'Yellow'
  Scrivi 'stesso membro, senza segnalare nulla.' 'Yellow'
}
else {
  Scrivi 'Tutte le radici hanno credenziali. Verifica con -Stato di Avvia-Codex.' 'Green'
}
Scrivi '' 'Gray'
