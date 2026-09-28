# Hook SessionEnd (variante Windows): registra l'impronta di ripresa come ultimo atto della
# sessione, cosi' che la sessione successiva possa sapere se questa si sia chiusa davvero.
#
# Il paradosso che questo hook risolve a meta', e che va capito prima di attivarlo. L'impronta
# serve a distinguere una sessione chiusa bene da una caduta; ma se la registrasse solo
# l'agente, una sessione caduta non la registrerebbe mai, che e' proprio il comportamento
# voluto. Se invece la registra un hook di chiusura, la registra anche quando la finestra viene
# chiusa di colpo, e allora una caduta diventa indistinguibile da una chiusura ordinata.
#
# La risoluzione sta in che cosa l'hook scrive. Un hook SessionEnd gira alla chiusura della
# sessione, comprese quelle ordinate, ma NON gira quando il processo muore per un crash vero o
# una interruzione dell'alimentazione, che sono i casi che contano di piu'. Quindi questo hook
# copre la chiusura distratta, cioe' la finestra chiusa senza aver aggiornato il file di
# ripresa, e lascia scoperta la caduta vera, che e' esattamente cio' che si vuole sia visibile.
#
# Ne discende una prescrizione d'uso, scritta anche nel README: questo hook e' una rete, non il
# percorso principale. Il percorso principale resta l'agente che, a fine sessione, aggiorna il
# file di ripresa con lo stato raggiunto e il prossimo passo, e poi registra. Un'impronta
# registrata senza quell'aggiornamento dice che lo stato di git e' noto e non dice dove eravamo.

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

# Qui la dichiarazione non ha dove andare, perche' l'uscita di un hook di chiusura non entra in
# nessun contesto: resta la ricerca, senza la riga che la racconta.
$strumento = Trova-Strumento "verifica-ripresa.py"
if (-not $strumento) { exit 0 }

& python $strumento --radice $radice --registra *> $null

exit 0
