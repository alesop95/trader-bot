# Valori del banco di prova llm-local. Si copia in llm-local.valori.sh (ignorato da git) e si compila con i percorsi reali.
# Nessun percorso di questa macchina vive nel banco: tutto sta qui, perche' lo stesso studio si rifaccia altrove cambiando solo questo file.

# Cartella del motore colibri compilato (contiene l'eseguibile ./coli).
COLI_DIR="$HOME/colibri"

# Magazzino stabile dei modelli. Su una macchina di sviluppo con WSL conviene una cartella Windows (es. /mnt/c/colibri-models),
# ma la corsa copia il modello su disco veloce ext4 prima di misurare: vedi COPIA_IN_EXT4.
MAGAZZINO="/mnt/c/colibri-models"

# Cartella ext4 veloce dove la corsa copia il modello prima di misurarlo (fuori da /mnt/c, per non falsare le letture dal disco).
EXT4_SCRATCH="$HOME/colibri-run"
COPIA_IN_EXT4=1

# Dove finiscono le righe di misura (una per modello e per tetto di RAM). Fuori dal repository.
MISURE="$MAGAZZINO/misure"

# Modelli da provare: nome logico -> sottocartella dentro il magazzino. Il nome logico si passa a --modello.
declare -A MODELLI=(
  [olmoe]="OLMoE"
  [qwen36]="Qwen3.6-35B-A3B"
  [deepseek-v4-flash]="DeepSeek-V4-Flash"
)

# Prompt fisso della prova e numero di parole da generare. Lo stesso per ogni corsa, altrimenti le misure non si confrontano.
PROMPT_PROVA="Spiega in tre frasi che cos'e' un sistema di controllo di versione."
TOKEN_DA_GENERARE=200

# Tetti di RAM da provare, passati a --ram. Il tetto conta anche la cache dei file (gruppo di controllo).
# Esempio: 16G e 32G per rispondere alla domanda dei due tagli.
