#!/usr/bin/env python3
"""Crea, aggiorna e verifica un vault Obsidian sopra la memoria e la documentazione di un progetto, senza copiare niente.

Perche' esiste. Il 2026-11-12 il proprietario ha chiesto che la memoria di ogni progetto possa
diventare un vault Obsidian, per leggere la documentazione e le relazioni fra i documenti, con
un insieme di plugin di base uguale a quello dei vault che usa gia'. Il sistema tiene la
memoria sotto `.claude/`, e Obsidian non mostra le cartelle il cui nome comincia con un punto:
aprire la radice del progetto come vault lascerebbe fuori proprio la memoria. Copiarla in una
cartella visibile creerebbe due verita', che e' il difetto che la regola sulla persistenza
esiste per evitare.

Che cosa fa. Crea una cartella di vault, per difetto `_vault/` nella radice del progetto, che
contiene soltanto collegamenti alle cartelle vere e la configurazione di Obsidian:

    _vault/memoria    ->  .claude/memory
    _vault/contesto   ->  .claude/context
    _vault/docs       ->  docs
    _vault/.obsidian/     plugin e impostazioni

Su Windows i collegamenti sono giunzioni di cartella, che non chiedono privilegi; altrove sono
collegamenti simbolici. Cio' che si scrive in Obsidian finisce nel file vero, che resta
versionato dov'e'. La cartella del vault non si versiona: e' una vista, e si ricrea con un
comando. Il comando lo dice e, con --ignora, aggiunge la riga al `.gitignore`.

I plugin. Dal 2026-11-17 i plugin non sono piu' scritti nel codice ma in un elenco versionato,
`plugin-vault.json` accanto alla cartella `tools` del pacchetto, che per ogni plugin fissa il
repository, la versione e l'impronta SHA-256 di ogni file del rilascio. L'elenco arriva ai
progetti con la passata di allineamento; `aggiorna` porta poi un vault, nuovo o esistente, alla
versione fissata. Un progetto aggiunge o toglie plugin per se' in `.claude/vault-plugin.json`,
che la passata non tocca. I file di un plugin si prendono da un vault gia' presente sulla
macchina quando l'impronta coincide, altrimenti, solo con --rete, dal rilascio su GitHub da cui
li scarica anche Obsidian; in entrambi i casi un file la cui impronta non coincide con quella
fissata non si scrive. `cerca` e `valuta` interrogano il catalogo ufficiale dei plugin, e
`fissa` scrive o sposta una voce dell'elenco: e' il passo con cui un plugin entra nella base
dopo una decisione del proprietario.

Uso:
    python tools/vault-progetto.py crea [--radice .] [--cartella _vault] [--da-vault <vault>] [--rete] [--ignora]
    python tools/vault-progetto.py aggiorna [--radice .] [--cartella _vault | --vault <cartella>] [--da-vault <vault>] [--rete]
    python tools/vault-progetto.py verifica [--radice .] [--cartella _vault | --vault <cartella>]
    python tools/vault-progetto.py togli [--radice .] [--cartella _vault]
    python tools/vault-progetto.py cerca <parole> [--limite 15]
    python tools/vault-progetto.py valuta <id> [--obsidian 1.15.1]
    python tools/vault-progetto.py fissa <id> --motivo "..." [--versione X] [--stato base|facoltativo|tolto] [--progetto]
    python tools/vault-progetto.py --autotest

`verifica` esce con 0 se il vault c'e', e' integro e ha i plugin alla versione fissata, 1 se
manca qualcosa, e lo elenca. `togli` rimuove i collegamenti e la configurazione, mai il
contenuto delle cartelle vere. `aggiorna` non tocca mai `data.json`, cioe' le impostazioni che
chi usa il vault ha dato a un plugin, ne' i plugin che l'elenco non nomina.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

COLLEGAMENTI = [("memoria", ".claude/memory"), ("contesto", ".claude/context"), ("docs", "docs")]
CORE = ["file-explorer", "global-search", "switcher", "graph", "backlink", "canvas", "outgoing-link", "tag-pane",
        "properties", "page-preview", "note-composer", "command-palette", "editor-status", "bookmarks", "outline",
        "word-count", "file-recovery"]
RIFERIMENTO = Path.home() / ".config" / "vault-riferimento.txt"
NOME_ELENCO = "plugin-vault.json"
ELENCO_NEL_PROGETTO = ".claude/templates/vault-di-progetto/" + NOME_ELENCO
SCELTE_DEL_PROGETTO = ".claude/vault-plugin.json"
STATI = ("base", "facoltativo", "tolto")
RAW = "https://raw.githubusercontent.com/obsidianmd/obsidian-releases/master/"
CATALOGO, STATISTICHE, RIMOSSI = RAW + "community-plugins.json", RAW + "community-plugin-stats.json", RAW + "community-plugins-removed.json"
RILASCIO = "https://github.com/{repo}/releases/download/{versione}/{file}"
API = "https://api.github.com/repos/{repo}"
FILE_RILASCIO = ["main.js", "manifest.json", "styles.css"]
GIORNI_FRESCHEZZA = 365


# ---------------------------------------------------------------- rete e impronte

def scarica_dalla_rete(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "vault-progetto", "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def impronta(dati: bytes) -> str:
    return hashlib.sha256(dati).hexdigest()


def leggi_json(p: Path, difetto=None):
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return difetto


def scrivi_json(p: Path, dato) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(dato, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


# ---------------------------------------------------------------- collegamenti

def e_collegamento(p: Path) -> bool:
    """Vero per un collegamento simbolico e per una giunzione di Windows."""
    if p.is_symlink():
        return True
    try:
        return bool(getattr(os.lstat(p), "st_file_attributes", 0) & 0x400)  # FILE_ATTRIBUTE_REPARSE_POINT
    except OSError:
        return False


def collega(nome: Path, bersaglio: Path) -> None:
    if os.name == "nt":
        r = subprocess.run(["cmd", "/c", "mklink", "/J", str(nome), str(bersaglio)], capture_output=True, text=True)
        if r.returncode != 0:
            raise OSError("giunzione non creata: " + (r.stdout + r.stderr).strip())
    else:
        os.symlink(bersaglio, nome, target_is_directory=True)


def scollega(p: Path) -> None:
    """Toglie il collegamento e mai cio' a cui punta."""
    if not e_collegamento(p):
        raise OSError("%s non e' un collegamento: non lo tocco" % p)
    if os.name == "nt" and not p.is_symlink():
        os.rmdir(p)
    else:
        os.unlink(p)


def vault_di_riferimento(esplicito: str | None) -> Path | None:
    candidati = [esplicito] if esplicito else []
    try:
        candidati += [r.split("#", 1)[0].strip() for r in RIFERIMENTO.read_text(encoding="utf-8-sig").splitlines()]
    except OSError:
        pass
    for c in candidati:
        if c and (Path(c) / ".obsidian" / "plugins").is_dir():
            return Path(c)
    return None


# ---------------------------------------------------------------- elenco dei plugin

def percorso_elenco(radice: Path) -> Path | None:
    """L'elenco consegnato dalla passata nel progetto, oppure quello accanto allo strumento."""
    for c in (radice / ELENCO_NEL_PROGETTO, Path(__file__).resolve().parent.parent / NOME_ELENCO):
        if c.is_file():
            return c
    return None


def plugin_voluti(radice: Path) -> tuple[dict, set, list]:
    """(voluti per id, ids da disattivare, avvisi) dall'elenco del template piu' le scelte del progetto."""
    avvisi = []
    p = percorso_elenco(radice)
    elenco = leggi_json(p, {}) if p else {}
    if not p:
        avvisi.append("elenco dei plugin %s non trovato: nessun plugin gestito" % NOME_ELENCO)
    voci = {v["id"]: v for v in elenco.get("plugin", [])}
    scelte = leggi_json(radice / SCELTE_DEL_PROGETTO, {}) or {}
    for v in scelte.get("plugin", []):
        voci[v["id"]] = dict(v, stato=v.get("stato", "base"))
    aggiungi, togli = set(scelte.get("aggiungi", [])), set(scelte.get("togli", []))
    for i in aggiungi - set(voci):
        avvisi.append("il progetto chiede %s, che l'elenco non conosce: va fissato con `fissa`" % i)
    voluti = {i: v for i, v in voci.items()
              if i not in togli and (v.get("stato") == "base" or (v.get("stato") == "facoltativo" and i in aggiungi))}
    via = {i for i, v in voci.items() if v.get("stato") == "tolto"} | togli
    return voluti, via - set(voluti), avvisi


def versione_installata(conf: Path, ident: str) -> str | None:
    m = leggi_json(conf / "plugins" / ident / "manifest.json")
    return m.get("version") if isinstance(m, dict) else None


def gia_alla_versione(conf: Path, voce: dict) -> bool:
    d = conf / "plugins" / voce["id"]
    for nome, h in voce.get("sha256", {}).items():
        try:
            if impronta((d / nome).read_bytes()) != h:
                return False
        except OSError:
            return False
    return bool(voce.get("sha256"))


def procura(voce: dict, origine: Path | None, rete: bool, scarica) -> tuple[dict | None, str]:
    """I byte di ogni file del plugin, verificati sull'impronta fissata; (None, motivo) se non si puo'."""
    attese = voce.get("sha256") or {}
    if not attese:
        return None, "voce senza impronte: va fissata con `fissa`"
    da_vault = {}
    if origine:
        d = origine / ".obsidian" / "plugins" / voce["id"]
        for nome, h in attese.items():
            try:
                b = (d / nome).read_bytes()
            except OSError:
                break
            if impronta(b) != h:
                break
            da_vault[nome] = b
    if len(da_vault) == len(attese):
        return da_vault, "dal vault di riferimento"
    if not rete:
        return None, "la versione %s non e' nel vault di riferimento: rilanciare con --rete per prenderla dal rilascio" % voce.get("versione")
    presi = {}
    for nome, h in attese.items():
        url = RILASCIO.format(repo=voce["repo"], versione=voce["versione"], file=nome)
        try:
            b = scarica(url)
        except Exception as err:  # rete assente, 404, tempo scaduto
            return None, "%s non scaricato: %s" % (nome, err)
        if impronta(b) != h:
            return None, "%s scaricato ha un'impronta diversa da quella fissata: non lo scrivo" % nome
        presi[nome] = b
    return presi, "dal rilascio %s" % voce["versione"]


def allinea_plugin(conf: Path, voluti: dict, via: set, origine: Path | None, rete: bool, scarica) -> tuple[list, list]:
    """Installa o aggiorna i plugin voluti, disattiva quelli tolti; (righe, mancati)."""
    righe, mancati = [], []
    attivi_file = conf / "community-plugins.json"
    attivi = leggi_json(attivi_file, [])
    if not isinstance(attivi, list):
        attivi = []
    for ident, voce in voluti.items():
        prima = versione_installata(conf, ident)
        if gia_alla_versione(conf, voce):
            righe.append("%s %s a posto" % (ident, voce.get("versione")))
        else:
            file, come = procura(voce, origine, rete, scarica)
            if file is None:
                mancati.append(ident)
                righe.append("%s non installato: %s" % (ident, come))
                continue
            dest = conf / "plugins" / ident
            dest.mkdir(parents=True, exist_ok=True)
            for nome, b in file.items():
                (dest / nome).write_bytes(b)
            if not prima:
                fatto = "installato " + voce["versione"]
            elif prima == voce["versione"]:
                fatto = "riscritto alla " + prima + ": i file installati non coincidevano con quelli del rilascio fissato,"
            else:
                fatto = "aggiornato da " + prima + " a " + voce["versione"]
            righe.append("%s %s %s" % (ident, fatto, come))
        if ident not in attivi:
            attivi.append(ident)
    for ident in sorted(via):
        if ident in attivi:
            attivi.remove(ident)
            righe.append("%s disattivato: tolto dall'elenco; la cartella resta, con le sue impostazioni" % ident)
    scrivi_json(attivi_file, attivi)
    return righe, mancati


# ---------------------------------------------------------------- azioni sul vault

def crea(radice: Path, cartella: str, da_vault: str | None, ignora: bool, rete: bool = False, scarica=scarica_dalla_rete) -> list:
    righe = []
    vault = radice / cartella
    vault.mkdir(exist_ok=True)
    for nome, vero in COLLEGAMENTI:
        bersaglio, link = radice / vero, vault / nome
        if not bersaglio.is_dir():
            righe.append("saltato %s: %s non esiste in questo progetto" % (nome, vero))
            continue
        if link.exists() or e_collegamento(link):
            if not e_collegamento(link):
                raise OSError("%s esiste e non e' un collegamento: non lo sostituisco" % link)
            righe.append("gia' presente %s" % nome)
            continue
        collega(link, bersaglio.resolve())
        righe.append("collegato %s -> %s" % (nome, vero))
    conf = vault / ".obsidian"
    conf.mkdir(exist_ok=True)
    for nome, dato in (("core-plugins.json", {n: True for n in CORE}),
                       ("app.json", {"alwaysUpdateLinks": True, "newLinkFormat": "relative", "useMarkdownLinks": True})):
        if not (conf / nome).exists():
            scrivi_json(conf / nome, dato)
    voluti, via, avvisi = plugin_voluti(radice)
    righe += avvisi
    r, mancati = allinea_plugin(conf, voluti, via, vault_di_riferimento(da_vault), rete, scarica)
    righe += r
    if mancati:
        righe.append("DA FARE: %d plugin non installati; `aggiorna --rete` li prende dal rilascio fissato" % len(mancati))
    riga = cartella.strip("/") + "/"
    gi = radice / ".gitignore"
    presenti = gi.read_text(encoding="utf-8-sig").splitlines() if gi.is_file() else []
    gia = subprocess.run(["git", "-C", str(radice), "check-ignore", "-q", riga + "x"], capture_output=True).returncode == 0
    if gia or riga in [r.strip() for r in presenti] or ("/" + riga) in [r.strip() for r in presenti]:
        righe.append(".gitignore ignora gia' %s" % riga)
    elif ignora:
        with gi.open("a", encoding="utf-8", newline="\n") as out:
            out.write(("" if not presenti or presenti[-1] == "" else "\n") + "# vista Obsidian del progetto: si ricrea con vault-progetto.py crea\n" + riga + "\n")
        righe.append("aggiunta al .gitignore la riga %s" % riga)
    else:
        righe.append("DA FARE: %s non e' ignorata da git; aggiungere la riga al .gitignore o rilanciare con --ignora" % riga)
    return righe


def aggiorna(radice: Path, vault: Path, da_vault: str | None, rete: bool, scarica=scarica_dalla_rete) -> tuple[list, int]:
    conf = vault / ".obsidian"
    if not conf.is_dir():
        raise OSError("%s non e' un vault: manca .obsidian (per crearlo: crea)" % vault)
    voluti, via, avvisi = plugin_voluti(radice)
    righe, mancati = allinea_plugin(conf, voluti, via, vault_di_riferimento(da_vault), rete, scarica)
    return avvisi + righe, len(mancati)


def verifica(radice: Path, cartella: str, vault: Path | None = None) -> list:
    """I difetti del vault; lista vuota se e' integro."""
    vault = vault or radice / cartella
    if not (vault / ".obsidian").is_dir():
        return ["il vault non esiste: %s" % vault]
    guai = []
    if vault == radice / cartella:
        for nome, vero in COLLEGAMENTI:
            link, bersaglio = vault / nome, radice / vero
            if not bersaglio.is_dir():
                continue
            if not e_collegamento(link):
                guai.append("%s non e' un collegamento a %s" % (nome, vero))
            elif not link.is_dir() or link.resolve() != bersaglio.resolve():
                guai.append("%s e' un collegamento rotto o punta altrove" % nome)
        r = subprocess.run(["git", "-C", str(radice), "check-ignore", "-q", cartella.strip("/") + "/x"], capture_output=True)
        if r.returncode == 1:
            guai.append("%s non e' ignorata da git: una vista non si versiona" % cartella)
    conf = vault / ".obsidian"
    attivi = leggi_json(conf / "community-plugins.json", []) or []
    voluti, via, _ = plugin_voluti(radice)
    for ident, voce in voluti.items():
        installata = versione_installata(conf, ident)
        if not installata:
            guai.append("plugin non installato: %s (lanciare aggiorna)" % ident)
        elif not gia_alla_versione(conf, voce):
            guai.append(("plugin da aggiornare: %s %s, fissata %s (lanciare aggiorna)" if installata != voce.get("versione") else
                         "plugin %s %s con file diversi dal rilascio fissato %s (lanciare aggiorna)") % (ident, installata, voce.get("versione")))
        elif ident not in attivi:
            guai.append("plugin installato ma non attivo: %s" % ident)
    for ident in sorted(via & set(attivi)):
        guai.append("plugin tolto dall'elenco ma ancora attivo: %s (lanciare aggiorna)" % ident)
    return guai


def togli(radice: Path, cartella: str) -> list:
    vault = radice / cartella
    righe = []
    for nome, _ in COLLEGAMENTI:
        link = vault / nome
        if e_collegamento(link):
            scollega(link)
            righe.append("tolto il collegamento %s" % nome)
        elif link.exists():
            raise OSError("%s non e' un collegamento: mi fermo senza toccare niente altro" % link)
    if (vault / ".obsidian").is_dir():
        shutil.rmtree(vault / ".obsidian")
        righe.append("tolta la configurazione")
    try:
        vault.rmdir()
        righe.append("tolta la cartella " + cartella)
    except OSError:
        righe.append("la cartella %s contiene altro e resta" % cartella)
    return righe


# ---------------------------------------------------------------- catalogo ufficiale

def catalogo(scarica) -> tuple[list, dict, dict]:
    voci = json.loads(scarica(CATALOGO))
    stat = json.loads(scarica(STATISTICHE))
    rimossi = {r["id"]: r.get("reason", "") for r in json.loads(scarica(RIMOSSI))}
    return voci, stat, rimossi


def data_ms(ms) -> str:
    return dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc).date().isoformat() if ms else "?"


def cerca(parole: list, limite: int, scarica=scarica_dalla_rete) -> list:
    voci, stat, rimossi = catalogo(scarica)
    chiavi = [p.lower() for p in parole]
    trovati = [v for v in voci if all(k in (v["id"] + " " + v["name"] + " " + v.get("description", "")).lower() for k in chiavi)]
    trovati.sort(key=lambda v: -stat.get(v["id"], {}).get("downloads", 0))
    righe = []
    for v in trovati[:limite]:
        s = stat.get(v["id"], {})
        righe.append("%-28s %9s scaricamenti, aggiornato %s, %s%s\n    %s" % (
            v["id"], s.get("downloads", "?"), data_ms(s.get("updated")), v["repo"],
            "  RIMOSSO DAL CATALOGO: " + rimossi[v["id"]] if v["id"] in rimossi else "", v.get("description", "")[:150]))
    righe.append("%d trovati su %d nel catalogo; mostrati i primi %d per scaricamenti" % (len(trovati), len(voci), min(limite, len(trovati))))
    return righe


def versione_obsidian() -> str | None:
    """La versione installata, dal nome del pacchetto applicativo che Obsidian tiene nei dati utente."""
    base = Path(os.environ.get("APPDATA", Path.home() / ".config")) / "obsidian"
    trovate = []
    for p in base.glob("obsidian-*.asar"):
        m = re.match(r"obsidian-(\d+(?:\.\d+)+)\.asar$", p.name)
        if m:
            trovate.append(tuple(int(x) for x in m.group(1).split(".")))
    return ".".join(map(str, max(trovate))) if trovate else None


def come_tupla(v: str | None) -> tuple:
    return tuple(int(x) for x in re.findall(r"\d+", v or ""))


def valuta(ident: str, obsidian: str | None, scarica=scarica_dalla_rete, oggi: dt.date | None = None) -> tuple[list, bool, dict]:
    """(righe, idoneo, dati) sui criteri misurabili; l'utilita' per il progetto resta un giudizio del proprietario."""
    oggi = oggi or dt.date.today()
    voci, stat, rimossi = catalogo(scarica)
    voce = next((v for v in voci if v["id"] == ident), None)
    if not voce:
        return ["%s non e' nel catalogo ufficiale dei plugin" % ident], False, {}
    repo = voce["repo"]
    rel = json.loads(scarica(API.format(repo=repo) + "/releases/latest"))
    versione = rel.get("tag_name", "")
    try:
        manifest = json.loads(scarica(RILASCIO.format(repo=repo, versione=versione, file="manifest.json")))
    except Exception:
        manifest = {}
    try:
        licenza = (json.loads(scarica(API.format(repo=repo) + "/license")).get("license") or {}).get("spdx_id")
    except Exception:
        licenza = None
    s = stat.get(ident, {})
    pubblicato = (rel.get("published_at") or "")[:10]
    giorni = (oggi - dt.date.fromisoformat(pubblicato)).days if pubblicato else None
    minimo = manifest.get("minAppVersion")
    criteri = [
        ("nel catalogo ufficiale e non rimosso", ident not in rimossi, rimossi.get(ident, "")),
        ("licenza letta a monte", bool(licenza) and licenza != "NOASSERTION", licenza or "non dichiarata"),
        ("ultimo rilascio entro %d giorni" % GIORNI_FRESCHEZZA, giorni is not None and giorni <= GIORNI_FRESCHEZZA, "%s, %s giorni fa" % (pubblicato or "?", giorni)),
        ("compatibile con l'Obsidian installato", bool(obsidian) and come_tupla(minimo) <= come_tupla(obsidian), "chiede %s, installato %s" % (minimo, obsidian or "non rilevato")),
        ("rilascio con main.js e manifest.json", {"main.js", "manifest.json"} <= {a["name"] for a in rel.get("assets", [])}, versione),
    ]
    righe = ["%s, %s, %s scaricamenti, repository %s" % (ident, voce["name"], s.get("downloads", "?"), repo), voce.get("description", "")]
    for nome, ok, dettaglio in criteri:
        righe.append(("ok    " if ok else "NO    ") + nome + (": " + str(dettaglio) if dettaglio else ""))
    idoneo = all(ok for _, ok, _ in criteri)
    righe.append("esito: " + ("idoneo sui criteri misurabili; se entra nella base lo decide il proprietario, con `fissa --motivo`" if idoneo else "non idoneo come plugin di base"))
    dati = {"id": ident, "nome": voce["name"], "repo": repo, "versione": versione, "minAppVersion": minimo, "licenza": licenza,
            "file": [a["name"] for a in rel.get("assets", []) if a["name"] in FILE_RILASCIO]}
    return righe, idoneo, dati


def fissa(radice: Path, ident: str, motivo: str, stato: str, versione: str | None, progetto: bool,
          scarica=scarica_dalla_rete, oggi: dt.date | None = None) -> list:
    """Scrive la voce del plugin, con le impronte del rilascio, nell'elenco del template o nelle scelte del progetto."""
    if stato not in STATI:
        raise ValueError("stato sconosciuto: %s" % stato)
    righe, idoneo, dati = valuta(ident, versione_obsidian(), scarica, oggi)
    if not dati:
        raise ValueError(righe[0])
    if not idoneo and stato == "base":
        raise ValueError("non entra nella base: " + "; ".join(r[6:] for r in righe if r.startswith("NO")))
    versione = versione or dati["versione"]
    impronte = {}
    for nome in dati["file"]:
        impronte[nome] = impronta(scarica(RILASCIO.format(repo=dati["repo"], versione=versione, file=nome)))
    voce = {"id": ident, "nome": dati["nome"], "repo": dati["repo"], "versione": versione, "minAppVersion": dati["minAppVersion"],
            "licenza": dati["licenza"], "stato": stato, "motivo": motivo, "fissato_il": (oggi or dt.date.today()).isoformat(), "sha256": impronte}
    dest = radice / SCELTE_DEL_PROGETTO if progetto else (percorso_elenco(radice) or radice / ELENCO_NEL_PROGETTO)
    dato = leggi_json(dest, {}) or {}
    if not progetto:
        dato.setdefault("schema", "vault-plugin-1")
    voci = [v for v in dato.get("plugin", []) if v["id"] != ident] + [voce]
    dato["plugin"] = sorted(voci, key=lambda v: v["id"])
    scrivi_json(dest, dato)
    return righe + ["scritta la voce %s %s, stato %s, in %s" % (ident, versione, stato, dest)]


# ---------------------------------------------------------------- prove

def autotest() -> int:
    import tempfile
    esiti = []

    def caso(nome, ok, dettaglio=""):
        esiti.append(ok)
        print(("ok    " if ok else "ROSSO ") + nome + ("" if ok else "  " + str(dettaglio)))

    def rilascio(ident, versione):
        return {"main.js": ("// %s %s\n" % (ident, versione)).encode(), "manifest.json": json.dumps({"id": ident, "version": versione}).encode()}

    def voce(ident, versione, stato="base"):
        return {"id": ident, "repo": "autore/" + ident, "versione": versione, "stato": stato, "motivo": "prova",
                "sha256": {n: impronta(b) for n, b in rilascio(ident, versione).items()}}

    rete = {}
    chiamate = []

    def finta_rete(url):
        chiamate.append(url)
        if url not in rete:
            raise OSError("404 " + url)
        return rete[url]

    for ident, versione in (("alfa", "2.0"), ("beta", "1.0"), ("gamma", "3.0")):
        for nome, b in rilascio(ident, versione).items():
            rete[RILASCIO.format(repo="autore/" + ident, versione=versione, file=nome)] = b

    with tempfile.TemporaryDirectory(prefix="vault-") as tmp:
        base = Path(tmp)
        prj, rif = base / "progetto", base / "riferimento"
        (prj / ".claude/memory").mkdir(parents=True)
        (prj / "docs").mkdir()
        (prj / ".claude/memory/index.md").write_text("stato\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(prj), "init", "-q"], capture_output=True)
        elenco = prj / ELENCO_NEL_PROGETTO
        scrivi_json(elenco, {"schema": "vault-plugin-1", "plugin": [voce("alfa", "2.0"), voce("beta", "1.0"), voce("gamma", "3.0", "facoltativo")]})
        for ident, versione in (("alfa", "2.0"), ("beta", "0.9")):
            d = rif / ".obsidian/plugins" / ident
            d.mkdir(parents=True)
            for nome, b in rilascio(ident, versione).items():
                (d / nome).write_bytes(b)
        righe = crea(prj, "_vault", str(rif), ignora=True, rete=False, scarica=finta_rete)
        v = prj / "_vault"
        conf = v / ".obsidian"
        caso("la memoria si vede dal vault attraverso un collegamento", e_collegamento(v / "memoria") and (v / "memoria/index.md").read_text(encoding="utf-8") == "stato\n", righe)
        caso("una cartella che il progetto non ha si salta e lo si dice", not (v / "contesto").exists() and any("saltato contesto" in r for r in righe), righe)
        (v / "memoria/nuova.md").write_text("scritta dal vault\n", encoding="utf-8")
        caso("cio' che si scrive nel vault finisce nel file vero", (prj / ".claude/memory/nuova.md").is_file())
        caso("un plugin con l'impronta giusta si copia dal vault di riferimento senza rete",
             versione_installata(conf, "alfa") == "2.0" and any("alfa" in r and "dal vault di riferimento" in r for r in righe) and not chiamate, righe)
        caso("negativo: una versione diversa nel riferimento non si copia senza --rete, e lo si dice",
             versione_installata(conf, "beta") is None and any("beta non installato" in r and "--rete" in r for r in righe), righe)
        caso("un plugin facoltativo non si installa se il progetto non lo chiede", not (conf / "plugins/gamma").exists())
        caso("con --ignora la cartella del vault entra nel .gitignore", "_vault/" in (prj / ".gitignore").read_text(encoding="utf-8"))
        guai = verifica(prj, "_vault")
        caso("la verifica segnala il plugin che manca, e solo quello", guai == ["plugin non installato: beta (lanciare aggiorna)"], guai)
        r, n = aggiorna(prj, v, str(rif), rete=True, scarica=finta_rete)
        caso("aggiorna con --rete prende dal rilascio la versione fissata", n == 0 and versione_installata(conf, "beta") == "1.0" and verifica(prj, "_vault") == [], r)
        (conf / "plugins/alfa/data.json").write_text('{"mio": 1}', encoding="utf-8")
        scrivi_json(elenco, {"schema": "vault-plugin-1", "plugin": [voce("alfa", "2.1"), voce("beta", "1.0", "tolto"), voce("gamma", "3.0", "facoltativo")]})
        for nome, b in rilascio("alfa", "2.1").items():
            rete[RILASCIO.format(repo="autore/alfa", versione="2.1", file=nome)] = b
        guai = verifica(prj, "_vault")
        caso("dopo una passata che sposta la versione, la verifica dice che cosa aggiornare",
             "plugin da aggiornare: alfa 2.0, fissata 2.1 (lanciare aggiorna)" in guai and "plugin tolto dall'elenco ma ancora attivo: beta (lanciare aggiorna)" in guai, guai)
        r, n = aggiorna(prj, v, None, rete=True, scarica=finta_rete)
        attivi = leggi_json(conf / "community-plugins.json")
        caso("aggiorna porta il plugin alla nuova versione e non tocca le sue impostazioni",
             versione_installata(conf, "alfa") == "2.1" and (conf / "plugins/alfa/data.json").read_text(encoding="utf-8") == '{"mio": 1}', r)
        caso("un plugin tolto si disattiva e la sua cartella resta", "beta" not in attivi and (conf / "plugins/beta/main.js").is_file(), attivi)
        (conf / "plugins/mio").mkdir()
        attivi.append("mio")
        scrivi_json(conf / "community-plugins.json", attivi)
        scrivi_json(prj / SCELTE_DEL_PROGETTO, {"aggiungi": ["gamma"], "togli": ["alfa"]})
        r, n = aggiorna(prj, v, None, rete=True, scarica=finta_rete)
        attivi = leggi_json(conf / "community-plugins.json")
        caso("le scelte del progetto aggiungono un facoltativo e tolgono un plugin di base",
             "gamma" in attivi and "alfa" not in attivi and versione_installata(conf, "gamma") == "3.0", (attivi, r))
        caso("un plugin che l'elenco non nomina resta attivo e intatto", "mio" in attivi and (conf / "plugins/mio").is_dir(), attivi)
        rete[RILASCIO.format(repo="autore/alfa", versione="2.1", file="main.js")] = b"// manomesso\n"
        shutil.rmtree(conf / "plugins/alfa")
        (prj / SCELTE_DEL_PROGETTO).unlink()
        r, n = aggiorna(prj, v, None, rete=True, scarica=finta_rete)
        caso("negativo: un file scaricato con un'impronta diversa non si scrive", n == 1 and not (conf / "plugins/alfa").exists()
             and any("impronta diversa" in x for x in r), r)
        prima = sorted(p.name for p in conf.iterdir())
        crea(prj, "_vault", None, ignora=True, rete=False, scarica=finta_rete)
        caso("rilanciare crea non duplica e non sovrascrive", sorted(p.name for p in conf.iterdir()) == prima
             and (prj / ".gitignore").read_text(encoding="utf-8").count("_vault/") == 1)
        togli(prj, "_vault")
        caso("togliere il vault non tocca la memoria vera", not v.exists() and (prj / ".claude/memory/index.md").is_file() and (prj / ".claude/memory/nuova.md").is_file())
        caso("negativo: senza vault la verifica lo dice", verifica(prj, "_vault")[0].startswith("il vault non esiste"))
        (prj / "_vault").mkdir()
        (prj / "_vault/memoria").mkdir()
        try:
            crea(prj, "_vault", None, ignora=False, scarica=finta_rete)
            rifiutato = False
        except OSError:
            rifiutato = True
        caso("negativo: una cartella vera al posto del collegamento non si sostituisce", rifiutato)
        altro = base / "senza"
        (altro / "docs").mkdir(parents=True)
        subprocess.run(["git", "-C", str(altro), "init", "-q"], capture_output=True)
        scrivi_json(altro / ELENCO_NEL_PROGETTO, {"plugin": [voce("alfa", "2.0")]})
        r2 = crea(altro, "_vault", str(base / "inesistente"), ignora=False, rete=False, scarica=finta_rete)
        caso("senza riferimento e senza rete scrive la configurazione e dice che cosa manca",
             any(r.startswith("DA FARE: 1 plugin") for r in r2) and leggi_json(altro / "_vault/.obsidian/community-plugins.json") == [], r2)
        caso("senza --ignora dichiara il da fare e non tocca il .gitignore", any("non e' ignorata da git" in r for r in r2) and not (altro / ".gitignore").exists(), r2)

        oggi = dt.date(2026, 11, 17)
        rete[CATALOGO] = json.dumps([{"id": "alfa", "name": "Alfa", "repo": "autore/alfa", "description": "grafo dei documenti"},
                                     {"id": "delta", "name": "Delta", "repo": "autore/delta", "description": "grafo vecchio"},
                                     {"id": "zeta", "name": "Zeta", "repo": "autore/zeta", "description": "altro"}]).encode()
        rete[STATISTICHE] = json.dumps({"alfa": {"downloads": 50, "updated": 0}, "delta": {"downloads": 900, "updated": 0}}).encode()
        rete[RIMOSSI] = json.dumps([{"id": "delta", "reason": "Archived repository"}]).encode()
        r = cerca(["grafo"], 5, scarica=finta_rete)
        caso("cerca filtra per parole, ordina per scaricamenti e segnala un plugin rimosso",
             r[0].startswith("delta") and "RIMOSSO" in r[0] and r[1].startswith("alfa") and r[-1].startswith("2 trovati"), r)
        rete[API.format(repo="autore/alfa") + "/releases/latest"] = json.dumps({"tag_name": "2.1", "published_at": "2026-10-01T00:00:00Z",
                                                                               "assets": [{"name": "main.js"}, {"name": "manifest.json"}]}).encode()
        rete[RILASCIO.format(repo="autore/alfa", versione="2.1", file="manifest.json")] = json.dumps({"id": "alfa", "version": "2.1", "minAppVersion": "1.5.0"}).encode()
        rete[RILASCIO.format(repo="autore/alfa", versione="2.1", file="main.js")] = rilascio("alfa", "2.1")["main.js"]
        rete[API.format(repo="autore/alfa") + "/license"] = json.dumps({"license": {"spdx_id": "MIT"}}).encode()
        righe, idoneo, _ = valuta("alfa", "1.15.1", scarica=finta_rete, oggi=oggi)
        caso("valuta dichiara idoneo un plugin che passa tutti i criteri misurabili", idoneo and righe[-1].startswith("esito: idoneo"), righe)
        righe, idoneo, _ = valuta("alfa", "1.4.0", scarica=finta_rete, oggi=oggi)
        caso("negativo: valuta respinge un plugin che chiede un Obsidian piu' nuovo", not idoneo and any(r.startswith("NO    compatibile") for r in righe), righe)
        righe, idoneo, _ = valuta("alfa", "1.15.1", scarica=finta_rete, oggi=dt.date(2028, 1, 1))
        caso("negativo: valuta respinge un plugin fermo da piu' di un anno", not idoneo and any(r.startswith("NO    ultimo rilascio") for r in righe), righe)
        caso("negativo: un plugin fuori dal catalogo non si valuta", valuta("omega", "1.15.1", scarica=finta_rete)[1] is False)
        rete[API.format(repo="autore/delta") + "/releases/latest"] = rete[API.format(repo="autore/alfa") + "/releases/latest"]
        rete[API.format(repo="autore/delta") + "/license"] = rete[API.format(repo="autore/alfa") + "/license"]
        righe, idoneo, _ = valuta("delta", "1.15.1", scarica=finta_rete, oggi=oggi)
        caso("negativo: valuta respinge un plugin tolto dal catalogo, anche se il resto passa",
             not idoneo and any(r.startswith("NO    nel catalogo") and "Archived" in r for r in righe), righe)
        fis = base / "fissa"
        (fis / ".claude/templates/vault-di-progetto").mkdir(parents=True)
        scrivi_json(fis / ELENCO_NEL_PROGETTO, {"schema": "vault-plugin-1", "plugin": [voce("beta", "1.0")]})
        globals()["versione_obsidian"], originale = (lambda: "1.15.1"), versione_obsidian
        try:
            fissa(fis, "alfa", "serve alla prova", "base", None, False, scarica=finta_rete, oggi=oggi)
            scritto = leggi_json(fis / ELENCO_NEL_PROGETTO)
            nuova = next(x for x in scritto["plugin"] if x["id"] == "alfa")
            caso("fissa scrive la voce con versione e impronte del rilascio, e lascia le altre",
                 nuova["versione"] == "2.1" and nuova["sha256"]["main.js"] == impronta(rilascio("alfa", "2.1")["main.js"])
                 and [x["id"] for x in scritto["plugin"]] == ["alfa", "beta"], scritto)
            fissa(fis, "alfa", "solo qui", "facoltativo", None, True, scarica=finta_rete, oggi=oggi)
            caso("fissa --progetto scrive nelle scelte del progetto e non nell'elenco del template",
                 leggi_json(fis / SCELTE_DEL_PROGETTO)["plugin"][0]["stato"] == "facoltativo" and leggi_json(fis / ELENCO_NEL_PROGETTO) == scritto)
            try:
                fissa(fis, "alfa", "x", "base", None, False, scarica=finta_rete, oggi=dt.date(2028, 1, 1))
                respinto = False
            except ValueError:
                respinto = True
            caso("negativo: fissa rifiuta di mettere nella base un plugin che non passa i criteri", respinto)
        finally:
            globals()["versione_obsidian"] = originale
    print("%d prove, %d fallite" % (len(esiti), esiti.count(False)))
    return 1 if False in esiti else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("azione", nargs="?", choices=["crea", "aggiorna", "verifica", "togli", "cerca", "valuta", "fissa"])
    ap.add_argument("argomenti", nargs="*", help="per cerca le parole, per valuta e fissa l'id del plugin")
    ap.add_argument("--radice", default=".")
    ap.add_argument("--cartella", default="_vault")
    ap.add_argument("--vault", help="un vault qualunque da aggiornare o verificare, anche non creato da questo strumento")
    ap.add_argument("--da-vault")
    ap.add_argument("--rete", action="store_true", help="consente di scaricare dal rilascio fissato i plugin che il vault di riferimento non ha")
    ap.add_argument("--ignora", action="store_true", help="aggiunge la cartella del vault al .gitignore")
    ap.add_argument("--limite", type=int, default=15)
    ap.add_argument("--obsidian", help="versione di Obsidian contro cui valutare; per difetto quella installata")
    ap.add_argument("--motivo")
    ap.add_argument("--stato", default="base", choices=STATI)
    ap.add_argument("--versione")
    ap.add_argument("--progetto", action="store_true", help="fissa nelle scelte del progetto invece che nell'elenco del template")
    ap.add_argument("--autotest", action="store_true")
    a = ap.parse_args()
    if a.autotest:
        return autotest()
    if not a.azione:
        ap.error("serve un'azione: crea, aggiorna, verifica, togli, cerca, valuta o fissa")
    radice = Path(a.radice).resolve()
    try:
        if a.azione == "crea":
            for r in crea(radice, a.cartella, a.da_vault, a.ignora, a.rete):
                print("  " + r)
            print("vault pronto: in Obsidian, «Apri cartella come vault» su %s" % (radice / a.cartella))
            return 0
        if a.azione == "aggiorna":
            righe, mancati = aggiorna(radice, Path(a.vault).resolve() if a.vault else radice / a.cartella, a.da_vault, a.rete)
            for r in righe:
                print("  " + r)
            print("aggiornamento: %d plugin non installati" % mancati + ("; se Obsidian e' aperto su questo vault, ricaricalo" if not mancati else ""))
            return 1 if mancati else 0
        if a.azione == "togli":
            for r in togli(radice, a.cartella):
                print("  " + r)
            return 0
        if a.azione == "cerca":
            if not a.argomenti:
                ap.error("cerca vuole almeno una parola")
            for r in cerca(a.argomenti, a.limite):
                print(r)
            return 0
        if a.azione in ("valuta", "fissa"):
            if len(a.argomenti) != 1:
                ap.error("%s vuole l'id di un plugin" % a.azione)
            if a.azione == "valuta":
                righe, idoneo, _ = valuta(a.argomenti[0], a.obsidian or versione_obsidian())
                print("\n".join(righe))
                return 0 if idoneo else 1
            if not a.motivo:
                ap.error("fissa vuole --motivo: perche' il plugin entra, o esce")
            print("\n".join(fissa(radice, a.argomenti[0], a.motivo, a.stato, a.versione, a.progetto)))
            return 0
        guai = verifica(radice, a.cartella, Path(a.vault).resolve() if a.vault else None)
        for g in guai:
            print("  " + g)
        print("vault: %d problemi" % len(guai))
        return 1 if guai else 0
    except (OSError, ValueError) as err:
        print("errore: %s" % err, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
