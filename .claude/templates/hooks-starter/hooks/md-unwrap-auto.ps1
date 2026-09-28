# Hook PostToolUse su Write ed Edit (variante Windows): riporta i paragrafi del file appena
# scritto su riga sorgente unica, secondo la convenzione della regola interaction-style.
#
# Perche' e' un hook e non una consegna all'agente. La convenzione dice di eseguire lo
# strumento dopo aver scritto o modificato un file Markdown, e quella prescrizione ha lo stesso
# difetto di tutte le prescrizioni che dipendono dal ricordarsene: funziona finche' qualcuno
# ricorda, e la volta che non ricorda nessuno se ne accorge, perche' un file hard-wrapped non
# sembra sbagliato. Se ne accorge il diff del commit successivo, che ri-avvolge righe che
# nessuno ha toccato, e a quel punto il rumore e' gia' entrato nella storia.
#
# Agisce dopo la scrittura e non prima, perche' e' una normalizzazione e non una difesa: non
# c'e' niente da bloccare, c'e' una forma da attuare. Per contratto lo strumento rifiuta di
# scrivere un file il cui rendering cambierebbe, quindi il caso peggiore e' che non faccia
# nulla, mai che rovini un file.
#
# Tocca soltanto i file .md, e soltanto dentro la radice del progetto.

$ErrorActionPreference = "SilentlyContinue"

$raw = [Console]::In.ReadToEnd()
if (-not $raw) { exit 0 }

try { $payload = $raw | ConvertFrom-Json } catch { exit 0 }
$percorso = $payload.tool_input.file_path
if (-not $percorso) { exit 0 }
if ($percorso -notmatch '\.md$') { exit 0 }
if (-not (Test-Path $percorso)) { exit 0 }

$radice = if ($env:CLAUDE_PROJECT_DIR) { $env:CLAUDE_PROJECT_DIR } else { (Get-Location).Path }

# Ricerca a cascata dello strumento. Le collocazioni legittime sono due e non una: in un
# progetto istanziato gli strumenti condivisi stanno in tools\ della radice, mentre nel
# repository che li produce, cioe' il template stesso, gli originali vivono sotto
# .claude\templates\, dove md-unwrap ha per giunta una cartella propria. Un hook che cercasse
# soltanto la prima uscirebbe zero senza fare nulla proprio nel repository dove quegli strumenti
# sono nati, e non come errore ma come silenzio, che e' il modo peggiore di fallire.
#
# La ricerca prova le tre cartelle in quest'ordine e restituisce la prima che risponde, e dove
# l'uscita dell'hook viene letta dichiara anche quale: un hook che sta lavorando su una copia
# dei modelli invece che sull'originale, o viceversa, deve poterlo far vedere.
$cartelleStrumenti = @("tools", ".claude\templates\tools", ".claude\templates\md-unwrap\tools")

function Trova-Strumento([string]$nome) {
    foreach ($cartella in $cartelleStrumenti) {
        $candidato = Join-Path (Join-Path $radice $cartella) $nome
        if (Test-Path $candidato) { return $candidato }
    }
    return $null
}

# Qui la dichiarazione tace: un hook PostToolUse che stampasse una riga a ogni scrittura
# riempirebbe il contesto di rumore proporzionale al lavoro fatto. Chi vuole sapere dove sta lo
# strumento lo legge dall'hook di apertura, che quella riga la stampa una volta sola.
$strumento = Trova-Strumento "md-unwrap.py"
if (-not $strumento) { exit 0 }

# Il marcatore che esenta una cartella dalla normalizzazione lo rispetta lo strumento stesso:
# qui non si duplica quella logica, perche' due copie della stessa regola divergono.
& python $strumento $percorso *> $null

exit 0
