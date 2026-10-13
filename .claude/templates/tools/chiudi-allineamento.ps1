<#
.SYNOPSIS
Chiude la passata di allineamento: committa e spinge, progetto per progetto, i
soli file che la passata ha scritto.

.DESCRIPTION
allinea-tutti.ps1 -Applica scrive nei progetti e si ferma li, perche commit e
push restano manuali dell'utente. Fino al 13/10/2026 quel passo si faceva a mano,
con un blocco di comandi lungo quanto i progetti applicati, e la misura di quella
giornata dice perche non bastava: su due tornate, nove push sono caduti su
timeout SSH verso GitHub lasciando commit locali non spinti, una riga del blocco
si e corrotta incollata nella console di PowerShell aprendo una virgoletta mai
chiusa, e da li in poi la console ha inghiottito in silenzio tutto il resto;
servirono tre giri di verifica repository per repository solo per sapere che cosa
fosse davvero arrivato sul remoto.

Nessuno di quei tre guasti era evitabile scrivendo meglio il blocco, perche
nessuno dei tre dipende da chi lo scrive: un elenco di comandi incollato in un
terminale non e atomico, una rete che cade non si corregge ripetendo il comando a
mano, e un git add -A non sa distinguere l'allineamento dal lavoro di un'altra
sessione aperta sullo stesso albero. Questo script toglie tutti e tre i problemi
perche prende le informazioni che la passata ha gia scritto su disco.

Che cosa committa, esattamente. Ogni corsa di allineamento lascia in
_notes/allineamento/corse/<data>/ un rapporto JSON per progetto, con una voce per
file e il suo esito, e il registro dice quale rapporto appartiene a quale
progetto. I file scritti sono quelli con esito NUOVO, VECCHIO, SUPERATO, MERGE e
INNESCO, piu la destinazione di uno SPOSTATO; sono rimossi l'origine di uno
SPOSTATO e i RIMOSSO, piu il marcatore .claude/allineamento-template.json. Lo
script mette in stage l'intersezione fra quell'elenco e cio che nell'albero
risulta davvero modificato, e dichiara quanti file sporchi ha lasciato fuori:
quelli sono il lavoro di qualcun altro, e restano dove sono.

Il push riprova da se sugli errori di rete, con attese crescenti, e se non basta
il progetto resta elencato come da riprendere: -SoloPush rifa i soli push
mancanti senza toccare nulla. Senza -Applica lo script non scrive niente e mostra
che cosa farebbe, come allinea-tutti.ps1.

Il controllo umano non sparisce, si sposta dove serve: lo script lo lancia
l'utente, dopo avere riletto con git diff cio che la passata ha scritto, ed e lo
stesso patto di chiudi-sessione.ps1. Il messaggio di commit porta il commit del
template a cui la passata ha allineato, cosi la storia di ogni progetto dice da
quale versione del template viene quella riga.

Guardie: template repository git; registro presente; per ogni progetto, cartella
esistente, repository git, branch in uscita, rapporto leggibile. Un progetto che
non passa una guardia viene elencato e saltato, senza fermare gli altri.

Codici di uscita: 0 se non resta niente da fare, 1 se qualche progetto e da
riprendere o da guardare a mano, 2 se una guardia iniziale non passa.

.EXAMPLE
.\chiudi-allineamento.ps1
.EXAMPLE
.\chiudi-allineamento.ps1 -Applica
.EXAMPLE
.\chiudi-allineamento.ps1 -SoloPush -Applica
.EXAMPLE
.\chiudi-allineamento.ps1 -Solo crosswords,totocalcio -Applica
#>
param(
  [string]$Template = '',
  [switch]$Applica,
  [string[]]$Solo = @(),
  [string[]]$Escludi = @(),
  [string]$Messaggio = '',
  [int]$Tentativi = 3,
  [switch]$SoloPush,
  [switch]$SaltaPush,
  [switch]$Autotest
)
Set-StrictMode -Version 2
$ErrorActionPreference = 'Continue'
$utf8 = New-Object System.Text.UTF8Encoding $false

function Dividi([string[]]$v) { @($v | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ }) }
$Solo = Dividi $Solo; $Escludi = Dividi $Escludi

function Esci-Guardia([string]$m) { Write-Host "GUARDIA: $m"; exit 2 }
# Non si chiama Git: in PowerShell una funzione con quel nome copre git.exe e
# richiamerebbe se stessa all'infinito.
function Invoca-Git([string]$repo) {
  $out = & git -C $repo @args 2>$null
  return $out
}

$ESITI_SCRITTI = @('NUOVO', 'VECCHIO', 'SUPERATO', 'MERGE', 'INNESCO')
$MARCATORE = '.claude/allineamento-template.json'

# I percorsi che la passata ha toccato, letti dal suo rapporto e non indovinati
# dall'albero: e' questa la differenza fra un commit dell'allineamento e un
# git add -A, che in un albero dove lavora un'altra sessione prende anche il suo.
function Percorsi-Rapporto([string]$rapporto) {
  $esiti = Get-Content -LiteralPath $rapporto -Raw -Encoding UTF8 | ConvertFrom-Json
  $p = New-Object System.Collections.Generic.HashSet[string]
  foreach ($e in $esiti) {
    if ($ESITI_SCRITTI -contains $e.esito) { [void]$p.Add($e.file) }
    elseif ($e.esito -eq 'SPOSTATO') { [void]$p.Add($e.file); if ($e.template) { [void]$p.Add($e.template) } }
    elseif ($e.esito -eq 'RIMOSSO') { [void]$p.Add($e.file) }
  }
  [void]$p.Add($MARCATORE)
  return $p
}

# -uall e' obbligatorio: senza, git riassume una cartella nuova in una sola riga
# che finisce con /, e l'intersezione con i percorsi del rapporto, che sono file,
# non troverebbe niente proprio dove la passata ha scritto di piu'.
function Sporchi([string]$prj) {
  $out = @()
  foreach ($r in @(Invoca-Git $prj status --porcelain -uall)) {
    if (-not $r -or $r.Length -lt 4) { continue }
    $p = $r.Substring(3).Trim()
    if ($p -match ' -> ') { $p = ($p -split ' -> ')[-1] }
    $out += $p.Trim('"').Replace('\', '/')
  }
  return $out
}

function Smista([string]$prj, [string]$rapporto) {
  $attesi = Percorsi-Rapporto $rapporto
  $miei = @(); $altrui = @()
  foreach ($f in (Sporchi $prj)) {
    if ($attesi.Contains($f)) { $miei += $f } else { $altrui += $f }
  }
  return [pscustomobject]@{ miei = $miei; altrui = $altrui }
}

function Ha-Remoto([string]$prj) {
  & git -C $prj rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>$null | Out-Null
  return ($LASTEXITCODE -eq 0)
}

function Avanti([string]$prj) {
  $n = & git -C $prj rev-list --count '@{u}..HEAD' 2>$null
  if ($LASTEXITCODE -ne 0) { return 0 }
  return [int]$n
}

# Una rete che cade non si corregge ripetendo il comando a mano: la ripetizione e'
# parte dello strumento, con attese crescenti. L'azione e' iniettabile per potere
# provare la ripetizione senza una rete.
function Spingi([string]$prj, [int]$tentativi, $azione, [int[]]$attese = @(5, 15, 30)) {
  if (-not $azione) { $azione = { param($p) & git -C $p push 2>&1 | Out-Null; return $LASTEXITCODE } }
  for ($i = 1; $i -le $tentativi; $i++) {
    $codice = & $azione $prj
    if ($codice -eq 0) { return [pscustomobject]@{ ok = $true; tentativi = $i } }
    if ($i -lt $tentativi) { Start-Sleep -Seconds $attese[[Math]::Min($i - 1, $attese.Count - 1)] }
  }
  return [pscustomobject]@{ ok = $false; tentativi = $tentativi }
}

function Chiudi-Progetto([string]$prj, [string]$rapporto, [string]$messaggio,
                         [bool]$applica, [int]$tentativi, [bool]$soloPush, [bool]$saltaPush, $azionePush) {
  $r = [pscustomobject]@{ percorso = $prj; esito = ''; file = 0; lasciati = 0; commit = ''; push = ''; tentativi = 0 }

  if (-not (Test-Path -LiteralPath $prj)) { $r.esito = 'cartella sparita'; return $r }
  Invoca-Git $prj rev-parse --git-dir | Out-Null
  if ($LASTEXITCODE -ne 0) { $r.esito = 'non e un repository'; return $r }
  $branch = (Invoca-Git $prj rev-parse --abbrev-ref HEAD)
  if (-not $branch -or $branch -eq 'HEAD') { $r.esito = 'head staccato'; return $r }

  if (-not $soloPush) {
    if (-not (Test-Path -LiteralPath $rapporto)) { $r.esito = 'rapporto mancante'; return $r }
    $s = Smista $prj $rapporto
    $r.file = $s.miei.Count; $r.lasciati = $s.altrui.Count
    if ($s.miei.Count -gt 0) {
      if ($applica) {
        # A blocchi: una riga di comando non e' infinita, e un progetto puo'
        # portare centinaia di percorsi.
        for ($i = 0; $i -lt $s.miei.Count; $i += 60) {
          $blocco = @($s.miei[$i..([Math]::Min($i + 59, $s.miei.Count - 1))])
          & git -C $prj add -- @blocco 2>&1 | Out-Null
          if ($LASTEXITCODE -ne 0) { $r.esito = 'git add fallito'; return $r }
        }
        & git -C $prj commit -m $messaggio 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { $r.esito = 'commit rifiutato'; return $r }
        $r.commit = (Invoca-Git $prj rev-parse --short HEAD)
        $r.esito = 'committato'
      }
      else { $r.esito = 'da committare' }
    }
    else { $r.esito = 'niente da committare' }
  }

  if ($saltaPush) { $r.push = 'saltato'; return $r }
  if (-not (Ha-Remoto $prj)) { $r.push = 'senza remoto'; return $r }
  $avanti = Avanti $prj
  if ($avanti -le 0) { $r.push = 'allineato al remoto'; return $r }
  if (-not $applica) { $r.push = "$avanti da spingere"; return $r }
  $e = Spingi $prj $tentativi $azionePush
  $r.tentativi = $e.tentativi
  if ($e.ok) { $r.push = 'spinto' } else { $r.push = 'push fallito' }
  return $r
}

# ----------------------------------------------------------------------------
# Prove interne. Ogni caso oppone cio' che deve entrare nel commit a cio' che non
# deve entrarci: uno strumento che mette in stage tutto passerebbe meta' delle
# prove da solo.
# ----------------------------------------------------------------------------
function Esegui-Autotest {
  $script:casi = @()
  function Prova([string]$nome, [bool]$esito) { $script:casi += [pscustomobject]@{ nome = $nome; ok = $esito } }
  $radice = Join-Path ([System.IO.Path]::GetTempPath()) ("autotest-chiudi-all-" + [guid]::NewGuid().ToString('N').Substring(0, 8))
  New-Item -ItemType Directory -Force -Path $radice | Out-Null
  try {
    function Nuovo-Repo([string]$nome) {
      $p = Join-Path $radice $nome
      New-Item -ItemType Directory -Force -Path $p | Out-Null
      & git -C $p init -q -b main 2>&1 | Out-Null
      & git -C $p config user.name 'prova' | Out-Null
      & git -C $p config user.email 'prova@esempio.invalid' | Out-Null
      & git -C $p config commit.gpgsign false | Out-Null
      return $p
    }
    function Scrivi([string]$p, [string]$rel, [string]$testo) {
      $f = Join-Path $p ($rel -replace '/', '\')
      New-Item -ItemType Directory -Force -Path (Split-Path $f) | Out-Null
      [System.IO.File]::WriteAllText($f, $testo, $utf8)
    }
    function Rapporto([string]$dove, $voci) {
      [System.IO.File]::WriteAllText($dove, (ConvertTo-Json @($voci) -Depth 3), $utf8)
      return $dove
    }
    function Commits([string]$p) { return [int](& git -C $p rev-list --count HEAD 2>$null) }

    $MSG = 'Allineamento dal template al commit abc1234'

    # 1-3. stage selettivo: entra cio' che il rapporto dichiara, resta fuori il resto
    $a = Nuovo-Repo 'selettivo'
    Scrivi $a 'suo.md' "prima`n"; Scrivi $a 'mio.md' "prima`n"
    & git -C $a add -A | Out-Null; & git -C $a commit -q -m 'base' | Out-Null
    Scrivi $a 'suo.md' "lavoro di un'altra sessione`n"
    Scrivi $a 'mio.md' "aggiornato dal template`n"
    Scrivi $a '.claude/norme/nuova.md' "nuova`n"
    $rapA = Rapporto (Join-Path $radice 'a.json') @(
      @{ file = 'mio.md'; template = 'mio.md'; esito = 'VECCHIO' },
      @{ file = '.claude/norme/nuova.md'; template = '.claude/norme/nuova.md'; esito = 'NUOVO' },
      @{ file = 'assente.md'; template = 'assente.md'; esito = 'UGUALE' })
    $rA = Chiudi-Progetto $a $rapA $MSG $true 1 $false $true $null
    $dentro = @(& git -C $a show --name-only --pretty=format: HEAD | Where-Object { $_ })
    Prova "il file che la passata ha scritto entra nel commit" ($dentro -contains 'mio.md')
    Prova "il file nuovo dentro una cartella nuova entra nel commit" ($dentro -contains '.claude/norme/nuova.md')
    Prova "il file di un'altra sessione resta fuori dal commit" (-not ($dentro -contains 'suo.md'))
    Prova "i file lasciati fuori si contano e si dichiarano" ($rA.lasciati -eq 1 -and $rA.file -eq 2)

    # 4. un albero senza niente da committare non produce un commit vuoto
    $b = Nuovo-Repo 'pulito'
    Scrivi $b 'mio.md' "prima`n"
    & git -C $b add -A | Out-Null; & git -C $b commit -q -m 'base' | Out-Null
    $prima = Commits $b
    $rB = Chiudi-Progetto $b $rapA $MSG $true 1 $false $true $null
    Prova "un albero pulito non produce un commit vuoto" ((Commits $b) -eq $prima -and $rB.esito -eq 'niente da committare')

    # 5. la rimozione decisa dalla passata entra nel commit come cancellazione
    $c = Nuovo-Repo 'rimozione'
    Scrivi $c 'vecchio.md' "prima`n"; Scrivi $c 'suo.md' "prima`n"
    & git -C $c add -A | Out-Null; & git -C $c commit -q -m 'base' | Out-Null
    Remove-Item -LiteralPath (Join-Path $c 'vecchio.md') -Force
    Scrivi $c 'suo.md' "lavoro altrui`n"
    $rapC = Rapporto (Join-Path $radice 'c.json') @(@{ file = 'vecchio.md'; template = $null; esito = 'RIMOSSO' })
    $null = Chiudi-Progetto $c $rapC $MSG $true 1 $false $true $null
    $stato = @(& git -C $c show --name-status --pretty=format: HEAD | Where-Object { $_ })
    Prova "la cancellazione decisa dalla passata entra nel commit" (($stato -join ' ') -match 'D\s+vecchio\.md')

    # 6. senza -Applica non si scrive niente
    $d = Nuovo-Repo 'avuoto'
    Scrivi $d 'mio.md' "prima`n"
    & git -C $d add -A | Out-Null; & git -C $d commit -q -m 'base' | Out-Null
    Scrivi $d 'mio.md' "cambiato`n"
    $prima = Commits $d
    $rD = Chiudi-Progetto $d $rapA $MSG $false 1 $false $true $null
    Prova "senza -Applica non si committa e lo si dichiara" ((Commits $d) -eq $prima -and $rD.esito -eq 'da committare')

    # 7. un progetto senza remoto non fa fallire la corsa
    $e = Nuovo-Repo 'senzaremoto'
    Scrivi $e 'mio.md' "prima`n"
    & git -C $e add -A | Out-Null; & git -C $e commit -q -m 'base' | Out-Null
    Scrivi $e 'mio.md' "cambiato`n"
    $rE = Chiudi-Progetto $e $rapA $MSG $true 1 $false $false $null
    Prova "un progetto senza remoto si committa e si dichiara senza remoto" ($rE.esito -eq 'committato' -and $rE.push -eq 'senza remoto')

    # 8-9. la ripetizione del push: due cadute e poi la riuscita, e il limite che non basta
    $script:giri = 0
    $instabile = { param($p) $script:giri++; if ($script:giri -lt 3) { return 1 }; return 0 }
    $script:giri = 0
    $ok = Spingi 'qualunque' 3 $instabile @(0, 0, 0)
    Prova "il push riprova dopo una caduta di rete e riesce" ($ok.ok -and $ok.tentativi -eq 3)
    $script:giri = 0
    $ko = Spingi 'qualunque' 2 $instabile @(0, 0, 0)
    Prova "se i tentativi finiscono il push resta fallito, non riuscito" (-not $ko.ok)

    # 10. il messaggio rispetta il presidio dell'hook commit-msg
    $m = Messaggio-Predefinito 'abc1234567890'
    Prova "il messaggio sta nei 72 caratteri e non porta attribuzioni" (
      $m.Length -le 72 -and $m -notmatch 'Co-Authored-By' -and $m -notmatch 'Generated with')
  }
  finally {
    Remove-Item -LiteralPath $radice -Recurse -Force -ErrorAction SilentlyContinue
  }
  $caduti = @($casi | Where-Object { -not $_.ok })
  foreach ($c in $casi) { $segno = 'ok'; if (-not $c.ok) { $segno = 'KO' }; Write-Host ("  {0}  {1}" -f $segno, $c.nome) }
  Write-Host ("{0} casi, {1} falliti" -f $casi.Count, $caduti.Count)
  if ($caduti) { return 1 }
  return 0
}

function Messaggio-Predefinito([string]$commit) {
  $breve = $commit
  if ($breve.Length -gt 7) { $breve = $breve.Substring(0, 7) }
  return "Allineamento dal template al commit $breve"
}

if ($Autotest) { exit (Esegui-Autotest) }

# --- guardie ----------------------------------------------------------------
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { Esci-Guardia 'git non e nel PATH' }
if (-not $Template) { $Template = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path }
if (-not (Test-Path -LiteralPath (Join-Path $Template '.claude\PROJECT-SYSTEM.md'))) { Esci-Guardia "$Template non sembra il template" }
$fileRegistro = Join-Path $Template '_notes\allineamento\registro.json'
if (-not (Test-Path -LiteralPath $fileRegistro)) { Esci-Guardia "registro assente: lanciare prima allinea-tutti.ps1 (${fileRegistro})" }

$registro = @{}
try { (Get-Content -LiteralPath $fileRegistro -Raw -Encoding UTF8 | ConvertFrom-Json).PSObject.Properties | ForEach-Object { $registro[$_.Name] = $_.Value } }
catch { Esci-Guardia 'registro illeggibile' }

$voci = @()
foreach ($k in ($registro.Keys | Sort-Object)) {
  $v = $registro[$k]
  if ($v.stato -ne 'applicato') { continue }
  $nome = Split-Path $k -Leaf
  if ($Solo -and -not ($Solo | Where-Object { $nome -like "*$_*" })) { continue }
  if ($Escludi | Where-Object { $nome -like "*$_*" }) { continue }
  $voci += [pscustomobject]@{ percorso = $k; nome = $nome; rapporto = $v.rapporto; commit = $v.template_commit; misurato = $v.misurato_il }
}
if (-not $voci) { Write-Host 'nessun progetto in stato applicato nel registro: niente da chiudere'; exit 0 }

$msg = $Messaggio
if (-not $msg) { $msg = Messaggio-Predefinito ($voci[0].commit) }
if ($msg.Length -gt 72) { Esci-Guardia "messaggio oltre i 72 caratteri ($($msg.Length)): l'hook commit-msg lo rifiuterebbe" }

$modo = 'a vuoto'
if ($Applica) { $modo = 'applica' }
$cosa = 'commit e push'
if ($SoloPush) { $cosa = 'solo push' }
if ($SaltaPush) { $cosa = 'solo commit' }
Write-Host ("template {0}  registro {1} progetti applicati" -f $Template, $voci.Count)
Write-Host ("modo: {0}   {1}   messaggio: {2}" -f $modo, $cosa, $msg)

# Lo stage si fonda su quali file la passata ha scritto, non su quali modifiche
# ha fatto: un file che un'altra sessione ha riadattato dopo la corsa risulta
# comunque nostro. L'eta' della corsa e' quindi parte della misura, e si dichiara.
$misure = @($voci | ForEach-Object { $_.misurato } | Where-Object { $_ } | Sort-Object)
if ($misure) {
  $ultima = [datetime]::Parse($misure[-1])
  $ore = [Math]::Round(((Get-Date) - $ultima).TotalHours, 1)
  Write-Host ("corsa misurata il {0}, {1} ore fa" -f $ultima.ToString('yyyy-MM-dd HH:mm'), $ore)
  if ($ore -gt 6) {
    Write-Host 'AVVISO: la corsa non e recente. Un file che un altra sessione ha riadattato da allora'
    Write-Host '        risulta comunque fra quelli da committare: rileggere con git diff, oppure'
    Write-Host '        rilanciare prima allinea-tutti.ps1 -Applica.'
  }
}
Write-Host ''

$esiti = @()
foreach ($v in $voci) {
  $r = Chiudi-Progetto $v.percorso $v.rapporto $msg ([bool]$Applica) $Tentativi ([bool]$SoloPush) ([bool]$SaltaPush) $null
  $esiti += $r
  $coda = ''
  if ($r.commit) { $coda = $r.commit }
  if ($r.tentativi -gt 1) { $coda = "$coda ($($r.tentativi) tentativi)" }
  Write-Host ('{0,-42} {1,-22} {2,-10} {3,-22} file {4}, lasciati {5}' -f $v.nome, $r.esito, $coda, $r.push, $r.file, $r.lasciati)
}

Write-Host ''
$falliti = @($esiti | Where-Object { $_.push -eq 'push fallito' -or $_.esito -in @('commit rifiutato', 'git add fallito', 'rapporto mancante', 'non e un repository', 'head staccato', 'cartella sparita') })
$committati = @($esiti | Where-Object { $_.esito -eq 'committato' })
$spinti = @($esiti | Where-Object { $_.push -eq 'spinto' })
Write-Host ("committati {0}, spinti {1}, da riprendere {2}" -f $committati.Count, $spinti.Count, $falliti.Count)
if ($falliti) {
  Write-Host ''
  Write-Host 'Da riprendere:'
  foreach ($f in $falliti) { Write-Host ("  {0}  ({1} {2})" -f $f.percorso, $f.esito, $f.push) }
  Write-Host ''
  Write-Host 'Per i soli push caduti, quando la rete torna:'
  Write-Host ('  powershell -NoProfile -ExecutionPolicy Bypass -File "' + $PSCommandPath + '" -SoloPush -Applica')
}
if (-not $Applica) { Write-Host ''; Write-Host 'a vuoto: niente e stato committato ne spinto. Rilanciare con -Applica.' }
if ($falliti) { exit 1 }
exit 0
