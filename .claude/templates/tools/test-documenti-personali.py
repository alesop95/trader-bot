#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Esegue nel template le prove degli strumenti che attuano la regola dei documenti personali.

Perché esiste
-------------
La regola `.claude/rules/documenti-personali.md` è sempre attiva dal 2026-10-07, e il
proprietario ha chiesto che la sua robustezza sia dimostrata da una prova e non soltanto
dichiarata. Gli strumenti che la attuano hanno ciascuno la propria prova, `--autotest`:
`anonymization/tools/Test-Anonymization.py`, che riconosce IBAN e numeri di carta nei file
pubblicabili, e `doc-ingest/doc-ingest.py`, che esclude i documenti personali prima di aprirli.
Nel template quei pacchetti stanno in cartelle che `chiudi` non percorre, e
`Test-Anonymization.py` senza il file di pattern di un progetto si ferma per scelta; questo
strumento lancia le due prove per percorso, così che `chiudi` le esegua a ogni commit del
template. Nei progetti istanziati `chiudi` lancia le stesse prove sulle copie in `tools/`.

Controlla anche che la regola esista e che si dichiari da caricare sempre, perché una regola
che non si carica non protegge niente anche quando gli strumenti sono giusti.

Uso
---
    python .claude/templates/tools/test-documenti-personali.py
"""

import subprocess
import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parents[3]
PROVE = [
    RADICE / ".claude" / "templates" / "anonymization" / "tools" / "Test-Anonymization.py",
    RADICE / ".claude" / "templates" / "doc-ingest" / "doc-ingest.py",
]
REGOLA = RADICE / ".claude" / "rules" / "documenti-personali.md"


def main():
    errori = 0
    testo = REGOLA.read_text(encoding="utf-8") if REGOLA.exists() else ""
    if "da caricare sempre" not in testo:
        errori += 1
        print("la regola %s manca o non si dichiara da caricare sempre" % REGOLA.relative_to(RADICE))
    for prova in PROVE:
        esito = subprocess.run([sys.executable, str(prova), "--autotest"], capture_output=True,
                               text=True, encoding="utf-8", errors="replace")
        ultima = (esito.stdout.strip().splitlines() or ["nessuna uscita"])[-1]
        print("%s: %s" % (prova.relative_to(RADICE).as_posix(), ultima))
        if esito.returncode != 0:
            errori += 1
            print(esito.stdout + esito.stderr)
    print("test-documenti-personali: %d problemi" % errori)
    return 1 if errori else 0


if __name__ == "__main__":
    sys.exit(main())
