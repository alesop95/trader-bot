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
#   - dal 2026-10-09 cio che appartiene a una sessione ancora aperta, di qualunque
#     account: si toglie tutto il resto subito, e quella si pulisce quando chiude
#     (blocco 0.4). Serve stato-magazzino.ps1 nella stessa cartella; senza, il wipe
#     rimanda tutto finche e aperta un'altra sessione.
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
  [switch]$List,     # sola lettura: elenca gli slug presenti marcati KEEP/WIPE
  [switch]$Forza,    # ignora le sessioni aperte: toglie anche cio che appartiene a loro
  # Solo per le prove (tools/tests/test-wipe-per-sessione.ps1): una home e una radice
  # temporanea finte al posto di quelle compilate. Nomi diversi da $base e $tmpRoot
  # perche' in PowerShell le variabili non distinguono maiuscole e minuscole.
  [string]$BaseProva,
  [string]$TempProva,
  [string]$McpProva,
  # Interno: la copia rilanciata dal modo hook attende la fine di questo PID (blocco 0.4).
  [int]$AttendiPid = 0,
  # Interno: la sessione che l'hook ha chiuso. E' chiusa con certezza, quindi non si
  # protegge nemmeno come candidata di un processo vivo senza file di sessione.
  [string]$SessioneChiusa
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
if ($BaseProva) { $base = $BaseProva }

# Modo hook o modo manuale. Lanciato dall'hook SessionEnd, lo script riceve sullo standard
# input il payload dell'evento, con hook_event_name e session_id: allora la sessione da
# cui discende e' quella che sta chiudendo, e si pulisce. Lanciato a mano, anche dal
# terminale integrato di una sessione aperta, quella sessione e' viva e si protegge come
# le altre. Il caso che ha imposto la distinzione, il 2026-10-09: una prova a vuoto
# lanciata da una sessione al lavoro avrebbe cancellato il verbale di quella stessa
# sessione, perche' fino ad allora ogni antenato contava come sessione in chiusura.
$script:payloadHook = $null
try {
  # La lettura ha un limite di due secondi: lanciato con uno standard input rediretto che
  # nessuno chiude, per esempio da una shell Bash, ReadToEnd aspetterebbe per sempre. E'
  # successo il 2026-10-09 durante le prove, con il wipe fermo per oltre sei minuti.
  # Claude Code scrive il payload e chiude l'ingresso subito, quindi due secondi bastano.
  $ingresso = $null
  if ([Console]::IsInputRedirected) {
    $lettura = [Console]::In.ReadToEndAsync()
    if ($lettura.Wait(2000)) { $ingresso = $lettura.Result }
  }
  if ($ingresso) {
    if ($ingresso.Trim()) {
      $o = $ingresso | ConvertFrom-Json
      if ($o.hook_event_name -eq 'SessionEnd') { $script:payloadHook = $o }
    }
  }
} catch { $script:payloadHook = $null }

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
# Le prove a vuoto e il modo -List scrivono in un diario a parte: dal 2026-10-10, dopo che il
# -List lanciato dal controllo di igiene aveva cancellato l'esito dell'ultima pulizia vera.
$script:logFile = if ($List -or $DryRun) { Join-Path $base 'session-end-wipe.prova.log' } else { Join-Path $base 'session-end-wipe.log' }
# La copia rilanciata dal modo hook continua il diario della corsa che l'ha lanciata.
if (-not $AttendiPid) { Set-Content -LiteralPath $script:logFile -Value '' -Encoding utf8 }
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

# 0.4 le sessioni ancora aperte. Storia, perche' spiega la forma attuale. Fino al
# 2026-10-05 il wipe cancellava tutto a ogni chiusura, compresi scratchpad, piani e task
# delle sessioni ANCORA APERTE di qualunque account, perche' la radice degli scratchpad
# (%LOCALAPPDATA%\Temp\claude) e comune a tutta l'utenza Windows: e' successo, e una
# sessione al lavoro se li e' visti sparire. Dal 2026-10-05 al 2026-10-09 il rimedio e'
# stato il rinvio totale, "chi chiude per ultimo pulisce", che pero' lasciava il magazzino
# a meta: con due account in uso insieme l'ultima a chiudere puliva solo il proprio, e il
# 2026-10-08 account1 aveva nove sessioni chiuse ferme da giorni per un PID mai attribuito.
#
# Dal 2026-10-09, su direttiva del proprietario, il wipe lavora PER SESSIONE: toglie
# subito tutto cio' che appartiene a sessioni chiuse e conserva soltanto cio' che
# appartiene a una sessione con un processo vivo. Quali siano lo decide stato-magazzino.ps1,
# caricato come libreria dalla stessa cartella, con le stesse regole con cui le mostra:
# sessione certa se esiste <account>\sessions\<pid>.json con lo stesso istante di avvio
# del processo; per un processo vivo senza file, i suoi primi tre candidati, finche' quel
# processo esiste. Cio' che non porta il nome di una sessione (piani, istantanee della
# shell, incollati, copie di .claude.json, cache) si conserva solo se scritto dopo l'avvio
# del processo vivo piu' vecchio. Senza la libreria si torna al rinvio totale, che e' il
# verso prudente. -Forza ignora le sessioni aperte e toglie tutto.
#
# Si contano i processi claude.exe di Claude Code (riga di comando, estensione dell'editor)
# e le installazioni via node; si escludono l'app desktop di claude.ai, che vive sotto
# WindowsApps e non e una sessione di Claude Code, i suoi processi ausiliari (--type=), e
# la catena di antenati di questo script, cioe la sessione che sta chiudendo e chi l'ha
# lanciata: quella sessione si pulisce, non si protegge.
function Get-AltreSessioniClaude([switch]$ConAntenati) {
  $tutti = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)
  $perPid = @{}
  foreach ($p in $tutti) { $perPid[[int]$p.ProcessId] = $p }
  $antenati = @{}
  $cur = [int]$PID
  $passi = 0
  while ($perPid.ContainsKey($cur) -and $passi -lt 64) {
    $antenati[$cur] = $true
    $cur = [int]$perPid[$cur].ParentProcessId
    $passi++
  }
  @($tutti | Where-Object {
    $cmd = [string]$_.CommandLine
    $exe = [string]$_.ExecutablePath
    $claudeCode = (($_.Name -eq 'claude.exe') -and ($exe -notmatch '\\WindowsApps\\') -and ($cmd -notmatch '--type=')) -or
                  (($_.Name -match '^node(\.exe)?$') -and ($cmd -match '@anthropic-ai[\\/]claude-code'))
    $claudeCode -and ($ConAntenati -or -not $antenati.ContainsKey([int]$_.ProcessId))
  })
}
$script:protezione = $null
$altre = @(Get-AltreSessioniClaude -ConAntenati:(-not $script:payloadHook))
# Il modo hook non lavora dentro l'hook. Osservato il 2026-10-09 alle 09:42 su account1: la
# prima corsa vera dall'hook ha scritto tre righe di diario e si e' fermata prima di
# rimuovere qualunque cosa, mentre le prove da terminale finivano in pochi secondi.
# Misurato lo stesso giorno con un hook sonda su Claude Code 2.1.294: l'hook di fine
# sessione viene interrotto dopo circa 1,4 secondi ("Hook cancelled"), e leggere i verbali
# per decidere che cosa proteggere costa di piu'. Si rilancia
# quindi lo script fuori dall'albero dei processi di Claude, con WMI, che lo crea come
# processo indipendente, e si esce subito. La copia rilanciata attende che il processo
# della sessione in chiusura sia uscito davvero, e solo allora pulisce: a quel punto
# quella sessione non e' piu' viva e non serve trattarla a parte, e Claude non puo' piu'
# riscrivere i suoi file dopo il wipe, che e' il caveat di tempi della sezione 15.
if ($script:payloadHook -and -not $DryRun -and -not $List -and -not $AttendiPid) {
  $perPidH = @{}
  foreach ($p in @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)) { $perPidH[[int]$p.ProcessId] = $p }
  $cur = [int]$PID; $passi = 0; $claudePid = 0
  while ($perPidH.ContainsKey($cur) -and $passi -lt 64) {
    if ($perPidH[$cur].Name -eq 'claude.exe' -or ([string]$perPidH[$cur].CommandLine -match '@anthropic-ai[\\/]claude-code')) { $claudePid = $cur; break }
    $cur = [int]$perPidH[$cur].ParentProcessId; $passi++
  }
  if ($claudePid) {
    $extra = ''
    if ($BaseProva) { $extra += (' -BaseProva "{0}"' -f $BaseProva) }
    if ($TempProva) { $extra += (' -TempProva "{0}"' -f $TempProva) }
    if ($McpProva) { $extra += (' -McpProva "{0}"' -f $McpProva) }
    if ($Forza) { $extra += ' -Forza' }
    if ($script:payloadHook.session_id -match '^[0-9a-fA-F-]{8,64}$') { $extra += (' -SessioneChiusa {0}' -f $script:payloadHook.session_id) }
    $riga = ('"{0}" -NoProfile -ExecutionPolicy Bypass -File "{1}" -AttendiPid {2}{3}' -f (Join-Path $PSHOME 'powershell.exe'), $PSCommandPath, $claudePid, $extra)
    $r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = $riga } -ErrorAction SilentlyContinue
    if ($r -and $r.ReturnValue -eq 0) {
      Write-Log ("Modo hook: SessionEnd della sessione {0} (motivo {1}). Rilanciato fuori dall'hook come PID {2}, che attende la fine del PID {3} e poi pulisce." -f $script:payloadHook.session_id, $script:payloadHook.reason, $r.ProcessId, $claudePid)
      exit 0
    }
    Write-Log ("Rilancio fuori dall'hook non riuscito (codice {0}): si prosegue qui, con il rischio di essere interrotti." -f $(if ($r) { $r.ReturnValue } else { 'nessuno' }))
  }
}
if ($AttendiPid) {
  $attesa = [Diagnostics.Stopwatch]::StartNew()
  while ((Get-Process -Id $AttendiPid -ErrorAction SilentlyContinue) -and $attesa.Elapsed.TotalSeconds -lt 120) { Start-Sleep -Milliseconds 250 }
  if (Get-Process -Id $AttendiPid -ErrorAction SilentlyContinue) {
    Write-Log ("Il PID {0} e ancora vivo dopo {1:N0} s: si pulisce comunque, e la sua sessione conta come aperta." -f $AttendiPid, $attesa.Elapsed.TotalSeconds)
  }
  else { Write-Log ("Modo distaccato: il PID {0} e uscito dopo {1:N1} s, si pulisce." -f $AttendiPid, $attesa.Elapsed.TotalSeconds) }
}
elseif ($script:payloadHook) { Write-Log ("Modo hook: SessionEnd della sessione {0} (motivo {1}), che si pulisce." -f $script:payloadHook.session_id, $script:payloadHook.reason) }
else { Write-Log 'Modo manuale: anche la sessione da cui eventualmente e stato lanciato conta come aperta.' }
if ($altre.Count -gt 0 -and -not $Forza) {
  $libreria = Join-Path $PSScriptRoot 'stato-magazzino.ps1'
  if (Test-Path -LiteralPath $libreria) {
    try {
      . $libreria -Libreria
      $magazzinoTutti = Read-Magazzino (Split-Path -Parent $base) $null
      $legamiTutti = @(Get-Legami @(Get-ProcessiClaude) $magazzinoTutti)
      if (-not $script:payloadHook) { foreach ($l in $legamiTutti) { $l.Processo.Proprio = $false } }
      $script:protezione = Get-Protezione $legamiTutti
      $chiusa = if ($SessioneChiusa) { $SessioneChiusa } elseif ($script:payloadHook) { [string]$script:payloadHook.session_id } else { '' }
      if ($chiusa -and $script:protezione.Ids.ContainsKey($chiusa)) {
        $script:protezione.Ids.Remove($chiusa)
        Write-Log ("La sessione {0} e quella chiusa dall'hook: non si protegge, anche se candidata di un processo senza file di sessione." -f $chiusa)
      }
    }
    catch { $script:protezione = $null; Write-Log ("Libreria stato-magazzino.ps1 non utilizzabile: {0}" -f $_.Exception.Message) }
  }
  if (-not $script:protezione) {
    Write-Log ("Rimandato: {0} altre sessioni di Claude Code aperte (PID {1}). Senza stato-magazzino.ps1 accanto a questo script non si sa che cosa appartenga a loro, e cancellare ora toglierebbe scratchpad e piani a sessioni ancora al lavoro: pulira l'ultima sessione che si chiude, oppure un'esecuzione manuale con -Forza." -f $altre.Count, (($altre | ForEach-Object { $_.ProcessId }) -join ', '))
    if (-not $DryRun) {
      Write-Log 'Nessuna rimozione eseguita.'
      exit 0
    }
    Write-Log '  [dry-run] in un''esecuzione reale lo script si fermerebbe qui; segue cio che farebbe con -Forza.'
  }
  else {
    $pz = $script:protezione
    Write-Log ("Sessioni aperte: {0} (PID {1}), di cui senza file di sessione: {2}. Si toglie cio che appartiene a sessioni chiuse." -f $pz.Vive.Count, ($pz.Vive -join ', '), $(if ($pz.Incerti) { $pz.Incerti -join ', ' } else { 'nessuna' }))
    Write-Log ("Conservate {0} sessioni, e cio che non porta il nome di una sessione se scritto dopo {1}:" -f $pz.Ids.Count, $pz.PrimoAvvio.ToString('yyyy-MM-dd HH:mm:ss'))
    foreach ($k in $pz.Ids.Keys) { Write-Log ("  {0}  ({1})" -f $k, $pz.Ids[$k]) }
  }
}
elseif ($altre.Count -gt 0) { Write-Log ("-Forza: {0} sessioni aperte ignorate (PID {1})." -f $altre.Count, (($altre | ForEach-Object { $_.ProcessId }) -join ', ')) }

# Un nome e' "di sessione" se inizia con un identificativo di sessione, intero o nella
# forma breve di otto cifre esadecimali che usa jobs\. Protetto se corrisponde a una
# sessione dell'insieme da conservare, in uno dei tre versi: uguale, prefisso breve
# dell'identificativo, oppure identificativo seguito da altro (todos\<id>-agent-<id>.json).
function Test-NomeDiSessione($nome) { return ($nome -match '^[0-9a-f]{8}(-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})?([-.].*)?$') }
function Test-Protetta($nome) {
  if (-not $script:protezione) { return $false }
  foreach ($id in $script:protezione.Ids.Keys) {
    if ($nome -eq $id -or $nome.StartsWith($id + '-') -or $nome.StartsWith($id + '.')) { return $true }
    if ($nome.Length -eq 8 -and $id.StartsWith($nome)) { return $true }
  }
  return $false
}
# Il momento piu' recente in cui qualcosa sotto un elemento e' stato scritto: la data di
# una cartella non cambia quando si scrive in una sua sottocartella.
function Get-UltimaScrittura($item) {
  $u = $item.LastWriteTime
  if ($item.PSIsContainer) {
    foreach ($f in @(Get-ChildItem -LiteralPath $item.FullName -Recurse -Force -ErrorAction SilentlyContinue)) { if ($f.LastWriteTime -gt $u) { $u = $f.LastWriteTime } }
  }
  return $u
}
# Per un progetto di un processo vivo senza file di sessione ma con account e cartella noti
# (stato-magazzino, Get-Protezione): l'avvio del processo, oppure $null.
function Get-AvvioSlug($chiave, [switch]$Comune) {
  if (-not $script:protezione) { return $null }
  $tab = if ($Comune) { $script:protezione.SlugComune } else { $script:protezione.SlugAccount }
  if (-not $tab) { return $null }
  $k = $chiave.ToLowerInvariant()
  if ($tab.ContainsKey($k)) { return $tab[$k] }
  return $null
}
function Test-Recente($item) {
  return ($script:protezione -and $script:protezione.PrimoAvvio -and $item.LastWriteTime -ge $script:protezione.PrimoAvvio)
}
# Decide un figlio di una cartella mista: per nome se e' di sessione, per data altrimenti.
function Test-DaConservare($item) {
  if (-not $script:protezione) { return $false }
  $nome = if ($item.PSIsContainer) { $item.Name } else { [IO.Path]::GetFileNameWithoutExtension($item.Name) }
  if (Test-NomeDiSessione $nome) { return (Test-Protetta $nome) }
  return (Test-Recente $item)
}

# GUARDIA DI ULTIMA ISTANZA. Tutto lo script e gia costruito per agire solo dentro
# $base e dentro la radice degli scratchpad, ma "corretto per costruzione" non e una
# garanzia: basta una riga sbagliata in una modifica futura perche una rimozione
# ricorsiva finisca su una cartella di progetto. Qui il perimetro smette di essere una
# proprieta del codice e diventa un controllo, secondo la sezione 17 del sistema.
# Qualunque percorso fuori dalle due radici consentite ferma lo script invece di essere
# rimosso: un wipe che si ferma e un fastidio, un wipe che sbaglia bersaglio e un danno
# non reversibile. Le cartelle di lavoro dei progetti, _notes/ compresa, vivono su altri
# dischi e non possono in nessun caso corrispondere.
$tmpRoot = if ($TempProva) { $TempProva.TrimEnd('\', '/') } else { Join-Path $env:LOCALAPPDATA 'Temp\claude' }
$mcpRoot = if ($McpProva) { $McpProva.TrimEnd('\', '/') } elseif ($TempProva) { $null } else { Join-Path $env:LOCALAPPDATA 'claude-cli-nodejs\Cache' }
$script:sep = [System.IO.Path]::DirectorySeparatorChar
$script:radiciConsentite = @($base, $tmpRoot, $mcpRoot) | Where-Object { $_ }
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

$script:rimossi = 0
$script:conservati = 0
$script:perCategoria = [ordered]@{}
# La categoria di un percorso, per il riepilogo del diario: il primo livello sotto la home
# dell'account, oppure scratchpad e log MCP per le due radici comuni.
function Get-Categoria($path) {
  $pieno = [System.IO.Path]::GetFullPath($path)
  foreach ($coppia in @(@($tmpRoot, 'scratchpad'), @($mcpRoot, 'log MCP'))) {
    if ($coppia[0] -and $pieno.StartsWith([System.IO.Path]::GetFullPath($coppia[0]).TrimEnd($script:sep) + $script:sep, [StringComparison]::OrdinalIgnoreCase)) { return $coppia[1] }
  }
  $rel = $pieno.Substring([System.IO.Path]::GetFullPath($base).TrimEnd($script:sep).Length).TrimStart($script:sep)
  return ($rel -split [regex]::Escape([string]$script:sep))[0]
}
function Remove-Target($path) {
  if (-not (Test-Path -LiteralPath $path)) { return }
  if (-not (Test-DentroPerimetro $path)) {
    Stop-Wipe ("RIFIUTO: '{0}' e fuori dalle radici consentite ({1}). Nessuna rimozione oltre questo punto." -f $path, ($script:radiciConsentite -join ' ; '))
  }
  $script:rimossi++
  $cat = Get-Categoria $path
  if ($script:perCategoria.Contains($cat)) { $script:perCategoria[$cat]++ } else { $script:perCategoria[$cat] = 1 }
  if ($DryRun) { Write-Log "  [dry-run] Remove-Item -Recurse -Force $path" }
  else { Remove-Item -LiteralPath $path -Recurse -Force }
}
# Svuota una cartella mista conservando i figli da conservare; la toglie se resta vuota.
function Clear-Mista($path, [switch]$TieniCartella) {
  if (-not (Test-Path -LiteralPath $path)) { return }
  if (-not $script:protezione) { Remove-Target $path; return }
  $tenuti = 0
  foreach ($f in @(Get-ChildItem -LiteralPath $path -Force)) {
    if (Test-DaConservare $f) { $tenuti++; $script:conservati++ } else { Remove-Target $f.FullName }
  }
  if ($tenuti -eq 0 -and -not $TieniCartella) { Remove-Target $path }
}

# --- 1) progetti: verbali e memoria nascosta, tranne i prefissi preservati e le sessioni aperte ---
# Ogni cartella di slug contiene <id>.jsonl, <id>\ (sottoagenti e risultati dei tool) ed
# eventualmente memory\: con sessioni aperte restano soltanto i primi due delle sessioni
# protette, e la cartella sparisce se non resta niente.
$nomeAccountProj = Split-Path -Leaf $base
if ($nomeAccountProj -ne '.claude') { $nomeAccountProj = $nomeAccountProj -replace '^\.claude-', '' }
foreach ($d in $all) {
  if (Test-Keep $d.Name) { continue }
  if (-not $script:protezione) { Remove-Target $d.FullName; continue }
  $avvioSlug = Get-AvvioSlug ('{0}|{1}' -f $nomeAccountProj, $d.Name)
  $tenuti = 0
  foreach ($f in @(Get-ChildItem -LiteralPath $d.FullName -Force)) {
    $id = if ($f.PSIsContainer) { $f.Name } else { [IO.Path]::GetFileNameWithoutExtension($f.Name) }
    $tieni = ((Test-NomeDiSessione $id) -and (Test-Protetta $id)) -or ($avvioSlug -and (Test-NomeDiSessione $id) -and ((Get-UltimaScrittura $f) -ge $avvioSlug))
    if ($tieni) { $tenuti++; $script:conservati++ } else { Remove-Target $f.FullName }
  }
  if ($tenuti -eq 0) { Remove-Target $d.FullName }
}

# --- 2) store per-account effimeri ---
# NB: 'daemon', 'skills', 'plugins', 'hooks' NON sono in lista: sono stato vivo o
# configurazione, non residui di sessione. 'sessions' contiene un file per processo vivo,
# <pid>.json e <pid>.<impronta>.key: si tolgono quelli dei processi che non ci sono piu'.
$ephemeral = @('session-env','shell-snapshots','file-history',
               'plans','tasks','paste-cache','backups','memory',
               'cache','jobs','ide','todos','statsig','telemetry')
foreach ($e in $ephemeral) { Clear-Mista (Join-Path $base $e) }
$sessDir = Join-Path $base 'sessions'
if (Test-Path -LiteralPath $sessDir) {
  if (-not $script:protezione) { Remove-Target $sessDir }
  else {
    foreach ($f in @(Get-ChildItem -LiteralPath $sessDir -Force -File)) {
      if ($f.Name -match '^(\d+)\.' -and ($script:protezione.Vive -contains [int]$Matches[1])) { $script:conservati++ } else { Remove-Target $f.FullName }
    }
  }
}
# history.jsonl e' la storia delle richieste di tutte le sessioni dell'account, una riga
# per richiesta con il suo sessionId: con sessioni aperte si riscrive con le sole righe
# delle sessioni protette, e quelle senza sessionId solo se scritte dopo il primo avvio vivo.
$hist = Join-Path $base 'history.jsonl'
if (Test-Path -LiteralPath $hist) {
  if (-not $script:protezione) { Remove-Target $hist }
  else {
    $righe = @(Get-Content -LiteralPath $hist -Encoding UTF8)
    $limite = [DateTimeOffset]::new($script:protezione.PrimoAvvio).ToUnixTimeMilliseconds()
    $tenute = @($righe | Where-Object {
      if ($_ -match '"sessionId"\s*:\s*"([^"]+)"') { Test-Protetta $Matches[1] }
      elseif ($_ -match '"timestamp"\s*:\s*(\d+)') { [long]$Matches[1] -ge $limite }
      else { $false }
    })
    if ($tenute.Count -eq 0) { Remove-Target $hist }
    elseif ($tenute.Count -lt $righe.Count) {
      $script:rimossi += ($righe.Count - $tenute.Count); $script:conservati += $tenute.Count
      if ($DryRun) { Write-Log ("  [dry-run] history.jsonl: tolte {0} righe, tenute {1}" -f ($righe.Count - $tenute.Count), $tenute.Count) }
      elseif (Test-DentroPerimetro $hist) {
        $tmpH = "$hist.tmp"
        [IO.File]::WriteAllLines($tmpH, [string[]]$tenute, (New-Object System.Text.UTF8Encoding($false)))
        Move-Item -LiteralPath $tmpH -Destination $hist -Force
      }
    }
  }
}
$mcpCache = Join-Path $base 'mcp-needs-auth-cache.json'
if ((Test-Path -LiteralPath $mcpCache) -and -not (Test-Recente (Get-Item -LiteralPath $mcpCache))) { Remove-Target $mcpCache }

# --- 3) scratchpad temporanei: <radice temporanea>\claude\<slug-progetto>\<id-sessione> ---
# Claude Code tiene qui scratchpad e output dei task, uno slug per progetto e una
# sottocartella per sessione. La radice e' condivisa fra tutti gli account della stessa
# utenza Windows, ed e' per questo che l'insieme delle sessioni protette si calcola su
# tutti gli account e non solo su questo. Si toccano solo le cartelle che sembrano slug
# di progetto (regex '^[A-Za-z]--'), cosi' da non toccare 'bundled-skills' e simili.
# Nella cartella di un progetto di un processo vivo senza file di sessione si conserva
# anche cio' che e' stato scritto dopo il suo avvio, perche' il nome della sua sessione non
# si conosce.
if (Test-Path -LiteralPath $tmpRoot) {
  foreach ($slugDir in @(Get-ChildItem -LiteralPath $tmpRoot -Directory | Where-Object { ($_.Name -match '^[A-Za-z]--') -and -not (Test-Keep $_.Name) })) {
    $avvioSlug = Get-AvvioSlug $slugDir.Name -Comune
    if (-not $avvioSlug -or -not $script:protezione) { Clear-Mista $slugDir.FullName; continue }
    $tenuti = 0
    foreach ($f in @(Get-ChildItem -LiteralPath $slugDir.FullName -Force)) {
      if ((Test-DaConservare $f) -or ((Get-UltimaScrittura $f) -ge $avvioSlug)) { $tenuti++; $script:conservati++ } else { Remove-Target $f.FullName }
    }
    if ($tenuti -eq 0) { Remove-Target $slugDir.FullName }
  }
}

# --- 3b) log dei server MCP: <LOCALAPPDATA>\claude-cli-nodejs\Cache\<slug-progetto> ---
# Aggiunto il 2026-10-09: un handoff di un'altra sessione li aveva trovati, e nessuna
# versione precedente di questo script li toccava (1568 file sulla macchina di prova).
# Sono per progetto e non per sessione, e la radice e' comune a tutti gli account: con
# sessioni aperte si tolgono i file scritti prima dell'avvio del processo vivo piu'
# vecchio e le cartelle rimaste vuote; senza, si toglie ogni cartella di slug.
function Clear-PerData($path) {
  if (-not (Test-Path -LiteralPath $path)) { return }
  if (-not $script:protezione) { Remove-Target $path; return }
  foreach ($f in @(Get-ChildItem -LiteralPath $path -Recurse -File -Force)) {
    if (Test-Recente $f) { $script:conservati++ } else { Remove-Target $f.FullName }
  }
  if ($DryRun) { return }
  foreach ($d in @(Get-ChildItem -LiteralPath $path -Recurse -Directory -Force | Sort-Object { $_.FullName.Length } -Descending)) {
    if (-not (Get-ChildItem -LiteralPath $d.FullName -Force)) { Remove-Target $d.FullName }
  }
  if (-not (Get-ChildItem -LiteralPath $path -Force)) { Remove-Target $path }
}
if ($mcpRoot -and (Test-Path -LiteralPath $mcpRoot)) {
  Get-ChildItem -LiteralPath $mcpRoot -Directory -Force |
    Where-Object { -not (Test-Keep $_.Name) } |
    ForEach-Object { Clear-PerData $_.FullName }
}

# --- 4) .claude.json: voci 'projects' dei percorsi non preservati, metriche di quelli preservati ---
# Senza questo passaggio l'elenco dei percorsi aperti sopravvive al wipe. Il file
# custodisce login e configurazione, quindi la modifica e' delegata a
# scrub-claude-json.js: ConvertFrom-Json di PowerShell 5.1 non e' utilizzabile qui,
# perche' considera le chiavi case-insensitive e va in errore su un .claude.json che
# contenga sia 'e:/progetto' sia 'E:/progetto'. Se Node non c'e', il passaggio si
# salta senza toccare il file. Si ripulisce anche l'eventuale .backup, che altrimenti
# conserverebbe le stesse voci. Con --solo-config dalle voci preservate si tolgono anche
# le metriche dell'ultima sessione, e restano permessi, MCP e fiducia nella cartella.
# Il file lo riscrive anche ogni sessione aperta di questo account: se ce n'e' una, o se
# un processo senza file di sessione ha candidati in questo account, il passaggio si
# rimanda alla prossima chiusura invece di rischiare di sovrascrivere una sua scrittura.
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
$nomeAccount = Split-Path -Leaf $base
if ($nomeAccount -ne '.claude') { $nomeAccount = $nomeAccount -replace '^\.claude-', '' }
if (-not $keepPathPrefixes) {
  Write-Log 'Blocco 4 saltato: keepPathPrefixes non compilato e non derivabile dai prefissi slug, .claude.json resta intatto.'
}
elseif ($script:protezione -and $script:protezione.AccountVivi.ContainsKey($nomeAccount)) {
  Write-Log 'Blocco 4 rimandato: questo account ha una sessione aperta che riscrive .claude.json; lo pulira la prossima chiusura.'
}
else {
  $scrubJs = Join-Path $base 'hooks\scrub-claude-json.js'
  $nodeExe = (Get-Command node -ErrorAction SilentlyContinue).Source
  if (-not $nodeExe) { $nodeExe = 'C:\Program Files\nodejs\node.exe' }
  if ((Test-Path $scrubJs) -and (Test-Path $nodeExe)) {
    foreach ($target in @($cfgFile, "$cfgFile.backup")) {
      if (-not (Test-Path -LiteralPath $target)) { continue }
      if ($DryRun) {
        Write-Log ("  [dry-run] node scrub-claude-json.js {0} --solo-config {1}" -f $target, ($keepPathPrefixes -join ' '))
      }
      else {
        & $nodeExe $scrubJs $target '--solo-config' @keepPathPrefixes | Out-Null
        # in caso di annullamento lo script non lascia residui, ma non costa nulla assicurarsene
        Remove-Item -LiteralPath "$target.tmp" -Force
      }
    }
  }
  else { Write-Log 'Blocco 4 saltato: scrub-claude-json.js o node non disponibili.' }
}

Write-Log ("Rimossi {0} elementi, conservati {1}." -f $script:rimossi, $script:conservati)
if ($script:perCategoria.Count) { Write-Log ('Rimossi per categoria: ' + (($script:perCategoria.Keys | ForEach-Object { '{0} {1}' -f $_, $script:perCategoria[$_] }) -join ', ') + '.') }
Write-Log 'Fatto.'
