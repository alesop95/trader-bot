<#
.SYNOPSIS
Porta allo stato corrente del template tutti i progetti istanziati da esso, e
tiene il registro di quali lo sono.

.DESCRIPTION
Il template evolve come progetto a se stante. Ogni volta che avanza, questo
script ne fa una passata sui progetti che ne portano la struttura, cioe su ogni
cartella sotto le radici indicate che contiene .claude/PROJECT-SYSTEM.md, senza
conoscerne i nomi in anticipo. Per ciascuno usa allinea-dal-template.py, che
decide file per file dalla storia git del template se la copia locale e intatta,
adattata o da fondere, e quindi non spende un modello linguistico.

La corsa ha tre fasi.

1. Guardie e prima misura, in sola lettura, progetto per progetto.

2. Consenso. Una riga che un file non ha in nessuna versione storica del
   template, ma che compare identica nello stesso file di almeno -Consenso
   progetti diversi, viene da una versione del template anteriore alla sua
   storia git e non da un singolo progetto. Le righe cosi riconosciute si passano
   allo strumento, che a quel punto aggiorna come SUPERATO una copia la cui sola
   differenza sono righe di quel tipo. Il consenso si calcola sui progetti
   trovati in questa corsa: con -Solo su pochi progetti vale di meno.

3. Seconda misura con il consenso e, con -Applica, scrittura dove tutte le
   guardie passano, seguita dalla verifica del risultato.

Guardie prima di cominciare: git e python presenti; template repository git con
.claude/PROJECT-SYSTEM.md; .claude del template senza modifiche non committate,
perche lo strumento legge solo la storia committata e una modifica locale non si
propagherebbe (con -Applica e un arresto, a vuoto un avviso); _notes/ del
template ignorato da git; una sola corsa per volta, con un file di blocco che
porta il PID e che si riprende da solo se il processo che lo aveva preso non
esiste piu.

Esiti per progetto:
  non-git              la cartella non e un repository
  albero-secondario    worktree aggiuntivo: la memoria versionata descrive la
                       branch, si allinea dall'albero principale (-IncludiAlberi
                       per forzare). Saltato per costruzione
  clone-del-template   condivide il commit radice con il template. Saltato
  operazione-in-corso  merge, rebase, cherry-pick o revert a meta
  head-staccato        nessuna branch in uscita
  escluso              elencato in _notes/allineamento/esclusi.txt del template,
                       per decisione del proprietario. Saltato finche non si toglie
  albero-sporco        modifiche non committate: si misura ma non si scrive, cosi
                       l'allineamento non si mescola a lavoro in corso
  errore-strumento     lo strumento non ha potuto misurare (codice 2)
  conflitti            modifiche locali che non si fondono da sole: a mano
  da-allineare         pronto; con -Applica diventa applicato
  allineato            niente da fare rispetto al commit corrente del template
  incompleto           scritto, ma la seconda misura trova ancora file da trattare
  fuori-perimetro      scritto, ma e cambiato un file fuori da .claude/, tools/,
                       docs/ e CLAUDE.md: niente si annulla da solo, decide la persona

Solo a verifica passata si scrive nel progetto .claude/allineamento-template.json,
che dichiara a quale commit e a quale albero .claude del template la struttura
del progetto corrisponde.

Le righe di innesco delle skill con RIFERIMENTO.md mancanti nel CLAUDE.md del
progetto sono un esito azionabile, INNESCO, e con -Applica lo strumento le scrive
prendendole da templates/CLAUDE.md: e il solo punto in cui l'allineamento tocca
CLAUDE.md, e solo per aggiungere righe. Un file che il progetto ha risolto a mano
si registra con allinea-dal-template.py --risolto <percorso> e resta ADATTATO
finche il template non lo cambia di nuovo.

Avvisi, che non bloccano: skill con RIFERIMENTO.md presenti ma non nominate come
skill nel CLAUDE.md, se l'innesco non e stato scritto; carico degli instruction
file oltre la soglia secondo misura-istruzioni.py.

Il registro vive in _notes/allineamento/registro.json del template, ignorato da
git perche contiene percorsi di progetti; ogni corsa lascia accanto log, rapporti
JSON e righe del consenso. Commit e push restano manuali, progetto per progetto;
memoria e conflitti veri si chiudono con una sessione nel progetto.

Codici di uscita: 0 tutto allineato o applicato, 1 qualche progetto da guardare,
2 guardia iniziale fallita.

.EXAMPLE
.\allinea-tutti.ps1
.EXAMPLE
.\allinea-tutti.ps1 -Applica
.EXAMPLE
.\allinea-tutti.ps1 -Radici D:\ -Escludi nome-a -Applica
#>
param(
  [string[]]$Radici = @('D:\', 'E:\'),
  [string]$Template = '',
  [switch]$Applica,
  [string[]]$Solo = @(),
  [string[]]$Escludi = @(),
  [int]$Profondita = 0,
  [int]$Consenso = 3,
  [switch]$IncludiAlberi,
  [switch]$ConsentiTemplateSporco
)
Set-StrictMode -Version 2
$ErrorActionPreference = 'Continue'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
$utf8 = New-Object System.Text.UTF8Encoding $false

function Dividi([string[]]$v) { @($v | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ }) }
$Solo = Dividi $Solo; $Escludi = Dividi $Escludi; $Radici = Dividi $Radici

function Esci-Guardia([string]$m) { Write-Host "GUARDIA: $m"; exit 2 }
# Non si chiama Git: in PowerShell una funzione con quel nome copre git.exe e
# richiamerebbe se stessa all'infinito.
function Invoca-Git([string]$repo) {
  $out = & git -C $repo @args 2>$null
  return $out
}

# --- guardie iniziali ---------------------------------------------------------
foreach ($c in 'git', 'python') { if (-not (Get-Command $c -ErrorAction SilentlyContinue)) { Esci-Guardia "$c non e sul PATH" } }
if (-not $Template) { $Template = Join-Path $PSScriptRoot '..\..\..' }
if (-not (Test-Path -LiteralPath $Template)) { Esci-Guardia "template non trovato: $Template" }
$tpl = (Resolve-Path -LiteralPath $Template).Path.TrimEnd('\')
if (-not (Test-Path -LiteralPath (Join-Path $tpl '.claude\PROJECT-SYSTEM.md'))) { Esci-Guardia "$tpl non ha .claude\PROJECT-SYSTEM.md: non e il template" }
$tplHead = Invoca-Git $tpl rev-parse HEAD
if ($LASTEXITCODE -ne 0 -or -not $tplHead) { Esci-Guardia "$tpl non e un repository git con almeno un commit" }
$tplAlbero = Invoca-Git $tpl rev-parse 'HEAD:.claude'
$tplRadici = @(Invoca-Git $tpl rev-list --max-parents=0 HEAD)
$tplData = Invoca-Git $tpl log -1 --format=%cs
$tplSporco = @(Invoca-Git $tpl status --porcelain -- .claude)
if ($tplSporco.Count -gt 0) {
  $m = "il .claude del template ha $($tplSporco.Count) modifiche non committate, che non si propagherebbero: committarle prima"
  if ($Applica -and -not $ConsentiTemplateSporco) { Esci-Guardia $m } else { Write-Host "AVVISO: $m"; Write-Host '' }
}
$strumento = Join-Path $tpl '.claude\templates\tools\allinea-dal-template.py'
$misura = Join-Path $tpl '.claude\templates\tools\misura-istruzioni.py'
if (-not (Test-Path -LiteralPath $strumento)) { Esci-Guardia "manca $strumento" }
if ($Consenso -lt 2) { Esci-Guardia '-Consenso deve essere almeno 2: una riga di un solo progetto e del progetto' }

$base = Join-Path $tpl '_notes\allineamento'
$null = & git -C $tpl check-ignore -q '_notes/allineamento/x' 2>$null
if ($LASTEXITCODE -ne 0) { Esci-Guardia "_notes/ del template non e ignorato da git: il registro non puo stare li" }
New-Item -ItemType Directory -Force -Path $base | Out-Null

$blocco = Join-Path $base '.in-corso'
if (Test-Path -LiteralPath $blocco) {
  $pid0 = (Get-Content -LiteralPath $blocco -Raw -ErrorAction SilentlyContinue) -as [int]
  if ($pid0 -and (Get-Process -Id $pid0 -ErrorAction SilentlyContinue)) { Esci-Guardia "un'altra corsa e in atto (PID $pid0)" }
  Write-Host "AVVISO: blocco lasciato da una corsa interrotta (PID $pid0, non piu attivo): ripreso"
  Remove-Item -LiteralPath $blocco -Force
}
try { [System.IO.File]::WriteAllText($blocco, "$PID", $utf8) } catch { Esci-Guardia "impossibile creare ${blocco}" }

$corsa = Get-Date -Format 'yyyyMMdd-HHmmss'
$dirCorsa = Join-Path $base "corse\$corsa"
New-Item -ItemType Directory -Force -Path $dirCorsa | Out-Null
$fileRegistro = Join-Path $base 'registro.json'
$fileLog = Join-Path $dirCorsa 'corsa.log'
$fileComuni = Join-Path $dirCorsa 'righe-comuni.json'

function Log([string]$riga) { Write-Host $riga; [System.IO.File]::AppendAllText($fileLog, $riga + "`r`n", $utf8) }

$AZIONABILI = 'CONFLITTO', 'SUPERATO', 'MERGE', 'VECCHIO', 'NUOVO', 'SPOSTATO', 'RIMOSSO', 'INNESCO'
function Leggi-Json([string]$f) { Get-Content -LiteralPath $f -Raw -Encoding UTF8 | ConvertFrom-Json }
function Conta($esiti) {
  $c = @{}; foreach ($k in $AZIONABILI + 'ADATTATO', 'LOCALE', 'UGUALE') { $c[$k] = 0 }
  foreach ($e in $esiti) { $c[$e.esito] = 1 + $c[$e.esito] }
  $c['azionabili'] = ($AZIONABILI | ForEach-Object { $c[$_] } | Measure-Object -Sum).Sum
  return $c
}
function Misura([string]$prj, [string]$json, [switch]$Scrivi) {
  $a = @($strumento, '--template', $tpl, '--progetto', $prj, '--json', $json, '--innesco')
  if (Test-Path -LiteralPath $fileComuni) { $a += '--righe-comuni', $fileComuni }
  if ($Scrivi) { $a += '--applica', '--rimuovi' }
  $out = & python @a 2>&1
  $codice = $LASTEXITCODE
  [System.IO.File]::AppendAllText($fileLog, "--- $prj" + $(if ($Scrivi) { ' (applica)' } else { '' }) + "`r`n" + ($out | Out-String) + "`r`n", $utf8)
  return $codice
}

# Prove interne degli strumenti che l'allineamento ha appena riscritto.
#
# Perche' esiste: le verifiche gia' presenti dicono che i file scritti sono quelli attesi e che
# nessuno sta fuori dal perimetro, cioe' guardano *dove* si e' scritto. Nessuna guarda *se il
# codice scritto gira*. Un rapporto pulito e un git diff pulito non lo dimostrano, e su una
# passata che tocca decine di progetti nessuno lo verifica a mano: il caso che questo passo
# copre e' un aggiornamento o una fusione a tre vie che lascia un file sintatticamente valido e
# funzionalmente rotto, che e' precisamente cio' che nessuno guarda dopo una passata riuscita.
#
# Che cosa NON copre, e va detto perche' credere che copra piu' di quanto copre e' peggio che
# non averlo. Il difetto che ha motivato questo passo, il 2026-09-28, era di un'altra specie:
# due strumenti si fermavano con ValueError quando il bersaglio stava su un'unita' diversa dalla
# radice, e il secondo solo sul ramo di scrittura. Verificato invece di supposto: la prova
# interna di quello strumento **passa anche sulla versione rotta**, perche' esercita l'analisi
# del testo e non la gestione dei percorsi. Una prova interna copre cio' che il suo autore ha
# pensato di coprire, e un presupposto sull'ambiente non e' fra quelle cose quasi mai. Questo
# passo distingue quindi uno strumento che non gira da uno che gira: e' meno di quanto
# servirebbe e molto piu' di niente.
#
# Si provano i soli strumenti che l'allineamento ha toccato, letti dal rapporto *prima* della
# scrittura, e fra quelli i soli che una prova interna la dichiarano: cercare il nome
# dell'argomento nel sorgente e' deterministico, mentre lanciarlo alla cieca su una copia locale
# che non ce l'ha produrrebbe un fallimento che non e' un fallimento. Per la stessa ragione un
# argomento rifiutato da argparse si legge come assenza di prova e non come difetto.
function Prove-Strumenti([string]$prj, $esitiPrima) {
  $falliti = @(); $provati = 0
  $tocchi = @($esitiPrima | Where-Object { $_.file -like 'tools/*.py' -and ($AZIONABILI -contains $_.esito) })
  foreach ($e in $tocchi) {
    $f = Join-Path $prj ($e.file -replace '/', '\')
    if (-not (Test-Path -LiteralPath $f)) { continue }
    $src = Get-Content -LiteralPath $f -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
    $flag = $null
    if ($src -match '--self-test') { $flag = '--self-test' } elseif ($src -match '--autotest') { $flag = '--autotest' }
    if (-not $flag) { continue }
    $out = & python $f $flag 2>&1
    $codice = $LASTEXITCODE
    $testo = ($out | Out-String)
    [System.IO.File]::AppendAllText($fileLog, "--- prova interna $($e.file) $flag (uscita $codice)`r`n" + $testo + "`r`n", $utf8)
    if ($codice -eq 0) { $provati++ }
    elseif ($testo -match 'unrecognized arguments|invalid choice|not recognized') { }
    else { $falliti += $e.file }
  }
  return [pscustomobject]@{ provati = $provati; falliti = $falliti }
}

# Progetti esclusi dalla passata per decisione del proprietario, finche non la ritira: una
# riga per percorso, con il motivo dopo il cancelletto. Vive in _notes/ del template perche
# i percorsi sono della macchina, come il registro, e non si versiona.
$fileEsclusi = Join-Path $base 'esclusi.txt'
$esclusi = @{}
if (Test-Path -LiteralPath $fileEsclusi) {
  foreach ($r in (Get-Content -LiteralPath $fileEsclusi -Encoding UTF8)) {
    $t = $r.Trim()
    if (-not $t -or $t.StartsWith('#')) { continue }
    $parti = $t -split '#', 2
    $percorso = $parti[0].Trim().TrimEnd([char]92, [char]47).Replace([string][char]47, [string][char]92)
    $motivo = if ($parti.Count -gt 1) { $parti[1].Trim() } else { 'senza motivo' }
    $esclusi[$percorso.ToLowerInvariant()] = $motivo
  }
}

$registro = @{}
if (Test-Path -LiteralPath $fileRegistro) {
  try { (Leggi-Json $fileRegistro).PSObject.Properties | ForEach-Object { $registro[$_.Name] = $_.Value } }
  catch { Write-Host 'AVVISO: registro illeggibile, se ne ricomincia uno nuovo' }
}

$esito = 2
try {
  Log "template $tpl  commit $($tplHead.Substring(0,7)) del $tplData  albero .claude $($tplAlbero.Substring(0,7))"
  Log ("modo: " + $(if ($Applica) { 'applica' } else { 'a vuoto' }) + "   radici: " + ($Radici -join ' ') + "   consenso: $Consenso progetti")
  Log ''

  # --- scoperta ---------------------------------------------------------------
  $trovati = foreach ($r in $Radici) {
    if (-not (Test-Path -LiteralPath $r)) { Log "AVVISO: radice assente $r"; continue }
    $gci = @{ LiteralPath = $r; Directory = $true; ErrorAction = 'SilentlyContinue' }
    if ($Profondita -gt 0) { $gci['Recurse'] = $true; $gci['Depth'] = $Profondita }
    Get-ChildItem @gci |
      Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName '.claude\PROJECT-SYSTEM.md') } |
      Where-Object { $_.FullName.TrimEnd('\') -ne $tpl } |
      Where-Object { $_.FullName -notmatch '\\\.claude\\' } |
      Where-Object { -not $Solo -or $Solo -contains $_.Name } |
      Where-Object { $Escludi -notcontains $_.Name }
  }
  $trovati = @($trovati | Sort-Object FullName -Unique)
  if (-not $trovati) { Log 'nessun progetto istanziato trovato'; $esito = 0; return }

  # --- fase 1: guardie e prima misura -----------------------------------------
  $progetti = foreach ($p in $trovati) {
    $prj = $p.FullName.TrimEnd('\')
    $o = [pscustomobject]@{ nome = $p.Name; percorso = $prj; slug = ($prj -replace '[:\\/]+', '--').Trim('-'); stato = $null; sporco = $false; c = $null; avvisi = @() }
    $dotgit = Join-Path $prj '.git'
    if ($esclusi.ContainsKey($prj.ToLowerInvariant())) { $o.stato = 'escluso'; $o.avvisi += 'escluso: ' + $esclusi[$prj.ToLowerInvariant()] }
    elseif (-not (Test-Path -LiteralPath $dotgit)) { $o.stato = 'non-git' }
    elseif ((Test-Path -LiteralPath $dotgit -PathType Leaf) -and -not $IncludiAlberi) { $o.stato = 'albero-secondario' }
    else {
      $radiciPrj = @(Invoca-Git $prj rev-list --max-parents=0 HEAD)
      if ($radiciPrj | Where-Object { $tplRadici -contains $_ }) { $o.stato = 'clone-del-template' }
      elseif (@('MERGE_HEAD', 'rebase-merge', 'rebase-apply', 'CHERRY_PICK_HEAD', 'REVERT_HEAD') | Where-Object { Test-Path -LiteralPath (Join-Path $prj (Invoca-Git $prj rev-parse --git-path $_)) }) { $o.stato = 'operazione-in-corso' }
      else {
        $null = Invoca-Git $prj symbolic-ref -q HEAD
        if ($LASTEXITCODE -ne 0) { $o.stato = 'head-staccato' }
      }
    }
    if (-not $o.stato) {
      $o.sporco = @(Invoca-Git $prj status --porcelain).Count -gt 0
      if ((Misura $prj (Join-Path $dirCorsa "$($o.slug).1.json")) -ge 2) { $o.stato = 'errore-strumento' }
    }
    $o
  }

  # --- fase 2: consenso fra progetti ------------------------------------------
  $conteggio = @{}; $testi = @{}
  foreach ($o in $progetti | Where-Object { -not $_.stato }) {
    foreach ($e in (Leggi-Json (Join-Path $dirCorsa "$($o.slug).1.json"))) {
      if ($e.esito -ne 'CONFLITTO' -or -not ($e.PSObject.Properties.Name -contains 'righe_proprie') -or -not $e.template) { continue }
      foreach ($r in @($e.righe_proprie | Sort-Object -Unique)) {
        $k = $e.template + "`0" + $r
        $conteggio[$k] = 1 + $conteggio[$k]; $testi[$k] = @($e.template, $r)
      }
    }
  }
  $comuni = @{}
  foreach ($k in $conteggio.Keys) { if ($conteggio[$k] -ge $Consenso) { $t = $testi[$k]; if (-not $comuni.ContainsKey($t[0])) { $comuni[$t[0]] = New-Object System.Collections.ArrayList }; [void]$comuni[$t[0]].Add($t[1]) } }
  if ($comuni.Count) {
    [System.IO.File]::WriteAllText($fileComuni, ($comuni | ConvertTo-Json -Depth 3), $utf8)
    Log ("consenso: {0} righe anteriori alla storia del template, in {1} file, condivise da almeno {2} progetti" -f (($comuni.Values | ForEach-Object { $_.Count } | Measure-Object -Sum).Sum), $comuni.Count, $Consenso)
    Log ''
  }

  # --- fase 3: seconda misura, applicazione, verifica --------------------------
  $skillNorme = @(Get-ChildItem -LiteralPath (Join-Path $tpl '.claude\skills') -Directory |
    Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'RIFERIMENTO.md') } | ForEach-Object { $_.Name })
  foreach ($o in $progetti) {
    $prj = $o.percorso
    if (-not $o.stato) {
      $json = Join-Path $dirCorsa "$($o.slug).json"
      if ((Misura $prj $json) -ge 2) { $o.stato = 'errore-strumento' }
      else {
        # Il rapporto si legge una volta sola e si conserva: la passata di scrittura riscrive
        # lo stesso file, quindi dopo non si saprebbe piu' quali strumenti sono stati toccati.
        $esitiPrima = Leggi-Json $json
        $o.c = Conta $esitiPrima
        $o.stato = if ($o.c.azionabili -eq 0) { 'allineato' } elseif ($o.c.CONFLITTO -gt 0) { 'conflitti' } else { 'da-allineare' }
        if ($o.sporco -and $o.stato -ne 'allineato') { $o.stato = 'albero-sporco' }

        if ($Applica -and $o.stato -eq 'da-allineare') {
          $codice = Misura $prj $json -Scrivi
          $json2 = Join-Path $dirCorsa "$($o.slug).dopo.json"
          $codice2 = Misura $prj $json2
          $fuori = @(Invoca-Git $prj status --porcelain | ForEach-Object { $_.Substring(3).Trim('"') } |
            Where-Object { $_ -notmatch '^(\.claude|tools|docs)/' -and $_ -ne 'CLAUDE.md' })
          if ($codice -ge 2 -or $codice2 -ge 2 -or -not (Test-Path -LiteralPath $json2)) { $o.stato = 'errore-strumento' }
          else {
            $c2 = Conta (Leggi-Json $json2)
            if ($c2.azionabili -gt 0) { $o.stato = 'incompleto' }
            elseif ($fuori) { $o.stato = 'fuori-perimetro'; $o.avvisi += 'cambiati fuori perimetro: ' + ($fuori -join ', ') }
            else {
              $o.stato = 'applicato'
              $pr = Prove-Strumenti $prj $esitiPrima
              if ($pr.falliti) {
                # Lo stato non e' fra quelli finali, quindi il progetto finisce fra quelli da
                # guardare a mano, l'uscita e 1 e il marcatore di allineamento non viene scritto:
                # un progetto i cui strumenti non girano non e un progetto allineato.
                $o.stato = 'prove-fallite'
                $o.avvisi += 'prova interna fallita: ' + ($pr.falliti -join ', ')
              }
              elseif ($pr.provati -gt 0) { Log ('{0,-44} {1}' -f '', "prove interne degli strumenti: $($pr.provati) superate") }
            }
          }
        }
        if ($Applica -and $o.stato -in 'applicato', 'allineato') {
          $marcatore = Join-Path $prj '.claude\allineamento-template.json'
          $vecchio = $null
          if (Test-Path -LiteralPath $marcatore) { try { $vecchio = Leggi-Json $marcatore } catch {} }
          if (-not $vecchio -or $vecchio.template_albero_claude -ne $tplAlbero) {
            $m = [ordered]@{ template_commit = $tplHead; template_albero_claude = $tplAlbero; data_commit_template = $tplData; allineato_il = (Get-Date -Format 'yyyy-MM-dd'); strumento = 'allinea-tutti.ps1' }
            [System.IO.File]::WriteAllText($marcatore, ($m | ConvertTo-Json) + "`n", $utf8)
          }
        }

        $claudeMd = Join-Path $prj 'CLAUDE.md'
        if (-not (Test-Path -LiteralPath $claudeMd)) { $claudeMd = Join-Path $prj '.claude\CLAUDE.md' }
        $testo = if (Test-Path -LiteralPath $claudeMd) { Get-Content -LiteralPath $claudeMd -Raw -Encoding UTF8 } else { '' }
        $senza = @($skillNorme | Where-Object { (Test-Path -LiteralPath (Join-Path $prj ".claude\skills\$_")) -and ($testo -notmatch [regex]::Escape('`' + $_ + '`')) })
        if ($senza) { $o.avvisi += 'innesco mancante nel CLAUDE.md: ' + ($senza -join ', ') }
        if (Test-Path -LiteralPath $misura) {
          $mis = & python $misura --root $prj 2>&1
          if ($LASTEXITCODE -ne 0) { $tot = ($mis | Select-String 'progetto [0-9.]+ caratteri' | Select-Object -First 1); $o.avvisi += 'carico istruzioni oltre soglia' + $(if ($tot) { " ($($tot.Line.Trim()))" } else { '' }) }
        }
      }
    }
    $sintesi = if ($o.c) { ($AZIONABILI + 'ADATTATO' | Where-Object { $o.c[$_] } | ForEach-Object { "$_=$($o.c[$_])" }) -join ' ' } else { '' }
    Log ('{0,-44} {1,-20} {2}' -f $o.nome, $o.stato, $sintesi)
    foreach ($a in $o.avvisi) { Log ('{0,-44} {1}' -f '', "avviso: $a") }
    $registro[$prj] = [ordered]@{
      stato = $o.stato; misurato_il = (Get-Date -Format 's'); template_commit = $tplHead; template_albero_claude = $tplAlbero
      conteggi = $o.c; avvisi = $o.avvisi; rapporto = (Join-Path $dirCorsa "$($o.slug).json")
    }
  }

  # --- sintesi ----------------------------------------------------------------
  [System.IO.File]::WriteAllText($fileRegistro, ($registro | ConvertTo-Json -Depth 5), $utf8)
  Log ''
  Log (($progetti | Group-Object stato | Sort-Object Name | ForEach-Object { "$($_.Name)=$($_.Count)" }) -join '  ')
  $SALTATI = @('clone-del-template', 'albero-secondario', 'escluso')
  $finali = @('allineato', 'applicato', 'da-allineare') + $SALTATI
  $saltati = @($progetti | Where-Object { $SALTATI -contains $_.stato })
  if ($saltati) { Log ''; Log 'Saltati per costruzione, nessuna azione:'; $saltati | ForEach-Object { Log "  $($_.percorso)  ($($_.stato))" } }
  $amano = @($progetti | Where-Object { $finali -notcontains $_.stato })
  if ($amano) { Log ''; Log 'Da guardare a mano:'; $amano | ForEach-Object { Log "  $($_.percorso)  ($($_.stato))" } }
  $applicati = @($progetti | Where-Object { $_.stato -eq 'applicato' })
  if ($applicati) { Log ''; Log 'Applicati, da rileggere con git diff e committare a mano:'; $applicati | ForEach-Object { Log "  $($_.percorso)" } }
  Log ''
  Log "registro: $fileRegistro"
  Log "log e rapporti di questa corsa: $dirCorsa"
  if (-not $Applica) { Log 'a vuoto: nessun progetto e stato scritto. Rilanciare con -Applica.' }
  $pendenti = @($progetti | Where-Object { $_.stato -eq 'da-allineare' })
  $esito = if ($amano -or (-not $Applica -and $pendenti)) { 1 } else { 0 }
}
finally {
  Remove-Item -LiteralPath $blocco -ErrorAction SilentlyContinue
}
exit $esito
