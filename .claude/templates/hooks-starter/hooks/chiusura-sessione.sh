#!/usr/bin/env bash
# Hook SessionEnd (variante POSIX): registra l'impronta di ripresa come ultimo atto della
# sessione, cosi' che la sessione successiva possa sapere se questa si sia chiusa davvero.
#
# Il paradosso che questo hook risolve a meta', e che va capito prima di attivarlo. L'impronta
# serve a distinguere una sessione chiusa bene da una caduta; ma se la registrasse solo
# l'agente, una sessione caduta non la registrerebbe mai, che e' proprio il comportamento
# voluto. Se invece la registra un hook di chiusura, la registra anche quando la finestra viene
# chiusa di colpo, e allora una caduta diventa indistinguibile da una chiusura ordinata.
#
# La risoluzione sta in che cosa l'hook copre. Un hook SessionEnd gira alla chiusura della
# sessione, comprese quelle ordinate, ma NON gira quando il processo muore per un crash vero o
# una interruzione dell'alimentazione, che sono i casi che contano di piu'. Quindi questo hook
# copre la chiusura distratta, cioe' la finestra chiusa senza aver aggiornato il file di
# ripresa, e lascia scoperta la caduta vera, che e' esattamente cio' che si vuole sia visibile.
#
# Ne discende una prescrizione d'uso, scritta anche nel README: questo hook e' una rete, non il
# percorso principale. Il percorso principale resta l'agente che, a fine sessione, aggiorna il
# file di ripresa con lo stato raggiunto e il prossimo passo, e poi registra. Un'impronta
# registrata senza quell'aggiornamento dice che lo stato di git e' noto e non dice dove eravamo.

RADICE="${CLAUDE_PROJECT_DIR:-$PWD}"

# Ricerca a cascata dello strumento. Le collocazioni legittime sono due e non una: in un
# progetto istanziato gli strumenti condivisi stanno in tools/ della radice, mentre nel
# repository che li produce, cioe' il template stesso, gli originali vivono sotto
# .claude/templates/, dove md-unwrap ha per giunta una cartella propria. Un hook che cercasse
# soltanto la prima uscirebbe zero senza fare nulla proprio nel repository dove quegli strumenti
# sono nati, e non come errore ma come silenzio, che e' il modo peggiore di fallire.
#
# La ricerca prova le tre cartelle in quest'ordine e restituisce la prima che risponde, e dove
# l'uscita dell'hook viene letta dichiara anche quale: un hook che sta lavorando su una copia
# dei modelli invece che sull'originale, o viceversa, deve poterlo far vedere.
CARTELLE_STRUMENTI="tools .claude/templates/tools .claude/templates/md-unwrap/tools"

trova_strumento() {
    for cartella in $CARTELLE_STRUMENTI; do
        if [ -f "$RADICE/$cartella/$1" ]; then
            printf '%s/%s/%s' "$RADICE" "$cartella" "$1"
            return 0
        fi
    done
    return 1
}

# Qui la dichiarazione non ha dove andare, perche' l'uscita di un hook di chiusura non entra in
# nessun contesto: resta la ricerca, senza la riga che la racconta.
STRUMENTO="$(trova_strumento verifica-ripresa.py)"
[ -n "$STRUMENTO" ] || exit 0

# L'interprete si sceglie invece di assumerlo. Su una macchina con Git Bash `python3` puo'
# esistere sul PATH ed essere l'alias fittizio del Microsoft Store, che non esegue niente e non
# sbaglia: un hook che lo invocasse uscirebbe zero senza aver fatto nulla, cioe' fallirebbe in
# silenzio, che e' il modo peggiore. Si prova quale dei due risponde davvero.
PY=""
for candidato in python3 python; do
    if command -v "$candidato" >/dev/null 2>&1 && "$candidato" -c "import sys" >/dev/null 2>&1; then
        PY="$candidato"
        break
    fi
done
[ -n "$PY" ] || exit 0

"$PY" "$STRUMENTO" --radice "$RADICE" --registra >/dev/null 2>&1

exit 0
