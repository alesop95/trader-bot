#!/usr/bin/env python3
"""Parti condivise fra craft-apps.py e craft-mcp.py.

Sta in un modulo a se' perche' i due strumenti devono concordare su che cosa sia
installato e dove: se ciascuno cercasse i binari a modo proprio, lo stato
riportato dal primo e la configurazione generata dal secondo potrebbero parlare
di due installazioni diverse senza che nulla lo segnali.
"""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
from pathlib import Path

ORG = "storytold"

# nome dell'app -> (repo, prefisso dei file di rilascio, cartella di installazione).
# Il launcher sta in tabella perche' si aggiorna come le altre, ma non ha CLI e
# non si collega mai a un agente.
APPS = {
    "photocraft":  ("photocraft",     "photocraft",        "PhotoCraft"),
    "vectorcraft": ("vectorcraft",    "vectorcraft",       "VectorCraft"),
    "filmcraft":   ("filmcraft",      "filmcraft",         "FilmCraft"),
    "lightcraft":  ("lightcraft",     "lightcraft",        "LightCraft"),
    "pdfcraft":    ("pdfcraft",       "pdfcraft",          "PdfCraft"),
    "effectcraft": ("effectcraft",    "effectcraft",       "EffectCraft"),
    "designcraft": ("designcraft",    "designcraft",       "DesignCraft"),
    # FigCraft, interfacce e prototipi, mancava fino al 2026-10-19: il launcher di
    # quella data ne installava tredici e questa tabella ne conosceva dodici.
    "figcraft":    ("figcraft",       "figcraft",          "FigCraft"),
    "wordcraft":   ("wordcraft",      "wordcraft",         "WordCraft"),
    "soundcraft":  ("soundcraft",     "soundcraft",        "SoundCraft"),
    "deckcraft":   ("deckcraft",      "deckcraft",         "DeckCraft"),
    "cadcraft":    ("cadcraft",       "cadcraft",          "CADCraft"),
    "gridcraft":   ("gridcraft",      "gridcraft",         "GridCraft"),
    "launcher":    ("craft-launcher", "artcraft-launcher", "ArtCraft Launcher"),
}

SENZA_CLI = {"launcher"}


def sistema() -> str:
    s = platform.system().lower()
    if s.startswith("win"):
        return "windows"
    if s == "linux":
        return "linux"
    if s == "darwin":
        return "macos"
    return s


def architettura(sist: str) -> str:
    m = platform.machine().lower()
    if sist == "windows":
        if m in ("amd64", "x86_64"):
            return "x64"
        if m in ("arm64", "aarch64"):
            return "arm64"
        return "x86"
    if m in ("x86_64", "amd64"):
        return "x86_64"
    if m in ("aarch64", "arm64"):
        return "aarch64"
    if m.startswith("riscv"):
        return "riscv64"
    return m


def canale_predefinito(sist: str) -> str:
    """Il canale che non chiede privilegi e che porta con se' il binario CLI.

    Su Linux il predefinito e' il tarball e non l'AppImage, benche' l'AppImage sia
    la forma piu' comoda per un essere umano: un AppImage e' un archivio che si
    monta all'avvio, e il binario `<app>-cli` resta dentro, quindi un agente non
    lo trova e il collegamento MCP non si puo' generare. Il tarball contiene
    `bin/<app>` e `bin/<app>-cli` affiancati, non chiede root e si scompatta dove
    si vuole. Verificato il 2026-10-12 sul tarball di GridCraft 0.5.0.
    """
    return {"windows": "portable", "linux": "tar", "macos": "dmg"}.get(sist, "portable")


def nome_asset(prefisso: str, versione: str, sist: str, arch: str, canale: str) -> str:
    """Il nome del file di rilascio per questa combinazione, senza inventarlo.

    Lo schema e' quello pubblicato da tutte e tredici le repo:
    <prefisso>-<versione>-<sistema>-<arch>[-portable].<estensione>.
    """
    base = prefisso + "-" + versione
    if sist == "windows":
        if canale == "portable":
            return base + "-windows-" + arch + "-portable.zip"
        if canale == "msi":
            return base + "-windows-" + arch + ".msi"
    elif sist == "linux":
        if canale == "appimage":
            return base + "-linux-" + arch + ".AppImage"
        if canale in ("deb", "rpm", "flatpak"):
            return base + "-linux-" + arch + "." + canale
        if canale == "tar":
            return base + "-linux-" + arch + ".tar.gz"
    elif sist == "macos" and canale == "dmg":
        return base + "-macos-universal.dmg"
    raise ValueError("canale '" + canale + "' non previsto per " + sist)


def analizza_somme(testo: str) -> dict:
    """Il contenuto di un SHA256SUMS.txt come mappa nome -> digest.

    Accetta sia la forma con due spazi sia quella con l'asterisco del modo
    binario, e scarta in silenzio tutto cio' che non sia un digest di 64 cifre
    esadecimali, perche' una riga storta non deve far passare un file non
    verificato per verificato.
    """
    mappa = {}
    for riga in testo.splitlines():
        riga = riga.strip()
        if not riga or riga.startswith("#"):
            continue
        parti = riga.split(None, 1)
        if len(parti) != 2:
            continue
        digest, nome = parti[0].lower(), parti[1].lstrip("*").strip()
        if re.fullmatch(r"[0-9a-f]{64}", digest):
            mappa[nome] = digest
    return mappa


def cartella_portatile() -> Path:
    env = os.environ.get("CRAFT_APPS_HOME")
    if env:
        return Path(env)
    if sistema() == "windows":
        return Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "CraftApps"
    return Path.home() / ".local" / "share" / "craft-apps"


def radici_installazione(sist: str) -> list:
    if sist == "windows":
        return [Path(os.environ.get("ProgramFiles", r"C:\Program Files")),
                Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")),
                cartella_portatile()]
    return [cartella_portatile(), Path.home() / "Applications",
            Path("/usr/bin"), Path("/usr/local/bin"), Path("/opt")]


def trova_cli(app: str, sist: str):
    """Il binario CLI dell'app, cercato per nome e non per cartella attesa.

    Cercarlo per nome fa trovare allo stesso modo un'installazione di sistema,
    una copia portabile e una cartella rinominata a mano, e fa fallire la ricerca
    invece di restituire un percorso plausibile che non esiste.
    """
    if app in SENZA_CLI:
        return None
    nome = app + "-cli" + (".exe" if sist == "windows" else "")
    su_path = shutil.which(nome)
    if su_path:
        return Path(su_path)
    # `bin/` serve per il tarball di Linux, che tiene i due binari in una
    # sottocartella; l'installatore di sistema e lo zip portabile li tengono
    # invece accanto alla radice dell'applicazione.
    for radice in radici_installazione(sist):
        if not radice.is_dir():
            continue
        for cand in (radice / APPS[app][2] / nome,
                     radice / APPS[app][2] / "bin" / nome,
                     radice / nome,
                     radice / "bin" / nome):
            if cand.is_file():
                return cand
        try:
            for voce in radice.iterdir():
                if not voce.is_dir():
                    continue
                for cand in (voce / nome, voce / "bin" / nome):
                    if cand.is_file():
                        return cand
        except (PermissionError, OSError):
            continue
    return None


def versione_installata(app: str, sist: str):
    cli = trova_cli(app, sist)
    if not cli:
        return None, None
    try:
        out = subprocess.run([str(cli), "--version"], capture_output=True, text=True,
                             timeout=60, encoding="utf-8", errors="replace")
    except (OSError, subprocess.TimeoutExpired):
        return "?", cli
    testo = (out.stdout or "") + (out.stderr or "")
    m = re.search(r"(\d+\.\d+\.\d+)", testo)
    return (m.group(1) if m else "?"), cli
