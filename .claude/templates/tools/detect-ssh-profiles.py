#!/usr/bin/env python3
"""Rileva i profili SSH verso GitHub configurati su QUESTA macchina, in sola lettura.

Esiste perché la regola `git-identity-and-repo.md` non può sapere quali alias e quali
chiavi esistano sulla macchina dove viene letta: gli alias sono una convenzione della
singola installazione, non un fatto del sistema di progetto, e assumerli porta a
proporre un remoto che punta a una chiave inesistente. Lo strumento legge la
configurazione reale e la presenta; la scelta del profilo resta dell'utente.

Non stampa mai materiale di chiave: solo percorsi, alias e il fatto che un file esista.

    python detect-ssh-profiles.py            # report leggibile
    python detect-ssh-profiles.py --json     # stessa informazione come JSON
    python detect-ssh-profiles.py --repo .   # aggiunge identità e remoto di quel repo

Esce 0 se trova almeno un alias verso GitHub, 1 se non ne trova nessuno: in quel
secondo caso non c'è niente da scegliere e il profilo va creato prima di proseguire.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys
from pathlib import Path

MAX_INCLUDE_DEPTH = 8
# Le sole direttive che servono a descrivere un profilo. Tutto il resto si ignora
# deliberatamente: questo non è un parser completo di ssh_config e non deve sembrarlo.
INTERESTING = {"hostname", "user", "identityfile", "identitiesonly", "port"}


def _split_tokens(line: str) -> list[str]:
    """Tokenizza una riga di ssh_config, rispettando le virgolette e l'uguale."""
    line = line.split("#", 1)[0].strip()
    if not line:
        return []
    if "=" in line and line.split("=", 1)[0].strip().isalpha():
        key, rest = line.split("=", 1)
        line = f"{key.strip()} {rest.strip()}"
    tokens, buf, quoted = [], "", False
    for ch in line:
        if ch == '"':
            quoted = not quoted
        elif ch.isspace() and not quoted:
            if buf:
                tokens.append(buf)
                buf = ""
        else:
            buf += ch
    if buf:
        tokens.append(buf)
    return tokens


def _expand(path: str, base: Path) -> str:
    path = os.path.expandvars(os.path.expanduser(path))
    if not os.path.isabs(path):
        path = str(base / path)
    return os.path.normpath(path)


def parse_config(path: Path, base: Path, depth: int = 0) -> tuple[list[dict], list[str]]:
    """Restituisce i blocchi Host del file e l'elenco dei file letti, Include compresi."""
    blocks: list[dict] = []
    read: list[str] = []
    if depth > MAX_INCLUDE_DEPTH or not path.is_file():
        return blocks, read
    read.append(str(path))
    current: dict | None = None
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return blocks, read
    for raw in lines:
        tokens = _split_tokens(raw)
        if not tokens:
            continue
        key, args = tokens[0].lower(), tokens[1:]
        if key == "include":
            # Un Include va risolto prima di concludere che un alias non esiste: è la
            # forma in cui molte macchine tengono i profili separati per committente.
            for pattern in args:
                for target in sorted(glob.glob(_expand(pattern, base))):
                    sub_blocks, sub_read = parse_config(Path(target), base, depth + 1)
                    blocks.extend(sub_blocks)
                    read.extend(sub_read)
            continue
        if key == "host":
            current = {"patterns": args, "source": str(path), "identityfile": []}
            blocks.append(current)
            continue
        if key == "match":
            # I blocchi Match sono condizionali: si registra che esistono e non si
            # attribuiscono a nessun alias, invece di fingere di averli capiti.
            current = None
            blocks.append({"patterns": [], "match": " ".join(args), "source": str(path), "identityfile": []})
            continue
        if current is None or key not in INTERESTING:
            continue
        if key == "identityfile":
            current["identityfile"].extend(_expand(a, base) for a in args)
        else:
            current[key] = " ".join(args)
    return blocks, read


def is_github(block: dict) -> bool:
    hostname = (block.get("hostname") or "").lower()
    if "github.com" in hostname:
        return True
    return any("github.com" in p.lower() for p in block.get("patterns", []))


def git(args: list[str], cwd: str | None = None) -> str:
    try:
        out = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True, timeout=10
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return out.stdout.strip() if out.returncode == 0 else ""


def collect(repo: str | None) -> dict:
    home = Path.home()
    ssh_dir = home / ".ssh"
    user_cfg = ssh_dir / "config"
    system_cfg = (
        Path(os.environ.get("ProgramData", r"C:\ProgramData")) / "ssh" / "ssh_config"
        if os.name == "nt"
        else Path("/etc/ssh/ssh_config")
    )

    blocks, read = parse_config(user_cfg, ssh_dir)
    sys_blocks, sys_read = parse_config(system_cfg, system_cfg.parent)
    blocks.extend(sys_blocks)
    read.extend(sys_read)

    profiles = []
    for b in blocks:
        if not is_github(b):
            continue
        keys = []
        for k in b["identityfile"]:
            keys.append({"path": k, "exists": os.path.isfile(k), "public": os.path.isfile(k + ".pub")})
        profiles.append(
            {
                "alias": b["patterns"][0] if b["patterns"] else "",
                "patterns": b["patterns"],
                "hostname": b.get("hostname", ""),
                "user": b.get("user", ""),
                "port": b.get("port", ""),
                "identities_only": b.get("identitiesonly", ""),
                "keys": keys,
                "source": b["source"],
            }
        )

    referenced = {k["path"] for p in profiles for k in p["keys"]}
    orphan_keys = []
    if ssh_dir.is_dir():
        for pub in sorted(ssh_dir.glob("*.pub")):
            priv = str(pub)[:-4]
            if os.path.isfile(priv) and priv not in referenced:
                orphan_keys.append(priv)

    info = {
        "ssh_config": str(user_cfg),
        "ssh_config_exists": user_cfg.is_file(),
        "files_read": read,
        "profiles": profiles,
        "match_blocks": [b["match"] for b in blocks if b.get("match")],
        "keys_without_alias": orphan_keys,
        "git": {
            "global_user_name": git(["config", "--global", "--get", "user.name"]),
            "global_user_email": git(["config", "--global", "--get", "user.email"]),
            "use_config_only": git(["config", "--global", "--get", "user.useConfigOnly"]),
        },
    }
    if repo:
        info["repo"] = {
            "path": os.path.abspath(repo),
            "is_repo": bool(git(["rev-parse", "--is-inside-work-tree"], repo)),
            "local_user_name": git(["config", "--local", "--get", "user.name"], repo),
            "local_user_email": git(["config", "--local", "--get", "user.email"], repo),
            "remote_origin": git(["config", "--local", "--get", "remote.origin.url"], repo),
            "core_ssh_command": git(["config", "--local", "--get", "core.sshCommand"], repo),
        }
    return info


def report(info: dict) -> None:
    print(f"Configurazione SSH letta: {info['ssh_config']}")
    if not info["ssh_config_exists"]:
        print("  (il file non esiste: nessun alias definito da questo utente)")
    for extra in info["files_read"][1:]:
        print(f"  incluso: {extra}")

    print()
    if not info["profiles"]:
        print("Nessun alias verso github.com trovato su questa macchina.")
    else:
        print(f"Alias verso github.com trovati: {len(info['profiles'])}")
        for p in info["profiles"]:
            print()
            print(f"  Host {' '.join(p['patterns'])}")
            print(f"    HostName        {p['hostname'] or '(non specificato)'}")
            if p["user"]:
                print(f"    User            {p['user']}")
            if p["port"]:
                print(f"    Port            {p['port']}")
            if p["identities_only"]:
                print(f"    IdentitiesOnly  {p['identities_only']}")
            if not p["keys"]:
                print("    IdentityFile    (nessuna: si userebbe la chiave di default)")
            for k in p["keys"]:
                stato = "presente" if k["exists"] else "MANCANTE"
                pub = "" if k["public"] else "  (senza .pub accanto)"
                print(f"    IdentityFile    {k['path']}  [{stato}]{pub}")
            print(f"    definito in     {p['source']}")

    if info["keys_without_alias"]:
        print()
        print("Chiavi presenti in ~/.ssh non riferite da nessun alias GitHub:")
        for k in info["keys_without_alias"]:
            print(f"  {k}")

    if info["match_blocks"]:
        print()
        print("Blocchi Match presenti (condizionali, non analizzati):")
        for m in info["match_blocks"]:
            print(f"  Match {m}")

    g = info["git"]
    print()
    print("Identità git globale:")
    print(f"  user.name          {g['global_user_name'] or '(non impostata)'}")
    print(f"  user.email         {g['global_user_email'] or '(non impostata)'}")
    print(f"  user.useConfigOnly {g['use_config_only'] or '(non impostata)'}")

    if "repo" in info:
        r = info["repo"]
        print()
        print(f"Repository {r['path']}:")
        if not r["is_repo"]:
            print("  (non è un repository git)")
        else:
            manca = "(non impostata: con user.useConfigOnly a true git rifiuta il commit)"
            print(f"  user.name        {r['local_user_name'] or manca}")
            print(f"  user.email       {r['local_user_email'] or '(non impostata)'}")
            print(f"  remote.origin    {r['remote_origin'] or '(nessun remoto)'}")
            print(f"  core.sshCommand  {r['core_ssh_command'] or '(non impostato)'}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true", help="stampa il rilevamento come JSON")
    ap.add_argument("--repo", metavar="PERCORSO", help="aggiunge identità e remoto del repository indicato")
    args = ap.parse_args()

    info = collect(args.repo)
    if args.json:
        print(json.dumps(info, indent=2, ensure_ascii=False))
    else:
        report(info)
    return 0 if info["profiles"] else 1


if __name__ == "__main__":
    sys.exit(main())
