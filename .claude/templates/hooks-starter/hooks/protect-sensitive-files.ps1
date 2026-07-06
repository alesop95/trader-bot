# Hook PreToolUse su Write|Edit (variante Windows): blocca le scritture su file sensibili.
# Difesa in profondita' rispetto alle regole deny del settings.json: intercetta la chiamata
# anche quando i permessi sono stati allargati. Blocco = exit 2 con motivo su stderr; in caso
# di input non parsabile lascia passare (un hook rotto non deve paralizzare il lavoro).
# NON attivo finche' non registrato nel settings.json (vedi settings.hooks.windows.json).

$raw = [Console]::In.ReadToEnd()
try { $payload = $raw | ConvertFrom-Json } catch { exit 0 }

$path = $null
if ($payload -and $payload.tool_input) { $path = $payload.tool_input.file_path }
if (-not $path) { exit 0 }

$norm = $path -replace '\\', '/'

# Eccezione esplicita: .env.example e' il template pubblico delle variabili, va scrivibile.
if ($norm -like '*.env.example') { exit 0 }

$blocked = ($norm -like '*.env') -or ($norm -like '*.env.*') -or ($norm -like '*.pem') -or ($norm -like '*.key') -or ($norm -like '*/.git/*') -or ($norm -like '.git/*')

if ($blocked) {
    [Console]::Error.WriteLine("File protetto dall'hook protect-sensitive-files: $path. Scrittura non consentita dagli hook di progetto (secret o area .git).")
    exit 2
}

exit 0
