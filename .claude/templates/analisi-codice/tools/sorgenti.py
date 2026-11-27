#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Scarica in `sorgenti/` il codice che compone il sistema da analizzare, come lo dichiara `analisi-codice.json`.

Perché esiste
-------------
Il sistema da analizzare spesso non è un repository: è l'unione dei repository che un file di
composizione, per esempio un Dockerfile, mette insieme. Una ricerca su "dove è usato X" vale solo
se copre la stessa unione, quindi l'elenco dei sorgenti non si scrive a mano ma si rilegge da quel
file a ogni aggiornamento, e ai repository letti di lì si aggiungono quelli elencati nella
configurazione. Ogni sorgente finisce in `sorgenti/<nome>` e il suo commit esatto in
`sorgenti/manifest.json`, che `dove-usato.py` e `ricerca.py` usano per link permanenti a file e riga.

La configurazione, nel blocco "sorgenti" di `analisi-codice.json` nella radice del progetto:
  composizione       {"repo", "ramo", "percorso"}: il file da cui leggere i `git clone -b <ramo> <url>`
  repository         [{"repo", "ramo", "famiglia"}]: sorgenti in più, o tutti se manca la composizione
  famiglie           proprietario GitHub -> famiglia; chi non c'è è "terzi"
  facoltative        famiglie scaricate solo se chieste con --con, perché grandi
  senza_prefisso     proprietari i cui repository si salvano senza il prefisso del proprietario
  storia_completa    nomi locali clonati con tutta la storia, che serve a git blame; gli altri a profondità 1

GitHub si raggiunge con `gh`, che fa anche da gestore delle credenziali di git: il clone dei
privati funziona in ogni shell. Un repository non accessibile si registra come tale nel manifesto
invece di sparire in silenzio.

    python tools/sorgenti.py                  le famiglie non facoltative
    python tools/sorgenti.py --con oca,core   anche le facoltative nominate
    python tools/sorgenti.py --tutte          tutte
    python tools/sorgenti.py --stato          mostra il manifesto senza scaricare
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

PROGETTO = Path.cwd()
SORGENTI = PROGETTO / "sorgenti"
MANIFESTO = SORGENTI / "manifest.json"
CONFIGURAZIONE = PROGETTO / "analisi-codice.json"
GIT = ["git", "-c", "core.longpaths=true", "-c", "credential.helper=", "-c", "credential.helper=!gh auth git-credential"]


def configurazione():
    if not CONFIGURAZIONE.exists():
        sys.exit(f"sorgenti: manca {CONFIGURAZIONE}; il modello è nel README del pacchetto analisi-codice")
    return json.loads(CONFIGURAZIONE.read_text(encoding="utf-8")).get("sorgenti", {})


def esegui(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


def leggi_composizione(c):
    r = esegui(["gh", "api", f"repos/{c['repo']}/contents/{c['percorso']}?ref={c['ramo']}",
                "-H", "Accept: application/vnd.github.raw"])
    if r.returncode:
        sys.exit(f"sorgenti: {c['percorso']} di {c['repo']}@{c['ramo']} non leggibile: {r.stderr.strip()}")
    return r.stdout


def elenco(testo, famiglie):
    """Le terne (owner/repo, ramo, famiglia) clonate dal file di composizione, nell'ordine in cui compaiono."""
    visti, fuori = set(), []
    for m in re.finditer(r"git clone[^\n;]*?-b\s+(\S+)\s+(?:https://github\.com/|git@github\.com:)([\w.-]+/[\w.-]+?)(?:\.git)?\s", testo):
        ramo, repo = m.group(1), m.group(2)
        if repo in visti:
            continue
        visti.add(repo)
        fuori.append((repo, ramo, famiglie.get(repo.split("/")[0].lower(), "terzi")))
    return fuori


def nome_locale(repo, senza_prefisso):
    owner, nome = repo.split("/")
    return nome if owner.lower() in senza_prefisso else f"{owner.lower()}-{nome}"


def estrai_senza_checkout(dest):
    """Ripiego quando git rifiuta un percorso che Windows non ammette, per esempio un file con i due
    punti nel nome: i file si estraggono da git archive, saltando quelli con nomi non validi e le
    cartelle di prova, che restano fuori dal perimetro di dove-usato."""
    import io
    import tarfile
    dati = subprocess.run(["git", "-c", "core.protectNTFS=false", "-C", str(dest), "archive", "--format=tar", "HEAD"], capture_output=True)
    saltati = 0
    with tarfile.open(fileobj=io.BytesIO(dati.stdout)) as tar:
        for m in tar.getmembers():
            if not m.isfile():
                continue
            if any(c in m.name for c in ':*?"<>|') or "/tests/" in "/" + m.name:
                saltati += 1
                continue
            uscita = dest / m.name
            uscita.parent.mkdir(parents=True, exist_ok=True)
            uscita.write_bytes(tar.extractfile(m).read())
    return subprocess.CompletedProcess([], 0, f"estratti senza checkout, {saltati} file saltati", "")


def scarica(repo, ramo, dest, completa):
    if (dest / ".git").exists():
        r = esegui(GIT + ["-C", str(dest), "fetch", "-q", "origin", ramo])
        if r.returncode == 0:
            r = esegui(GIT + ["-C", str(dest), "checkout", "-q", "-B", ramo, "FETCH_HEAD"])
            if r.returncode:
                esegui(GIT + ["-C", str(dest), "update-ref", f"refs/heads/{ramo}", "FETCH_HEAD"])
                r = estrai_senza_checkout(dest)
    else:
        # Clone senza checkout, poi checkout; se git rifiuta un percorso che Windows non ammette,
        # ripiego su estrai_senza_checkout.
        prof = [] if completa else ["--depth", "1"]
        r = esegui(GIT + ["clone", "-q", "--no-checkout", "-b", ramo, *prof, f"https://github.com/{repo}.git", str(dest)])
        if r.returncode == 0:
            r = esegui(GIT + ["-C", str(dest), "checkout", "-q", ramo])
            if r.returncode:
                r = estrai_senza_checkout(dest)
    if r.returncode:
        return None, r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "errore sconosciuto"
    sha = esegui(["git", "-C", str(dest), "rev-parse", "HEAD"]).stdout.strip()
    return sha, None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--con", default="", help="famiglie facoltative da scaricare, separate da virgola")
    ap.add_argument("--tutte", action="store_true", help="anche tutte le famiglie facoltative")
    ap.add_argument("--stato", action="store_true", help="mostra il manifesto e basta")
    a = ap.parse_args()

    if a.stato:
        print(MANIFESTO.read_text(encoding="utf-8") if MANIFESTO.exists() else "nessun manifesto")
        return

    conf = configurazione()
    famiglie = {k.lower(): v for k, v in conf.get("famiglie", {}).items()}
    senza_prefisso = {p.lower() for p in conf.get("senza_prefisso", [])}
    facoltative = set(conf.get("facoltative", []))
    chieste = facoltative if a.tutte else {f for f in a.con.split(",") if f}
    completa = set(conf.get("storia_completa", []))

    SORGENTI.mkdir(exist_ok=True)
    comp = conf.get("composizione")
    voci = elenco(leggi_composizione(comp), famiglie) if comp else []
    voci += [(r["repo"], r["ramo"], r.get("famiglia", "terzi")) for r in conf.get("repository", [])]
    if not voci:
        sys.exit("sorgenti: nessun sorgente; analisi-codice.json non dichiara né composizione né repository")
    vecchio = json.loads(MANIFESTO.read_text(encoding="utf-8")) if MANIFESTO.exists() else {}
    manifesto = {"generato": datetime.now().isoformat(timespec="seconds"),
                 "ambiente": f"{comp['repo']}@{comp['ramo']}" if comp else "elenco della configurazione",
                 "sorgenti": vecchio.get("sorgenti", {})}

    for repo, ramo, famiglia in voci:
        if famiglia in facoltative and famiglia not in chieste:
            continue
        nome = nome_locale(repo, senza_prefisso)
        sha, errore = scarica(repo, ramo, SORGENTI / nome, nome in completa)
        manifesto["sorgenti"][nome] = {"repo": repo, "ramo": ramo, "famiglia": famiglia,
                                       "commit": sha, "accessibile": sha is not None,
                                       **({"errore": errore} if errore else {})}
        print(f"{'ok ' if sha else 'NO '} {famiglia:17} {repo}@{ramo} {sha[:8] if sha else errore}")

    MANIFESTO.write_text(json.dumps(manifesto, indent=2, ensure_ascii=False), encoding="utf-8")
    ok = sum(1 for v in manifesto["sorgenti"].values() if v["accessibile"])
    print(f"sorgenti: {ok} accessibili su {len(manifesto['sorgenti'])} nel manifesto {MANIFESTO}")


if __name__ == "__main__":
    main()
