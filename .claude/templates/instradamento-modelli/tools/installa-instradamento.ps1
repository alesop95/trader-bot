<#
.SYNOPSIS
  Registra la mod instradamento-modelli in una o piu' radici (account) locali di
  Claude Code, e vi depone la configurazione di partenza.

.DESCRIPTION
  La mod vive nel template e NON si copia dentro le radici: ogni account la
  carica dal percorso del template tramite env.CLAUDE_CODE_PLUGIN_DIRS nel
  proprio settings.json. Due copie divergerebbero in silenzio, che e' il difetto
  che il resto del sistema esiste per evitare.

  Cio' che invece e' per account, ed e' il punto di questo script, e' la
  CONFIGURAZIONE: ogni radice ha il proprio instradamento-modelli.json, quindi
  un account puo' instradare e un altro no, con tabelle diverse, sulla stessa
  macchina e sullo stesso progetto.

  Alla prima installazione la configurazione parte in modo `osserva`, che
  dichiara in trascrizione che cosa instraderebbe senza instradare niente: e' la
  linea di partenza da misurare prima di spostare qualunque traffico.

  Cosa NON viene mai toccato: .credentials.json, mcp.json, e ogni chiave del
  settings.json diversa da env.CLAUDE_CODE_PLUGIN_DIRS. Una configurazione gia'
  presente non viene sovrascritta senza -Forza.

.PARAMETER Account
  Numeri delle radici da servire, cioe' %USERPROFILE%\.claude-account<N>.
  Default: 1, 2, 3.

.PARAMETER IncludiDefault
  Serve anche la radice di default %USERPROFILE%\.claude.

.PARAMETER Mod
  Cartella della mod. Default: la cartella `mod` di questo pacchetto.

.PARAMETER Radice
  Percorso esplicito di una radice da servire, al posto dei numeri di -Account.
  Serve alle prove, che non possono scrivere nella home vera, e alle
  installazioni dove la radice non segue la convenzione .claude-account<N>.

.PARAMETER Verifica
  Sola lettura: non scrive nulla, stampa il quadro di ogni radice. La domanda
  «questa mod e' registrata?» la risolve merge-instradamento-settings.js in modo
  --stato, cioe' confrontando percorsi normalizzati dopo JSON.parse. Cercare il
  percorso nel testo grezzo del settings.json e' sbagliato su Windows, dove il
  JSON raddoppia le barre rovesciate: il percorso scritto con barre singole non
  si trova mai e una mod regolarmente registrata risulta assente. Per questo
  -Verifica richiede Node come il resto dello script.

.PARAMETER Rimuovi
  Toglie la registrazione dal settings.json. La configurazione resta sul disco,
  perche' e' lavoro dell'utente: si cancella a mano.

.PARAMETER Forza
  Riscrive la configurazione di una radice dalla copia di riferimento.

.EXAMPLE
  .\installa-instradamento.ps1 -Verifica
.EXAMPLE
  .\installa-instradamento.ps1 -Account 2
.EXAMPLE
  .\installa-instradamento.ps1 -Account 1,2,3 -IncludiDefault

.NOTES
  Dopo l'installazione, una sessione gia' aperta non vede la mod: si apre una
  sessione nuova, oppure si lancia /reload-plugins. Per controllare che sia
  attiva: /plugin mostra una riga "1 mod active - instradamento-modelli".
#>
[CmdletBinding()]
param(
  [int[]]$Account = @(1, 2, 3),
  [switch]$IncludiDefault,
  [string]$Mod,
  [string[]]$Radice,
  [switch]$Verifica,
  [switch]$Rimuovi,
  [switch]$Forza
)

$ErrorActionPreference = 'Stop'

$pacchetto = Split-Path -Parent $PSScriptRoot
if (-not $Mod) { $Mod = Join-Path $pacchetto 'mod' }
$riferimento = Join-Path $pacchetto 'instradamento-modelli.riferimento.json'
$fusione = Join-Path $PSScriptRoot 'merge-instradamento-settings.js'

function Esci($messaggio) {
  Write-Host "ERRORE: $messaggio" -ForegroundColor Red
  exit 1
}

if (-not (Test-Path (Join-Path $Mod '.claude-plugin\plugin.json'))) {
  Esci "la cartella della mod non contiene .claude-plugin\plugin.json: $Mod"
}
if (-not (Test-Path $riferimento)) { Esci "manca la copia di riferimento: $riferimento" }
if (-not (Test-Path $fusione)) { Esci "manca lo script di fusione: $fusione" }
$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) {
  if ($Verifica) { Esci "serve Node.js anche per la verifica, e non e' nel PATH: senza, la risposta sarebbe un'ipotesi sul testo del file" }
  Esci "serve Node.js per scrivere il settings.json in sicurezza, e non e' nel PATH"
}

$radici = @()
if ($Radice) {
  $radici += $Radice
} else {
  foreach ($n in $Account) { $radici += (Join-Path $env:USERPROFILE ".claude-account$n") }
  if ($IncludiDefault) { $radici += (Join-Path $env:USERPROFILE '.claude') }
}

Write-Host ''
Write-Host "Mod: $Mod"
Write-Host ''

foreach ($radice in $radici) {
  $nome = Split-Path $radice -Leaf
  if (-not (Test-Path $radice)) {
    Write-Host "$nome : saltata, la radice non esiste" -ForegroundColor DarkYellow
    continue
  }

  $impostazioni = Join-Path $radice 'settings.json'
  $configurazione = Join-Path $radice 'instradamento-modelli.json'

  if ($Verifica) {
    $registrata = $false
    $modo = '(nessuna configurazione)'
    if (Test-Path $impostazioni) {
      $risposta = & node $fusione $impostazioni $Mod --stato 2>&1
      if ($LASTEXITCODE -eq 0) { $registrata = $true }
      elseif ($LASTEXITCODE -ne 3) { Esci "la verifica di $impostazioni e' fallita: $risposta" }
    }
    if (Test-Path $configurazione) {
      try {
        $modo = (Get-Content -Raw -Path $configurazione | ConvertFrom-Json).modo
      } catch {
        $modo = '(JSON non valido)'
      }
    }
    $stato = if ($registrata) { 'registrata' } else { 'NON registrata' }
    Write-Host "$nome : mod $stato, modo $modo"
    continue
  }

  if ($Rimuovi) {
    & node $fusione $impostazioni $Mod --rimuovi
    if ($LASTEXITCODE -ne 0) { Esci "fusione fallita su $impostazioni" }
    Write-Host "$nome : la configurazione $configurazione resta sul disco, cancellala a mano se non serve" -ForegroundColor DarkGray
    continue
  }

  if ((Test-Path $configurazione) -and (-not $Forza)) {
    Write-Host "$nome : configurazione gia' presente, lasciata com'e'" -ForegroundColor DarkGray
  } else {
    Copy-Item -Path $riferimento -Destination $configurazione -Force
    Write-Host "$nome : configurazione scritta in modo osserva" -ForegroundColor Green
  }

  & node $fusione $impostazioni $Mod
  if ($LASTEXITCODE -ne 0) { Esci "fusione fallita su $impostazioni" }
  Write-Host ''
}

if (-not $Verifica -and -not $Rimuovi) {
  Write-Host 'Fatto. Apri una sessione nuova (o lancia /reload-plugins) e poi /instradamento.'
  Write-Host 'Si misura la linea di partenza in modo osserva, e solo dopo si passa a instrada.'
}
