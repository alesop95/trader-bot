#!/usr/bin/env bash
# Baseline riproducibile per una VPS Ubuntu di fornitore cloud.
#
# Porta una macchina appena creata allo stato "pronta e vergine" da cui si
# prende l'istantanea di ripristino, e lo verifica. Idempotente.
#
# Si esegue SULLA macchina, come utente operativo, con un terminale vero,
# perche' le verifiche che contano richiedono elevazione:
#   scp tools/baseline-vps.sh <alias>:/tmp/
#   ssh -t <alias> 'bash /tmp/baseline-vps.sh --verifica'
#   ssh -t <alias> 'bash /tmp/baseline-vps.sh --applica --ammessi <indirizzo>'
#
# La redirezione dallo standard input funziona su una shell POSIX ma non su
# PowerShell, che non ha l'operatore: la copia preventiva vale su entrambe.
#
# Senza argomenti verifica e basta: non applica nulla finche' non glielo si
# chiede, perche' un errore sul servizio SSH chiude fuori chi lo sta lanciando.
#
# Una regola governa tutto il file: uno stato che lo script non ha potuto
# leggere si dichiara non verificabile, mai buono. Un comando elevato che
# fallisce restituisce un vuoto che somiglia a un'assenza, e un ripiego che
# somiglia a una misura e' peggio di un errore. Il perche' dei singoli passi
# sta in README.md di questo pacchetto.

set -uo pipefail

MODO="verifica"
AMMESSI=""
PORTE_WEB="80,443"

while [ $# -gt 0 ]; do
  case "$1" in
    --applica) MODO="applica" ;;
    --verifica) MODO="verifica" ;;
    --ammessi) AMMESSI="${2:-}"; shift ;;
    --porte-web) PORTE_WEB="${2:-}"; shift ;;
    *) echo "argomento non riconosciuto: $1" >&2; exit 2 ;;
  esac
  shift
done

OPERATIVO="$(id -un)"
ESITO=0
sez() { printf '\n== %s\n' "$1"; }
ok() { printf '   ok   %s\n' "$1"; }
no() { printf '   DA FARE  %s\n' "$1"; ESITO=1; }
boh() { printf '   NON VERIFICABILE  %s\n' "$1"; ESITO=1; }
fatto() { printf '   APPLICATO  %s\n' "$1"; }

if [ "$OPERATIVO" = "root" ]; then
  echo "Non eseguire come amministratore: lo script limita il servizio SSH a chi" >&2
  echo "lo sta lanciando, e come root lo chiuderebbe fuori." >&2
  exit 2
fi

# L'elevazione si accerta una volta sola, e decide che cosa si puo' affermare.
if sudo -n true 2>/dev/null; then
  ELEV=1
elif [ -t 0 ] && sudo -v 2>/dev/null; then
  ELEV=1
else
  ELEV=0
fi
[ "$ELEV" -eq 0 ] && echo "AVVISO: nessuna elevazione disponibile. Le sezioni che la richiedono" \
  && [ "$ELEV" -eq 0 ] && echo "        non riporteranno un esito. Rilancia con ssh -t."
if [ "$ELEV" -eq 0 ] && [ "$MODO" = "applica" ]; then
  echo "Senza elevazione non si applica niente." >&2; exit 2
fi

sez "Identita' della macchina"
echo "   utente operativo: $OPERATIVO"
echo "   host: $(hostnamectl --static 2>/dev/null || hostname)"
echo "   kernel in esecuzione: $(uname -r)"
echo "   impronta della chiave di host, da confrontare fuori banda alla prima connessione:"
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub 2>/dev/null | sed 's/^/     /' \
  || echo "     non leggibile"

# ---------------------------------------------------------------------------
sez "1. Utente predefinito dell'immagine del fornitore"
# L'immagine del fornitore porta un utente proprio, con la stessa chiave
# iniettata alla creazione e spesso elevazione senza password. E' una via
# parallela che aggira l'utente operativo e non compare in nessuna consegna.
PREDEF=""
for u in ubuntu debian admin cloud-user ec2-user; do
  if id "$u" >/dev/null 2>&1 && [ "$u" != "$OPERATIVO" ]; then PREDEF="$u"; break; fi
done

if [ -z "$PREDEF" ]; then
  ok "nessun utente predefinito dell'immagine presente"
else
  echo "   trovato: $PREDEF"
  SHELL_PREDEF="$(getent passwd "$PREDEF" | cut -d: -f7)"
  case "$SHELL_PREDEF" in
    /usr/sbin/nologin|/bin/false|/sbin/nologin) ok "shell di accesso revocata" ;;
    *)
      if [ "$MODO" = "applica" ]; then
        sudo usermod -s /usr/sbin/nologin "$PREDEF" && fatto "shell revocata a $PREDEF"
      else
        no "ha ancora una shell di accesso ($SHELL_PREDEF)"
      fi ;;
  esac

  CHIAVI="/home/$PREDEF/.ssh/authorized_keys"
  if [ "$ELEV" -eq 0 ]; then
    boh "chiavi autorizzate di $PREDEF: servirebbe elevazione per leggerle"
  else
    BYTE="$(sudo stat -c %s "$CHIAVI" 2>/dev/null)"
    if [ -z "$BYTE" ]; then
      ok "$PREDEF non ha un file di chiavi autorizzate"
    elif [ "$BYTE" -eq 0 ]; then
      ok "nessuna chiave autorizzata per $PREDEF"
    elif [ "$MODO" = "applica" ]; then
      sudo cp "$CHIAVI" "/root/authorized_keys.$PREDEF.bak-$(date +%Y%m%d)"
      sudo truncate -s 0 "$CHIAVI" && fatto "chiavi di $PREDEF svuotate, copia sotto /root"
    else
      no "$PREDEF ha $BYTE byte di chiavi autorizzate: e' una via di accesso parallela"
    fi
  fi

  if [ "$ELEV" -eq 0 ]; then
    boh "elevazione senza password di $PREDEF: servirebbe elevazione per verificarla"
  else
    SUDOERS="$(sudo grep -rl "^$PREDEF .*NOPASSWD" /etc/sudoers.d/ 2>/dev/null | head -1)"
    if [ -z "$SUDOERS" ]; then
      ok "nessuna elevazione senza password per $PREDEF"
    elif [ "$MODO" = "applica" ]; then
      SALVA="/root/$(basename "$SUDOERS").bak-$(date +%Y%m%d)"
      sudo cp "$SUDOERS" "$SALVA"; sudo rm -f "$SUDOERS"
      if sudo visudo -c >/dev/null 2>&1; then
        fatto "rimossa l'elevazione senza password di $PREDEF"
      else
        sudo cp "$SALVA" "$SUDOERS"
        no "rimozione annullata: l'insieme delle regole non convalidava"
      fi
    else
      no "$PREDEF ha elevazione senza password in $SUDOERS"
    fi
  fi
fi

# ---------------------------------------------------------------------------
sez "2. Servizio SSH"
if [ "$ELEV" -eq 0 ]; then
  boh "configurazione in vigore del servizio: servirebbe elevazione"
  echo "     dal solo file, che puo' non coincidere con cio' che e' in vigore:"
  grep -iE '^(PermitRootLogin|PasswordAuthentication|AllowUsers)' /etc/ssh/sshd_config 2>/dev/null \
    | sed 's/^/       /'
else
  EFF="$(sudo sshd -T 2>/dev/null)"
  val() { echo "$EFF" | grep -i "^$1 " | head -1 | cut -d' ' -f2-; }
  if [ -z "$EFF" ]; then
    boh "il servizio non ha restituito la propria configurazione"
  else
    [ "$(val permitrootlogin)" = "no" ] && ok "amministratore non raggiungibile" \
      || no "l'amministratore puo' entrare via SSH"
    [ "$(val passwordauthentication)" = "no" ] && ok "autenticazione a sola chiave" \
      || no "l'autenticazione per password e' abilitata"
    if echo "$EFF" | grep -qi "^allowusers .*$OPERATIVO"; then
      ok "accesso limitato all'utente operativo"
    elif [ "$MODO" = "applica" ]; then
      sudo cp /etc/ssh/sshd_config "/etc/ssh/sshd_config.bak-$(date +%Y%m%d)"
      echo "AllowUsers $OPERATIVO" | sudo tee -a /etc/ssh/sshd_config >/dev/null
      if sudo sshd -t 2>/dev/null; then
        sudo systemctl reload ssh && fatto "accesso limitato a $OPERATIVO, servizio ricaricato"
        echo "     PROVA ORA una sessione nuova da un altro terminale PRIMA di chiudere questa."
      else
        sudo cp "/etc/ssh/sshd_config.bak-$(date +%Y%m%d)" /etc/ssh/sshd_config
        no "configurazione non valida: ripristinata quella precedente"
      fi
    else
      no "l'accesso non e' limitato al solo utente operativo"
    fi
  fi
fi
echo "   chiavi autorizzate per $OPERATIVO:"
ssh-keygen -lf "$HOME/.ssh/authorized_keys" 2>/dev/null | sed 's/^/     /' || echo "     nessuna"

# ---------------------------------------------------------------------------
sez "3. Registro degli accessi, da leggere PRIMA di restringere"
if [ "$ELEV" -eq 0 ]; then
  boh "registro degli accessi: un conteggio a zero senza elevazione non e' uno zero"
else
  echo "   accessi riusciti, dal primo avvio:"
  sudo last -F -a 2>/dev/null | head -8 | sed 's/^/     /'
  echo "   tentativi falliti nella finestra conservata dal giornale:"
  printf '     %s\n' "$(sudo journalctl -u ssh --no-pager 2>/dev/null \
    | grep -cE 'Failed password|Invalid user')"
fi

# ---------------------------------------------------------------------------
sez "4. Filtro di sistema"
if ! command -v ufw >/dev/null 2>&1; then
  no "il filtro non e' installato"
elif [ "$ELEV" -eq 0 ]; then
  boh "regole del filtro: senza elevazione lo strumento non risponde"
else
  sudo ufw status verbose 2>/dev/null | sed 's/^/     /'
  STATO="$(sudo ufw status 2>/dev/null)"
  if [ -n "$AMMESSI" ]; then
    if echo "$STATO" | grep -q "22/tcp.*$AMMESSI"; then
      ok "porta di amministrazione gia' ristretta a $AMMESSI"
    elif [ "$MODO" = "applica" ]; then
      sudo ufw allow from "$AMMESSI" to any port 22 proto tcp \
        comment 'SSH solo da provenienza ammessa' >/dev/null
      sudo ufw delete allow 22/tcp >/dev/null 2>&1
      sudo ufw delete allow OpenSSH >/dev/null 2>&1
      fatto "porta di amministrazione ristretta a $AMMESSI"
    else
      no "porta di amministrazione aperta a chiunque; passa --ammessi <indirizzo>"
    fi
  else
    echo "     nessuna provenienza indicata: la restrizione non viene toccata"
  fi
  for p in ${PORTE_WEB//,/ }; do
    if echo "$STATO" | grep -q "^$p/tcp"; then
      ok "porta $p ammessa"
    elif [ "$MODO" = "applica" ]; then
      sudo ufw allow "$p/tcp" >/dev/null && fatto "aperta la porta $p"
    else
      no "porta $p non ammessa"
    fi
  done
fi

# ---------------------------------------------------------------------------
sez "5. Aggiornamenti"
[ "$(systemctl is-enabled unattended-upgrades 2>/dev/null)" = "enabled" ] \
  && ok "aggiornamenti non presidiati abilitati" \
  || no "aggiornamenti non presidiati non abilitati"
echo "   pacchetti aggiornabili: $(apt list --upgradable 2>/dev/null | tail -n +2 | wc -l)"
echo "     gli automatismi coprono il solo canale di sicurezza: il resto si accumula"
if [ -f /var/run/reboot-required ]; then
  no "riavvio richiesto: finche' non si riavvia, i nuclei installati non sono attivi"
  echo "     il riavvio e' anche la prova che questa configurazione sopravvive"
  echo "     all'inizializzazione automatica dell'istanza. Si fa adesso, non dopo."
else
  ok "nessun riavvio richiesto"
fi

# ---------------------------------------------------------------------------
sez "6. Servizi attesi"
for s in ssh ufw fail2ban; do
  [ "$(systemctl is-active "$s" 2>/dev/null)" = "active" ] && ok "$s attivo" \
    || no "$s non attivo"
done

# ---------------------------------------------------------------------------
sez "Esito"
if [ "$ESITO" -eq 0 ]; then
  echo "   La macchina e' nello stato di riferimento, e ogni voce e' stata verificata."
  echo "   E' il momento di prendere l'istantanea di ripristino dal pannello."
else
  echo "   Restano scostamenti o voci non verificabili: rileggili prima di applicare."
  [ "$ELEV" -eq 0 ] && echo "   Questo giro non aveva elevazione: rilancialo con ssh -t."
fi
exit "$ESITO"
