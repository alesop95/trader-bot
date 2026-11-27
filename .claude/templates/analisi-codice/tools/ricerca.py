#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Il ciclo di una ricerca sul codice: cartella, mappa, controlli, pagine, indice, Desktop.

Ogni ricerca vive in `ricerche/<nome>/`:
  ricerca.json   titolo, domanda, data di apertura, termini da mappare
  analisi.md     l'analisi scritta, tecnica e operativa, con i link a file, riga e commit
  mappa.md       generata da dove-usato.py: ogni occorrenza dei termini nell'istanza
  mappa.json     la stessa mappa come dati
  *.html         le pagine, con il design system del progetto, generate e mai scritte a mano

`genera` non pubblica una pagina che non passa i controlli delle regole di progetto: trattini,
accenti, segni del testo generato, un paragrafo di prosa per riga, giro chiuso fra testo e pagina.
Poi rigenera `ricerche/indice.html` e, se `analisi-codice.json` dichiara `cartella_desktop`, una
cartella sul Desktop con un collegamento numerato per pagina.

Si lancia dalla radice del progetto. Gli strumenti di controllo si cercano prima in `tools/` del
progetto, poi accanto a questo file e nei pacchetti del template, così lo stesso file funziona
copiato nel progetto o lanciato dal template.

    python tools/ricerca.py nuova <nome> --titolo "..." --domanda "..." --termini a,b,c
    python tools/ricerca.py mappa <nome>
    python tools/ricerca.py genera <nome>          controlli, pagine, indice, Desktop
    python tools/ricerca.py genera --tutte
    python tools/ricerca.py controlla <nome>       solo i controlli
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

PROGETTO = Path.cwd()
RICERCHE = PROGETTO / "ricerche"
QUI = Path(__file__).resolve().parent
_conf = PROGETTO / "analisi-codice.json"
CONF = json.loads(_conf.read_text(encoding="utf-8")) if _conf.exists() else {}
SISTEMA = CONF.get("sistema", PROGETTO.name)
ETICHETTE = [x for x in (CONF.get("organizzazione"), CONF.get("descrizione")) if x]
CARTELLA_DESKTOP = CONF.get("cartella_desktop")
PAGINE = ("analisi", "mappa")


def trova(nome):
    """Uno strumento: nel progetto, accanto a questo file, o in un pacchetto del template."""
    for cand in [PROGETTO / "tools" / nome, QUI / nome, *sorted(QUI.parent.parent.glob(f"*/tools/{nome}"))]:
        if cand.is_file():
            return cand
    sys.exit(f"ricerca: strumento {nome} non trovato né nel progetto né nel template")


def py(strumento, *argomenti):
    return subprocess.run([sys.executable, str(trova(strumento)), *map(str, argomenti)],
                          capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=PROGETTO)


def prosa_su_una_riga(percorso):
    """Righe di prosa spezzate: due righe consecutive non vuote fuori dalle strutture del generatore."""
    righe = percorso.read_text(encoding="utf-8").splitlines()
    errori, dentro, i = [], False, 0
    if righe and righe[0] == "---":
        i = righe.index("---", 1) + 1
    precedente = ""
    for n in range(i, len(righe)):
        r = righe[n].strip()
        if r.startswith(":::"):
            dentro = r != ":::" or not dentro
            if r == ":::":
                dentro = False
            precedente = ""
            continue
        if dentro or not r or r.startswith(("#", ">")):
            precedente = "" if not r or r.startswith("#") else r
            continue
        if precedente and not precedente.startswith(">"):
            errori.append(f"{percorso.name}:{n + 1}: paragrafo spezzato su più righe")
        precedente = r
    return errori


def link_rotti(percorso):
    """Ogni link a GitHub di un sorgente scaricato: file presente, righe dentro il file, commit noto.

    Il link si verifica sul clone locale, che è allo stesso commit del manifesto: un link a un
    commit diverso da quello del manifesto si segnala, perché la riga citata potrebbe non essere
    quella che il lettore vede."""
    sorgenti = json.loads((PROGETTO / "sorgenti" / "manifest.json").read_text(encoding="utf-8"))["sorgenti"]
    per_repo = {i["repo"].lower(): (n, i) for n, i in sorgenti.items() if i.get("accessibile")}
    testo = percorso.read_text(encoding="utf-8")
    errori = []
    for repo, sha, file, da, a in re.findall(
            r"https://github\.com/([\w.-]+/[\w.-]+)/blob/([0-9a-f]{7,40})/([^#)\s]+)(?:#L(\d+)(?:-L(\d+))?)?", testo):
        voce = per_repo.get(repo.lower())
        if not voce:
            continue
        nome, info = voce
        if not info["commit"].startswith(sha):
            errori.append(f"{percorso.name}: {repo}/{file} punta a {sha[:8]}, il manifesto è a {info['commit'][:8]}")
            continue
        locale = PROGETTO / "sorgenti" / nome / file
        if not locale.is_file():
            errori.append(f"{percorso.name}: {repo}/{file} non esiste")
            continue
        n = len(locale.read_text(encoding="utf-8", errors="replace").splitlines())
        for riga in (da, a):
            if riga and int(riga) > n:
                errori.append(f"{percorso.name}: {repo}/{file}#L{riga} oltre la fine del file ({n} righe)")
    for repo, sha in re.findall(r"https://github\.com/([\w.-]+/[\w.-]+)/commit/([0-9a-f]{7,40})", testo):
        voce = per_repo.get(repo.lower())
        if not voce:
            continue
        r = subprocess.run(["git", "-C", str(PROGETTO / "sorgenti" / voce[0]), "cat-file", "-e", f"{sha}^{{commit}}"],
                           capture_output=True)
        if r.returncode:
            errori.append(f"{percorso.name}: commit {sha[:8]} assente in {repo}")
    return errori


def componi(cartella):
    """La pagina della ricerca: l'analisi con la mappa come macro-sezione, prima delle Note.

    Analisi e mappa restano due sorgenti, perché una si scrive e l'altra si genera, ma diventano
    una pagina sola: chi legge un difetto trova nella stessa pagina tutti i punti in cui compare
    l'oggetto. Il file composto è temporaneo e nascosto, e si cancella dopo l'uso."""
    testo = (cartella / "analisi.md").read_text(encoding="utf-8")
    mappa = cartella / "mappa.md"
    if mappa.exists():
        blocco = mappa.read_text(encoding="utf-8").strip() + "\n\n"
        m = re.search(r"^## Note\b", testo, re.M)
        testo = testo[:m.start()] + blocco + testo[m.start():] if m else testo.rstrip("\n") + "\n\n" + blocco
    composta = cartella / ".pagina.md"
    composta.write_text(testo, encoding="utf-8")
    return composta


def impatti_mancanti(cartella):
    conf = json.loads((cartella / "ricerca.json").read_text(encoding="utf-8"))
    mancano = [t for t in conf.get("termini", []) if not conf.get("impatti", {}).get(t)]
    return [f"ricerca.json: impatto operativo da scrivere per {', '.join(mancano)}"] if mancano else []


def controlla(cartella):
    """Esegue tutti i controlli sui .md della ricerca e sulla pagina composta. Torna i problemi."""
    problemi = impatti_mancanti(cartella)
    for nome in PAGINE:
        md = cartella / f"{nome}.md"
        if not md.exists():
            continue
        problemi += prosa_su_una_riga(md)
        problemi += link_rotti(md)
        for strumento in ("fix-dashes.py", "fix-accents.py"):
            r = py(strumento, "--check", md)
            if re.search(r"\b[1-9]\d* da modificare", r.stdout):
                problemi.append(f"{md.name}: {strumento} segnala da modificare")
        if nome == "analisi":
            r = py("lint-prosa.py", md)
            segni = [riga for riga in r.stdout.splitlines() if re.search(r":\d+\s+P\d", riga)]
            problemi += [f"{md.name}: anti-slop {riga.split(md.name)[-1].strip()}" for riga in segni]
    if (cartella / "analisi.md").exists():
        composta = componi(cartella)
        r = py("documento-genera.py", composta, "--giro")
        composta.unlink()
        if "il giro chiude" not in r.stdout:
            problemi.append(f"pagina: il giro fra testo e pagina non chiude: {(r.stdout + r.stderr).strip()[-200:]}")
    return problemi


def desktop():
    r = subprocess.run(["powershell", "-NoProfile", "-Command", "[Environment]::GetFolderPath('Desktop')"],
                       capture_output=True, text=True)
    return Path(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else None


def collegamento(cartella, nome, bersaglio):
    (cartella / f"{nome}.url").write_text(f"[InternetShortcut]\nURL={bersaglio.as_uri()}\n", encoding="utf-8")


def indice():
    """ricerche/indice.md e .html, poi la cartella sul Desktop con un collegamento per pagina."""
    voci = []
    for c in sorted(p for p in RICERCHE.iterdir() if (p / "ricerca.json").exists()):
        conf = json.loads((c / "ricerca.json").read_text(encoding="utf-8"))
        voci.append((c, conf))
    righe = ["---", f"titolo: Analisi del codice {SISTEMA}",
             f"intestazione: Indice delle ricerche | {date.today():%d/%m/%Y}",
             "etichette: " + " | ".join(ETICHETTE + ["Una cartella per ricerca"]), "---", "",
             f'# Analisi del codice {SISTEMA} {{occhiello="Indice delle ricerche"}}', "",
             f"> {len(voci)} ricerche. Ognuna è una pagina con l'analisi scritta e, come sezione, la mappa generata di tutti i punti in cui compaiono gli oggetti coinvolti.", "",
             "::: schede"]
    for i, (c, conf) in enumerate(voci):
        if i:
            righe.append("---")
        righe += [f"Ricerca: [{conf['titolo']}]({c.name}/analisi.html)",
                  f"Domanda: {conf.get('domanda', '')}",
                  f"Aperta: {conf.get('aperta', '')}",
                  f"Termini mappati: {len(conf.get('termini', []))}"]
    righe += [":::", ""]
    md = RICERCHE / "indice.md"
    md.write_text("\n".join(righe), encoding="utf-8")
    py("documento-genera.py", md, "--uscita", RICERCHE / "indice.html", "--incorpora", "--con-caratteri")

    if not CARTELLA_DESKTOP:
        return
    d = desktop()
    if not d:
        print("ricerca: cartella Desktop non trovata, collegamenti non aggiornati")
        return
    cart = d / CARTELLA_DESKTOP
    cart.mkdir(exist_ok=True)
    for vecchio in cart.glob("*.url"):
        vecchio.unlink()
    collegamento(cart, "00 - Indice delle ricerche", RICERCHE / "indice.html")
    for n, (c, conf) in enumerate(voci, 1):
        if (c / "analisi.html").exists():
            collegamento(cart, f"{n:02d} - {conf['titolo']}", c / "analisi.html")
    print(f"ricerca: indice e collegamenti aggiornati in {cart}")


def genera(cartella):
    problemi = controlla(cartella)
    if problemi:
        print("\n".join(problemi))
        sys.exit(f"ricerca: {len(problemi)} problemi in {cartella.name}, pagine non generate")
    composta = componi(cartella)
    r = py("documento-genera.py", composta, "--uscita", cartella / "analisi.html", "--incorpora", "--con-caratteri")
    composta.unlink()
    print(r.stdout.strip() or r.stderr.strip())
    # La mappa era una pagina a sé fino al 26/11/2026: la copia vecchia si toglie, perché un
    # collegamento rimasto a una pagina superata mostra dati che la ricerca non aggiorna più.
    (cartella / "mappa.html").unlink(missing_ok=True)
    for cache in (PROGETTO / "tools").glob("__pycache__"):
        for f in cache.iterdir():
            f.unlink()
        cache.rmdir()


def nuova(nome, titolo, domanda, termini):
    c = RICERCHE / nome
    c.mkdir(parents=True, exist_ok=False)
    (c / "ricerca.json").write_text(json.dumps(
        {"titolo": titolo, "domanda": domanda, "aperta": date.today().isoformat(), "termini": termini},
        indent=2, ensure_ascii=False), encoding="utf-8")
    (c / "analisi.md").write_text(
        f"---\ntitolo: {titolo}\nintestazione: Analisi del codice {SISTEMA} | {date.today():%d/%m/%Y}\n"
        f"etichette: {' | '.join(ETICHETTE + ['Analisi su codice'])}\n---\n\n"
        f'# {titolo} {{occhiello="Analisi del codice di produzione"}}\n\n> {domanda}\n', encoding="utf-8")
    print(f"ricerca: creata {c}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("azione", choices=["nuova", "mappa", "genera", "controlla"])
    ap.add_argument("nome", nargs="?")
    ap.add_argument("--titolo")
    ap.add_argument("--domanda", default="")
    ap.add_argument("--termini", default="")
    ap.add_argument("--tutte", action="store_true")
    a = ap.parse_args()

    if a.azione == "nuova":
        nuova(a.nome, a.titolo or a.nome, a.domanda, [t for t in a.termini.split(",") if t])
        return
    cartelle = sorted(p for p in RICERCHE.iterdir() if (p / "ricerca.json").exists()) if a.tutte else [RICERCHE / a.nome]
    for c in cartelle:
        if a.azione == "mappa":
            r = py("dove-usato.py", "--ricerca", c)
            print(r.stdout.strip(), r.stderr.strip(), sep="\n")
        elif a.azione == "controlla":
            problemi = controlla(c)
            print("\n".join(problemi) or f"{c.name}: nessun problema")
        else:
            genera(c)
    if a.azione == "genera":
        indice()


if __name__ == "__main__":
    main()
