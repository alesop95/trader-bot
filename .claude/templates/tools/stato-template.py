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
    # Dal 2026-11-12 (L-009 di un progetto istanziato) il nome della cartella del template non
    # sta piu' scritto qui, perche' questo file arriva in ogni progetto: l'indirizzo si legge
    # da ~/.config/template-claude-path.txt, lo stesso file che usa il controllo delle identita'.
    indirizzo = Path.home() / ".config" / "template-claude-path.txt"
    if indirizzo.is_file():
        candidates.append(indirizzo.read_text(encoding="utf-8-sig").strip())
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


def cella(valore):
    """Una cella di tabella sta su una riga sola e non contiene barre verticali."""
    testo = "" if valore is None else str(valore)
    return testo.replace("|", "/").replace("\r", " ").replace("\n", " ").strip()


ATTESE = "docs/attese-dai-filoni.json"


def attese(template, progetto):
    """Cio' che un filone del template aspetta da questo progetto.

    Il registro dei filoni vive nel template e non viene consegnato ai progetti,
    quindi una decisione gia' presa a monte resta invisibile da valle e il
    progetto la ripropone come propria: e' la lezione L-018 di un progetto
    istanziato, del 2026-11-09. La ricevuta e' il posto che il progetto legge da
    se', e questa funzione sceglie le sole voci che riguardano lui.
    """
    if not template:
        return []
    percorso = Path(template) / ATTESE
    if not percorso.is_file():
        return []
    try:
        voci = json.loads(percorso.read_text(encoding="utf-8-sig"))
    except ValueError:
        return []
    if not isinstance(voci, list):
        return []
    nome = Path(progetto).name.strip().lower()
    scelte = []
    for voce in voci:
        if not isinstance(voce, dict):
            continue
        if str(voce.get("progetto", "")).strip().lower() != nome:
            continue
        if str(voce.get("stato", "aperta")).strip().lower() != "aperta":
            continue
        # Il documento sta nel template e non nel progetto: si cita con il nome della
        # cartella del template davanti, altrimenti il controllo dei link del progetto
        # lo legge come un percorso locale inesistente e lo riscrive, facendo divergere
        # la ricevuta dal generatore a ogni passata (misurato il 2026-11-09).
        voce = dict(voce)
        documento = str(voce.get("documento", "")).strip().lstrip("/")
        if documento and not documento.startswith(Path(template).name + "/"):
            voce["documento"] = Path(template).resolve().name + "/" + documento
        scelte.append(voce)
    return scelte


TITOLO_ATTESE = "## Il template aspetta da questo progetto"


def sezione_attese(attesi):
    """La sezione che porta al progetto cio' che un filone aspetta da lui."""
    attesi = list(attesi or [])
    if not attesi:
        return ""
    testo = "\n" + TITOLO_ATTESE + "\n\n"
    testo += (
        # Accenti veri e non apostrofi: la ricevuta e' un documento generato, e il
        # correttore degli accenti di un progetto lo riscriverebbe a ogni chiusura,
        # facendo divergere per sempre la copia dal generatore (misurato il 2026-11-09).
        "Voci aperte nell'indice dei filoni del template, che resta a monte e non arriva qui. "
        "Finché una voce è aperta, la capacità che descrive è già decisa: non si ripropone "
        "come nuova e non si costruisce a mano una seconda volta.\n\n"
    )
    testo += "| Filone | Che cosa aspetta da qui | Documento a monte | Aperta il |\n|---|---|---|---|\n"
    for voce in attesi:
        testo += "| %s | %s | `%s` | %s |\n" % (
            cella(voce.get("filone")),
            cella(voce.get("attesa")),
            cella(voce.get("documento")),
            cella(voce.get("aperta")),
        )
    return testo


def innesta_attese(testo, attesi):
    """Aggiorna la sola sezione delle attese dentro una ricevuta gia' scritta.

    Serve quando la passata non consegna nessun file: rigenerare la ricevuta
    cancellerebbe il verbale dell'ultima consegna, e riscriverla identica a ogni
    corsa lascerebbe il progetto "incompleto" per sempre, come misurato il
    2026-11-09 sul primo progetto con un'attesa aperta.
    """
    corpo = testo.split(TITOLO_ATTESE)[0].rstrip("\n")
    sezione = sezione_attese(attesi)
    if not sezione:
        return corpo + "\n"
    return corpo + "\n" + sezione


def ricevuta(esiti, commit, attesi=None):
    written = [
        e
        for e in esiti
        if e["esito"]
        in ("NUOVO", "VECCHIO", "SUPERATO", "MERGE", "RISOLTO", "INNESCO", "SPOSTATO", "RIMOSSO")
    ]
    attesi = list(attesi or [])
    if not written and not attesi:
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
    text += sezione_attese(attesi)
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
