<#
.SYNOPSIS
  Installa nel profilo PowerShell i comandi brevi per tutte le radici dei due
  agenti da terminale: claude-account<N> e codex-account<N>.

.DESCRIPTION
  Il repository e' la FONTE degli strumenti, non il modo in cui li si lancia ogni
  giorno. Prima di questo script i comandi dei due agenti erano asimmetrici senza
  ragione: Claude si avviava con `claude-account2`, Codex con il percorso intero
  di uno script dentro il repository. La simmetria di sostanza esisteva gia', ma
  non quella d'uso, ed e' quella che si sente.

  Dopo l'installazione entrambi si avviano allo stesso modo:

      cd <progetto>
      claude-account2
      codex-account2

  DIFFERENZA INTERNA, documentata perche' non e' arbitraria. La funzione di
  Claude imposta la variabile d'ambiente e chiama l'eseguibile: basta cosi',
  perche' la pulizia di fine sessione la fa un hook nativo. La funzione di Codex
  passa invece per `Avvia-Codex.ps1`, perche' Codex NON ha un hook di ciclo di
  vita: le guardie sulla radice, il vincolo sulla cartella di lavoro e la pulizia
  all'uscita vivono nel wrapper. Stessa invocazione, motori diversi.

  La cartella di lavoro e' quella corrente, come ci si aspetta da un comando di
  shell, e resta sovrascrivibile passando `-Progetto`.

  Il blocco contiene anche `chiudi`, che lancia chiudi-sessione.ps1 del repository
  in cui si trova il terminale: e' uguale per i due agenti, perche' la chiusura
  (controlli, commit confermato, push, impronta, wipe) non dipende da chi ha lavorato.

  Il blocco inserito nel profilo e' delimitato da marcatori e viene SOSTITUITO a
  ogni esecuzione: lo script e' idempotente e non accumula definizioni duplicate.
  Il profilo viene copiato prima di essere toccato.

.PARAMETER Verifica
  Sola lettura: mostra che cosa verrebbe scritto e dove, senza scrivere.

.PARAMETER RimuoviVecchie
  Rimuove dal profilo le definizioni di claude-account<N> e codex-account<N>
  scritte a mano fuori dal blocco generato. Non tocca nient'altro, e il profilo
  viene comunque copiato prima. Serve una volta sola, alla prima installazione.

.PARAMETER Profilo
  Percorso del profilo da modificare. Per default quello dell'host corrente.

.EXAMPLE
  .\scripts\Installa-Comandi.ps1 -Verifica
.EXAMPLE
  .\scripts\Installa-Comandi.ps1

.NOTES
  Scheda: docs\10_CODEX_CLI_E_WORKSPACE_OPENAI.md
  Dopo l'installazione serve riaprire PowerShell, oppure `. $PROFILE`.
#>
[CmdletBinding()]
param(
  [switch]$Verifica,
  [switch]$RimuoviVecchie,
  [string]$Profilo
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$INIZIO = '# >>> comandi agenti (windows-status) >>>'
$FINE = '# <<< comandi agenti (windows-status) <<<'

function Nota($t, $c) { Write-Host $t -ForegroundColor $c }

Nota '' 'Gray'
Nota '=== Installa-Comandi ===' 'Cyan'
if ($Verifica) { Nota 'Modo: SOLA LETTURA, nessuna modifica.' 'Yellow' }

if (-not $Profilo) { $Profilo = $PROFILE.CurrentUserCurrentHost }
Nota ("Profilo     {0}" -f $Profilo) 'White'

$avvia = Join-Path $PSScriptRoot 'Avvia-Codex.ps1'
if (-not (Test-Path -LiteralPath $avvia)) {
  Nota "MANCA $avvia. Interrotto." 'Red'
  exit 1
}
Nota ("Launcher    {0}" -f $avvia) 'White'

# --- scoperta delle radici --------------------------------------------------
function Trova($prefisso) {
  @(Get-ChildItem -LiteralPath $env:USERPROFILE -Directory -Filter "$prefisso*" -ErrorAction SilentlyContinue |
    ForEach-Object { if ($_.Name -match '(\d+)$') { [int]$Matches[1] } } | Sort-Object -Unique)
}
$claude = Trova '.claude-account'
$codex = Trova '.codex-account'
Nota ("Radici      Claude: {0}   Codex: {1}" -f ($claude -join ','), ($codex -join ',')) 'White'

if ($claude.Count -eq 0 -and $codex.Count -eq 0) {
  Nota 'Nessuna radice trovata: non c e nulla da installare.' 'Yellow'
  exit 1
}

# --- generazione del blocco -------------------------------------------------
$righe = New-Object System.Collections.Generic.List[string]
$righe.Add($INIZIO)
$righe.Add('# Generato da scripts\Installa-Comandi.ps1. Non modificare a mano:')
$righe.Add('# le modifiche si fanno nello script e si ridistribuiscono rieseguendolo.')
$righe.Add('')

foreach ($n in $claude) {
  $righe.Add("function claude-account$n {")
  $righe.Add("    `$env:CLAUDE_CONFIG_DIR = `"`$env:USERPROFILE\.claude-account$n`"")
  $righe.Add('    claude @args')
  $righe.Add('}')
}
if ($claude.Count -gt 0) { $righe.Add('') }

foreach ($n in $codex) {
  # Passa dal launcher: guardie sulla radice, vincolo sulla cartella di lavoro e
  # pulizia all'uscita. La cartella corrente diventa il progetto, salvo che
  # chi chiama passi esplicitamente -Progetto.
  $righe.Add("function codex-account$n {")
  $righe.Add("    if (`$args -contains '-Progetto') { & '$avvia' -Account $n @args }")
  $righe.Add("    else { & '$avvia' -Account $n -Progetto (Get-Location).Path @args }")
  $righe.Add('}')
}
if ($codex.Count -gt 0) { $righe.Add('') }

# Chiusura di sessione, uguale per Claude e Codex perche' non dipende dall'agente: cerca
# chiudi-sessione.ps1 nel repository in cui si trova il terminale, in tools\ di un progetto
# istanziato oppure sotto .claude\templates\tools\ nel template, e gli passa gli argomenti.
$righe.Add('function chiudi {')
$righe.Add('    $radice = (git rev-parse --show-toplevel 2>$null)')
$righe.Add('    if (-not $radice) { Write-Host "chiudi: la cartella corrente non e'' dentro un repository git." -ForegroundColor Red; return }')
$righe.Add('    $script = @("tools\chiudi-sessione.ps1", ".claude\templates\tools\chiudi-sessione.ps1") | ForEach-Object { Join-Path $radice $_ } | Where-Object { Test-Path $_ } | Select-Object -First 1')
$righe.Add('    if (-not $script) { Write-Host "chiudi: chiudi-sessione.ps1 non e'' istanziato in $radice." -ForegroundColor Red; return }')
$righe.Add('    powershell -NoProfile -ExecutionPolicy Bypass -File $script @args')
$righe.Add('}')
$righe.Add($FINE)
$blocco = ($righe -join [Environment]::NewLine)

if ($Verifica) {
  Nota '' 'Gray'
  Nota '--- blocco che verrebbe scritto ---' 'Cyan'
  Write-Host $blocco
  Nota '' 'Gray'
  if (Test-Path -LiteralPath $Profilo) {
    $att = Get-Content -LiteralPath $Profilo -Raw
    if ($att -match [regex]::Escape($INIZIO)) { Nota 'Nel profilo esiste gia un blocco generato: verrebbe SOSTITUITO.' 'Yellow' }
    else { Nota 'Nel profilo non c e ancora un blocco generato: verrebbe AGGIUNTO in coda.' 'Yellow' }
    $fuori = @(Select-String -LiteralPath $Profilo -Pattern '^\s*function\s+(claude|codex)-account\d+' -ErrorAction SilentlyContinue |
      Where-Object { $true })
    if ($fuori.Count -gt 0) {
      Nota ("Attenzione: {0} definizioni di funzione esistono gia nel profilo." -f $fuori.Count) 'Yellow'
      Nota 'Quelle FUORI dal blocco generato non vengono rimosse e resterebbero a fare ombra.' 'Yellow'
      Nota 'Vanno cancellate a mano una volta sola, dopo la prima installazione.' 'Yellow'
    }
  }
  else { Nota 'Il profilo non esiste: verrebbe creato.' 'Yellow' }
  exit 0
}

# --- scrittura, difensiva ---------------------------------------------------
$cartella = Split-Path -Parent $Profilo
if ($cartella -and -not (Test-Path -LiteralPath $cartella)) { New-Item -ItemType Directory -Path $cartella -Force | Out-Null }

$attuale = ''
if (Test-Path -LiteralPath $Profilo) {
  $backup = "$Profilo.bak-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
  Copy-Item -LiteralPath $Profilo -Destination $backup -Force
  Nota ("Copia del profilo: {0}" -f $backup) 'DarkGray'
  $attuale = Get-Content -LiteralPath $Profilo -Raw
}

# Le definizioni precedenti, scritte a mano fuori dal blocco, farebbero ombra a
# quelle generate perche' in PowerShell vince l'ultima definita. Si rimuovono
# solo su richiesta esplicita, e solo quelle con i nomi che questo script
# rigenera: nient'altro viene toccato. Il profilo e' gia' stato copiato sopra.
if ($RimuoviVecchie -and $attuale) {
  # Si toglie il blocco generato dal testo, si ripuliscono le definizioni sparse
  # in cio' che resta, e si rimette il blocco dov'era. Cosi' la rimozione non
  # puo' mai intaccare il blocco stesso, che verrebbe comunque rigenerato sotto
  # ma la cui perdita renderebbe l'operazione non idempotente.
  $segna = "@@BLOCCO-GENERATO@@"
  $pat = [regex]::Escape($INIZIO) + '.*?' + [regex]::Escape($FINE)
  $m = [regex]::Match($attuale, $pat, 'Singleline')
  $bloccoVecchio = if ($m.Success) { $m.Value } else { '' }
  $testo = if ($m.Success) { [regex]::Replace($attuale, $pat, $segna, 'Singleline') } else { $attuale }

  $out = New-Object System.Collections.Generic.List[string]
  $salta = $false
  $tolte = 0
  foreach ($l in ($testo -split "`r?`n")) {
    if (-not $salta -and $l -match '^\s*function\s+(claude|codex)-account\d+\s*\{') { $salta = $true; $tolte++; continue }
    if ($salta) { if ($l -match '^\s*\}\s*$') { $salta = $false }; continue }
    $out.Add($l)
  }

  $testo = ($out -join [Environment]::NewLine)
  if ($m.Success) { $testo = $testo.Replace($segna, $bloccoVecchio) }
  $attuale = $testo
  if ($tolte -gt 0) { Nota ("Rimosse {0} definizioni precedenti fuori dal blocco." -f $tolte) 'Green' }
  else { Nota 'Nessuna definizione sparsa da rimuovere.' 'DarkGray' }
}

if ($attuale -match [regex]::Escape($INIZIO)) {
  $pattern = [regex]::Escape($INIZIO) + '.*?' + [regex]::Escape($FINE)
  $nuovo = [regex]::Replace($attuale, $pattern, [System.Text.RegularExpressions.MatchEvaluator] { param($m) $blocco }, 'Singleline')
  Nota 'Blocco esistente sostituito.' 'Green'
}
else {
  $sep = if ($attuale -and -not $attuale.EndsWith([Environment]::NewLine)) { [Environment]::NewLine } else { '' }
  $nuovo = $attuale + $sep + [Environment]::NewLine + $blocco + [Environment]::NewLine
  Nota 'Blocco aggiunto in coda al profilo.' 'Green'
}

Set-Content -LiteralPath $Profilo -Value $nuovo -Encoding UTF8

# --- verifica: cio che doveva esserci c e -----------------------------------
$riletto = Get-Content -LiteralPath $Profilo -Raw
$mancanti = @()
foreach ($n in $claude) { if ($riletto -notmatch "function claude-account$n\b") { $mancanti += "claude-account$n" } }
foreach ($n in $codex) { if ($riletto -notmatch "function codex-account$n\b") { $mancanti += "codex-account$n" } }
if ($riletto -notmatch "function chiudi\b") { $mancanti += "chiudi" }
if ($mancanti.Count -gt 0) {
  Nota ("ANOMALIA: dopo la scrittura mancano {0}" -f ($mancanti -join ', ')) 'Red'
  exit 1
}

Nota '' 'Gray'
Nota ("Installati {0} comandi." -f ($claude.Count + $codex.Count + 1)) 'Green'
foreach ($n in $claude) { Nota ("  claude-account$n") 'White' }
foreach ($n in $codex) { Nota ("  codex-account$n") 'White' }
Nota '  chiudi' 'White'

# Le definizioni fuori dal blocco restano e farebbero ombra a quelle generate,
# perche' in PowerShell l'ultima definizione vince: vanno tolte a mano, una volta.
$fuori = @(Select-String -LiteralPath $Profilo -Pattern '^\s*function\s+(claude|codex)-account\d+')
$dentro = $claude.Count + $codex.Count
if ($fuori.Count -gt $dentro) {
  Nota '' 'Gray'
  Nota ("ATTENZIONE: nel profilo ci sono {0} definizioni ma il blocco ne genera {1}." -f $fuori.Count, $dentro) 'Yellow'
  Nota 'Le definizioni precedenti, fuori dal blocco, sono ancora li e in PowerShell' 'Yellow'
  Nota 'vince l ultima definita: vanno cancellate a mano, una volta sola.' 'Yellow'
}

Nota '' 'Gray'
Nota 'Per usarli subito nella sessione corrente: . $PROFILE' 'Cyan'
Nota '' 'Gray'
