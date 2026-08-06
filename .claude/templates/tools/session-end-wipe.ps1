# ============================================================================
# session-end-wipe.ps1  (TEMPLATE)
# Wipe del magazzino nascosto di Claude Code, eseguito da un hook SessionEnd a
# OGNI chiusura di sessione dell'account. Mantiene il magazzino nascosto pulito
# nel tempo, senza dover lanciare comandi a mano.
#
# Installazione per-account (vedi PROJECT-SYSTEM.md sezione 15):
#   1. copia questo file in <CLAUDE_CONFIG_DIR>\hooks\session-end-wipe.ps1
#      e, accanto, scrub-claude-json.js preso dalla stessa cartella del template
#   2. sostituisci il segnaposto <CLAUDE_CONFIG_DIR> qui sotto con il path
#      assoluto della home dell'account (es. C:\Users\<utente>\.claude oppure
#      ...\.claude-accountN)
#   3. registra l'hook in <CLAUDE_CONFIG_DIR>\settings.json:
#        "hooks": { "SessionEnd": [ { "hooks": [ {
#          "type": "command",
#          "command": "powershell.exe -NoProfile -ExecutionPolicy Bypass -File \"<CLAUDE_CONFIG_DIR>\\hooks\\session-end-wipe.ps1\""
#        } ] } ] }
#      Nella home di default, che non ha settings.json, l'hook si registra in
#      settings.local.json.
#
# COSA PRESERVA, sempre:
#   - i progetti il cui slug inizia con uno dei prefissi in $keepPrefixes. L'insieme
#     e SPECIFICO della macchina: un prefisso per ogni disco dove stanno i progetti
#     di sviluppo (es. 'D--' se i progetti stanno su D:, 'E--' se anche su E:, e cosi
#     via se lo sviluppo e distribuito su piu dischi).
#   - configurazione, login, skill, plugin: settings.json, .credentials.json,
#     skills\, plugins\, hooks\, daemon\  -> mai toccati
#   - di .claude.json si rimuovono SOLO le voci 'projects' dei percorsi non
#     preservati: login e configurazione restano intatti (vedi blocco 4)
#   - i file dei progetti su disco (E:\, D:\, ...) -> mai toccati: si agisce
#     solo dentro la home dell'account e nello scratchpad temporaneo.
# ============================================================================
$ErrorActionPreference = 'SilentlyContinue'
$base = '<CLAUDE_CONFIG_DIR>'         # <-- sostituire col path assoluto dell'account
$keepPrefixes = @('D--')              # prefissi slug da preservare; SPECIFICI DELLA MACCHINA (un prefisso per disco)
# Percorso di .claude.json: con CLAUDE_CONFIG_DIR impostato sta DENTRO la home
# dell'account; nella home di default sta invece accanto ad essa, in $HOME\.claude.json.
$cfgFile = Join-Path $base '.claude.json'
# Prefissi di PERCORSO da preservare dentro 'projects' di .claude.json (blocco 4).
# Su Windows si derivano dai prefissi slug ('D--' -> 'D:'); su un'altra convenzione
# di percorsi vanno elencati a mano (es. @('/home/utente/dev')).
$keepPathPrefixes = @($keepPrefixes | ForEach-Object { $_.Substring(0,1) + ':' })

# --- 1) progetti: rimuovi transcript + memoria nascosta di tutto tranne i prefissi preservati ---
$projects = Join-Path $base 'projects'
if (Test-Path $projects) {
  Get-ChildItem -LiteralPath $projects -Directory |
    Where-Object { $name = $_.Name; -not ($keepPrefixes | Where-Object { $name -like "$_*" }) } |
    ForEach-Object { Remove-Item -LiteralPath $_.FullName -Recurse -Force }
}

# --- 2) store per-account effimeri ---
# Per conservare resume/undo dei progetti preservati tra una sessione e l'altra,
# commenta le voci che vuoi mantenere (es. 'sessions','file-history').
# NB: 'daemon', 'skills', 'plugins', 'hooks' NON sono in lista: sono stato vivo o
# configurazione, non residui di sessione.
$ephemeral = @('sessions','session-env','shell-snapshots','file-history',
               'plans','tasks','paste-cache','backups','memory',
               'cache','jobs','ide','todos','statsig','telemetry')
foreach ($e in $ephemeral) {
  $p = Join-Path $base $e
  if (Test-Path $p) { Remove-Item -LiteralPath $p -Recurse -Force }
}
Remove-Item -LiteralPath (Join-Path $base 'history.jsonl') -Force
Remove-Item -LiteralPath (Join-Path $base 'mcp-needs-auth-cache.json') -Force

# --- 3) scratchpad temporanei: %LOCALAPPDATA%\Temp\claude\<slug-progetto> ---
# Claude Code tiene qui scratchpad e output dei task, uno slug per progetto e una
# sottocartella per sessione. Questa radice e' condivisa fra tutti gli account della
# stessa utenza Windows, quindi il passaggio e' idempotente: chiunque chiuda per ultimo
# la ripulisce. Si rimuovono solo le cartelle che sembrano slug di progetto (regex
# '^[A-Za-z]--'), cosi' da non toccare 'bundled-skills' e simili.
$tmpRoot = Join-Path $env:LOCALAPPDATA 'Temp\claude'
if (Test-Path $tmpRoot) {
  Get-ChildItem -LiteralPath $tmpRoot -Directory |
    Where-Object {
      $name = $_.Name
      ($name -match '^[A-Za-z]--') -and -not ($keepPrefixes | Where-Object { $name -like "$_*" })
    } |
    ForEach-Object { Remove-Item -LiteralPath $_.FullName -Recurse -Force }
}

# --- 4) .claude.json: rimuovi le voci 'projects' dei percorsi non preservati ---
# Senza questo passaggio l'elenco dei percorsi aperti sopravvive al wipe. Il file
# custodisce login e configurazione, quindi la modifica e' delegata a
# scrub-claude-json.js: ConvertFrom-Json di PowerShell 5.1 non e' utilizzabile qui,
# perche' considera le chiavi case-insensitive e va in errore su un .claude.json che
# contenga sia 'e:/progetto' sia 'E:/progetto'. Se Node non c'e', il passaggio si
# salta senza toccare il file. Si ripulisce anche l'eventuale .backup, che altrimenti
# conserverebbe le stesse voci.
$scrubJs = Join-Path $base 'hooks\scrub-claude-json.js'
$nodeExe = (Get-Command node -ErrorAction SilentlyContinue).Source
if (-not $nodeExe) { $nodeExe = 'C:\Program Files\nodejs\node.exe' }
if ((Test-Path $scrubJs) -and (Test-Path $nodeExe)) {
  foreach ($target in @($cfgFile, "$cfgFile.backup")) {
    if (Test-Path $target) {
      & $nodeExe $scrubJs $target @keepPathPrefixes | Out-Null
      # in caso di annullamento lo script non lascia residui, ma non costa nulla assicurarsene
      Remove-Item -LiteralPath "$target.tmp" -Force
    }
  }
}
