"""Distingue i modelli distribuiti dai pacchetti adottati e dalle istanze complete."""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath


REGISTRO = ".claude/pacchetti.json"
RICETTE = ".claude/templates/pacchetti-istanza.json"


def relativo(value):
    path = PurePosixPath(value)
    if not value or not path.parts or path.is_absolute() or ".." in path.parts or "\\" in value or ":" in value or path.parts[0] in (".git", "_notes"):
        raise ValueError("percorso pubblico non valido nel contratto del pacchetto")
    return path.as_posix()


def decisioni(project):
    path = project / REGISTRO
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if data.get("versione") != 1 or not isinstance(data.get("pacchetti"), dict):
        raise ValueError("registro dei pacchetti non valido")
    for name, entry in data["pacchetti"].items():
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name) or entry.get("stato") not in ("adottato", "rifiutato", "rimandato"):
            raise ValueError("decisione di pacchetto non valida")
    return data["pacchetti"]


def piano(project, recipes, available):
    """Solo decisioni esplicite o dotazioni comuni autorizzate producono file da istanziare."""
    choices = decisioni(project)
    adopted = {name for name, item in choices.items() if item["stato"] == "adottato"}
    adopted.update(recipes.get("comuni", []))
    result = []
    for name in sorted(adopted):
        entry = choices.get(name, {})
        if entry.get("stato") in ("rifiutato", "rimandato"):
            continue
        files = entry.get("file", recipes.get("ricette", {}).get(name, {}).get("file", []))
        for item in files:
            source, target = relativo(item["origine"]), relativo(item["destinazione"])
            if not source.startswith(".claude/templates/" + name + "/"):
                raise ValueError("origine fuori dal pacchetto adottato: " + name)
            if target.startswith(".claude/templates/"):
                raise ValueError("una destinazione nel magazzino non è un'istanza")
            if not (project / target).resolve().is_relative_to(project.resolve()):
                raise ValueError("destinazione collegata fuori dal progetto")
            if source not in available:
                raise ValueError("origine assente dalla versione pubblicata: " + source)
            # La convenzione scripts/ già adottata si conserva, senza una seconda copia.
            if target.startswith("tools/") and (project / ("scripts/" + target[6:])).is_file() and not (project / target).exists():
                target = "scripts/" + target[6:]
            result.append((name, source, target))
    return result


def audit(project, recipes, catalog):
    choices = decisioni(project)
    names = sorted(set(re.findall(r"^\| `([a-z0-9][a-z0-9-]*)`", catalog, re.M)) | set(choices) | set(recipes.get("ricette", {})))
    result = []
    for name in names:
        entry = choices.get(name)
        state = entry["stato"] if entry else "non-censito"
        files = (entry or {}).get("file", recipes.get("ricette", {}).get(name, {}).get("file", []))
        required = [relativo(item["destinazione"]) for item in files]
        present = [p for p in required if (project / p).is_file() or (p.startswith("tools/") and (project / ("scripts/" + p[6:])).is_file())]
        material = "completo" if required and len(present) == len(required) else "parziale" if present else "non-istanziato" if required else "non-verificabile"
        result.append({"pacchetto": name, "decisione": state, "istanza": material, "presenti": present, "richiesti": required})
    # L'anonimizzazione richiede anche dati privati: non si leggono o esportano i valori.
    anon = next((item for item in result if item["pacchetto"] == "anonymization"), None)
    if anon:
        custom = choices.get("anonymization", {}).get("configurazione", {}).get("patterns", "_notes/.anonymization-patterns.json")
        config = (project / custom).resolve()
        if not config.is_relative_to(project.resolve()):
            raise ValueError("configurazione privata fuori dalla radice: usare un riferimento locale verificabile")
        ignored = subprocess.run(["git", "-C", str(project), "check-ignore", "-q", str(config)], capture_output=True).returncode == 0
        configured = False
        if config.is_file() and ignored:
            values = json.loads(config.read_text(encoding="utf-8-sig"))
            configured = not values.get("_da_compilare", False) and all(k in values for k in ("reti_documentali_ammesse", "ip_ammessi", "prefissi_reali", "mac_ammessi_prefissi", "email_ammesse", "nomi_propri"))
        anon["configurazione"] = "schema-presente-da-collaudare" if configured else "da-configurare"
        anon["percorso_configurazione"] = custom
        closers = [project / "tools/chiudi-sessione.ps1", project / "tools/chiudi-sessione.sh"]
        anon["richiamo"] = "presente-da-collaudare" if any(p.is_file() and "Test-Anonymization.py" in p.read_text(encoding="utf-8-sig") for p in closers) else "non-rilevato"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--progetto", type=Path, default=Path("."))
    parser.add_argument("--template", type=Path, default=Path("."))
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    try:
        recipes = json.loads((args.template / RICETTE).read_text(encoding="utf-8"))
        report = audit(args.progetto.resolve(), recipes, (args.template / ".claude/templates/PACKAGES.md").read_text(encoding="utf-8"))
        if args.json:
            args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        for item in report:
            if item["decisione"] == "adottato" or item["pacchetto"] == "anonymization":
                print(json.dumps(item, ensure_ascii=False))
        print("Pacchetti senza decisione censita: " + str(sum(r["decisione"] == "non-censito" for r in report)))
        return 1 if any(r["decisione"] == "adottato" and (r["istanza"] != "completo" or r.get("configurazione") == "da-configurare" or r.get("richiamo") == "non-rilevato") for r in report) else 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("pacchetti non verificabili: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
