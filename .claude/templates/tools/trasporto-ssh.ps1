<#
.SYNOPSIS
Trasporto comune di allinea-tutti.ps1 e chiudi-allineamento.ps1: fa girare la stessa
operazione su un progetto locale o su un progetto dentro una macchina raggiungibile
con un alias SSH.

.DESCRIPTION
Si carica con il punto, non si lancia da solo. Un progetto remoto si scrive
ssh://<alias>/<percorso assoluto>, dove l'alias e' una voce Host di ~/.ssh/config;
un progetto locale resta un percorso di Windows. Ogni funzione qui sotto accetta
l'uno e l'altro, cosi' i due script hanno una sola logica e non una copia per le
macchine virtuali, che invecchierebbe per conto suo.

Perche' esiste. Fino al 19/10/2026 la passata guardava solo le radici locali, e i
progetti istanziati dentro le macchine raggiungibili via SSH non erano mai stati
allineati: misurato quel giorno, sette progetti su sei macchine, nessuno con il
marcatore .claude/allineamento-template.json, e nessun conteggio li nominava
perche' la scoperta non li vedeva.

Il comando remoto viaggia in base64 dentro una sola riga: Windows PowerShell 5.1
non protegge le virgolette doppie negli argomenti di un eseguibile e, in una pipe
verso un eseguibile, converte il testo nella codifica della console e aggiunge un
CR a ogni riga. Con il base64 nessuna delle due cose puo' toccare il comando. Gli
argomenti si citano con l'apice singolo della shell POSIX, l'unica citazione che
non interpreta niente.

Il template sulla macchina remota vive in ~/.cache/template-claude-developing,
con la sua storia, perche' allinea-dal-template.py decide dalla storia git del
template. Ci arriva come git bundle, solo quando il suo HEAD non coincide con
quello locale. E' una copia di servizio: non e' un progetto e non si allinea.
#>

$script:SSH_OPZIONI = @('-o', 'BatchMode=yes', '-o', 'ConnectTimeout=8', '-o', 'ServerAliveInterval=15')
$script:TPL_REMOTO = '.cache/template-claude-developing'

function Test-Remoto([string]$prj) { return $prj -match '^ssh://[^/]+/' }

function Dividi-Remoto([string]$prj) {
  if ($prj -notmatch '^ssh://([^/]+)(/.*)$') { throw "non e' un progetto remoto: $prj" }
  return [pscustomobject]@{ alias = $Matches[1]; percorso = $Matches[2].TrimEnd('/') }
}

# Apice singolo POSIX: dentro non si interpreta niente, e l'apice stesso si chiude,
# si scrive protetto e si riapre.
function Q([string]$s) { return "'" + $s.Replace("'", "'\''") + "'" }

# ConnectTimeout copre solo l'apertura della connessione, e ServerAliveInterval solo
# una rete caduta: un comando che sulla macchina remota non torna mai, come un test
# su un disco bloccato, teneva ferma l'intera passata. Il 2026-10-27 un controllo su
# vm207 e' rimasto appeso per mezz'ora. Il comando gira quindi sotto timeout remoto,
# dove esiste, e oltre il tempo la macchina risulta non raggiunta invece di bloccare.
$script:SSH_TEMPO_MASSIMO = 300

function Comando-Ssh([string]$comando) {
  $b64 = [Convert]::ToBase64String((New-Object System.Text.UTF8Encoding $false).GetBytes($comando))
  return "echo $b64 | base64 -d | { if command -v timeout >/dev/null 2>&1; then timeout $($script:SSH_TEMPO_MASSIMO) bash; else bash; fi; }"
}

function Esegui-Ssh([string]$alias, [string]$comando) {
  $out = & ssh @script:SSH_OPZIONI $alias (Comando-Ssh $comando) 2>$null
  return $out
}

# Esegue un programma con la cartella del progetto come cartella corrente: in
# locale con Push-Location, in remoto con un cd. Ogni argomento si cita da se'.
function Esegui-In([string]$prj, [string]$programma, [string[]]$argomenti) {
  if (Test-Remoto $prj) {
    $r = Dividi-Remoto $prj
    $riga = 'cd ' + (Q $r.percorso) + ' && ' + $programma + ' ' + (($argomenti | ForEach-Object { Q $_ }) -join ' ') + ' 2>&1'
    return Esegui-Ssh $r.alias $riga
  }
  Push-Location -LiteralPath $prj
  try { $out = & $programma @argomenti 2>&1 } finally { Pop-Location }
  return $out
}

# Non si chiama Git: in PowerShell una funzione con quel nome copre git.exe e
# richiamerebbe se stessa all'infinito.
function Invoca-Git([string]$repo) {
  if (Test-Remoto $repo) {
    $r = Dividi-Remoto $repo
    $riga = 'git -C ' + (Q $r.percorso) + ' ' + (($args | ForEach-Object { Q ([string]$_) }) -join ' ') + ' 2>/dev/null'
    return Esegui-Ssh $r.alias $riga
  }
  $out = & git -C $repo @args 2>$null
  return $out
}

# Come Invoca-Git, ma con lo stderr nell'uscita: serve dove un rifiuto va letto.
function Invoca-GitTutto([string]$repo) {
  if (Test-Remoto $repo) {
    $r = Dividi-Remoto $repo
    $riga = 'git -C ' + (Q $r.percorso) + ' ' + (($args | ForEach-Object { Q ([string]$_) }) -join ' ') + ' 2>&1'
    return Esegui-Ssh $r.alias $riga
  }
  $out = & git -C $repo @args 2>&1
  return $out
}

function Nome-Progetto([string]$prj) {
  if (Test-Remoto $prj) { $r = Dividi-Remoto $prj; return $r.alias + ':' + ($r.percorso -split '/')[-1] }
  return Split-Path $prj -Leaf
}

# Tipo: 'qualunque', 'file' o 'cartella'.
function Esiste([string]$prj, [string]$rel, [string]$tipo = 'qualunque') {
  if (Test-Remoto $prj) {
    $r = Dividi-Remoto $prj
    $f = switch ($tipo) { 'file' { '-f' } 'cartella' { '-d' } default { '-e' } }
    $percorso = if ($rel) { $r.percorso + '/' + $rel.Replace('\', '/').TrimStart('/') } else { $r.percorso }
    $out = Esegui-Ssh $r.alias ("test $f " + (Q $percorso) + ' && echo SI || echo NO')
    return (@($out) -contains 'SI')
  }
  $p = if ($rel) { Join-Path $prj ($rel -replace '/', '\') } else { $prj }
  switch ($tipo) {
    'file' { return Test-Path -LiteralPath $p -PathType Leaf }
    'cartella' { return Test-Path -LiteralPath $p -PathType Container }
    default { return Test-Path -LiteralPath $p }
  }
}

function Leggi-Testo([string]$prj, [string]$rel) {
  if (Test-Remoto $prj) {
    $r = Dividi-Remoto $prj
    $out = Esegui-Ssh $r.alias ('cat ' + (Q ($r.percorso + '/' + $rel.Replace('\', '/'))) + ' 2>/dev/null')
    return (@($out) -join "`n")
  }
  $p = Join-Path $prj ($rel -replace '/', '\')
  if (-not (Test-Path -LiteralPath $p)) { return '' }
  return Get-Content -LiteralPath $p -Raw -Encoding UTF8
}

function Scrivi-Testo([string]$prj, [string]$rel, [string]$testo) {
  if (Test-Remoto $prj) {
    $r = Dividi-Remoto $prj
    $b64 = [Convert]::ToBase64String((New-Object System.Text.UTF8Encoding $false).GetBytes($testo))
    $out = Esegui-Ssh $r.alias ("echo $b64 | base64 -d > " + (Q ($r.percorso + '/' + $rel.Replace('\', '/'))) + ' && echo SCRITTO')
    return (@($out) -contains 'SCRITTO')
  }
  [System.IO.File]::WriteAllText((Join-Path $prj ($rel -replace '/', '\')), $testo, (New-Object System.Text.UTF8Encoding $false))
  return $true
}

function Copia-Su([string]$alias, [string]$locale, [string]$remoto) {
  & scp -q @script:SSH_OPZIONI $locale "${alias}:$remoto" 2>$null | Out-Null
  return ($LASTEXITCODE -eq 0)
}

function Copia-Giu([string]$alias, [string]$remoto, [string]$locale) {
  & scp -q @script:SSH_OPZIONI "${alias}:$remoto" $locale 2>$null | Out-Null
  return ($LASTEXITCODE -eq 0)
}

# Gli alias di ~/.ssh/config che possono ospitare progetti: le voci Host senza
# caratteri jolly, tolte quelle che puntano a GitHub, che sono identita' per il push
# e non macchine. Il testo si passa per poterlo provare senza toccare il file vero.
function Host-Ssh([string]$testo = $null) {
  if ($null -eq $testo -or $testo -eq '') {
    $f = Join-Path $env:USERPROFILE '.ssh\config'
    if (-not (Test-Path -LiteralPath $f)) { return @() }
    $testo = Get-Content -LiteralPath $f -Raw
  }
  $voci = New-Object System.Collections.ArrayList; $correnti = @()
  foreach ($riga in ($testo -split "`r?`n")) {
    $t = $riga.Trim()
    if ($t -match '^(?i)Host\s+(.+)$') {
      foreach ($c in $correnti) { [void]$voci.Add($c) }
      $correnti = @($Matches[1].Trim() -split '\s+' | Where-Object { $_ -notmatch '[*?!]' } |
        ForEach-Object { [pscustomobject]@{ alias = $_; hostname = $_ } })
    }
    elseif ($t -match '^(?i)HostName\s+(\S+)') { foreach ($c in $correnti) { $c.hostname = $Matches[1] } }
    elseif ($t -match '^(?i)Match\s') { foreach ($c in $correnti) { [void]$voci.Add($c) }; $correnti = @() }
  }
  foreach ($c in $correnti) { [void]$voci.Add($c) }
  return @($voci | Where-Object { $_.hostname -notmatch '(^|\.)github\.com$' -and $_.alias -notmatch '^github' } |
    ForEach-Object { $_.alias } | Select-Object -Unique)
}

# Cerca sulla macchina i progetti istanziati (P) e le cartelle con .claude ma senza
# PROJECT-SYSTEM.md (Q), sotto le radici date e fino alla profondita' data. Dice
# anche se git e python3 ci sono, perche' senza l'uno o l'altro la macchina non si
# puo' allineare e va detto, non saltato.
function Scopri-Remoti([string]$alias, [string[]]$radici, [int]$profondita = 5) {
  $lista = ($radici | ForEach-Object { if ($_ -eq '~') { '"$HOME"' } else { Q $_ } }) -join ' '
  $cmd = "command -v git >/dev/null && command -v python3 >/dev/null && echo STRUMENTI || echo SENZA-STRUMENTI`n" +
    "for d in $lista; do [ -d `"`$d`" ] && find `"`$d`" -maxdepth $profondita -type d -name .claude -not -path '*/node_modules/*' -not -path '*/.cache/*' 2>/dev/null; done | sort -u | while read -r c; do`n" +
    "  p=`$(dirname `"`$c`")`n" +
    "  case `"`$p`" in */.claude/*) continue;; esac`n" +
    "  if [ -f `"`$c/PROJECT-SYSTEM.md`" ]; then echo `"P `$p`"; else echo `"Q `$p`"; fi`n" +
    "done"
  $out = @(Esegui-Ssh $alias ('echo "H $HOME"' + "`n" + $cmd))
  $raggiunto = ($out -contains 'STRUMENTI') -or ($out -contains 'SENZA-STRUMENTI')
  $casa = @($out | Where-Object { $_ -like 'H /*' } | ForEach-Object { $_.Substring(2) }) | Select-Object -First 1
  $progetti = @($out | Where-Object { $_ -like 'P /*' } | ForEach-Object { $_.Substring(2) })
  $parziali = @($out | Where-Object { $_ -like 'Q /*' } | ForEach-Object { $_.Substring(2) } |
    Where-Object { -not (Parziale-Rumore $_ $casa $progetti) })
  return [pscustomobject]@{
    alias = $alias; raggiunto = $raggiunto; strumenti = ($out -contains 'STRUMENTI')
    progetti = @($progetti | ForEach-Object { "ssh://$alias" + $_ })
    parziali = @($parziali | ForEach-Object { "ssh://$alias" + $_ })
  }
}

# Una cartella con .claude ma senza PROJECT-SYSTEM.md e' rumore, non un progetto da
# istanziare, in tre casi misurati alla prima passata via SSH del 2026-10-19, che ne
# aveva elencate sette su quattro macchine e nessuna era un progetto: la home di un
# utente, perche' ~/.claude e' la configurazione di Claude Code; un percorso con una
# cartella nascosta, come le estensioni di un editor; e una cartella dentro un progetto
# gia' trovato, che appartiene a quel progetto. Il confronto con la home si fa anche
# sulle altre home sotto /home, che la scoperta attraversa.
function Parziale-Rumore([string]$p, [string]$casa, [string[]]$progetti) {
  if ($casa -and $p -eq $casa) { return $true }
  if ($p -match '^/home/[^/]+$' -or $p -eq '/root') { return $true }
  if ($p -match '/\.[^/]') { return $true }
  foreach ($q in $progetti) { if ($p.StartsWith($q + '/')) { return $true } }
  return $false
}

# Porta il template sulla macchina allo stesso commit di quello locale e restituisce
# il percorso assoluto della copia remota, oppure $null con il motivo in
# $script:ErroreTemplate. Non tocca nient'altro che ~/.cache/template-claude-developing.
function Prepara-Template([string]$alias, [string]$tpl, [string]$tplHead) {
  $script:ErroreTemplate = ''
  $stato = @(Esegui-Ssh $alias ('d="$HOME/' + $script:TPL_REMOTO + '"; echo "$d"; git -C "$d" rev-parse HEAD 2>/dev/null || echo ASSENTE'))
  if ($stato.Count -lt 2) { $script:ErroreTemplate = 'ssh non risponde'; return $null }
  $assoluto = $stato[0]
  if ($stato[1] -eq $tplHead) { return $assoluto }
  $bundle = Join-Path ([System.IO.Path]::GetTempPath()) ('tcd-' + $tplHead.Substring(0, 12) + '.bundle')
  if (-not (Test-Path -LiteralPath $bundle)) {
    & git -C $tpl bundle create $bundle HEAD 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { $script:ErroreTemplate = 'git bundle fallito'; return $null }
  }
  $null = Esegui-Ssh $alias 'mkdir -p "$HOME/.cache"'
  if (-not (Copia-Su $alias $bundle '.cache/template-claude-developing.bundle')) { $script:ErroreTemplate = 'scp del bundle fallito'; return $null }
  $cmd = 'd="$HOME/' + $script:TPL_REMOTO + '"; b="$HOME/.cache/template-claude-developing.bundle"; ' +
    'if [ -d "$d/.git" ]; then git -C "$d" fetch -q "$b" HEAD; else rm -rf "$d" && git clone -q --no-checkout "$b" "$d"; fi && ' +
    'git -C "$d" checkout -q -f --detach ' + $tplHead + ' && rm -f "$b" && git -C "$d" rev-parse HEAD'
  $fine = @(Esegui-Ssh $alias $cmd)
  if (-not $fine -or $fine[-1] -ne $tplHead) { $script:ErroreTemplate = 'il template remoto non e arrivato al commit atteso'; return $null }
  return $assoluto
}

# Elenco di percorsi con motivo, uno per riga, il motivo dopo il cancelletto. I
# percorsi locali si normalizzano alla barra di Windows, quelli ssh:// restano come
# sono; la chiave e' in minuscolo per il confronto.
function Leggi-Elenco([string]$file) {
  $elenco = @{}
  if (-not (Test-Path -LiteralPath $file)) { return $elenco }
  foreach ($r in (Get-Content -LiteralPath $file -Encoding UTF8)) {
    $t = $r.Trim()
    if (-not $t -or $t.StartsWith('#')) { continue }
    $parti = $t -split '#', 2
    $percorso = $parti[0].Trim()
    if ($percorso -match '^ssh://') { $percorso = $percorso.TrimEnd('/') }
    else { $percorso = $percorso.TrimEnd([char]92, [char]47).Replace([string][char]47, [string][char]92) }
    $motivo = if ($parti.Count -gt 1) { $parti[1].Trim() } else { 'senza motivo' }
    $elenco[$percorso.ToLowerInvariant()] = $motivo
  }
  return $elenco
}

# Un progetto e' nell'elenco se c'e' il suo percorso o, per un remoto, il suo host
# intero nella forma ssh://alias.
function In-Elenco($elenco, [string]$prj) {
  $k = $prj.TrimEnd('\', '/').ToLowerInvariant()
  if ($elenco.ContainsKey($k)) { return $elenco[$k] }
  if (Test-Remoto $prj) { $h = 'ssh://' + (Dividi-Remoto $prj).alias.ToLowerInvariant(); if ($elenco.ContainsKey($h)) { return $elenco[$h] } }
  return $null
}
