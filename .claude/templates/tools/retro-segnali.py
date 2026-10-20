#!/usr/bin/env python3
"""I segni di fatica di una sessione, letti dalla sua trascrizione, per la retrospettiva.

Perché esiste. Una lezione del sistema nasce oggi solo se qualcuno nota il problema
mentre lavora: il 2026-10-05, in un progetto istanziato, uno script di scrittura non
trovava la propria ancora nei file CRLF e per cinque giri un file è stato dichiarato
scritto senza esserlo, e il difetto è emerso per caso. La skill `retrospettiva`, adattata
il 2026-10-20 da `retro` di mattpocock/skills (licenza MIT), va invece a cercare quei
momenti alla fine di una sessione faticosa. Questo strumento ne fa la parte che non
richiede giudizio: legge la trascrizione JSONL di Claude Code e conta, senza modello e
senza token, i punti in cui la sessione ha arrancato.

I segni sono sei: i comandi falliti, le chiamate negate dai permessi o dall'utente, lo
stesso file letto più volte, la stessa ricerca ripetuta, i risultati di strumento molto
voluminosi, e i messaggi dell'utente che correggono o interrompono. Ogni segno porta il
numero del turno e un estratto, così che chi propone una correzione possa ricondurla a
un momento preciso invece di inventare un consiglio generico.

    python .claude/templates/tools/retro-segnali.py                     # la sessione più recente del progetto
    python .claude/templates/tools/retro-segnali.py --sessione <file.jsonl>
    python .claude/templates/tools/retro-segnali.py --json _notes/retrospettiva/segnali.json
    python .claude/templates/tools/retro-segnali.py --autotest

La trascrizione sta in `<cartella di configurazione>/projects/<progetto>/<sessione>.jsonl`,
dove la cartella è `CLAUDE_CONFIG_DIR` oppure `~/.claude`. Su una macchina con il wipe a
fine sessione la trascrizione di una sessione chiusa non esiste più: la retrospettiva si
fa nella sessione stessa, prima di chiudere. Le trascrizioni di Codex non sono ancora lette.
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import re
import sys
import tempfile
from pathlib import Path

VOLUMINOSO = 20000
RILETTURE = 3
RICERCHE = 2
ESTRATTO = 160

NEGATA = re.compile(r"doesn't want to proceed|was rejected|denied|permission to use .* has been denied|negat", re.I)
CORREZIONE = re.compile(
    r"^\s*no\b|\bsbagliat|\bnon (?:ho capito|è quello|era quello|funziona|hai)|\bti (?:ho|avevo) detto"
    r"|\bdi nuovo\b|\bancora\b.*\b(?:errore|sbagli)|\bperché hai\b|\binvece\b|\bcristo\b|\bma come\b"
    r"|\bthat's wrong\b|\bi said\b|\bnot what i\b", re.I)
INTERRUZIONE = "[Request interrupted by user"


def cartella_progetto(radice: Path) -> Path:
    base = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    nome = re.sub(r"[^A-Za-z0-9]", "-", str(radice.resolve()))
    return base / "projects" / nome


def sessione_recente(radice: Path) -> Path:
    d = cartella_progetto(radice)
    file = sorted(d.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True) if d.is_dir() else []
    if not file:
        raise SystemExit("nessuna trascrizione in %s: la sessione è già stata cancellata dal wipe, "
                         "oppure il progetto si apre da un altro percorso (usa --sessione)" % d)
    return file[0]


def testo_di(contenuto) -> str:
    if isinstance(contenuto, str):
        return contenuto
    if isinstance(contenuto, list):
        return "\n".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in contenuto)
    return ""


def estratto(s: str) -> str:
    s = " ".join(s.split())
    return s if len(s) <= ESTRATTO else s[:ESTRATTO - 1] + "…"


def riassumi_input(nome: str, inp: dict) -> str:
    for chiave in ("file_path", "pattern", "command", "url", "query", "description", "skill"):
        if chiave in inp:
            return "%s %s" % (nome, estratto(str(inp[chiave])))
    return nome


def analizza(righe) -> dict:
    turno = 0
    usi = {}
    s = {"turni": 0, "chiamate": 0, "errori": [], "negate": [], "riletture": [], "ricerche": [],
         "voluminosi": [], "correzioni": [], "interruzioni": []}
    letture = collections.defaultdict(list)
    cercate = collections.defaultdict(list)
    for riga in righe:
        riga = riga.strip()
        if not riga:
            continue
        try:
            d = json.loads(riga)
        except json.JSONDecodeError:
            continue
        if d.get("isSidechain") or d.get("type") not in ("user", "assistant"):
            continue
        msg = d.get("message") or {}
        cont = msg.get("content")
        if d["type"] == "user" and not d.get("isMeta"):
            blocchi = cont if isinstance(cont, list) else [{"type": "text", "text": cont or ""}]
            risultati = [b for b in blocchi if isinstance(b, dict) and b.get("type") == "tool_result"]
            if not risultati:
                testo = testo_di([b for b in blocchi if isinstance(b, dict) and b.get("type") == "text"])
                if INTERRUZIONE in testo:
                    s["interruzioni"].append({"turno": turno})
                    continue
                if testo.lstrip().startswith("<"):
                    continue
                turno += 1
                if CORREZIONE.search(testo):
                    s["correzioni"].append({"turno": turno, "testo": estratto(testo)})
                continue
            for b in risultati:
                uso = usi.get(b.get("tool_use_id"), ("?", "?"))
                testo = testo_di(b.get("content"))
                if b.get("is_error"):
                    voce = {"turno": turno, "strumento": uso[1], "testo": estratto(testo)}
                    s["negate" if NEGATA.search(testo) else "errori"].append(voce)
                if len(testo) >= VOLUMINOSO:
                    s["voluminosi"].append({"turno": turno, "strumento": uso[1], "caratteri": len(testo)})
        elif d["type"] == "assistant" and isinstance(cont, list):
            for b in cont:
                if not isinstance(b, dict) or b.get("type") != "tool_use":
                    continue
                s["chiamate"] += 1
                nome, inp = b.get("name", "?"), b.get("input") or {}
                usi[b.get("id")] = (nome, riassumi_input(nome, inp))
                if nome == "Read" and inp.get("file_path"):
                    letture[inp["file_path"]].append(turno)
                if nome in ("Grep", "Glob") and inp.get("pattern"):
                    cercate[(nome, inp["pattern"], inp.get("path", ""))].append(turno)
    s["turni"] = turno
    s["riletture"] = [{"file": f, "volte": len(t), "turni": sorted(set(t))} for f, t in letture.items() if len(t) >= RILETTURE]
    s["ricerche"] = [{"strumento": k[0], "pattern": k[1], "volte": len(t), "turni": sorted(set(t))}
                     for k, t in cercate.items() if len(t) >= RICERCHE]
    return s


def stampa(s: dict, origine: str) -> None:
    print("sessione: %s" % origine)
    print("turni dell'utente: %d, chiamate di strumento: %d" % (s["turni"], s["chiamate"]))
    sezioni = [
        ("errori", "comandi falliti", lambda v: "turno %d, %s: %s" % (v["turno"], v["strumento"], v["testo"])),
        ("negate", "chiamate negate", lambda v: "turno %d, %s: %s" % (v["turno"], v["strumento"], v["testo"])),
        ("riletture", "file letti più volte", lambda v: "%s, %d volte (turni %s)" % (v["file"], v["volte"], v["turni"])),
        ("ricerche", "ricerche ripetute", lambda v: "%s %r, %d volte (turni %s)" % (v["strumento"], v["pattern"], v["volte"], v["turni"])),
        ("voluminosi", "risultati voluminosi", lambda v: "turno %d, %s: %d caratteri" % (v["turno"], v["strumento"], v["caratteri"])),
        ("correzioni", "correzioni dell'utente", lambda v: "turno %d: %s" % (v["turno"], v["testo"])),
        ("interruzioni", "interruzioni dell'utente", lambda v: "dopo il turno %d" % v["turno"]),
    ]
    totale = 0
    for chiave, titolo, riga in sezioni:
        voci = s[chiave]
        totale += len(voci)
        if voci:
            print("\n== %s: %d" % (titolo, len(voci)))
            for v in voci:
                print("   " + riga(v))
    print("\nsegni di fatica: %d" % totale)


# --------------------------------------------------------------------------- prove

def autotest() -> int:
    casi = rossi = 0

    def caso(nome: str, ok: bool) -> None:
        nonlocal casi, rossi
        casi += 1
        rossi += 0 if ok else 1
        print(("ok   " if ok else "ROSSO ") + nome)

    def utente(testo, **extra):
        return dict({"type": "user", "message": {"role": "user", "content": testo}}, **extra)

    def uso(i, nome, **inp):
        return {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": i, "name": nome, "input": inp}]}}

    def esito(i, testo, errore=False):
        return {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": i, "content": testo, "is_error": errore}]}}

    righe = [
        utente("aggiungi la funzione"),
        uso("1", "Read", file_path="a.py"), esito("1", "x"),
        uso("2", "Read", file_path="a.py"), esito("2", "x"),
        uso("3", "Grep", pattern="def foo"), esito("3", ""),
        uso("4", "Grep", pattern="def foo"), esito("4", ""),
        uso("5", "Edit", file_path="a.py"), esito("5", "String to replace not found in file.", True),
        uso("6", "Bash", command="rm -rf build"), esito("6", "The user doesn't want to proceed with this tool use.", True),
        uso("7", "Bash", command="cat grande.log"), esito("7", "y" * VOLUMINOSO),
        utente("no, non è quello che ti ho chiesto"),
        uso("8", "Read", file_path="a.py"), esito("8", "x"),
        uso("9", "Read", file_path="b.py"), esito("9", "x"),
        utente([{"type": "text", "text": "[Request interrupted by user]"}]),
        utente("<command-name>/riprendi</command-name>"),
        utente("va bene, procedi"),
        utente("ordine del subagente", isSidechain=True),
        {"type": "assistant", "isSidechain": True, "message": {"content": [{"type": "tool_use", "id": "s", "name": "Read", "input": {"file_path": "b.py"}}]}},
        "questa riga non è JSON",
    ]
    testo = "\n".join(r if isinstance(r, str) else json.dumps(r) for r in righe)
    s = analizza(testo.splitlines())
    caso("un comando fallito si conta con lo strumento che l'ha prodotto", len(s["errori"]) == 1 and s["errori"][0]["strumento"].startswith("Edit"))
    caso("una chiamata negata non si confonde con un errore", len(s["negate"]) == 1 and "rm -rf" in s["negate"][0]["strumento"])
    caso("un file letto tre volte è una rilettura", [r["file"] for r in s["riletture"]] == ["a.py"])
    caso("un file letto una volta sola non lo è, neanche se lo legge un subagente", all(r["file"] != "b.py" for r in s["riletture"]))
    caso("la stessa ricerca due volte è una ricerca ripetuta", len(s["ricerche"]) == 1 and s["ricerche"][0]["volte"] == 2)
    caso("un risultato oltre la soglia è voluminoso", len(s["voluminosi"]) == 1 and s["voluminosi"][0]["caratteri"] == VOLUMINOSO)
    caso("una correzione dell'utente si riconosce con il suo turno", [c["turno"] for c in s["correzioni"]] == [2])
    caso("un messaggio neutro non è una correzione", not any("procedi" in c["testo"] for c in s["correzioni"]))
    caso("un'interruzione si conta e non diventa un turno", len(s["interruzioni"]) == 1 and s["turni"] == 3)
    caso("le chiamate del subagente restano fuori", s["chiamate"] == 9)
    with tempfile.TemporaryDirectory() as d:
        vecchio = os.environ.get("CLAUDE_CONFIG_DIR")
        os.environ["CLAUDE_CONFIG_DIR"] = d
        try:
            prj = Path(d) / "mio progetto"
            prj.mkdir()
            cartella = cartella_progetto(prj)
            caso("la cartella delle trascrizioni sostituisce ogni carattere non alfanumerico",
                 cartella.parent == Path(d) / "projects" and re.fullmatch(r"[A-Za-z0-9-]+", cartella.name) is not None)
            cartella.mkdir(parents=True)
            (cartella / "vecchia.jsonl").write_text("{}", encoding="utf-8")
            nuova = cartella / "nuova.jsonl"
            nuova.write_text("{}", encoding="utf-8")
            os.utime(cartella / "vecchia.jsonl", (1, 1))
            caso("senza --sessione si prende la trascrizione più recente", sessione_recente(prj) == nuova)
        finally:
            if vecchio is None:
                os.environ.pop("CLAUDE_CONFIG_DIR", None)
            else:
                os.environ["CLAUDE_CONFIG_DIR"] = vecchio
    print("\n%d casi superati su %d" % (casi - rossi, casi))
    return 1 if rossi else 0


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    p = argparse.ArgumentParser(description="I segni di fatica di una sessione, per la retrospettiva.")
    p.add_argument("--autotest", action="store_true")
    p.add_argument("--radice", default=".", help="radice del progetto, per trovare le sue trascrizioni")
    p.add_argument("--sessione", help="trascrizione JSONL da leggere, invece della più recente")
    p.add_argument("--json", dest="uscita", help="scrive i segni anche in questo file JSON")
    a = p.parse_args(argv)
    if a.autotest:
        return autotest()
    f = Path(a.sessione) if a.sessione else sessione_recente(Path(a.radice))
    with f.open(encoding="utf-8", errors="replace") as h:
        s = analizza(h)
    stampa(s, str(f))
    if a.uscita:
        u = Path(a.uscita)
        u.parent.mkdir(parents=True, exist_ok=True)
        u.write_text(json.dumps(dict(s, sessione=str(f)), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        print("scritto %s" % u)
    return 0


if __name__ == "__main__":
    sys.exit(main())
