#!/usr/bin/env python3
"""Dice se il .claude del template e avanti rispetto all'ultima passata di allineamento.

La propagazione di una modifica del template ai progetti istanziati e un comando solo,
`allinea-tutti.ps1 -Applica`, ma va ricordato: il 2026-09-29 dodici progetti sono rimasti
con le norme vecchie per una giornata perché nessuno sapeva che la passata andava rifatta.
Una regola scritta che dice di ricordarlo non basta, per la stessa ragione per cui non
bastava la memoria di chi chiudeva; lo dice quindi `chiudi` sul template, dopo il push,
chiamando questo strumento.

Il confronto e deterministico: ogni progetto del registro `_notes/allineamento/registro.json`
porta l'albero `.claude` del template contro cui e stato misurato l'ultima volta, e se uno
solo e diverso da quello di HEAD la passata non è stata fatta su questo stato del template.
Un registro assente vuol dire che non ne e mai stata fatta una.

Uso, dalla radice del template:
    python .claude/templates/tools/passata-in-sospeso.py

Esce con 0 se non c'è niente da propagare, con 1 se la passata va fatta, con 2 se non
e il template o git non risponde.
"""
import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    radice = Path.cwd()
    if not (radice / ".claude/PROJECT-SYSTEM.md").is_file() or not (radice / ".claude/templates/PACKAGES.md").is_file():
        print("non e la radice del template", file=sys.stderr)
        return 2
    r = subprocess.run(["git", "rev-parse", "HEAD:.claude"], capture_output=True, text=True, cwd=radice)
    if r.returncode != 0:
        print("git non risponde: " + r.stderr.strip(), file=sys.stderr)
        return 2
    albero = r.stdout.strip()
    registro = radice / "_notes/allineamento/registro.json"
    comando = ('powershell -NoProfile -ExecutionPolicy Bypass -File '
               '".claude/templates/tools/allinea-tutti.ps1" -Applica')
    if not registro.is_file():
        print("nessuna passata registrata: per portare questo stato del template ai progetti lanciare")
        print("   " + comando)
        return 1
    try:
        voci = json.loads(registro.read_text(encoding="utf-8"))
    except ValueError:
        print("registro illeggibile: " + str(registro), file=sys.stderr)
        return 2
    # solo i progetti che esistono ancora: il registro conserva anche le voci delle prove
    # lanciate su cartelle temporanee, che non verranno mai rimisurate
    misurati = [v for k, v in voci.items() if isinstance(v, dict) and v.get("template_albero_claude")
                and Path(k).is_dir() and "\\temp\\" not in k.lower() and "/temp/" not in k.lower()]
    indietro = [v for v in misurati if v["template_albero_claude"] != albero]
    if misurati and not indietro:
        print("passata gia fatta su questo stato del template (albero .claude %s)" % albero[:7])
        return 0
    print("il .claude del template e cambiato dall'ultima passata (%d progetti misurati su un "
          "albero diverso): per propagarlo lanciare" % len(indietro))
    print("   " + comando)
    print("e poi committare i progetti che la passata elenca come applicati")
    return 1


if __name__ == "__main__":
    sys.exit(main())
