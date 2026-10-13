#!/usr/bin/env python3
"""Inventario, scaricamento verificato e aggiornamento delle applicazioni Craft.

Parla direttamente con l'API dei rilasci di GitHub e verifica ogni file scaricato
contro il SHA256SUMS.txt del rilascio stesso. Non usa il launcher ufficiale, che
per sapere quali versioni esistano interroga api.storyteller.ai, cioe' il backend
del fornitore: qui l'unico host contattato e' GitHub.

    python craft-apps.py stato
    python craft-apps.py installa effectcraft pdfcraft
    python craft-apps.py aggiorna --tutte --solo-scarica

Il canale predefinito non chiede privilegi di amministratore: su Windows lo zip
portabile, su Linux l'AppImage. Gli installatori di sistema (MSI, deb, rpm) si
chiedono con --canale, e il comando elevato viene stampato invece che eseguito.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import ssl
import sys
import tarfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from craft_apps_comune import (  # noqa: E402
    APPS, ORG, analizza_somme, architettura, canale_predefinito,
    cartella_portatile, nome_asset, sistema, versione_installata,
)

API = "https://api.github.com/repos/{org}/{repo}/releases/latest"


# --------------------------------------------------------------------------- #
# rilasci
# --------------------------------------------------------------------------- #

def _apri(url: str, binario: bool = False):
    req = urllib.request.Request(url, headers={
        "User-Agent": "craft-apps/1 (template-claude-developing)",
        "Accept": "application/octet-stream" if binario else "application/vnd.github+json",
    })
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    return urllib.request.urlopen(req, timeout=120, context=ssl.create_default_context())


_cache_rilasci = {}


def rilascio(repo: str) -> dict:
    if repo in _cache_rilasci:
        return _cache_rilasci[repo]
    try:
        with _apri(API.format(org=ORG, repo=repo)) as r:
            dati = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 403:
            raise SystemExit(
                "GitHub ha risposto 403: quota delle richieste anonime esaurita (60 all'ora). "
                "Imposta GITHUB_TOKEN oppure riprova piu' tardi."
            )
        raise SystemExit("GitHub ha risposto " + str(e.code) + " per " + repo + ": " + str(e.reason))
    _cache_rilasci[repo] = dati
    return dati


def somme(rel: dict) -> dict:
    url = None
    for a in rel.get("assets", []):
        if a["name"] == "SHA256SUMS.txt":
            url = a["browser_download_url"]
            break
    if not url:
        raise SystemExit("il rilascio " + str(rel.get("tag_name")) +
                         " non pubblica SHA256SUMS.txt: non si installa alla cieca")
    with _apri(url, binario=True) as r:
        return analizza_somme(r.read().decode("utf-8", "replace"))


def scarica(url: str, destinazione: Path, atteso: str) -> Path:
    """Scarica calcolando l'impronta mentre scrive, e cancella cio' che non torna."""
    destinazione.parent.mkdir(parents=True, exist_ok=True)
    parziale = destinazione.with_name(destinazione.name + ".parziale")
    h = hashlib.sha256()
    with _apri(url, binario=True) as r, open(parziale, "wb") as f:
        while True:
            blocco = r.read(1 << 20)
            if not blocco:
                break
            h.update(blocco)
            f.write(blocco)
    ottenuto = h.hexdigest()
    if ottenuto != atteso:
        parziale.unlink(missing_ok=True)
        raise SystemExit(
            "impronta SHA-256 diversa da quella pubblicata per " + destinazione.name +
            ": attesa " + atteso + ", ottenuta " + ottenuto + ". Il file e' stato cancellato."
        )
    parziale.replace(destinazione)
    return destinazione


# --------------------------------------------------------------------------- #
# comandi
# --------------------------------------------------------------------------- #

def elenco_app(args, tutte_se_vuoto: bool = True) -> list:
    if args.app:
        return list(args.app)
    if tutte_se_vuoto or getattr(args, "tutte", False):
        return [a for a in APPS if a != "launcher"]
    return []


def peso_asset(rel: dict, prefisso: str, versione: str, sist: str, arch: str,
               canale: str) -> str:
    """Quanto pesa, per questa macchina, il file che servirebbe scaricare.

    Si chiede al rilascio invece di stimarlo, perche' la domanda che segue a
    «non installata» e' sempre «quanto costa averla», e una risposta a memoria
    invecchia a ogni versione.
    """
    try:
        atteso = nome_asset(prefisso, versione, sist, arch, canale)
    except ValueError:
        return "-"
    for a in rel.get("assets", []):
        if a["name"] == atteso:
            return "%.0f MB" % (a["size"] / 1048576.0)
    return "-"


def cmd_stato(args) -> int:
    sist = sistema()
    arch = args.arch or architettura(sist)
    canale = args.canale or canale_predefinito(sist)
    print("sistema " + sist + " " + arch + ", canale " + canale)
    print("%-12s %-12s %-12s %-8s %s" % ("app", "installata", "ultima", "peso", "esito"))
    da_aggiornare, mancanti = [], []
    for app in elenco_app(args):
        loc, dove = versione_installata(app, sist)
        try:
            rel = rilascio(APPS[app][0])
        except SystemExit as e:
            print("%-12s %-12s %-12s %-8s %s" % (app, loc or "-", "?", "-", e))
            continue
        tag = rel.get("tag_name", "?").lstrip("v")
        peso = peso_asset(rel, APPS[app][1], tag, sist, arch, canale)
        if loc is None:
            esito = "non installata"
            mancanti.append(app)
        elif loc == tag:
            esito = "aggiornata"
        else:
            esito = "DA AGGIORNARE"
            da_aggiornare.append(app)
        coda = ("   " + str(dove)) if (dove and args.percorsi) else ""
        print("%-12s %-12s %-12s %-8s %s%s" % (app, loc or "-", tag, peso, esito, coda))
    if da_aggiornare:
        print("\nda aggiornare: " + " ".join(da_aggiornare))
    if mancanti:
        print("\nnon installate: " + " ".join(mancanti))
        print("per prenderne una sola, che e' quasi sempre cio' che serve:")
        print("  python tools/craft-apps.py installa " + mancanti[0])
    return 0


def _posa(app: str, sist: str, canale: str, file: Path, nome_cartella: str) -> int:
    if canale == "portable":
        destinazione = cartella_portatile() / nome_cartella
        if destinazione.exists():
            shutil.rmtree(destinazione)
        destinazione.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(file) as z:
            z.extractall(destinazione)
        voci = list(destinazione.iterdir())
        if len(voci) == 1 and voci[0].is_dir():
            interna = voci[0]
            for v in list(interna.iterdir()):
                shutil.move(str(v), str(destinazione / v.name))
            interna.rmdir()
        print(app + ": posata in " + str(destinazione))
        return 0
    if canale == "appimage":
        destinazione = cartella_portatile() / (app + ".AppImage")
        destinazione.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file, destinazione)
        destinazione.chmod(0o755)
        print(app + ": posata in " + str(destinazione))
        print(app + ": il CLI sta dentro l'AppImage; per averlo separato estrailo con "
              + str(destinazione) + " --appimage-extract")
        return 0
    if canale == "tar":
        destinazione = cartella_portatile() / nome_cartella
        if destinazione.exists():
            shutil.rmtree(destinazione)
        destinazione.mkdir(parents=True, exist_ok=True)
        with tarfile.open(file, "r:gz") as a:
            # `filter="data"` rifiuta percorsi assoluti, risalite con .. e voci
            # speciali: un archivio scaricato resta un archivio scaricato anche
            # quando l'impronta corrisponde a quella pubblicata.
            a.extractall(destinazione, filter="data")
        voci = list(destinazione.iterdir())
        if len(voci) == 1 and voci[0].is_dir():
            interna = voci[0]
            for v in list(interna.iterdir()):
                shutil.move(str(v), str(destinazione / v.name))
            interna.rmdir()
        print(app + ": posata in " + str(destinazione))
        for binario in (destinazione / "bin" / app, destinazione / "bin" / (app + "-cli")):
            if binario.is_file():
                binario.chmod(0o755)
        cli = destinazione / "bin" / (app + "-cli")
        if cli.is_file():
            print(app + ": CLI in " + str(cli))
        return 0
    comandi = {
        "msi": 'msiexec /i "' + str(file) + '" /qn /norestart',
        "deb": 'sudo dpkg -i "' + str(file) + '"',
        "rpm": 'sudo rpm -Uvh "' + str(file) + '"',
        "flatpak": 'flatpak install --user "' + str(file) + '"',
        "dmg": 'hdiutil attach "' + str(file) + '"',
    }
    print(app + ": scaricata e verificata. L'installazione con questo canale la esegui tu:")
    print("  " + comandi.get(canale, "(canale senza comando noto)"))
    return 0


def _installa_una(app: str, sist: str, arch: str, canale: str, cartella: Path,
                  solo_scarica: bool) -> int:
    repo, prefisso, nome_cartella = APPS[app]
    rel = rilascio(repo)
    versione = rel.get("tag_name", "").lstrip("v")
    try:
        atteso = nome_asset(prefisso, versione, sist, arch, canale)
    except ValueError as e:
        print(app + ": " + str(e))
        return 1
    asset = None
    for a in rel.get("assets", []):
        if a["name"] == atteso:
            asset = a
            break
    if not asset:
        print(app + ": nessun file '" + atteso + "' nel rilascio " + versione +
              " (ne pubblica " + str(len(rel.get("assets", []))) + ")")
        return 1
    digest = somme(rel).get(atteso)
    if not digest:
        print(app + ": " + atteso + " non compare in SHA256SUMS.txt, non lo installo")
        return 1
    locale = cartella / atteso
    print(app + ": scarico " + atteso + " (%.1f MB)" % (asset["size"] / 1048576.0))
    scarica(asset["browser_download_url"], locale, digest)
    print(app + ": impronta SHA-256 verificata")
    if solo_scarica:
        print(app + ": " + str(locale))
        return 0
    return _posa(app, sist, canale, locale, nome_cartella)


def cmd_installa(args) -> int:
    sist = sistema()
    arch = args.arch or architettura(sist)
    canale = args.canale or canale_predefinito(sist)
    cartella = Path(args.cartella) if args.cartella else cartella_portatile() / "_scaricati"
    elenco = elenco_app(args, tutte_se_vuoto=False)
    if not elenco:
        print("nessuna app indicata: passa i nomi oppure --tutte")
        return 2
    esito = 0
    for app in elenco:
        try:
            esito |= _installa_una(app, sist, arch, canale, cartella, args.solo_scarica)
        except SystemExit as e:
            print(app + ": " + str(e))
            esito = 1
    return esito


def cmd_aggiorna(args) -> int:
    sist = sistema()
    da_fare = []
    for app in elenco_app(args):
        loc, _ = versione_installata(app, sist)
        if loc is None and not args.tutte:
            continue
        try:
            tag = rilascio(APPS[app][0]).get("tag_name", "").lstrip("v")
        except SystemExit as e:
            print(app + ": " + str(e))
            return 1
        if loc != tag:
            da_fare.append(app)
    if not da_fare:
        print("niente da aggiornare")
        return 0
    print("aggiorno: " + " ".join(da_fare))
    args.app = da_fare
    return cmd_installa(args)


def _opzioni_comuni(p) -> None:
    p.add_argument("app", nargs="*", choices=sorted(APPS), default=None, metavar="APP")
    p.add_argument("--tutte", action="store_true")
    p.add_argument("--canale", choices=["portable", "msi", "appimage", "deb", "rpm",
                                        "flatpak", "tar", "dmg"])
    p.add_argument("--arch")
    p.add_argument("--cartella", help="dove tenere i file scaricati")
    p.add_argument("--solo-scarica", action="store_true", dest="solo_scarica",
                   help="scarica e verifica l'impronta, senza posare niente")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        description="Inventario e aggiornamento verificato delle applicazioni Craft.")
    sub = p.add_subparsers(dest="comando")

    ps = sub.add_parser("stato", help="versione installata contro ultimo rilascio")
    ps.add_argument("app", nargs="*", choices=sorted(APPS), default=None, metavar="APP")
    ps.add_argument("--percorsi", action="store_true", help="mostra dove sta il binario trovato")
    ps.add_argument("--canale", choices=["portable", "msi", "appimage", "deb", "rpm",
                                         "flatpak", "tar", "dmg"],
                    help="il canale su cui calcolare il peso")
    ps.add_argument("--arch")
    ps.set_defaults(func=cmd_stato)

    pi = sub.add_parser("installa", help="scarica, verifica l'impronta e posa")
    _opzioni_comuni(pi)
    pi.set_defaults(func=cmd_installa)

    pa = sub.add_parser("aggiorna", help="aggiorna cio' che e' gia' installato")
    _opzioni_comuni(pa)
    pa.set_defaults(func=cmd_aggiorna)

    args = p.parse_args(argv)
    if not getattr(args, "func", None):
        args = p.parse_args(["stato"])
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
