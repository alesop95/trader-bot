#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Confronta la visibilita' dichiarata dal progetto con quella che il servizio riporta.

Perche' esiste. La regola di anonimizzazione si attiva quando il repository e' leggibile
oltre la cerchia che lo scrive, ma la visibilita' e' un attributo che cambia con un clic e
che nessuno ricontrolla: un repository nato privato puo' diventare pubblico per errore o
per decisione presa altrove, e in quel momento tutto cio' che e' stato scritto confidando
sulla privatezza diventa pubblico insieme alla sua storia, senza che niente lo dica. La
dichiarazione nel CLAUDE.md, chiesta dalla lezione L-001 di un progetto istanziato del
2026-10-28, rende azionabile la regola ma invecchia da sola: questo controllo la rilegge
e la confronta con il servizio a ogni chiusura.

Tre esiti e non due, come prescrive il riferimento della skill `prove-che-misurano`.
Conforme: dichiarato e osservato coincidono. Non conforme: differiscono, e il controllo
fallisce, perche' significa che il progetto sta lavorando con un presupposto sbagliato.
Non verificabile: manca `gh`, manca l'autenticazione, oppure il remoto non e' su un
servizio che sappiamo interrogare; non fallisce, ma lo dichiara invece di tacere, perche'
un ripiego letto come conformita' e' il modo di fallire che questo controllo esiste per
evitare.

La dichiarazione sta nel CLAUDE.md del progetto, dove l'agente la legge a ogni sessione,
in un commento che il rendering non mostra:

    <!-- visibilita: private, verificata il 2026-10-28 -->

I valori ammessi sono quelli del servizio, cioe' public, private e internal. Senza la
riga il controllo avvisa e non blocca, perche' un progetto che non l'ha ancora scritta
non e' in pericolo per questo: diventa un errore solo quando la riga c'e' e mente.

Uso:
    python tools/check-visibilita.py              controlla il progetto corrente
    python tools/check-visibilita.py --giorni 90  avvisa se la verifica e' piu' vecchia
    python tools/check-visibilita.py --autotest   esegue le prove interne
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

DICHIARAZIONE = re.compile(
    r"<!--\s*visibilit[aà]\s*:\s*(public|private|internal)\s*,\s*"
    r"verificata il (\d{4}-\d{2}-\d{2})\s*-->",
    re.I,
)
AMMESSI = {"public", "private", "internal"}


def dichiarata(radice: Path) -> tuple[str, str] | None:
    """Legge la riga di dichiarazione dal CLAUDE.md del progetto, se c'e'."""
    for nome in ("CLAUDE.md", ".claude/CLAUDE.md"):
        f = radice / nome
        if not f.is_file():
            continue
        m = DICHIARAZIONE.search(f.read_text(encoding="utf-8", errors="replace"))
        if m:
            return m.group(1).lower(), m.group(2)
    return None


def slug_da_remoto(radice: Path) -> str | None:
    """owner/repo dal remoto origin, nelle forme SSH con alias, SSH canonica e HTTPS."""
    r = subprocess.run(["git", "-C", str(radice), "config", "--get", "remote.origin.url"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    url = r.stdout.strip()
    if not url:
        return None
    m = re.search(r"[:/]([^/:]+)/([^/]+?)(?:\.git)?$", url)
    if not m:
        return None
    return f"{m.group(1)}/{m.group(2)}"


def osservata(slug: str) -> tuple[str | None, str]:
    """Chiede al servizio. Torna (visibilita, motivo) e la visibilita' e' None se non si sa."""
    try:
        r = subprocess.run(["gh", "api", f"repos/{slug}", "--jq", ".visibility"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return None, "gh non e' installato"
    v = r.stdout.strip().lower()
    if r.returncode != 0 or v not in AMMESSI:
        detto = (r.stderr or r.stdout).strip().splitlines()
        return None, "gh non ha risposto con una visibilita' (%s)" % (detto[-1][:90] if detto else "nessun messaggio")
    return v, ""


def controlla(radice: Path, giorni: int) -> int:
    d = dichiarata(radice)
    slug = slug_da_remoto(radice)
    if slug is None:
        print("check-visibilita: nessun remoto origin, niente da confrontare")
        return 0
    if d is None:
        print("check-visibilita: AVVISO, il CLAUDE.md non dichiara la visibilita' del repository.")
        print("  Si scrive una riga come questa, dove l'agente la legge a ogni sessione:")
        print("    <!-- visibilita: private, verificata il %s -->" % dt.date.today().isoformat())
        print("  Senza di essa la regola di anonimizzazione resta una prescrizione senza presupposto.")
        return 0

    detta, quando = d
    vista, motivo = osservata(slug)
    if vista is None:
        print("check-visibilita: NON VERIFICABILE per %s: %s" % (slug, motivo))
        print("  Dichiarata %s il %s, non confermata. Non e' un verde: e' un controllo che non ha guardato."
              % (detta, quando))
        return 0

    if vista != detta:
        print("check-visibilita: NON CONFORME. %s e' %s, il CLAUDE.md dichiara %s dal %s."
              % (slug, vista.upper(), detta, quando))
        if vista == "public":
            print("  Il repository e' leggibile da chiunque, insieme a tutta la sua storia:")
            print("  la regola di anonimizzazione si applica, e cio' che e' gia' dentro va guardato.")
        print("  Si corregge la riga nel CLAUDE.md, con la data di oggi, dopo aver deciso che fare.")
        return 1

    eta = (dt.date.today() - dt.date.fromisoformat(quando)).days
    print("check-visibilita: %s e' %s, come dichiarato il %s (%d giorni fa)." % (slug, vista, quando, eta))
    if eta > giorni:
        print("  AVVISO: la verifica ha piu' di %d giorni. Si aggiorna la data nel CLAUDE.md." % giorni)
    return 0


def autotest() -> int:
    casi = rossi = 0

    def caso(nome: str, ok: bool) -> None:
        nonlocal casi, rossi
        casi += 1
        if not ok:
            rossi += 1
        print("%s %s" % ("ok  " if ok else "ROSSO", nome))

    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        (p / "CLAUDE.md").write_text("# prova\n\n<!-- visibilita: private, verificata il 2026-10-28 -->\n",
                                     encoding="utf-8")
        caso("la dichiarazione si legge dal CLAUDE.md", dichiarata(p) == ("private", "2026-10-28"))

        (p / "CLAUDE.md").write_text("# prova\n\n<!-- visibilità : PUBLIC , verificata il 2026-01-02 -->\n",
                                     encoding="utf-8")
        caso("accetta l'accento, gli spazi e le maiuscole", dichiarata(p) == ("public", "2026-01-02"))

        (p / "CLAUDE.md").write_text("# prova\n\nNessuna dichiarazione qui.\n", encoding="utf-8")
        caso("senza la riga torna None e non indovina", dichiarata(p) is None)

        (p / "CLAUDE.md").write_text("# prova\n\n<!-- visibilita: segreto, verificata il 2026-10-28 -->\n",
                                     encoding="utf-8")
        caso("un valore fuori dai tre ammessi non si accetta", dichiarata(p) is None)

        (p / "CLAUDE.md").write_text("# prova\n\n<!-- visibilita: private, verificata il ieri -->\n",
                                     encoding="utf-8")
        caso("una data non in forma ISO non si accetta", dichiarata(p) is None)

    # Gli indirizzi di prova sono inventati e nessuno di essi e' di una persona vera: questo
    # file e' tracciato e il template lo propaga in ogni progetto, quindi un identificativo
    # reale scritto qui si moltiplica per il numero dei repository che ne discendono. E' la
    # stessa ragione per cui l'autotest dell'anonimizzazione non porta mai un valore reale,
    # e il 2026-10-28 la guardia test-identita-personali ha fermato la passata proprio qui.
    for url, atteso in [
        ("git@alias-di-macchina:organizzazione-finta/progetto.git", "organizzazione-finta/progetto"),
        ("git@servizio.example:utente-finto/altro-progetto.git", "utente-finto/altro-progetto"),
        ("https://github.com/pola-rs/polars", "pola-rs/polars"),
    ]:
        m = re.search(r"[:/]([^/:]+)/([^/]+?)(?:\.git)?$", url)
        caso("dal remoto %s si ricava owner/repo" % url.split(":")[0],
             m is not None and f"{m.group(1)}/{m.group(2)}" == atteso)

    v, motivo = osservata("questo-owner-non-esiste-xyz/questo-repo-non-esiste-xyz")
    caso("un repository irraggiungibile e' NON VERIFICABILE e non conforme", v is None and bool(motivo))

    print("\n%d casi superati su %d" % (casi - rossi, casi))
    return 1 if rossi else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("radice", nargs="?", default=".", type=Path)
    ap.add_argument("--giorni", type=int, default=180,
                    help="oltre questa eta' della verifica si avvisa (default: 180)")
    ap.add_argument("--autotest", action="store_true")
    a = ap.parse_args()
    if a.autotest:
        return autotest()
    return controlla(a.radice.resolve(), a.giorni)


if __name__ == "__main__":
    sys.exit(main())
