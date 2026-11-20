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


def voci_catalogo(catalog):
    return sorted(set(re.findall(r"^\| `([a-z0-9][a-z0-9-]*)`", catalog, re.M)))


def gate(project, catalog):
    """Quante voci del catalogo nessuna tornata del gate ha mai visto né deciso.

    Dal 2026-11-20 (L-002 di un progetto istanziato). Un allineamento in blocco porta il catalogo
    nel progetto ma non esegue il gate, che è riservato al proprietario, e niente lo
    diceva alla sessione successiva: un progetto con novanta commit non aveva mai fatto
    una tornata. Il solo conto dei pacchetti senza decisione non basta, perché il gate
    propone soltanto i settori che riconosce e il resto resterebbe non censito per sempre:
    per questo ogni tornata registra in `tornate` l'elenco delle voci che ha visto, e il
    debito sono le voci comparse dopo l'ultima tornata e mai decise."""
    names = voci_catalogo(catalog)
    if not names:
        return None
    path = project / REGISTRO
    data = json.loads(path.read_text(encoding="utf-8-sig")) if path.is_file() else {}
    decided = set(data.get("pacchetti") or {})
    rounds = data.get("tornate") or []
    if not isinstance(rounds, list) or not all(isinstance(t, dict) and isinstance(t.get("catalogo"), list) for t in rounds):
        raise ValueError("tornate del gate non valide nel registro dei pacchetti")
    seen = set()
    for t in rounds:
        seen.update(t["catalogo"])
    new = [n for n in names if n not in seen and n not in decided]
    last = max((str(t.get("data", "")) for t in rounds), default="") or None
    return {"dovuto": bool(new), "nuovi": new, "ultima": last, "voci": len(names), "registro": path.is_file()}


def riga_gate(state):
    if state is None:
        return "Gate dei pacchetti non calcolabile: catalogo assente."
    if not state["dovuto"]:
        return "Gate in pari: tutte le %d voci del catalogo sono state viste dalla tornata del %s." % (state["voci"], state["ultima"])
    quando = "ultima tornata registrata il %s" % state["ultima"] if state["ultima"] else "nessuna tornata registrata"
    return ("Gate dovuto: %d voci del catalogo su %d non sono mai state viste dal gate né decise (%s). "
            "La tornata la avvia /riprendi, oppure /gate-pacchetti." % (len(state["nuovi"]), state["voci"], quando))


def registra_tornata(project, catalog, data):
    """Scrive nel registro la tornata appena conclusa con le voci del catalogo viste."""
    names = voci_catalogo(catalog)
    if not names:
        raise ValueError("catalogo assente: nessuna tornata da registrare")
    path = project / REGISTRO
    registry = json.loads(path.read_text(encoding="utf-8-sig")) if path.is_file() else {"versione": 1, "pacchetti": {}}
    registry.setdefault("tornate", []).append({"data": data, "catalogo": names})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    decisioni(project)
    return len(names)


def riepilogo(project, template):
    """Le righe che /riprendi mostra all'apertura: dove sta il progetto rispetto al template e
    che cosa usa del catalogo. Dal 2026-11-20: il proprietario voleva vederlo a ogni ripresa
    senza lanciare niente a mano, e prima lo sapeva solo chi apriva il registro."""
    righe = []
    marcatore = project / ".claude/allineamento-template.json"
    try:
        m = json.loads(marcatore.read_text(encoding="utf-8-sig"))
        righe.append("Template: allineato al commit %s del %s (%s)." % (
            str(m.get("template_commit", "?"))[:7], m.get("allineato_il", "?"), m.get("strumento", "?")))
    except (OSError, ValueError):
        righe.append("Template: nessun allineamento registrato in .claude/allineamento-template.json.")
    try:
        catalog = (template / ".claude/templates/PACKAGES.md").read_text(encoding="utf-8")
    except OSError:
        righe.append("Pacchetti: catalogo assente, niente da riepilogare.")
        return righe
    try:
        ricette_path = template / RICETTE
        recipes = json.loads(ricette_path.read_text(encoding="utf-8")) if ricette_path.is_file() else {}
        report = audit(project, recipes, catalog)
        choices = decisioni(project)
    except (OSError, ValueError, KeyError, TypeError) as error:
        righe.append("Pacchetti: registro non leggibile (%s)." % error)
        return righe
    adottati = ["%s (%s)" % (r["pacchetto"], r["istanza"]) for r in report if r["decisione"] == "adottato"]
    righe.append("Pacchetti adottati: " + (", ".join(adottati) if adottati else "nessuno registrato in " + REGISTRO) + ".")
    # Installati prima che il registro esistesse, o a mano: in uso ma senza decisione scritta.
    # La tornata del gate li mostra e chiede soltanto di registrarli.
    presenti = {r["pacchetto"] for r in report
                if r["decisione"] == "non-censito" and r["istanza"] in ("completo", "parziale")}
    # Le ricette coprono pochi pacchetti: il riconoscimento per skill e strumenti è quello di
    # cerca-pacchetto.py, riusato invece di riscriverlo.
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("cerca_pacchetto", Path(__file__).with_name("cerca-pacchetto.py"))
        cerca = importlib.util.module_from_spec(spec)
        # @dataclass cerca il modulo in sys.modules mentre lo si esegue
        sys.modules[spec.name] = cerca
        spec.loader.exec_module(cerca)
        for voce in cerca.leggi_catalogo(template / ".claude/templates/PACKAGES.md"):
            if voce.nome not in choices and cerca.adottato(voce, project, template / ".claude/templates"):
                presenti.add(voce.nome)
    except (OSError, ImportError, AttributeError) as error:
        righe.append("Riconoscimento dei pacchetti installati non riuscito: %s." % error)
    presenti = sorted(presenti)
    if presenti:
        righe.append("Pacchetti presenti ma mai registrati: " + ", ".join(presenti) + ".")
    for stato in ("rifiutato", "rimandato"):
        nomi = sorted(n for n, e in choices.items() if e.get("stato") == stato)
        if nomi:
            righe.append("Pacchetti %s: %s." % ("rifiutati" if stato == "rifiutato" else "rimandati", ", ".join(nomi)))
    try:
        righe.append(riga_gate(gate(project, catalog)))
    except (OSError, ValueError, TypeError) as error:
        righe.append("Gate non calcolabile: %s." % error)
    return righe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--progetto", type=Path, default=Path("."))
    parser.add_argument("--template", type=Path, default=Path("."))
    parser.add_argument("--json", type=Path)
    parser.add_argument("--gate", action="store_true",
                        help="dice soltanto se una tornata del gate è dovuta e su quante voci; esce sempre 0")
    parser.add_argument("--registra-tornata", action="store_true",
                        help="a fine tornata del gate: registra le voci del catalogo viste, con la data di sistema")
    parser.add_argument("--riepilogo", action="store_true",
                        help="per /riprendi: allineamento al template, pacchetti adottati, rifiutati e rimandati, stato del gate")
    args = parser.parse_args()
    if args.gate or args.registra_tornata:
        try:
            catalog = (args.template / ".claude/templates/PACKAGES.md").read_text(encoding="utf-8")
            if args.registra_tornata:
                import datetime
                n = registra_tornata(args.progetto.resolve(), catalog, datetime.date.today().isoformat())
                print("Tornata registrata in %s: %d voci del catalogo viste." % (REGISTRO, n))
            print(riga_gate(gate(args.progetto.resolve(), catalog)))
            return 0
        except (OSError, ValueError, KeyError, TypeError) as error:
            print("gate non calcolabile: " + str(error), file=sys.stderr)
            return 0 if args.gate else 2
    if args.riepilogo:
        # Esce sempre 0: è la vista che /riprendi mostra all'apertura, non un controllo.
        for riga in riepilogo(args.progetto.resolve(), args.template):
            print(riga)
        return 0
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
