#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Trova ogni punto del sistema analizzato in cui compare un termine, con tipo, effetto, link e commit.

Perché esiste
-------------
Quando l'analisi scopre un oggetto, un campo, un gruppo, una regola, un metodo, la domanda che
segue è sempre la stessa: dove altro è usato, nel codice e per chi usa l'istanza. Questo strumento
risponde su tutti i sorgenti scaricati da `sorgenti.py`, che sono la stessa unione di repository
che il file di composizione dichiarato in `analisi-codice.json` mette insieme.

La classificazione di tipo, livello ed effetto conosce gli oggetti di Odoo (viste, regole,
gruppi, ACL, menu, azioni, moduli con __manifest__.py); su un altro stack ogni occorrenza resta
classificata come uso in codice, definizione o dato, e link, contesto e commit valgono uguali.

Per ogni occorrenza dà:
  tipo       definizione di campo o metodo, uso in codice, vista, template, regola di accesso,
             permesso (ACL), menu, azione, gruppo, azione pianificata, modello email, traduzione
  livello    logica, sicurezza, interfaccia, dati, etichetta
  contesto   modulo, e la classe con il metodo per il Python, il record con il modello per l'XML
  effetto    che cosa cambia per chi usa l'istanza, dedotto dal tipo e dagli attributi groups
  link       permanente, al commit registrato nel manifesto, con l'ancora alla riga
  origine    commit, data e autore che hanno introdotto la riga (git blame), dove la storia c'è

La ricerca è testuale con confini di parola, sulle estensioni .py .xml .csv .js e sui soli file
it.po fra le traduzioni. Non risolve l'ereditarietà dei modelli né le chiamate dinamiche
(getattr, stringhe composte): una chiamata costruita a runtime non si trova, e lo strumento lo
dichiara nel perimetro dell'uscita.

    python tools/dove-usato.py nome_campo nome_gruppo
    python tools/dove-usato.py --ricerca ricerche/<nome>            legge i termini da ricerca.json
    python tools/dove-usato.py TERMINE --famiglie personalizzazione,oca
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

PROGETTO = Path.cwd()
SORGENTI = PROGETTO / "sorgenti"
CONF = json.loads((PROGETTO / "analisi-codice.json").read_text(encoding="utf-8")) if (PROGETTO / "analisi-codice.json").exists() else {}
ESTENSIONI = {".py", ".xml", ".csv", ".js"}
SALTA_DIR = {".git", "node_modules", "__pycache__", "lib", "tests", "test", "setup"}
METODI_GENERICI = {"write", "create", "unlink", "default_get", "search", "read", "name_get",
                   "copy", "onchange", "_compute", "fields_view_get", "action_apply", "init"}

TIPI_XML = {
    "ir.ui.view": ("vista", "interfaccia"),
    "ir.rule": ("regola di accesso", "sicurezza"),
    "res.groups": ("gruppo", "sicurezza"),
    "ir.ui.menu": ("menu", "interfaccia"),
    "ir.actions.act_window": ("azione finestra", "interfaccia"),
    "ir.actions.server": ("azione server", "logica"),
    "ir.actions.report": ("report", "interfaccia"),
    "ir.cron": ("azione pianificata", "logica"),
    "base.automation": ("azione automatica", "logica"),
    "mail.template": ("modello email", "interfaccia"),
    "ir.model.access": ("permesso (ACL)", "sicurezza"),
    "funzione XML": ("funzione eseguita all'aggiornamento del modulo", "dati"),
}


def manifesto():
    p = SORGENTI / "manifest.json"
    if not p.exists():
        sys.exit("dove-usato: manca sorgenti/manifest.json, eseguire prima tools/sorgenti.py")
    return json.loads(p.read_text(encoding="utf-8"))["sorgenti"]


def modulo_di(percorso, radice):
    """La cartella del modulo Odoo che contiene il file: la più vicina con __manifest__.py."""
    d = percorso.parent
    while d != radice and d != d.parent:
        if (d / "__manifest__.py").exists() or (d / "__openerp__.py").exists():
            return d.name
        d = d.parent
    return ""


def contesti_python(righe):
    """Per ogni riga: (classe, modello, metodo). Modello è _name, altrimenti _inherit."""
    fuori, classe, modello, metodo, ind_classe = [], "", "", "", -1
    for r in righe:
        nudo = r.lstrip()
        ind = len(r) - len(nudo)
        m = re.match(r"class\s+(\w+)", nudo)
        if m:
            classe, modello, metodo, ind_classe = m.group(1), "", "", ind
        elif nudo and ind <= ind_classe and not nudo.startswith(("#", "@", ")")):
            classe, modello, metodo = "", "", ""
        m = re.match(r"_(name|inherit)\s*=\s*\[?['\"]([\w.]+)['\"]", nudo)
        if m and classe and (m.group(1) == "name" or not modello):
            modello = m.group(2)
        m = re.match(r"def\s+(\w+)", nudo)
        if m:
            metodo = m.group(1)
        fuori.append((classe, modello, metodo))
    return fuori


def contesti_xml(righe):
    """Per ogni riga: il record che la contiene (id, modello del record, modello della vista)."""
    fuori, corrente = [], {}
    for r in righe:
        m = re.search(r"<record\b[^>]*", r)
        if m:
            tag = m.group(0)
            corrente = {"id": (re.search(r'id="([^"]+)"', tag) or [None, ""])[1],
                        "tipo": (re.search(r'model="([^"]+)"', tag) or [None, ""])[1], "modello": ""}
        m = re.search(r'<function\s[^>]*name="(\w+)"[^>]*model="([\w.]+)"', r)
        if m and not corrente:
            corrente = {"id": f"{m.group(2)}.{m.group(1)}()", "tipo": "funzione XML", "modello": ""}
        for etichetta, tipo in (("template", "template QWeb"), ("menuitem", "ir.ui.menu")):
            m = re.search(r"<%s\b[^>]*" % etichetta, r)
            if m:
                corrente = {"id": (re.search(r'id="([^"]+)"', m.group(0)) or [None, ""])[1],
                            "tipo": tipo, "modello": ""}
        m = re.search(r'<field name="model"[^>]*>([\w.]+)<', r) or re.search(r'<field name="model_id" ref="([\w.]+)"', r)
        if m and corrente:
            corrente["modello"] = m.group(1)
        fuori.append(dict(corrente))
        if "</record>" in r or "</template>" in r or (corrente.get("tipo") == "funzione XML" and re.match(r"\s*</function>\s*$", r) and not r.startswith("        ")) or (re.search(r"<menuitem\b", r) and "/>" in r):
            corrente = {}
    return fuori


def blame(cartella, relativo):
    """Riga → (commit, data, autore, oggetto), con un solo git blame per file."""
    r = subprocess.run(["git", "-C", str(cartella), "blame", "--line-porcelain", "--", relativo],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    fuori, intest, n = {}, {}, 0
    for riga in r.stdout.splitlines():
        m = re.match(r"^([0-9a-f]{40}) \d+ (\d+)", riga)
        if m:
            intest = {"commit": m.group(1)}
            n = int(m.group(2))
        elif riga.startswith("author "):
            intest["autore"] = riga[7:]
        elif riga.startswith("author-time "):
            intest["data"] = datetime.fromtimestamp(int(riga[12:])).strftime("%d/%m/%Y")
        elif riga.startswith("summary "):
            intest["oggetto"] = riga[8:]
        elif riga.startswith("\t"):
            fuori[n] = dict(intest)
    return fuori


def classifica(est, testo, termine, ctx, nome_file):
    """(tipo, livello, contesto, effetto) per un'occorrenza."""
    groups = re.search(r'groups="([^"]+)"', testo)
    if est == ".py":
        classe, modello, metodo = ctx
        dove = f"{modello or classe}.{metodo}" if metodo else (modello or classe)
        if re.search(r"\b%s\s*=\s*fields\.(\w+)" % re.escape(termine), testo):
            tipo = "definizione campo " + re.search(r"fields\.(\w+)", testo).group(1)
            return tipo, "dati", modello or classe, f"campo salvato sul modello {modello}"
        if re.search(r"def\s+%s\b" % re.escape(termine), testo):
            return "definizione metodo", "logica", dove, "logica eseguita dal server"
        if "has_group" in testo or "ref(" in testo:
            return "controllo di gruppo", "sicurezza", dove, "comportamento diverso per i membri del gruppo"
        return "uso in codice", "logica", dove, f"letto o scritto in {dove}" if metodo else "uso a livello di classe"
    if est == ".xml":
        tipo_rec = ctx.get("tipo", "")
        tipo, livello = TIPI_XML.get(tipo_rec, (tipo_rec or "dato XML", "dati"))
        if tipo_rec == "template QWeb":
            livello = "interfaccia"
        contesto = ctx.get("id", "") + (f" ({ctx['modello']})" if ctx.get("modello") else "")
        effetto = {"vista": "mostrato nella maschera", "regola di accesso": "cambia quali record vedono i membri del gruppo",
                   "menu": "voce di menu", "gruppo": "definizione o membri del gruppo",
                   "template QWeb": "mostrato nel sito o nel portale o in un report"}.get(tipo, "dato caricato all'installazione")
        if groups:
            effetto += f", solo per {groups.group(1)}"
        return tipo, livello, contesto, effetto
    if est == ".csv":
        campi = [c.strip() for c in testo.split(",")]
        if len(campi) >= 8 and "ir.model.access" in nome_file:
            perms = "".join(lettera for lettera, v in zip("RWCU", campi[4:8]) if v == "1")
            return "permesso (ACL)", "sicurezza", f"{campi[2]} per {campi[3] or 'tutti'}", f"permessi {perms or 'nessuno'}"
        return "dato CSV", "dati", nome_file, "dato caricato all'installazione"
    if est == ".js":
        return "client web", "interfaccia", nome_file, "comportamento del browser"
    return "traduzione", "etichetta", nome_file, "testo mostrato in italiano"


def cerca(termini, famiglie):
    sorgenti = manifesto()
    schemi = {t: re.compile(r"(?<![\w])%s(?![\w])" % re.escape(t)) for t in termini}
    trovati = defaultdict(list)
    for nome, info in sorgenti.items():
        if not info.get("accessibile") or (famiglie and info["famiglia"] not in famiglie):
            continue
        radice = SORGENTI / nome
        storia = not (radice / ".git" / "shallow").exists()
        for dirpath, dirnames, filenames in os.walk(radice):
            dirnames[:] = [d for d in dirnames if d not in SALTA_DIR]
            for f in filenames:
                p = Path(dirpath) / f
                est = p.suffix
                if est not in ESTENSIONI and not (est == ".po" and f == "it.po"):
                    continue
                try:
                    testo = p.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                if not any(s.search(testo) for s in schemi.values()):
                    continue
                righe = testo.splitlines()
                ctx = contesti_python(righe) if est == ".py" else contesti_xml(righe) if est == ".xml" else None
                rel = p.relative_to(radice).as_posix()
                autori = blame(radice, rel) if storia else {}
                for n, r in enumerate(righe, 1):
                    for t, s in schemi.items():
                        if not s.search(r):
                            continue
                        c = ctx[n - 1] if ctx else None
                        tipo, livello, contesto, effetto = classifica(est, r, t, c, f)
                        trovati[t].append({
                            "sorgente": nome, "famiglia": info["famiglia"], "repo": info["repo"],
                            "file": rel, "riga": n, "modulo": modulo_di(p, radice), "testo": r.strip(),
                            "tipo": tipo, "livello": livello, "contesto": contesto, "effetto": effetto,
                            "link": f"https://github.com/{info['repo']}/blob/{info['commit']}/{rel}#L{n}",
                            "origine": autori.get(n),
                            "metodo": c[2] if est == ".py" and c else "",
                            "record": c.get("id", "") if est == ".xml" and c else "",
                        })
    return trovati, sorgenti


def collegati(trovati, termini):
    """Simboli vicini alle occorrenze che meritano una ricerca a sé: metodi, record, gruppi."""
    fuori = set()
    for occ in trovati.values():
        for o in occ:
            if o["metodo"] and o["metodo"] not in METODI_GENERICI:
                fuori.add(o["metodo"])
            if o["record"]:
                fuori.add(o["record"].split(".")[-1])
            for g in re.findall(r"ref\(['\"]([\w.]+)['\"]\)", o["testo"]):
                fuori.add(g.split(".")[-1])
    return sorted(fuori - set(termini))


def cella(s, n=150):
    s = s.replace("`", "'").replace("|", "/")
    return s if len(s) <= n else s[:n - 1] + "…"


def markdown(trovati, termini, sorgenti, famiglie, impatti=None):
    """La mappa come macro-sezione dell'analisi: un titolo ## e un ### per termine.

    Non ha front matter né titolo di documento, perché non è una pagina a sé: `ricerca.py genera`
    la accoda all'analisi e ne fa una pagina sola. L'impatto operativo di ogni termine non si
    deduce dal codice, lo scrive chi analizza in ricerca.json; qui apre il riepilogo e ogni
    termine, così che chi legge veda prima che cosa cambia per chi usa il sistema e poi dove."""
    impatti = impatti or {}
    usati = [n for n, i in sorgenti.items() if i.get("accessibile") and (not famiglie or i["famiglia"] in famiglie)]
    mancanti = [i["repo"] for i in sorgenti.values() if not i.get("accessibile")]
    tot = sum(len(v) for v in trovati.values())
    fuori = ['## Mappa delle occorrenze {occhiello="Dove è usato, punto per punto"}', "",
             f"{tot} occorrenze di {len(termini)} termini in {len(usati)} sorgenti, il {datetime.now():%d/%m/%Y}: ricerca testuale con confini di parola su .py .xml .csv .js e it.po, che non trova le chiamate costruite a runtime."
             + (" Non accessibili e quindi non cercati: " + ", ".join(sorted(mancanti)) + "." if mancanti else ""), "",
             "### Riepilogo per termine", "", "::: schede"]
    for i, t in enumerate(termini):
        per_livello = defaultdict(int)
        for o in trovati.get(t, []):
            per_livello[o["livello"]] += 1
        if i:
            fuori.append("---")
        fuori += [f"Termine: `{t}`",
                  f"Impatto operativo: {impatti.get(t, 'da scrivere in ricerca.json')}",
                  f"Occorrenze: {len(trovati.get(t, []))}",
                  "Per livello: " + (", ".join(f"{k} {v}" for k, v in sorted(per_livello.items())) or "nessuna")]
    fuori += [":::", ""]
    for t in termini:
        occ = sorted(trovati.get(t, []), key=lambda o: (o["livello"], o["modulo"], o["file"], o["riga"]))
        fuori += [f"### `{t}`, {len(occ)} occorrenze", "", "> [!riquadro]", "> **Impatto operativo**", ">",
                  f"> {impatti.get(t, 'da scrivere in ricerca.json')}", ""]
        if not occ:
            fuori += ["Nessuna occorrenza nei sorgenti cercati.", ""]
            continue
        fuori.append("::: schede")
        for i, o in enumerate(occ):
            if i:
                fuori.append("---")
            org = o["origine"]
            origine = (f"[{org['commit'][:8]}](https://github.com/{o['repo']}/commit/{org['commit']}) {org['data']} {cella(org['autore'], 30)}: {cella(org['oggetto'], 70)}"
                       if org else "storia non disponibile (clone superficiale)")
            fuori += [f"Effetto: {o['effetto']}",
                      f"Dove: [{o['modulo'] or o['sorgente']}/{o['file'].split('/')[-1]}:{o['riga']}]({o['link']})",
                      f"Tipo: {o['tipo']}, {o['livello']}",
                      f"Contesto: `{cella(o['contesto'], 80)}`" if o["contesto"] else "Contesto: -",
                      f"Riga: `{cella(o['testo'])}`",
                      f"Introdotta: {origine}"]
        fuori += [":::", ""]
    sugg = collegati(trovati, termini)
    if sugg:
        fuori += ["### Termini collegati", "",
                  "Simboli che compaiono accanto alle occorrenze, da aggiungere alla ricerca se rilevanti: " + ", ".join(f"`{s}`" for s in sugg) + ".", ""]
    return "\n".join(fuori) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("termini", nargs="*")
    ap.add_argument("--ricerca", help="cartella di una ricerca: legge ricerca.json e scrive mappa.md e mappa.json")
    ap.add_argument("--famiglie", help="personalizzazione,terzi,oca,core; per difetto tutte le scaricate")
    a = ap.parse_args()

    termini, uscita, impatti = list(a.termini), None, {}
    if a.ricerca:
        cartella = Path(a.ricerca)
        conf = json.loads((cartella / "ricerca.json").read_text(encoding="utf-8"))
        termini = termini or conf["termini"]
        impatti = conf.get("impatti", {})
        uscita = cartella
    if not termini:
        ap.error("nessun termine")
    famiglie = set(a.famiglie.split(",")) if a.famiglie else set()

    trovati, sorgenti = cerca(termini, famiglie)
    md = markdown(trovati, termini, sorgenti, famiglie, impatti)
    if uscita:
        (uscita / "mappa.md").write_text(md, encoding="utf-8")
        (uscita / "mappa.json").write_text(json.dumps(trovati, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"dove-usato: scritte {uscita / 'mappa.md'} e mappa.json")
    else:
        print(md)
    for t in termini:
        print(f"  {t}: {len(trovati.get(t, []))}", file=sys.stderr)


if __name__ == "__main__":
    main()
