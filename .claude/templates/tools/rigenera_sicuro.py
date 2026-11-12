#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scrittura dei file generati senza perdere il testo che il generatore non produce.

Perché esiste
--------------
Un file generato, o un blocco generato fra due marcatori dentro un file scritto a mano,
accumula col tempo testo scritto a mano: una voce aggiunta direttamente nel file generato,
una sezione messa in coda al file quando la coda era dentro il blocco. Il controllo di
allineamento del generatore vede soltanto la differenza e dice «disallineato: rigenerare»,
cioè chiede proprio il gesto che toglie quel testo, senza alcun errore. In un progetto
istanziato, il 2026-11-11, una rigenerazione così ha tolto 340 righe di sezioni autorate da un
registro versionato, recuperate solo dal diff, e un file generato non versionato portava una
voce scritta a mano che nessuna rete avrebbe salvato (lezione L-010 di quel progetto).

Che cosa garantisce
--------------------
Due cose, in quest'ordine. Prima di sovrascrivere, la versione attuale del file si copia
byte per byte in `_notes/archivio/rigenerazioni/`, con data e ora nel nome: qualunque cosa
la rigenerazione tolga, resta recuperabile anche se il file non è tracciato e anche se la
perdita non si vede subito. Poi, se fra le righe che sparirebbero ce n'è una che il
chiamante dichiara strutturale, cioè un titolo di sezione o una voce bibliografica, la
scrittura si ferma ed elenca quelle righe: il testo autorato va portato nella sorgente del
generatore o fuori dai marcatori, e solo `--forza` procede lo stesso.

Uso, da un generatore
----------------------
Il modulo si copia accanto al generatore, o si importa da .claude/templates/tools/.

    import rigenera_sicuro
    esito = rigenera_sicuro.scrivi(percorso, nuovo, schema=r"^#{1,6} ", forza=args.forza)

    python tools/rigenera_sicuro.py --autotest
"""

import datetime
import os
import re
import sys
from collections import Counter

def _trova_radice():
    """La radice del repository che contiene il modulo, cercata risalendo fino a .git.

    Il modulo vive in tools/ di un progetto oppure in .claude/templates/tools/, quindi la
    radice non è a una distanza fissa; senza .git si ricade sulla cartella sopra tools/.
    """
    qui = os.path.dirname(os.path.abspath(__file__))
    d = qui
    while True:
        if os.path.exists(os.path.join(d, ".git")):
            return d
        su = os.path.dirname(d)
        if su == d:
            return os.path.dirname(qui)
        d = su


RADICE = _trova_radice()
ARCHIVIO = os.path.join(RADICE, "_notes", "archivio", "rigenerazioni")


def _rel(percorso):
    """Il percorso relativo alla radice quando si può, altrimenti quello dato."""
    try:
        return os.path.relpath(percorso, RADICE)
    except ValueError:
        return percorso


def righe_tolte(vecchio, nuovo):
    """Le righe del vecchio testo che il nuovo non contiene, contate come multinsieme."""
    restano = Counter(nuovo.splitlines())
    tolte = []
    for riga in vecchio.splitlines():
        if restano[riga] > 0:
            restano[riga] -= 1
        else:
            tolte.append(riga)
    return tolte


def perdite_strutturali(vecchio, nuovo, schema):
    """Le righe strutturali del vecchio testo che nel nuovo non compaiono più."""
    if not schema:
        return []
    regola = re.compile(schema)
    return [r for r in righe_tolte(vecchio, nuovo) if regola.search(r)]


def avviso(percorso, vecchio, nuovo, schema):
    """Il testo da stampare in modalità di controllo quando il file è disallineato."""
    perse = perdite_strutturali(vecchio, nuovo, schema)
    tolte = righe_tolte(vecchio, nuovo)
    righe = ["  la rigenerazione toglierebbe %d righe e ne aggiungerebbe %d"
             % (len(tolte), len(righe_tolte(nuovo, vecchio)))]
    if perse:
        righe.append("  ATTENZIONE: fra le righe tolte ce ne sono %d strutturali, che il generatore non produce:" % len(perse))
        righe.extend("    " + r[:160] for r in perse[:20])
        righe.append("  rigenerare si fermerebbe: portare quel testo nella sorgente o fuori dal blocco generato")
    return "\n".join(righe)


def scrivi(percorso, nuovo, schema=None, forza=False, archivio=ARCHIVIO, silenzioso=False):
    """Scrive `nuovo` in `percorso` con terminatori LF; ritorna 0 se ha scritto o se non serviva, 1 se si è fermato."""
    vecchio_b = None
    if os.path.exists(percorso):
        with open(percorso, "rb") as f:
            vecchio_b = f.read()
    nuovo_b = nuovo.encode("utf-8")
    if vecchio_b == nuovo_b:
        return 0
    if vecchio_b is not None:
        vecchio = vecchio_b.decode("utf-8").replace("\r\n", "\n")
        perse = perdite_strutturali(vecchio, nuovo, schema)
        if perse and not forza:
            if silenzioso:
                return 1
            print("FERMO: la rigenerazione di %s toglierebbe %d righe strutturali che il generatore non produce:"
                  % (_rel(percorso), len(perse)))
            for r in perse[:20]:
                print("    " + r[:160])
            print("  Portare quel testo nella sorgente del generatore o fuori dal blocco generato; "
                  "--forza procede comunque, e la versione attuale resta archiviata. Nessun file scritto.")
            return 1
        os.makedirs(archivio, exist_ok=True)
        ora = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        copia = os.path.join(archivio, "%s-%s" % (ora, os.path.basename(percorso)))
        with open(copia, "wb") as f:
            f.write(vecchio_b)
        with open(copia, "rb") as f:
            if f.read() != vecchio_b:
                print("FERMO: la copia d'archivio di %s non si rilegge uguale. Nessun file scritto." % percorso)
                return 1
        if not silenzioso:
            print("  %s: %d righe tolte, %d aggiunte; versione precedente in %s"
                  % (_rel(percorso), len(righe_tolte(vecchio, nuovo)),
                     len(righe_tolte(nuovo, vecchio)), _rel(copia)))
    os.makedirs(os.path.dirname(percorso) or ".", exist_ok=True)
    with open(percorso, "wb") as f:
        f.write(nuovo_b)
    return 0


def autotest():
    import tempfile
    falliti = 0

    def prova(nome, cond):
        nonlocal falliti
        if not cond:
            falliti += 1
            print("  FALLITO: " + nome)

    with tempfile.TemporaryDirectory() as d:
        arch = os.path.join(d, "arch")
        p = os.path.join(d, "f.md")
        prova("un file nuovo si scrive", scrivi(p, "a\n", archivio=arch, silenzioso=True) == 0
              and open(p, encoding="utf-8").read() == "a\n")
        prova("un file uguale non si archivia", scrivi(p, "a\n", archivio=arch, silenzioso=True) == 0
              and not os.path.exists(arch))
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write("<!-- inizio -->\n## Sezione autorata\ntesto\n## Indice\nvecchio\n")
        esito = scrivi(p, "<!-- inizio -->\n## Indice\nnuovo\n", schema=r"^#{1,6} ", archivio=arch, silenzioso=True)
        prova("un titolo che sparirebbe ferma la scrittura", esito == 1)
        prova("e il file resta com'era", "Sezione autorata" in open(p, encoding="utf-8").read())
        esito = scrivi(p, "<!-- inizio -->\n## Indice\nnuovo\n", schema=r"^#{1,6} ", forza=True, archivio=arch,
                       silenzioso=True)
        prova("con forza scrive", esito == 0 and "nuovo" in open(p, encoding="utf-8").read())
        copie = os.listdir(arch) if os.path.isdir(arch) else []
        prova("e la versione precedente è archiviata intera", len(copie) == 1 and
              "Sezione autorata" in open(os.path.join(arch, copie[0]), encoding="utf-8").read())
        prova("una riga cambiata senza titoli scrive e archivia",
              scrivi(p, "<!-- inizio -->\n## Indice\naltro\n", schema=r"^#{1,6} ", archivio=arch, silenzioso=True) == 0
              and len(os.listdir(arch)) == 2)
        prova("una voce bibliografica tolta ferma la scrittura",
              perdite_strutturali("\\bibitem{a}\nx\n\\bibitem{b}\n", "\\bibitem{a}\nx\n", r"^\\bibitem\{")
              == ["\\bibitem{b}"])
        prova("le righe tolte si contano come multinsieme", righe_tolte("x\nx\ny\n", "x\ny\n") == ["x"])
    print("autotest di rigenera_sicuro: %s" % ("verde" if not falliti else "%d falliti" % falliti))
    return 1 if falliti else 0


if __name__ == "__main__":
    if "--autotest" in sys.argv:
        sys.exit(autotest())
    print(__doc__)
