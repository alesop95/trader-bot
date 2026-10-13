"""Prepara da codice gli estratti di un lotto di documenti, perche' un modello economico li schedi.

Nato in un progetto istanziato il 2026-10-06 (diy-2way-monitors-home, MS-212 e MS-213), dove
le schede di fonte di un corpus di migliaia di documenti convertiti si scrivono con il modello
economico. Il lavoro meccanico, cioe' scegliere i documenti, escludere quelli personali e tagliare
lo scheletro e le prime parole, resta nel codice; il modello legge soltanto gli estratti.

Lavora su una cache di doc-ingest, o su qualunque cartella di file Markdown convertiti: percorre
i file .md, salta _INDEX.md, filtra per sottostringa del percorso relativo, esclude i documenti
personali secondo un file di schemi (regola documenti-personali.md) e scrive un estratto per
documento piu' un elenco.json. La scelta e' deterministica, in ordine di percorso, e --salta
permette i lotti successivi.

Uso:
    python estratti-lotto.py CACHE --filtro "cartella" --quanti 50 --parole 800 --dest _notes/lotti/L2-01
    python estratti-lotto.py CACHE --filtro "cartella" --quanti 50 --salta 50 --dest _notes/lotti/L2-02

Il file di schemi, --esclusi, contiene un'espressione regolare per riga confrontata con il
percorso relativo; senza quel file lo strumento si ferma, perche' un lotto di massa senza
esclusione dei documenti personali e' esattamente il caso che la regola esiste per impedire.
"""
import argparse
import json
import re
import sys
from pathlib import Path


def carica_schemi(p):
    if not p.exists():
        sys.exit(f"manca {p}: senza schemi di esclusione dei documenti personali non si procede")
    righe = (r.strip() for r in p.read_text(encoding="utf-8").splitlines())
    return [re.compile(r, re.IGNORECASE) for r in righe if r and not r.startswith("#")]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cache", help="cartella con i file .md convertiti")
    ap.add_argument("--filtro", default="", help="sottostringa del percorso relativo, per esempio una cartella")
    ap.add_argument("--quanti", type=int, default=50)
    ap.add_argument("--salta", type=int, default=0)
    ap.add_argument("--parole", type=int, default=800, help="parole iniziali dell'estratto")
    ap.add_argument("--minimo", type=int, default=300, help="parole minime del documento")
    ap.add_argument("--esclusi", default="_notes/privacy/esclusi-personali.txt")
    ap.add_argument("--dest", required=True)
    a = ap.parse_args()
    cache = Path(a.cache)
    schemi = carica_schemi(Path(a.esclusi))
    scelti = []
    for f in sorted(cache.rglob("*.md")):
        rel = f.relative_to(cache).as_posix()
        if f.name == "_INDEX.md" or a.filtro.lower() not in rel.lower():
            continue
        # Il percorso completo, perché gli schemi delle cartelle cercano un separatore
        # prima del nome, che il percorso relativo di primo livello non ha.
        if any(s.search(str(f.resolve())) for s in schemi):
            continue
        testo = f.read_text(encoding="utf-8", errors="replace")
        if len(testo.split()) >= a.minimo:
            scelti.append((rel, testo))
    scelti = scelti[a.salta:a.salta + a.quanti]
    dest = Path(a.dest)
    dest.mkdir(parents=True, exist_ok=True)
    elenco = []
    for i, (rel, testo) in enumerate(scelti, 1):
        titoli = [r for r in testo.splitlines() if re.match(r"#{1,3} ", r)][:60]
        parole = testo.split()
        nome = f"{i:03d}.md"
        (dest / nome).write_bytes((
            f"# Estratto {i:03d}\n\nfile: {rel}\nparole totali: {len(parole)}\n\n## Scheletro\n\n"
            + ("\n".join(titoli) or "(nessuna intestazione)")
            + f"\n\n## Prime {min(a.parole, len(parole))} parole\n\n" + " ".join(parole[:a.parole]) + "\n"
        ).encode("utf-8"))
        elenco.append({"estratto": nome, "file": rel, "parole": len(parole)})
    (dest / "elenco.json").write_bytes((json.dumps(elenco, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    print(f"estratti {len(elenco)} in {dest}; parole negli estratti {sum(min(a.parole, e['parole']) for e in elenco)}")


if __name__ == "__main__":
    main()
