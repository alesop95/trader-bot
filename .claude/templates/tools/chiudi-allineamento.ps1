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
  [switch]$Autotest,
  [string]$AutotestSsh = ''
)
Set-StrictMode -Version 2
$ErrorActionPreference = 'Continue'
$utf8 = New-Object System.Text.UTF8Encoding $false

function Dividi([string[]]$v) { @($v | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ }) }
$Solo = Dividi $Solo; $Escludi = Dividi $Escludi

function Esci-Guardia([string]$m) { Write-Host "GUARDIA: $m"; exit 2 }
# Invoca-Git ed Esiste valgono per un progetto locale e per uno ssh://<alias>/<percorso>:
# per un progetto in una macchina via SSH commit e push girano sulla macchina, con
# l'identita' git, il ramo, gli hook e le chiavi di quel progetto, che e' il suo
# version control e non quello di questa postazione.
. (Join-Path $PSScriptRoot 'trasporto-ssh.ps1')

$ESITI_SCRITTI = @('NUOVO', 'VECCHIO', 'SUPERATO', 'MERGE', 'INNESCO')
$MARCATORE = '.claude/allineamento-template.json'
$RISOLTI = '.claude/allineamento-risolti.json'

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
  # Il registro delle risoluzioni a mano e' parte dell'allineamento come il marcatore: senza,
  # un conflitto risolto con --risolto restava fuori dal commit e la passata successiva lo
  # ritrovava aperto. Osservato il 2026-10-19 su tre progetti; si mette in stage solo se e' cambiato.
  [void]$p.Add($RISOLTI)
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

# Le corse che hanno scritto in questo progetto dopo il suo ultimo commit, non solo l'ultima.
# Una corsa finita incompleta lascia file scritti e non committati; la corsa successiva li trova
# gia' a posto e non li elenca, e il commit li lasciava fuori: misurato il 2026-10-20, quindici
# file per progetto. Una corsa ha scritto se accanto al suo rapporto c'e' <slug>.dopo.json.
function Percorsi-Corse([string]$prj, [string]$rapporto) {
  # Un insieme nuovo: quello restituito da Percorsi-Rapporto esce dalla funzione come array di
  # dimensione fissa, e un Add su quello fallisce senza fermare niente.
  $tutti = New-Object System.Collections.Generic.HashSet[string]
  foreach ($f in (Percorsi-Rapporto $rapporto)) { [void]$tutti.Add($f) }
  $cartella = Split-Path (Split-Path $rapporto -Parent) -Parent
  $slug = [System.IO.Path]::GetFileNameWithoutExtension($rapporto)
  # L'ultimo commit dell'allineamento, cioe' quello che ha toccato il marcatore, e non l'ultimo
  # commit del progetto: un'altra sessione che committa il proprio lavoro dopo una corsa non
  # rende committato cio' che la corsa aveva scritto.
  $dataHead = @(Invoca-Git $prj log -1 --format=%cd --date=format:%Y%m%d-%H%M%S -- .claude/allineamento-template.json) | Select-Object -First 1
  if (-not (Test-Path -LiteralPath $cartella)) { return , $tutti }
  # Al primo allineamento nessun marcatore e ancora versionato: valgono tutte le corse scritte.
  if (-not $dataHead) { $dataHead = "" }
  foreach ($c in (Get-ChildItem -LiteralPath $cartella -Directory -ErrorAction SilentlyContinue)) {
    if ($c.Name -le $dataHead) { continue }
    if (-not (Test-Path -LiteralPath (Join-Path $c.FullName "$slug.dopo.json"))) { continue }
    $r = Join-Path $c.FullName "$slug.json"
    if (Test-Path -LiteralPath $r) { foreach ($f in (Percorsi-Rapporto $r)) { [void]$tutti.Add($f) } }
  }
  return , $tutti
}

function Smista([string]$prj, [string]$rapporto) {
  $attesi = Percorsi-Corse $prj $rapporto
  $miei = @(); $altrui = @()
  # Gli adattatori Codex sono generati dalla passata con sync-codex-skills, non scritti dal
  # rapporto: senza questa regola restavano fuori dal commit e la chiusura del progetto si fermava.
  # Ma sono della passata solo dove il progetto li aveva gia' tracciati, perche' la passata li
  # aggiorna e non li crea: il 2026-10-20 una sessione aperta su un progetto ha creato da se'
  # .agents/, e il commit dell'allineamento l'avrebbe preso per suo.
  $adattatoriTracciati = @(Invoca-Git $prj ls-files -- .agents).Count -gt 0
  foreach ($f in (Sporchi $prj)) {
    if ($attesi.Contains($f) -or ($adattatoriTracciati -and $f -like '.agents/skills/*')) { $miei += $f } else { $altrui += $f }
  }
  return [pscustomobject]@{ miei = $miei; altrui = $altrui }
}

function Ha-Remoto([string]$prj) {
  Invoca-Git $prj rev-parse --abbrev-ref --symbolic-full-name '@{u}' | Out-Null
  return ($LASTEXITCODE -eq 0)
}

function Avanti([string]$prj) {
  $n = Invoca-Git $prj rev-list --count '@{u}..HEAD'
  if ($LASTEXITCODE -ne 0) { return 0 }
  return [int]$n
}

# Una rete che cade non si corregge ripetendo il comando a mano: la ripetizione e'
# parte dello strumento, con attese crescenti. L'azione e' iniettabile per potere
# provare la ripetizione senza una rete.
function Spingi([string]$prj, [int]$tentativi, $azione, [int[]]$attese = @(5, 15, 30)) {
  if (-not $azione) { $azione = { param($p) Invoca-Git $p push | Out-Null; return $LASTEXITCODE } }
  for ($i = 1; $i -le $tentativi; $i++) {
    $codice = & $azione $prj
    if ($codice -eq 0) { return [pscustomobject]@{ ok = $true; tentativi = $i } }
    if ($i -lt $tentativi) { Start-Sleep -Seconds $attese[[Math]::Min($i - 1, $attese.Count - 1)] }
  }
  return [pscustomobject]@{ ok = $false; tentativi = $tentativi }
}

# Remoti oltre all'upstream su cui un progetto tiene lo stesso ramo, per decisione del
# proprietario: _notes/allineamento/push-remoti.txt, una riga per progetto con il percorso
# seguito dai nomi dei remoti, il motivo dopo il cancelletto. Nato il 2026-10-19 per un
# progetto che tiene il ramo allineato su due remoti, dove spingere solo l'upstream
# lasciava l'altro indietro di un commit a ogni passata.
function Leggi-PushRemoti([string]$file) {
  $m = @{}
  if (-not (Test-Path -LiteralPath $file)) { return $m }
  foreach ($r in (Get-Content -LiteralPath $file -Encoding UTF8)) {
    $t = ($r -split '#', 2)[0].Trim()
    if (-not $t) { continue }
    $parti = @($t -split '\s+')
    if ($parti.Count -lt 2) { continue }
    $m[$parti[0].TrimEnd('\', '/').ToLowerInvariant()] = @($parti[1..($parti.Count - 1)])
  }
  return $m
}

# Spinge il ramo corrente su un remoto che non e' l'upstream, solo se quel remoto e'
# indietro, e mai con forza: un ramo divergente resta un push fallito da guardare.
function Spingi-Altro([string]$prj, [string]$remoto, [bool]$applica, [int]$tentativi) {
  $branch = Invoca-Git $prj rev-parse --abbrev-ref HEAD
  $null = Invoca-Git $prj fetch -q $remoto $branch
  $dietro = Invoca-Git $prj rev-list --count "$remoto/${branch}..HEAD"
  if ($LASTEXITCODE -eq 0 -and [int]$dietro -eq 0) { return "$remoto allineato" }
  if (-not $applica) { return "$remoto da spingere" }
  $azione = { param($p) Invoca-Git $p push $remoto "HEAD:refs/heads/$branch" | Out-Null; return $LASTEXITCODE }.GetNewClosure()
  $e = Spingi $prj $tentativi $azione
  if ($e.ok) { return "$remoto spinto" }
  return "$remoto push fallito"
}

function Chiudi-Progetto([string]$prj, [string]$rapporto, [string]$messaggio,
                         [bool]$applica, [int]$tentativi, [bool]$soloPush, [bool]$saltaPush, $azionePush, [string[]]$altriRemoti = @()) {
  $r = Chiudi-ProgettoUpstream $prj $rapporto $messaggio $applica $tentativi $soloPush $saltaPush $azionePush
  if ($saltaPush -or -not $altriRemoti -or $r.esito -in @('cartella sparita', 'non e un repository', 'head staccato', 'rapporto mancante', 'git add fallito', 'commit rifiutato')) { return $r }
  $esiti = @($altriRemoti | ForEach-Object { Spingi-Altro $prj $_ $applica $tentativi })
  $r.push = (@($r.push) + $esiti) -join ', '
  return $r
}

function Chiudi-ProgettoUpstream([string]$prj, [string]$rapporto, [string]$messaggio,
                         [bool]$applica, [int]$tentativi, [bool]$soloPush, [bool]$saltaPush, $azionePush) {
  $r = [pscustomobject]@{ percorso = $prj; esito = ''; file = 0; lasciati = 0; commit = ''; push = ''; tentativi = 0 }

  if (-not (Esiste $prj '' 'cartella')) { $r.esito = 'cartella sparita'; return $r }
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
          Invoca-Git $prj add -- @blocco | Out-Null
          if ($LASTEXITCODE -ne 0) { $r.esito = 'git add fallito'; return $r }
        }
        Invoca-Git $prj commit -m $messaggio | Out-Null
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

    # 3b. il registro delle risoluzioni a mano entra nel commit dell'allineamento
    $h = Nuovo-Repo 'risolti'
    Scrivi $h 'mio.md' "prima`n"; Scrivi $h '.claude/allineamento-risolti.json' "{}`n"
    & git -C $h add -A | Out-Null; & git -C $h commit -q -m 'base' | Out-Null
    Scrivi $h '.claude/allineamento-risolti.json' "{`"tools/x.py`": `"abc`"}`n"
    $null = Chiudi-Progetto $h $rapA $MSG $true 1 $false $true $null
    Prova "il registro delle risoluzioni a mano entra nel commit" ((@(& git -C $h show --name-only --pretty=format: HEAD) -contains '.claude/allineamento-risolti.json'))

    # 3c. l'adattatore Codex generato dalla passata entra nel commit
    $k = Nuovo-Repo 'adattatori'
    Scrivi $k 'mio.md' "prima`n"; Scrivi $k '.agents/skills/vecchia/SKILL.md' "adattatore`n"
    & git -C $k add -A | Out-Null; & git -C $k commit -q -m 'base' | Out-Null
    Scrivi $k '.agents/skills/nuova/SKILL.md' "adattatore`n"
    $null = Chiudi-Progetto $k $rapA $MSG $true 1 $false $true $null
    Prova "l'adattatore Codex generato dalla passata entra nel commit" ((@(& git -C $k show --name-only --pretty=format: HEAD) -contains '.agents/skills/nuova/SKILL.md'))
    # 3d. una cartella .agents creata da un'altra sessione, dove il progetto non ne tracciava, resta fuori
    $q = Nuovo-Repo 'agentialtrui'
    Scrivi $q 'mio.md' "prima`n"
    & git -C $q add -A | Out-Null; & git -C $q commit -q -m 'base' | Out-Null
    Scrivi $q 'mio.md' "aggiornato`n"; Scrivi $q '.agents/skills/sua/SKILL.md' "di un'altra sessione`n"
    $rQ = Chiudi-Progetto $q $rapA $MSG $true 1 $false $true $null
    Prova ".agents creata da un'altra sessione resta fuori dal commit" (-not (@(& git -C $q show --name-only --pretty=format: HEAD) -contains '.agents/skills/sua/SKILL.md') -and $rQ.lasciati -eq 1)

    # 3e. il commit prende i file di tutte le corse che hanno scritto dopo l'ultimo allineamento
    $u = Nuovo-Repo 'corse'
    Scrivi $u 'a.md' "prima`n"; Scrivi $u 'b.md' "prima`n"; Scrivi $u 'c.md' "prima`n"; Scrivi $u 'd.md' "prima`n"
    Scrivi $u '.claude/allineamento-template.json' "{}`n"
    & git -C $u add -A | Out-Null; & git -C $u commit -q -m 'allineamento precedente' | Out-Null
    $corse = Join-Path $radice 'registro-corse'
    function Corsa([string]$nome, [string]$file, [bool]$scritta) {
      $d = Join-Path $corse $nome; New-Item -ItemType Directory -Force -Path $d | Out-Null
      [System.IO.File]::WriteAllText((Join-Path $d 'prj.json'), (ConvertTo-Json @(@{ file = $file; template = $file; esito = 'VECCHIO' })), $utf8)
      if ($scritta) { [System.IO.File]::WriteAllText((Join-Path $d 'prj.dopo.json'), '[]', $utf8) }
      return (Join-Path $d 'prj.json')
    }
    $null = Corsa '20000101-000000' 'c.md' $true
    $null = Corsa '29991230-000000' 'a.md' $true
    $null = Corsa '29991230-120000' 'd.md' $false
    $ultimaCorsa = Corsa '29991231-000000' 'b.md' $true
    foreach ($n in 'a.md', 'b.md', 'c.md', 'd.md') { Scrivi $u $n "aggiornato`n" }
    $rU = Chiudi-Progetto $u $ultimaCorsa $MSG $true 1 $false $true $null
    $dentroU = @(& git -C $u show --name-only --pretty=format: HEAD | Where-Object { $_ })
    Prova "una corsa precedente che ha scritto dopo l'ultimo allineamento entra nel commit" ($dentroU -contains 'a.md' -and $dentroU -contains 'b.md')
    Prova "una corsa anteriore all'ultimo allineamento, o che ha solo misurato, resta fuori" (-not ($dentroU -contains 'c.md') -and -not ($dentroU -contains 'd.md') -and $rU.lasciati -eq 2)

    # 3f. CLI reale dopo due passate, prima di versionare il primo marcatore.
    $ripetuto = Nuovo-Repo 'riallineato'
    Scrivi $ripetuto 'mio.md' "prima`n"
    & git -C $ripetuto add -A | Out-Null; & git -C $ripetuto commit -q -m 'base' | Out-Null
    Scrivi $ripetuto 'mio.md' "dopo`n"; Scrivi $ripetuto 'altrui.md' "locale`n"
    $tplProva = Join-Path $radice 'template-prova'
    Scrivi $tplProva '.claude/PROJECT-SYSTEM.md' "prova`n"
    $primaDir = Join-Path $tplProva '_notes/allineamento/corse/20200101-000000'
    $dopoDir = Join-Path $tplProva '_notes/allineamento/corse/20200102-000000'
    New-Item -ItemType Directory -Force -Path $primaDir, $dopoDir | Out-Null
    $null = Rapporto (Join-Path $primaDir 'prj.json') @(@{file='mio.md';esito='VECCHIO'})
    [IO.File]::WriteAllText((Join-Path $primaDir 'prj.dopo.json'),'[]',$utf8)
    [IO.File]::WriteAllText((Join-Path $dopoDir 'prj.json'),'[]',$utf8)
    $regProva = @{}
    $regProva[$ripetuto] = @{stato='allineato';rapporto=(Join-Path $dopoDir 'prj.json');template_commit='abc1234';misurato_il=(Get-Date).ToString('s')}
    $regProva[(Join-Path $radice 'escluso')] = @{stato='escluso';template_commit='abc1234'}
    $regProva[(Join-Path $radice 'allineato-vecchio')] = @{stato='allineato';template_commit='abc1234';rapporto=(Join-Path $primaDir 'prj.json')}
    [IO.File]::WriteAllText((Join-Path $tplProva '_notes/allineamento/registro.json'),(ConvertTo-Json $regProva -Depth 6),$utf8)
    $cli = (& powershell -NoProfile -ExecutionPolicy Bypass -File $PSCommandPath -Template $tplProva -SaltaPush 2>&1 | Out-String)
    Prova "la CLI include un progetto allineato con consegna precedente non committata" ($cli -match 'da committare' -and $cli -match 'file 1, lasciati 1')
    Prova "la CLI lascia escluso il progetto escluso" ($cli -notmatch 'escluso\s+(da committare|cartella sparita)')
    Prova "la CLI non riapre copie allineate assenti dall'ultima corsa" ($cli -notmatch 'allineato-vecchio\s+')
    & git -C $ripetuto diff --cached --quiet
    Prova "l'anteprima della CLI non mette file in stage" ($LASTEXITCODE -eq 0)

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

    # 11-13. un secondo remoto dichiarato riceve lo stesso ramo, ma mai con forza
    function Nudo([string]$nome) { $p = Join-Path $radice $nome; & git init -q --bare -b main $p 2>&1 | Out-Null; return $p }
    $up = Nudo 'up.git'; $altro = Nudo 'altro.git'
    $f = Nuovo-Repo 'dueremoti'
    Scrivi $f 'mio.md' "prima`n"
    & git -C $f add -A | Out-Null; & git -C $f commit -q -m 'base' | Out-Null
    & git -C $f remote add origin $up | Out-Null; & git -C $f remote add altro $altro | Out-Null
    & git -C $f push -q -u origin main 2>&1 | Out-Null; & git -C $f push -q altro main 2>&1 | Out-Null
    Scrivi $f 'mio.md' "cambiato`n"
    $rF = Chiudi-Progetto $f $rapA $MSG $true 1 $false $false $null @('altro')
    $testa = & git -C $f rev-parse HEAD
    Prova "il secondo remoto dichiarato riceve il commit" ((& git -C $altro rev-parse main) -eq $testa)
    Prova "l'upstream riceve il commit anche con un secondo remoto" ((& git -C $up rev-parse main) -eq $testa -and $rF.push -match '^spinto, altro spinto$')
    $g = Join-Path $radice 'divergente'
    & git clone -q $altro $g 2>&1 | Out-Null
    & git -C $g config user.name prova | Out-Null; & git -C $g config user.email prova@esempio.invalid | Out-Null
    Scrivi $g 'altrui.md' "altrove`n"; & git -C $g add -A | Out-Null; & git -C $g commit -q -m 'altrove' | Out-Null; & git -C $g push -q 2>&1 | Out-Null
    $diAltro = & git -C $altro rev-parse main
    Scrivi $f 'mio.md' "ancora`n"
    $rG = Chiudi-Progetto $f $rapA $MSG $true 1 $false $false $null @('altro')
    Prova "un secondo remoto divergente non si sovrascrive e il push risulta fallito" ((& git -C $altro rev-parse main) -eq $diAltro -and $rG.push -match 'altro push fallito')

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

# La stessa prova dello stage selettivo, ma su un progetto in una macchina via SSH:
# le prove qui sopra non passano mai dal trasporto, e un trasporto che cita male un
# percorso o perde un codice di uscita le lascerebbe verdi. Il repository di prova
# vive in ~/.cache della macchina e si cancella alla fine; nessun progetto si tocca.
function Esegui-AutotestSsh([string]$alias) {
  $script:casi = @()
  function Prova([string]$nome, [bool]$esito) { $script:casi += [pscustomobject]@{ nome = $nome; ok = $esito } }
  $dir = '.cache/autotest-chiudi-allineamento-' + [guid]::NewGuid().ToString('N').Substring(0, 8)
  $abs = @(Esegui-Ssh $alias ('d="$HOME/' + $dir + '"; mkdir -p "$d/.claude/norme" && cd "$d" && git init -q -b main && git config user.name prova && git config user.email prova@esempio.invalid && git config commit.gpgsign false && echo prima > "con spazio.md" && echo prima > suo.md && git add -A && git commit -q -m base && echo aggiornato > "con spazio.md" && echo altrui > suo.md && echo nuova > .claude/norme/nuova.md && echo "$d"'))
  if (-not $abs -or $abs[-1] -notlike '/*') { Write-Host "  KO  repository di prova non creato su $alias"; return 1 }
  $prj = "ssh://$alias" + $abs[-1]
  $rap = Join-Path ([System.IO.Path]::GetTempPath()) ("autotest-ssh-" + [guid]::NewGuid().ToString('N').Substring(0, 8) + '.json')
  try {
    [System.IO.File]::WriteAllText($rap, (ConvertTo-Json @(
      @{ file = 'con spazio.md'; template = 'con spazio.md'; esito = 'VECCHIO' },
      @{ file = '.claude/norme/nuova.md'; template = '.claude/norme/nuova.md'; esito = 'NUOVO' }) -Depth 3), $utf8)
    Prova 'il progetto remoto esiste visto dal trasporto' (Esiste $prj '' 'cartella')
    Prova 'un percorso remoto assente non esiste' (-not (Esiste $prj 'manca.md'))
    $r = Chiudi-Progetto $prj $rap "Allineamento dal template al commit abc1234" $true 1 $false $true $null
    $dentro = @(Invoca-Git $prj show --name-only --pretty=format: HEAD | Where-Object { $_ })
    Prova 'via ssh il file con uno spazio nel nome entra nel commit' ($dentro -contains 'con spazio.md')
    Prova 'via ssh il file nuovo in una cartella nuova entra nel commit' ($dentro -contains '.claude/norme/nuova.md')
    Prova "via ssh il file di un'altra sessione resta fuori" (-not ($dentro -contains 'suo.md'))
    Prova 'via ssh il commit porta il messaggio intero' ((@(Invoca-Git $prj log -1 --format=%s) -join '') -eq 'Allineamento dal template al commit abc1234')
    Prova 'via ssh esito e conteggi tornano giusti' ($r.esito -eq 'committato' -and $r.file -eq 2 -and $r.lasciati -eq 1)
    Prova 'via ssh un progetto senza upstream non ha remoto' (-not (Ha-Remoto $prj))
  }
  finally {
    Remove-Item -LiteralPath $rap -Force -ErrorAction SilentlyContinue
    $null = Esegui-Ssh $alias ('rm -rf "$HOME/' + $dir + '"')
  }
  $caduti = @($casi | Where-Object { -not $_.ok })
  foreach ($c in $casi) { $segno = 'ok'; if (-not $c.ok) { $segno = 'KO' }; Write-Host ("  {0}  {1}" -f $segno, $c.nome) }
  Write-Host ("{0} casi su {1}, {2} falliti" -f $casi.Count, $alias, $caduti.Count)
  if ($caduti) { return 1 }
  return 0
}

if ($Autotest) { exit (Esegui-Autotest) }
if ($AutotestSsh) { exit (Esegui-AutotestSsh $AutotestSsh) }

# --- guardie ----------------------------------------------------------------
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { Esci-Guardia 'git non e nel PATH' }
if (-not $Template) { $Template = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path }
if (-not (Test-Path -LiteralPath (Join-Path $Template '.claude\PROJECT-SYSTEM.md'))) { Esci-Guardia "$Template non sembra il template" }
$fileRegistro = Join-Path $Template '_notes\allineamento\registro.json'
$pushRemoti = Leggi-PushRemoti (Join-Path $Template '_notes\allineamento\push-remoti.txt')
if (-not (Test-Path -LiteralPath $fileRegistro)) { Esci-Guardia "registro assente: lanciare prima allinea-tutti.ps1 (${fileRegistro})" }

$registro = @{}
try { (Get-Content -LiteralPath $fileRegistro -Raw -Encoding UTF8 | ConvertFrom-Json).PSObject.Properties | ForEach-Object { $registro[$_.Name] = $_.Value } }
catch { Esci-Guardia 'registro illeggibile' }

# I vecchi allineato del registro possono riferirsi a copie non piu presenti.
$ultimaCorsa = @($registro.Values | Where-Object { $_.stato -in @('applicato', 'allineato') -and $_.rapporto } | ForEach-Object { Split-Path $_.rapporto -Parent } | Sort-Object | Select-Object -Last 1)
$voci = @()
foreach ($k in ($registro.Keys | Sort-Object)) {
  $v = $registro[$k]
  if ($v.stato -notin @('applicato', 'allineato')) { continue }
  if ($v.stato -eq 'allineato' -and (Split-Path $v.rapporto -Parent) -ne $ultimaCorsa[0]) { continue }
  $nome = Nome-Progetto $k
  if ($Solo -and -not ($Solo | Where-Object { $nome -like "*$_*" })) { continue }
  if ($Escludi | Where-Object { $nome -like "*$_*" }) { continue }
  $voci += [pscustomobject]@{ percorso = $k; nome = $nome; rapporto = $v.rapporto; commit = $v.template_commit; misurato = $v.misurato_il }
}
if (-not $voci) { Write-Host 'nessun progetto applicato o allineato nel registro: niente da chiudere'; exit 0 }

$msg = $Messaggio
if (-not $msg) { $msg = Messaggio-Predefinito ($voci[0].commit) }
if ($msg.Length -gt 72) { Esci-Guardia "messaggio oltre i 72 caratteri ($($msg.Length)): l'hook commit-msg lo rifiuterebbe" }

$modo = 'a vuoto'
if ($Applica) { $modo = 'applica' }
$cosa = 'commit e push'
if ($SoloPush) { $cosa = 'solo push' }
if ($SaltaPush) { $cosa = 'solo commit' }
Write-Host ("template {0}  registro {1} progetti applicati o allineati" -f $Template, $voci.Count)
Write-Host ("modo: {0}   {1}   messaggio: {2}" -f $modo, $cosa, $msg)

# Lo stage si fonda su quali file la passata ha scritto, non su quali modifiche
# ha fatto: un file che un'altra sessione ha riadattato dopo la corsa risulta
# comunque nostro. L'eta' della corsa e' quindi parte della misura, e si dichiara.
$misure = @($voci | ForEach-Object { $_.misurato } | Where-Object { $_ } | Sort-Object)
if ($misure) {
  $ultima = [datetime]::Parse($misure[-1], [Globalization.CultureInfo]::InvariantCulture)
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
  $altri = @(); $kp = $v.percorso.TrimEnd('\', '/').ToLowerInvariant(); if ($pushRemoti.ContainsKey($kp)) { $altri = $pushRemoti[$kp] }
  $r = Chiudi-Progetto $v.percorso $v.rapporto $msg ([bool]$Applica) $Tentativi ([bool]$SoloPush) ([bool]$SaltaPush) $null $altri
  $esiti += $r
  $coda = ''
  if ($r.commit) { $coda = $r.commit }
  if ($r.tentativi -gt 1) { $coda = "$coda ($($r.tentativi) tentativi)" }
  Write-Host ('{0,-42} {1,-22} {2,-10} {3,-22} file {4}, lasciati {5}' -f $v.nome, $r.esito, $coda, $r.push, $r.file, $r.lasciati)
}

Write-Host ''
$falliti = @($esiti | Where-Object { $_.push -match 'push fallito' -or $_.esito -in @('commit rifiutato', 'git add fallito', 'rapporto mancante', 'non e un repository', 'head staccato', 'cartella sparita') })
$committati = @($esiti | Where-Object { $_.esito -eq 'committato' })
$spinti = @($esiti | Where-Object { $_.push -match '^spinto' })
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
