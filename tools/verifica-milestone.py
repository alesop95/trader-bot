"""Perimetro di chiusura: inventario verificabile, stage preservato e avvisi didattici."""

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path


def git(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True)
    if result.returncode:
        raise ValueError("lettura git fallita: " + result.stderr.decode("utf-8", "replace"))
    return result.stdout


def inventario(root):
    records = git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all").split(b"\0")
    paths, staged = {}, False
    position = 0
    while position < len(records):
        record = records[position]
        position += 1
        if not record:
            continue
        status = record[:2].decode("ascii")
        path = record[3:].decode("utf-8")
        staged |= status[0] not in (" ", "?")
        names = [path]
        if "R" in status or "C" in status:
            names.append(records[position].decode("utf-8"))
            position += 1
        for name in names:
            target = root / name
            content = target.read_bytes() if target.is_file() else b"<assente>"
            paths[name] = {"status": status, "sha256": hashlib.sha256(content).hexdigest()}
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "--verify", "HEAD"], capture_output=True)
    return {
        "head": head.stdout.decode().strip() if head.returncode == 0 else "PENDING-FIRST-COMMIT",
        "paths": sorted(paths),
        "files": paths,
        "staged": staged,
    }


def controlla(root, data):
    if data["staged"]:
        raise ValueError("stage già presente: chiusura fermata senza modificarlo")
    scope = root / "_notes/COMMIT-SCOPE.json"
    if scope.is_file():
        expected = json.loads(scope.read_text(encoding="utf-8-sig"))
        if expected.get("head") != data["head"]:
            raise ValueError("perimetro preparato su un altro HEAD: ricontrollare la milestone")
        paths = expected.get("paths")
        if not isinstance(paths, list) or not paths or any(not isinstance(p, str) for p in paths):
            raise ValueError("perimetro privo di una lista non vuota di percorsi esatti")
        outside = sorted(set(data["paths"]) - set(paths))
        missing = sorted(set(paths) - set(data["paths"]))
        if missing:
            raise ValueError("perimetro diverso: percorsi attesi assenti=" + repr(missing))
        data["fuori_perimetro"] = outside
        data["paths"] = sorted(set(paths))
        data["files"] = {name: data["files"][name] for name in data["paths"]}
    groups = Counter(path.split("/", 1)[0] if "/" in path else "(radice)" for path in data["paths"])
    warnings = []
    data["conferma_aree"] = len(data["paths"]) > 10 or len(groups) > 1
    if data.get("fuori_perimetro"):
        warnings.append("Lavoro fuori perimetro conservato: " + repr(data["fuori_perimetro"]))
    if len(data["paths"]) > 10 or len(groups) > 1:
        warnings.append("Il messaggio deve descrivere tutte le aree: " + ", ".join(f"{k}: {v}" for k, v in sorted(groups.items())))
    master = ".claude/context/studio-didattico-master.md"
    if (root / master).is_file():
        changed = data["paths"]
        relevant = any(p.startswith(("tools/", "deploy/", "infra/")) or p == ".claude/memory/decisions.md" for p in changed)
        teaching = master in changed or any(p.startswith(".claude/context/refactor-") for p in changed)
        if relevant and not teaching:
            warnings.append("Didattica adottata: ADR, strumenti o deploy cambiati senza una voce nel registro; verificare se serve e motivare l'eventuale assenza.")
    data["warnings"] = warnings
    return data


def verifica_risoluzioni_index(root):
    registry = ".claude/allineamento-risolti.json"
    if not git(root, "diff", "--cached", "--name-only", "--", registry).strip():
        return
    staged = json.loads(git(root, "show", ":" + registry))
    previous = subprocess.run(["git", "-C", str(root), "show", "HEAD:" + registry], capture_output=True)
    old = json.loads(previous.stdout) if previous.returncode == 0 else {}
    for name, entry in staged.items():
        if old.get(name) == entry:
            continue
        if not isinstance(entry, dict):
            raise ValueError("voce di risoluzione nuova non valida: " + name)
        expected = entry.get("locale_sha256_lf")
        if not expected:
            raise ValueError("risoluzione nuova senza firma del contenuto: " + name)
        content = git(root, "show", ":" + name).replace(b"\r\n", b"\n")
        if hashlib.sha256(content).hexdigest() != expected:
            raise ValueError("la risoluzione e il contenuto fuso non sono nello stesso commit: " + name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--radice", default=".")
    parser.add_argument("--snapshot", help="salva l'inventario per la conferma manuale")
    parser.add_argument("--verifica", help="rifiuta cambiamenti successivi all'inventario")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--paths0", action="store_true")
    parser.add_argument("--stage-risoluzioni", action="store_true")
    args = parser.parse_args()
    try:
        root = Path(args.radice).resolve()
        if args.stage_risoluzioni:
            verifica_risoluzioni_index(root)
            print("Risoluzioni e contenuti nello stage coerenti.")
            return 0
        data = controlla(root, inventario(root))
        if args.verifica:
            expected = json.loads(Path(args.verifica).read_text(encoding="utf-8"))
            keys = ("head", "paths", "files", "staged")
            if any(data.get(key) != expected.get(key) for key in keys):
                raise ValueError("file cambiati dopo l'anteprima: ripetere controlli e conferma")
        if args.snapshot:
            Path(args.snapshot).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        if args.paths0:
            sys.stdout.buffer.write(b"\0".join(p.encode("utf-8") for p in data["paths"]) + b"\0")
        elif args.json:
            print(json.dumps(data))
        else:
            print("Perimetro: " + str(len(data["paths"])) + " file")
            for message in data["warnings"]:
                print("AVVISO: " + message)
        return 0
    except (ValueError, OSError, KeyError, IndexError) as error:
        print("Chiusura fermata: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
