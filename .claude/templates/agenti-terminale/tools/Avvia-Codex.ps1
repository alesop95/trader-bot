<#
.SYNOPSIS
  Avvia Codex CLI su una radice di account isolata, e ripulisce all'uscita.

.DESCRIPTION
  Codex tiene tutto il proprio stato persistente sotto la radice indicata da
  CODEX_HOME. Se quella variabile non e' impostata, ricade SILENZIOSAMENTE sulla
  radice di default del profilo utente: il comando riesce, stampa "Successfully
  logged in", e le credenziali finiscono nel posto sbagliato.

  Questo e' il motivo per cui il comando non va digitato a mano. E' successo
  davvero durante l'installazione del 2026-09-21: l'assegnamento della variabile
  con la sintassi di un'altra shell e' fallito, l'errore stampato sembrava una
  riga scollegata, e il login e' andato a buon fine sulla radice di default.

  Lo script imposta la radice, verifica che esista e sia configurata, esegue
  Codex, e al ritorno del processo invoca la pulizia se e' installata.

  NON e' un hook, e la ragione e' misurata, non di gusto. Codex un hook di fine
  sessione CE L'HA, da codex-cli 0.155.1: si chiama SessionEnd, si configura in
  <CODEX_HOME>\hooks.json, scatta davvero, e riceve gia' pronti session_id e
  cwd della sessione. Non basta lo stesso, per due limiti indipendenti e
  ciascuno sufficiente da solo.

  PRIMO. Non scatta su `codex exec`, quindi non copre NULLA del lavoro non
  interattivo. E' il caso del pacchetto lavoro-a-lotti, che invoca esattamente
  quel comando, ed e' anche il caso che produce piu' sessioni da rimuovere: una
  giornata a mano ne lascia tre o quattro, un corpus a lotti ne lascia decine.

  SECONDO. Non puo' rimuovere la sessione che si sta chiudendo. SessionEnd
  scatta "right before a session ends", cioe' quando la sessione e' ancora
  aperta e di proprieta' del processo che la sta chiudendo, e `codex delete` su
  di essa esce con codice 1 e "Error: failed to delete session".

  Verificato il 2026-09-22 nello stesso terminale: la sessione
  01a0c9c7-50ea-7530-84ea-754c1420aba2 non e' stata rimossa dall'hook e lo e'
  stata un secondo dopo dal blocco finally qui sotto. Stesso identificativo,
  stessa radice, stesso comando sotto. Cambia solo il momento.

  Ne segue la regola strutturale: la pulizia deve avvenire quando il processo e'
  GIA' USCITO, e nessun hook interno puo' trovarsi in quel momento. E' il
  motivo per cui questo wrapper esiste e non e' sostituibile.

.PARAMETER Account
  Numero della radice, che corrisponde a <PROFILO_UTENTE>\.codex-account<N>.

.PARAMETER Stato
  Sola lettura: non avvia Codex, stampa lo stato di login e la diagnosi.

.PARAMETER NoPulizia
  Salta la pulizia all'uscita. Da usare quando si vuole conservare la sessione
  per un resume.

.PARAMETER Resto
  Argomenti passati a Codex cosi' come sono.

.EXAMPLE
  .\scripts\Avvia-Codex.ps1 -Account 1
.EXAMPLE
  .\scripts\Avvia-Codex.ps1 -Account 1 -Stato
.EXAMPLE
  .\scripts\Avvia-Codex.ps1 -Account 2 -Resto 'login'

.NOTES
  Scheda di riferimento: docs\10_CODEX_CLI_E_WORKSPACE_OPENAI.md
  Sola lettura sul sistema tranne per cio' che scrive Codex stesso.
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [ValidateRange(1, 99)]
  [int]$Account,

  [string]$Progetto,

  [switch]$Stato,

  [switch]$NoPulizia,

  # Conserva le sessioni invece di azzerarle. Per default la pulizia e' TOTALE,
  # perche' una trascrizione che sopravvive nella radice dell'account e' memoria
  # fuori dal progetto: la memoria di un progetto vive dentro il progetto,
  # versionata. Vedi la sezione "Che cosa si preserva nel wipe" del README.
  [switch]$ConservaSessioni,

  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$Resto
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$radice = Join-Path $env:USERPROFILE ".codex-account$Account"

# --- Guardia 1: la radice esiste ed e' configurata -------------------------
# Senza questa, un numero di account sbagliato creerebbe una radice nuova e
# vuota, e Codex chiederebbe un login che nessuno si aspetta.
if (-not (Test-Path -LiteralPath $radice)) {
  Write-Host "La radice $radice non esiste." -ForegroundColor Red
  Write-Host "Creala e mettici il config.toml di riferimento (scheda 10, sez. 3.4), poi rilancia." -ForegroundColor Yellow
  exit 1
}
$configToml = Join-Path $radice 'config.toml'
if (-not (Test-Path -LiteralPath $configToml)) {
  Write-Host "La radice $radice esiste ma non ha config.toml." -ForegroundColor Red
  Write-Host "Senza di esso Codex gira con i default, non con il perimetro deciso. Vedi scheda 10, sez. 3.4." -ForegroundColor Yellow
  exit 1
}

# --- Guardia 2: codex e' raggiungibile -------------------------------------
$codex = Get-Command codex -ErrorAction SilentlyContinue
if (-not $codex) {
  Write-Host "codex non e' nel PATH. Installalo con: npm install -g @openai/codex" -ForegroundColor Red
  exit 1
}

$env:CODEX_HOME = $radice
Write-Host "CODEX_HOME = $radice" -ForegroundColor Cyan

# --- Modo di sola lettura ---------------------------------------------------
if ($Stato) {
  & codex login status
  & codex doctor --summary
  exit 0
}

# --- Guardia 3: la cartella di lavoro -------------------------------------
# Senza una cartella di lavoro esplicita Codex parte nella home dell'utente, e
# con sandbox_mode = "workspace-write" il perimetro scrivibile diventa l'INTERA
# home. E' molto piu' largo di quanto chiunque intenda, e non lo segnala nessuno.
# C'e' anche un secondo effetto, osservato il 2026-09-21: partendo dalla home,
# Codex scambia la radice di default `~\.codex` per una configurazione di
# progetto, perche' si trova dentro la cartella corrente.
$argomenti = @()
if ($Progetto) {
  if (-not (Test-Path -LiteralPath $Progetto)) {
    Write-Host "La cartella di progetto $Progetto non esiste." -ForegroundColor Red
    exit 1
  }
  $Progetto = (Resolve-Path -LiteralPath $Progetto).Path
  $argomenti += @('-C', $Progetto)
  Write-Host "Progetto    = $Progetto" -ForegroundColor Cyan
}
elseif (-not $Resto -or $Resto.Count -eq 0) {
  Write-Host '' -ForegroundColor Gray
  Write-Host 'ATTENZIONE: nessuna cartella di progetto indicata.' -ForegroundColor Yellow
  Write-Host 'La sessione partirebbe nella home dell''utente, e con sandbox workspace-write' -ForegroundColor Yellow
  Write-Host 'il perimetro scrivibile sarebbe l''intera home. Indica il progetto:' -ForegroundColor Yellow
  Write-Host ("  .\scripts\Avvia-Codex.ps1 -Account {0} -Progetto <percorso>" -f $Account) -ForegroundColor White
  exit 1
}

# --- Esecuzione -------------------------------------------------------------
try {
  $tutti = @($argomenti) + @($Resto | Where-Object { $_ })
  if ($tutti.Count -gt 0) {
    & codex @tutti
  }
  else {
    & codex
  }
}
finally {
  # Il finally copre anche Ctrl+C e un'uscita per errore, che sono i casi in cui
  # una pulizia messa in coda al blocco try non verrebbe mai eseguita.
  if (-not $NoPulizia) {
    $pulizia = Join-Path $PSScriptRoot 'Pulisci-Codex.ps1'
    if (Test-Path -LiteralPath $pulizia) {
      Write-Host 'Pulizia degli store di sessione...' -ForegroundColor Cyan
      if ($ConservaSessioni) { & $pulizia -Account $Account }
      else { & $pulizia -Account $Account -Tutto }
    }
    else {
      # Il percorso cercato va STAMPATO, non solo il fatto che manchi: la causa
      # osservata e' una finestra che aveva caricato il profilo prima che gli
      # script cambiassero posizione, e le sue funzioni puntavano alla vecchia.
      # Senza il percorso, il messaggio non distingue "file assente" da
      # "sto guardando nel posto sbagliato", che sono due diagnosi opposte.
      Write-Host ("Pulisci-Codex.ps1 non trovato in: {0}" -f $pulizia) -ForegroundColor DarkYellow
      Write-Host 'Nessuna pulizia eseguita. Se il percorso sopra non e'' quello atteso,' -ForegroundColor DarkYellow
      Write-Host 'questa finestra ha un profilo vecchio: esegui . $PROFILE oppure aprine una nuova.' -ForegroundColor DarkYellow
    }
  }
}
