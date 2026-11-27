#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Esegue nel template le prove del pacchetto agenti-terminale che nessun controllo lanciava.

Perché esiste
-------------
Il pacchetto `agenti-terminale` porta due strumenti in Python con le proprie prove:
`riserva-agenti.py`, che decide se il wrapper di Codex avvia la sessione senza gli strumenti
di delega, con `--autotest`, e `configura-progetti.py`, che rende fidati i progetti approvati
nelle radici di account, con le prove di `tests/test_configura_progetti.py`. Stanno in una
cartella che `chiudi` non percorre, e fino al 2026-11-16 si lanciavano a mano: una prova
affidata alla memoria di chi chiude non gira. Questo strumento le lancia per percorso, così
che `chiudi` le esegua a ogni commit del template.

Le prove usano cartelle temporanee: non leggono e non scrivono le radici di account vere.

Uso
---
    python .claude/templates/tools/test-agenti-terminale.py
"""

import shutil
import subprocess
import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parents[3]
PACCHETTO = RADICE / ".claude" / "templates" / "agenti-terminale"
PROVE = [
    ("riserva-agenti.py --autotest", [sys.executable, str(PACCHETTO / "tools" / "riserva-agenti.py"), "--autotest"]),
    ("tests/test_configura_progetti.py", [sys.executable, "-m", "unittest", "discover", "-s", str(PACCHETTO / "tests")]),
]


def main():
    errori = 0
    prove = list(PROVE)
    if sys.platform == "win32":
        powershell = shutil.which("powershell")
        if not powershell:
            print("PowerShell non trovato")
            return 1
        prove.append(("tests/test-temporanei-agenti.ps1", [
            powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
            str(PACCHETTO / "tests" / "test-temporanei-agenti.ps1"),
        ]))
    for nome, argomenti in prove:
        esito = subprocess.run(argomenti, capture_output=True, text=True,
                               encoding="utf-8", errors="replace")
        uscita = (esito.stdout + esito.stderr).strip()
        ultima = (uscita.splitlines() or ["nessuna uscita"])[-1]
        print("%s: %s" % (nome, ultima))
        if esito.returncode != 0:
            errori += 1
            print(uscita)
    print("test-agenti-terminale: %d problemi" % errori)
    return 1 if errori else 0


if __name__ == "__main__":
    sys.exit(main())
