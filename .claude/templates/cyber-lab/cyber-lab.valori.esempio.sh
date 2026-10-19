# Valori del laboratorio cyber-lab. Si copia in cyber-lab.valori.sh (ignorato da git) e si compila.
# Le immagini si fissano per digest (sha256), mai con un tag mobile come :latest: il digest si legge dal registry al momento dell'adozione.
# Tutto cio' che e' specifico della macchina sta qui, cosi' lo stesso laboratorio si rifa' altrove cambiando solo questo file.

# Console di scansione difensiva. Greenbone Community Edition: vedi la documentazione ufficiale per il compose completo dei suoi container.
export IMG_GREENBONE="greenbone/gvmd@sha256:METTERE_IL_DIGEST_REALE"

# Contenitore leggero con gli strumenti mirati (Nmap, Nuclei, OSV-Scanner). Immagine ufficiale dello strumento scelto, per digest.
export IMG_SCANNER="projectdiscovery/nuclei@sha256:METTERE_IL_DIGEST_REALE"

# Lettura dei log per la funzione Detect (Hayabusa/Chainsaw o un agente Wazuh). Per digest.
export IMG_DETECT="METTERE_IMMAGINE@sha256:METTERE_IL_DIGEST_REALE"

# Bersagli di studio: una macchina propria o un'immagine di addestramento pubblicata apposta. Restano nella rete interna.
# Lasciare vuoto finche' non si sceglie: su.sh avverte se non c'e' nessun bersaglio, ma non lo impone.
export IMG_BERSAGLIO=""

# Nome della rete interna del laboratorio. Resta interna (senza gateway verso l'esterno): non modificare questo principio nel compose.
export LAB_RETE="cyber-lab-interna"
