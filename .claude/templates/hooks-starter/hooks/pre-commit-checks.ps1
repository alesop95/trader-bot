# Hook PreToolUse su Bash (variante Windows): quando il comando in arrivo e' un git commit,
# esegue la batteria di controlli che la convenzione prescrive prima di un commit, e blocca
# se uno fallisce.
#
# Quali controlli, e perche' proprio questi. Sono i quattro che verificano una convenzione
# dichiarata invece di un comportamento: la forma dei paragrafi Markdown, la tipografia, i
# comandi copiabili in una riga sola dentro i blocchi di codice, e i riferimenti a file che
# non esistono. Hanno in comune il modo di fallire, ed e' la ragione per cui vale automatizzarli
# proprio loro: nessuno dei quattro produce un errore visibile. Un paragrafo hard-wrapped
# sembra normale finche' il diff non ri-avvolge righe che nessuno ha toccato; un accento
# scritto con l'apostrofo si legge; un comando spezzato si copia e fallisce dopo; un documento
# che nomina un file inesistente non rompe niente e manda fuori strada chi lo legge.
#
# Che cosa NON copre, e va detto. Questo hook vede il git commit dell'agente. I commit manuali
# dell'utente non passano di qui, ed e' il caso normale in questo sistema, dove le operazioni
# git restano dell'utente: per coprirli serve un hook nativo di git, e il README del pacchetto
# spiega come. Vale quindi come rete e non come garanzia.
#
# Blocco = exit 2 con il motivo su stderr.

$ErrorActionPreference = "SilentlyContinue"

$raw = [Console]::In.ReadToEnd()
if ($raw -notmatch 'git\s+commit') { exit 0 }

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

# Il repository che produce i modelli chiede due argomenti in piu', ed e' la seconda meta' dello
# stesso difetto che la cascata risolve. I tre strumenti tipografici rifiutano di scrivere sotto
# .claude\templates\, perche' in un progetto ospite quelli sono copie e correggerle le farebbe
# divergere dall'originale; qui pero' gli originali sono proprio loro, e senza --includi-modelli
# il controllo guarda una frazione dei file e passa. Allo stesso modo il controllo sui
# riferimenti vuole --bundle, perche' i percorsi dell'anatomia di un progetto ospite, nominati
# dai modelli, qui non esistono e non sono riferimenti rotti. Entrambi i casi falliscono verso il
# verde, che e' la direzione sbagliata: un via libera indistinguibile da quello vero.
#
# Il marcatore del bundle sono i due prompt di istanziazione, che nessun progetto ospite riceve:
# si riconosce per cio' che il repository fa, non per come si chiama la sua cartella.
$eBundle = Test-Path (Join-Path $radice ".claude\PROMPT-nuovo-progetto.md")
$modelli = if ($eBundle) { @("--includi-modelli") } else { @() }
$bundle  = if ($eBundle) { @("--bundle") } else { @() }

# Ogni voce e' il nome del controllo, il nome del file dello strumento e gli argomenti. Un
# controllo il cui strumento non si trova in nessuna delle tre cartelle si salta in silenzio: un
# progetto puo' legittimamente non avere quel pacchetto, e un hook che fallisse per questo
# renderebbe impossibile committare.
# Il perimetro e' la radice del progetto e non il punto: il punto si risolve sulla cartella
# corrente del processo che esegue l'hook, e le due coincidono in una sessione ordinaria ma non
# per contratto. Un controllo che girasse sulla cartella sbagliata non darebbe un errore, darebbe
# zero segnalazioni, cioe' un via libera indistinguibile da quello vero.
$controlli = @(
    @{ nome = "forma dei paragrafi Markdown"; file = "md-unwrap.py";           args = @("--check", "--oracle", "require", $radice) },
    @{ nome = "accenti";                      file = "fix-accents.py";         args = @("--check") + $modelli + @($radice) },
    @{ nome = "trattini";                     file = "fix-dashes.py";          args = @("--check") + $modelli + @($radice) },
    @{ nome = "comandi copiabili";            file = "lint-md-commands.py";    args = @($radice) },
    @{ nome = "riferimenti a file";           file = "lint-doc-references.py"; args = @("--radice", $radice, "--solo-vivi") + $bundle }
)

$falliti = @()
foreach ($c in $controlli) {
    $percorso = Trova-Strumento $c.file
    if (-not $percorso) { continue }
    & python $percorso @($c.args) *> $null
    if ($LASTEXITCODE -ne 0) { $falliti += @{ nome = $c.nome; percorso = $percorso; args = $c.args } }
}

if ($falliti.Count -gt 0) {
    $righe = @("Controlli pre-commit falliti (hook pre-commit-checks). Il commit e' stato fermato.")
    foreach ($c in $falliti) {
        # Si nomina il percorso davvero usato e non il solo nome del file: dove le cartelle
        # candidate sono tre, un comando da rilanciare che non dica quale e' da indovinare.
        $righe += ("  - " + $c.nome + ": rilanciare  python " + $c.percorso.Substring($radice.Length).TrimStart('\') + " " + ($c.args -join " "))
    }
    $righe += "Nessuno di questi produce un errore visibile se lo si ignora: e' la ragione per cui li controlla un programma."
    [Console]::Error.WriteLine(($righe -join "`n"))
    exit 2
}

exit 0
