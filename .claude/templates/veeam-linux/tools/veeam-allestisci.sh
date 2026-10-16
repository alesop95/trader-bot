#!/usr/bin/env bash
# Allestimento di Veeam Agent for Linux su una macchina Linux.
# Attua le fasi da 0 a 5 della guida del pacchetto veeam-linux (GUIDA.md).
#
# Lo script raccomanda e non decide: "controlli" stampa i fatti della macchina
# e un blocco di valori proposto, che va riletto e corretto prima di proseguire.
# Le tre decisioni che cambiano da una macchina all'altra (variante del
# pacchetto, percorsi inclusi, collocazione del deposito) restano di chi esegue.
#
# Uso:
#   veeam-allestisci.sh controlli
#   veeam-allestisci.sh --valori ./valori.sh installa
#   veeam-allestisci.sh --valori ./valori.sh configura
#   veeam-allestisci.sh --valori ./valori.sh esegui [--pieno] [--attendi]
#   veeam-allestisci.sh --valori ./valori.sh stato

set -uo pipefail

VALORI=""
SOTTOCOMANDO=""
PIENO=0
ATTENDI=0

msg()    { printf '%s\n' "$*"; }
titolo() { printf '\n== %s ==\n' "$*"; }
errore() { printf 'ERRORE: %s\n' "$*" >&2; exit 1; }
avviso() { printf 'ATTENZIONE: %s\n' "$*" >&2; }

uso() {
  sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'
  exit 2
}

while [ $# -gt 0 ]; do
  case "$1" in
    --valori)  VALORI="${2:-}"; shift 2 ;;
    --pieno)   PIENO=1; shift ;;
    --attendi) ATTENDI=1; shift ;;
    -h|--help) uso ;;
    -*)        errore "opzione sconosciuta: $1" ;;
    *)         SOTTOCOMANDO="$1"; shift ;;
  esac
done

[ -n "$SOTTOCOMANDO" ] || uso

# --- Privilegi --------------------------------------------------------------
# veeamconfig e' un collegamento a /usr/sbin/veeamworker, -rwxr-x--- root:veeam:
# gira da root oppure da una sessione che porta il gruppo veeam. L'appartenenza
# al gruppo si legge al login, quindi la sessione da cui si installa non ce l'ha.
vc() {
  if [ "$(id -u)" -eq 0 ] || id -nG | tr ' ' '\n' | grep -qx veeam; then
    veeamconfig "$@"
  else
    sudo veeamconfig "$@"
  fi
}

carica_valori() {
  [ -n "$VALORI" ] || errore "serve --valori FILE per il sottocomando '$SOTTOCOMANDO' (modello: valori.example.sh)"
  [ -f "$VALORI" ] || errore "file dei valori non trovato: $VALORI"
  # shellcheck disable=SC1090
  . "$VALORI"
  for v in PACCHETTO LIVELLO VERSIONE_REPO DEPOSITO NOME_DEPOSITO NOME_LAVORO PUNTI; do
    eval "valore=\${$v:-}"
    [ -n "$valore" ] || errore "il file dei valori non definisce $v"
  done
  TIPO_DEPOSITO="${TIPO_DEPOSITO:-local}"
  case "$TIPO_DEPOSITO" in
    local) : ;;
    smb)
      [ -n "${SMB_UTENTE:-}" ] || errore "TIPO_DEPOSITO e' smb ma SMB_UTENTE non e' definito"
      case "$DEPOSITO" in
        //*) : ;;
        *) errore "TIPO_DEPOSITO e' smb ma DEPOSITO non ha la forma //server/condivisione: $DEPOSITO" ;;
      esac ;;
    *) errore "TIPO_DEPOSITO sconosciuto: $TIPO_DEPOSITO (local oppure smb)" ;;
  esac
  if [ "$LIVELLO" = "fileLevel" ] && [ -z "${INCLUDI:-}" ]; then
    errore "LIVELLO e' fileLevel ma INCLUDI e' vuoto: ogni punto di innesto da salvare va nominato"
  fi
}

# --- Fase 0: controlli ------------------------------------------------------
cmd_controlli() {
  titolo "Macchina"
  msg "host:    $(hostname)"
  msg "sistema: $( . /etc/os-release 2>/dev/null; printf '%s' "${PRETTY_NAME:-sconosciuto}" )"
  msg "kernel:  $(uname -r)"
  msg "utente:  $(id -un)  gruppi: $(id -nG)"

  titolo "Volumi"
  lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT | grep -v '^loop'

  local lvm="no"
  if lsblk -rno TYPE 2>/dev/null | grep -qx lvm; then lvm="si"; fi
  msg ""
  msg "strato LVM presente: $lvm"

  titolo "Filesystem montati"
  df -hT -x tmpfs -x devtmpfs -x squashfs -x efivarfs

  # Un file sparso dichiara una dimensione molto maggiore dei blocchi che
  # occupa davvero: du conta i blocchi, una lettura sequenziale legge la
  # dimensione apparente, e il totale che il lavoro dichiara e' calcolato a
  # blocchi. Non si vede quindi da nessuna parte, e si manifesta solo come una
  # corsa che legge molto piu' di quanto la macchina contenga e non finisce mai.
  # Caso osservato il 2026-10-15: un disco virtuale di Docker Desktop fermo da
  # nove mesi, 376,6 GB apparenti contro 1,7 GB occupati, che da solo moltiplicava
  # per otto la durata di ogni corsa.
  titolo "File sparsi (dimensione apparente molto maggiore dei blocchi occupati)"
  local sparsi
  sparsi=$(find / /home -xdev -type f -size +2G -printf '%s\t%b\t%p\n' 2>/dev/null \
    | awk -F'\t' '{app=$1; occ=$2*512; if (occ > 0 && app > occ*1.5) printf "  apparente=%.1f GB  occupato=%.1f GB  %s\n", app/1073741824, occ/1073741824, $3}')
  if [ -n "$sparsi" ]; then
    printf '%s\n' "$sparsi"
    msg ""
    msg "Ognuno di questi va deciso prima di creare il lavoro: se il contenuto e' vivo si include e si accetta il tempo di lettura, se e' un residuo si mette in ESCLUDI. Deciderlo dopo non ripulisce il pieno gia' scritto, perche' una catena forever forward non crea mai pieni nuovi."
  else
    msg "  nessun file sparso oltre i 2 GB"
  fi

  titolo "Presupposti del modulo del kernel"
  msg "header per il kernel in uso: $(dpkg -l "linux-headers-$(uname -r)" 2>/dev/null | grep -c '^ii')"
  msg "dkms: $(command -v dkms >/dev/null && echo presente || echo assente)"

  titolo "Veeam gia' installato"
  if dpkg -l 2>/dev/null | grep -E '^ii +(veeam|veeam-nosnap|veeamsnap|blksnap) ' ; then
    avviso "l'agente risulta gia' installato: la fase 1 va saltata, e la configurazione va riverificata con i comandi del programma (voce E della guida)"
  else
    msg "nessun pacchetto veeam installato"
  fi

  # --- Raccomandazione ------------------------------------------------------
  local pacchetto livello nota
  if [ "$lvm" = "si" ]; then
    pacchetto="veeam-nosnap"; livello="volumeLevel"
    nota="i volumi sono LVM, quindi la variante senza modulo prende l'istantanea tramite LVM e il livello di volume e' disponibile senza dipendere dal kernel."
  else
    pacchetto="veeam-nosnap"; livello="fileLevel"
    nota="le partizioni sono semplici, quindi senza il modulo del kernel il livello di volume non e' possibile. Il modulo e' software di terze parti che insegue il kernel e su una distribuzione recente puo' non compilare: se serve l'immagine avviabile, o si prova il pacchetto 'veeam' accettando quel rischio, o la si prende a macchina spenta con Clonezilla."
  fi

  titolo "Raccomandazione"
  msg "$nota"
  msg ""
  msg "Variante consigliata: $pacchetto, livello $livello."
  msg "La tabella che decide sta nella sezione iniziale di GUIDA.md: questa e' una raccomandazione, non una scelta fatta."

  # --- Blocco di valori proposto -------------------------------------------
  local inclusi deposito avanzo base
  inclusi=$(findmnt -rno TARGET,SOURCE,FSTYPE 2>/dev/null \
    | awk '$2 ~ /^\/dev\// && $3 != "squashfs" && $3 != "vfat" {print $1}' \
    | sort -u | paste -sd, -)
  [ -n "$inclusi" ] || inclusi="/"

  # Deposito proposto sul filesystem incluso con piu' spazio libero.
  base=$(df -P -x tmpfs -x devtmpfs -x squashfs 2>/dev/null \
    | awk 'NR>1 {print $4, $6}' | sort -rn | head -1 | awk '{print $2}')
  [ -n "$base" ] || base="/"
  avanzo=$(df -h "$base" 2>/dev/null | awk 'NR>1 {print $4}')
  if [ "$base" = "/" ]; then deposito="/veeam-repo"; else deposito="$base/veeam-repo"; fi

  titolo "Blocco di valori proposto (da rileggere e correggere)"
  cat <<BLOCCO
PACCHETTO="$pacchetto"
LIVELLO="$livello"
VERSIONE_REPO="1.0.11"
DEPOSITO="$deposito"
NOME_DEPOSITO="repo-locale"
NOME_LAVORO="backup-$(hostname)"
INCLUDI="$inclusi"
ESCLUDI="$deposito,/proc,/sys,/dev,/run,/tmp,/snap,/mnt,/media"
PUNTI="2"
CAMPIONI="/etc/fstab,/etc/hostname"
ALBERO_CONTEGGIO="\$HOME"
DESTINAZIONE_ESTERNA=""
BLOCCO

  msg ""
  msg "Il deposito proposto sta su $base, che dichiara $avanzo liberi ed e' incluso nel backup: per questo compare anche in ESCLUDI."
  msg "VERSIONE_REPO non e' misurata qui: e' il solo valore che invecchia da solo e va verificato sul sito del produttore."
}

# --- Fase 1: installare -----------------------------------------------------
cmd_installa() {
  carica_valori
  local url="https://repository.veeam.com/backup/linux/agent/dpkg/debian/public/pool/veeam/v/veeam-release-deb/veeam-release-deb_${VERSIONE_REPO}_amd64.deb"

  titolo "Repository di Veeam"
  curl -sSL -o /tmp/veeam-release-deb.deb "$url" || errore "scaricamento del pacchetto di repository fallito: $url"
  sudo dpkg -i /tmp/veeam-release-deb.deb || errore "installazione del pacchetto di repository fallita"
  sudo apt update || errore "apt update fallito"

  titolo "Agente ($PACCHETTO)"
  # cifs-utils non e' una comodita': la documentazione Veeam lo dichiara
  # necessario perche' l'agente monta la condivisione con il client cifs del
  # kernel, e senza quel pacchetto il deposito SMB non si crea.
  local pacchetti="$PACCHETTO"
  [ "$TIPO_DEPOSITO" = "smb" ] && pacchetti="$pacchetti cifs-utils"
  if ! sudo apt install -y $pacchetti; then
    avviso "installazione fallita. Se si tratta della variante con modulo, il registro di compilazione sta in /var/lib/dkms/<modulo>/<versione>/build/make.log: la voce D della guida dice come distinguere un ambiente incompleto da un modulo scritto per un kernel precedente."
    exit 1
  fi

  titolo "Servizio"
  systemctl is-active veeamservice || avviso "veeamservice non risulta attivo"

  titolo "Contratti (fase 2)"
  msg "Il comando che segue chiede di accettare due contratti e attende 'yes' per ciascuno."
  msg "Non ha redirezione, di proposito: con l'uscita rediretta la domanda finisce nel file e il terminale sembra bloccato (voce A della guida)."
  vc repository list

  titolo "Gruppo veeam"
  # Misurato il 2026-10-15 su Ubuntu 26.04 con l'agente 6.3.2.1501:
  # l'installazione crea il gruppo e NON vi aggiunge l'utente, quindi il gruppo
  # resta vuoto e ogni comando passa da sudo finche' non lo si aggiunge a mano.
  # Non si da' quindi per scontato: si guarda.
  if getent group veeam | cut -d: -f4 | tr ',' '\n' | grep -qx "$(id -un)"; then
    msg "l'utente $(id -un) appartiene gia' al gruppo veeam"
  else
    msg "il gruppo veeam non contiene $(id -un): l'installazione non ve lo ha aggiunto."
    msg "Senza quel gruppo ogni comando dell'agente passa da sudo. Per toglierlo di mezzo:"
    msg ""
    msg "  sudo usermod -aG veeam $(id -un)"
    msg ""
  fi
  msg "In entrambi i casi serve una sessione nuova: un processo riceve i propri gruppi al login e non li rilegge mai piu', quindi questa sessione non li vedra' comunque."
}

# --- Fasi 3 e 4: configurare ------------------------------------------------
cmd_configura() {
  carica_valori

  titolo "Contratti e stato corrente"
  # Senza cattura, cosi' una eventuale richiesta di accettazione resta visibile.
  vc repository list || errore "veeamconfig non risponde: se il messaggio e' 'Permission denied', vale la voce B della guida"

  local depositi lavori
  depositi=$(vc repository list 2>/dev/null) || errore "lettura dei depositi fallita"
  lavori=$(vc job list 2>/dev/null)          || errore "lettura dei lavori fallita"

  titolo "Fase 3, deposito"
  if printf '%s\n' "$depositi" | awk 'NR>1 {print $1}' | grep -Fxq "$NOME_DEPOSITO"; then
    msg "il deposito '$NOME_DEPOSITO' risulta gia' registrato: nessuna azione"
  elif [ "$TIPO_DEPOSITO" = "smb" ]; then
    msg "Il comando chiede la password di $SMB_UTENTE a terminale: --password si passa senza valore, cosi' la password non entra nella riga di comando ne' nella cronologia della shell."
    if [ -n "${SMB_DOMINIO:-}" ]; then
      vc repository create --name "$NOME_DEPOSITO" --type smb --location "$DEPOSITO" \
         --username "$SMB_UTENTE" --domain "$SMB_DOMINIO" --password \
        || errore "creazione del deposito SMB fallita"
    else
      vc repository create --name "$NOME_DEPOSITO" --type smb --location "$DEPOSITO" \
         --username "$SMB_UTENTE" --password \
        || errore "creazione del deposito SMB fallita. Se il rifiuto riguarda l'autenticazione, la prima cosa da provare e' SMB_DOMINIO con il nome del server"
    fi
    msg "creato."
  else
    vc repository create --name "$NOME_DEPOSITO" --location "$DEPOSITO" --type local \
      || errore "creazione del deposito fallita"
    msg "creato."
  fi
  # La colonna Accessible e' la misura che conta: dopo un errore di
  # autenticazione la riga del deposito puo' comparire lo stesso.
  vc repository list

  titolo "Fase 4, lavoro"
  if printf '%s\n' "$lavori" | awk 'NR>1 {print $1}' | grep -Fxq "$NOME_LAVORO"; then
    msg "il lavoro '$NOME_LAVORO' risulta gia' registrato: nessuna azione"
  else
    # La cifratura si decide qui e non dopo: si cifra il lavoro e non
    # l'archivio, quindi attivarla in seguito significa rifare il backup.
    # Il comando chiede password e suggerimento a terminale.
    local cifra=""
    if [ "${CIFRATURA:-no}" = "si" ]; then
      cifra="--setEncryption"
      msg "Cifratura richiesta: il comando chiedera' una password e un suggerimento a terminale."
      msg "Quella password va custodita fuori da questa macchina: senza di essa l'archivio non si ripristina e nessuno la puo' recuperare."
    fi
    if [ "$LIVELLO" = "volumeLevel" ]; then
      vc job create volumeLevel --name "$NOME_LAVORO" --repoName "$NOME_DEPOSITO" \
         --backupAllSystem --maxPoints "$PUNTI" $cifra \
        || errore "creazione del lavoro fallita. Se il messaggio e' 'Item cannot be backed up without veeam snapshot kernel module', vale la voce C della guida: non c'e' nulla da correggere nella configurazione, va cambiata la variante o il livello"
    else
      vc job create fileLevel --name "$NOME_LAVORO" --repoName "$NOME_DEPOSITO" \
         --includeDirs "$INCLUDI" --excludeDirs "${ESCLUDI:-}" --nosnap --maxPoints "$PUNTI" $cifra \
        || errore "creazione del lavoro fallita"
    fi
    msg "creato."
  fi
  vc job list

  # Pianificazione. Senza ORARIO il lavoro resta manuale, che e' il difetto:
  # una pianificazione si aggiunge in un comando, una pianificazione sbagliata
  # si scopre quando serve il backup.
  if [ -n "${ORARIO:-}" ]; then
    titolo "Pianificazione"
    vc schedule set --jobName "$NOME_LAVORO" --daily --at "$ORARIO" \
      || errore "pianificazione fallita"
    vc schedule show --jobName "$NOME_LAVORO"
    msg ""
    msg "Il pieno attivo resta deliberatamente non pianificato: e' cio' che tiene la catena forever forward, cioe' un pieno solo che assorbe il punto piu' vecchio quando la finestra si riempie. Pianificarlo con 'veeamconfig schedule activefull' produrrebbe pieni nuovi e indipendenti, che e' una scelta diversa e va presa apposta."
  else
    msg ""
    msg "ORARIO non e' definito nel file dei valori: il lavoro resta manuale e nessuna corsa partira' da sola."
  fi

  case ",${ESCLUDI:-}," in
    *",$DEPOSITO,"*) : ;;
    *) avviso "il deposito $DEPOSITO non compare in ESCLUDI: se sta dentro un percorso incluso, il lavoro copiera' se stesso (voce F della guida)" ;;
  esac
}

# --- Fase 5: eseguire -------------------------------------------------------
cmd_esegui() {
  carica_valori

  titolo "Avvio del lavoro"
  if [ "$PIENO" -eq 1 ]; then
    msg "con --activeFull: punto pieno e indipendente, che costa altrettanto spazio del primo e non eredita dipendenze"
    vc job start --name "$NOME_LAVORO" --activeFull || errore "avvio fallito"
  else
    msg "senza --activeFull: punto incrementale, che dipende dal pieno precedente e non si porta fuori da solo"
    vc job start --name "$NOME_LAVORO" || errore "avvio fallito"
  fi

  if [ "$ATTENDI" -eq 0 ]; then
    msg ""
    msg "Il lavoro prosegue in secondo piano. L'avanzamento si segue da qualunque sessione:"
    msg "  df -h '$DEPOSITO'"
    msg "  ps -eo etime,cmd | grep -E 'veeamjobman|veeamagent' | grep -v grep"
    msg "A corsa finita l'esito va letto: 'veeamconfig session list', perche' un lavoro che finisce non e' un lavoro che riesce."
    return 0
  fi

  titolo "Attesa"
  while pgrep -x veeamjobman >/dev/null 2>&1 || pgrep -x veeamagent >/dev/null 2>&1; do
    printf '%s  %s\n' "$(date +%H:%M:%S)" "$(df -h "$DEPOSITO" | awk 'NR>1 {print $3" usati, "$4" liberi"}')"
    sleep 30
  done

  titolo "Esito dichiarato"
  msg "Lo stato puo' essere anche Warning o Failed: va letto, non dedotto dal fatto che la corsa sia finita."
  vc session list
}

cmd_stato() {
  carica_valori
  titolo "Depositi";  vc repository list
  titolo "Lavori";    vc job list
  titolo "Backup";    vc backup list
  titolo "Sessioni";  vc session list
  titolo "Spazio del deposito"; df -h "$DEPOSITO"
}

case "$SOTTOCOMANDO" in
  controlli) cmd_controlli ;;
  installa)  cmd_installa ;;
  configura) cmd_configura ;;
  esegui)    cmd_esegui ;;
  stato)     cmd_stato ;;
  *)         errore "sottocomando sconosciuto: $SOTTOCOMANDO" ;;
esac
