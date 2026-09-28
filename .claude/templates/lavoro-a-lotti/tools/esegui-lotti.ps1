<#
.SYNOPSIS
  Esegue un lavoro a lotti su tutto il registro, un lotto per sessione.

.DESCRIPTION
  PERCHE' TANTE SESSIONI BREVI E NON UNA LUNGA. Il costo per elemento CRESCE con
  la dimensione del lotto, perche' il contesto si accumula e la cache riletta con
  esso. Misurato su un caso reale: con lo stesso modello, 20.000 token per
  elemento su un lotto da 10 e 122.000 su uno da 24. Un lotto unico su tutto il
  corpus non e' quindi piu' economico di molti lotti brevi: e' molto peggio.

  Ogni invocazione di `codex exec` apre una sessione NUOVA, con contesto pulito.
  Il registro e' cio' che rende indolore l'azzeramento: la sessione successiva
  non deve sapere nulla della precedente, le basta leggere quali elementi sono
  ancora da fare.

  Lo script e' un ciclo attorno a quella idea, con le guardie che servono a non
  restare appesi.

  SPECIFICO DI UN AGENTE. Il registro e il presidio sono agnostici; questo
  esecutore no, perche' parla la riga di comando di Codex. Un altro agente
  richiede il proprio esecutore, che lavora sullo stesso registro.

.PARAMETER Registro
  Percorso del registro JSONL.

.PARAMETER Istruzioni
  File di testo con il mandato da dare all'agente a ogni lotto. Deve gia'
  contenere il vocabolario chiuso degli stati e la regola di durevolezza per
  elemento. Il numero di elementi viene sostituito al segnaposto {N}.

.PARAMETER Account
  Numero della radice Codex da usare.

.PARAMETER PerLotto
  Elementi per lotto. Default 25.

.PARAMETER MaxLotti
  Numero massimo di lotti. 0 = fino a esaurimento.

.PARAMETER Modello
  Modello da usare. Per una mappatura ripetitiva va scelto quello economico.

.PARAMETER Ragionamento
  Livello di ragionamento. Per un mandato meccanico, `low`.

.PARAMETER DryRun
  Stampa che cosa farebbe, senza eseguire nulla.

.EXAMPLE
  .\tools\esegui-lotti.ps1 -Registro _notes\registro.jsonl -Istruzioni _notes\mandato.txt -DryRun
.EXAMPLE
  .\tools\esegui-lotti.ps1 -Registro _notes\registro.jsonl -Istruzioni _notes\mandato.txt -Account 3

.NOTES
  Pacchetto: lavoro-a-lotti. Il presidio `registro.py stato` resta il modo di
  verificare l'esito: questo script guarda solo se il lavoro avanza.
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$Registro,
  [Parameter(Mandatory = $true)][string]$Istruzioni,
  [int]$Account = 3,
  [int]$PerLotto = 25,
  [int]$MaxLotti = 0,
  [string]$Modello = 'gpt-5.6-luna',
  [string]$Ragionamento = 'low',
  [string]$Progetto,
  [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Nota($t, $c) { Write-Host $t -ForegroundColor $c }

foreach ($f in @($Registro, $Istruzioni)) {
  if (-not (Test-Path -LiteralPath $f)) { Nota "MANCA $f. Interrotto." 'Red'; exit 1 }
}
$presidio = Join-Path $PSScriptRoot 'registro.py'
if (-not (Test-Path -LiteralPath $presidio)) { Nota "MANCA $presidio. Interrotto." 'Red'; exit 1 }

$radice = Join-Path $env:USERPROFILE ".codex-account$Account"
if (-not (Test-Path -LiteralPath $radice)) { Nota "MANCA la radice $radice. Interrotto." 'Red'; exit 1 }

function Residui {
  $out = & python $presidio stato $Registro --radice '.' 2>&1
  foreach ($r in $out) {
    if ($r -match 'residui reali\s+(\d+)') { return [int]$Matches[1] }
  }
  return -1
}

if (-not $Progetto) { $Progetto = (Get-Location).Path }
$Progetto = (Resolve-Path -LiteralPath $Progetto).Path

$mandato = Get-Content -LiteralPath $Istruzioni -Raw

Nota '' 'Gray'
Nota '=== esegui-lotti ===' 'Cyan'
Nota ("registro   {0}" -f $Registro) 'White'
Nota ("radice     {0}" -f $radice) 'White'
Nota ("modello    {0}  ragionamento {1}" -f $Modello, $Ragionamento) 'White'
Nota ("per lotto  {0}" -f $PerLotto) 'White'
Nota ("progetto   {0}" -f $Progetto) 'White'
if ($DryRun) { Nota 'Modo: A VUOTO, nessuna esecuzione.' 'Yellow' }

$env:CODEX_HOME = $radice
$lotto = 0
$precedenti = -1
$fermi = 0

while ($true) {
  $residui = Residui
  if ($residui -lt 0) { Nota 'Impossibile leggere i residui dal presidio. Interrotto.' 'Red'; break }
  if ($residui -eq 0) { Nota '' 'Gray'; Nota 'FINITO: nessun elemento residuo.' 'Green'; break }

  # GUARDIA: se un lotto non produce progresso, fermarsi invece di ripetere.
  # Un ciclo che rilancia su un ostacolo che non cambia brucia quota senza
  # avanzare, ed e' il modo in cui un'automazione diventa dannosa.
  if ($residui -eq $precedenti) {
    $fermi++
    if ($fermi -ge 2) {
      Nota '' 'Gray'
      Nota ("INTERROTTO: due lotti consecutivi senza progresso, restano {0} elementi." -f $residui) 'Red'
      Nota 'Esegui il presidio per capire che cosa blocca, prima di rilanciare.' 'Yellow'
      break
    }
  }
  else { $fermi = 0 }
  $precedenti = $residui

  $lotto++
  if ($MaxLotti -gt 0 -and $lotto -gt $MaxLotti) {
    Nota '' 'Gray'
    Nota ("Raggiunto il massimo di {0} lotti. Restano {1} elementi." -f $MaxLotti, $residui) 'Yellow'
    break
  }

  $n = [Math]::Min($PerLotto, $residui)
  $prompt = $mandato.Replace('{N}', [string]$n)

  Nota '' 'Gray'
  Nota ("--- lotto {0}: {1} elementi, {2} residui ---" -f $lotto, $n, $residui) 'Cyan'

  if ($DryRun) {
    Nota ('  [dry-run] codex exec -s workspace-write -C ' + $Progetto + ' -m ' + $Modello) 'DarkGray'
    Nota '  [dry-run] il mandato verrebbe passato con {N} sostituito.' 'DarkGray'
    if ($lotto -ge 3) { Nota '  [dry-run] mi fermo dopo tre lotti simulati.' 'Yellow'; break }
    $precedenti = -1
    continue
  }

  $inizio = Get-Date
  # Niente --ask-for-approval: `codex exec` non lo accetta, perche' in modalita'
  # non interattiva non puo' chiedere. O il comando passa nella sandbox o
  # fallisce, che e' esattamente il comportamento voluto per un lotto.
  # -C fissa la cartella di lavoro: senza, la sandbox avrebbe come perimetro la
  # cartella da cui capita di lanciare lo script.
  # Il mandato si passa da STDIN, non come argomento posizionale: `codex exec`
  # legge comunque stdin quando lo trova collegato, e in un host non interattivo
  # lo e' sempre. Passandolo come argomento l'agente restava in attesa di input
  # aggiuntivo dichiarando "Reading additional input from stdin".
  # ErrorActionPreference locale a Continue, e NIENTE 2>&1: in PowerShell 5.1
  # la redirezione dello stderr di un eseguibile nativo avvolge ogni riga in un
  # record di errore, e con la preferenza a Stop il ciclo termina su un semplice
  # messaggio informativo come "Reading prompt from stdin".
  $vecchiaPref = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  try {
    $prompt | & codex exec -s workspace-write -C $Progetto -m $Modello -c "model_reasoning_effort=`"$Ragionamento`"" |
      Select-Object -Last 3 | ForEach-Object { Nota ("  " + $_) 'DarkGray' }
  }
  finally { $ErrorActionPreference = $vecchiaPref }
  $durata = (Get-Date) - $inizio
  Nota ("  lotto concluso in {0:mm\:ss}" -f $durata) 'Green'
}

$env:CODEX_HOME = $null

Nota '' 'Gray'
Nota 'Verifica finale con il presidio:' 'Cyan'
Nota ("  python {0} stato {1} --radice ." -f $presidio, $Registro) 'White'
Nota '' 'Gray'
