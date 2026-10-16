#!/usr/bin/env bash
# Rilettura di un punto di ripristino Veeam: fase 6 della guida del pacchetto
# veeam-linux (GUIDA.md). Un backup non e' tale finche' non e' stato riletto.
#
# Monta l'ultimo punto del lavoro, esegue quattro verifiche e smonta. Dichiara
# l'esito di ciascuna separatamente invece di riassumerle in un verde unico, e
# termina con stato diverso da zero se anche una sola fallisce.
#
# Uso:
#   veeam-verifica.sh --valori ./valori.sh [--punto {ID}] [--lascia-montato]

set -uo pipefail

VALORI=""
PUNTO=""
LASCIA=0
MONTAGGIO="/mnt/backup"

msg()    { printf '%s\n' "$*"; }
titolo() { printf '\n== %s ==\n' "$*"; }
errore() { printf 'ERRORE: %s\n' "$*" >&2; exit 1; }

ESITI=""
registra() { ESITI="${ESITI}$1|$2|$3"$'\n'; }

while [ $# -gt 0 ]; do
  case "$1" in
    --valori)         VALORI="${2:-}"; shift 2 ;;
    --punto)          PUNTO="${2:-}"; shift 2 ;;
    --lascia-montato) LASCIA=1; shift ;;
    -h|--help)        sed -n '2,11p' "$0" | sed 's/^# \{0,1\}//'; exit 2 ;;
    *)                errore "argomento sconosciuto: $1" ;;
  esac
done

[ -n "$VALORI" ] || errore "serve --valori FILE (modello: valori.example.sh)"
[ -f "$VALORI" ] || errore "file dei valori non trovato: $VALORI"
# shellcheck disable=SC1090
. "$VALORI"
for v in NOME_LAVORO DEPOSITO; do
  eval "valore=\${$v:-}"
  [ -n "$valore" ] || errore "il file dei valori non definisce $v"
done

vc() {
  if [ "$(id -u)" -eq 0 ] || id -nG | tr ' ' '\n' | grep -qx veeam; then
    veeamconfig "$@"
  else
    sudo veeamconfig "$@"
  fi
}

uuid() { grep -oE '\{[0-9a-fA-F-]{36}\}' | tail -1; }

# --- Individuazione del punto ----------------------------------------------
if [ -z "$PUNTO" ]; then
  titolo "Backup del lavoro '$NOME_LAVORO'"
  elenco=$(vc backup list 2>/dev/null) || errore "lettura dei backup fallita"
  printf '%s\n' "$elenco"
  BACKUP=$(printf '%s\n' "$elenco" | awk -v n="$NOME_LAVORO" '$1==n' | uuid)
  [ -n "$BACKUP" ] || errore "nessun backup trovato per il lavoro '$NOME_LAVORO'. Dopo una purga dei pacchetti la configurazione sparisce senza che nulla lo segnali: vale la voce E della guida"

  titolo "Punti di ripristino"
  punti=$(vc point list --backupId "$BACKUP" 2>/dev/null) || errore "lettura dei punti fallita"
  printf '%s\n' "$punti"
  PUNTO=$(printf '%s\n' "$punti" | uuid)
  [ -n "$PUNTO" ] || errore "nessun punto di ripristino nel backup $BACKUP"
  msg ""
  msg "Scelto l'ultimo punto elencato: $PUNTO. Con --punto se ne indica un altro."
fi

# --- Montaggio --------------------------------------------------------------
titolo "Montaggio del punto $PUNTO"
msg "Il montaggio espone il contenuto come filesystem percorribile e non scrive nulla sul sistema vivo."
uscita_mount=$(vc point mount --id "$PUNTO" 2>&1) || { printf '%s\n' "$uscita_mount"; errore "montaggio fallito"; }
printf '%s\n' "$uscita_mount"
SESSIONE=$(printf '%s\n' "$uscita_mount" | uuid)

[ -d "$MONTAGGIO" ] || errore "il punto risulta montato ma $MONTAGGIO non esiste"

smonta() {
  [ "$LASCIA" -eq 1 ] && { msg ""; msg "Punto lasciato montato su $MONTAGGIO come richiesto."; return 0; }
  titolo "Smontaggio"
  if [ -n "$SESSIONE" ] && [ "$SESSIONE" != "$PUNTO" ]; then
    vc session stop --id "$SESSIONE" && msg "sessione di montaggio $SESSIONE chiusa"
  else
    msg "L'identificativo della sessione di montaggio non e' stato riconosciuto nell'uscita del comando."
    msg "Lo smontaggio va fatto a mano: la sessione si trova con 'veeamconfig session list' e si chiude con"
    msg "  veeamconfig session stop --id {IDENTIFICATIVO-DELLA-SESSIONE-DI-MONTAGGIO}"
    msg "L'identificativo da usare e' quello della sessione di montaggio, non quello del punto."
  fi
  msg "contenuto di $MONTAGGIO dopo lo smontaggio: $(ls -A "$MONTAGGIO" 2>/dev/null | wc -l) voci"
}
trap smonta EXIT

# --- Verifica 1: presenza di ogni filesystem incluso ------------------------
titolo "Verifica 1, presenza di cio' che si teme manchi"
esito1=0
IFS=',' read -r -a percorsi <<< "${INCLUDI:-/}"
for p in "${percorsi[@]}"; do
  [ -n "$p" ] || continue
  if [ "$p" = "/" ]; then bersaglio="$MONTAGGIO"; else bersaglio="$MONTAGGIO$p"; fi
  n=$(ls -A "$bersaglio" 2>/dev/null | wc -l)
  if [ "$n" -gt 0 ]; then
    msg "ok    $p  ->  $bersaglio ($n voci)"
  else
    msg "vuoto $p  ->  $bersaglio"
    esito1=1
  fi
done
if [ "$esito1" -eq 0 ]; then
  registra "1" "superata" "ogni punto di innesto incluso ha contenuto dentro l'archivio"
else
  registra "1" "FALLITA" "un punto di innesto incluso e' vuoto dentro l'archivio: vale la voce G della guida"
fi

# --- Verifica 2: confronto per impronta -------------------------------------
titolo "Verifica 2, confronto per impronta fra sistema vivo e archivio"
esito2=0
if [ -z "${CAMPIONI:-}" ]; then
  msg "CAMPIONI non e' definito nel file dei valori: la verifica non e' stata eseguita."
  registra "2" "NON ESEGUITA" "CAMPIONI non definito"
else
  IFS=',' read -r -a campioni <<< "$CAMPIONI"
  for f in "${campioni[@]}"; do
    [ -n "$f" ] || continue
    if [ ! -r "$f" ]; then msg "saltato $f (non leggibile sul sistema vivo)"; esito2=1; continue; fi
    if [ ! -r "$MONTAGGIO$f" ]; then msg "assente $f dentro l'archivio"; esito2=1; continue; fi
    a=$(sha256sum "$f" | awk '{print $1}')
    b=$(sha256sum "$MONTAGGIO$f" | awk '{print $1}')
    if [ "$a" = "$b" ]; then msg "uguale  $f"; else msg "DIVERSO $f"; esito2=1; fi
  done
  if [ "$esito2" -eq 0 ]; then
    registra "2" "superata" "i file campione sono identici fra vivo e archivio"
  else
    registra "2" "FALLITA" "almeno un file campione manca o differisce"
  fi
fi

# --- Verifica 3: conteggio ---------------------------------------------------
titolo "Verifica 3, conteggio"
msg "Un confronto per impronta prova che i file scelti sono identici e non dice nulla dei file non scelti: da solo non distingue una copia integrale da una copia parziale fatta bene."
albero="${ALBERO_CONTEGGIO:-$HOME}"
if [ -d "$albero" ] && [ -d "$MONTAGGIO$albero" ]; then
  vivo=$(find "$albero" 2>/dev/null | wc -l)
  arch=$(find "$MONTAGGIO$albero" 2>/dev/null | wc -l)
  msg "albero: $albero    vivo=$vivo  archivio=$arch"
  if [ "$arch" -ge "$vivo" ]; then
    registra "3" "superata" "l'archivio contiene almeno tanti elementi quanti il vivo ($arch contro $vivo) su $albero"
  else
    registra "3" "FALLITA" "l'archivio contiene meno elementi del vivo ($arch contro $vivo) su $albero"
  fi
  msg "Il conteggio e' preso dopo la corsa, quindi una differenza piccola puo' venire da file nati nel frattempo: va letta, non ignorata."
else
  msg "albero non confrontabile: $albero"
  registra "3" "NON ESEGUITA" "l'albero $albero non esiste sul vivo o dentro l'archivio"
fi

# --- Verifica 4: il deposito non e' dentro se stesso -------------------------
titolo "Verifica 4, il deposito non e' finito dentro l'archivio"
msg "Si verifica per assenza, non deducendolo dalla dimensione dell'archivio."
if [ -d "$MONTAGGIO$DEPOSITO" ] && [ "$(ls -A "$MONTAGGIO$DEPOSITO" 2>/dev/null | wc -l)" -gt 0 ]; then
  msg "il deposito $DEPOSITO ha contenuto dentro l'archivio"
  registra "4" "FALLITA" "il lavoro ha copiato il proprio deposito: vale la voce F della guida"
else
  msg "il deposito $DEPOSITO e' assente o vuoto dentro l'archivio"
  registra "4" "superata" "il deposito non e' stato copiato dentro se stesso"
fi

# --- Riepilogo ---------------------------------------------------------------
titolo "Riepilogo"
printf '%s' "$ESITI" | while IFS='|' read -r n stato nota; do
  [ -n "$n" ] || continue
  printf 'verifica %s: %-13s %s\n' "$n" "$stato" "$nota"
done

if printf '%s' "$ESITI" | grep -q '|FALLITA|'; then
  msg ""
  msg "Almeno una verifica e' fallita: il backup non si dichiara riletto."
  exit 1
fi
if printf '%s' "$ESITI" | grep -q '|NON ESEGUITA|'; then
  msg ""
  msg "Nessuna verifica e' fallita, ma almeno una non e' stata eseguita: il backup si dichiara riletto in parte, e la parte mancante va detta."
  exit 2
fi
msg ""
msg "Tutte le verifiche sono superate: il punto e' stato riletto."
msg "Resta la prova completa, cioe' ripristinare davvero su una macchina di prova o in una macchina virtuale e avviare il risultato: finche' non e' fatta, la voce corrispondente del registro delle pendenze resta aperta."
