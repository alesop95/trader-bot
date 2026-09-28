<#
.SYNOPSIS
  Installa o riallinea le radici multi-account di Claude Code, con il wipe di
  fine sessione. Gemello di Installa-Codex.ps1.

.DESCRIPTION
  I due agenti da terminale di questa macchina si installano in modo diverso per
  una ragione tecnica, e la differenza vale la pena conoscerla.

  Claude Code ha un hook SessionEnd: e' un comando registrato nel settings.json
  dell'account che punta a un file, quindi lo script di wipe DEVE esistere come
  copia dentro ogni radice. Codex non ha un hook di ciclo di vita, si avvia da
  un wrapper, e quindi non ha bisogno di copie: i suoi script restano nel
  repository. Da qui l'asimmetria, che senza questo script si traduceva in una
  installazione a mano, lunga e con un passaggio pericoloso.

  FONTE DI VERITA': le copie di riferimento restano nel TEMPLATE, non qui.
  Duplicarle in questo repository creerebbe la divergenza silenziosa che tutto
  il resto del progetto esiste per evitare. Lo script legge dal template e si
  ferma dichiarandolo se non lo trova.

  Cosa NON viene mai toccato: .credentials.json, mcp.json, le chiavi esistenti
  del settings.json diverse da `hooks.SessionEnd` e `autoMemoryEnabled`.

.PARAMETER Account
  Numeri delle radici da installare. Default: 1, 2, 3.

.PARAMETER Template
  Radice del repository template che contiene templates\tools\.

.PARAMETER Prefissi
  Prefissi degli slug da PRESERVARE nel wipe, es. 'D--','E--'. Se omesso, lo
  script li ricava da una installazione gia' presente su questa macchina; se non
  ne trova, si ferma e spiega come scoprirli. NON vanno indovinati: un insieme
  sbagliato non produce un errore, preserva l'insieme vuoto e cancella tutto.

.PARAMETER IncludiDefault
  Include anche la home di default %USERPROFILE%\.claude, che su questa macchina
  e' coperta dal wipe al pari delle altre.

.PARAMETER Verifica
  Sola lettura: non scrive nulla, stampa il quadro.

.PARAMETER Forza
  Riscrive gli hook gia' presenti dalla copia di riferimento del template.

.EXAMPLE
  .\scripts\Installa-Claude.ps1 -Verifica
.EXAMPLE
  .\scripts\Installa-Claude.ps1 -Prefissi 'D--','E--'
.EXAMPLE
  .\scripts\Installa-Claude.ps1 -Forza -Template 'E:\template-claude-developing'

.NOTES
  Riferimento: docs\10_CODEX_CLI_E_WORKSPACE_OPENAI.md (simmetria fra i due
  agenti) e la sezione sull'auto-memory del PROJECT-SYSTEM del template.
#>
[CmdletBinding()]
param(
  [int[]]$Account = @(1, 2, 3),
  [string]$Template,
  [string[]]$Prefissi,

  # Dichiara che NESSUNA trascrizione va preservata. Serve perche' un insieme
  # vuoto e' ambiguo: puo' significare "non preservare niente" oppure "i prefissi
  # non sono stati determinati", e le due cose hanno esiti opposti. La guardia 2
  # rifiuta il secondo caso, e questo interruttore rende il primo una scelta
  # dichiarata invece che un silenzio. E' la scelta corretta per default: le
  # cartelle sotto 'projects' contengono verbali di conversazioni, non memoria di
  # progetto, che vive versionata dentro il progetto.
  [switch]$NienteDaPreservare,

  # Prefissi di PERCORSO per le voci 'projects' di .claude.json, che sono
  # IMPOSTAZIONI e non conversazioni. Se omesso si derivano dagli slug, come
  # prima. Va passato quando si usa -NienteDaPreservare e si vogliono comunque
  # conservare permessi e dialogo di fiducia dei propri progetti.
  [string[]]$PrefissiImpostazioni,

  [switch]$IncludiDefault,
  [switch]$Verifica,
  [switch]$Forza
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Scrivi($testo, $colore) { Write-Host $testo -ForegroundColor $colore }

Scrivi '' 'Gray'

# Il template si DERIVA dalla posizione di questo script, che vive in
# <template>/.claude/templates/agenti-terminale/tools/. Cablare un percorso
# assoluto renderebbe il pacchetto inservibile su un'altra macchina, cioe'
# esattamente cio' che un template non deve essere. Il parametro resta, per i
# casi in cui il template stia altrove.
if (-not $Template) {
  $Template = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
}

Scrivi '=== Installa-Claude ===' 'Cyan'
if ($Verifica) { Scrivi 'Modo: SOLA LETTURA, nessuna modifica.' 'Yellow' }

# --- GUARDIA 1: il template esiste e contiene gli strumenti -----------------
$toolsTemplate = Join-Path $Template '.claude\templates\tools'
$srcWipe = Join-Path $toolsTemplate 'session-end-wipe.ps1'
$srcScrub = Join-Path $toolsTemplate 'scrub-claude-json.js'
foreach ($f in @($srcWipe, $srcScrub)) {
  if (-not (Test-Path -LiteralPath $f)) {
    Scrivi "MANCA la copia di riferimento: $f" 'Red'
    Scrivi 'Le copie di riferimento vivono nel template, non in questo repository.' 'Yellow'
    Scrivi 'Clona il template, oppure indica il percorso giusto con -Template. Interrotto.' 'Red'
    exit 1
  }
}
Scrivi ("Template        {0}" -f $Template) 'Green'

# --- GUARDIA 2: i prefissi non si indovinano --------------------------------
# Se non sono stati passati, si leggono da una installazione gia' presente.
if ($NienteDaPreservare) {
  $Prefissi = @()
  Scrivi 'Prefissi        nessuno: NESSUNA trascrizione viene preservata (scelta dichiarata)' 'Green'
  if ($PrefissiImpostazioni -and $PrefissiImpostazioni.Count -gt 0) {
    Scrivi ("Impostazioni    {0}  (voci di .claude.json conservate per questi percorsi)" -f ($PrefissiImpostazioni -join ', ')) 'Green'
  }
  else {
    Scrivi 'Impostazioni    nessuna: anche permessi e dialogo di fiducia verranno rimossi' 'Yellow'
  }
}
elseif (-not $Prefissi -or $Prefissi.Count -eq 0) {
  foreach ($n in $Account) {
    $candidato = Join-Path $env:USERPROFILE ".claude-account$n\hooks\session-end-wipe.ps1"
    if (-not (Test-Path -LiteralPath $candidato)) { continue }
    $riga = Select-String -LiteralPath $candidato -Pattern '^\s*\$keepPrefixes\s*=\s*@\((.*?)\)' -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $riga) { continue }
    $dentro = $riga.Matches[0].Groups[1].Value
    if ($dentro -match '<.*>') { continue }
    $trovati = @([regex]::Matches($dentro, "'([^']+)'") | ForEach-Object { $_.Groups[1].Value })
    if ($trovati.Count -gt 0) {
      $Prefissi = $trovati
      Scrivi ("Prefissi        {0}  (letti da .claude-account{1})" -f ($Prefissi -join ', '), $n) 'Green'
      break
    }
  }
}
else {
  Scrivi ("Prefissi        {0}  (passati a riga di comando)" -f ($Prefissi -join ', ')) 'Green'
}

if (-not $NienteDaPreservare -and (-not $Prefissi -or $Prefissi.Count -eq 0)) {
  Scrivi '' 'Gray'
  Scrivi 'PREFISSI NON DETERMINATI. Non li invento, e non devi indovinarli tu.' 'Red'
  Scrivi 'Sono specifici della macchina, uno per ogni radice su cui vivono i progetti.' 'Yellow'
  Scrivi 'Su Windows nascono dalla lettera del disco e hanno la forma D-- oppure E--.' 'Yellow'
  Scrivi 'Si scoprono elencando gli slug presenti in un magazzino gia popolato:' 'Yellow'
  Scrivi '  powershell -File <radice-account>\hooks\session-end-wipe.ps1 -List' 'White'
  Scrivi 'Poi rilancia passandoli con -Prefissi.' 'Yellow'
  exit 1
}

# --- radici da trattare -----------------------------------------------------
$radici = @()
foreach ($n in $Account) {
  $radici += [pscustomobject]@{ Nome = ".claude-account$n"; Percorso = (Join-Path $env:USERPROFILE ".claude-account$n") }
}
if ($IncludiDefault) {
  $radici += [pscustomobject]@{ Nome = '.claude (default)'; Percorso = (Join-Path $env:USERPROFILE '.claude') }
}

$node = Get-Command node -ErrorAction SilentlyContinue
$merge = Join-Path $PSScriptRoot 'merge-claude-settings.js'

$quadro = @()
foreach ($r in $radici) {
  $azioni = @()
  $hooksDir = Join-Path $r.Percorso 'hooks'
  $dstWipe = Join-Path $hooksDir 'session-end-wipe.ps1'
  $dstScrub = Join-Path $hooksDir 'scrub-claude-json.js'
  $settings = Join-Path $r.Percorso 'settings.json'

  if (-not (Test-Path -LiteralPath $r.Percorso)) {
    if ($Verifica) { $azioni += 'radice da creare' }
    else { New-Item -ItemType Directory -Path $r.Percorso -Force | Out-Null; $azioni += 'radice creata' }
  }
  if (-not $Verifica -and -not (Test-Path -LiteralPath $hooksDir)) {
    New-Item -ItemType Directory -Path $hooksDir -Force | Out-Null
  }

  # --- lo script di wipe, con i segnaposto sostituiti -----------------------
  $serve = (-not (Test-Path -LiteralPath $dstWipe)) -or $Forza
  if ($serve) {
    if ($Verifica) { $azioni += 'wipe da installare' }
    else {
      # Sostituzione RIGA PER RIGA, non con -replace su tutto il file.
      # Motivo, appurato sul campo: nella stringa di sostituzione di -replace i
      # caratteri `$` sono riferimenti a gruppi di cattura, non testo letterale.
      # Righe che contengono variabili PowerShell, come queste, escono mangiate
      # e il file installato risulta malformato senza che nulla lo segnali.
      $elenco = ($Prefissi | ForEach-Object { "'" + $_ + "'" }) -join ', '
      $righe = Get-Content -LiteralPath $srcWipe
      $nuove = New-Object System.Collections.Generic.List[string]
      foreach ($riga in $righe) {
        $t = $riga.TrimStart()
        if ($t.StartsWith('$base = ') -and $riga.Contains('<CLAUDE_CONFIG_DIR>')) {
          $nuove.Add('$base = ' + [char]39 + $r.Percorso + [char]39 + '   # <-- specifico di questo account')
        }
        elseif ($t.StartsWith('$keepPrefixes = ') -and $riga.Contains('<KEEP_PREFIXES>')) {
          if ($NienteDaPreservare) {
            $nuove.Add('$keepPrefixes = @()       # nessuna trascrizione si preserva: la memoria di progetto vive nel progetto')
          }
          else {
            $nuove.Add('$keepPrefixes = @(' + $elenco + ')       # dischi con progetti di sviluppo su questa macchina')
          }
        }
        elseif ($t.StartsWith('$keepPathPrefixes = ') -and $riga.Contains('<KEEP_PATH_PREFIXES>')) {
          # Le voci 'projects' di .claude.json sono IMPOSTAZIONI, non conversazioni:
          # si governano a parte, altrimenti svuotare le trascrizioni farebbe
          # ricomparire il dialogo di fiducia a ogni progetto a ogni sessione.
          if ($PrefissiImpostazioni -and $PrefissiImpostazioni.Count -gt 0) {
            $elencoImp = ($PrefissiImpostazioni | ForEach-Object { [char]39 + $_ + [char]39 }) -join ', '
            $nuove.Add('$keepPathPrefixes = @(' + $elencoImp + ')   # permessi e fiducia conservati per questi percorsi')
          }
          elseif ($NienteDaPreservare) {
            $nuove.Add('$keepPathPrefixes = @()   # nulla conservato, nemmeno permessi e dialogo di fiducia')
          }
          else {
            $nuove.Add('$keepPathPrefixes = @($keepPrefixes | ForEach-Object { $_.Substring(0,1) + ' + [char]39 + ':' + [char]39 + ' })')
          }
        }
        elseif ($t.StartsWith('$allowEmptyKeep = ') -and $NienteDaPreservare) {
          # Il template ha gia' la deroga esplicita all'insieme vuoto: si usa quella
          # invece di introdurne una seconda. Copre entrambe le guardie, quella sul
          # segnaposto mai compilato e quella su "nessuno slug corrisponde".
          $nuove.Add('$allowEmptyKeep = $true   # scelta dichiarata: nessuna trascrizione si preserva')
        }
        else { $nuove.Add($riga) }
      }
      Set-Content -LiteralPath $dstWipe -Value $nuove -Encoding UTF8
      $azioni += 'wipe installato'
    }
  }

  # --- il companion, copiato tale e quale ----------------------------------
  $serveScrub = (-not (Test-Path -LiteralPath $dstScrub)) -or $Forza
  if ($serveScrub) {
    if ($Verifica) { $azioni += 'companion da copiare' }
    else { Copy-Item -LiteralPath $srcScrub -Destination $dstScrub -Force; $azioni += 'companion copiato' }
  }

  # --- GUARDIA 3: nessun segnaposto deve essere sopravvissuto ---------------
  # E' il modo in cui questa installazione sbaglia senza dare errore: uno
  # script con i segnaposto intatti si rifiuta di girare, ma uno con una
  # sostituzione parziale e' molto peggio.
  # Si guardano le sole righe di ASSEGNAMENTO, non i commenti: l'intestazione
  # del template cita i nomi dei segnaposto per spiegare quali sostituire, e
  # quelle citazioni restano li' legittimamente. Una guardia che contasse anche
  # quelle darebbe un allarme a ogni installazione riuscita, e un allarme che
  # suona sempre smette di essere letto.
  $residui = 0
  if ((-not $Verifica) -and (Test-Path -LiteralPath $dstWipe)) {
    $residui = @(Get-Content -LiteralPath $dstWipe | Where-Object {
        $t = $_.TrimStart()
        ($t.StartsWith('$base = ') -or $t.StartsWith('$keepPrefixes = ') -or $t.StartsWith('$keepPathPrefixes = ')) -and
        ($_ -match '<CLAUDE_CONFIG_DIR>|<KEEP_PREFIXES>|<KEEP_PATH_PREFIXES>')
      }).Count
    if ($residui -gt 0) {
      Scrivi ("  {0}: ANOMALIA, {1} segnaposto non sostituiti in session-end-wipe.ps1" -f $r.Nome, $residui) 'Red'
      Scrivi '  Il formato del template potrebbe essere cambiato. Verifica a mano prima di usarlo.' 'Red'
    }
  }

  # --- settings.json, fusione difensiva via Node ---------------------------
  # Si passa a Node il solo PERCORSO, e il comando lo compone lui. Motivo,
  # appurato sul campo: PowerShell 5.1 mangia le virgolette annidate quando passa
  # un argomento a un eseguibile nativo, e l'hook finiva registrato con il
  # percorso non quotato. Su un percorso con spazi non avrebbe funzionato, e il
  # difetto sarebbe emerso solo alla prima chiusura di sessione.
  $hookOk = $false
  if (Test-Path -LiteralPath $settings) {
    $hookOk = @(Select-String -LiteralPath $settings -Pattern 'SessionEnd' -ErrorAction SilentlyContinue).Count -gt 0
  }
  if ((-not $hookOk) -or $Forza) {
    if ($Verifica) { $azioni += 'settings.json da aggiornare' }
    elseif (-not $node) { Scrivi ("  {0}: node non disponibile, settings.json non aggiornato" -f $r.Nome) 'Yellow' }
    elseif (-not (Test-Path -LiteralPath $merge)) { Scrivi ("  {0}: manca merge-claude-settings.js" -f $r.Nome) 'Yellow' }
    else {
      & node $merge $settings $dstWipe | Out-Null
      if ($LASTEXITCODE -eq 0) { $azioni += 'settings.json aggiornato' }
      else { Scrivi ("  {0}: fusione di settings.json FALLITA, file lasciato intatto" -f $r.Nome) 'Red' }
    }
  }

  if ($azioni.Count -eq 0) { $azioni += 'gia a posto' }

  $quadro += [pscustomobject]@{
    Radice = $r.Nome
    Wipe   = (Test-Path -LiteralPath $dstWipe)
    Hook   = ((Test-Path -LiteralPath $settings) -and (@(Select-String -LiteralPath $settings -Pattern 'SessionEnd' -ErrorAction SilentlyContinue).Count -gt 0))
    Login  = $(if (Test-Path -LiteralPath (Join-Path $r.Percorso '.credentials.json')) { 'presente' } else { 'DA FARE' })
    Azione = ($azioni -join ' + ')
  }
}

Scrivi '' 'Gray'
$quadro | Format-Table -AutoSize

$daLoggare = @($quadro | Where-Object { $_.Login -eq 'DA FARE' })
if ($daLoggare.Count -gt 0) {
  Scrivi 'Login ancora da fare (uno alla volta, da una finestra browser pulita):' 'Yellow'
  foreach ($r in $daLoggare) {
    Scrivi ("  `$env:CLAUDE_CONFIG_DIR = '{0}\{1}'; claude" -f $env:USERPROFILE, $r.Radice) 'White'
  }
}
else { Scrivi 'Tutte le radici hanno credenziali.' 'Green' }

Scrivi '' 'Gray'
Scrivi 'Promemoria: mcp.json e .credentials.json non sono toccati da questo script.' 'DarkGray'
Scrivi 'I server MCP di account vanno ricreati a mano su una macchina nuova.' 'DarkGray'
Scrivi '' 'Gray'
