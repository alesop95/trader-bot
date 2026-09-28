# Hook PreToolUse su Bash (variante Windows): se il comando in arrivo e' un git commit,
# scansiona il diff in stage alla ricerca di pattern di secret e blocca il commit se ne trova.
# Nota onesta: con il settings.json di baseline del sistema il git commit dell'agente e' gia'
# negato (i commit restano manuali dell'utente), quindi questo hook e' difesa in profondita'
# per i progetti che allentano quel deny. I commit manuali dell'utente NON passano di qui: per
# coprirli serve un hook nativo di git (core.hooksPath), vedi README del pacchetto.
#
# Perimetro, e cosa NON copre. Questo hook guarda il solo diff in stage, che e' la scelta
# giusta per il suo compito: un segreto lo si introduce, e va fermato quando lo si
# introduce. Ne discende pero' che un residuo GIA' PRESENTE nel repository gli e'
# invisibile per costruzione, perche' nessun commit successivo lo riporta in stage. Per
# quella meta' del problema serve un controllo che passi il perimetro intero a ogni
# esecuzione: e' il pacchetto `anonymization`, che cerca anche una categoria diversa,
# cioe' i dati che identificano persone e infrastrutture invece delle credenziali. I due
# si usano insieme e nessuno dei due sostituisce l'altro.
# Blocco = exit 2 con motivo su stderr. NON attivo finche' non registrato nel settings.json.

$ErrorActionPreference = "SilentlyContinue"

$raw = [Console]::In.ReadToEnd()

# Interviene solo se il payload contiene un git commit; altrimenti lascia passare subito.
if ($raw -notmatch 'git\s+commit') { exit 0 }

$staged = (git diff --cached) -join "`n"
if (-not $staged) { exit 0 }

# Pattern di secret: chiavi AWS, blocchi di chiave privata, token GitHub/OpenAI/Slack,
# assegnazioni quotate di api key e password.
$patterns = @(
    'AKIA[0-9A-Z]{16}',
    '-----BEGIN [A-Z ]*PRIVATE KEY-----',
    'ghp_[A-Za-z0-9]{36}',
    'github_pat_[A-Za-z0-9_]{22,}',
    'sk-[A-Za-z0-9_-]{20,}',
    'xox[baprs]-[A-Za-z0-9-]{10,}',
    '(?i)api[_-]?key["'']?\s*[:=]\s*["''][A-Za-z0-9_\-]{16,}',
    '(?i)password["'']?\s*[:=]\s*["''][^"'']{6,}'
)

foreach ($p in $patterns) {
    if ($staged -match $p) {
        [Console]::Error.WriteLine("Possibile secret rilevato nel diff in stage (hook secret-scan). Rimuoverlo dallo stage prima di committare; se e' un falso positivo, adattare i pattern in .claude/hooks/secret-scan.ps1.")
        exit 2
    }
}

exit 0
