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
  albero-sporco        modifiche non committate su almeno uno dei file che questa
                       passata riscriverebbe: si misura ma non si scrive, cosi
                       l'allineamento non si mescola a lavoro in corso. Un albero
                       sporco altrove non ferma niente e lascia solo un avviso,
                       perche la ragione della guardia e' tenere leggibile il
                       git diff dei file allineati, non l'igiene del progetto
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

La scoperta guarda il primo livello di ogni radice: un progetto annidato piu' in
basso, per esempio D:\gruppo\progetto, si raggiunge solo con -Profondita 1. E una
cartella che ha .claude ma non .claude/PROJECT-SYSTEM.md non e istanziata, quindi
la passata non la tratta; non resta pero' invisibile, perche a fine corsa viene
elencata a parte, da istanziare o da escludere.

Progetti dentro macchine raggiungibili via SSH. Oltre alle radici locali la
passata interroga ogni alias di ~/.ssh/config che non punta a GitHub (oppure i
soli -Ssh indicati; -SoloLocali li salta tutti) e cerca .claude/PROJECT-SYSTEM.md
sotto -RadiciRemote fino a -ProfonditaRemota livelli. Un progetto remoto si scrive
ssh://<alias>/<percorso> e passa per le stesse guardie, la stessa misura e la
stessa scrittura di uno locale, attraverso trasporto-ssh.ps1; il template gli
arriva come git bundle in ~/.cache/template-claude-developing della macchina.
Un progetto remoto si tratta solo se il proprietario lo ha approvato in
_notes/allineamento/remoti-approvati.txt: uno nuovo resta da-confermare, si
elenca e non si tocca, perche' una macchina nuova con progetti di sviluppo e' una
decisione del proprietario e non della passata. esclusi.txt accetta anche
ssh://<alias>, che esclude l'host intero. Un host che non risponde, che non ha
git o python3, o su cui il template non arriva, si elenca fra quelli da guardare.

  da-confermare        progetto remoto trovato ma non ancora approvato dal
                       proprietario: non si misura e non si scrive

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
  [switch]$ConsentiTemplateSporco,
  [string[]]$Ssh = @(),
  [switch]$SoloLocali,
  [string[]]$RadiciRemote = @('~', '/opt', '/srv', '/var/www', '/home'),
  [int]$ProfonditaRemota = 5,
  [switch]$Autotest
)
Set-StrictMode -Version 2
$ErrorActionPreference = 'Continue'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
$utf8 = New-Object System.Text.UTF8Encoding $false

function Dividi([string[]]$v) { @($v | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ }) }
$Solo = Dividi $Solo; $Escludi = Dividi $Escludi; $Radici = Dividi $Radici; $Ssh = Dividi $Ssh; $RadiciRemote = Dividi $RadiciRemote

function Esci-Guardia([string]$m) { Write-Host "GUARDIA: $m"; exit 2 }
# Invoca-Git, Esiste, Leggi-Testo, Scrivi-Testo e la scoperta remota: un solo
# codice per i progetti locali e per quelli nelle macchine raggiungibili via SSH.
. (Join-Path $PSScriptRoot 'trasporto-ssh.ps1')

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
# Per un progetto remoto lo strumento gira sulla macchina, con la copia del template
# preparata li', e il rapporto torna qui con scp: da quel momento consenso, registro
# e chiudi-allineamento lo leggono come quello di un progetto locale.
$tplRemoti = @{}
function Misura([string]$prj, [string]$json, [switch]$Scrivi) {
  if (Test-Remoto $prj) {
    $r = Dividi-Remoto $prj
    $rt = $tplRemoti[$r.alias]
    $rjson = '.cache/allinea-rapporti/' + [System.IO.Path]::GetFileName($json)
    $a = @("$rt/.claude/templates/tools/allinea-dal-template.py", '--template', $rt, '--progetto', $r.percorso, '--json', "`$HOME/$rjson", '--innesco')
    if (Test-Path -LiteralPath $fileComuni) { $a += '--righe-comuni', "`$HOME/.cache/allinea-rapporti/righe-comuni.json" }
    if ($Scrivi) { $a += '--applica', '--rimuovi' }
    # $HOME resta fuori dagli apici perche' la shell remota lo espanda.
    $riga = 'mkdir -p "$HOME/.cache/allinea-rapporti" && python3 ' + (($a | ForEach-Object { if ($_ -like '$HOME/*') { '"' + $_ + '"' } else { Q $_ } }) -join ' ') + ' 2>&1; echo "USCITA=$?"'
    $out = @(Esegui-Ssh $r.alias $riga)
    $u = $out | Where-Object { $_ -like 'USCITA=*' } | Select-Object -Last 1
    $codice = if ($u) { [int]$u.Substring(7) } else { 2 }
    $out = @($out | Where-Object { $_ -notlike 'USCITA=*' })
    if ($codice -lt 2 -and -not (Copia-Giu $r.alias $rjson $json)) { $codice = 2; $out += 'rapporto non riportato con scp' }
  }
  else {
    $a = @($strumento, '--template', $tpl, '--progetto', $prj, '--json', $json, '--innesco')
    if (Test-Path -LiteralPath $fileComuni) { $a += '--righe-comuni', $fileComuni }
    if ($Scrivi) { $a += '--applica', '--rimuovi' }
    $out = & python @a 2>&1
    $codice = $LASTEXITCODE
  }
  [System.IO.File]::AppendAllText($fileLog, "--- $prj" + $(if ($Scrivi) { ' (applica)' } else { '' }) + "`r`n" + ($out | Out-String) + "`r`n", $utf8)
  return $codice
}

# L'albero sporco, e perche' la domanda giusta non e' "ci sono modifiche" ma "ci sono
# modifiche DOVE scrivo".
#
# La guardia esisteva per una ragione sola: dopo una passata il proprietario rilegge con
# git diff i soli file che l'allineamento ha scritto, e un lavoro in corso sugli stessi
# file rende quel diff illeggibile. Finche' la guardia ha guardato l'albero intero ha pero'
# fermato anche chi aveva modifiche altrove, dove non c'era niente da confondere. Misurato
# il 2026-10-13 sulla passata del giorno prima: dei sette progetti fermati, sei avevano zero
# file in comune fra lo sporco e cio' che la passata avrebbe scritto, e il settimo ne aveva
# uno. Sei progetti su sette rimandavano l'allineamento per un conflitto che non esisteva.
function Sporchi([string]$prj) {
  $out = @()
  foreach ($r in @(Invoca-Git $prj status --porcelain)) {
    if ($r.Length -lt 4) { continue }
    $p = $r.Substring(3).Trim()
    # Una rinomina si scrive "vecchio -> nuovo": conta la destinazione, che e' il file su disco.
    if ($p -match ' -> ') { $p = ($p -split ' -> ')[-1] }
    $out += $p.Trim('"').Replace('\', '/')
  }
  return , @($out)
}

# I file che la passata precedente ha scritto in questo progetto, letti dal suo rapporto. Una
# passata finita incompleta lascia l'albero sporco proprio su quei file, e la guardia li prendeva
# per lavoro di un'altra sessione: il 2026-10-20, dopo una corsa incompleta, 38 progetti su 38
# risultavano albero-sporco per lo sporco lasciato dall'allineamento stesso.
# Si legge la corsa piu' recente che in questo progetto ha davvero scritto, riconoscibile dal
# rapporto <slug>.dopo.json, che nasce solo dopo una scrittura: non il registro, che ogni corsa
# riscrive anche quando misura soltanto, e che farebbe passare per "nostro" cio' che si sta per
# scrivere adesso, rendendo cieca la guardia.
# Tutte le corse che hanno scritto dopo l'ultimo commit dell'allineamento, non solo l'ultima: due
# corse incomplete di fila lasciano sporchi i file di entrambe, e la seconda non elenca quelli che
# trova gia' scritti dalla prima. Leggere solo l'ultima ha lasciato 36 progetti fermi il 2026-10-20.
function Scritti-Prima([string]$slug, [string]$cartellaCorse, [string]$esclusa = '', [string]$dopoIl = '') {
  $out = @()
  $corse = @(Get-ChildItem -LiteralPath $cartellaCorse -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -ne $esclusa -and $_.Name -gt $dopoIl -and (Test-Path -LiteralPath (Join-Path $_.FullName "$slug.dopo.json")) })
  foreach ($c in $corse) {
    $rapporto = Join-Path $c.FullName "$slug.json"
    if (-not (Test-Path -LiteralPath $rapporto)) { continue }
    foreach ($e in (Leggi-Json $rapporto)) {
      if ($AZIONABILI -contains $e.esito -and $e.esito -ne 'CONFLITTO') { $out += $e.file; if ($e.esito -eq 'SPOSTATO' -and $e.template) { $out += $e.template } }
    }
  }
  $out += '.claude/allineamento-template.json', '.claude/allineamento-risolti.json'
  return , @($out | Sort-Object -Unique)
}

function Collisione($esitiPrima, $sporchi) {
  # Un CONFLITTO non viene scritto, quindi non puo' mescolarsi a niente; gli altri esiti
  # azionabili si', RIMOSSO compreso, perche' la passata gira con --rimuovi.
  $scritti = @($esitiPrima | Where-Object { $AZIONABILI -contains $_.esito -and $_.esito -ne 'CONFLITTO' } |
    ForEach-Object { $_.file })
  $out = @()
  foreach ($s in $sporchi) {
    foreach ($f in $scritti) {
      # Una cartella non tracciata compare come "cartella/": vale per tutto cio' che sta sotto.
      if ($f -eq $s -or ($s.EndsWith('/') -and $f.StartsWith($s))) { $out += $f; break }
    }
  }
  return , @($out | Sort-Object -Unique)
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
    if (-not (Esiste $prj $e.file 'file')) { continue }
    $src = Leggi-Testo $prj $e.file
    $flag = $null
    if ($src -match '--self-test') { $flag = '--self-test' } elseif ($src -match '--autotest') { $flag = '--autotest' }
    # Uno strumento senza prova interna si prova almeno a caricare, con --help. Misurato il
    # 2026-10-13 sulla passata del giorno prima: dei 24 strumenti riscritti nei 25 progetti
    # applicati, nessuno dichiarava --self-test o --autotest, quindi questo passo riportava
    # "0 provati" su una passata che aveva riscritto 24 file di codice. --help non esercita il
    # comportamento, ma un file troncato o con un import rotto cade qui e in nessun altro punto
    # della passata.
    if (-not $flag) { $flag = '--help' }
    if (Test-Remoto $prj) {
      $out = @(Esegui-Ssh (Dividi-Remoto $prj).alias ('cd ' + (Q (Dividi-Remoto $prj).percorso) + ' && python3 ' + (Q $e.file) + ' ' + $flag + ' 2>&1; echo "USCITA=$?"'))
      $u = $out | Where-Object { $_ -like 'USCITA=*' } | Select-Object -Last 1
      $codice = if ($u) { [int]$u.Substring(7) } else { 2 }
      $out = @($out | Where-Object { $_ -notlike 'USCITA=*' })
    }
    else {
      $out = & python (Join-Path $prj ($e.file -replace '/', '\')) $flag 2>&1
      $codice = $LASTEXITCODE
    }
    $testo = ($out | Out-String)
    [System.IO.File]::AppendAllText($fileLog, "--- prova interna $($e.file) $flag (uscita $codice)`r`n" + $testo + "`r`n", $utf8)
    if ($codice -eq 0) { $provati++ }
    elseif ($testo -match 'unrecognized arguments|invalid choice|not recognized') { }
    elseif ($flag -eq '--help' -and $testo -notmatch 'Traceback') { }
    else { $falliti += $e.file }
  }
  return [pscustomobject]@{ provati = $provati; falliti = $falliti }
}

# Progetti esclusi dalla passata per decisione del proprietario, finche non la ritira: una
# riga per percorso, con il motivo dopo il cancelletto. Vive in _notes/ del template perche
# i percorsi sono della macchina, come il registro, e non si versiona.
$fileEsclusi = Join-Path $base 'esclusi.txt'
$esclusi = Leggi-Elenco $fileEsclusi
# I progetti remoti che il proprietario ha approvato: un progetto in una macchina
# raggiungibile via SSH non si tocca finche' non sta qui, perche' una macchina nuova
# con progetti di sviluppo si decide, non si scopre.
$fileApprovati = Join-Path $base 'remoti-approvati.txt'
$approvati = Leggi-Elenco $fileApprovati

# Prove interne della guardia dell'albero sporco. Sono qui e non in tests/ perche'
# esercitano due funzioni di questo script e non il suo giro completo: il giro completo
# ha per bersaglio decine di repository veri, queste due domande no.
if ($Autotest) {
  $rossi = 0
  function Caso([string]$nome, $atteso, $ottenuto) {
    $a = @($atteso) -join '|'; $o = @($ottenuto) -join '|'
    if ($a -eq $o) { Write-Host "ok   $nome" } else { $script:rossi++; Write-Host "ROSSO $nome"; Write-Host "      atteso  $a"; Write-Host "      ottenuto $o" }
  }
  $esitiFinti = @(
    [pscustomobject]@{ file = '.claude/rules/uno.md'; esito = 'VECCHIO' },
    [pscustomobject]@{ file = '.claude/skills/attrezzo/SKILL.md'; esito = 'NUOVO' },
    [pscustomobject]@{ file = 'tools/vecchio.py'; esito = 'RIMOSSO' },
    [pscustomobject]@{ file = '.claude/rules/due.md'; esito = 'CONFLITTO' },
    [pscustomobject]@{ file = '.claude/rules/tre.md'; esito = 'UGUALE' }
  )
  Caso 'lo sporco sugli stessi file e una collisione' @('.claude/rules/uno.md') (Collisione $esitiFinti @('.claude/rules/uno.md', 'docs/altro.md'))
  Caso 'lo sporco altrove non e una collisione' @() (Collisione $esitiFinti @('docs/altro.md', 'src/app.py', '.claude/memory/progress.md'))
  Caso 'un file in conflitto non viene scritto, quindi non collide' @() (Collisione $esitiFinti @('.claude/rules/due.md'))
  Caso 'un file che resta uguale non viene scritto, quindi non collide' @() (Collisione $esitiFinti @('.claude/rules/tre.md'))
  Caso 'un file da rimuovere collide se e sporco' @('tools/vecchio.py') (Collisione $esitiFinti @('tools/vecchio.py'))
  Caso 'una cartella non tracciata copre cio che sta sotto' @('.claude/skills/attrezzo/SKILL.md') (Collisione $esitiFinti @('.claude/skills/attrezzo/'))

  # Il trasporto verso le macchine raggiungibili via SSH, nelle parti che non chiedono una rete.
  $configFinta = "Host github-corp`n  HostName github.com`nHost vm-a vm-b`n  HostName 192.0.2.1`nHost *.interno`n  User x`nHost github.com`n  HostName github.com`nHost gh-lavoro`n  HostName ssh.github.com`nHost studio`n  HostName studio.lan"
  Caso 'gli alias GitHub e quelli con jolly non sono macchine' @('vm-a', 'vm-b', 'studio') (Host-Ssh $configFinta)
  Caso "l'apice singolo si cita senza aprire la stringa" @("'a'\''b'") (Q "a'b")
  Caso 'un progetto remoto si divide in alias e percorso' @('vm-a', '/opt/x') (@((Dividi-Remoto 'ssh://vm-a/opt/x/') | ForEach-Object { $_.alias; $_.percorso }))
  Caso 'un percorso locale non e remoto' @($false) (Test-Remoto 'D:\progetto')
  $elencoFinto = @{ 'ssh://vm-b' = 'host intero'; 'ssh://vm-a/opt/x' = 'progetto'; 'd:\locale' = 'locale' }
  Caso "l'host escluso copre tutti i suoi progetti" @('host intero') (In-Elenco $elencoFinto 'ssh://VM-B/home/y')
  Caso 'un progetto remoto si trova per percorso' @('progetto') (In-Elenco $elencoFinto 'ssh://vm-a/opt/x')
  Caso "un progetto nuovo su un host noto non e approvato" @($null) (In-Elenco $elencoFinto 'ssh://vm-a/opt/nuovo')
  Caso 'un percorso locale si trova senza distinguere le maiuscole' @('locale') (In-Elenco $elencoFinto 'D:\Locale\')
  $b64 = (Comando-Ssh "echo 'x'") -replace '^echo (\S+) \|.*$', '$1'
  Caso 'il comando remoto torna identico dal base64' @("echo 'x'") ([System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($b64)))
  $corseFinte = Join-Path ([System.IO.Path]::GetTempPath()) ('corse-finte-' + [guid]::NewGuid().ToString('N').Substring(0, 6))
  $scritta = Join-Path $corseFinte '20260101-000000'; $misurata = Join-Path $corseFinte '20260102-000000'
  New-Item -ItemType Directory -Force -Path $scritta, $misurata | Out-Null
  [System.IO.File]::WriteAllText((Join-Path $scritta 'prj.json'), (ConvertTo-Json @(@{ file = '.claude/rules/uno.md'; esito = 'VECCHIO' }, @{ file = '.claude/rules/due.md'; esito = 'CONFLITTO' })), $utf8)
  [System.IO.File]::WriteAllText((Join-Path $scritta 'prj.dopo.json'), '[]', $utf8)
  [System.IO.File]::WriteAllText((Join-Path $misurata 'prj.json'), (ConvertTo-Json @(@{ file = '.claude/rules/tre.md'; esito = 'VECCHIO' })), $utf8)
  $seconda = Join-Path $corseFinte '20260103-000000'; New-Item -ItemType Directory -Force -Path $seconda | Out-Null
  [System.IO.File]::WriteAllText((Join-Path $seconda 'prj.json'), (ConvertTo-Json @(@{ file = '.claude/rules/quattro.md'; esito = 'VECCHIO' })), $utf8)
  [System.IO.File]::WriteAllText((Join-Path $seconda 'prj.dopo.json'), '[]', $utf8)
  $scrittiFinti = Scritti-Prima 'prj' $corseFinte
  Caso 'due corse scritte di fila contano entrambe, non solo l ultima' @($true, $true) @((@($scrittiFinti) -contains '.claude/rules/uno.md'), (@($scrittiFinti) -contains '.claude/rules/quattro.md'))
  Caso 'una corsa anteriore all ultimo allineamento non conta' @($false) (@(Scritti-Prima 'prj' $corseFinte '' '20260102-000000') -contains '.claude/rules/uno.md')
  Caso 'cio che la passata precedente ha scritto si riconosce come suo' @($true) (@($scrittiFinti) -contains '.claude/rules/uno.md')
  Caso 'un file in conflitto non e scritto dalla passata, quindi resta altrui' @($false) (@($scrittiFinti) -contains '.claude/rules/due.md')
  Caso 'una corsa che ha solo misurato non rende suo niente' @($false) (@($scrittiFinti) -contains '.claude/rules/tre.md')
  Remove-Item -LiteralPath $corseFinte -Recurse -Force
  $progFinti = @('/opt/app')
  Caso 'la home di un utente non e un progetto parziale' @($true, $true) @((Parziale-Rumore '/home/dev' '/home/dev' $progFinti), (Parziale-Rumore '/home/altro' '/home/dev' $progFinti))
  Caso 'un percorso con una cartella nascosta e rumore' @($true) (Parziale-Rumore '/home/dev/.vscode/extensions/x' '/home/dev' $progFinti)
  Caso 'una cartella dentro un progetto trovato e del progetto' @($true) (Parziale-Rumore '/opt/app/_notes/MCP-docx' '/home/dev' $progFinti)
  Caso 'una cartella vera con .claude senza PROJECT-SYSTEM resta elencata' @($false) (Parziale-Rumore '/home/dev/Scrivania/nuovo' '/home/dev' $progFinti)
  Write-Host ''
  Write-Host "$(24 - $rossi) casi superati su 24"
  Remove-Item -LiteralPath $blocco -Force -ErrorAction SilentlyContinue
  exit $(if ($rossi) { 1 } else { 0 })
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
      Where-Object { $Escludi -notcontains $_.Name } |
      ForEach-Object { [pscustomobject]@{ percorso = $_.FullName.TrimEnd('\'); nome = $_.Name } }
  }
  $trovati = @($trovati | Sort-Object percorso -Unique)

  # Le macchine raggiungibili via SSH. Una macchina esclusa per intero non si
  # interroga nemmeno; una che non risponde non ferma la corsa ma si dichiara, perche'
  # un progetto che la passata non vede e' un progetto che resta indietro in silenzio.
  $hostProblemi = @(); $parzialiRemoti = @(); $remotiTrovati = @()
  if (-not $SoloLocali) {
    $alias = if ($Ssh) { $Ssh } else { Host-Ssh }
    foreach ($h in $alias) {
      if (In-Elenco $esclusi "ssh://$h/") { continue }
      $s = Scopri-Remoti $h $RadiciRemote $ProfonditaRemota
      if (-not $s.raggiunto) { $hostProblemi += [pscustomobject]@{ alias = $h; motivo = 'non risponde via ssh' }; continue }
      if (-not $s.strumenti) { $hostProblemi += [pscustomobject]@{ alias = $h; motivo = 'manca git o python3' }; continue }
      $progettiHost = @($s.progetti | Where-Object { -not $Solo -or $Solo -contains (($_ -split '/')[-1]) } | Where-Object { $Escludi -notcontains (($_ -split '/')[-1]) })
      $parzialiRemoti += @($s.parziali | Where-Object { -not (In-Elenco $esclusi $_) })
      if (-not $progettiHost) { continue }
      $daMisurare = @($progettiHost | Where-Object { (In-Elenco $approvati $_) -and -not (In-Elenco $esclusi $_) })
      if ($daMisurare) {
        $rt = Prepara-Template $h $tpl $tplHead
        if (-not $rt) { $hostProblemi += [pscustomobject]@{ alias = $h; motivo = $script:ErroreTemplate }; continue }
        $tplRemoti[$h] = $rt
      }
      $remotiTrovati += @($progettiHost | ForEach-Object { [pscustomobject]@{ percorso = $_.TrimEnd('/'); nome = (Nome-Progetto $_) } })
    }
  }
  $trovati = @($trovati) + @($remotiTrovati)

  # Una cartella che ha .claude ma non .claude/PROJECT-SYSTEM.md e' invisibile a
  # questa passata, e lo resta in silenzio: non essendo istanziata non entra nel
  # registro, quindi nessun conteggio la nomina e nessuno si accorge che il
  # template non la raggiunge. Misurato il 2026-10-13 sulle due radici: nove
  # progetti su nove di D:\ erano coperti, ma dodici cartelle con .claude e senza
  # PROJECT-SYSTEM.md non erano mai comparse in nessuna corsa, e una di esse
  # aveva una sessione di agente viva. Si elencano a fine corsa senza toccarle,
  # perche' inizializzarle o escluderle e' una decisione del proprietario.
  $parziali = foreach ($r in $Radici) {
    if (-not (Test-Path -LiteralPath $r)) { continue }
    $gci = @{ LiteralPath = $r; Directory = $true; ErrorAction = 'SilentlyContinue' }
    if ($Profondita -gt 0) { $gci['Recurse'] = $true; $gci['Depth'] = $Profondita }
    Get-ChildItem @gci |
      Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName '.claude') } |
      Where-Object { -not (Test-Path -LiteralPath (Join-Path $_.FullName '.claude\PROJECT-SYSTEM.md')) } |
      Where-Object { $_.FullName.TrimEnd('\') -ne $tpl } |
      Where-Object { $_.FullName -notmatch '\\\.claude\\' } |
      Where-Object { -not $esclusi.ContainsKey($_.FullName.TrimEnd('\').ToLowerInvariant()) } |
      Where-Object { -not $Solo -or $Solo -contains $_.Name } |
      Where-Object { $Escludi -notcontains $_.Name }
  }
  $parziali = @($parziali | Sort-Object FullName -Unique)

  if (-not $trovati -and -not $hostProblemi) { Log 'nessun progetto istanziato trovato'; $esito = 0; return }

  # --- fase 1: guardie e prima misura -----------------------------------------
  $progetti = foreach ($p in $trovati) {
    $prj = $p.percorso
    $o = [pscustomobject]@{ nome = $p.nome; percorso = $prj; slug = ($prj -replace '[:\\/]+', '--').Trim('-'); stato = $null; sporco = $false; sporchi = @(); c = $null; avvisi = @() }
    $escl = In-Elenco $esclusi $prj
    if ($escl) { $o.stato = 'escluso'; $o.avvisi += 'escluso: ' + $escl }
    elseif ((Test-Remoto $prj) -and -not (In-Elenco $approvati $prj)) { $o.stato = 'da-confermare' }
    elseif (-not (Esiste $prj '.git')) { $o.stato = 'non-git' }
    elseif ((Esiste $prj '.git' 'file') -and -not $IncludiAlberi) { $o.stato = 'albero-secondario' }
    else {
      $radiciPrj = @(Invoca-Git $prj rev-list --max-parents=0 HEAD)
      if ($radiciPrj | Where-Object { $tplRadici -contains $_ }) { $o.stato = 'clone-del-template' }
      elseif (@('MERGE_HEAD', 'rebase-merge', 'rebase-apply', 'CHERRY_PICK_HEAD', 'REVERT_HEAD') | Where-Object { $gp = Invoca-Git $prj rev-parse --git-path $_; $gp -and (Esiste $prj $gp) }) { $o.stato = 'operazione-in-corso' }
      else {
        $null = Invoca-Git $prj symbolic-ref -q HEAD
        if ($LASTEXITCODE -ne 0) { $o.stato = 'head-staccato' }
      }
    }
    if (-not $o.stato) {
      $o.sporchi = Sporchi $prj
      $o.sporco = $o.sporchi.Count -gt 0
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
    foreach ($h in @($tplRemoti.Keys)) {
      if (-not (Copia-Su $h $fileComuni '.cache/allinea-rapporti/righe-comuni.json')) { Log "AVVISO: righe del consenso non copiate su $h" }
    }
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
        $collisi = @()
        if ($o.sporco -and $o.stato -ne 'allineato') {
          $collisi = Collisione $esitiPrima $o.sporchi
          if ($collisi) {
            $dataMarcatore = @(Invoca-Git $prj log -1 --format=%cd --date=format:%Y%m%d-%H%M%S -- .claude/allineamento-template.json) | Select-Object -First 1
            $nostri = Scritti-Prima $o.slug (Join-Path $base 'corse') $corsa ([string]$dataMarcatore)
            $altrui = @($collisi | Where-Object { $nostri -notcontains $_ -and $_ -notlike '.agents/skills/*' })
            if (-not $altrui) { $o.avvisi += "albero sporco solo per la passata precedente non committata ($($collisi.Count) file): si completa"; $collisi = @() }
            else { $collisi = $altrui }
          }
          if ($collisi) {
            $o.stato = 'albero-sporco'
            $o.avvisi += 'lavoro in corso sui file da allineare: ' + ($collisi -join ', ')
          }
          else { $o.avvisi += "albero sporco in $($o.sporchi.Count) file, nessuno fra quelli che questa passata scrive" }
        }

        if ($Applica -and $o.stato -eq 'da-allineare') {
          $codice = Misura $prj $json -Scrivi
          # Gli adattatori Codex delle skill si rigenerano subito dopo la scrittura. Senza, un
          # progetto che riceve una skill nuova si trovava la chiusura ferma su sync-codex-skills:
          # misurato il 2026-10-19 su un progetto istanziato con cerca-pacchetto, segnalato da quel
          # progetto. Lo strumento e' quello del template, che arriva in ogni progetto.
          # Solo dove gli adattatori esistono gia': la prima corsa del 2026-10-20 li lanciava ovunque e
          # ha creato da zero .agents/ in ventotto progetti che non avevano mai scelto Codex.
          if ($codice -lt 2 -and (Esiste $prj '.agents/skills' 'cartella')) {
            if (Test-Remoto $prj) {
              $r = Dividi-Remoto $prj
              $null = Esegui-Ssh $r.alias ('python3 ' + (Q "$($tplRemoti[$r.alias])/.claude/templates/tools/sync-codex-skills.py") + ' --project-root ' + (Q $r.percorso) + ' >/dev/null 2>&1')
            }
            else { $null = & python (Join-Path $tpl '.claude\templates\tools\sync-codex-skills.py') --project-root $prj 2>&1 }
          }
          $json2 = Join-Path $dirCorsa "$($o.slug).dopo.json"
          $codice2 = Misura $prj $json2
          # Cio' che era gia' sporco prima della scrittura non e' opera di questa passata:
          # senza questa sottrazione un progetto con lavoro in corso fuori dal perimetro
          # verrebbe marcato fuori-perimetro per modifiche che non ha fatto l'allineamento.
          $fuori = @((Sporchi $prj) | Where-Object { $o.sporchi -notcontains $_ } |
            Where-Object { $_ -notmatch '^(\.claude|\.agents|tools|docs)/' -and $_ -ne 'CLAUDE.md' })
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
          $marcatore = '.claude/allineamento-template.json'
          $vecchio = $null
          if (Esiste $prj $marcatore 'file') { try { $vecchio = (Leggi-Testo $prj $marcatore) | ConvertFrom-Json } catch {} }
          if (-not $vecchio -or $vecchio.template_albero_claude -ne $tplAlbero) {
            $m = [ordered]@{ template_commit = $tplHead; template_albero_claude = $tplAlbero; data_commit_template = $tplData; allineato_il = (Get-Date -Format 'yyyy-MM-dd'); strumento = 'allinea-tutti.ps1' }
            if (-not (Scrivi-Testo $prj $marcatore (($m | ConvertTo-Json) + "`n"))) { $o.avvisi += 'marcatore di allineamento non scritto' }
          }
        }

        $relMd = if (Esiste $prj 'CLAUDE.md' 'file') { 'CLAUDE.md' } else { '.claude/CLAUDE.md' }
        $testo = Leggi-Testo $prj $relMd
        $senza = @($skillNorme | Where-Object { (Esiste $prj ".claude/skills/$_" 'cartella') -and ($testo -notmatch [regex]::Escape('`' + $_ + '`')) })
        if ($senza) { $o.avvisi += 'innesco mancante nel CLAUDE.md: ' + ($senza -join ', ') }
        if (Test-Path -LiteralPath $misura) {
          if (Test-Remoto $prj) {
            $r = Dividi-Remoto $prj
            $mis = @(Esegui-Ssh $r.alias ('python3 ' + (Q "$($tplRemoti[$r.alias])/.claude/templates/tools/misura-istruzioni.py") + ' --root ' + (Q $r.percorso) + ' 2>&1; echo "USCITA=$?"'))
            $u = $mis | Where-Object { $_ -like 'USCITA=*' } | Select-Object -Last 1
            $global:LASTEXITCODE = if ($u) { [int]$u.Substring(7) } else { 0 }
          }
          else { $mis = & python $misura --root $prj 2>&1 }
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
  $daConfermare = @($progetti | Where-Object { $_.stato -eq 'da-confermare' })
  $amano = @($progetti | Where-Object { $finali -notcontains $_.stato -and $_.stato -ne 'da-confermare' })
  if ($amano) { Log ''; Log 'Da guardare a mano:'; $amano | ForEach-Object { Log "  $($_.percorso)  ($($_.stato))" } }
  if ($hostProblemi) { Log ''; Log 'Macchine raggiungibili via SSH che questa passata non ha potuto trattare:'; $hostProblemi | ForEach-Object { Log "  $($_.alias)  ($($_.motivo))" }; Log '  si sistema l accesso, oppure si escludono con ssh://<alias> in _notes/allineamento/esclusi.txt' }
  if ($daConfermare) {
    Log ''
    Log 'Progetti nelle macchine via SSH non ancora approvati dal proprietario: non toccati'
    $daConfermare | ForEach-Object { Log "  $($_.percorso)" }
    Log "  si approvano in $fileApprovati oppure si escludono in esclusi.txt, su decisione del proprietario"
  }
  $tuttiParziali = @($parziali | ForEach-Object { $_.FullName }) + @($parzialiRemoti)
  if ($tuttiParziali) {
    Log ''
    Log 'Hanno .claude ma non .claude/PROJECT-SYSTEM.md: la passata non li vede'
    $tuttiParziali | ForEach-Object { Log "  $_" }
    Log '  si istanziano con la skill init-project-system, oppure si elencano in _notes/allineamento/esclusi.txt per non rivederli'
  }
  $applicati = @($progetti | Where-Object { $_.stato -eq 'applicato' })
  if ($applicati) { Log ''; Log 'Applicati, da rileggere con git diff e committare a mano:'; $applicati | ForEach-Object { Log "  $($_.percorso)" } }
  Log ''
  Log "registro: $fileRegistro"
  Log "log e rapporti di questa corsa: $dirCorsa"
  if (-not $Applica) { Log 'a vuoto: nessun progetto e stato scritto. Rilanciare con -Applica.' }
  $pendenti = @($progetti | Where-Object { $_.stato -eq 'da-allineare' })
  $esito = if ($amano -or $hostProblemi -or $daConfermare -or (-not $Applica -and $pendenti)) { 1 } else { 0 }
}
finally {
  Remove-Item -LiteralPath $blocco -ErrorAction SilentlyContinue
}
exit $esito
