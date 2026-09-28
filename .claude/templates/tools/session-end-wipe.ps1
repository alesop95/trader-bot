# ============================================================================
# session-end-wipe.ps1  (TEMPLATE)
# Wipe del magazzino nascosto di Claude Code, eseguito da un hook SessionEnd a
# OGNI chiusura di sessione dell'account. Mantiene il magazzino nascosto pulito
# nel tempo, senza dover lanciare comandi a mano.
#
# QUESTO TEMPLATE NON PARTE FINCHE' NON E' STATO COMPILATO. I segnaposto
# <CLAUDE_CONFIG_DIR> e <KEEP_PREFIXES> sono deliberatamente non funzionanti: uno
# script che cancella non deve avere un default che funziona, perche' un default
# giusto su una macchina e' un default sbagliato su tutte le altre, e il modo in cui
# sbaglia e' silenzioso. I prefissi di questa macchina non si indovinano e non si
# ereditano da un'altra installazione: si leggono con -List. Vedi il blocco 0.
#
# Installazione per-account (vedi PROJECT-SYSTEM.md sezione 15):
#   1. copia questo file in <CLAUDE_CONFIG_DIR>\hooks\session-end-wipe.ps1
#      e, accanto, scrub-claude-json.js preso dalla stessa cartella del template
#   2. scopri quali slug esistono davvero in questo account, senza inventarli:
#        powershell -NoProfile -ExecutionPolicy Bypass -File session-end-wipe.ps1 -List
#      il comando non cancella nulla e stampa gli slug presenti marcati KEEP o WIPE,
#      con la radice da cui derivano: e' da li' che si decide chi sono 'D--' ed 'E--'
#      su QUESTA macchina, che non sono gli stessi di un'altra
#   3. sostituisci i segnaposto <CLAUDE_CONFIG_DIR>, <KEEP_PREFIXES> e
#      <KEEP_PATH_PREFIXES> qui sotto
#   4. prova a vuoto, che non rimuove niente e stampa cosa farebbe:
#        powershell -NoProfile -ExecutionPolicy Bypass -File session-end-wipe.ps1 -DryRun
#   5. registra l'hook in <CLAUDE_CONFIG_DIR>\settings.json:
#        "hooks": { "SessionEnd": [ { "hooks": [ {
#          "type": "command",
#          "command": "powershell.exe -NoProfile -ExecutionPolicy Bypass -File \"<CLAUDE_CONFIG_DIR>\\hooks\\session-end-wipe.ps1\""
#        } ] } ] }
#      Nella home di default, che non ha settings.json, l'hook si registra in
#      settings.local.json.
#
# COSA PRESERVA, sempre:
#   - configurazione, login, skill, plugin: settings.json, .credentials.json,
#     skills\, plugins\, hooks\, daemon\  -> mai toccati
#   - di .claude.json si rimuovono SOLO le voci 'projects' dei percorsi non
#     preservati: login e configurazione restano intatti (vedi blocco 4)
#   - i file dei progetti su disco (E:\, D:\, ...) -> mai toccati: si agisce
#     solo dentro la home dell'account e nello scratchpad temporaneo.
#
# $keepPrefixes: QUALI TRASCRIZIONI SI SALVANO, e la risposta giusta e' NESSUNA.
#
#   Ogni cartella sotto 'projects' e' lo slug di un percorso di lavoro, con i due
#   punti e le barre sostituiti da trattini: 'E--mio-progetto' sta per
#   'E:\mio-progetto'. Dentro NON c'e' nulla del progetto: ci sono solo i verbali
#   delle conversazioni avvenute li'. La cartella si chiama come il progetto e
#   non lo contiene, ed e' esattamente per questo che la si preserva per sbaglio.
#
#   La memoria di un progetto vive DENTRO il progetto, versionata: .claude/memory/,
#   il work-log, il diario, il resume-prompt. E' la regola 'token-economy', alla
#   voce su cio' che non si fa: non si accumula stato fuori dal progetto. Una
#   trascrizione che sopravvive qui e' precisamente quello, cioe' memoria fuori
#   dal progetto, non versionata, non ispezionabile, che nessuno rileggera'.
#
#   Ne segue che elencare qui i dischi di sviluppo e' il contrario di cio' che
#   sembra: non protegge la memoria dei progetti, conserva i doppioni proprio dei
#   progetti che la memoria ce l'hanno gia'. L'insieme corretto e' VUOTO, e ogni
#   prefisso aggiunto e' un'eccezione da giustificare per iscritto.
#
#   Se la ripresa di un lavoro dipende da una trascrizione conservata qui, il
#   difetto non e' nel wipe: e' che quel lavoro non ha lasciato traccia dove
#   doveva. La risposta non e' preservare la trascrizione, e' scrivere il file
#   di ripresa.
#
#   Cio' che si perde con l'insieme vuoto, detto per intero: la possibilita' di
#   riaprire una conversazione passata con --resume o --continue. Nient'altro.
#
# $keepPathPrefixes: e' un'ALTRA cosa, e di norma NON va svuotato.
#
#   Governa le voci 'projects' di .claude.json, che contengono impostazioni e non
#   conversazioni: permessi concessi, server MCP, la conferma 'mi fido di questa
#   cartella', piu' contatori d'uso. Svuotarlo fa ricomparire il dialogo di
#   fiducia a ogni progetto a ogni sessione. Le trascrizioni sono memoria, queste
#   sono configurazione: si trattano in modo diverso, e sono due parametri
#   distinti proprio per poterlo fare.
# ============================================================================
param(
  [switch]$DryRun,   # stampa cosa verrebbe rimosso, senza rimuovere niente
  [switch]$List      # sola lettura: elenca gli slug presenti marcati KEEP/WIPE
)
$ErrorActionPreference = 'SilentlyContinue'

# --- configurazione, da compilare all'installazione -------------------------
# $base: path assoluto della home dell'account. Lasciando il segnaposto, lo script lo
# risolve da CLAUDE_CONFIG_DIR e in sua mancanza da %USERPROFILE%\.claude, e comunque
# lo valida prima di toccare qualunque cosa.
$base = '<CLAUDE_CONFIG_DIR>'
# $keepPrefixes: prefissi degli slug da preservare. SPECIFICI DELLA MACCHINA, uno per
# ogni disco dove stanno i progetti di sviluppo. Su una macchina diversa da quella su
# cui il template e stato scritto NON sono 'D--' ed 'E--' per default: si leggono con
# -List e si scelgono insieme a chi la usa, perche' un prefisso mancante non preserva.
$keepPrefixes = @('<KEEP_PREFIXES>')
# $keepPathPrefixes: prefissi di PERCORSO da preservare dentro 'projects' di
# .claude.json (blocco 4). Su Windows si derivano dai prefissi slug ('D--' -> 'D:') e
# il segnaposto qui sotto attiva quella derivazione; su un'altra convenzione di percorsi
# vanno elencati a mano (es. @('/home/utente/dev')).
$keepPathPrefixes = @('<KEEP_PATH_PREFIXES>')
# Deroga esplicita alla guardia dell'insieme vuoto (blocco 0.3): si imposta a $true solo
# se si vuole davvero un account in cui NESSUN progetto e preservato.
$allowEmptyKeep = $false

# --- diario ------------------------------------------------------------------
# L'hook SessionEnd gira senza che nessuno ne veda l'output, quindi un rifiuto a partire
# sarebbe invisibile: l'esito dell'ultima corsa si scrive nella home dell'account.
$script:logFile = $null
function Write-Log($msg) {
  Write-Output $msg
  if ($script:logFile) { Add-Content -LiteralPath $script:logFile -Value $msg -Encoding utf8 }
}
function Stop-Wipe($msg) {
  Write-Log "ABORT: $msg"
  Write-Log 'Nessuna rimozione eseguita.'
  exit 1
}

# --- blocco 0: guardie, prima di qualunque rimozione ------------------------

# 0.1 dove sta davvero il magazzino. Un $base non risolto o non valido farebbe
# Remove-Item -Recurse su percorsi che non sono la home di un account, quindi si verifica
# che il posto esista e assomigli a un magazzino di Claude Code prima di toccarlo.
if ([string]::IsNullOrWhiteSpace($base) -or $base -match '<.*>') {
  $base = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $env:USERPROFILE '.claude' }
}
$base = $base.TrimEnd('\', '/')
if ([string]::IsNullOrWhiteSpace($base)) { Stop-Wipe 'base vuoto dopo la risoluzione.' }
if ($base -eq $env:USERPROFILE -or $base -match '^[A-Za-z]:[\\/]?$') {
  Stop-Wipe "base risolto a '$base', che non e' la home di un account Claude Code."
}
if (-not (Test-Path -LiteralPath $base)) {
  Stop-Wipe "base '$base' non esiste: controlla CLAUDE_CONFIG_DIR o sostituisci il segnaposto."
}
$looksLikeStore = @('projects', 'settings.json', 'settings.local.json', '.credentials.json') |
  Where-Object { Test-Path -LiteralPath (Join-Path $base $_) }
if (-not $looksLikeStore) {
  Stop-Wipe "base '$base' non contiene ne projects\ ne un settings.json: non sembra il magazzino di un account Claude Code."
}
$script:logFile = Join-Path $base 'session-end-wipe.log'
Set-Content -LiteralPath $script:logFile -Value '' -Encoding utf8
$mode = if ($List) { 'list' } elseif ($DryRun) { 'dry' } else { 'wipe' }
Write-Log ("session-end-wipe: {0}  modo={1}  base={2}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $mode, $base)

# 0.2 la configurazione e stata compilata. Il segnaposto non si sostituisce da solo, e un
# insieme di prefissi vuoto significherebbe "non preservare niente". La guardia non vale
# in modo -List, che e proprio il comando con cui si scopre che cosa configurare: li la
# mancanza si segnala e si prosegue in sola lettura.
# $allowEmptyKeep vale per ENTRAMBE le guardie sull'insieme vuoto, questa e la 0.3, e rende "non preservare niente" una scelta DICHIARATA, distinta dal
# silenzio di un segnaposto mai compilato. Senza la distinzione le due cose sono
# indistinguibili dal di dentro e hanno esiti opposti: una e corretta, l'altra e un
# wipe totale per distrazione. La prima e anche la forma normale, perche le cartelle
# sotto 'projects' non contengono i progetti ma i verbali delle conversazioni, e la
# memoria di un progetto vive dentro il progetto, versionata.
$keepPrefixes = @($keepPrefixes | Where-Object { $_ -and $_ -notmatch '<.*>' })
$keepConfigured = ([bool]$keepPrefixes) -or $allowEmptyKeep
if (-not $keepConfigured -and -not $List) {
  Stop-Wipe "keepPrefixes non compilato e $allowEmptyKeep non dichiarato. Esegui con -List per vedere gli slug presenti; se non si vuole preservare nulla, imposta $allowEmptyKeep = $true."
}

# 0.3 i prefissi parlano di QUESTA macchina. E la guardia che conta davvero: un insieme
# di prefissi corretto altrove non corrisponde a nessuno slug qui, l'insieme preservato
# risulta vuoto e il wipe cancellerebbe l'intero magazzino senza segnalare niente. Il
# caso tipico e un 'D--' portato su una macchina dove lo sviluppo sta altrove, o su
# Linux dove gli slug derivano da /home.
function Test-Keep($name) {
  foreach ($p in $keepPrefixes) { if ($name -like "$p*") { return $true } }
  return $false
}
$projects = Join-Path $base 'projects'
$all = @()
if (Test-Path -LiteralPath $projects) {
  $all = @(Get-ChildItem -LiteralPath $projects -Directory)
}
$keptList = @($all | Where-Object { Test-Keep $_.Name })
if ($List) {
  Write-Log "Slug presenti in ${projects} (sola lettura, nessuna rimozione):"
  if (-not $all) { Write-Log '  (nessuno)' }
  foreach ($d in $all) {
    $tag = if (Test-Keep $d.Name) { 'KEEP' } else { 'WIPE' }
    Write-Log ("  [{0}] {1}" -f $tag, $d.Name)
  }
  Write-Log ("Totale {0}, preservati {1}, da rimuovere {2}." -f $all.Count, $keptList.Count, ($all.Count - $keptList.Count))
  if ($keepConfigured) { Write-Log ("keepPrefixes attuali: {0}" -f ($keepPrefixes -join ' ')) }
  else {
    Write-Log "keepPrefixes non e ancora compilato: finche resta cosi lo script rifiuta di rimuovere."
    Write-Log 'Scegli i prefissi dagli slug qui sopra, uno per ogni radice di sviluppo da preservare.'
  }
  exit 0
}
if ($all.Count -gt 0 -and $keptList.Count -eq 0 -and -not $allowEmptyKeep) {
  Stop-Wipe ("nessuno dei {0} slug in {1} corrisponde a keepPrefixes ('{2}'): la configurazione e di un'altra macchina. Esegui con -List e correggi i prefissi; se l'insieme vuoto e voluto, imposta `$allowEmptyKeep = `$true." -f $all.Count, $projects, ($keepPrefixes -join ' '))
}
Write-Log ("Progetti: {0} totali, {1} preservati, {2} da rimuovere." -f $all.Count, $keptList.Count, ($all.Count - $keptList.Count))

# GUARDIA DI ULTIMA ISTANZA. Tutto lo script e gia costruito per agire solo dentro
# $base e dentro la radice degli scratchpad, ma "corretto per costruzione" non e una
# garanzia: basta una riga sbagliata in una modifica futura perche una rimozione
# ricorsiva finisca su una cartella di progetto. Qui il perimetro smette di essere una
# proprieta del codice e diventa un controllo, secondo la sezione 17 del sistema.
# Qualunque percorso fuori dalle due radici consentite ferma lo script invece di essere
# rimosso: un wipe che si ferma e un fastidio, un wipe che sbaglia bersaglio e un danno
# non reversibile. Le cartelle di lavoro dei progetti, _notes/ compresa, vivono su altri
# dischi e non possono in nessun caso corrispondere.
$script:sep = [System.IO.Path]::DirectorySeparatorChar
$script:radiciConsentite = @($base, (Join-Path $env:LOCALAPPDATA (Join-Path 'Temp' 'claude')))
function Test-DentroPerimetro($path) {
  # Niente backslash letterali in questa funzione: si usa DirectorySeparatorChar.
  # Un separatore perso in una modifica futura renderebbe il confronto un semplice
  # prefisso di stringa, e '...account30' risulterebbe dentro '...account3'.
  $pieno = [System.IO.Path]::GetFullPath($path).TrimEnd($script:sep)
  foreach ($r in $script:radiciConsentite) {
    if ([string]::IsNullOrWhiteSpace($r)) { continue }
    $radice = [System.IO.Path]::GetFullPath($r).TrimEnd($script:sep)
    if ($pieno -eq $radice) { return $true }
    if ($pieno.StartsWith($radice + $script:sep, [StringComparison]::OrdinalIgnoreCase)) { return $true }
  }
  return $false
}

function Remove-Target($path) {
  if (-not (Test-Path -LiteralPath $path)) { return }
  if (-not (Test-DentroPerimetro $path)) {
    Stop-Wipe ("RIFIUTO: '{0}' e fuori dalle radici consentite ({1}). Nessuna rimozione oltre questo punto." -f $path, ($script:radiciConsentite -join ' ; '))
  }
  if ($DryRun) { Write-Log "  [dry-run] Remove-Item -Recurse -Force $path" }
  else { Remove-Item -LiteralPath $path -Recurse -Force }
}

# --- 1) progetti: rimuovi transcript + memoria nascosta di tutto tranne i prefissi preservati ---
foreach ($d in $all) {
  if (Test-Keep $d.Name) { continue }
  Remove-Target $d.FullName
}

# --- 2) store per-account effimeri ---
# Per conservare resume/undo dei progetti preservati tra una sessione e l'altra,
# commenta le voci che vuoi mantenere (es. 'sessions','file-history').
# NB: 'daemon', 'skills', 'plugins', 'hooks' NON sono in lista: sono stato vivo o
# configurazione, non residui di sessione.
$ephemeral = @('sessions','session-env','shell-snapshots','file-history',
               'plans','tasks','paste-cache','backups','memory',
               'cache','jobs','ide','todos','statsig','telemetry')
foreach ($e in $ephemeral) { Remove-Target (Join-Path $base $e) }
Remove-Target (Join-Path $base 'history.jsonl')
Remove-Target (Join-Path $base 'mcp-needs-auth-cache.json')

# --- 3) scratchpad temporanei: %LOCALAPPDATA%\Temp\claude\<slug-progetto> ---
# Claude Code tiene qui scratchpad e output dei task, uno slug per progetto e una
# sottocartella per sessione. Questa radice e' condivisa fra tutti gli account della
# stessa utenza Windows, quindi il passaggio e' idempotente: chiunque chiuda per ultimo
# la ripulisce. Si rimuovono solo le cartelle che sembrano slug di progetto (regex
# '^[A-Za-z]--'), cosi' da non toccare 'bundled-skills' e simili.
$tmpRoot = Join-Path $env:LOCALAPPDATA 'Temp\claude'
if (Test-Path -LiteralPath $tmpRoot) {
  Get-ChildItem -LiteralPath $tmpRoot -Directory |
    Where-Object { ($_.Name -match '^[A-Za-z]--') -and -not (Test-Keep $_.Name) } |
    ForEach-Object { Remove-Target $_.FullName }
}

# --- 4) .claude.json: rimuovi le voci 'projects' dei percorsi non preservati ---
# Senza questo passaggio l'elenco dei percorsi aperti sopravvive al wipe. Il file
# custodisce login e configurazione, quindi la modifica e' delegata a
# scrub-claude-json.js: ConvertFrom-Json di PowerShell 5.1 non e' utilizzabile qui,
# perche' considera le chiavi case-insensitive e va in errore su un .claude.json che
# contenga sia 'e:/progetto' sia 'E:/progetto'. Se Node non c'e', il passaggio si
# salta senza toccare il file. Si ripulisce anche l'eventuale .backup, che altrimenti
# conserverebbe le stesse voci.
# Percorso di .claude.json: con CLAUDE_CONFIG_DIR impostato sta DENTRO la home
# dell'account; nella home di default sta invece accanto ad essa, in $HOME\.claude.json.
$cfgFile = Join-Path $base '.claude.json'
if (-not (Test-Path -LiteralPath $cfgFile)) {
  $alt = Join-Path $env:USERPROFILE '.claude.json'
  if (Test-Path -LiteralPath $alt) { $cfgFile = $alt }
}
# I prefissi di percorso: se il segnaposto e ancora li, si derivano dai prefissi slug,
# ma SOLO per quelli in forma 'X--' che sono davvero una lettera di disco. Un prefisso
# di altra forma non ha una derivazione ovvia, e piuttosto che inventarne una sbagliata
# il blocco si salta lasciando .claude.json intatto.
$keepPathPrefixes = @($keepPathPrefixes | Where-Object { $_ -and $_ -notmatch '<.*>' })
if (-not $keepPathPrefixes) {
  $derivabili = @($keepPrefixes | Where-Object { $_ -match '^[A-Za-z]--' })
  if ($derivabili.Count -eq $keepPrefixes.Count) {
    $keepPathPrefixes = @($derivabili | ForEach-Object { $_.Substring(0,1) + ':' })
  }
}
if (-not $keepPathPrefixes) {
  Write-Log 'Blocco 4 saltato: keepPathPrefixes non compilato e non derivabile dai prefissi slug, .claude.json resta intatto.'
}
else {
  $scrubJs = Join-Path $base 'hooks\scrub-claude-json.js'
  $nodeExe = (Get-Command node -ErrorAction SilentlyContinue).Source
  if (-not $nodeExe) { $nodeExe = 'C:\Program Files\nodejs\node.exe' }
  if ((Test-Path $scrubJs) -and (Test-Path $nodeExe)) {
    foreach ($target in @($cfgFile, "$cfgFile.backup")) {
      if (-not (Test-Path -LiteralPath $target)) { continue }
      if ($DryRun) {
        Write-Log ("  [dry-run] node scrub-claude-json.js {0} {1}" -f $target, ($keepPathPrefixes -join ' '))
      }
      else {
        & $nodeExe $scrubJs $target @keepPathPrefixes | Out-Null
        # in caso di annullamento lo script non lascia residui, ma non costa nulla assicurarsene
        Remove-Item -LiteralPath "$target.tmp" -Force
      }
    }
  }
  else { Write-Log 'Blocco 4 saltato: scrub-claude-json.js o node non disponibili.' }
}

Write-Log 'Fatto.'
