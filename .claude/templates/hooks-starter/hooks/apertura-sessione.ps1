# Hook SessionStart (variante Windows): rende automatica la verifica di ripresa e chiede
# all'agente di misurare il drift, che e' il passo che un programma non puo' fare da se'.
#
# Perche' esiste, e che cosa lo distingue da session-context. Quell'hook stampa lo stato:
# branch, commit, file modificati, testa della memoria. Questo non stampa lo stato, lo
# CONFRONTA con quello che la sessione precedente aveva registrato, e la differenza e' tutta
# qui: una sessione caduta a meta' lascia un file di ripresa che descrive un passato, e un
# file di ripresa non aggiornato ha esattamente lo stesso aspetto di uno aggiornato. Nessuna
# stampa dello stato corrente rivela quella condizione: serve il confronto.
#
# I due hook si attivano insieme senza pestarsi, perche' rispondono a due domande diverse:
# "dove siamo" e "cio' che credo di sapere e' ancora vero".
#
# Il secondo mestiere di questo hook e' meno ovvio. L'uscita di un hook SessionStart entra nel
# contesto della sessione, quindi una riga di istruzione qui dentro e' il solo modo di rendere
# automatico un passo che richiede l'agente e non un programma: la misura del drift fra schede
# e codice la fa la skill sync-context, e nessun hook puo' invocare una skill.

$ErrorActionPreference = "SilentlyContinue"

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

# Il perimetro si passa esplicitamente. Un hook non gira per contratto nella radice del
# progetto: gira nella cartella corrente del processo che lo ospita, e le due coincidono in una
# sessione ordinaria ma non sempre. Uno strumento che risolvesse la radice sul punto leggerebbe
# un altro repository, o nessuno, e direbbe che il file di ripresa non esiste invece di dire che
# lo sta cercando nel posto sbagliato: un difetto che si traveste da diagnosi.
$strumento = Trova-Strumento "verifica-ripresa.py"

Write-Output "=== Verifica di ripresa ==="

if (-not $strumento) {
    # Lo strumento non si trova in nessuna delle tre cartelle: si dichiara e non si blocca
    # niente. Un hook che fallisse qui renderebbe inutilizzabile un progetto che ha scelto di
    # non averlo.
    Write-Output "verifica-ripresa.py non e' istanziato in questo progetto, ne' in tools\ ne'"
    Write-Output "sotto .claude\templates\: la verifica di ripresa non e' disponibile. Si"
    Write-Output "istanzia dal pacchetto del template."
} else {
    Write-Output ("strumento: " + $strumento.Substring($radice.Length).TrimStart('\'))
    $uscita = & python $strumento --radice $radice 2>&1
    $esito = $LASTEXITCODE
    $uscita | ForEach-Object { Write-Output $_ }
    if ($esito -ne 0) {
        Write-Output ""
        Write-Output "ISTRUZIONE PER L'AGENTE: sopra ci sono divergenze fra il file di ripresa e"
        Write-Output "lo stato reale. Riportale all'utente PRIMA di qualunque altra cosa e prima"
        Write-Output "di leggere il file di ripresa, seguendo la skill riprendi: un file lasciato"
        Write-Output "a meta' puo' essere un lavoro da riprendere o uno da buttare, e la"
        Write-Output "differenza non si legge dal contenuto. Non decidere: chiedi."
    }
}

Write-Output ""
Write-Output "ISTRUZIONE PER L'AGENTE: come secondo atto della sessione invoca la skill"
Write-Output "sync-context, per misurare il drift fra le schede di .claude/context/ e il codice."
Write-Output "Nessun hook puo' invocare una skill, quindi questo passo dipende da te. Poi leggi"
Write-Output "le sole schede pertinenti al task, mai tutte insieme."

exit 0
