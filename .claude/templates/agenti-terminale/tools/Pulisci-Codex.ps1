<#
.SYNOPSIS
  Azzera gli store di sessione di Codex CLI, preservando le credenziali.

.DESCRIPTION
  Codex non partiziona le sessioni per progetto: la cartella di lavoro sta
  DENTRO il file di rollout, non nel nome di una cartella. Una logica di
  preservazione basata sui nomi delle cartelle, presa da un altro agente, qui
  non corrisponderebbe a nulla, preserverebbe l'insieme vuoto e cancellerebbe
  tutto senza emettere errori. Per questo la selezione avviene leggendo la
  cartella di lavoro dentro ogni rollout, e per questo esistono le tre guardie.

  Gli store di questa macchina sono CINQUE, non tre, e i due che si dimenticano
  sono gli ultimi:
    1-3) le radici <PROFILO_UTENTE>\.codex-account<N>
      4) <PROFILO_UTENTE>\.codex, radice di default usata dall'app desktop
      5) <PROFILO_UTENTE>\Documents\Codex, dati delle attivita' fuori progetto,
         che sta FUORI da ogni CODEX_HOME e non e' isolato per account

  Le sessioni non si rimuovono cancellando file: sono indicizzate da
  thread_history_1.sqlite e state_5.sqlite, e togliere i file da sotto l'indice
  lo disallinea. Si usa il comando supportato `codex delete <uuid> --force`.

  Cosa NON viene mai toccato: auth.json, config.toml, skills\, plugins\.
  Il login sopravvive a ogni modo di esecuzione.

.PARAMETER Account
  Numeri delle radici da pulire. Default: 1, 2, 3.

.PARAMETER Lista
  SOLA LETTURA. Elenca le sessioni presenti con la loro cartella di lavoro,
  marcate KEEP o WIPE, e non rimuove nulla. Funziona anche a segnaposto non
  sostituito: e' il comando con cui si SCOPRE che cosa configurare.

.PARAMETER DryRun
  Stampa ogni rimozione che verrebbe fatta, senza farne nessuna.

.PARAMETER Tutto
  Azzera anche i database di stato, ignorando la preservazione. Da usare quando
  non si vuole conservare nessuna sessione.

.PARAMETER IncludiDefault
  Include anche <PROFILO_UTENTE>\.codex, la radice dell'app desktop. Esclusa per
  default perche' pulirla slogga dall'app e ne cancella lo stato; va fatto ad
  app chiusa.

.PARAMETER GiorniAttivita
  Giorni di dati da conservare in Documents\Codex. Default 0, cioe' tutto.

.PARAMETER Deroga
  Forza l'esecuzione quando la terza guardia rifiuta. Da usare solo se si vuole
  davvero un account in cui nulla e' preservato.

.EXAMPLE
  .\scripts\Pulisci-Codex.ps1 -Lista
.EXAMPLE
  .\scripts\Pulisci-Codex.ps1 -DryRun
.EXAMPLE
  .\scripts\Pulisci-Codex.ps1 -Account 1

.NOTES
  Scheda di riferimento: docs\10_CODEX_CLI_E_WORKSPACE_OPENAI.md, sezione 4.
  Invocato automaticamente da Avvia-Codex.ps1 all'uscita della sessione.
#>
[CmdletBinding()]
param(
  # Vuoto = scoperta automatica delle radici presenti. Un elenco fisso qui
  # significherebbe che una quarta radice creata domani resta fuori dalla
  # pulizia senza che nulla lo segnali.
  [int[]]$Account,
  [switch]$Lista,
  [switch]$DryRun,
  [switch]$Tutto,
  [switch]$IncludiDefault,
  [int]$GiorniAttivita = 0,
  [string[]]$Prefissi,
  [switch]$Deroga
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# =============================================================================
#  CONFIGURAZIONE SPECIFICA DELLA MACCHINA
#
#  Prefissi delle cartelle di lavoro da PRESERVARE. Una sessione la cui cartella
#  di lavoro comincia per uno di questi non viene rimossa.
#
#  Il segnaposto e' deliberatamente non funzionante. NON inventare questi valori:
#  si leggono, con `.\scripts\Pulisci-Codex.ps1 -Lista`, che funziona anche ora.
#  Sono specifici della macchina, uno per ogni radice su cui vivono i progetti.
#  Su Windows hanno la forma 'D:\' o 'E:\'; su un'altra macchina sarebbero altri,
#  e un insieme sbagliato non produce un errore ma un magazzino vuoto.
# =============================================================================
#  Compilati il 2026-09-21 su questa macchina, dopo averli LETTI con -Lista da
#  una sessione reale. Corrispondono alle due radici su cui vivono i progetti di
#  sviluppo, le stesse che il wipe di Claude preserva come slug 'D--' ed 'E--'.
#  Su un'altra macchina vanno riletti, non riusati.
$prefissiDaPreservare = @('D:\', 'E:\')

# Override a riga di comando, con -Prefissi. Serve per un uso occasionale su un
# insieme diverso, e soprattutto per poter COLLAUDARE la terza guardia: senza di
# esso l'unico modo di provarla sarebbe modificare il file, che e' il momento in
# cui una guardia smette di essere provata e diventa una dichiarazione.
if ($Prefissi -and $Prefissi.Count -gt 0) { $prefissiDaPreservare = $Prefissi }

$attivitaRoot = Join-Path $env:USERPROFILE 'Documents\Codex'
$logFile = Join-Path $env:USERPROFILE 'Documents\Codex\pulisci-codex.log'

# --- utilita' ---------------------------------------------------------------

function Scrivi($testo, $colore) {
  Write-Host $testo -ForegroundColor $colore
  try { Add-Content -LiteralPath $logFile -Value ("{0}  {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $testo) -ErrorAction SilentlyContinue } catch { }
}

function Stop-Pulizia($motivo) {
  Scrivi "INTERROTTO: $motivo" 'Red'
  Scrivi 'Nessuna rimozione eseguita.' 'Red'
  exit 1
}

function Test-Configurato {
  if (-not $prefissiDaPreservare) { return $false }
  foreach ($p in $prefissiDaPreservare) {
    if ($p -and $p -notlike '*KEEP_PREFIXES*') { return $true }
  }
  return $false
}

function Test-Preservare($cartella) {
  if (-not $cartella) { return $true }   # ignoto = si preserva, mai si rimuove
  foreach ($p in $prefissiDaPreservare) {
    if ($p -and $p -notlike '*KEEP_PREFIXES*' -and $cartella.StartsWith($p, 'OrdinalIgnoreCase')) { return $true }
  }
  return $false
}

# Legge la cartella di lavoro dentro un rollout. Il campo `cwd` compare nei primi
# record di metadati; si leggono poche righe invece del file intero perche' un
# rollout lungo pesa e la risposta sta sempre in testa.
function Get-CartellaLavoro($file) {
  try {
    $righe = Get-Content -LiteralPath $file -TotalCount 40 -ErrorAction Stop
  }
  catch { return $null }
  foreach ($riga in $righe) {
    if ($riga -notmatch '"cwd"') { continue }
    try {
      $o = $riga | ConvertFrom-Json -ErrorAction Stop
    }
    catch { continue }
    $trovato = Find-Cwd $o
    if ($trovato) { return $trovato }
  }
  return $null
}

function Find-Cwd($nodo) {
  if ($null -eq $nodo) { return $null }
  if ($nodo -is [string]) { return $null }
  if ($nodo -is [System.Collections.IEnumerable]) {
    foreach ($v in $nodo) { $r = Find-Cwd $v; if ($r) { return $r } }
    return $null
  }
  if ($nodo.PSObject -and $nodo.PSObject.Properties) {
    foreach ($p in $nodo.PSObject.Properties) {
      if ($p.Name -eq 'cwd' -and $p.Value -is [string] -and $p.Value) { return $p.Value }
      if ($p.Value -and -not ($p.Value -is [string])) { $r = Find-Cwd $p.Value; if ($r) { return $r } }
    }
  }
  return $null
}

function Get-Sessioni($radice) {
  $dir = Join-Path $radice 'sessions'
  if (-not (Test-Path -LiteralPath $dir)) { return @() }
  $out = @()
  foreach ($f in (Get-ChildItem -LiteralPath $dir -Recurse -File -Filter 'rollout-*.jsonl' -ErrorAction SilentlyContinue)) {
    $id = $null
    if ($f.BaseName -match '([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})') { $id = $Matches[1] }
    $out += [pscustomobject]@{
      Id       = $id
      Cartella = (Get-CartellaLavoro $f.FullName)
      File     = $f.FullName
    }
  }
  return $out
}

function Remove-Percorso($percorso, $etichetta) {
  if (-not (Test-Path -LiteralPath $percorso)) { return }
  if ($DryRun) { Scrivi "    [dry-run] rimuoverei $etichetta : $percorso" 'DarkGray'; return }
  Remove-Item -LiteralPath $percorso -Recurse -Force -ErrorAction SilentlyContinue
  Scrivi "    rimosso $etichetta" 'DarkGray'
}

# --- radici da trattare -----------------------------------------------------

# Scoperta automatica: si enumerano le radici realmente presenti nel profilo.
if (-not $Account -or $Account.Count -eq 0) {
  $Account = @(Get-ChildItem -LiteralPath $env:USERPROFILE -Directory -Filter '.codex-account*' -ErrorAction SilentlyContinue |
    ForEach-Object { if ($_.Name -match '(\d+)$') { [int]$Matches[1] } } | Sort-Object -Unique)
  if (-not $Account -or $Account.Count -eq 0) { $Account = @(1, 2, 3) }
}

$radici = @()
foreach ($n in $Account) {
  $radici += [pscustomobject]@{ Nome = ".codex-account$n"; Percorso = (Join-Path $env:USERPROFILE ".codex-account$n") }
}
if ($IncludiDefault) {
  $radici += [pscustomobject]@{ Nome = '.codex (app desktop)'; Percorso = (Join-Path $env:USERPROFILE '.codex') }
}

Scrivi '' 'Gray'
Scrivi '=== Pulisci-Codex ===' 'Cyan'
if ($Lista) { Scrivi 'Modo: SOLA LETTURA. Nessuna rimozione.' 'Yellow' }
elseif ($DryRun) { Scrivi 'Modo: A VUOTO. Nessuna rimozione.' 'Yellow' }

# --- raccolta e GUARDIE -----------------------------------------------------

$tutteLeSessioni = @()
$radiciValide = @()

foreach ($r in $radici) {
  # GUARDIA 1: la radice esiste e assomiglia a una radice di Codex.
  # Senza questa, un segnaposto non sostituito o un percorso sbagliato si
  # tradurrebbero in rimozioni altrove.
  if (-not (Test-Path -LiteralPath $r.Percorso)) {
    Scrivi ("  {0}: inesistente, saltata" -f $r.Nome) 'DarkGray'
    continue
  }
  $paiaRadice = (Test-Path -LiteralPath (Join-Path $r.Percorso 'config.toml')) -or (Test-Path -LiteralPath (Join-Path $r.Percorso 'sessions'))
  if (-not $paiaRadice) {
    Scrivi ("  {0}: non sembra una radice Codex (manca config.toml e sessions\), saltata" -f $r.Nome) 'Yellow'
    continue
  }
  $radiciValide += $r
  foreach ($s in (Get-Sessioni $r.Percorso)) {
    $tutteLeSessioni += [pscustomobject]@{
      Radice   = $r.Nome
      Percorso = $r.Percorso
      Id       = $s.Id
      Cartella = $s.Cartella
      File     = $s.File
    }
  }
}

if ($radiciValide.Count -eq 0) { Stop-Pulizia 'nessuna radice Codex valida fra quelle indicate.' }

$configurato = Test-Configurato

# --- modo SOLA LETTURA ------------------------------------------------------

if ($Lista) {
  Scrivi '' 'Gray'
  Scrivi ("Sessioni presenti: {0}" -f $tutteLeSessioni.Count) 'White'
  if ($tutteLeSessioni.Count -eq 0) {
    Scrivi '  (nessuna)' 'DarkGray'
  }
  else {
    foreach ($s in $tutteLeSessioni) {
      $tag = 'WIPE'
      if (Test-Preservare $s.Cartella) { $tag = 'KEEP' }
      $c = $s.Cartella
      if (-not $c) { $c = '(cartella di lavoro non determinata -> preservata per prudenza)' }
      Scrivi ("  [{0}] {1}  {2}" -f $tag, $s.Radice, $c) 'White'
    }
  }
  Scrivi '' 'Gray'
  if ($configurato) {
    Scrivi ("prefissi attuali: {0}" -f ($prefissiDaPreservare -join '  ')) 'White'
  }
  else {
    Scrivi 'prefissiDaPreservare NON e'' ancora compilato: finche'' resta cosi'' lo script' 'Yellow'
    Scrivi 'rifiuta di rimuovere. Scegli i prefissi dalle cartelle di lavoro qui sopra,' 'Yellow'
    Scrivi 'uno per ogni radice di sviluppo da preservare, e sostituiscili nello script.' 'Yellow'
  }
  Scrivi '' 'Gray'
  Scrivi ("Dati attivita' fuori progetto: {0}" -f $attivitaRoot) 'White'
  if (Test-Path -LiteralPath $attivitaRoot) {
    $g = @(Get-ChildItem -LiteralPath $attivitaRoot -Directory -ErrorAction SilentlyContinue)
    Scrivi ("  {0} cartelle per data" -f $g.Count) 'DarkGray'
  }
  else { Scrivi '  (inesistente)' 'DarkGray' }
  exit 0
}

# GUARDIA 2: i prefissi non sono piu' il segnaposto.
# Un insieme vuoto significherebbe non preservare niente.
if (-not $configurato -and -not $Tutto) {
  Stop-Pulizia 'i prefissi da preservare sono ancora il segnaposto. Esegui con -Lista per scoprire quali impostare, oppure usa -Tutto se vuoi davvero non preservare nulla.'
}

# GUARDIA 3: se esistono sessioni e NESSUNA corrisponde ai prefissi, la
# configurazione appartiene a un'altra macchina. E' il caso che non somiglia a
# un errore: lo script farebbe esattamente cio' che gli e' stato chiesto,
# cancellando tutto, senza emettere alcun avviso.
if ($configurato -and -not $Tutto -and $tutteLeSessioni.Count -gt 0) {
  $corrispondenti = @($tutteLeSessioni | Where-Object { Test-Preservare $_.Cartella })
  if ($corrispondenti.Count -eq 0) {
    if (-not $Deroga) {
      Stop-Pulizia 'esistono sessioni ma nessuna corrisponde ai prefissi configurati: la configurazione sembra di un''altra macchina. Verifica con -Lista, oppure forza con -Deroga se vuoi davvero non preservare nulla.'
    }
    Scrivi 'ATTENZIONE: nessuna sessione corrisponde ai prefissi, si procede per -Deroga.' 'Yellow'
  }
}

# --- rimozione --------------------------------------------------------------

foreach ($r in $radiciValide) {
  Scrivi '' 'Gray'
  Scrivi ("--- {0}" -f $r.Nome) 'Cyan'

  $sessioniRadice = @($tutteLeSessioni | Where-Object { $_.Percorso -eq $r.Percorso })
  $daRimuovere = @($sessioniRadice | Where-Object { $Tutto -or -not (Test-Preservare $_.Cartella) })
  Scrivi ("  sessioni: {0} totali, {1} da rimuovere" -f $sessioniRadice.Count, $daRimuovere.Count) 'White'

  # Le sessioni si rimuovono con il comando supportato, non cancellando file:
  # sono indicizzate da thread_history_1.sqlite e state_5.sqlite.
  $env:CODEX_HOME = $r.Percorso
  foreach ($s in $daRimuovere) {
    if (-not $s.Id) {
      Scrivi ("    saltata, identificativo non ricavabile: {0}" -f $s.File) 'Yellow'
      continue
    }
    if ($DryRun) { Scrivi ("    [dry-run] codex delete {0} --force" -f $s.Id) 'DarkGray'; continue }
    & codex delete $s.Id --force 2>&1 | Out-Null
    Scrivi ("    eliminata sessione {0}" -f $s.Id) 'DarkGray'
  }

  # Store effimeri, sempre.
  Remove-Percorso (Join-Path $r.Percorso 'history.jsonl') 'history.jsonl'
  Remove-Percorso (Join-Path $r.Percorso 'log') 'log\'

  # Database di stato: solo in modo totale, perche' rimuoverli disallineerebbe
  # l'indice delle sessioni che si e' scelto di preservare.
  if ($Tutto) {
    foreach ($db in @('state_5', 'logs_2', 'goals_1', 'memories_1', 'memories_v2_1', 'queue_1', 'thread_history_1')) {
      foreach ($est in @('.sqlite', '.sqlite-shm', '.sqlite-wal')) {
        Remove-Percorso (Join-Path $r.Percorso ($db + $est)) ($db + $est)
      }
    }
    Remove-Percorso (Join-Path $r.Percorso 'sessions') 'sessions\'
    Remove-Percorso (Join-Path $r.Percorso 'tmp') 'tmp\'
  }

  # Verifica che cio' che deve sopravvivere sia sopravvissuto. Un wipe che porta
  # via le credenziali e' indistinguibile da uno corretto finche' non si riapre
  # la sessione successiva.
  if (-not $DryRun) {
    foreach ($tenere in @('auth.json', 'config.toml')) {
      $p = Join-Path $r.Percorso $tenere
      if (-not (Test-Path -LiteralPath $p)) {
        if ($tenere -eq 'auth.json') { Scrivi ("    nota: {0} non presente (radice non autenticata)" -f $tenere) 'DarkGray' }
        else { Scrivi ("    ANOMALIA: {0} non c'e' piu'" -f $tenere) 'Red' }
      }
    }
  }
}
$env:CODEX_HOME = $null

# --- quinto store: dati delle attivita' fuori progetto -----------------------
# Sta FUORI da ogni CODEX_HOME e non e' isolato per account: tutte le radici e
# l'app desktop vi scrivono nello stesso posto. Una pulizia limitata alle radici
# lo lascia intatto, ed e' il motivo per cui e' trattato qui esplicitamente.

Scrivi '' 'Gray'
Scrivi ("--- attivita' fuori progetto: {0}" -f $attivitaRoot) 'Cyan'
if (-not (Test-Path -LiteralPath $attivitaRoot)) {
  Scrivi '  (inesistente)' 'DarkGray'
}
else {
  $soglia = (Get-Date).Date.AddDays(-$GiorniAttivita)
  $cartelle = @(Get-ChildItem -LiteralPath $attivitaRoot -Directory -ErrorAction SilentlyContinue)
  $rimosse = 0
  foreach ($c in $cartelle) {
    # Due accorgimenti che PowerShell 5.1 pretende e che falliscono solo a tempo
    # di esecuzione, cioe' durante una pulizia vera: il provider dev'essere
    # InvariantCulture e non $null, e la variabile passata per riferimento
    # dev'essere gia' tipizzata [datetime], altrimenti l'overload non si risolve.
    [datetime]$data = [datetime]::MinValue
    if ([datetime]::TryParseExact($c.Name, 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::None, [ref]$data)) {
      if ($GiorniAttivita -gt 0 -and $data -ge $soglia) { continue }
    }
    Remove-Percorso $c.FullName ("attivita' " + $c.Name)
    $rimosse++
  }
  Scrivi ("  {0} cartelle per data, {1} trattate" -f $cartelle.Count, $rimosse) 'White'
}

Scrivi '' 'Gray'
Scrivi 'Fatto.' 'Green'
Scrivi '' 'Gray'
