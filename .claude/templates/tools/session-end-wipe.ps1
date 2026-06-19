# ============================================================================
# session-end-wipe.ps1  (TEMPLATE)
# Wipe del magazzino nascosto di Claude Code, eseguito da un hook SessionEnd a
# OGNI chiusura di sessione dell'account. Mantiene il magazzino nascosto pulito
# nel tempo, senza dover lanciare comandi a mano.
#
# Installazione per-account (vedi PROJECT-SYSTEM.md sezione 15):
#   1. copia questo file in <CLAUDE_CONFIG_DIR>\hooks\session-end-wipe.ps1
#   2. sostituisci il segnaposto <CLAUDE_CONFIG_DIR> qui sotto con il path
#      assoluto della home dell'account (es. C:\Users\<utente>\.claude oppure
#      ...\.claude-accountN)
#   3. registra l'hook in <CLAUDE_CONFIG_DIR>\settings.json:
#        "hooks": { "SessionEnd": [ { "hooks": [ {
#          "type": "command",
#          "command": "powershell.exe -NoProfile -ExecutionPolicy Bypass -File \"<CLAUDE_CONFIG_DIR>\\hooks\\session-end-wipe.ps1\""
#        } ] } ] }
#
# COSA PRESERVA, sempre:
#   - i progetti il cui slug inizia con $keepPrefix. Il prefisso e SPECIFICO della
#     macchina: dove i progetti di sviluppo stanno su un disco dedicato (su questa
#     macchina D:, quindi slug 'D--') si imposta quello, su un'altra macchina si cambia.
#   - configurazione, login, skill, plugin: settings.json, .credentials.json,
#     .claude.json, skills\, plugins\, hooks\  -> mai toccati
#   - i file dei progetti su disco (E:\, D:\, ...) -> mai toccati: si agisce
#     solo dentro la home dell'account.
# ============================================================================
$ErrorActionPreference = 'SilentlyContinue'
$base = '<CLAUDE_CONFIG_DIR>'   # <-- sostituire col path assoluto dell'account
$keepPrefix = 'D--'             # prefisso slug da preservare; SPECIFICO DELLA MACCHINA (qui D:)

# --- 1) progetti: rimuovi transcript + memoria nascosta di tutto tranne $keepPrefix* ---
$projects = Join-Path $base 'projects'
if (Test-Path $projects) {
  Get-ChildItem -LiteralPath $projects -Directory |
    Where-Object { $_.Name -notlike "$keepPrefix*" } |
    ForEach-Object { Remove-Item -LiteralPath $_.FullName -Recurse -Force }
}

# --- 2) store per-account effimeri ---
# Per conservare resume/undo dei progetti preservati tra una sessione e l'altra,
# commenta le voci che vuoi mantenere (es. 'sessions','file-history').
$ephemeral = @('sessions','session-env','shell-snapshots','file-history',
               'plans','tasks','paste-cache','backups','memory')
foreach ($e in $ephemeral) {
  $p = Join-Path $base $e
  if (Test-Path $p) { Remove-Item -LiteralPath $p -Recurse -Force }
}
Remove-Item -LiteralPath (Join-Path $base 'history.jsonl') -Force
