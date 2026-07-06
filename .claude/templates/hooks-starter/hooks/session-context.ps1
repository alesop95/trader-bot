# Hook SessionStart (variante Windows): inietta il contesto di ripresa a inizio sessione.
# Stampa branch, ultimi commit, file modificati e la testa di .claude/memory/index.md con il
# punto di ripresa; l'output su stdout entra nel contesto della sessione (sezioni 12 e 14 di
# PROJECT-SYSTEM.md). Sola lettura, nessuna rete. NON attivo finche' non registrato nel
# settings.json del progetto (vedi settings.hooks.windows.json).

$ErrorActionPreference = "SilentlyContinue"

$root = $env:CLAUDE_PROJECT_DIR
if ($root -and (Test-Path $root)) { Set-Location $root }

Write-Output "=== Contesto di ripresa (hook session-context) ==="

$branch = git branch --show-current
if (-not $branch) { $branch = git rev-parse --abbrev-ref HEAD }
if (-not $branch) { $branch = "n/a" }
Write-Output "Branch: $branch"

Write-Output "Ultimi commit:"
git rev-parse --verify HEAD *> $null
if ($?) {
    Write-Output (git log --oneline -3)
} else {
    Write-Output "  (nessuna storia git: nessun commit ancora)"
}

$changed = git status --short | Select-Object -First 20
if ($changed) {
    Write-Output "File modificati non committati:"
    Write-Output $changed
} else {
    Write-Output "Working tree pulito."
}

$indexPath = ".claude\memory\index.md"
if (Test-Path $indexPath) {
    Write-Output "--- .claude/memory/index.md (testa) ---"
    Get-Content $indexPath -TotalCount 40 -Encoding UTF8
    Write-Output "--- (leggere il file completo per la tabella di sincronizzazione) ---"
} else {
    Write-Output "Nota: .claude/memory/index.md non trovato (sistema non ancora inizializzato?)."
}

exit 0
