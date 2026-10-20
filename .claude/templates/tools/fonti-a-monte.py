#!/usr/bin/env python3
"""I repository altrui da cui il sistema prende o descrive qualcosa, e quando cambiano.

Perché esiste. Alcuni pacchetti del template descrivono il contenuto di un repository
GitHub di qualcun altro: quali skill contiene, quante sono, come si installa. Il
2026-10-20 la scheda di `matt-pocock-skills` consigliava ancora `resolving-merge-conflicts`,
che l'autore aveva tolto il giorno prima, e la valutazione completa fatta subito dopo ha
trovato altre tre schede invecchiate in silenzio: K-Dense era passata da 166 a 177 skill
e non vendorava più gli strumenti di Anthropic, wshobson/agents da 194 a 202 agent, e la
guida di Cranot non si aggiornava più da sola da febbraio. Una scheda vecchia ha lo stesso
aspetto di una aggiornata, quindi il controllo non può affidarsi al ricordo.

Il registro ha due elenchi. `sorvegliati` sono i repository di cui una scheda descrive il
contenuto, con la cartella interna che conta, oppure le release quando la scheda descrive
quelle, e l'ultimo commit o tag confrontato con la scheda. `citati` sono quelli soltanto
nominati, con il motivo per cui non si sorvegliano: non diventano falsi quando cambiano.

Il censimento rende il registro completo da sé. Percorre i file e raccoglie ogni
repository GitHub che vi compare, in un URL o in un comando d'installazione; quello che
non sta in nessuno dei due elenchi entra fra i sorvegliati come mai verificato, perché
l'errore sicuro è un avviso in più e non una scheda che invecchia senza che nessuno lo
sappia. Chi lo esamina poi lo segna come verificato o lo sposta fra i citati con un motivo.
Un sorvegliato che non compare più in nessun file si toglie.

Il template e i progetti usano lo stesso strumento, che riconosce da sé dove si trova.

Nel template il registro è `.claude/templates/fonti-a-monte.json` e il censimento percorre
i pacchetti e il catalogo. `controlla` gira all'apertura di ogni sessione; i chiudi del
template lanciano `censisci --check`, che ferma il commit se un repository nuovo non è
stato censito, così che registro e schede entrino nello stesso commit.

In un progetto istanziato il registro è `.claude/fonti-a-monte.json`, del progetto. Le
schede dei pacchetti le corregge il template e arrivano con l'allineamento; ciò che può
invecchiare nel progetto è quanto il progetto ha preso da un repository a monte, cioè skill,
agenti e comandi installati. Il censimento percorre quindi i soli posti dove quel materiale
si installa, `.claude/skills`, `.claude/agents`, `.claude/commands`, `.claude/agent-catalog`
e `.agents`, escluse le skill di sistema che arrivano dal template. Nel progetto il
controllo avvisa e non ferma mai il commit.

    python .claude/templates/tools/fonti-a-monte.py controlla      # censisce, poi chiede a GitHub
    python .claude/templates/tools/fonti-a-monte.py censisci [--check]
    python .claude/templates/tools/fonti-a-monte.py segna <owner/repo>
    python .claude/templates/tools/fonti-a-monte.py cita <owner/repo> --motivo "..."
    python .claude/templates/tools/fonti-a-monte.py sorveglia <owner/repo> --cartella skills [--release]
    python .claude/templates/tools/fonti-a-monte.py --autotest

Le richieste vanno all'API pubblica di GitHub. Il token si prende da `GH_TOKEN`, da
`GITHUB_TOKEN` o da `gh auth token`; senza, GitHub ne concede sessanta l'ora, e al limite
lo strumento si ferma dicendolo invece di riportare repository invariati che non ha letto.
`controlla` esce con 0 anche quando trova cambiamenti o non raggiunge la rete, salvo
`--rigoroso`.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REGISTRO_TEMPLATE = Path(".claude") / "templates" / "fonti-a-monte.json"
REGISTRO_PROGETTO = Path(".claude") / "fonti-a-monte.json"
MARCATORE_TEMPLATE = Path(".claude") / "PROMPT-nuovo-progetto.md"
DEFINIZIONE_SISTEMA = Path(".claude") / "templates" / "tools" / "allinea-dal-template.py"
PAGINA = 30
ESTENSIONI = {".md", ".json", ".yaml", ".yml", ".txt"}
FUORI = {"_notes", "fixtures", "__pycache__", ".git", "node_modules"}
POSTI_PROGETTO = [".claude/skills", ".claude/agents", ".claude/commands", ".claude/agent-catalog", ".agents"]
# Primi segmenti di github.com che non sono un utente o un'organizzazione.
RISERVATI = {"en", "orgs", "settings", "features", "topics", "marketplace", "apps", "sponsors", "login",
             "about", "pricing", "site", "collections", "explore", "notifications", "new", "search",
             "enterprise", "security", "customer-stories", "readme", "trending", "events", "github"}
NOME = r"[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9._-]+"
SCHEMI = [
    re.compile(r"(?<![\w.])(?:https?://)?(?:www\.)?github\.com/(" + NOME + ")"),
    re.compile(r"raw\.githubusercontent\.com/(" + NOME + ")"),
    re.compile(r"(?:gh skill install|gh repo clone|npx skills(?:@[\w.]+)? add|marketplace add)\s+(" + NOME + ")"),
]
# Un nome fra apici inversi, come `ryoppippi/ccusage`, è un repository solo se non è un percorso:
# il primo segmento non è una cartella del repository e il secondo non finisce con un'estensione.
APICI = re.compile(r"`(" + NOME + ")`")
ESTENSIONE = re.compile(r"\.[A-Za-z0-9]{1,5}$")


class LimiteRaggiunto(Exception):
    pass


class RepoAssente(Exception):
    pass


# --------------------------------------------------------------------------- dove siamo

def nel_template(radice: Path) -> bool:
    # Il prompt di inizializzazione da solo non basta: alcuni progetti ne hanno una copia, trovato il
    # 2026-10-20 su quattro progetti locali. Il catalogo dei pacchetti nel README c'è solo nel template.
    readme = radice / "README.md"
    return (radice / MARCATORE_TEMPLATE).is_file() and readme.is_file() and \
        "<!-- sync-readme:packages:start -->" in readme.read_text(encoding="utf-8", errors="replace")


def percorso_registro(radice: Path) -> Path:
    return radice / (REGISTRO_TEMPLATE if nel_template(radice) else REGISTRO_PROGETTO)


def leggi_registro(radice: Path) -> dict:
    f = percorso_registro(radice)
    if not f.exists():
        return {"sorvegliati": [], "citati": []}
    dati = json.loads(f.read_text(encoding="utf-8"))
    if isinstance(dati, list):
        dati = {"sorvegliati": dati, "citati": []}
    dati.setdefault("sorvegliati", [])
    dati.setdefault("citati", [])
    for v in dati["sorvegliati"]:
        for campo in ("repo", "pacchetto", "scheda"):
            if not v.get(campo):
                raise ValueError("voce senza %s fra i sorvegliati: %r" % (campo, v))
    for v in dati["citati"]:
        if not v.get("repo") or not v.get("motivo"):
            raise ValueError("voce citata senza repo o senza motivo: %r" % (v,))
    return dati


def scrivi_registro(radice: Path, dati: dict) -> None:
    f = percorso_registro(radice)
    f.parent.mkdir(parents=True, exist_ok=True)
    dati["sorvegliati"].sort(key=lambda v: (v["repo"].lower(), v.get("cartella", "")))
    dati["citati"].sort(key=lambda v: v["repo"].lower())
    f.write_text(json.dumps(dati, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def chiave(repo: str) -> str:
    return repo.lower()


# --------------------------------------------------------------------------- censimento

def pulisci(nome: str):
    owner, _, repo = nome.partition("/")
    repo = re.sub(r"\.git$", "", repo).rstrip(".")
    if owner.lower() in RISERVATI or not repo or repo.startswith("."):
        return None
    return owner + "/" + repo


def skill_di_sistema(radice: Path) -> set:
    f = radice / DEFINIZIONE_SISTEMA
    if not f.exists():
        return set()
    m = re.search(r"SKILL_SISTEMA\s*=\s*\[(.*?)\]", f.read_text(encoding="utf-8"), re.S)
    return set(re.findall(r'"([^"]+)"', m.group(1))) if m else set()


def spediti_dal_template(radice: Path) -> dict:
    """Le skill, gli agenti e i comandi che il template porta nei progetti, letti nel template.

    Un progetto non vede la cartella `.claude/skills` del template, quindi non saprebbe che una
    sua skill, come `pipeline-app`, arriva dal template e non da un repository a monte: il
    template scrive l'elenco nel registro, che l'allineamento porta nei progetti.
    """
    nomi = {"skills": set(), "agents": set(), "commands": set()}
    for base in (radice / ".claude", radice / ".claude" / "templates"):
        for tipo in nomi:
            for d in base.rglob(tipo):
                if not d.is_dir() or FUORI.intersection(d.relative_to(radice).parts):
                    continue
                for x in d.iterdir():
                    if tipo == "skills" and x.is_dir():
                        nomi[tipo].add(x.name)
                    elif tipo != "skills" and x.suffix == ".md":
                        nomi[tipo].add(x.stem)
    return {k: sorted(v) for k, v in nomi.items()}


def del_template(rel: tuple, spediti: dict) -> bool:
    """Se un file del progetto appartiene a una skill, a un agente o a un comando del template."""
    if len(rel) > 2 and rel[0] in (".claude", ".agents") and rel[1] == "skills":
        return rel[2] in spediti.get("skills", ())
    if len(rel) > 2 and rel[0] == ".claude" and rel[1] in ("agents", "commands"):
        return Path(rel[2]).stem in spediti.get(rel[1], ())
    return False


def file_da_censire(radice: Path) -> list:
    if nel_template(radice):
        basi = [radice / ".claude" / p for p in ("templates", "skills", "rules", "norme")]
        basi += [radice / ".claude" / "PROJECT-SYSTEM.md", radice / "README.md"]
        spediti = {}
    else:
        basi = [radice / p for p in POSTI_PROGETTO]
        spediti = leggi_registro_template(radice).get("spediti", {})
        spediti = dict(spediti, skills=sorted(set(spediti.get("skills", [])) | skill_di_sistema(radice)))
    trovati = []
    for base in basi:
        for f in ([base] if base.is_file() else sorted(base.rglob("*")) if base.is_dir() else []):
            rel = f.relative_to(radice).parts
            if not f.is_file() or f.suffix.lower() not in ESTENSIONI or FUORI.intersection(rel):
                continue
            if f.name == "fonti-a-monte.json" or del_template(rel, spediti):
                continue
            trovati.append(f)
    return trovati


def leggi_registro_template(radice: Path) -> dict:
    f = radice / REGISTRO_TEMPLATE
    if not f.exists():
        return {}
    dati = json.loads(f.read_text(encoding="utf-8"))
    return dati if isinstance(dati, dict) else {}


def pacchetto_di(radice: Path, f: Path) -> str:
    rel = f.relative_to(radice).parts
    if nel_template(radice):
        if rel[:2] == (".claude", "templates"):
            return rel[2] if len(rel) > 3 else "catalogo"
        if rel[:2] == (".claude", "skills") and len(rel) > 3:
            return "skill " + rel[2]
        return "sistema"
    return "/".join(rel[1:3]) if len(rel) > 2 else rel[-1]


def cartelle_locali(radice: Path) -> set:
    nomi = set()
    for _, sotto, _ in os.walk(radice):
        sotto[:] = [x for x in sotto if x != ".git"]
        nomi.update(x.lower() for x in sotto)
    return nomi


def tra_apici(testo: str, locali: set) -> list:
    nomi = []
    for m in APICI.finditer(testo):
        owner, _, repo = m.group(1).partition("/")
        if owner.lower() in locali or ESTENSIONE.search(repo):
            continue
        nomi.append(pulisci(m.group(1)))
    return nomi


def censimento(radice: Path, dati: dict) -> dict:
    """Ogni repository che compare nei file, con il primo file in cui compare."""
    noti = {chiave(v["repo"]): v["repo"] for v in dati["sorvegliati"] + dati["citati"]}
    # Fra apici inversi solo nel template, dove il catalogo nomina così i repository. In un progetto
    # la stessa forma è quasi sempre codice: `testing-library/no-node-access` è una regola di lint
    # (misurato il 2026-10-20 sui progetti locali).
    locali = cartelle_locali(radice) if nel_template(radice) else None
    trovati = {}
    for f in file_da_censire(radice):
        testo = f.read_text(encoding="utf-8", errors="replace")
        nomi = [pulisci(m.group(1)) for s in SCHEMI for m in s.finditer(testo)]
        if locali is not None:
            nomi += tra_apici(testo, locali)
        # Un repository già noto conta anche scritto senza URL, come `mattpocock/skills`.
        basso = testo.lower()
        nomi += [r for k, r in noti.items() if k in basso]
        for n in nomi:
            if n and chiave(n) not in trovati:
                trovati[chiave(n)] = (n, f)
    return trovati


def censisci(radice: Path, scrivi: bool) -> tuple:
    dati = leggi_registro(radice)
    trovati = censimento(radice, dati)
    classificati = {chiave(v["repo"]) for v in dati["sorvegliati"] + dati["citati"]}
    nuovi = [(n, f) for k, (n, f) in sorted(trovati.items()) if k not in classificati]
    orfani = [v for v in dati["sorvegliati"] if chiave(v["repo"]) not in trovati]
    # Anche un citato che non compare più si toglie, in silenzio: non c'è niente da guardare.
    citati = [v for v in dati["citati"] if chiave(v["repo"]) in trovati]
    spediti = spediti_dal_template(radice) if nel_template(radice) else dati.get("spediti")
    elenco_vecchio = spediti != dati.get("spediti")
    if scrivi and (nuovi or orfani or elenco_vecchio or len(citati) != len(dati["citati"])):
        dati["citati"] = citati
        for n, f in nuovi:
            dati["sorvegliati"].append({"repo": n, "cartella": "", "pacchetto": pacchetto_di(radice, f),
                                        "scheda": f.relative_to(radice).as_posix()})
        dati["sorvegliati"] = [v for v in dati["sorvegliati"] if v not in orfani]
        if spediti is not None:
            dati["spediti"] = spediti
        scrivi_registro(radice, dati)
    return nuovi, orfani, elenco_vecchio


def cmd_censisci(radice: Path, check: bool) -> int:
    nuovi, orfani, elenco_vecchio = censisci(radice, scrivi=not check)
    for n, f in nuovi:
        print("   +  %s, citato in %s: %s" % (n, f.relative_to(radice).as_posix(),
              "da censire" if check else "aggiunto ai sorvegliati, mai verificato"))
    for v in orfani:
        print("   -  %s: non compare più in nessun file, %s" % (v["repo"], "da togliere" if check else "tolto"))
    if elenco_vecchio:
        print("   *  elenco delle skill, degli agenti e dei comandi del template: %s" % ("da aggiornare" if check else "aggiornato"))
    if check and (nuovi or orfani or elenco_vecchio):
        print("censimento incompleto: lancia fonti-a-monte.py censisci, poi segna o cita ciascun nuovo")
        return 1 if nel_template(radice) else 0
    print("censimento: %d nuovi, %d tolti" % (len(nuovi), len(orfani)))
    return 0


# --------------------------------------------------------------------------- GitHub

_TOKEN = None


def token() -> str:
    global _TOKEN
    if _TOKEN is None:
        _TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
        if not _TOKEN:
            try:
                r = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=10)
                _TOKEN = r.stdout.strip() if r.returncode == 0 else ""
            except (OSError, subprocess.SubprocessError):
                _TOKEN = ""
    return _TOKEN


def api(percorso: str):
    req = urllib.request.Request("https://api.github.com/" + percorso,
                                 headers={"Accept": "application/vnd.github+json", "User-Agent": "fonti-a-monte"})
    if token():
        req.add_header("Authorization", "Bearer " + token())
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code in (403, 429) and e.headers.get("X-RateLimit-Remaining") == "0":
            raise LimiteRaggiunto("limite orario dell'API di GitHub raggiunto; imposta GH_TOKEN o accedi con gh")
        if e.code == 404:
            raise RepoAssente("GitHub risponde 404")
        raise


def leggi_github(voce: dict) -> list:
    """Le versioni più recenti, dalla più nuova: [(identificativo, data)]."""
    repo = voce["repo"]
    if voce.get("tipo") == "release":
        try:
            r = api("repos/%s/releases/latest" % repo)
        except RepoAssente:
            api("repos/%s" % repo)
            return []
        return [(r["tag_name"], (r.get("published_at") or "")[:10])]
    q = {"per_page": str(PAGINA)}
    if voce.get("cartella"):
        q["path"] = voce["cartella"]
    dati = api("repos/%s/commits?%s" % (repo, urllib.parse.urlencode(q)))
    return [(c["sha"], c["commit"]["committer"]["date"][:10]) for c in dati]


def esamina(voce: dict, leggi=leggi_github) -> dict:
    try:
        versioni = leggi(voce)
    except LimiteRaggiunto:
        raise
    except RepoAssente as e:
        return {"stato": "sparito", "errore": str(e)}
    except (urllib.error.URLError, OSError, ValueError, KeyError) as e:
        return {"stato": "non-raggiunta", "errore": str(e)}
    if not versioni:
        cosa = "nessuna release" if voce.get("tipo") == "release" else "nessun commit per quella cartella: spostata o rinominata?"
        return {"stato": "non-raggiunta", "errore": cosa}
    ultimo, data = versioni[0]
    noto = voce.get("verificato", "")
    if not noto:
        return {"stato": "mai-verificata", "ultimo": ultimo, "data": data}
    if ultimo == noto:
        return {"stato": "invariata"}
    ids = [i for i, _ in versioni]
    return {"stato": "cambiata", "ultimo": ultimo, "data": data, "nuovi": ids.index(noto) if noto in ids else None}


def breve(identificativo: str) -> str:
    return identificativo[:12] if re.fullmatch(r"[0-9a-f]{40}", identificativo) else identificativo


def cmd_controlla(radice: Path, rigoroso: bool = False, leggi=leggi_github) -> int:
    nuovi, orfani, _ = censisci(radice, scrivi=True)
    for n, f in nuovi:
        print("   +  %s, citato in %s: aggiunto ai sorvegliati" % (n, f.relative_to(radice).as_posix()))
    for v in orfani:
        print("   -  %s: non compare più in nessun file, tolto" % v["repo"])
    voci = leggi_registro(radice)["sorvegliati"]
    cambiate = 0
    saltate = 0
    for i, v in enumerate(voci):
        dove = v["repo"] + ("/" + v["cartella"] if v.get("cartella") else "") + (" (release)" if v.get("tipo") == "release" else "")
        try:
            e = esamina(v, leggi)
        except LimiteRaggiunto as x:
            saltate = len(voci) - i
            print("   ?  %s; %d repository non controllati" % (x, saltate))
            break
        if e["stato"] == "invariata":
            continue
        if e["stato"] == "non-raggiunta":
            print("   ?  %s (%s): non raggiunto, %s" % (v["pacchetto"], dove, e["errore"]))
            continue
        cambiate += 1
        if e["stato"] == "sparito":
            print("   !  %s (%s): il repository non esiste più o è diventato privato" % (v["pacchetto"], dove))
        elif e["stato"] == "mai-verificata":
            print("   !  %s (%s): mai confrontato con la scheda; ultima versione %s del %s" % (v["pacchetto"], dove, breve(e["ultimo"]), e["data"]))
        else:
            if v.get("tipo") == "release":
                quanti = "nuova release %s" % e["ultimo"]
            else:
                quanti = "%d commit" % e["nuovi"] if e["nuovi"] is not None else "più di %d commit" % (PAGINA - 1)
            print("   !  %s (%s): %s dal %s, ultimo del %s" % (v["pacchetto"], dove, quanti, v.get("data", "?"), e["data"]))
            print("      differenza: https://github.com/%s/compare/%s...%s" % (v["repo"], breve(v["verificato"]), breve(e["ultimo"])))
        print("      scheda da rileggere: %s; poi segna %s, oppure cita %s --motivo" % (v["scheda"], v["repo"], v["repo"]))
    print("fonti a monte: %d da guardare su %d sorvegliate%s" % (cambiate, len(voci), ", %d non controllate" % saltate if saltate else ""))
    return 1 if (rigoroso and cambiate) else 0


# --------------------------------------------------------------------------- registro a mano

def trova(dati: dict, repo: str, elenco: str = "sorvegliati") -> list:
    return [v for v in dati[elenco] if chiave(v["repo"]) == chiave(repo)]


def cmd_segna(radice: Path, repo: str, leggi=leggi_github, oggi: str = "") -> str:
    dati = leggi_registro(radice)
    voci = trova(dati, repo)
    if not voci:
        raise SystemExit("repository non sorvegliato: %s" % repo)
    for v in voci:
        versioni = leggi(v)
        if not versioni:
            raise SystemExit("nessuna versione leggibile per %s: non segno niente" % repo)
        v["verificato"] = versioni[0][0]
        v["data"] = oggi or dt.date.today().isoformat()
    scrivi_registro(radice, dati)
    return voci[0]["verificato"]


def cmd_cita(radice: Path, repo: str, motivo: str) -> None:
    if not motivo.strip():
        raise SystemExit("un repository citato porta il motivo per cui non si sorveglia")
    dati = leggi_registro(radice)
    dati["sorvegliati"] = [v for v in dati["sorvegliati"] if chiave(v["repo"]) != chiave(repo)]
    dati["citati"] = [v for v in dati["citati"] if chiave(v["repo"]) != chiave(repo)] + [{"repo": repo, "motivo": motivo.strip()}]
    scrivi_registro(radice, dati)


def cmd_sorveglia(radice: Path, repo: str, cartella: str, release: bool, pacchetto: str, scheda: str) -> None:
    dati = leggi_registro(radice)
    vecchie = trova(dati, repo)
    v = vecchie[0] if vecchie else {"repo": repo}
    if not (pacchetto or v.get("pacchetto")) or not (scheda or v.get("scheda")):
        raise SystemExit("un repository nuovo vuole --pacchetto e --scheda")
    v.update({"cartella": cartella, "pacchetto": pacchetto or v["pacchetto"], "scheda": scheda or v["scheda"]})
    if release:
        v["tipo"] = "release"
    else:
        v.pop("tipo", None)
    v.pop("verificato", None)
    v.pop("data", None)
    dati["citati"] = [x for x in dati["citati"] if chiave(x["repo"]) != chiave(repo)]
    dati["sorvegliati"] = [x for x in dati["sorvegliati"] if chiave(x["repo"]) != chiave(repo)] + [v]
    scrivi_registro(radice, dati)


# --------------------------------------------------------------------------- prove

def autotest() -> int:
    import contextlib
    import io

    casi = rossi = 0

    def caso(nome: str, ok: bool) -> None:
        nonlocal casi, rossi
        casi += 1
        rossi += 0 if ok else 1
        print(("ok   " if ok else "ROSSO ") + nome)

    storia = {"a/uno": [("c3", "2026-10-20"), ("c2", "2026-10-19"), ("c1", "2026-10-18")],
              "b/due": [("x1", "2026-10-01")], "r/rel": [("v2", "2026-10-20")]}
    limite = {"attivo": False}

    def finta(voce):
        repo = voce["repo"]
        if limite["attivo"]:
            raise LimiteRaggiunto("limite orario raggiunto")
        if repo == "rete/assente":
            raise urllib.error.URLError("rete assente")
        if repo == "via/sparito":
            raise RepoAssente("404")
        return storia.get(repo, [])

    def esegui(radice, rigoroso=False):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cmd_controlla(radice, rigoroso, finta)
        return rc, buf.getvalue()

    def zitto(f, *a):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = f(*a)
        return rc, buf.getvalue()

    with tempfile.TemporaryDirectory() as d:
        r = Path(d) / "template"
        (r / MARCATORE_TEMPLATE).parent.mkdir(parents=True)
        (r / MARCATORE_TEMPLATE).write_text("x", encoding="utf-8")
        (r / "README.md").write_text("<!-- sync-readme:packages:start -->\n", encoding="utf-8")
        (r / ".claude" / "skills" / "pipeline-app").mkdir(parents=True)
        (r / ".claude" / "skills" / "pipeline-app" / "RIFERIMENTO.md").write_text("https://github.com/lint/staged\n", encoding="utf-8")
        pa = r / ".claude" / "templates" / "pa"
        pa.mkdir(parents=True)
        (pa / "README.md").write_text("Fonte https://github.com/a/uno e `b/due`, guida https://github.com/en/get-started.\n", encoding="utf-8")
        (r / ".claude" / "templates" / "PACKAGES.md").write_text(
            "| x | `gh skill install r/rel nome` | `apici/repo` | `templates/pa` | `linux/blk_snap.h` |\n", encoding="utf-8")
        (r / ".claude" / "templates" / "_notes").mkdir()
        (r / ".claude" / "templates" / "_notes" / "n.md").write_text("https://github.com/note/ignorate\n", encoding="utf-8")
        caso("si riconosce il template dal suo marcatore", nel_template(r) and percorso_registro(r) == r / REGISTRO_TEMPLATE)

        nuovi = censisci(r, scrivi=False)[0]
        nomi = [n for n, _ in nuovi]
        caso("il censimento trova URL, comandi d'installazione e nomi fra apici, anche nelle skill del template",
             nomi == ["a/uno", "apici/repo", "b/due", "lint/staged", "r/rel"])
        caso("un percorso locale o un file fra apici non è un repository", not any(n.startswith(("templates/", "linux/")) for n in nomi))
        caso("i percorsi riservati di github.com e le note restano fuori", not any(n.startswith(("en/", "note/")) for n in nomi))
        caso("censisci --check ferma il commit del template se manca un repository", zitto(cmd_censisci, r, True)[0] == 1)
        zitto(cmd_censisci, r, False)
        reg = leggi_registro(r)
        uno = trova(reg, "a/uno")[0]
        caso("un repository nuovo entra da sé fra i sorvegliati, con pacchetto e scheda", (uno["pacchetto"], uno["scheda"]) == ("pa", ".claude/templates/pa/README.md"))
        caso("dal catalogo il pacchetto si chiama catalogo", trova(reg, "r/rel")[0]["pacchetto"] == "catalogo")
        caso("dopo il censimento il controllo del commit passa", zitto(cmd_censisci, r, True)[0] == 0)
        caso("il registro elenca le skill che il template porta nei progetti", "pipeline-app" in leggi_registro(r)["spediti"]["skills"])
        (r / ".claude" / "skills" / "nuova-skill").mkdir()
        caso("una skill nuova del template rende vecchio l'elenco e ferma il commit", zitto(cmd_censisci, r, True)[0] == 1)
        zitto(cmd_censisci, r, False)
        rc, out = esegui(r)
        caso("un repository appena censito si segnala come mai confrontato", "pa (a/uno): mai confrontato" in out and rc == 0)

        cmd_sorveglia(r, "a/uno", "skills", False, "", "")
        cmd_segna(r, "a/uno", finta, "2026-10-18")
        reg = leggi_registro(r)
        trova(reg, "a/uno")[0]["verificato"] = "c1"
        scrivi_registro(r, reg)
        cmd_sorveglia(r, "r/rel", "", True, "", "")
        storia["r/rel"] = [("v1", "2026-10-01")]
        cmd_segna(r, "r/rel", finta, "2026-10-01")
        storia["r/rel"] = [("v2", "2026-10-20")]
        cmd_cita(r, "b/due", "soltanto citato in un elenco")
        rc, out = esegui(r)
        caso("un repository cambiato si segnala con il numero di commit", "pa (a/uno/skills): 2 commit" in out)
        caso("la differenza si legge dal commit verificato all'ultimo", "compare/c1...c3" in out)
        caso("una release nuova si segnala con il suo tag", "nuova release v2" in out)
        caso("un repository citato non si interroga", "b/due" not in out)
        caso("il controllo avvisa ma non blocca", rc == 0)
        caso("con --rigoroso un cambiamento blocca", esegui(r, True)[0] == 1)
        storia["a/uno"] = [("c%d" % i, "2026-10-20") for i in range(40, 1, -1)]
        caso("oltre una pagina di commit si dice che sono di più", "più di 29 commit" in esegui(r)[1])
        cmd_segna(r, "a/uno", finta, "2026-10-21")
        cmd_segna(r, "r/rel", finta, "2026-10-21")
        v = trova(leggi_registro(r), "a/uno")[0]
        caso("segna registra l'ultima versione e la data", (v["verificato"], v["data"]) == ("c40", "2026-10-21"))
        caso("dopo segna tutto tace", "0 da guardare" in esegui(r)[1])

        (pa / "README.md").write_text("Ora cita https://github.com/via/sparito e https://github.com/rete/assente e `b/due`.\n", encoding="utf-8")
        rc, out = esegui(r)
        caso("un repository tolto dalle schede esce dal registro", "a/uno: non compare più" in out and not trova(leggi_registro(r), "a/uno"))
        caso("i citati che compaiono ancora restano citati", trova(leggi_registro(r), "b/due", "citati") != [])
        for n in ("via/sparito", "rete/assente"):
            reg = leggi_registro(r)
            trova(reg, n)[0]["verificato"] = "z"
            scrivi_registro(r, reg)
        rc, out = esegui(r)
        caso("un repository sparito si segnala come da guardare", "(via/sparito): il repository non esiste più" in out)
        caso("una rete assente si dice e non blocca", "(rete/assente): non raggiunto" in out and rc == 0)
        limite["attivo"] = True
        out = esegui(r)[1]
        caso("al limite dell'API si dice quanti non sono stati controllati", "non controllati" in out and "0 da guardare" in out)
        limite["attivo"] = False

        prj = Path(d) / "progetto"
        (prj / ".claude" / "templates" / "tools").mkdir(parents=True)
        (prj / DEFINIZIONE_SISTEMA).write_text('SKILL_SISTEMA = [\n    "riprendi", "retrospettiva",\n]\n', encoding="utf-8")
        (prj / ".claude" / "templates" / "pa").mkdir()
        (prj / ".claude" / "templates" / "pa" / "README.md").write_text("https://github.com/a/uno\n", encoding="utf-8")
        for nome, testo in (("grill-me", "source: https://github.com/mattpocock/skills\n"),
                            ("retrospettiva", "adattata da https://github.com/mattpocock/skills\n"),
                            ("prove", "regola `testing-library/no-node-access` del lint\n")):
            (prj / ".claude" / "skills" / nome).mkdir(parents=True)
            (prj / ".claude" / "skills" / nome / "SKILL.md").write_text(testo, encoding="utf-8")
        (prj / "docs").mkdir()
        (prj / "docs" / "fonti.md").write_text("https://github.com/documentazione/qualunque\n", encoding="utf-8")
        caso("in un progetto il registro è del progetto", not nel_template(prj) and percorso_registro(prj) == prj / REGISTRO_PROGETTO)
        (prj / MARCATORE_TEMPLATE).write_text("copia del prompt d'inizializzazione", encoding="utf-8")
        (prj / ".claude" / "templates" / "fonti-a-monte.json").write_text((r / REGISTRO_TEMPLATE).read_text(encoding="utf-8"), encoding="utf-8")
        (prj / ".claude" / "skills" / "pipeline-app").mkdir(parents=True)
        (prj / ".claude" / "skills" / "pipeline-app" / "RIFERIMENTO.md").write_text("https://github.com/lint/staged\n", encoding="utf-8")
        nuovi = censisci(prj, scrivi=False)[0]
        caso("in un progetto si censisce ciò che il progetto ha installato", [n for n, _ in nuovi] == ["mattpocock/skills"])
        caso("un progetto con una copia del prompt d'inizializzazione resta un progetto", not nel_template(prj))
        caso("le skill di sistema e le schede del template non si censiscono nel progetto",
             str(nuovi[0][1]).replace("\\", "/").endswith(".claude/skills/grill-me/SKILL.md"))
        caso("nel progetto il controllo del commit avvisa e non ferma", zitto(cmd_censisci, prj, True)[0] == 0)
        zitto(cmd_censisci, prj, False)
        caso("il progetto aggiunge da sé il repository al proprio registro", trova(leggi_registro(prj), "mattpocock/skills")[0]["pacchetto"] == "skills/grill-me")

        (r / REGISTRO_TEMPLATE).write_text(json.dumps({"sorvegliati": [{"repo": "a/uno", "scheda": "x"}]}), encoding="utf-8")
        try:
            leggi_registro(r)
            ok = False
        except ValueError:
            ok = True
        caso("una voce senza pacchetto è un errore del registro", ok)
        (r / REGISTRO_TEMPLATE).write_text(json.dumps([{"repo": "a/uno", "pacchetto": "pa", "scheda": "x"}]), encoding="utf-8")
        caso("il registro nella forma di prima, un elenco, si legge ancora", trova(leggi_registro(r), "a/uno") != [])
    print("\n%d casi superati su %d" % (casi - rossi, casi))
    return 1 if rossi else 0


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    p = argparse.ArgumentParser(description="I repository altrui da cui il sistema prende o descrive qualcosa.")
    p.add_argument("--autotest", action="store_true")
    p.add_argument("--radice", default=".", help="radice del template o del progetto")
    sub = p.add_subparsers(dest="comando")
    pc = sub.add_parser("controlla", help="censisce, poi i repository sorvegliati cambiati dall'ultima verifica")
    pc.add_argument("--rigoroso", action="store_true")
    pn = sub.add_parser("censisci", help="aggiunge i repository nuovi e toglie quelli spariti dalle schede")
    pn.add_argument("--check", action="store_true", help="non scrive; nel template esce con 1 se il registro è incompleto")
    ps = sub.add_parser("segna", help="registra come verificata la versione di adesso, dopo aver aggiornato la scheda")
    ps.add_argument("repo")
    pt = sub.add_parser("cita", help="un repository soltanto citato, che non si sorveglia")
    pt.add_argument("repo")
    pt.add_argument("--motivo", required=True)
    pv = sub.add_parser("sorveglia", help="aggiunge o corregge un repository sorvegliato")
    pv.add_argument("repo")
    pv.add_argument("--cartella", default="")
    pv.add_argument("--release", action="store_true", help="sorveglia le release invece dei commit")
    pv.add_argument("--pacchetto", default="")
    pv.add_argument("--scheda", default="")
    a = p.parse_args(argv)
    if a.autotest:
        return autotest()
    radice = Path(a.radice)
    if a.comando == "controlla":
        return cmd_controlla(radice, a.rigoroso)
    if a.comando == "censisci":
        return cmd_censisci(radice, a.check)
    if a.comando == "segna":
        print("verificato %s a %s" % (a.repo, breve(cmd_segna(radice, a.repo))))
        return 0
    if a.comando == "cita":
        cmd_cita(radice, a.repo, a.motivo)
        print("citato %s" % a.repo)
        return 0
    if a.comando == "sorveglia":
        cmd_sorveglia(radice, a.repo, a.cartella, a.release, a.pacchetto, a.scheda)
        print("sorvegliato %s; ora va confrontato con la scheda e segnato" % a.repo)
        return 0
    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
