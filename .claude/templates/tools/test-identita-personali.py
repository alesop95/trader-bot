#!/usr/bin/env python3
"""Nessun identificativo personale nei file che il template porta nei progetti.

Perché esiste. Fino al commit 74b6f6b il template aveva una regola versionata sulle identità git
di questa macchina che conteneva, accanto al profilo di lavoro, il profilo personale: utente,
email e alias SSH. L'inizializzazione e l'allineamento copiano le regole in ogni progetto, quindi
quel profilo è finito, committato e spinto, nei repository aziendali; il 2026-10-21 lo si è
trovato nella storia di undici di loro, e toglierlo ha richiesto di riscriverne la storia. Il
template è un repository privato da cui nascono anche progetti aziendali: ciò che contiene nei
file che propaga deve valere per chiunque li riceva.

Lo strumento legge l'elenco degli identificativi personali da un file locale, mai versionato
perché l'elenco è esso stesso un dato personale, e cerca ciascuno, senza distinguere maiuscole e
minuscole, in tutto ciò che l'allineamento propaga: `.claude/` del template, cioè
`PROJECT-SYSTEM.md`, regole, norme, skill e pacchetti con i loro strumenti. Esce con 1 se ne
trova uno, e anche se l'elenco manca: un controllo senza elenco direbbe sempre pulito, cioè
fallirebbe in silenzio.

L'elenco si cerca, nell'ordine, in `_notes/allineamento/identita-personali.txt` del template e in
`~/.config/identita-personali.txt`: una stringa per riga, le righe che cominciano con # sono
commenti. `chiudi` lo lancia nel template e ferma il commit; `allinea-tutti.ps1` lo lancia prima
di ogni passata e non parte se trova qualcosa.

    python .claude/templates/tools/test-identita-personali.py
    python .claude/templates/tools/test-identita-personali.py --elenco percorso.txt
    python .claude/templates/tools/test-identita-personali.py --autotest
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

PERIMETRO = [".claude"]
FUORI = {"_notes", "__pycache__", ".git", "node_modules"}
ELENCHI = [Path("_notes") / "allineamento" / "identita-personali.txt", Path.home() / ".config" / "identita-personali.txt"]
QUESTO = "test-identita-personali.py"


def leggi_elenco(radice: Path, esplicito: str = "") -> tuple:
    candidati = [Path(esplicito)] if esplicito else [radice / ELENCHI[0], ELENCHI[1]]
    for f in candidati:
        if f.is_file():
            voci = [r.strip() for r in f.read_text(encoding="utf-8").splitlines() if r.strip() and not r.strip().startswith("#")]
            return f, voci
    return None, []


def file_del_perimetro(radice: Path) -> list:
    """I file tracciati da git, perché l'allineamento propaga ciò che è committato e non i file
    locali ignorati, come `settings.local.json`; fuori da un repository, tutti i file."""
    import subprocess
    r = subprocess.run(["git", "-C", str(radice), "ls-files", "-z", *PERIMETRO], capture_output=True)
    if r.returncode == 0:
        return [radice / p for p in r.stdout.decode("utf-8", errors="replace").split("\0") if p]
    return [f for base in PERIMETRO for f in sorted((radice / base).rglob("*"))]


def cerca(radice: Path, voci: list) -> list:
    basse = [v.lower() for v in voci]
    trovate = []
    for f in file_del_perimetro(radice):
        rel = f.relative_to(radice)
        if not f.is_file() or FUORI.intersection(rel.parts) or f.name == QUESTO:
            continue
        try:
            testo = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for n, riga in enumerate(testo.splitlines(), 1):
            bassa = riga.lower()
            for v, vb in zip(voci, basse):
                if vb in bassa:
                    trovate.append((rel.as_posix(), n, v))
    return trovate


def controlla(radice: Path, esplicito: str = "") -> int:
    f, voci = leggi_elenco(radice, esplicito)
    if not voci:
        print("identita personali: manca l'elenco (%s oppure %s): senza elenco il controllo non vede niente"
              % (ELENCHI[0].as_posix(), ELENCHI[1].as_posix()))
        return 1
    trovate = cerca(radice, voci)
    for rel, n, v in trovate:
        # L'identificativo non si stampa per intero: questa uscita finisce in log e trascrizioni.
        print("   %s:%d contiene un identificativo personale (%s...)" % (rel, n, v[:3]))
    if trovate:
        print("identita personali: %d occorrenze nei file che il template propaga; toglierle prima di committare o allineare" % len(trovate))
        return 1
    print("identita personali: nessuna delle %d voci nei file che il template propaga" % len(voci))
    return 0


def autotest() -> int:
    casi = rossi = 0

    def caso(nome, ok):
        nonlocal casi, rossi
        casi += 1
        rossi += 0 if ok else 1
        print(("ok   " if ok else "ROSSO ") + nome)

    import contextlib
    import io
    with tempfile.TemporaryDirectory() as d:
        r = Path(d)
        (r / ".claude" / "rules").mkdir(parents=True)
        (r / "_notes" / "allineamento").mkdir(parents=True)
        (r / ".claude" / "rules" / "identita.md").write_text("Profilo di lavoro: lavoro@azienda.example\n", encoding="utf-8")
        (r / "README.md").write_text("persona.privata@posta.example fuori dal perimetro\n", encoding="utf-8")

        def esegui(*a):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = controlla(r, *a)
            return rc, buf.getvalue()

        rc, out = esegui()
        caso("senza elenco il controllo fallisce invece di dire pulito", rc == 1 and "manca l'elenco" in out)
        (r / "_notes" / "allineamento" / "identita-personali.txt").write_text("# commento\nPersona.Privata@posta.example\nutentepriv\n", encoding="utf-8")
        rc, out = esegui()
        caso("un perimetro pulito passa, e un file fuori perimetro non conta", rc == 0 and "nessuna delle 2 voci" in out)
        (r / ".claude" / "rules" / "identita.md").write_text("Profilo personale: utente UtentePriv, persona.privata@posta.example\n", encoding="utf-8")
        rc, out = esegui()
        caso("un identificativo in una regola ferma, senza distinguere maiuscole", rc == 1 and "identita.md:1" in out and "2 occorrenze" in out)
        caso("l'identificativo non si stampa per intero", "persona.privata" not in out.lower())
        (r / ".claude" / "_notes").mkdir()
        (r / ".claude" / "rules" / "identita.md").write_text("pulito\n", encoding="utf-8")
        (r / ".claude" / "_notes" / "x.md").write_text("utentepriv\n", encoding="utf-8")
        caso("le note locali sotto .claude non contano", esegui()[0] == 0)
        altro = r / "altro.txt"
        altro.write_text("pulito\n", encoding="utf-8")
        (r / ".claude" / "rules" / "identita.md").write_text("utentepriv\n", encoding="utf-8")
        caso("un elenco esplicito sostituisce quello di default", esegui(str(altro))[0] == 0)
    print("\n%d casi superati su %d" % (casi - rossi, casi))
    return 1 if rossi else 0


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    p = argparse.ArgumentParser(description="Nessun identificativo personale nei file che il template propaga.")
    p.add_argument("--radice", default=".")
    p.add_argument("--elenco", default="")
    p.add_argument("--autotest", action="store_true")
    a = p.parse_args(argv)
    if a.autotest:
        return autotest()
    return controlla(Path(a.radice), a.elenco)


if __name__ == "__main__":
    sys.exit(main())
