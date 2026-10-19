#!/usr/bin/env bash
# Banco di prova di colibri: tiene il motore sotto un tetto di RAM dato e misura la velocita' con l'harness ufficiale del repository.
# Il processo limitato e' il server (coli serve), perche' e' lui a caricare il modello e a leggere gli esperti; l'harness e' solo un client.
# Non scarica modelli e non installa colibri. Svuota la cache dei file prima della corsa (serve sudo) e, se chiesto, copia il modello su ext4.
# Metodo e campi del rapporto vengono dal protocollo ufficiale docs/benchmarking.md di colibri; le regole sulla cache e sul perimetro valgono anche qui.
set -euo pipefail

VALORI=""; MODELLO=""; RAM=""
while [ $# -gt 0 ]; do
  case "$1" in
    --valori) VALORI="$2"; shift 2 ;;
    --modello) MODELLO="$2"; shift 2 ;;
    --ram) RAM="$2"; shift 2 ;;
    *) echo "argomento sconosciuto: $1" >&2; exit 2 ;;
  esac
done
[ -n "$VALORI" ] && [ -n "$MODELLO" ] && [ -n "$RAM" ] || { echo "uso: bench-colibri.sh --valori <file> --modello <nome> --ram <tetto, es. 16G>" >&2; exit 2; }
[ -f "$VALORI" ] || { echo "file dei valori assente: $VALORI" >&2; exit 2; }
# shellcheck disable=SC1090
. "$VALORI"

[ -n "${MODELLI[$MODELLO]:-}" ] || { echo "modello non in tabella: $MODELLO" >&2; exit 2; }
command -v systemd-run >/dev/null || { echo "systemd-run assente: serve systemd per limitare la RAM del solo processo" >&2; exit 2; }
command -v python3 >/dev/null || { echo "python3 assente: serve per l'harness ufficiale" >&2; exit 2; }
[ -x "$COLI_DIR/coli" ] || { echo "motore colibri non compilato in $COLI_DIR/coli" >&2; exit 2; }
# L'harness ufficiale sta in tools/ accanto a coli (build con coli in c/) oppure in c/tools/ (coli a radice): si cerca in entrambi.
HARNESS=""
for cand in "$COLI_DIR/tools/benchmark_http_serving.py" "$COLI_DIR/c/tools/benchmark_http_serving.py"; do
  [ -f "$cand" ] && { HARNESS="$cand"; break; }
done
[ -n "$HARNESS" ] || { echo "harness ufficiale benchmark_http_serving.py non trovato sotto $COLI_DIR" >&2; exit 2; }

SRC="$MAGAZZINO/${MODELLI[$MODELLO]}"
[ -d "$SRC" ] || { echo "modello non presente nel magazzino: $SRC" >&2; exit 2; }

# Dentro WSL il modello non deve stare su /mnt/c o la misura delle letture dal disco e' falsata: copia su ext4 una volta.
RUNDIR="$SRC"
if [ "${COPIA_IN_EXT4:-0}" = "1" ]; then
  RUNDIR="$EXT4_SCRATCH/${MODELLI[$MODELLO]}"
  if [ ! -d "$RUNDIR" ]; then
    echo "copio il modello su ext4: $RUNDIR (una volta sola)"; mkdir -p "$RUNDIR"; cp -r "$SRC/." "$RUNDIR/"
  fi
fi

mkdir -p "$MISURE"
PORTA="${PORTA:-8000}"
MODEL_ID="bench-$MODELLO"
SCOPE="colibri-serve-$MODELLO-$RAM-$$"
WORKLOAD="$(mktemp --suffix=.jsonl)"
REPORT="$MISURE/$MODELLO-$RAM-$(date +%Y%m%d-%H%M%S).json"
printf '{"messages":[{"role":"user","content":%s}]}\n' "$(printf '%s' "$PROMPT_PROVA" | python3 -c 'import json,sys;print(json.dumps(sys.stdin.read()))')" > "$WORKLOAD"
trap 'rm -f "$WORKLOAD"; systemctl --user stop "$SCOPE.scope" 2>/dev/null || true' EXIT

# Svuota la cache dei file prima della corsa, cosi' gli esperti si leggono davvero dal disco. Richiede privilegio.
svuota_cache() {
  if [ "$(id -u)" = "0" ]; then sync; echo 3 > /proc/sys/vm/drop_caches
  elif sudo -n true 2>/dev/null; then sync; sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'
  else echo "ATTENZIONE: cache dei file non svuotata (serve sudo): la prima misura sara' ottimistica." >&2; fi
}

echo "== prova: modello=$MODELLO tetto=$RAM cartella=$RUNDIR porta=$PORTA"
svuota_cache

# Il limite di memoria lo impone --ram a colibri, NON il gruppo di controllo. Misurato il 2026-10-19: un MemoryMax stretto
# non limita la cache degli esperti, la sopprime, tenendola vuota e falsando la prova (vedi docs/filone-llm-locali-senza-gpu.md).
# colibri dimensiona la cache sul proprio --ram; il gruppo di controllo resta solo come muro di sicurezza sopra il budget, non come limite.
CAP_GB="$(printf '%s' "$RAM" | sed -E 's/[Gg].*$//')"
RAM_BUDGET="$CAP_GB"
WALL_GB=$(( CAP_GB + 6 ))

echo "avvio coli serve con --ram $RAM_BUDGET (muro di sicurezza MemoryMax=${WALL_GB}G) ..."
systemd-run --user --scope -p "MemoryMax=${WALL_GB}G" -p "MemorySwapMax=0" --unit "$SCOPE" \
  env COLI_MODEL="$RUNDIR" COLI_API_KEY=local "$COLI_DIR/coli" serve --host 127.0.0.1 --port "$PORTA" --model-id "$MODEL_ID" --ram "$RAM_BUDGET" &
SERVE_BG=$!

# Attesa che l'endpoint risponda (massimo ~120s: un modello grande ci mette a caricare).
echo "attendo l'endpoint /v1 ..."
for _ in $(seq 1 120); do
  if curl -fsS "http://127.0.0.1:$PORTA/v1/models" -H "Authorization: Bearer local" >/dev/null 2>&1; then break; fi
  sleep 1
done

# Harness ufficiale come client: non e' limitato, misura il server che lo e'.
OPENAI_API_KEY=local python3 "$HARNESS" \
  --base-url "http://127.0.0.1:$PORTA/v1" --model "$MODEL_ID" \
  --workload "$WORKLOAD" --concurrency 1 --repeats 3 \
  --max-tokens "$TOKEN_DA_GENERARE" --temperature 0 --timeout 120 --output "$REPORT" || true

# Memoria massima dal gruppo di controllo, se leggibile.
PICCO="n/d"
CG="$(systemctl --user show -p ControlGroup --value "$SCOPE.scope" 2>/dev/null | sed 's#^/##')"
[ -r "/sys/fs/cgroup/$CG/memory.peak" ] && PICCO="$(cat "/sys/fs/cgroup/$CG/memory.peak" 2>/dev/null || echo n/d)"
systemctl --user stop "$SCOPE.scope" 2>/dev/null || true
wait "$SERVE_BG" 2>/dev/null || true

HW="$(nproc)cpu/$(free -g | awk '/Mem:/{print $2"GB"}')"
RIGA="$(date -Is)\t$MODELLO\t$RAM\tpicco=$PICCO\thw=$HW\treport=$(basename "$REPORT")"
printf '%b\n' "$RIGA" | tee -a "$MISURE/$MODELLO.tsv"
echo "rapporto completo dell'harness (token, durata, TTFT, byte letti) in: $REPORT"
echo "nota: il rapporto va corredato a mano del perimetro richiesto da docs/benchmarking.md (stato della cache, dimensione e coda delle letture, modello e quantizzazione)."
