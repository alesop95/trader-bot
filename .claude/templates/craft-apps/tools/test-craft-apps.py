#!/usr/bin/env python3
"""Prove degli strumenti Craft, piu' una prova dal vivo del confinamento.

Le prove in memoria coprono le quattro decisioni che, sbagliate, non fanno
rumore: come si legge un file di impronte, come si costruisce il nome di un file
di rilascio, quali opzioni appartengono davvero al sottocomando mcp e quando un
percorso sta davvero dentro il progetto. Ciascuna ha una coppia di casi che
differiscono per una proprieta' sola, cosi' che passare non sia gratis.

La prova dal vivo e' la sola che dimostri la cosa che conta per la sicurezza,
cioe' che una radice di scrittura venga davvero imposta dal binario e non solo
dichiarata nell'aiuto. Si salta da se' dove EffectCraft non e' installato.

    python test-craft-apps.py
    python test-craft-apps.py --senza-vivo
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import craft_apps_comune  # noqa: E402
from craft_apps_comune import analizza_somme, nome_asset, sistema, trova_cli  # noqa: E402

import importlib.util  # noqa: E402


def _carica(nome_modulo, nome_file):
    spec = importlib.util.spec_from_file_location(
        nome_modulo, str(Path(__file__).resolve().parent / nome_file))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


craft_mcp = _carica("craft_mcp", "craft-mcp.py")
craft_apps = _carica("craft_apps", "craft-apps.py")

ESITI = []


def prova(nome: str, condizione: bool, dettaglio: str = "") -> None:
    ESITI.append((nome, condizione, dettaglio))


# --------------------------------------------------------------------------- #

SOMME_ESEMPIO = """\
# un commento
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  effectcraft-0.8.0-windows-x64.msi
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 *effectcraft-0.8.0-linux-x86_64.AppImage
abc  troppo-corto.msi
"""


def prove_somme() -> None:
    m = analizza_somme(SOMME_ESEMPIO)
    prova("somme: riga normale letta", "effectcraft-0.8.0-windows-x64.msi" in m)
    prova("somme: forma binaria con asterisco letta senza l'asterisco",
          "effectcraft-0.8.0-linux-x86_64.AppImage" in m)
    prova("somme: digest troppo corto scartato", "troppo-corto.msi" not in m,
          "un digest non valido non deve far passare il file per verificato")
    prova("somme: il commento non diventa una voce", len(m) == 2, str(sorted(m)))


def prove_nome_asset() -> None:
    casi = [
        (("effectcraft", "0.8.0", "windows", "x64", "portable"),
         "effectcraft-0.8.0-windows-x64-portable.zip"),
        (("effectcraft", "0.8.0", "windows", "x64", "msi"),
         "effectcraft-0.8.0-windows-x64.msi"),
        (("effectcraft", "0.8.0", "linux", "x86_64", "appimage"),
         "effectcraft-0.8.0-linux-x86_64.AppImage"),
        (("effectcraft", "0.8.0", "linux", "aarch64", "deb"),
         "effectcraft-0.8.0-linux-aarch64.deb"),
        (("artcraft-launcher", "0.3.2", "macos", "universal", "dmg"),
         "artcraft-launcher-0.3.2-macos-universal.dmg"),
    ]
    for argomenti, atteso in casi:
        ottenuto = nome_asset(*argomenti)
        prova("nome asset " + argomenti[2] + "/" + argomenti[4], ottenuto == atteso,
              "atteso " + atteso + ", ottenuto " + ottenuto)
    try:
        nome_asset("effectcraft", "0.8.0", "windows", "x64", "appimage")
        prova("nome asset: combinazione impossibile rifiutata", False,
              "un AppImage su Windows non deve produrre un nome plausibile")
    except ValueError:
        prova("nome asset: combinazione impossibile rifiutata", True)


AIUTO_PHOTOCRAFT = """\
photocraft-cli: headless Photocraft

USAGE:
  photocraft-cli info <file> [--compact]
      Print the document as JSON.
  photocraft-cli mcp [--bridge <127.0.0.1:port>] [--control-token <64-hex>]
      [--automation-read-root <dir>] [--automation-write-root <dir>]
      Run the MCP server on stdio.
  photocraft-cli serve [--port <port>]
      Keep one headless session open.
"""

AIUTO_PDFCRAFT = """\
pdfcraft-cli info   <file.pdf>                      document summary as JSON
pdfcraft-cli mcp    [--root DIR] [--compact]        MCP server on stdin/stdout (opt-in)
                                                      --compact lists a core set of tools
pdfcraft-cli ui     --control FILE <method>         drive a running app
"""


def prove_sezione_mcp() -> None:
    sezione = craft_mcp.sezione_mcp(AIUTO_PHOTOCRAFT)
    prova("sezione mcp: prende le radici di confinamento",
          "--automation-write-root" in sezione)
    prova("sezione mcp: non prende il --compact di un altro sottocomando",
          "--compact" not in sezione,
          "e' il caso che distingue: --compact esiste nell'aiuto ma appartiene a info")
    prova("sezione mcp: si ferma al sottocomando successivo", "--port" not in sezione,
          "--port appartiene a serve, che viene subito dopo mcp nell'aiuto")

    sezione = craft_mcp.sezione_mcp(AIUTO_PDFCRAFT)
    prova("sezione mcp: prende il --compact quando e' davvero di mcp",
          "--compact" in sezione)
    prova("sezione mcp: riconosce il dialetto a --root", "--root" in sezione)
    prova("sezione mcp: testo senza mcp da' sezione vuota",
          craft_mcp.sezione_mcp("nessun sottocomando qui") == "")


def prove_dentro() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        progetto = base / "progetto"
        (progetto / "src").mkdir(parents=True)
        gemello = base / "progetto-altro"
        gemello.mkdir()
        prova("dentro: una sottocartella sta dentro",
              craft_mcp.dentro(progetto / "src", progetto))
        prova("dentro: il progetto sta dentro se stesso",
              craft_mcp.dentro(progetto, progetto))
        prova("dentro: una cartella fratello sta fuori",
              not craft_mcp.dentro(base / "altrove", progetto))
        prova("dentro: un nome con lo stesso prefisso sta fuori",
              not craft_mcp.dentro(gemello, progetto),
              "progetto-altro non e' dentro progetto, per quanto la stringa lo somigli")


def prove_argomenti_mcp() -> None:
    p_roots = {"dialetto": "roots", "compatto": False}
    arg = craft_mcp.argomenti_mcp(p_roots, ["/w"], ["/r"], True)
    prova("argomenti: dialetto a radici separate",
          arg == ["mcp", "--automation-write-root", "/w", "--automation-read-root", "/r"],
          str(arg))
    p_root = {"dialetto": "root", "compatto": True}
    arg = craft_mcp.argomenti_mcp(p_root, ["/w"], ["/r"], True)
    prova("argomenti: dialetto a --root unico, con compatto",
          arg == ["mcp", "--root", "/w", "--root", "/r", "--compact"], str(arg))
    arg = craft_mcp.argomenti_mcp(p_root, ["/w"], [], False)
    prova("argomenti: compatto non imposto quando non lo si chiede",
          "--compact" not in arg, str(arg))
    prova("argomenti: --autosave non compare mai",
          all("--autosave" not in a for a in arg),
          "l'autosalvataggio scrive fuori dalle radici e non va mai generato")


# --------------------------------------------------------------------------- #
# prova dal vivo
# --------------------------------------------------------------------------- #

def prove_canale_e_tarball() -> None:
    """Il percorso Linux, esercitato anche da una macchina che Linux non e'.

    La forma del tarball e' quella reale, letta il 2026-10-12 dal rilascio di
    GridCraft 0.5.0: una cartella di primo livello, i due binari sotto `bin/`.
    E' la ragione per cui su Linux il canale predefinito e' il tarball e non
    l'AppImage, che il binario CLI se lo tiene dentro.
    """
    prova("canale: su Linux il predefinito porta con se' il CLI",
          craft_apps_comune.canale_predefinito("linux") == "tar",
          "un AppImage non espone <app>-cli, quindi il collegamento MCP non si genera")
    prova("canale: su Windows resta lo zip portabile",
          craft_apps_comune.canale_predefinito("windows") == "portable")

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        sorgente = base / "gridcraft-0.5.0-linux-x86_64"
        (sorgente / "bin").mkdir(parents=True)
        (sorgente / "bin" / "gridcraft-cli").write_text("#!/bin/sh\n", encoding="utf-8")
        (sorgente / "bin" / "gridcraft").write_text("#!/bin/sh\n", encoding="utf-8")
        (sorgente / "share").mkdir()
        (sorgente / "share" / "README.md").write_text("x", encoding="utf-8")
        archivio = base / "gridcraft-0.5.0-linux-x86_64.tar.gz"
        with tarfile.open(archivio, "w:gz") as a:
            a.add(sorgente, arcname=sorgente.name)

        casa = base / "casa"
        vecchio = os.environ.get("CRAFT_APPS_HOME")
        os.environ["CRAFT_APPS_HOME"] = str(casa)
        try:
            esito = craft_apps._posa("gridcraft", "linux", "tar", archivio, "GridCraft")
            prova("tarball: la posa riesce", esito == 0)
            atteso = casa / "GridCraft" / "bin" / "gridcraft-cli"
            prova("tarball: la cartella di primo livello viene appiattita", atteso.is_file(),
                  "atteso " + str(atteso))
            trovato = craft_apps_comune.trova_cli("gridcraft", "linux")
            prova("tarball: il CLI viene trovato dentro bin/",
                  trovato is not None and trovato.name == "gridcraft-cli",
                  str(trovato))
            prova("tarball: niente CLI per un'app non posata",
                  craft_apps_comune.trova_cli("deckcraft", "linux") is None)
        finally:
            if vecchio is None:
                os.environ.pop("CRAFT_APPS_HOME", None)
            else:
                os.environ["CRAFT_APPS_HOME"] = vecchio


def prove_dal_vivo() -> None:
    sist = sistema()
    cli = trova_cli("effectcraft", sist)
    if not cli:
        print("prova dal vivo saltata: EffectCraft non e' installato su questa macchina")
        return
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        radice = base / "dentro"
        radice.mkdir()
        fuori = base / "fuori.ecproj"
        messaggi = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
                "protocolVersion": "2024-11-05", "capabilities": {},
                "clientInfo": {"name": "prova", "version": "1"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
                "name": "open_project", "arguments": {"new": True}}},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
                "name": "save_project", "arguments": {"path": str(radice / "dentro.ecproj")}}},
            {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {
                "name": "save_project", "arguments": {"path": str(fuori)}}},
            {"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {
                "name": "run_script", "arguments": {"code": "writeLn('x')"}}},
        ]
        ingresso = "".join(json.dumps(m) + "\n" for m in messaggi)
        try:
            out = subprocess.run([str(cli), "mcp", "--automation-write-root", str(radice)],
                                 input=ingresso, capture_output=True, text=True,
                                 timeout=240, encoding="utf-8", errors="replace")
        except (OSError, subprocess.TimeoutExpired) as e:
            prova("dal vivo: il server MCP risponde", False, str(e))
            return
        risposte = {}
        for riga in (out.stdout or "").splitlines():
            riga = riga.strip()
            if not riga.startswith("{"):
                continue
            try:
                m = json.loads(riga)
            except ValueError:
                continue
            if "id" in m:
                risposte[m["id"]] = json.dumps(m, ensure_ascii=False)
        prova("dal vivo: scrittura dentro la radice riuscita",
              "3" in str(list(risposte)) and "dentro.ecproj" in risposte.get(3, ""),
              risposte.get(3, "nessuna risposta"))
        fuori_testo = risposte.get(4, "")
        prova("dal vivo: scrittura fuori dalla radice rifiutata",
              "outside the automation roots" in fuori_testo, fuori_testo[:200])
        prova("dal vivo: nessun file creato fuori dalla radice", not fuori.exists(),
              "il rifiuto deve valere sul disco e non solo nel messaggio")
        script_testo = risposte.get(5, "")
        prova("dal vivo: lo scripting e' negato mentre il confinamento e' attivo",
              "not available while file access is confined" in script_testo,
              script_testo[:200])


def main() -> int:
    p = argparse.ArgumentParser(description="Prove degli strumenti Craft.")
    p.add_argument("--senza-vivo", action="store_true", dest="senza_vivo",
                   help="salta la prova che avvia davvero il server MCP")
    args = p.parse_args()

    prove_somme()
    prove_nome_asset()
    prove_sezione_mcp()
    prove_dentro()
    prove_argomenti_mcp()
    prove_canale_e_tarball()
    if not args.senza_vivo:
        prove_dal_vivo()

    falliti = [e for e in ESITI if not e[1]]
    for nome, ok, dettaglio in ESITI:
        if not ok:
            print("FALLITA  " + nome + ("\n         " + dettaglio if dettaglio else ""))
    print("%d prove, %d fallite" % (len(ESITI), len(falliti)))
    return 1 if falliti else 0


if __name__ == "__main__":
    sys.exit(main())
