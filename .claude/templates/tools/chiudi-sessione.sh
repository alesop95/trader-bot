#!/usr/bin/env bash
# chiudi-sessione.sh - Chiusura di sessione in un comando solo (Bash su Linux/macOS).
#
# Stessa sequenza e stesse ragioni di chiudi-sessione.ps1, a cui si rimanda per il commento
# esteso: stato, controlli istanziati (si ferma se uno fallisce), commit con conferma, push
# verificato, impronta di ripresa, wipe degli account se nessuna sessione Claude Code e' aperta.
# Si lancia dal proprio terminale dopo aver chiuso Claude Code. Le regole che applica sono elencate
# in testa a chiudi-sessione.ps1: il messaggio lo fa rispettare l'hook .githooks/commit-msg.
#
# Uso:
#   bash tools/chiudi-sessione.sh                      tutto, con conferma
#   bash tools/chiudi-sessione.sh -m "Testo"           messaggio esplicito
#   bash tools/chiudi-sessione.sh --si                 senza conferma
#   bash tools/chiudi-sessione.sh --solo-controlli     stato e controlli, nient'altro
#   bash tools/chiudi-sessione.sh --no-wipe            salta il wipe
#   bash tools/chiudi-sessione.sh --account account2   wipe del solo ~/.claude-account2
set -u

messaggio=""; si=0; solo=0; nowipe=0; account=""; radice=""
while [ $# -gt 0 ]; do
    case "$1" in
        -m|--messaggio|--account|--radice)
            [ $# -ge 2 ] && [ -n "$2" ] || { echo "Valore mancante per $1" >&2; exit 2; }
            case "$1" in
                -m|--messaggio) messaggio="$2" ;;
                --account) account="$2" ;;
                --radice) radice="$2" ;;
            esac
            shift 2 ;;
        --si) si=1; shift ;;
        --solo-controlli) solo=1; shift ;;
        --no-wipe) nowipe=1; shift ;;
        *) echo "opzione sconosciuta: $1" >&2; exit 2 ;;
    esac
done

titolo() { printf '\n== %s\n' "$1"; }
ok() { printf '   ok  %s\n' "$1"; }
avvisi=0
ko() { avvisi=$((avvisi+1)); printf '   KO  %s\n' "$1"; }
nota() { printf '   %s\n' "$1"; }

dir_script="$(cd "$(dirname "$0")" && pwd)"
[ -n "$radice" ] || radice="$(git -C "$dir_script" rev-parse --show-toplevel 2>/dev/null)"
[ -n "$radice" ] || { echo "Non trovo il repository: passare --radice." >&2; exit 2; }
cd "$radice" || exit 2
# Il bundle si riconosce da due file insieme: PACKAGES.md da solo compare anche in ogni progetto
# allineato, perche' la procedura importa l'intera cartella dei modelli; PROMPT-nuovo-progetto.md
# vive solo nel bundle e non si importa mai.
bundle=0; [ -f .claude/templates/PACKAGES.md ] && [ -f .claude/PROMPT-nuovo-progetto.md ] && bundle=1

cartelle="tools .claude/templates/tools .claude/templates/md-unwrap/tools .claude/templates/readme-sync/tools .claude/templates/fix-typography/tools"
# In un progetto si eseguono soltanto i controlli istanziati in tools/: le copie dei modelli sono
# pacchetti non ancora adottati, e lanciarli fermerebbe il commit per strumenti che nessuno ha scelto.
[ $bundle = 0 ] && cartelle="tools"
trova() { for c in $cartelle; do [ -f "$c/$1" ] && { echo "$c/$1"; return; }; done; }

python=""
# Il -c scarta l'alias del Microsoft Store, che su Windows risponde a command -v e non esegue.
for c in python3 python; do "$c" -c 'import sys' >/dev/null 2>&1 && { python="$c"; break; }; done

titolo "Stato"
# symbolic-ref funziona anche senza commit e fallisce con HEAD staccato, da fermare prima del commit.
ramo="$(git symbolic-ref --short -q HEAD)"
[ -n "$ramo" ] || { echo "HEAD staccato: passare a un ramo (git switch <ramo>) e rilanciare; niente e' stato committato."; exit 1; }
haorigin=0; git remote | grep -qx origin && haorigin=1
nota "repository: $radice"
nota "ramo: $ramo$([ $bundle = 1 ] && echo '   (bundle del template)')"
[ $haorigin = 1 ] || nota "attenzione: nessun remoto 'origin': si committa in locale e il push si salta"
ncambi="$(git status --porcelain | wc -l | tr -d ' ')"
if [ "$ncambi" = 0 ]; then nota "albero pulito: niente da committare"
else git --no-pager status --short; git rev-parse -q --verify HEAD >/dev/null && git --no-pager diff --stat HEAD; fi
resume="_notes/RESUME-PROMPT.md"
if [ -f "$resume" ] && [ -n "$(find "$resume" -mtime +0 2>/dev/null)" ]; then
    nota "attenzione: $resume non e' stato aggiornato nelle ultime 24 ore"
fi

titolo "Controlli"
b=""; m=""; o=""
[ $bundle = 1 ] && { b="--bundle"; m="--includi-modelli"; o="--oracle require"; }
# nome|argomenti|file richiesto|solo bundle
controlli="md-unwrap.py|--check --only-tracked $o .||0
sync-readme.py|--check $b|README.md|0
lint-md-commands.py|.||0
lint-doc-references.py|--solo-vivi $b||0
check-eol.py|.||0
misura-istruzioni.py|||0
fix-accents.py|--check $m .||0
fix-dashes.py|--check $m .||0
fix-missing-accents.py|--check $m .||0
sync-codex-skills.py|--project-root . --check|.claude/skills|0
check-copie-modelli.py|||1
check-catalogo.py|||1
check-raggiungibilita.py|||1
test-tipografia.py|||1"

falliti=""
if [ -z "$python" ]; then ko "Python non trovato"; falliti="python"
else
    while IFS='|' read -r nome argomenti serve solobundle; do
        [ "$solobundle" = 1 ] && [ $bundle = 0 ] && continue
        [ -n "$serve" ] && [ ! -e "$serve" ] && continue
        p="$(trova "$nome")"; [ -n "$p" ] || continue
        # shellcheck disable=SC2086
        uscita="$("$python" "$p" $argomenti 2>&1)"; rc=$?
        if [ $rc = 0 ]; then ok "$nome"
        else ko "$nome (uscita $rc)"; printf '%s\n' "$uscita" | tail -15 | sed 's/^/       /'; falliti="$falliti $nome"; fi
    done <<EOF
$controlli
EOF
fi
if [ -n "$falliti" ]; then printf '\nControlli falliti:%s. Mi fermo prima del commit.\n' "$falliti"; exit 1; fi
[ $solo = 1 ] && { printf '\nControlli verdi.\n'; exit 0; }

filemsg="_notes/COMMIT-MSG.txt"
if [ "$ncambi" != 0 ]; then
    titolo "Commit"
    if [ -z "$messaggio" ] && [ -f "$filemsg" ]; then
        messaggio="$(grep -m1 -v '^[[:space:]]*$' "$filemsg")"
        [ -n "$messaggio" ] && nota "messaggio preparato dall'agente in $filemsg"
    fi
    if [ -z "$messaggio" ]; then
        read -r -p "   Messaggio di commit: " messaggio || { echo "Input non disponibile: mi fermo."; exit 1; }
    fi
    [ -n "$messaggio" ] || { echo "Messaggio vuoto: mi fermo."; exit 1; }
    # git-identity-and-repo.md: si firma solo con l'identita' locale del repository.
    nome="$(git config --local user.name)"; email="$(git config --local user.email)"
    [ -n "$nome" ] && [ -n "$email" ] || { echo "Identita' git locale non impostata: impostare user.name e user.email del repository e rilanciare."; exit 1; }
    nota "$ncambi file  ->  \"$messaggio\""
    nota "autore: $nome <$email>"
    if [ $si = 0 ]; then
        read -r -p "   Committo tutto e pusho su '$ramo'? [s/N] " r || { echo "Input non disponibile: niente e' stato committato."; exit 1; }
        case "$r" in s|si|y|yes) ;; *) echo "Annullato: niente e' stato committato."; exit 1 ;; esac
    fi
    git add -A || { echo "Stage fallito: niente e' stato committato."; exit 1; }
    git commit -m "$messaggio" || { echo "Commit rifiutato (hook o errore): correggere e rilanciare."; exit 1; }
    rm -f "$filemsg"
fi

titolo "Push"
if [ $haorigin = 0 ]; then nota "nessun remoto 'origin': push saltato, il commit resta locale"
elif ! git rev-parse -q --verify HEAD >/dev/null; then nota "nessun commit sul ramo: niente da pushare"
else
    # Destinazione esplicita: un upstream diverso da origin non deve deviare la chiusura.
    git push -u origin "HEAD:refs/heads/$ramo" || { echo "Push fallito: l'impronta non si registra finche' il remoto non e' allineato."; exit 1; }
    locale="$(git rev-parse HEAD)"
    remoto="$(git ls-remote --exit-code origin "refs/heads/$ramo")" || { ko "verifica del ramo remoto fallita"; exit 1; }
    remoto="${remoto%%[[:space:]]*}"
    [ "$locale" = "$remoto" ] || { ko "HEAD $locale diverso dal remoto $remoto"; exit 1; }
    ok "HEAD e remoto coincidono su '$ramo' (${locale:0:7})"
fi

# Sul template, una modifica a .claude/ si propaga ai progetti solo con la passata di
# allinea-tutti: lo si ricorda qui, dopo il push, invece di affidarlo alla memoria.
if [ $bundle = 1 ] && [ -n "$python" ] && [ -f .claude/templates/tools/passata-in-sospeso.py ]; then
    titolo "Propagazione ai progetti"
    "$python" .claude/templates/tools/passata-in-sospeso.py | sed 's/^/   /'
fi

titolo "Impronta di ripresa"
vr="$(trova verifica-ripresa.py)"
if [ -n "$vr" ] && [ -n "$python" ]; then
    "$python" "$vr" --radice "$radice" --registra && ok "impronta registrata" || ko "verifica-ripresa.py --registra"
else nota "verifica-ripresa.py non istanziato: passo saltato"; fi

# 0 se tutto e' andato, 3 se il commit e' fatto ma un passo successivo ha dato KO.
fine() {
    if [ "$avvisi" -gt 0 ]; then printf '\nChiusura completata con %s avvisi (KO sopra)%s.\n' "$avvisi" "$1"; exit 3; fi
    printf '\nChiusura completata%s.\n' "$1"; exit 0
}
[ $nowipe = 1 ] && fine ", wipe saltato su richiesta"
titolo "Wipe del magazzino nascosto"
scripts=()
for d in "$HOME"/.claude*; do
    [ -d "$d" ] || continue
    n="$(basename "$d")"
    [ -z "$account" ] || [ "$n" = ".claude-$account" ] || [ "$n" = "$account" ] || continue
    [ -f "$d/hooks/session-end-wipe.sh" ] && scripts+=("$d/hooks/session-end-wipe.sh")
done
if [ ${#scripts[@]} -eq 0 ]; then nota "nessuno script di wipe installato negli account: passo saltato"
elif pgrep -x claude >/dev/null 2>&1; then
    nota "processi Claude Code ancora aperti: wipe rimandato. Chiuderli e lanciare:"
    for s in "${scripts[@]}"; do nota "bash \"$s\""; done
else
    for s in "${scripts[@]}"; do bash "$s" && ok "$s" || ko "$s"; done
fi
fine ""
