#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Converte i sottotitoli VTT in testo leggibile, togliendo la duplicazione.

Perché esiste
--------------
I sottotitoli automatici di YouTube arrivano in forma scorrevole: ogni blocco ripete
quasi interamente il precedente aggiungendo poche parole, così che a video il testo
sembri salire. Convertiti ingenuamente producono un file tre o quattro volte più lungo
del parlato, con ogni frase ripetuta. Questo strumento ricostruisce il testo una volta
sola, e mantiene facoltativamente le marcature temporali.

Il percorso completo per una fonte video, che la regola sulle fonti non recuperabili
prescrive di annotare accanto all'identificativo del video, è questo:

    python -m yt_dlp --skip-download --write-auto-subs --sub-langs "en.*" -o "%(id)s" URL
    python tools/vtt-to-text.py ID.en.vtt --out _notes/fonti/data-fonte.txt

Il download dell'audio non serve: i sottotitoli automatici sono già il risultato del
riconoscimento vocale fatto da YouTube. Serve solo quando i sottotitoli non esistono, e
in quel caso si passa al riconoscimento vocale locale, che nel catalogo dei pacchetti
è `voicestudio` e che scrive nella stessa cartella con la stessa convenzione di nome.

Uso
---
    python tools/vtt-to-text.py FILE.vtt
    python tools/vtt-to-text.py FILE.vtt --out testo.txt --timestamps
"""

import argparse
import io
import re
import sys

RE_TIME = re.compile(r"^(\d{2}:\d{2}:\d{2}\.\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2}\.\d{3})")
RE_TAG = re.compile(r"<[^>]+>")


def parse(path):
    """Ritorna una lista di (inizio, testo) senza duplicazioni."""
    with io.open(path, encoding="utf-8", errors="replace") as fh:
        righe = fh.read().splitlines()

    blocchi = []
    inizio = None
    buffer = []
    for riga in righe:
        m = RE_TIME.match(riga.strip())
        if m:
            if inizio is not None and buffer:
                blocchi.append((inizio, " ".join(buffer).strip()))
            inizio = m.group(1)
            buffer = []
            continue
        if riga.startswith("WEBVTT") or riga.startswith("Kind:") or riga.startswith("Language:"):
            continue
        testo = RE_TAG.sub("", riga).strip()
        if testo:
            buffer.append(testo)
    if inizio is not None and buffer:
        blocchi.append((inizio, " ".join(buffer).strip()))

    # Deduplicazione: ogni blocco dei sottotitoli scorrevoli ripete la coda del
    # precedente. Si tiene solo la parte nuova, cercando la sovrapposizione più lunga.
    uscita = []
    accumulato = ""
    for inizio, testo in blocchi:
        if not testo:
            continue
        if testo in accumulato[-len(testo) - 1:] if testo else False:
            continue
        nuovo = testo
        massimo = min(len(accumulato), len(testo))
        for k in range(massimo, 0, -1):
            if accumulato.endswith(testo[:k]):
                nuovo = testo[k:]
                break
        nuovo = nuovo.strip()
        if not nuovo:
            continue
        accumulato = (accumulato + " " + nuovo).strip()
        uscita.append((inizio, nuovo))
    return uscita


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("vtt", help="file .vtt da convertire")
    ap.add_argument("--out", help="file di destinazione; senza questo scrive a schermo")
    ap.add_argument("--timestamps", action="store_true",
                    help="mantiene il momento di inizio di ogni frammento")
    ap.add_argument("--wrap", type=int, default=0,
                    help="se maggiore di zero, spezza il testo in paragrafi di N frammenti")
    args = ap.parse_args()

    blocchi = parse(args.vtt)
    if not blocchi:
        print("nessun contenuto riconosciuto in %s" % args.vtt, file=sys.stderr)
        return 1

    pezzi = []
    if args.timestamps:
        for inizio, testo in blocchi:
            pezzi.append("[%s] %s" % (inizio[:8], testo))
        testo_finale = "\n".join(pezzi)
    else:
        parole = " ".join(t for _i, t in blocchi)
        if args.wrap:
            frasi = re.split(r"(?<=[.!?]) +", parole)
            paragrafi, corrente = [], []
            for f in frasi:
                corrente.append(f)
                if len(corrente) >= args.wrap:
                    paragrafi.append(" ".join(corrente))
                    corrente = []
            if corrente:
                paragrafi.append(" ".join(corrente))
            testo_finale = "\n\n".join(paragrafi)
        else:
            testo_finale = parole

    if args.out:
        with io.open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(testo_finale + "\n")
        print("scritti %d frammenti e %d caratteri in %s"
              % (len(blocchi), len(testo_finale), args.out))
    else:
        sys.stdout.write(testo_finale + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
