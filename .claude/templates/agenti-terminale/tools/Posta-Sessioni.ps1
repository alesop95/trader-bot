# Punto comune ai launcher: nessun protocollo privato dei due agenti.
function Prepara-PostaSessioni([string]$Agente, [int]$Account, [string]$Progetto, [string]$Posta) {
  $tool = Join-Path $PSScriptRoot 'posta-sessioni.py'
  if (-not (Test-Path -LiteralPath $tool)) { throw "Manca la cassetta comune: $tool" }
  if (-not $Posta) { $Posta = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..\_notes\posta-sessioni')) }
  $Posta = [IO.Path]::GetFullPath($Posta)
  $nome = '{0}-account{1}-{2}' -f $Agente, $Account, ([guid]::NewGuid().ToString('N'))
  # Scopa le registrazioni che nessuno ha congedato, cioe' quelle delle sessioni cadute: senza
  # questa, un elenco di partecipanti vivi torna a riempirsi di morti e smette di dire chi c'e'.
  # La soglia e' deliberatamente larga, e il motivo e' un errore misurato il 2026-11-03: con 24 ore
  # la scopa ha congedato la registrazione di una sessione ancora viva, che stava scrivendo in quel
  # momento, perche' era aperta dal giorno prima. L'eta' della registrazione non misura la vitalita'
  # e non puo' misurarla: il meccanismo vero e' il congedo all'uscita, questa e' solo la rete sotto.
  # Una soglia larga sbaglia per eccesso di prudenza, cioe' lascia qualche morto in elenco; una
  # soglia stretta sbaglia togliendo dall'elenco chi c'e', che e' l'errore peggiore dei due.
  & python $tool --root $Posta congeda --inattivi-da 168 | Out-Null
  $registrazione = & python $tool --root $Posta registra --nome $nome --agente $Agente --progetto $Progetto
  if ($LASTEXITCODE -ne 0) { throw "Registrazione nella cassetta fallita: $registrazione" }
  $env:PROJECT_AGENT_MAILBOX_ROOT = $Posta
  $env:PROJECT_AGENT_MAILBOX_ID = $nome
  $env:PROJECT_AGENT_MAILBOX_TOOL = $tool
  $env:PROJECT_TEMPLATE_ROOT = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..'))
  # Stato in ingresso e lezioni in uscita, visibili a ogni avvio dei due agenti.
  $statoTemplate = Join-Path $env:PROJECT_TEMPLATE_ROOT '.claude/templates/tools/stato-template.py'
  if (Test-Path -LiteralPath $statoTemplate) {
    & python $statoTemplate --progetto $Progetto --template $env:PROJECT_TEMPLATE_ROOT | ForEach-Object { Write-Host $_ }
  }
  $lezioniTemplate = Join-Path $env:PROJECT_TEMPLATE_ROOT '.claude/templates/tools/lezioni-template.py'
  if (Test-Path -LiteralPath $lezioniTemplate) {
    & python $lezioniTemplate --radice $Progetto controlla | ForEach-Object { Write-Host $_ }
  }
  Write-Host "Posta comune = $Posta; partecipante $nome" -ForegroundColor Cyan
  Write-Host 'Gli agenti leggono la cassetta a inizio sessione e a ogni giro; nessuna notifica push.' -ForegroundColor DarkGray
  return $Posta
}

# Chiude la registrazione all'uscita del processo dell'agente. Va chiamata nel blocco finally del
# launcher, prima che le variabili d'ambiente vengano rimosse, perche' e' li' che vive l'identita'.
# Non fallisce mai la chiusura della sessione: un congedo mancato lascia una voce che la scopa per
# eta' chiudera' al prossimo avvio, mentre un'eccezione qui mangerebbe l'uscita dell'agente.
function Congeda-PostaSessioni() {
  if (-not $env:PROJECT_AGENT_MAILBOX_TOOL -or -not $env:PROJECT_AGENT_MAILBOX_ID) { return }
  if (-not $env:PROJECT_AGENT_MAILBOX_ROOT) { return }
  try {
    & python $env:PROJECT_AGENT_MAILBOX_TOOL --root $env:PROJECT_AGENT_MAILBOX_ROOT congeda --nome $env:PROJECT_AGENT_MAILBOX_ID | Out-Null
  } catch {
    Write-Host "Congedo dalla cassetta non riuscito: $_" -ForegroundColor DarkYellow
  }
}
