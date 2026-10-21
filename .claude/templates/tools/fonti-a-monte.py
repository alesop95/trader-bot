#!/usr/bin/env python3
"""Tutto ciò che il sistema prende da altri, e quando cambia.

Perché esiste. Il template installa, configura, importa e consiglia materiale altrui, e
prende affermazioni da fonti altrui: skill, server MCP, programmi, librerie, guide. Il
2026-10-20 la scheda di `matt-pocock-skills` consigliava ancora `resolving-merge-conflicts`,
che l'autore aveva tolto il giorno prima, e la valutazione completa fatta subito dopo ha
trovato altre tre schede invecchiate in silenzio. Il 2026-10-21 è successo di nuovo con
`taste-skill`, passata da tredici skill a una sola: il controllo all'apertura non l'ha vista
perché il registro la teneva fra i repository «soltanto citati», che non si interrogavano.
Da quel giorno, su direttiva del proprietario, non esiste più un elenco di esclusi: ogni
fonte che compare nel template si sorveglia, e porta scritto quale ruolo ha nel template e
che cosa il template ne prende.

Il registro ha un elenco solo, `fonti`. Ogni voce ha un identificativo con il suo tipo,
`github:owner/repo`, `npm:nome`, `pypi:nome`, `crates:nome`, `brew:nome`, `docker:immagine`,
`winget:Id` o `apt:nome`; un `ruolo` dell'insieme chiuso `RUOLI`; il `motivo`, cioè che cosa
il template ne prende; la `scheda` che lo descrive; e il `controllo`, cioè come si sa che è
cambiata: `release` o `commit`, eventualmente su una `cartella`, per GitHub, `versione` per un
registro di pacchetti, `manuale` con una scadenza in giorni per ciò che non ha un'interfaccia
interrogabile. Una voce può seguire un'altra fonte con `via`, come un'immagine di ghcr.io che
segue le release del repository da cui nasce.

L'unico elenco a parte è `falsi`: stringhe che il censimento scambia per una fonte e non lo
sono, come una parola italiana dopo `npx` in una frase. Una voce entra fra i falsi solo se lo
strumento verifica che a monte non esiste, e il controllo la rilegge a ogni corsa: se un giorno
esiste, lo dice. Così non c'è modo di escludere una fonte vera chiamandola falsa.

Il censimento rende il registro completo da sé. Percorre i file e raccoglie ogni repository
GitHub in un URL, in un comando o fra apici inversi; ogni pacchetto in un comando npx, npm,
pip, uv, pipx, cargo, brew, winget, apt o docker, e negli `args` di una configurazione MCP; e,
nel template, ogni libreria non di sistema importata dagli strumenti Python. Ciò che non è nel
registro entra senza ruolo e senza motivo, mai verificato; una voce che non compare più si
toglie.

Il template e i progetti usano lo stesso strumento, che riconosce da sé dove si trova.

Nel template il registro è `.claude/templates/fonti-a-monte.json`, il documento che lo rende
leggibile per ruolo è `.claude/templates/fonti-a-monte.md`, generato, e il censimento percorre
pacchetti, catalogo, skill, regole, norme, `PROJECT-SYSTEM.md` e README. `controlla` gira
all'apertura di ogni sessione. I chiudi del template lanciano `censisci --check`, che ferma il
commit se una fonte manca dal registro, è senza ruolo o senza motivo, non è mai stata
verificata, oppure se il documento non corrisponde al registro.

In un progetto istanziato il registro è `.claude/fonti-a-monte.json`. Le schede dei pacchetti
le corregge il template e arrivano con l'allineamento; ciò che può invecchiare nel progetto è
quanto il progetto ha installato da altri, quindi il censimento percorre `.claude/skills`,
`.claude/agents`, `.claude/commands`, `.claude/agent-catalog` e `.agents`, escluse le skill di
sistema che arrivano dal template, e assegna da sé ruolo e motivo dal posto dove ha trovato
la fonte. Nel progetto il controllo avvisa e non ferma mai il commit.

    python .claude/templates/tools/fonti-a-monte.py controlla
    python .claude/templates/tools/fonti-a-monte.py censisci [--check]
    python .claude/templates/tools/fonti-a-monte.py classifica <id> --ruolo F --motivo "..." [--controllo C] [--cartella X] [--via ID] [--scadenza N]
    python .claude/templates/tools/fonti-a-monte.py segna <id>
    python .claude/templates/tools/fonti-a-monte.py falso <stringa> --motivo "..."
    python .claude/templates/tools/fonti-a-monte.py elenca [--scrivi]
    python .claude/templates/tools/fonti-a-monte.py --autotest

Un identificativo senza tipo, `owner/repo`, si legge come `github:owner/repo`. Le richieste a
GitHub usano il token di `GH_TOKEN`, `GITHUB_TOKEN` o `gh auth token`; senza, GitHub ne concede
sessanta l'ora, e al limite lo strumento si ferma dicendolo invece di riportare invariate le
fonti che non ha letto. `controlla` esce con 0 anche quando trova cambiamenti o non raggiunge
la rete, salvo `--rigoroso`.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import json
import os
import re
import ssl
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REGISTRO_TEMPLATE = Path(".claude") / "templates" / "fonti-a-monte.json"
DOCUMENTO_TEMPLATE = Path(".claude") / "templates" / "fonti-a-monte.md"
REGISTRO_PROGETTO = Path(".claude") / "fonti-a-monte.json"
MARCATORE_TEMPLATE = Path(".claude") / "PROMPT-nuovo-progetto.md"
DEFINIZIONE_SISTEMA = Path(".claude") / "templates" / "tools" / "allinea-dal-template.py"
PAGINA = 30
SCADENZA_MANUALE = 90
DA_CLASSIFICARE = "da-classificare"
TESTO = {".md", ".json", ".yaml", ".yml", ".txt"}
CODICE = {".ps1", ".sh", ".py", ".toml"}
FUORI = {"_notes", "fixtures", "__pycache__", ".git", "node_modules"}
POSTI_PROGETTO = [".claude/skills", ".claude/agents", ".claude/commands", ".claude/agent-catalog", ".agents"]
TIPI = ("github", "npm", "pypi", "crates", "brew", "docker", "winget", "apt", "feed", "hf")
CONTROLLI = ("commit", "release", "versione", "manuale")

# L'insieme chiuso dei ruoli. Si chiamano ruoli e non filoni perché nel template un filone è una
# linea di sviluppo di `docs/FILONI.md`. Ogni fonte ne ha uno, quello principale, e
# il documento generato li spiega in quest'ordine.
RUOLI = {
    "skill-e-agenti": (
        "Skill, agenti, comandi e plugin",
        "Skill, agenti, comandi e plugin per Claude Code o Codex che il template installa, adatta o consiglia, e i loro installatori.",
        "che il contenuto descritto dalla scheda, cioè nomi, conteggi e varianti, sia ancora quello, e che il comando d'installazione funzioni ancora così come è scritto"),
    "server-mcp": (
        "Server MCP",
        "Server MCP che il template configura in `.mcp.json` o consiglia in una scheda.",
        "il nome del pacchetto o dell'immagine, il comando di avvio, gli strumenti esposti e le variabili richieste"),
    "strumenti": (
        "Strumenti, programmi e servizi",
        "Programmi a riga di comando, applicazioni, contenitori e servizi da installare sulla macchina perché un pacchetto del template funzioni.",
        "il comando d'installazione, i requisiti, la versione dove la scheda ne fissa una e la licenza"),
    "librerie": (
        "Librerie",
        "Librerie che gli strumenti del template importano o fanno installare.",
        "che il nome del pacchetto sia lo stesso e che l'interfaccia usata dallo strumento esista ancora, cosa che l'autotest dello strumento prova quando la libreria è installata"),
    "fonti-di-norme": (
        "Fonti di norme e guide",
        "Repository da cui una regola, una norma, una guida o un registro delle fonti del template prende affermazioni o citazioni.",
        "che le affermazioni citate si leggano ancora alla versione corrente; se sono cambiate o spostate, la citazione si data e si indica dove sta ora"),
    "cataloghi": (
        "Cataloghi e indici",
        "Indici e raccolte curate da cui il template pesca a richiesta, e da cui il catalogo dei pacchetti ricava candidati.",
        "la struttura e i conteggi che la scheda dichiara"),
    "ispirazioni": (
        "Ispirazioni e crediti",
        "Progetti da cui il template ha adattato un'idea o un pattern senza copiarne file, riconosciuti nei crediti del README o nella scheda del pacchetto.",
        "che esistano, non siano archiviati e abbiano la licenza dichiarata, e se l'idea adattata è cambiata in modo che il pacchetto debba seguirla"),
    "candidati": (
        "Candidati e alternative",
        "Repository valutati e non adottati: candidati segnalati da una fonte di scouting, studiati in un filone di `docs/FILONI.md`, o elencati come alternative in un documento di ricerca o di handoff datato.",
        "che esistano, non siano archiviati e abbiano la licenza dichiarata; un documento datato non si riscrive, ma un candidato maturato si porta alle quattro domande di `docs/FILONI.md` per diventare voce di catalogo"),
    "scouting": (
        "Fonti di scouting",
        "Siti ed elenchi che si ricontrollano per trovare strumenti da portare nel template, registrati in `docs/fonti-di-scouting.md`; si sorvegliano dal loro feed.",
        "che cosa la fonte ha pubblicato dopo l'ultimo passaggio, secondo il metodo di `docs/fonti-di-scouting.md`, e si aggiorna là la data dell'ultimo controllo"),
}

# Primi segmenti di github.com che non sono un utente o un'organizzazione.
RISERVATI = {"en", "orgs", "settings", "features", "topics", "marketplace", "apps", "sponsors", "login",
             "about", "pricing", "site", "collections", "explore", "notifications", "new", "search",
             "enterprise", "security", "customer-stories", "readme", "trending", "events", "github"}
NOME = r"[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9._-]+"
SCHEMI_GITHUB = [
    re.compile(r"(?<![\w.])(?:https?://)?(?:www\.)?github\.com/(" + NOME + ")"),
    re.compile(r"raw\.githubusercontent\.com/(" + NOME + ")"),
    re.compile(r"(?:gh skill install|gh repo clone|npx skills(?:@[\w.]+)? add|marketplace add)\s+(" + NOME + ")"),
    # Una GitHub Action in un workflow, `uses: owner/repo@v6` o `uses: owner/repo/sotto@v1`.
    re.compile(r"\buses:\s*['\"]?(" + NOME + r")(?:/[\w./-]+)?@"),
]
# Un nome fra apici inversi, come `ryoppippi/ccusage`, è un repository solo se non è un percorso:
# il primo segmento non è una cartella del repository e il secondo non finisce con un'estensione.
APICI = re.compile(r"`(" + NOME + ")`")
ESTENSIONE = re.compile(r"\.[A-Za-z0-9]{1,5}$")
PKG_NPM = r"(@?[a-z0-9][a-z0-9._-]*(?:/[a-z0-9][a-z0-9._-]*)?)"
SCHEMI_PACCHETTI = [
    ("npm", re.compile(r"\bnpx\s+(?:(?:-y|--yes)\s+)?" + PKG_NPM)),
    ("npm", re.compile(r"\bnpm\s+(?:install|i)\s+(?:-g|--global)\s+" + PKG_NPM)),
    ("npm", re.compile(r"\"npx\"[^\]]*?\"(?:-y|--yes)\",\s*\"" + PKG_NPM)),
    ("pypi", re.compile(r"\bpip3?\s+install\s+(?:(?:-U|--upgrade|--user|-q)\s+)*([A-Za-z0-9][\w.-]*)")),
    ("pypi", re.compile(r"\b(?:uv tool install|uv pip install|pipx install|uvx)\s+(?:--\S+\s+)*([A-Za-z0-9][\w.-]*)")),
    ("crates", re.compile(r"\bcargo\s+install\s+(?:--\S+\s+)*([a-z0-9][\w-]*)")),
    ("brew", re.compile(r"\bbrew\s+install\s+(?:--cask\s+)?([a-z0-9][\w@.+-]*)")),
    ("winget", re.compile(r"\bwinget\s+install\s+(?:-e\s+)?(?:--id[ =]\s*)?([A-Za-z0-9][\w-]*\.[\w.-]+)")),
    ("docker", re.compile(r"\bdocker\s+(?:run|pull)\b[^\n`|]*?\s((?:[a-z0-9.-]+\.[a-z]{2,}/)?[a-z0-9][\w.-]*/[\w.-]+(?:/[\w.-]+)*)")),
]
# Il feed di una fonte di scouting: un URL che finisce in rss, feed o atom, con o senza .xml.
FEED = re.compile(r"(https?://[\w.-]+(?:/[\w.-]+)*/(?:rss|feed|atom)(?:\.xml)?)(?![\w/-])")
# Un modello o un dataset di Hugging Face: un URL, oppure un nome fra apici inversi subito dopo
# la parola HuggingFace, come nel documento del filone dei modelli locali.
HF = re.compile(r"(?:huggingface\.co/|Hugging ?Face\s+`)(" + NOME + ")")
APT = re.compile(r"\bapt(?:-get)?\s+install\s+(?:-y\s+)?((?:[a-z0-9][a-z0-9.+-]+\s*)+)")
# Moduli Python il cui pacchetto su PyPI ha un altro nome.
MODULI_PYPI = {"PIL": "pillow", "docx": "python-docx", "yaml": "pyyaml", "markdown_it": "markdown-it-py",
               "fitz": "pymupdf", "cv2": "opencv-python", "bs4": "beautifulsoup4", "sklearn": "scikit-learn",
               "pptx": "python-pptx", "dateutil": "python-dateutil"}
IMPORT = re.compile(r"^\s*(?:import|from)\s+([A-Za-z_]\w*)", re.M)


class LimiteRaggiunto(Exception):
    pass


class FonteAssente(Exception):
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


# --------------------------------------------------------------------------- identificativi

def normale(ident: str) -> str:
    """`owner/repo` diventa `github:owner/repo`; il resto resta com'è."""
    ident = ident.strip()
    tipo, sep, _ = ident.partition(":")
    if sep and tipo in TIPI:
        return ident
    return "github:" + ident


def tipo_di(ident: str) -> str:
    return ident.partition(":")[0]


def nome_di(ident: str) -> str:
    return ident.partition(":")[2]


def chiave(ident: str) -> str:
    return ident.lower()


def link(ident: str) -> str:
    t, n = tipo_di(ident), nome_di(ident)
    return {"github": "https://github.com/%s" % n,
            "npm": "https://www.npmjs.com/package/%s" % n,
            "pypi": "https://pypi.org/project/%s/" % n,
            "crates": "https://crates.io/crates/%s" % n,
            "brew": "https://formulae.brew.sh/formula/%s" % n,
            "feed": n,
            "hf": "https://huggingface.co/%s" % n,
            "docker": "https://hub.docker.com/r/%s" % n if n.count("/") == 1 and "." not in n.split("/")[0] else "",
            }.get(t, "")


# --------------------------------------------------------------------------- registro

def migra(dati, nel_tpl: bool) -> dict:
    """Il registro nella forma di prima, con `sorvegliati` e `citati`, nella forma di adesso.

    I citati diventano fonti come le altre: è la direttiva del 2026-10-21. Nel template entrano
    senza ruolo, perché il ruolo si sceglie leggendo la scheda; in un progetto lo si deduce
    dal posto, come per una fonte nuova.
    """
    if isinstance(dati, list):
        dati = {"sorvegliati": dati}
    if "fonti" in dati:
        # Il primo giorno della forma nuova la chiave si chiamava `filone`.
        for v in dati["fonti"]:
            if "filone" in v and "ruolo" not in v:
                v["ruolo"] = v.pop("filone")
        return dati
    fonti = []
    for v in dati.get("sorvegliati", []):
        f = {"id": normale(v["repo"]), "ruolo": DA_CLASSIFICARE if nel_tpl else ruolo_dal_posto(v.get("scheda", "")),
             "motivo": "" if nel_tpl else motivo_dal_posto(v.get("scheda", "")),
             "pacchetto": v.get("pacchetto", ""), "scheda": v.get("scheda", ""),
             "controllo": "release" if v.get("tipo") == "release" else "commit", "cartella": v.get("cartella", "")}
        for campo in ("verificato", "data"):
            if v.get(campo):
                f[campo] = v[campo]
        fonti.append(f)
    for v in dati.get("citati", []):
        fonti.append({"id": normale(v["repo"]), "ruolo": DA_CLASSIFICARE,
                      "motivo": "", "nota-di-prima": v.get("motivo", ""), "pacchetto": "", "scheda": ""})
    nuovo = {"fonti": fonti, "falsi": []}
    if "spediti" in dati:
        nuovo["spediti"] = dati["spediti"]
    return nuovo


def leggi_registro(radice: Path) -> dict:
    f = percorso_registro(radice)
    if not f.exists():
        return {"fonti": [], "falsi": []}
    dati = migra(json.loads(f.read_text(encoding="utf-8")), nel_template(radice))
    dati.setdefault("fonti", [])
    dati.setdefault("falsi", [])
    for v in dati["fonti"]:
        if not v.get("id") or tipo_di(v["id"]) not in TIPI:
            raise ValueError("fonte senza identificativo valido: %r" % (v,))
        if v.get("ruolo", DA_CLASSIFICARE) not in RUOLI and v.get("ruolo") != DA_CLASSIFICARE:
            raise ValueError("ruolo sconosciuto %r per %s" % (v.get("ruolo"), v["id"]))
        if v.get("controllo") and v["controllo"] not in CONTROLLI:
            raise ValueError("controllo sconosciuto %r per %s" % (v["controllo"], v["id"]))
    for v in dati["falsi"]:
        if not v.get("id") or not v.get("motivo"):
            raise ValueError("falso senza identificativo o senza motivo: %r" % (v,))
    return dati


def scrivi_registro(radice: Path, dati: dict) -> None:
    f = percorso_registro(radice)
    f.parent.mkdir(parents=True, exist_ok=True)
    dati["fonti"].sort(key=lambda v: (chiave(v["id"]), v.get("cartella", "")))
    dati["falsi"].sort(key=lambda v: chiave(v["id"]))
    ordinato = {"fonti": dati["fonti"], "falsi": dati["falsi"]}
    if "spediti" in dati:
        ordinato["spediti"] = dati["spediti"]
    f.write_text(json.dumps(ordinato, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    # Nel template il documento segue il registro a ogni scrittura, così non resta mai indietro.
    if nel_template(radice):
        (radice / DOCUMENTO_TEMPLATE).write_text(documento(ordinato), encoding="utf-8", newline="\n")


def trova(dati: dict, ident: str, elenco: str = "fonti") -> list:
    return [v for v in dati[elenco] if chiave(v["id"]) == chiave(normale(ident))]


def ruolo_dal_posto(scheda: str) -> str:
    return "cataloghi" if "/agent-catalog" in scheda else "skill-e-agenti"


def motivo_dal_posto(scheda: str) -> str:
    return "installato nel progetto, in %s" % (scheda or "un posto non registrato")


# --------------------------------------------------------------------------- censimento

def pulisci(nome: str):
    owner, _, repo = nome.partition("/")
    repo = re.sub(r"\.git$", "", repo).rstrip(".")
    if owner.lower() in RISERVATI or not repo or repo.startswith("."):
        return None
    return "github:" + owner + "/" + repo


def pulisci_pacchetto(tipo: str, nome: str):
    nome = nome.strip().rstrip(".,;:)")
    if tipo == "npm":
        # Una versione dopo il nome, `pacchetto@latest` o `@scope/nome@1.2`, non fa parte del nome.
        if nome.startswith("@"):
            scope, _, resto = nome.partition("/")
            nome = scope + "/" + resto.split("@")[0]
        else:
            nome = nome.split("@")[0]
    elif tipo == "pypi":
        nome = re.split(r"[\[<>=!~]", nome)[0]
        if nome.endswith(".txt") or nome.startswith("-") or "/" in nome:
            return None
        nome = nome.lower().replace("_", "-")
    elif tipo == "docker":
        nome = nome.split(":")[0]
    if not nome or nome in ("-", "@"):
        return None
    return tipo + ":" + nome


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
    tpl = nel_template(radice)
    if tpl:
        basi = [radice / ".claude" / p for p in ("templates", "skills", "rules", "norme")]
        basi += [radice / ".claude" / "PROJECT-SYSTEM.md", radice / "README.md", radice / "docs"]
        spediti = {}
        estensioni = TESTO | CODICE | {".html"}
    else:
        basi = [radice / p for p in POSTI_PROGETTO]
        spediti = leggi_registro_template(radice).get("spediti", {})
        spediti = dict(spediti, skills=sorted(set(spediti.get("skills", [])) | skill_di_sistema(radice)))
        estensioni = TESTO
    stesso = Path(__file__).resolve()
    trovati = []
    for base in basi:
        for f in ([base] if base.is_file() else sorted(base.rglob("*")) if base.is_dir() else []):
            rel = f.relative_to(radice).parts
            if not f.is_file() or f.suffix.lower() not in estensioni or FUORI.intersection(rel):
                continue
            if f.name in ("fonti-a-monte.json", "fonti-a-monte.md") or del_template(rel, spediti):
                continue
            if f.resolve() == stesso or f.name == "fonti-a-monte.py":
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
        if rel[0] == "docs":
            nome = Path(rel[-1]).stem
            if nome.startswith("filone-"):
                return "filone " + nome[len("filone-"):].replace("-censimento", "").replace("-percorso", "")
            if nome == "fonti-di-scouting":
                return "scouting"
            return "docs"
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


def moduli_locali(radice: Path) -> set:
    return {f.stem for f in (radice / ".claude").rglob("*.py")} | {f.stem for f in (radice / "tools").rglob("*.py")} \
        if (radice / "tools").is_dir() else {f.stem for f in (radice / ".claude").rglob("*.py")}


def importati(testo: str, locali: set) -> list:
    std = set(getattr(sys, "stdlib_module_names", ()))
    nomi = []
    for m in IMPORT.finditer(testo):
        mod = m.group(1)
        if mod in std or mod in locali or mod == "__future__" or mod.startswith("_"):
            continue
        nomi.append("pypi:" + MODULI_PYPI.get(mod, mod.lower().replace("_", "-")))
    return nomi


def pacchetti(testo: str) -> list:
    nomi = []
    for tipo, schema in SCHEMI_PACCHETTI:
        nomi += [pulisci_pacchetto(tipo, m.group(1)) for m in schema.finditer(testo)]
    for m in APT.finditer(testo):
        nomi += ["apt:" + n for n in m.group(1).split() if not n.startswith("$")]
    nomi += ["feed:" + m.group(1) for m in FEED.finditer(testo)]
    nomi += ["hf:" + m.group(1) for m in HF.finditer(testo)]
    return nomi


def censimento(radice: Path, dati: dict) -> dict:
    """Ogni fonte che compare nei file, con il primo file in cui compare."""
    tpl = nel_template(radice)
    noti = {chiave(nome_di(v["id"])): v["id"] for v in dati["fonti"] if tipo_di(v["id"]) == "github"}
    # Fra apici inversi solo nel template, dove il catalogo nomina così i repository. In un progetto
    # la stessa forma è quasi sempre codice: `testing-library/no-node-access` è una regola di lint
    # (misurato il 2026-10-20 sui progetti locali).
    locali = cartelle_locali(radice) if tpl else None
    moduli = moduli_locali(radice) if tpl else set()
    trovati = {}
    for f in file_da_censire(radice):
        testo = f.read_text(encoding="utf-8", errors="replace")
        nomi = pacchetti(testo) + [pulisci(m.group(1)) for s in SCHEMI_GITHUB for m in s.finditer(testo)]
        if f.suffix.lower() in TESTO:
            if locali is not None:
                nomi += tra_apici(testo, locali)
            # Un repository già noto conta anche scritto senza URL, come `mattpocock/skills`.
            basso = testo.lower()
            nomi += [r for k, r in noti.items() if k in basso]
        if tpl and f.suffix.lower() == ".py":
            nomi += importati(testo, moduli)
        modelli = {chiave(nome_di(n)) for n in nomi if n and n.startswith("hf:")}
        nomi = [n for n in nomi if not (n and n.startswith("github:") and chiave(nome_di(n)) in modelli)]
        for n in nomi:
            if n and chiave(n) not in trovati:
                trovati[chiave(n)] = (n, f)
    # Un'immagine di ghcr.io nasce da un repository GitHub con lo stesso nome: si segue quello.
    return trovati


def nuova_voce(radice: Path, ident: str, f: Path) -> dict:
    scheda = f.relative_to(radice).as_posix()
    v = {"id": ident, "pacchetto": pacchetto_di(radice, f), "scheda": scheda}
    if nel_template(radice):
        v.update({"ruolo": DA_CLASSIFICARE, "motivo": ""})
    else:
        v.update({"ruolo": ruolo_dal_posto(scheda), "motivo": motivo_dal_posto(scheda)})
    if tipo_di(ident) == "docker" and nome_di(ident).startswith("ghcr.io/"):
        v["via"] = "github:" + "/".join(nome_di(ident).split("/")[1:3])
    return v


def censisci(radice: Path, scrivi: bool) -> tuple:
    dati = leggi_registro(radice)
    trovati = censimento(radice, dati)
    falsi = {chiave(v["id"]) for v in dati["falsi"]}
    noti = {chiave(v["id"]) for v in dati["fonti"]}
    nuovi = [(n, f) for k, (n, f) in sorted(trovati.items()) if k not in noti and k not in falsi]
    # Una fonte seguita da un'altra con `via` resta finché la segue qualcuno.
    seguiti = {chiave(v["via"]) for v in dati["fonti"] if v.get("via")}
    orfani = [v for v in dati["fonti"] if chiave(v["id"]) not in trovati and chiave(v["id"]) not in seguiti]
    falsi_spariti = [v for v in dati["falsi"] if chiave(v["id"]) not in trovati]
    spediti = spediti_dal_template(radice) if nel_template(radice) else dati.get("spediti")
    elenco_vecchio = spediti != dati.get("spediti")
    if scrivi and (nuovi or orfani or falsi_spariti or elenco_vecchio or "fonti" not in leggi_grezzo(radice)):
        dati["fonti"] = [v for v in dati["fonti"] if v not in orfani] + [nuova_voce(radice, n, f) for n, f in nuovi]
        dati["falsi"] = [v for v in dati["falsi"] if v not in falsi_spariti]
        if spediti is not None:
            dati["spediti"] = spediti
        scrivi_registro(radice, dati)
    return nuovi, orfani, elenco_vecchio


def leggi_grezzo(radice: Path) -> dict:
    f = percorso_registro(radice)
    if not f.exists():
        return {"fonti": []}
    dati = json.loads(f.read_text(encoding="utf-8"))
    return dati if isinstance(dati, dict) else {}


def incomplete(dati: dict) -> list:
    """Le fonti che non si possono ancora dire sorvegliate: senza ruolo, senza motivo, mai verificate."""
    righe = []
    for v in dati["fonti"]:
        manca = []
        if v.get("ruolo", DA_CLASSIFICARE) == DA_CLASSIFICARE:
            manca.append("ruolo")
        if not v.get("motivo", "").strip():
            manca.append("motivo")
        if not v.get("verificato"):
            manca.append("verifica")
        if manca:
            righe.append((v["id"], manca))
    return righe


LICENZE = re.compile(r"(?<![\w-])(MIT|Apache-2\.0|AGPL-3\.0|LGPL-3\.0|GPL-3\.0|GPL-2\.0|BSD-2-Clause|BSD-3-Clause|MPL-2\.0|ISC|Unlicense|Elastic License 2\.0|BUSL-1\.1)(?![\w.])")
SPDX_DICHIARABILI = {"MIT", "Apache-2.0", "AGPL-3.0", "LGPL-3.0", "GPL-3.0", "GPL-2.0", "BSD-2-Clause", "BSD-3-Clause", "MPL-2.0", "ISC", "Unlicense"}


def licenze_discordanti(radice: Path, dati: dict) -> list:
    """Le righe che dichiarano per un repository una licenza diversa da quella letta a monte.

    Il 2026-10-21 le schede davano MIT a otto repository che a monte erano Apache-2.0, Elastic o
    GPL, e AGPL a uno che era MIT: nessuno se ne era accorto, perché la licenza si scrive una volta.
    La licenza letta da `segna` sta nel registro; qui la si confronta senza rete con ogni riga che
    nomina un solo repository noto e dichiara una licenza. Una riga che ne dichiara più di una, per
    una licenza per componente, passa se fra quelle c'è la licenza letta a monte.
    """
    licenze = {chiave(nome_di(v["id"])): v["licenza"] for v in dati["fonti"]
               if tipo_di(v["id"]) == "github" and v.get("licenza") in SPDX_DICHIARABILI}
    righe = []
    for f in file_da_censire(radice):
        if f.suffix.lower() not in (".md", ".html"):
            continue
        for n, riga in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            nomi = {chiave(nome_di(x)) for x in (pulisci(m.group(1)) for s in SCHEMI_GITHUB for m in s.finditer(riga)) if x}
            nomi |= {k for k in licenze if ("repo " + k) in riga.lower()}
            nomi &= set(licenze)
            if len(nomi) != 1:
                continue
            repo = nomi.pop()
            dichiarate = set(LICENZE.findall(riga))
            if dichiarate and licenze[repo] not in dichiarate:
                righe.append((f.relative_to(radice).as_posix(), n, repo, sorted(dichiarate), licenze[repo]))
    return righe


def cmd_censisci(radice: Path, check: bool) -> int:
    tpl = nel_template(radice)
    nuovi, orfani, elenco_vecchio = censisci(radice, scrivi=not check)
    for n, f in nuovi:
        print("   +  %s, in %s: %s" % (n, f.relative_to(radice).as_posix(),
              "da censire" if check else "aggiunta al registro, da classificare e verificare"))
    for v in orfani:
        print("   -  %s: non compare più in nessun file, %s" % (v["id"], "da togliere" if check else "tolta"))
    if elenco_vecchio:
        print("   *  elenco delle skill, degli agenti e dei comandi del template: %s" % ("da aggiornare" if check else "aggiornato"))
    dati = leggi_registro(radice) if not check else applica_censimento(radice, nuovi, orfani)
    aperte = incomplete(dati)
    for ident, manca in aperte[:40]:
        print("   ?  %s: manca %s" % (ident, ", ".join(manca)))
    if len(aperte) > 40:
        print("   ?  e altre %d fonti incomplete" % (len(aperte) - 40))
    discordanti = licenze_discordanti(radice, dati)
    for f, n, repo, dichiarate, vera in discordanti:
        print("   !  %s:%d dichiara %s per %s, a monte è %s" % (f, n, " e ".join(dichiarate), repo, vera))
    doc_vecchio = False
    if tpl:
        f = radice / DOCUMENTO_TEMPLATE
        atteso = documento(dati)
        doc_vecchio = not f.exists() or f.read_text(encoding="utf-8") != atteso
        if doc_vecchio and not check:
            f.write_text(atteso, encoding="utf-8", newline="\n")
            doc_vecchio = False
            print("   *  %s rigenerato" % DOCUMENTO_TEMPLATE.as_posix())
        elif doc_vecchio:
            print("   *  %s non corrisponde al registro: lancia elenca --scrivi" % DOCUMENTO_TEMPLATE.as_posix())
    rotto = (check and (nuovi or orfani or elenco_vecchio)) or aperte or doc_vecchio or discordanti
    if rotto:
        print("censimento incompleto: %d nuove, %d tolte, %d fonti incomplete su %d, %d licenze discordanti; classifica, segna e correggi"
              % (len(nuovi), len(orfani), len(aperte), len(dati["fonti"]), len(discordanti)))
        return 1 if tpl else 0
    stato = "%d fonti, tutte classificate e verificate" % len(dati["fonti"]) if dati["fonti"] else "nessuna fonte"
    print("censimento: %d nuovi, %d tolti; %s" % (len(nuovi), len(orfani), stato))
    return 0


def applica_censimento(radice: Path, nuovi: list, orfani: list) -> dict:
    """Il registro come sarebbe dopo il censimento, senza scriverlo: per il controllo del commit."""
    dati = leggi_registro(radice)
    dati["fonti"] = [v for v in dati["fonti"] if v not in orfani] + [nuova_voce(radice, n, f) for n, f in nuovi]
    return dati


# --------------------------------------------------------------------------- documento

def cella(testo: str) -> str:
    return " ".join(str(testo).split()).replace("|", "\\|")


def documento(dati: dict) -> str:
    fonti = dati["fonti"]
    righe = [
        "# Fonti a monte del template",
        "",
        "> Documento generato da `python .claude/templates/tools/fonti-a-monte.py elenca --scrivi` a partire da `.claude/templates/fonti-a-monte.json`: non si modifica a mano, si modifica il registro con lo strumento e si rigenera. Il commit del template si ferma se i due non corrispondono.",
        "",
        "Il template installa, configura, importa e consiglia materiale altrui, e prende affermazioni da fonti altrui. Ciascuna di queste fonti invecchia senza avvisare, e una scheda che la descrive ha lo stesso aspetto quando è vera e quando non lo è più. Per questo ogni fonte che compare nei file del template sta qui, con il ruolo a cui appartiene, ciò che il template ne prende, la scheda che la descrive e il modo in cui si sa che è cambiata, e `fonti-a-monte.py controlla` le interroga tutte all'apertura di ogni sessione. Non esiste un elenco di fonti escluse: dal 2026-10-21, su direttiva del proprietario, una fonte presente nel template si sorveglia sempre, qualunque sia il suo ruolo.",
        "",
        "Il controllo si sceglie per fonte. Un repository GitHub che pubblica release si segue per release, uno che non le pubblica per commit, eventualmente sulla sola cartella che la scheda descrive; un pacchetto npm, PyPI, crates o Homebrew per la versione pubblicata, che è ciò che davvero si installa; ciò che non ha un'interfaccia interrogabile, come un pacchetto di una distribuzione Linux o un prodotto commerciale, si rivede a mano entro una scadenza in giorni, e il controllo segnala la scadenza passata. Oltre alla versione, per GitHub il controllo segnala un repository archiviato, rinominato o trasferito, o una licenza cambiata, e `censisci --check` confronta senza rete la licenza letta a monte con quella che le schede dichiarano.",
        "",
        "Le fonti stanno qui per ruolo, cioè per ciò che il template ne fa, e la colonna del pacchetto dice dove le usa. Il ruolo non va confuso con i filoni di `docs/FILONI.md`, che sono linee di sviluppo: un repository nominato nel documento di un filone porta il nome del filone come pacchetto, e uno segnalato dallo scouting di `docs/fonti-di-scouting.md` porta `scouting`, mentre il feed della fonte di scouting ha un ruolo proprio, così che il controllo all'apertura dica anche quante segnalazioni nuove aspettano un passaggio.",
        "",
        "## Riepilogo",
        "",
        "| Ruolo | Fonti | Per release o versione | Per commit | A mano |",
        "|---|---|---|---|---|",
    ]
    ordine = list(RUOLI) + [DA_CLASSIFICARE]
    for nome in ordine:
        gruppo = [v for v in fonti if v.get("ruolo", DA_CLASSIFICARE) == nome]
        if not gruppo:
            continue
        titolo = RUOLI[nome][0] if nome in RUOLI else "Da classificare"
        controlli = [v.get("controllo", "") for v in gruppo]
        righe.append("| %s | %d | %d | %d | %d |" % (titolo, len(gruppo), sum(c in ("release", "versione") for c in controlli),
                                                     sum(c in ("commit", "") for c in controlli), controlli.count("manuale")))
    righe.append("| Totale | %d | | | |" % len(fonti))
    for nome in ordine:
        gruppo = sorted((v for v in fonti if v.get("ruolo", DA_CLASSIFICARE) == nome), key=lambda v: chiave(v["id"]))
        if not gruppo:
            continue
        if nome in RUOLI:
            titolo, cosa, verifica = RUOLI[nome]
            righe += ["", "## " + titolo, "", cosa + " Quando il controllo segnala una di queste fonti, si verifica " + verifica + "."]
        else:
            righe += ["", "## Da classificare", "", "Fonti appena censite, che non hanno ancora un ruolo e un motivo: finché restano qui il commit del template si ferma."]
        righe += ["", "| Fonte | Che cosa ne prende il template | Pacchetto o filone | Scheda | Controllo | Verificata |", "|---|---|---|---|---|---|"]
        for v in gruppo:
            u = link(v["id"])
            fonte = "[%s](%s)" % (v["id"], u) if u else "`%s`" % v["id"]
            controllo = v.get("controllo", "") or "da scegliere"
            if v.get("cartella"):
                controllo += " su `%s`" % v["cartella"]
            if v.get("via"):
                controllo += " via `%s`" % v["via"]
            if controllo.startswith("manuale"):
                controllo += ", ogni %s giorni" % v.get("scadenza", SCADENZA_MANUALE)
            verificata = ("%s, %s" % (breve(v["verificato"]), v.get("data", "?"))) if v.get("verificato") else "mai"
            righe.append("| %s | %s | %s | `%s` | %s | %s |" % (fonte, cella(v.get("motivo", "")) or "da scrivere", cella(v.get("pacchetto", "")) or "?",
                                                                cella(v.get("scheda", "")), cella(controllo), cella(verificata)))
    righe += ["", "## Falsi del censimento", ""]
    if dati["falsi"]:
        righe += ["Stringhe che il censimento scambia per una fonte e non lo sono. Lo strumento ne accetta una solo dopo aver verificato che a monte non esiste, e la rilegge a ogni controllo.", "",
                  "| Stringa | Perché non è una fonte |", "|---|---|"]
        righe += ["| `%s` | %s |" % (v["id"], cella(v["motivo"])) for v in sorted(dati["falsi"], key=lambda v: chiave(v["id"]))]
    else:
        righe.append("Nessuno.")
    return "\n".join(righe) + "\n"


def cmd_elenca(radice: Path, scrivi: bool) -> int:
    dati = leggi_registro(radice)
    testo = documento(dati)
    if scrivi:
        if not nel_template(radice):
            raise SystemExit("il documento delle fonti si scrive soltanto nel template")
        (radice / DOCUMENTO_TEMPLATE).write_text(testo, encoding="utf-8", newline="\n")
        print("scritto %s: %d fonti" % (DOCUMENTO_TEMPLATE.as_posix(), len(dati["fonti"])))
    else:
        sys.stdout.write(testo)
    return 0


# --------------------------------------------------------------------------- a monte

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


def contesto_tls():
    """Le radici dei certificati di `certifi` quando c'è, quelle del sistema altrimenti.

    Il 2026-10-21 Docker Hub rispondeva a curl e non a Python su questa macchina, per la stessa
    radice scaduta nell'archivio di sistema descritta in `community-sources/tools/fetch-reddit.py`.
    La verifica non si disattiva mai: si cambia l'elenco delle radici di cui ci si fida.
    """
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def scarica(url: str, github: bool = False):
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "fonti-a-monte (template-claude-developing)"})
    if github:
        req.add_header("Accept", "application/vnd.github+json")
        if token():
            req.add_header("Authorization", "Bearer " + token())
    try:
        with urllib.request.urlopen(req, timeout=25, context=contesto_tls()) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if github and e.code in (403, 429) and e.headers.get("X-RateLimit-Remaining") == "0":
            raise LimiteRaggiunto("limite orario dell'API di GitHub raggiunto; imposta GH_TOKEN o accedi con gh")
        if e.code == 404:
            raise FonteAssente("risponde 404")
        raise


def scarica_testo(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "fonti-a-monte (template-claude-developing)"})
    try:
        with urllib.request.urlopen(req, timeout=25, context=contesto_tls()) as r:
            return r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        if e.code in (404, 410):
            raise FonteAssente("risponde %d" % e.code)
        raise


def voci_del_feed(testo: str) -> list:
    """Le voci di un feed RSS o Atom, dalla più recente: [(istante ISO, data)]."""
    import email.utils
    import xml.etree.ElementTree as ET
    radice = ET.fromstring(testo)
    voci = []
    for el in radice.iter():
        if el.tag.split("}")[-1] not in ("item", "entry"):
            continue
        quando = ""
        for figlio in el:
            nome = figlio.tag.split("}")[-1]
            if nome in ("pubDate", "published", "updated", "date") and (figlio.text or "").strip():
                testo_data = figlio.text.strip()
                try:
                    if nome == "pubDate":
                        d = email.utils.parsedate_to_datetime(testo_data)
                    else:
                        d = dt.datetime.fromisoformat(testo_data.replace("Z", "+00:00"))
                    if d.tzinfo is None:
                        d = d.replace(tzinfo=dt.timezone.utc)
                    quando = d.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                except (ValueError, TypeError):
                    continue
                if nome in ("pubDate", "published"):
                    break
        if quando:
            voci.append((quando, quando[:10]))
    return sorted(voci, reverse=True)


def api(percorso: str):
    return scarica("https://api.github.com/" + percorso, github=True)


def leggi_a_monte(voce: dict) -> dict:
    """Lo stato di una fonte a monte: {versioni: [(id, data)], licenza, archiviato, controllo}."""
    ident = voce.get("via") or voce["id"]
    tipo, nome = tipo_di(ident), nome_di(ident)
    controllo = voce.get("controllo", "")
    if controllo == "manuale" or (tipo in ("winget", "apt") and not voce.get("via")):
        return {"controllo": "manuale", "versioni": []}
    if tipo == "github":
        meta = api("repos/%s" % nome)
        esito = {"licenza": ((meta.get("license") or {}).get("spdx_id") or ""), "archiviato": bool(meta.get("archived"))}
        # GitHub segue in silenzio un repository rinominato o trasferito: lo si dice, perché la scheda
        # porta ancora il nome vecchio (sei casi trovati il 2026-10-21).
        if meta.get("full_name") and meta["full_name"].lower() != nome.lower():
            esito["rinominata"] = meta["full_name"]
        if controllo in ("", "release"):
            try:
                r = api("repos/%s/releases/latest" % nome)
                esito.update(controllo="release", versioni=[(r["tag_name"], (r.get("published_at") or "")[:10])])
                return esito
            except FonteAssente:
                if controllo == "release":
                    esito.update(controllo="release", versioni=[])
                    return esito
        q = {"per_page": str(PAGINA)}
        if voce.get("cartella"):
            q["path"] = voce["cartella"]
        dati = api("repos/%s/commits?%s" % (nome, urllib.parse.urlencode(q)))
        esito.update(controllo="commit", versioni=[(c["sha"], c["commit"]["committer"]["date"][:10]) for c in dati])
        return esito
    if tipo == "npm":
        d = scarica("https://registry.npmjs.org/%s/latest" % nome.replace("/", "%2F"))
        return {"controllo": "versione", "versioni": [(d["version"], "")], "licenza": d.get("license") if isinstance(d.get("license"), str) else "",
                "archiviato": bool(d.get("deprecated"))}
    if tipo == "pypi":
        d = scarica("https://pypi.org/pypi/%s/json" % nome)
        data = (d.get("urls") or [{}])[0].get("upload_time", "")[:10]
        return {"controllo": "versione", "versioni": [(d["info"]["version"], data)], "licenza": "", "archiviato": False}
    if tipo == "crates":
        d = scarica("https://crates.io/api/v1/crates/%s" % nome)
        c = d["crate"]
        return {"controllo": "versione", "versioni": [(c.get("max_stable_version") or c["max_version"], (c.get("updated_at") or "")[:10])],
                "licenza": "", "archiviato": False}
    if tipo == "brew":
        d = scarica("https://formulae.brew.sh/api/formula/%s.json" % nome)
        return {"controllo": "versione", "versioni": [(d["versions"]["stable"], "")], "licenza": d.get("license") or "",
                "archiviato": bool(d.get("deprecated") or d.get("disabled"))}
    if tipo == "hf":
        d = scarica("https://huggingface.co/api/models/%s" % nome)
        return {"controllo": "versione", "versioni": [((d.get("sha") or "")[:12], (d.get("lastModified") or "")[:10])],
                "licenza": ((d.get("cardData") or {}).get("license") or ""), "archiviato": False}
    if tipo == "feed":
        return {"controllo": "versione", "versioni": voci_del_feed(scarica_testo(nome)), "licenza": "", "archiviato": False}
    if tipo == "docker":
        if "." in nome.split("/")[0]:
            raise ValueError("registro di immagini senza interfaccia pubblica: serve via o controllo manuale")
        d = scarica("https://hub.docker.com/v2/repositories/%s/tags?page_size=25&ordering=last_updated" % nome)
        # Solo i tag che sono versioni: `latest` e i suoi alias si spostano a ogni pubblicazione.
        tag = [t for t in d.get("results", []) if re.match(r"v?[0-9]", t.get("name", ""))]
        return {"controllo": "versione", "versioni": [(t["name"], (t.get("last_updated") or "")[:10]) for t in tag], "licenza": "", "archiviato": False}
    raise ValueError("tipo senza controllo automatico: %s" % tipo)


def esamina(voce: dict, leggi=leggi_a_monte, oggi: str = "") -> dict:
    try:
        stato = leggi(voce)
    except LimiteRaggiunto:
        raise
    except FonteAssente as e:
        return {"stato": "sparita", "errore": str(e)}
    except (urllib.error.URLError, OSError, ValueError, KeyError, TypeError) as e:
        return {"stato": "non-raggiunta", "errore": str(e)}
    esito = {"controllo": stato.get("controllo", "")}
    if esito["controllo"] == "manuale":
        noto = voce.get("verificato", "")
        if not noto:
            return dict(esito, stato="mai-verificata", ultimo="", data="")
        giorni = int(voce.get("scadenza", SCADENZA_MANUALE))
        oggi = oggi or dt.date.today().isoformat()
        try:
            scaduta = dt.date.fromisoformat(oggi) - dt.date.fromisoformat(voce.get("data", noto)) > dt.timedelta(days=giorni)
        except ValueError:
            scaduta = True
        return dict(esito, stato="scaduta" if scaduta else "invariata", giorni=giorni)
    versioni = stato.get("versioni") or []
    avvisi = []
    if stato.get("archiviato") and not voce.get("archiviato"):
        avvisi.append("archiviata o deprecata a monte")
    licenza = stato.get("licenza") or ""
    if licenza and voce.get("licenza") and licenza != voce["licenza"]:
        avvisi.append("licenza cambiata da %s a %s" % (voce["licenza"], licenza))
    # Una rinomina già vista e registrata da `segna` non si ripete: un documento datato o copiato da
    # una fonte esterna tiene il nome che aveva, e correggerlo lì romperebbe l'allineamento dei
    # progetti che ne hanno una copia normalizzata (tre conflitti il 2026-10-21).
    if stato.get("rinominata") and stato["rinominata"].lower() != voce.get("rinominata", "").lower():
        avvisi.append("rinominata o trasferita in %s: si corregge il nome nelle schede vive, oppure si registra con segna dove il nome vecchio resta" % stato["rinominata"])
    esito["avvisi"] = avvisi
    if not versioni:
        cosa = "nessuna release" if esito["controllo"] == "release" else "nessuna versione leggibile: spostata o rinominata?"
        return dict(esito, stato="non-raggiunta", errore=cosa)
    ultimo, data = versioni[0]
    noto = voce.get("verificato", "")
    if not noto:
        return dict(esito, stato="mai-verificata", ultimo=ultimo, data=data)
    if ultimo == noto and not avvisi:
        return dict(esito, stato="invariata")
    ids = [i for i, _ in versioni]
    if tipo_di(voce.get("via") or voce["id"]) == "feed":
        # Un feed mostra solo le ultime voci: si contano quelle dopo la verifica, e se lo sono
        # tutte non si sa quante siano davvero.
        nuove = sum(1 for i in ids if i > noto)
        return dict(esito, stato="cambiata", ultimo=ultimo, data=data, feed=True,
                    nuovi=nuove if nuove < len(ids) else None, mostrate=len(ids))
    return dict(esito, stato="cambiata" if ultimo != noto else "avvisi", ultimo=ultimo, data=data,
                nuovi=ids.index(noto) if noto in ids else None)


def breve(identificativo: str) -> str:
    return identificativo[:12] if re.fullmatch(r"[0-9a-f]{40}", identificativo) else identificativo


def dove(v: dict) -> str:
    return v["id"] + ("/" + v["cartella"] if v.get("cartella") else "") + (" (via %s)" % v["via"] if v.get("via") else "")


def esamina_tutte(voci: list, leggi, oggi: str = "") -> tuple:
    """Interroga le fonti in parallelo; al limite dell'API conta quelle rimaste."""
    esiti = {}
    limite = None
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futuri = {pool.submit(esamina, v, leggi, oggi): i for i, v in enumerate(voci)}
        for fut in concurrent.futures.as_completed(futuri):
            try:
                esiti[futuri[fut]] = fut.result()
            except LimiteRaggiunto as x:
                limite = str(x)
    return esiti, limite


def cmd_controlla(radice: Path, rigoroso: bool = False, leggi=leggi_a_monte, oggi: str = "") -> int:
    nuovi, orfani, _ = censisci(radice, scrivi=True)
    for n, f in nuovi:
        print("   +  %s, in %s: aggiunta al registro, da classificare e verificare" % (n, f.relative_to(radice).as_posix()))
    for v in orfani:
        print("   -  %s: non compare più in nessun file, tolta" % v["id"])
    dati = leggi_registro(radice)
    voci = dati["fonti"]
    esiti, limite = esamina_tutte(voci, leggi, oggi)
    da_guardare = 0
    per_ruolo = {}
    cambiato_registro = False
    for i, v in enumerate(voci):
        e = esiti.get(i)
        if e is None:
            continue
        if e.get("controllo") and not v.get("controllo"):
            v["controllo"] = e["controllo"]
            cambiato_registro = True
        if e["stato"] == "invariata":
            continue
        ruolo = v.get("ruolo", DA_CLASSIFICARE)
        etichetta = "%s, %s" % (ruolo, v.get("pacchetto") or "?")
        if e["stato"] == "non-raggiunta":
            print("   ?  %s (%s): non raggiunta, %s" % (etichetta, dove(v), e["errore"]))
            continue
        da_guardare += 1
        per_ruolo[ruolo] = per_ruolo.get(ruolo, 0) + 1
        if e["stato"] == "sparita":
            print("   !  %s (%s): non esiste più a monte o è diventata privata" % (etichetta, dove(v)))
        elif e["stato"] == "mai-verificata":
            ultimo = (" ultima versione %s del %s;" % (breve(e["ultimo"]), e["data"] or "?")) if e.get("ultimo") else ""
            print("   !  %s (%s): mai confrontata con la scheda;%s" % (etichetta, dove(v), ultimo))
        elif e["stato"] == "scaduta":
            print("   !  %s (%s): controllo a mano scaduto, ultimo il %s, scadenza %d giorni" % (etichetta, dove(v), v.get("data", "?"), e["giorni"]))
        else:
            if e["stato"] == "cambiata":
                if e.get("feed"):
                    quanti = "%d voci nuove" % e["nuovi"] if e["nuovi"] is not None else "almeno %d voci nuove" % e["mostrate"]
                elif e["controllo"] in ("release", "versione"):
                    quanti = "nuova versione %s" % e["ultimo"]
                else:
                    quanti = "%d commit" % e["nuovi"] if e["nuovi"] is not None else "più di %d commit" % (PAGINA - 1)
                print("   !  %s (%s): %s dal %s, ultimo del %s" % (etichetta, dove(v), quanti, v.get("data", "?"), e["data"] or "?"))
                base = v.get("via") or v["id"]
                if tipo_di(base) == "github":
                    print("      differenza: https://github.com/%s/compare/%s...%s" % (nome_di(base), breve(v["verificato"]), breve(e["ultimo"])))
            for a in e.get("avvisi", []):
                print("   !  %s (%s): %s" % (etichetta, dove(v), a))
        if v.get("ruolo", DA_CLASSIFICARE) == DA_CLASSIFICARE or not v.get("motivo"):
            print("      senza ruolo o motivo: classifica %s --ruolo ... --motivo \"...\"" % v["id"])
        print("      scheda da rileggere: %s; poi segna %s" % (v.get("scheda") or "?", v["id"]))
    for f in dati["falsi"]:
        try:
            leggi({"id": f["id"], "controllo": ""})
            da_guardare += 1
            print("   !  %s: registrata fra i falsi, ma a monte esiste; va classificata e sorvegliata" % f["id"])
        except (FonteAssente, ValueError, KeyError, TypeError):
            pass
        except (urllib.error.URLError, OSError, LimiteRaggiunto):
            pass
    if cambiato_registro:
        scrivi_registro(radice, dati)
    saltate = len(voci) - len(esiti)
    if limite:
        print("   ?  %s; %d fonti non controllate" % (limite, saltate))
    dettaglio = ", ".join("%s %d" % (k, n) for k, n in sorted(per_ruolo.items()))
    print("fonti a monte: %d da guardare su %d sorvegliate%s%s" % (da_guardare, len(voci),
          " (%s)" % dettaglio if dettaglio else "", ", %d non controllate" % saltate if saltate else ""))
    return 1 if (rigoroso and da_guardare) else 0


# --------------------------------------------------------------------------- registro a mano

def cmd_segna(radice: Path, ident: str, leggi=leggi_a_monte, oggi: str = "") -> str:
    dati = leggi_registro(radice)
    voci = trova(dati, ident)
    if not voci:
        raise SystemExit("fonte non nel registro: %s" % normale(ident))
    oggi = oggi or dt.date.today().isoformat()
    for v in voci:
        if v.get("ruolo", DA_CLASSIFICARE) == DA_CLASSIFICARE or not v.get("motivo", "").strip():
            raise SystemExit("%s non ha ruolo o motivo: prima classifica, poi segna" % v["id"])
        stato = leggi(v)
        v["controllo"] = v.get("controllo") or stato.get("controllo", "")
        if stato.get("controllo") == "manuale":
            v["controllo"] = "manuale"
            v["verificato"] = oggi
        else:
            if not stato.get("versioni"):
                raise SystemExit("nessuna versione leggibile per %s: non segno niente" % v["id"])
            v["verificato"] = stato["versioni"][0][0]
            if stato.get("licenza"):
                v["licenza"] = stato["licenza"]
            if stato.get("archiviato"):
                v["archiviato"] = True
            else:
                v.pop("archiviato", None)
            if stato.get("rinominata"):
                v["rinominata"] = stato["rinominata"]
            else:
                v.pop("rinominata", None)
        v["data"] = oggi
        v.pop("nota-di-prima", None)
    scrivi_registro(radice, dati)
    return voci[0]["verificato"]


def cmd_classifica(radice: Path, ident: str, ruolo: str, motivo: str, controllo: str = "", cartella=None,
                   via: str = "", scadenza: int = 0, pacchetto: str = "", scheda: str = "") -> None:
    if ruolo not in RUOLI:
        raise SystemExit("ruolo sconosciuto %r; i ruoli sono: %s" % (ruolo, ", ".join(RUOLI)))
    if not motivo.strip():
        raise SystemExit("una fonte porta il motivo per cui sta nel template")
    if controllo and controllo not in CONTROLLI:
        raise SystemExit("controllo sconosciuto %r; sono: %s" % (controllo, ", ".join(CONTROLLI)))
    dati = leggi_registro(radice)
    voci = trova(dati, ident)
    if not voci:
        if not (pacchetto and scheda):
            raise SystemExit("%s non è nel registro: per aggiungerla a mano servono --pacchetto e --scheda" % normale(ident))
        voci = [{"id": normale(ident)}]
        dati["fonti"].append(voci[0])
    for v in voci:
        prima = (v.get("controllo"), v.get("cartella", ""), v.get("via", ""))
        v.update({"ruolo": ruolo, "motivo": " ".join(motivo.split())})
        if pacchetto:
            v["pacchetto"] = pacchetto
        if scheda:
            v["scheda"] = scheda
        if controllo:
            v["controllo"] = controllo
        if cartella is not None:
            v["cartella"] = cartella
        if via:
            v["via"] = normale(via)
        if scadenza:
            v["scadenza"] = scadenza
        # Cambiare il modo di controllare rende vecchia la versione verificata.
        if (v.get("controllo"), v.get("cartella", ""), v.get("via", "")) != prima and prima[0]:
            v.pop("verificato", None)
            v.pop("data", None)
    scrivi_registro(radice, dati)


def cmd_falso(radice: Path, ident: str, motivo: str, leggi=leggi_a_monte) -> None:
    if not motivo.strip():
        raise SystemExit("un falso porta il motivo per cui non è una fonte")
    ident = normale(ident)
    try:
        leggi({"id": ident, "controllo": ""})
    except FonteAssente:
        pass
    except (ValueError, KeyError, TypeError):
        pass
    else:
        raise SystemExit("%s esiste a monte: non è un falso, si classifica e si sorveglia" % ident)
    dati = leggi_registro(radice)
    dati["fonti"] = [v for v in dati["fonti"] if chiave(v["id"]) != chiave(ident)]
    dati["falsi"] = [v for v in dati["falsi"] if chiave(v["id"]) != chiave(ident)] + [{"id": ident, "motivo": " ".join(motivo.split())}]
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

    storia = {"github:a/uno": [("c3", "2026-10-20"), ("c2", "2026-10-19"), ("c1", "2026-10-18")],
              "github:b/due": [("x1", "2026-10-01")], "github:r/rel": [("v2", "2026-10-20")],
              "npm:pacco": [("1.2.0", "")], "github:actions/checkout": [("v4", "2026-10-01")], "hf:ente/modello-7b": [("abc123", "2026-10-01")],
              "feed:https://esempio.dev/feed.xml": [("2026-10-01T10:00:00Z", "2026-10-01"), ("2026-09-30T10:00:00Z", "2026-09-30")], "pypi:markitdown": [("0.1.3", "2026-10-01")]}
    release = {"github:r/rel"}
    meta = {"github:a/uno": {"licenza": "MIT", "archiviato": False}}
    limite = {"attivo": False}

    def finta(voce):
        ident = voce.get("via") or voce["id"]
        if limite["attivo"]:
            raise LimiteRaggiunto("limite orario raggiunto")
        if ident == "github:rete/assente":
            raise urllib.error.URLError("rete assente")
        if ident in ("github:via/sparito", "npm:diretto"):
            raise FonteAssente("404")
        if voce.get("controllo") == "manuale" or tipo_di(ident) in ("apt", "winget"):
            return {"controllo": "manuale", "versioni": []}
        if ident not in storia:
            raise FonteAssente("404")
        c = "versione" if tipo_di(ident) != "github" else ("release" if ident in release else "commit")
        return dict(meta.get(ident, {"licenza": "", "archiviato": False}), controllo=c, versioni=storia[ident])

    def esegui(radice, rigoroso=False, oggi=""):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cmd_controlla(radice, rigoroso, finta, oggi)
        return rc, buf.getvalue()

    def zitto(f, *a, **k):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            try:
                rc = f(*a, **k)
            except SystemExit as e:
                rc = "uscita: %s" % e
        return rc, buf.getvalue()

    def classifica_tutte(r):
        for v in leggi_registro(r)["fonti"]:
            cmd_classifica(r, v["id"], "strumenti", "usata dalla prova")

    with tempfile.TemporaryDirectory() as d:
        r = Path(d) / "template"
        (r / MARCATORE_TEMPLATE).parent.mkdir(parents=True)
        (r / MARCATORE_TEMPLATE).write_text("x", encoding="utf-8")
        (r / "README.md").write_text("<!-- sync-readme:packages:start -->\n", encoding="utf-8")
        (r / ".claude" / "skills" / "pipeline-app").mkdir(parents=True)
        (r / ".claude" / "skills" / "pipeline-app" / "RIFERIMENTO.md").write_text("https://github.com/lint/staged\n", encoding="utf-8")
        pa = r / ".claude" / "templates" / "pa"
        (pa / "tools").mkdir(parents=True)
        (pa / "README.md").write_text("Fonte https://github.com/a/uno e `b/due`, guida https://github.com/en/get-started.\n"
                                      "Si installa con `npx -y pacco@latest` e `pip install markitdown[all]`.\n"
                                      "Scouting dal feed https://esempio.dev/feed.xml.\n"
                                      "Convertito dal repository HuggingFace `ente/modello-7b`.\n", encoding="utf-8")
        (pa / "tools" / "conv.py").write_text("import json\nimport markitdown\nfrom yaml import safe_load\nimport conv\n", encoding="utf-8")
        (pa / "tools" / "giro.sh").write_text("command -v jq || echo 'apt install jq'\n", encoding="utf-8")
        (r / ".claude" / "templates" / "mcp.json").write_text('{"s": {"command": "npx",\n "args": ["-y", "@org/server-mcp@1.0"]}}\n', encoding="utf-8")
        (r / ".claude" / "templates" / "PACKAGES.md").write_text(
            "| x | `gh skill install r/rel nome` | `apici/repo` | `templates/pa` | `linux/blk_snap.h` |\n"
            "| y | `docker run --rm -p 1:1 ghcr.io/org/immagine` | `winget install --id Ditta.Programma` |\n", encoding="utf-8")
        (r / ".claude" / "templates" / "pa" / "flusso.yml").write_text("steps:\n  - uses: actions/checkout@v4\n", encoding="utf-8")
        (r / ".claude" / "templates" / "_notes").mkdir()
        (r / ".claude" / "templates" / "_notes" / "n.md").write_text("https://github.com/note/ignorate\n", encoding="utf-8")
        caso("si riconosce il template dal suo marcatore", nel_template(r) and percorso_registro(r) == r / REGISTRO_TEMPLATE)

        nuovi = censisci(r, scrivi=False)[0]
        nomi = [n for n, _ in nuovi]
        caso("il censimento trova URL, comandi d'installazione e nomi fra apici, anche nelle skill del template",
             all(x in nomi for x in ("github:a/uno", "github:apici/repo", "github:b/due", "github:lint/staged", "github:r/rel")))
        caso("il censimento trova i pacchetti npm e PyPI dei comandi, senza versione né extra", "npm:pacco" in nomi and "pypi:markitdown" in nomi)
        caso("il censimento trova i server MCP negli args di una configurazione", "npm:@org/server-mcp" in nomi)
        caso("il censimento trova le librerie importate, con il nome del pacchetto", "pypi:pyyaml" in nomi and "pypi:json" not in nomi and "pypi:conv" not in nomi)
        caso("il censimento trova le GitHub Action dei workflow", "github:actions/checkout" in nomi)
        caso("un modello di Hugging Face è una fonte hf e non un repository GitHub", "hf:ente/modello-7b" in nomi and "github:ente/modello-7b" not in nomi)
        caso("il censimento trova docker, winget e apt, anche negli script", all(x in nomi for x in ("docker:ghcr.io/org/immagine", "winget:Ditta.Programma", "apt:jq")))
        caso("un percorso locale o un file fra apici non è un repository", not any(n.startswith(("github:templates/", "github:linux/")) for n in nomi))
        caso("i percorsi riservati di github.com e le note restano fuori", not any(n.startswith(("github:en/", "github:note/")) for n in nomi))
        caso("censisci --check ferma il commit del template se manca una fonte", zitto(cmd_censisci, r, True)[0] == 1)
        zitto(cmd_censisci, r, False)
        reg = leggi_registro(r)
        uno = trova(reg, "a/uno")[0]
        caso("una fonte nuova entra con pacchetto e scheda, senza ruolo né motivo",
             (uno["pacchetto"], uno["scheda"], uno["ruolo"], uno["motivo"]) == ("pa", ".claude/templates/pa/README.md", DA_CLASSIFICARE, ""))
        caso("un'immagine di ghcr.io segue il repository da cui nasce", trova(reg, "docker:ghcr.io/org/immagine")[0].get("via") == "github:org/immagine")
        caso("dal catalogo il pacchetto si chiama catalogo", trova(reg, "r/rel")[0]["pacchetto"] == "catalogo")
        rc, out = zitto(cmd_censisci, r, True)
        caso("dopo il censimento il commit resta fermo finché le fonti non sono classificate", rc == 1 and "manca ruolo, motivo, verifica" in out)
        caso("segna rifiuta una fonte senza ruolo", "prima classifica" in str(zitto(cmd_segna, r, "a/uno", finta)[0]))
        caso("classifica rifiuta un ruolo fuori dall'insieme", "ruolo sconosciuto" in str(zitto(cmd_classifica, r, "a/uno", "varie", "x")[0]))
        caso("classifica rifiuta una fonte senza motivo", "motivo" in str(zitto(cmd_classifica, r, "a/uno", "strumenti", " ")[0]))
        caso("non esiste più un modo di escludere una fonte vera", "esiste a monte" in str(zitto(cmd_falso, r, "b/due", "solo citato", leggi=finta)[0]))
        classifica_tutte(r)
        rc, out = esegui(r)
        caso("una fonte classificata e mai verificata si segnala", "strumenti, pa (github:a/uno): mai confrontata" in out and rc == 0)
        caso("la prima corsa sceglie da sé release o commit", trova(leggi_registro(r), "r/rel")[0]["controllo"] == "release"
             and trova(leggi_registro(r), "a/uno")[0]["controllo"] == "commit")
        caso("il registro elenca le skill che il template porta nei progetti", "pipeline-app" in leggi_registro(r)["spediti"]["skills"])

        for v in leggi_registro(r)["fonti"]:
            if v["id"] in ("github:apici/repo", "github:lint/staged", "docker:ghcr.io/org/immagine", "npm:@org/server-mcp", "pypi:pyyaml"):
                storia[v.get("via") or v["id"]] = [("z1", "2026-10-01")]
        cmd_classifica(r, "github:a/uno", "strumenti", "usata dalla prova", cartella="skills")
        cmd_segna(r, "a/uno", finta, "2026-10-18")
        reg = leggi_registro(r)
        trova(reg, "a/uno")[0]["verificato"] = "c1"
        scrivi_registro(r, reg)
        storia["github:r/rel"] = [("v1", "2026-10-01")]
        for v in leggi_registro(r)["fonti"]:
            cmd_segna(r, v["id"], finta, "2026-10-01") if v["id"] != "github:a/uno" else None
        storia["github:r/rel"] = [("v2", "2026-10-20")]
        storia["npm:pacco"] = [("1.3.0", "")]
        storia["feed:https://esempio.dev/feed.xml"] = [("2026-10-20T09:00:00Z", "2026-10-20"), ("2026-10-19T09:00:00Z", "2026-10-19"),
                                                       ("2026-10-01T10:00:00Z", "2026-10-01")]
        rc, out = esegui(r, oggi="2026-10-21")
        caso("un repository cambiato si segnala con il numero di commit", "(github:a/uno/skills): 2 commit" in out)
        caso("la differenza si legge dal commit verificato all'ultimo", "compare/c1...c3" in out)
        caso("una release nuova si segnala con il suo tag", "nuova versione v2" in out)
        caso("una versione nuova di un pacchetto npm si segnala", "(npm:pacco): nuova versione 1.3.0" in out)
        caso("un feed di scouting dice quante voci ha pubblicato dopo la verifica", "(feed:https://esempio.dev/feed.xml): 2 voci nuove" in out)
        caso("il censimento trova il feed di una fonte di scouting", trova(leggi_registro(r), "feed:https://esempio.dev/feed.xml") != [])
        caso("il conteggio dice i ruoli", "da guardare su" in out and "strumenti 4" in out)
        caso("il controllo avvisa ma non blocca", rc == 0)
        caso("con --rigoroso un cambiamento blocca", esegui(r, True, "2026-10-21")[0] == 1)
        caso("una fonte a mano entro la scadenza tace", "winget:Ditta.Programma" not in out)
        caso("una fonte a mano oltre la scadenza si segnala", "(winget:Ditta.Programma): controllo a mano scaduto" in esegui(r, oggi="2027-02-01")[1])
        storia["github:a/uno"] = [("c%d" % i, "2026-10-20") for i in range(40, 1, -1)]
        caso("oltre una pagina di commit si dice che sono di più", "più di 29 commit" in esegui(r, oggi="2026-10-21")[1])
        meta["github:a/uno"] = {"licenza": "GPL-3.0", "archiviato": True}
        out = esegui(r, oggi="2026-10-21")[1]
        caso("un repository archiviato si segnala", "archiviata o deprecata a monte" in out)
        caso("una licenza cambiata si segnala", "licenza cambiata da MIT a GPL-3.0" in out)
        meta["github:b/due"] = {"licenza": "", "archiviato": False, "rinominata": "nuovo/due"}
        caso("un repository rinominato si segnala con il nome nuovo", "rinominata o trasferita in nuovo/due" in esegui(r, oggi="2026-10-21")[1])
        cmd_segna(r, "b/due", finta, "2026-10-21")
        caso("una rinomina registrata con segna non si ripete", "rinominata o trasferita" not in esegui(r, oggi="2026-10-21")[1])
        meta.pop("github:b/due")
        for v in leggi_registro(r)["fonti"]:
            cmd_segna(r, v["id"], finta, "2026-10-21")
        v = trova(leggi_registro(r), "a/uno")[0]
        caso("segna registra versione, data, licenza e archiviazione", (v["verificato"], v["data"], v["licenza"], v.get("archiviato")) == ("c40", "2026-10-21", "GPL-3.0", True))
        caso("dopo segna tutto tace", "0 da guardare" in esegui(r, oggi="2026-10-21")[1])
        rc, out = zitto(cmd_censisci, r, True)
        caso("con tutte le fonti classificate e verificate il commit passa", rc == 0 and "tutte classificate e verificate" in out)
        testo_pa = (pa / "README.md").read_text(encoding="utf-8")
        (pa / "README.md").write_text(testo_pa + "Credito: https://github.com/a/uno (licenza Apache-2.0).\n", encoding="utf-8")
        rc, out = zitto(cmd_censisci, r, True)
        caso("una licenza scritta diversa da quella letta a monte ferma il commit", rc == 1 and "dichiara Apache-2.0 per a/uno, a monte è GPL-3.0" in out)
        (pa / "README.md").write_text(testo_pa + "Credito: https://github.com/a/uno (SolidLSP MIT, applicazione GPL-3.0).\n", encoding="utf-8")
        caso("una licenza per componente passa se comprende quella letta a monte", zitto(cmd_censisci, r, True)[0] == 0)
        (pa / "README.md").write_text(testo_pa, encoding="utf-8")
        doc = (r / DOCUMENTO_TEMPLATE).read_text(encoding="utf-8")
        caso("il documento traccia ogni fonte sotto il suo ruolo", "## Strumenti, programmi e servizi" in doc and "github:a/uno" in doc and "| Totale | %d |" % len(leggi_registro(r)["fonti"]) in doc)
        (r / DOCUMENTO_TEMPLATE).write_text(doc + "a mano\n", encoding="utf-8")
        caso("un documento ritoccato a mano ferma il commit", zitto(cmd_censisci, r, True)[0] == 1)
        zitto(cmd_elenca, r, True)

        (pa / "README.md").write_text("Ora cita https://github.com/via/sparito e https://github.com/rete/assente e `b/due`, e npx diretto.\n"
                                      "Si installa con `npx -y pacco@latest` e `pip install markitdown[all]`.\n", encoding="utf-8")
        rc, out = esegui(r, oggi="2026-10-21")
        caso("una fonte tolta dalle schede esce dal registro", "github:a/uno: non compare più" in out and not trova(leggi_registro(r), "a/uno"))
        caso("una parola dopo npx diventa una fonte da guardare, non un'esclusione silenziosa", trova(leggi_registro(r), "npm:diretto") != [])
        zitto(cmd_falso, r, "npm:diretto", "parola della frase «via npx diretto», non un pacchetto", leggi=finta)
        caso("un falso verificato come inesistente esce dalle fonti", not trova(leggi_registro(r), "npm:diretto") and trova(leggi_registro(r), "npm:diretto", "falsi"))
        storia["npm:diretto"] = [("0.0.1", "")]
        def finta_vera(voce):
            return dict(controllo="versione", versioni=[("0.0.1", "")]) if voce["id"] == "npm:diretto" else finta(voce)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cmd_controlla(r, False, finta_vera, "2026-10-21")
        caso("un falso che comincia a esistere si segnala", "npm:diretto: registrata fra i falsi, ma a monte esiste" in buf.getvalue())
        classifica_tutte(r)
        for n in ("via/sparito", "rete/assente"):
            reg = leggi_registro(r)
            trova(reg, n)[0]["verificato"] = "z"
            scrivi_registro(r, reg)
        rc, out = esegui(r, oggi="2026-10-21")
        caso("una fonte sparita si segnala come da guardare", "(github:via/sparito): non esiste più" in out)
        caso("una rete assente si dice e non blocca", "(github:rete/assente): non raggiunta" in out and rc == 0)
        limite["attivo"] = True
        out = esegui(r, oggi="2026-10-21")[1]
        caso("al limite dell'API si dice quante non sono state controllate", "non controllate" in out and "0 da guardare" in out)
        limite["attivo"] = False

        vecchio = Path(d) / "vecchio"
        (vecchio / MARCATORE_TEMPLATE).parent.mkdir(parents=True)
        (vecchio / MARCATORE_TEMPLATE).write_text("x", encoding="utf-8")
        (vecchio / "README.md").write_text("<!-- sync-readme:packages:start -->\n", encoding="utf-8")
        (vecchio / REGISTRO_TEMPLATE).parent.mkdir(parents=True, exist_ok=True)
        (vecchio / REGISTRO_TEMPLATE).write_text(json.dumps({
            "sorvegliati": [{"repo": "r/rel", "cartella": "", "pacchetto": "catalogo", "scheda": "x", "tipo": "release", "verificato": "v1", "data": "2026-10-01"}],
            "citati": [{"repo": "b/due", "motivo": "soltanto citato"}]}), encoding="utf-8")
        reg = leggi_registro(vecchio)
        caso("il registro di prima si legge: i sorvegliati restano verificati", trova(reg, "r/rel")[0]["verificato"] == "v1" and trova(reg, "r/rel")[0]["controllo"] == "release")
        caso("i citati di prima diventano fonti da classificare e verificare", trova(reg, "b/due")[0]["ruolo"] == DA_CLASSIFICARE and not trova(reg, "b/due")[0].get("verificato"))

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
        caso("in un progetto si censisce ciò che il progetto ha installato", [n for n, _ in nuovi] == ["github:mattpocock/skills"])
        caso("un progetto con una copia del prompt d'inizializzazione resta un progetto", not nel_template(prj))
        caso("le skill di sistema e le schede del template non si censiscono nel progetto",
             str(nuovi[0][1]).replace("\\", "/").endswith(".claude/skills/grill-me/SKILL.md"))
        caso("nel progetto il controllo del commit avvisa e non ferma", zitto(cmd_censisci, prj, True)[0] == 0)
        zitto(cmd_censisci, prj, False)
        v = trova(leggi_registro(prj), "mattpocock/skills")[0]
        caso("nel progetto ruolo e motivo vengono dal posto", (v["pacchetto"], v["ruolo"]) == ("skills/grill-me", "skill-e-agenti") and "grill-me" in v["motivo"])

        (r / REGISTRO_TEMPLATE).write_text(json.dumps({"fonti": [{"id": "github:a/uno", "ruolo": "varie"}]}), encoding="utf-8")
        try:
            leggi_registro(r)
            ok = False
        except ValueError:
            ok = True
        caso("un ruolo fuori dall'insieme è un errore del registro", ok)
        (r / REGISTRO_TEMPLATE).write_text(json.dumps([{"repo": "a/uno", "pacchetto": "pa", "scheda": "x"}]), encoding="utf-8")
        caso("il registro nella forma più vecchia, un elenco, si legge ancora", trova(leggi_registro(r), "a/uno") != [])
    print("\n%d casi superati su %d" % (casi - rossi, casi))
    return 1 if rossi else 0


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    p = argparse.ArgumentParser(description="Tutto ciò che il sistema prende da altri, e quando cambia.")
    p.add_argument("--autotest", action="store_true")
    p.add_argument("--radice", default=".", help="radice del template o del progetto")
    sub = p.add_subparsers(dest="comando")
    pc = sub.add_parser("controlla", help="censisce, poi interroga a monte ogni fonte")
    pc.add_argument("--rigoroso", action="store_true")
    pn = sub.add_parser("censisci", help="aggiunge le fonti nuove, toglie quelle sparite, rigenera il documento")
    pn.add_argument("--check", action="store_true", help="non scrive; nel template esce con 1 se il registro è incompleto")
    ps = sub.add_parser("segna", help="registra come verificata la versione di adesso, dopo aver aggiornato la scheda")
    ps.add_argument("id")
    pk = sub.add_parser("classifica", help="assegna ruolo e motivo a una fonte, e se serve il modo di controllarla")
    pk.add_argument("id")
    pk.add_argument("--ruolo", required=True, choices=list(RUOLI))
    pk.add_argument("--motivo", required=True, help="che cosa il template ne prende")
    pk.add_argument("--controllo", default="", choices=["", *CONTROLLI])
    pk.add_argument("--cartella", default=None)
    pk.add_argument("--via", default="", help="un'altra fonte da cui si sa che questa è cambiata")
    pk.add_argument("--scadenza", type=int, default=0, help="giorni fra due controlli a mano")
    pk.add_argument("--pacchetto", default="")
    pk.add_argument("--scheda", default="")
    pf = sub.add_parser("falso", help="una stringa che il censimento scambia per una fonte e che a monte non esiste")
    pf.add_argument("id")
    pf.add_argument("--motivo", required=True)
    pe = sub.add_parser("elenca", help="il documento delle fonti per ruolo")
    pe.add_argument("--scrivi", action="store_true")
    for vecchio in ("cita", "sorveglia"):
        pv = sub.add_parser(vecchio, help="abolito: vedi classifica")
        pv.add_argument("resto", nargs=argparse.REMAINDER)
    a = p.parse_args(argv)
    if a.autotest:
        return autotest()
    radice = Path(a.radice)
    if a.comando == "controlla":
        return cmd_controlla(radice, a.rigoroso)
    if a.comando == "censisci":
        return cmd_censisci(radice, a.check)
    if a.comando == "segna":
        print("verificata %s a %s" % (normale(a.id), breve(cmd_segna(radice, a.id))))
        return 0
    if a.comando == "classifica":
        cmd_classifica(radice, a.id, a.ruolo, a.motivo, a.controllo, a.cartella, a.via, a.scadenza, a.pacchetto, a.scheda)
        print("classificata %s con il ruolo %s; ora va confrontata con la scheda e segnata" % (normale(a.id), a.ruolo))
        return 0
    if a.comando == "falso":
        cmd_falso(radice, a.id, a.motivo)
        print("registrato fra i falsi %s" % normale(a.id))
        return 0
    if a.comando == "elenca":
        return cmd_elenca(radice, a.scrivi)
    if a.comando in ("cita", "sorveglia"):
        print("`%s` non esiste più dal 2026-10-21: ogni fonte del template si sorveglia. Si usa "
              "`classifica <id> --ruolo F --motivo \"...\"`, con --controllo, --cartella o --via per scegliere come." % a.comando)
        return 2
    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
