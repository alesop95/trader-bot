"""Stato del template all'apertura e manutenzione sicura delle esclusioni."""

from pathlib import Path
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import uuid


def git(root, *args):
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode:
        raise ValueError(result.stderr.strip() or "git non risponde")
    return result.stdout.strip()


def individua(progetto, esplicito=None):
    local = Path(progetto) / "_notes/template-root.txt"
    candidates = [esplicito, os.environ.get("PROJECT_TEMPLATE_ROOT")]
    if local.is_file():
        candidates.append(local.read_text(encoding="utf-8").strip())
    candidates.append(Path(progetto).resolve().parent / "template-claude-developing")
    for candidate in candidates:
        if candidate and (Path(candidate) / ".claude/PROJECT-SYSTEM.md").is_file():
            return Path(candidate).resolve()
    return None


def stato(progetto, template=None, ancora=None):
    progetto = Path(progetto)
    template = individua(progetto, template)
    marker = progetto / ".claude/allineamento-template.json"
    if not marker.is_file() and not ancora:
        return {
            "stato": "senza-ancora",
            "messaggio": "template: manca il marcatore di allineamento",
        }
    if template is None:
        return {
            "stato": "non-verificabile",
            "messaggio": "template: percorso non individuato; configurare PROJECT_TEMPLATE_ROOT",
        }
    try:
        previous = (
            ancora
            or json.loads(marker.read_text(encoding="utf-8-sig"))["template_commit"]
        )
        head = git(template, "rev-parse", "HEAD")
        git(template, "merge-base", "--is-ancestor", previous, head)
        count = int(git(template, "rev-list", "--count", previous + ".." + head))
        paths = git(
            template,
            "diff",
            "--name-only",
            "--diff-filter=A",
            previous,
            head,
            "--",
            ".claude/templates",
        ).splitlines()
        packages = sorted(
            {
                p.split("/")[2]
                for p in paths
                if len(p.split("/")) > 3
                and p.split("/")[2]
                not in ("tools", "skills", "rules", "agents", "norme")
                and git(
                    template,
                    "ls-tree",
                    "-d",
                    previous,
                    "--",
                    "/".join(p.split("/")[:3]),
                )
                == ""
            }
        )
        dirty = git(template, "status", "--porcelain", "--", ".claude").splitlines()
        msg = (
            "template: avanti di %d commit" % count
            if count
            else "template: nessun commit successivo all’ancora"
        )
        if packages:
            msg += "; pacchetti nuovi: " + ", ".join(packages)
        if dirty:
            msg += "; %d modifiche locali a monte non ancora propagabili" % len(dirty)
        return {
            "stato": "indietro" if count else "allineato",
            "commit_indietro": count,
            "pacchetti_nuovi": packages,
            "modifiche_locali_template": len(dirty),
            "messaggio": msg,
        }
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        return {
            "stato": "non-verificabile",
            "messaggio": "template: confronto non verificabile (%s)" % str(exc)[:160],
        }


def scadenza(motivo, oggi=None):
    oggi = oggi or dt.date.today()
    match = re.search(r"(?:^|\|)\s*fino=(\d{4}-\d{2}-\d{2})(?:\s*\||\s*$)", motivo)
    if match:
        try:
            end = dt.date.fromisoformat(match.group(1))
        except ValueError:
            return "scadenza non valida"
        return (
            "SCADUTA il " + end.isoformat()
            if end < oggi
            else "scade il " + end.isoformat()
        )
    if re.search(r"(?:^|\|)\s*condizione=\S", motivo):
        return (
            "condizione da verificare: "
            + motivo.split("condizione=", 1)[1].split("|", 1)[0].strip()
        )
    if re.search(r"(?:^|\|)\s*permanente(?:\s*\||\s*$)", motivo):
        return "permanente dichiarata"
    return "SENZA SCADENZA: aggiungere | fino=AAAA-MM-GG, | condizione=... oppure | permanente"


def normalizza(percorso):
    return percorso.replace("\\", "/").rstrip("/").casefold()


def rimuovi(elenco, progetto):
    """Una sola riga, byte delle altre invariati, copia preventiva e conteggio."""
    elenco = Path(elenco)
    original = elenco.read_bytes()
    bom = b"\xef\xbb\xbf" if original.startswith(b"\xef\xbb\xbf") else b""
    lines = original[len(bom) :].splitlines(keepends=True)
    key = normalizza(progetto)
    matches = [
        i
        for i, line in enumerate(lines)
        if normalizza(line.decode("utf-8-sig").split("#", 1)[0].strip()) == key
    ]
    if len(matches) != 1:
        raise ValueError("attesa una sola esclusione, trovate %d" % len(matches))
    backup = elenco.with_name(elenco.name + ".bak-" + uuid.uuid4().hex)
    shutil.copyfile(elenco, backup)
    if backup.read_bytes() != original:
        raise ValueError("copia preventiva non verificata")
    result = bom + b"".join(line for i, line in enumerate(lines) if i != matches[0])
    if len(result[len(bom) :].splitlines()) != len(lines) - 1:
        raise ValueError("conteggio delle righe incoerente")
    if elenco.read_bytes() != original:
        raise ValueError("elenco modificato da un’altra sessione")
    tmp = elenco.with_name(elenco.name + ".tmp-" + uuid.uuid4().hex)
    tmp.write_bytes(result)
    os.replace(tmp, elenco)
    if elenco.read_bytes() != result:
        raise ValueError("rilettura differente dalla scrittura")
    return {
        "righe_prima": len(lines),
        "righe_dopo": len(result[len(bom) :].splitlines()),
        "backup": str(backup),
        "sha256": hashlib.sha256(result).hexdigest(),
    }


def ricevuta(esiti, commit):
    written = [
        e
        for e in esiti
        if e["esito"]
        in ("NUOVO", "VECCHIO", "SUPERATO", "MERGE", "INNESCO", "SPOSTATO", "RIMOSSO")
    ]
    if not written:
        return None
    conflicts = [e["file"] for e in esiti if e["esito"] == "CONFLITTO"]
    text = (
        "# Ultimo allineamento dal template\n\n<!-- generato da allinea-dal-template.py -->\n\nCommit a monte: `%s`. File interessati dalla passata: %d. Commit e push del progetto restano manuali.\n\n"
        % (commit, len(written))
    )
    text += "| Esito | File |\n|---|---|\n"
    text += "".join("| %s | `%s` |\n" % (e["esito"], e["file"]) for e in written)
    text += "\nConflitti ancora da risolvere: %d.\n" % len(conflicts)
    if conflicts:
        text += "\n" + "\n".join("`%s`" % p for p in conflicts) + "\n"
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--progetto", default=".")
    parser.add_argument("--template")
    parser.add_argument(
        "--ancora", help="commit letto dal marcatore di un progetto remoto"
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--esclusione", help="motivo con metadati | fino=... o | condizione=..."
    )
    parser.add_argument("--rimuovi-esclusione", metavar="ELENCO")
    args = parser.parse_args()
    if args.rimuovi_esclusione:
        print(
            json.dumps(
                rimuovi(args.rimuovi_esclusione, args.progetto), ensure_ascii=False
            )
        )
        return 0
    result = stato(args.progetto, args.template, args.ancora)
    if args.esclusione is not None:
        result["scadenza_esclusione"] = scadenza(args.esclusione)
        result["messaggio"] += "; esclusione " + result["scadenza_esclusione"]
    print(json.dumps(result, ensure_ascii=False) if args.json else result["messaggio"])
    receipt = Path(args.progetto) / ".claude/ultimo-allineamento.md"
    if not args.json and receipt.is_file():
        print("Ultima consegna: leggere .claude/ultimo-allineamento.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
