#!/usr/bin/env python3
"""Collega un'applicazione Craft a un agente, confinata alle cartelle del progetto.

Non si fida di una tabella scritta a mano: interroga il binario CLI installato,
legge dal suo aiuto quali opzioni di confinamento accetta e genera di conseguenza
la configurazione per Claude Code (.mcp.json) o per Codex (codex mcp add).
Un'applicazione che non sappia confinare l'accesso ai file non viene collegata, a
meno di chiederlo per nome con --senza-confinamento.

    python craft-mcp.py elenca --conta
    python craft-mcp.py genera effectcraft --scrittura src/animation --per claude
    python craft-mcp.py genera pdfcraft --lettura _notes/fonti --per codex

La misura del costo di contesto si prende con --conta, che avvia davvero ogni
server e conta i tool che dichiara: e' l'unica forma onesta, perche' i documenti
delle applicazioni elencano meno tool di quanti i binari ne espongano.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from craft_apps_comune import APPS, SENZA_CLI, sistema, trova_cli  # noqa: E402

# Dialetti di confinamento riconosciuti, in ordine di preferenza. Il primo che
# compare nell'aiuto del binario vince. La tabella dice solo come si scrive
# l'opzione, non quali applicazioni la abbiano: quello lo dice il binario.
DIALETTI = [
    ("roots", ("--automation-write-root", "--automation-read-root")),
    ("root", ("--root",)),
]


def aiuto(cli: Path) -> str:
    for argomenti in (["--help"], ["mcp", "--help"], []):
        try:
            out = subprocess.run([str(cli)] + argomenti, capture_output=True, text=True,
                                 timeout=60, encoding="utf-8", errors="replace")
        except (OSError, subprocess.TimeoutExpired):
            continue
        testo = (out.stdout or "") + (out.stderr or "")
        if "mcp" in testo:
            return testo
    return ""


def sezione_mcp(testo: str) -> str:
    """Le sole righe dell'aiuto che descrivono il sottocomando mcp.

    Serve a non confondere un'opzione di un altro sottocomando con una di questo:
    l'aiuto di photocraft-cli documenta un --compact che appartiene a `info`, e
    cercarlo nel testo intero faceva credere che il server MCP lo accettasse,
    cosa che si scopriva solo quando il server rifiutava di partire.
    """
    righe = testo.splitlines()
    inizio = None
    for i, riga in enumerate(righe):
        if re.search(r"(^|\s)mcp(\s|$)", riga) and ("[" in riga or "--" in riga):
            inizio = i
            break
    if inizio is None:
        return ""
    rientro = len(righe[inizio]) - len(righe[inizio].lstrip())
    presa = [righe[inizio]]
    for riga in righe[inizio + 1:]:
        if not riga.strip():
            break
        if (len(riga) - len(riga.lstrip())) <= rientro:
            break
        presa.append(riga)
    return "\n".join(presa)


def profilo(app: str, sist: str) -> dict:
    """Che cosa questo binario sa fare davvero, letto dal binario."""
    cli = trova_cli(app, sist)
    if not cli:
        return {"app": app, "installata": False}
    testo = aiuto(cli)
    sezione = sezione_mcp(testo)
    dialetto = None
    for nome, opzioni in DIALETTI:
        if all(o in sezione for o in opzioni):
            dialetto = nome
            break
    return {
        "app": app,
        "installata": True,
        "cli": cli,
        "mcp": bool(sezione),
        "dialetto": dialetto,
        "compatto": "--compact" in sezione,
        "controllo": "--control" in testo,
    }


# --------------------------------------------------------------------------- #
# misura del costo di contesto
# --------------------------------------------------------------------------- #

def conta_tool(cli: Path, argomenti: list) -> tuple:
    """Avvia il server MCP e conta i tool dichiarati. Ritorna (quanti, byte)."""
    messaggi = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2024-11-05", "capabilities": {},
            "clientInfo": {"name": "craft-mcp", "version": "1"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    ]
    ingresso = "".join(json.dumps(m) + "\n" for m in messaggi)
    try:
        out = subprocess.run([str(cli)] + argomenti, input=ingresso, capture_output=True,
                             text=True, timeout=180, encoding="utf-8", errors="replace")
    except (OSError, subprocess.TimeoutExpired):
        return (None, None)
    for riga in (out.stdout or "").splitlines():
        riga = riga.strip()
        if not riga.startswith("{"):
            continue
        try:
            m = json.loads(riga)
        except ValueError:
            continue
        tool = (m.get("result") or {}).get("tools")
        if tool is not None:
            blob = json.dumps(tool, ensure_ascii=False)
            return (len(tool), len(blob.encode("utf-8")))
    return (None, None)


def cmd_elenca(args) -> int:
    sist = sistema()
    print("%-12s %-11s %-13s %-9s %s" % ("app", "installata", "confinamento", "compatto", "tool"))
    for app in sorted(APPS):
        if app in SENZA_CLI:
            continue
        p = profilo(app, sist)
        if not p["installata"]:
            print("%-12s %-11s %-13s %-9s %s" % (app, "no", "-", "-", "-"))
            continue
        conta = "-"
        if args.conta and p["mcp"]:
            argomenti = ["mcp"] + (["--compact"] if p["compatto"] else [])
            quanti, byte = conta_tool(p["cli"], argomenti)
            if quanti is not None:
                conta = "%d (~%d token%s)" % (quanti, byte // 4,
                                              ", compatto" if p["compatto"] else "")
        print("%-12s %-11s %-13s %-9s %s" % (
            app, "si", p["dialetto"] or "NESSUNO", "si" if p["compatto"] else "no", conta))
    if args.conta:
        print("\nI token sono il costo che ogni sessione paga per avere quel server collegato,")
        print("prima ancora del primo messaggio. Vedi la sezione sul contesto nel README.")
    return 0


# --------------------------------------------------------------------------- #
# generazione
# --------------------------------------------------------------------------- #

def dentro(figlio: Path, genitore: Path) -> bool:
    try:
        figlio.resolve().relative_to(genitore.resolve())
        return True
    except ValueError:
        return False


def argomenti_mcp(p: dict, scrittura: list, lettura: list, compatto: bool) -> list:
    argomenti = ["mcp"]
    if p["dialetto"] == "roots":
        for d in scrittura:
            argomenti += ["--automation-write-root", d]
        for d in lettura:
            argomenti += ["--automation-read-root", d]
    elif p["dialetto"] == "root":
        for d in scrittura + lettura:
            argomenti += ["--root", d]
    if compatto and p["compatto"]:
        argomenti.append("--compact")
    return argomenti


def cmd_genera(args) -> int:
    sist = sistema()
    progetto = Path(args.progetto).resolve()
    scrittura, lettura = [], []
    for elenco, sorgente in ((scrittura, args.scrittura or []), (lettura, args.lettura or [])):
        for d in sorgente:
            percorso = (progetto / d).resolve() if not Path(d).is_absolute() else Path(d).resolve()
            if not dentro(percorso, progetto) and not args.fuori_progetto:
                print("rifiuto: " + str(percorso) + " sta fuori dal progetto " + str(progetto) +
                      ". Passa --fuori-progetto se e' davvero cio' che vuoi.")
                return 2
            if not percorso.exists():
                print("rifiuto: " + str(percorso) + " non esiste. Creala prima, "
                      "cosi' la radice e' quella che credi.")
                return 2
            elenco.append(str(percorso).replace("\\", "/"))

    if not scrittura and not lettura:
        print("rifiuto: nessuna radice indicata. Un server senza confinamento vede "
              "tutto il disco con i permessi del tuo utente.")
        return 2

    voci, righe_codex, saltate = {}, [], []
    for app in args.app:
        p = profilo(app, sist)
        if not p["installata"]:
            saltate.append(app + " (non installata)")
            continue
        if not p["mcp"]:
            saltate.append(app + " (il suo CLI non ha il sottocomando mcp)")
            continue
        if p["dialetto"] is None and not args.senza_confinamento:
            saltate.append(app + " (non dichiara opzioni di confinamento: "
                           "usa --senza-confinamento se accetti il rischio)")
            continue
        argomenti = argomenti_mcp(p, scrittura, lettura, not args.pdfcraft_completo)
        voci[app] = {"command": str(p["cli"]), "args": argomenti}
        citati = " ".join('"' + a + '"' if " " in a else a for a in argomenti)
        righe_codex.append('codex mcp add ' + app + ' -- "' + str(p["cli"]) + '" ' + citati)

    if saltate:
        print("non collegate: " + "; ".join(saltate))
    if not voci:
        return 1

    if args.per == "codex":
        print("\nCodex tiene i server MCP nella radice dell'account e non nel progetto:")
        print("questi comandi valgono per tutte le sessioni di quel CODEX_HOME, quindi la")
        print("radice qui sotto diventa il confine di ogni progetto aperto con esso.\n")
        for riga in righe_codex:
            print(riga)
        return 0

    blocco = {"mcpServers": voci}
    destinazione = progetto / ".mcp.json"
    if not args.scrivi:
        print("\n" + json.dumps(blocco, indent=2, ensure_ascii=False))
        print("\nScrivilo in " + str(destinazione) + " con --scrivi (le voci esistenti restano).")
        return 0

    esistente = {}
    if destinazione.is_file():
        try:
            esistente = json.loads(destinazione.read_text(encoding="utf-8"))
        except ValueError:
            print("rifiuto: " + str(destinazione) + " non e' JSON valido, non lo sovrascrivo")
            return 1
    esistente.setdefault("mcpServers", {}).update(voci)
    destinazione.write_text(json.dumps(esistente, indent=2, ensure_ascii=False) + "\n",
                            encoding="utf-8")
    print("scritto " + str(destinazione) + ": " + ", ".join(sorted(voci)))
    return 0


def cmd_controlla(args) -> int:
    """Rilegge un .mcp.json gia' scritto e dice che cosa vi e' rimasto scoperto."""
    progetto = Path(args.progetto).resolve()
    destinazione = Path(args.file) if args.file else progetto / ".mcp.json"
    if not destinazione.is_file():
        print("nessun " + str(destinazione) + " da controllare")
        return 0
    try:
        dati = json.loads(destinazione.read_text(encoding="utf-8"))
    except ValueError as e:
        print("rifiuto: " + str(destinazione) + " non e' JSON valido (" + str(e) + ")")
        return 1
    rilievi = []
    esaminate = 0
    for nome, voce in (dati.get("mcpServers") or {}).items():
        argomenti = [str(a) for a in (voce.get("args") or [])]
        comando = str(voce.get("command", ""))
        if "mcp" not in argomenti or not any(c in (comando + " " + nome).lower()
                                             for c in APPS):
            continue
        esaminate += 1
        radici = [argomenti[i + 1] for i, a in enumerate(argomenti[:-1])
                  if a in ("--automation-write-root", "--automation-read-root", "--root")]
        if not radici:
            rilievi.append(nome + ": nessuna radice di confinamento, il server vede tutto "
                                  "il disco con i permessi del tuo utente")
        for r in radici:
            p = Path(r)
            if not p.exists():
                rilievi.append(nome + ": la radice " + r + " non esiste")
            elif not dentro(p, progetto):
                rilievi.append(nome + ": la radice " + r + " sta fuori dal progetto")
        if "--autosave" in argomenti:
            rilievi.append(nome + ": --autosave scrive copie del progetto in una cartella "
                                  "dei dati applicativi, che non e' una delle radici e non "
                                  "e' ignorata da git perche' sta fuori dal repository")
        if "--bridge" in argomenti or "--connect" in argomenti:
            rilievi.append(nome + ": in modo ponte il confinamento lo impone l'applicazione "
                                  "in esecuzione, non queste opzioni")
    if esaminate == 0:
        print("nessun server Craft in " + str(destinazione))
        return 0
    if not rilievi:
        print("controllati " + str(esaminate) + " server Craft in " + str(destinazione) +
              ": niente da segnalare")
        return 0
    print("controllati " + str(esaminate) + " server Craft in " + str(destinazione) + ":")
    for r in rilievi:
        print("  " + r)
    return 1


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Collegamento confinato delle applicazioni Craft a un agente.")
    sub = p.add_subparsers(dest="comando")

    pe = sub.add_parser("elenca", help="che cosa sa fare ogni binario installato")
    pe.add_argument("--conta", action="store_true",
                    help="avvia ogni server e misura quanti tool dichiara")
    pe.set_defaults(func=cmd_elenca)

    pg = sub.add_parser("genera", help="genera la configurazione per Claude Code o Codex")
    pg.add_argument("app", nargs="+", choices=sorted(a for a in APPS if a not in SENZA_CLI),
                    metavar="APP")
    pg.add_argument("--scrittura", action="append", metavar="DIR",
                    help="cartella in cui l'agente puo' scrivere e leggere (ripetibile)")
    pg.add_argument("--lettura", action="append", metavar="DIR",
                    help="cartella in sola lettura (ripetibile)")
    pg.add_argument("--progetto", default=os.getcwd())
    pg.add_argument("--per", choices=["claude", "codex"], default="claude")
    pg.add_argument("--scrivi", action="store_true", help="aggiorna .mcp.json invece di stampare")
    pg.add_argument("--fuori-progetto", action="store_true", dest="fuori_progetto")
    pg.add_argument("--senza-confinamento", action="store_true", dest="senza_confinamento")
    pg.add_argument("--pdfcraft-completo", action="store_true", dest="pdfcraft_completo",
                    help="non passare --compact dove esiste, al prezzo di contesto del README")
    pg.set_defaults(func=cmd_genera)

    pc = sub.add_parser("controlla", help="rilegge un .mcp.json e segnala cio' che resta scoperto")
    pc.add_argument("--progetto", default=os.getcwd())
    pc.add_argument("--file", help="un .mcp.json diverso da quello del progetto")
    pc.set_defaults(func=cmd_controlla)

    args = p.parse_args(argv)
    if not getattr(args, "func", None):
        args = p.parse_args(["elenca"])
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
