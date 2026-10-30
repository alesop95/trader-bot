"""Cassetta comune Claude/Codex: file atomici, lettura esplicita, nessuna esecuzione."""

from pathlib import Path
import argparse
import datetime as dt
import json
import os
import re
import uuid


def nome(value):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", value) or ".." in value:
        raise ValueError("nome partecipante non valido")
    return value


def pubblica(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(".tmp-" + uuid.uuid4().hex)
    data = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    with tmp.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, path)


def registra(root, identifier, agente, progetto):
    identifier = nome(identifier)
    if agente not in ("claude", "codex"):
        raise ValueError("agente non riconosciuto")
    value = {
        "nome": identifier,
        "agente": agente,
        "progetto": str(Path(progetto).resolve()),
        "registrato_il": dt.datetime.now(dt.timezone.utc).isoformat(),
        "stato": "registrato",
    }
    pubblica(Path(root) / identifier / "partecipante.json", value)
    (Path(root) / identifier / "in").mkdir(exist_ok=True)
    return value


def invia(root, sender, recipient, subject, body):
    sender, recipient = nome(sender), nome(recipient)
    root = Path(root)
    for identifier in (sender, recipient):
        if not (root / identifier / "partecipante.json").is_file():
            raise ValueError("partecipante non registrato: " + identifier)
    if len(body.encode("utf-8")) > 131072:
        raise ValueError("messaggio oltre128KiB")
    message = {
        "id": uuid.uuid4().hex,
        "da": sender,
        "a": recipient,
        "oggetto": subject,
        "testo": body,
        "creato_il": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    path = (
        root
        / recipient
        / "in"
        / (
            dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            + "-"
            + message["id"]
            + ".json"
        )
    )
    pubblica(path, message)
    return message


def leggi(root, identifier, archivia=False):
    identifier = nome(identifier)
    inbox = Path(root) / identifier / "in"
    result = []
    for path in sorted(inbox.glob("*.json")):
        message = json.loads(path.read_text(encoding="utf-8"))
        if message.get("a") != identifier:
            raise ValueError("destinatario incoerente: " + path.name)
        result.append(message)
        if archivia:
            dest = inbox.parent / "letti" / path.name
            dest.parent.mkdir(exist_ok=True)
            path.rename(dest)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=os.environ.get("PROJECT_AGENT_MAILBOX_ROOT"))
    sub = parser.add_subparsers(dest="azione", required=True)
    reg = sub.add_parser("registra")
    reg.add_argument("--nome", required=True)
    reg.add_argument("--agente", choices=["claude", "codex"], required=True)
    reg.add_argument("--progetto", required=True)
    send = sub.add_parser("invia")
    send.add_argument("--da", dest="sender", required=True)
    send.add_argument("--a", dest="recipient", required=True)
    send.add_argument("--oggetto", required=True)
    group = send.add_mutually_exclusive_group(required=True)
    group.add_argument("--testo")
    group.add_argument("--testo-file")
    read = sub.add_parser("leggi")
    read.add_argument("--nome", default=os.environ.get("PROJECT_AGENT_MAILBOX_ID"))
    read.add_argument("--archivia", action="store_true")
    sub.add_parser("elenca")
    args = parser.parse_args()
    if not args.root:
        parser.error("specificare --root oppure PROJECT_AGENT_MAILBOX_ROOT")
    try:
        if args.azione == "registra":
            result = registra(args.root, args.nome, args.agente, args.progetto)
        elif args.azione == "invia":
            body = (
                Path(args.testo_file).read_text(encoding="utf-8")
                if args.testo_file
                else args.testo
            )
            result = invia(args.root, args.sender, args.recipient, args.oggetto, body)
        elif args.azione == "leggi":
            if not args.nome:
                parser.error("specificare --nome oppure PROJECT_AGENT_MAILBOX_ID")
            result = leggi(args.root, args.nome, args.archivia)
        else:
            result = [
                json.loads(p.read_text(encoding="utf-8"))
                for p in sorted(Path(args.root).glob("*/partecipante.json"))
            ]
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError) as exc:
        print("posta: " + str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
