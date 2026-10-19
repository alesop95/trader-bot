#!/usr/bin/env python3
"""Lint degli strumenti Python del template con ruff, alle regole predefinite.

Perché esiste. Il 2026-10-19 un progetto istanziato ha adottato ruff e ha trovato
riscontri in quattro strumenti che sono copie byte per byte del template.
Correggerli là avrebbe creato una divergenza che la propagazione successiva
cancella, quindi il progetto li ha esclusi e ha fatto risalire il difetto. Misurato
qui lo stesso giorno, con le stesse regole: 42 riscontri in 17 strumenti, non 12
in 4, perché quel progetto vedeva solo le copie che aveva istanziato. La regola
che ne è nata sta nella sezione 16 di PROJECT-SYSTEM.md: un controllo di qualità
che un progetto adotta e che trova riscontri nelle copie del template si corregge
nel template, e il template adotta lo stesso controllo sui propri strumenti, perché
una correzione senza controllo regredisce al primo strumento nuovo.

Le regole sono E4, E7, E9 e F, scritte qui e non lasciate al predefinito di ruff:
sono il predefinito fino alla 0.14, cioè il minimo che un progetto adotta senza
configurare niente. Il predefinito cambia con la versione, e il 2026-10-19 lo ha
mostrato al primo commit: con ruff 0.17.1 lo stesso albero, a zero con la 0.14.2,
dava 1.098 riscontri di regole nuove. Un controllo il cui esito dipende dalla
versione installata non dice niente sul codice.
Restano fuori le fixture di md-unwrap, che sono materiale di confronto byte per
byte e non codice.

Se ruff non è installato il controllo fallisce, e lo dice: un controllo che si
salta da solo quando manca il suo strumento è un controllo solo sulla carta. Si
cerca prima l'eseguibile sul PATH, poi il modulo dell'interprete corrente.

Uso:
    python .claude/templates/tools/lint-strumenti.py
    python .claude/templates/tools/lint-strumenti.py --radice E:/template-claude-developing

Esce con 0 senza riscontri, con 1 se ce ne sono o se ruff manca.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

PERCORSI = [".claude", "tools"]
REGOLE = "E4,E7,E9,F"
ESCLUSI = [".claude/templates/md-unwrap/tests/fixtures"]


def comando_ruff() -> list[str] | None:
    exe = shutil.which("ruff")
    if exe:
        return [exe]
    r = subprocess.run([sys.executable, "-m", "ruff", "--version"], capture_output=True)
    if r.returncode == 0:
        return [sys.executable, "-m", "ruff"]
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Lint degli strumenti Python del template con ruff.")
    ap.add_argument("--radice", default=".", help="radice del repository, per default la cartella corrente")
    a = ap.parse_args()
    radice = Path(a.radice).resolve()
    ruff = comando_ruff()
    if not ruff:
        print("ruff non e' installato: il lint degli strumenti non puo' girare.")
        print("Si installa una volta con:  python -m pip install --user ruff")
        return 1
    percorsi = [p for p in PERCORSI if (radice / p).exists()]
    # --no-cache: la cartella .ruff_cache sotto .claude/templates/ fa fallire check-catalogo,
    # che vi vede un pacchetto senza voce; misurato alla prima corsa, il 2026-10-19.
    cmd = ruff + ["check", "--isolated", "--no-cache", "--select", REGOLE, "--output-format", "concise", "--extend-exclude", ",".join(ESCLUSI), *percorsi]
    r = subprocess.run(cmd, cwd=radice, capture_output=True, text=True, encoding="utf-8", errors="replace")
    uscita = (r.stdout + r.stderr).strip()
    if r.returncode == 0:
        print("lint-strumenti: nessun riscontro di ruff")
        return 0
    print(uscita)
    return 1


if __name__ == "__main__":
    sys.exit(main())
