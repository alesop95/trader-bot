#!/usr/bin/env python3
"""Genera il riferimento completo del template: ogni skill, pacchetto, strumento e fonte, con come, perché, quando e quando no.

Perche' esiste. Il 2026-11-12 il proprietario ha chiesto che la documentazione contenga tutto:
ogni skill, ogni strumento e ogni fonte, con come si usa, perche', quando e quando no. Quel
contenuto esisteva gia' quasi tutto ma in quattro posti, ciascuno con una meta': il catalogo
dei pacchetti dice che cosa fa una voce e quando offrirla, il registro delle fonti a monte
dice ogni fonte e che cosa se ne prende, gli strumenti si descrivono nella propria prima riga,
le skill nella propria descrizione. Mancava il «quando no» come campo dichiarato e mancava un
punto d'ingresso unico. Un inventario scritto a mano invecchia nel modo che `check-catalogo.py`
racconta, quindi questo documento si genera dal disco: cio' che un programma sa ricavare lo
ricava, e cio' che non sa ricavare, cioe' come si usa in una frase, perche' e quando no, sta
in un file di dati accanto, una voce per skill e per pacchetto.

Che cosa legge.
  .claude/templates/PACKAGES.md              settori, voci, che cosa fa, quando offrirlo
  .claude/templates/riferimento-voci.json    le tre frasi scritte a mano, per pacchetto e per skill
  .claude/skills/*/SKILL.md                  nome e descrizione delle skill di sistema
  .claude/templates/tools/*                  prima riga di descrizione di ogni strumento
  .claude/templates/fonti-a-monte.json       le fonti di ogni pacchetto, con l'indirizzo

Che cosa ferma. `--check` esce con 1 se il documento non corrisponde a cio' che si genererebbe
adesso, se una skill o un pacchetto non ha la sua voce nel file di dati o ne ha una con un
campo vuoto, se il file di dati ha una voce che sul disco non esiste piu', o se uno strumento
non ha una riga di descrizione. Un «quando no» che la documentazione del pacchetto non
dichiara si scrive come tale, e il documento li conta: e' un debito visibile, non un errore.

Vale per il repository del template, riconosciuto dai due prompt di istanziazione; in un
progetto istanziato non ha oggetto e lo dice.

Uso:
    python tools/riferimento.py --scrivi     rigenera docs/RIFERIMENTO.md
    python tools/riferimento.py --check      confronta senza scrivere
    python tools/riferimento.py --autotest
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CATALOGO = ".claude/templates/PACKAGES.md"
DATI = ".claude/templates/riferimento-voci.json"
FONTI = ".claude/templates/fonti-a-monte.json"
USCITA = "docs/RIFERIMENTO.md"
CAMPI = ("come", "perche", "quando_no")
NON_DICHIARATO = "Non dichiarato nella documentazione del pacchetto."
RIGA = re.compile(r"^\| `([a-z0-9][a-z0-9.-]*)`((?: \([^)|]*\))?) \|(.*)\|\s*$")


def catalogo(testo: str) -> list:
    """Le voci del catalogo, nell'ordine del file, con il settore a cui appartengono."""
    settore, voci = None, []
    for r in testo.splitlines():
        if r.startswith("### "):
            settore = r[4:].strip()
        elif r.startswith("## "):
            settore = None
        m = RIGA.match(r)
        if m and settore:
            celle = [c.strip() for c in m.group(3).split(" | ")]
            voci.append({"nome": m.group(1), "tipo": m.group(2).strip(" ()"), "settore": settore,
                         "cosa_fa": celle[0] if celle else "", "quando": celle[1] if len(celle) > 1 else ""})
    return voci


def frontmatter(testo: str) -> dict:
    """Nome e descrizione di una skill; la descrizione puo' stare su piu' righe rientrate."""
    if not testo.startswith("---"):
        return {}
    righe = testo.split("\n")[1:]
    dati, chiave = {}, None
    for r in righe:
        if r.strip() in ("---", "..."):
            break
        m = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$", r)
        if m:
            chiave = m.group(1)
            valore = m.group(2).strip()
            dati[chiave] = "" if valore in (">", "|", ">-", "|-") else valore.strip("\"'")
        elif chiave and r.startswith((" ", "\t")):
            dati[chiave] = (dati[chiave] + " " + r.strip()).strip()
    return dati


def skill_di_sistema(radice: Path) -> list:
    esito = []
    base = radice / ".claude/skills"
    for d in sorted(p for p in base.iterdir() if p.is_dir()) if base.is_dir() else []:
        f = d / "SKILL.md"
        if f.is_file():
            fm = frontmatter(f.read_text(encoding="utf-8-sig"))
            esito.append({"nome": fm.get("name") or d.name, "descrizione": fm.get("description", ""),
                          "manuale": fm.get("disable-model-invocation", "").lower() == "true"})
    return esito


def descrizione_strumento(percorso: Path) -> str:
    """La prima riga che descrive lo strumento: docstring, .SYNOPSIS, o primo commento."""
    try:
        testo = percorso.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return ""
    if percorso.suffix == ".py":
        m = re.search(r'^(?:#[^\n]*\n|\s*\n)*(?:from __future__[^\n]*\n\s*)?[rR]?("""|\'\'\')(.*?)\1', testo, re.S)
        if m:
            return next((r.strip() for r in m.group(2).splitlines() if r.strip()), "")
    if percorso.suffix == ".ps1":
        m = re.search(r"\.SYNOPSIS\s*\n\s*(.+)", testo)
        if m:
            return m.group(1).strip()
    for r in testo.splitlines():
        s = r.strip()
        if s.startswith("#!") or s in ("", "<#", "#>", "#"):
            continue
        if s.startswith("#"):
            return s.lstrip("# ").strip()
        break
    return ""


def strumenti(radice: Path) -> list:
    base = radice / ".claude/templates/tools"
    return [{"nome": p.name, "descrizione": descrizione_strumento(p)}
            for p in sorted(base.iterdir()) if p.is_file() and p.suffix in (".py", ".ps1", ".sh")] if base.is_dir() else []


def indirizzo(ident: str) -> str:
    tipo, _, resto = ident.partition(":")
    # Gli host si compongono a pezzi: scritti interi in un sorgente, il censimento delle fonti a
    # monte li scambierebbe per fonti citate dal template.
    h = "https://"
    modelli = {"github": h + "github" + ".com/%s", "npm": h + "www.npmjs" + ".com/package/%s", "pypi": h + "pypi" + ".org/project/%s",
               "crates": h + "crates" + ".io/crates/%s", "hf": h + "huggingface" + ".co/%s", "gist": h + "gist.github" + ".com/%s",
               "docker": h + "hub.docker" + ".com/r/%s"}
    if tipo in ("web", "feed"):
        return resto
    return modelli[tipo] % resto if tipo in modelli else ""


def fonti_per_pacchetto(registro: dict) -> dict:
    per = {}
    for v in registro.get("fonti", []):
        per.setdefault(v.get("pacchetto", ""), []).append(v["id"])
    return per


def cella(testo: str) -> str:
    return re.sub(r"\s+", " ", testo or "").replace("|", "\\|").strip()


def collega(ident: str) -> str:
    url = indirizzo(ident)
    nome = ident.split(":", 1)[1] if ":" in ident else ident
    nome = re.sub(r"^https?://(www\.)?", "", nome).rstrip("/")
    return "[%s](%s)" % (nome, url) if url else "`%s`" % ident


def problemi(voci: list, skill: list, attrezzi: list, dati: dict) -> list:
    esito = []
    attesi = {"pacchetto:" + v["nome"] for v in voci} | {"skill:" + s["nome"] for s in skill}
    for chiave in sorted(attesi):
        voce = dati.get(chiave)
        if not isinstance(voce, dict):
            esito.append("%s non ha una voce in %s" % (chiave, DATI))
            continue
        for c in CAMPI:
            if not str(voce.get(c, "")).strip():
                esito.append("%s: campo «%s» vuoto" % (chiave, c))
    for chiave in sorted(set(dati) - attesi):
        esito.append("%s sta nel file di dati e non sul disco" % chiave)
    for a in attrezzi:
        if not a["descrizione"]:
            esito.append("strumento %s senza una riga di descrizione in testa" % a["nome"])
    return esito


def genera(voci: list, skill: list, attrezzi: list, dati: dict, registro: dict) -> str:
    per_pacchetto = fonti_per_pacchetto(registro)
    non_dich = sum(1 for k, v in dati.items() if isinstance(v, dict) and str(v.get("quando_no", "")).strip() == NON_DICHIARATO)
    settori = []
    for v in voci:
        if v["settore"] not in settori:
            settori.append(v["settore"])
    o = []
    o.append("# Riferimento completo del template")
    o.append("")
    o.append("> Documento generato da `python .claude/templates/tools/riferimento.py --scrivi`: non si modifica a mano. Le colonne «Che cosa fa» e «Quando offrirlo» vengono dal catalogo `.claude/templates/PACKAGES.md`, le descrizioni delle skill e degli strumenti dai loro file, le fonti dal registro `.claude/templates/fonti-a-monte.json`; «Come si usa», «Perché» e «Quando no» stanno in `.claude/templates/riferimento-voci.json`, che è il solo file da correggere quando una di quelle tre frasi è sbagliata. Il commit del template si ferma se questo documento non corrisponde al disco o se una skill o un pacchetto non ha le sue tre frasi.")
    o.append("")
    o.append("## Come si legge")
    o.append("")
    o.append("Il template offre le proprie capacità in quattro forme, e questo documento le elenca tutte: %d skill di sistema, che ogni progetto istanziato riceve; %d voci di catalogo in %d settori, che il gate propone e l'utente sceglie; %d strumenti, che le skill e `chiudi` eseguono; e %d fonti a monte, sorvegliate a ogni apertura di sessione. Per ogni skill e per ogni pacchetto ci sono cinque risposte: che cosa fa, come si usa, perché adottarlo, quando conviene e quando no. Il dettaglio di un pacchetto sta nel suo `README.md` sotto `.claude/templates/<nome>/`; quello di ogni fonte, con ciò che il template ne prende e la data dell'ultima verifica, in `.claude/templates/fonti-a-monte.md`." % (len(skill), len(voci), len(settori), len(attrezzi), len(registro.get("fonti", []))))
    o.append("")
    if non_dich:
        o.append("Per %d voci il «quando no» non è dichiarato nella documentazione del pacchetto, ed è scritto così invece di essere inventato: è un debito da chiudere leggendo la fonte." % non_dich)
        o.append("")
    o.append("## Skill di sistema")
    o.append("")
    o.append("Arrivano in ogni progetto con l'istanziazione e con l'allineamento. Una skill a invocazione manuale non pesa sul contesto e si richiama con `/nome` in Claude Code o con `$nome` in Codex; le altre le carica l'agente quando riconosce la situazione.")
    o.append("")
    o.append("| Skill | Che cosa fa | Come si usa | Perché | Quando no |")
    o.append("|---|---|---|---|---|")
    for s in skill:
        d = dati.get("skill:" + s["nome"], {})
        nome = "`%s`%s" % (s["nome"], " (manuale)" if s["manuale"] else "")
        o.append("| %s | %s | %s | %s | %s |" % (nome, cella(s["descrizione"]), cella(d.get("come", "")), cella(d.get("perche", "")), cella(d.get("quando_no", ""))))
    o.append("")
    o.append("## Pacchetti, per settore")
    o.append("")
    o.append("Un pacchetto è opzionale: il gate lo propone quando riconosce il settore dai fatti del progetto, e niente si installa senza una risposta. L'ultima colonna elenca le fonti a monte che il registro lega al pacchetto.")
    for st in settori:
        o.append("")
        o.append("### " + st)
        o.append("")
        o.append("| Pacchetto | Che cosa fa | Come si usa | Perché | Quando offrirlo | Quando no | Fonti |")
        o.append("|---|---|---|---|---|---|---|")
        for v in (x for x in voci if x["settore"] == st):
            d = dati.get("pacchetto:" + v["nome"], {})
            nome = "`%s`%s" % (v["nome"], (" (" + v["tipo"] + ")") if v["tipo"] else "")
            fonti = ", ".join(collega(i) for i in sorted(per_pacchetto.get(v["nome"], []), key=str.lower)) or "nessuna"
            o.append("| %s | %s | %s | %s | %s | %s | %s |" % (nome, cella(v["cosa_fa"]), cella(d.get("come", "")), cella(d.get("perche", "")), cella(v["quando"]), cella(d.get("quando_no", "")), fonti))
    o.append("")
    o.append("## Strumenti")
    o.append("")
    o.append("Stanno in `.claude/templates/tools/` e in un progetto istanziato in `tools/`. La descrizione è la prima riga che ciascuno dichiara di sé; l'uso completo sta nella sua intestazione e in `.claude/templates/tools/README.md`.")
    o.append("")
    o.append("| Strumento | Che cosa fa |")
    o.append("|---|---|")
    for a in attrezzi:
        o.append("| `%s` | %s |" % (a["nome"], cella(a["descrizione"])))
    o.append("")
    o.append("## Fonti che non appartengono a un pacchetto")
    o.append("")
    note = sorted(k for k in per_pacchetto if k and k not in {v["nome"] for v in voci})
    o.append("Il registro lega ogni fonte a un pacchetto, a un filone o al sistema. Quelle dei pacchetti sono nelle tabelle qui sopra; le altre sono raggruppate qui per appartenenza, e il motivo di ciascuna sta in `.claude/templates/fonti-a-monte.md`.")
    o.append("")
    o.append("| Appartenenza | Fonti |")
    o.append("|---|---|")
    for k in note:
        o.append("| %s | %s |" % (cella(k), ", ".join(collega(i) for i in sorted(per_pacchetto[k], key=str.lower))))
    return "\n".join(o) + "\n"


def carica(radice: Path):
    voci = catalogo((radice / CATALOGO).read_text(encoding="utf-8-sig"))
    try:
        dati = json.loads((radice / DATI).read_text(encoding="utf-8-sig"))
    except OSError:
        dati = {}
    registro = json.loads((radice / FONTI).read_text(encoding="utf-8-sig")) if (radice / FONTI).is_file() else {}
    return voci, skill_di_sistema(radice), strumenti(radice), dati, registro


def autotest() -> int:
    import tempfile
    esiti = []

    def caso(nome, ok, dettaglio=""):
        esiti.append(ok)
        print(("ok    " if ok else "ROSSO ") + nome + ("" if ok else "  " + str(dettaglio)))

    testo = "## Catalogo\n\n### Settore uno\n\n| Pacchetto | Cosa fa | Quando offrirlo | Cosa istanzia | Note |\n|---|---|---|---|---|\n| `alfa` | Fa alfa | Quando serve alfa | file | nota |\n| `beta-mcp` (MCP) | Fa beta | Quando serve beta | niente | nota |\n\n## Aggiungere un pacchetto\n\n| `finto` | non conta | x | y | z |\n"
    voci = catalogo(testo)
    caso("il catalogo si legge per settore, anche le voci con il tipo fra parentesi", [v["nome"] for v in voci] == ["alfa", "beta-mcp"] and voci[1]["tipo"] == "MCP", voci)
    caso("una riga fuori da un settore non e' una voce", all(v["nome"] != "finto" for v in voci))
    fm = frontmatter("---\nname: prova\ndescription: >\n  Prima riga\n  seconda riga.\ndisable-model-invocation: true\n---\ncorpo\n")
    caso("la descrizione di una skill su piu' righe si ricompone", fm.get("description") == "Prima riga seconda riga." and fm.get("name") == "prova", fm)
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        (t / "a.py").write_text('#!/usr/bin/env python3\n"""Prima riga del modulo.\n\nAltro."""\n', encoding="utf-8")
        (t / "b.ps1").write_text("<#\n.SYNOPSIS\n  Fa una cosa in PowerShell.\n#>\n", encoding="utf-8")
        (t / "c.sh").write_text("#!/usr/bin/env bash\n# Fa una cosa in shell.\nset -e\n", encoding="utf-8")
        (t / "d.py").write_text("import os\n", encoding="utf-8")
        caso("la descrizione di uno strumento viene dalla docstring", descrizione_strumento(t / "a.py") == "Prima riga del modulo.")
        caso("da .SYNOPSIS per PowerShell", descrizione_strumento(t / "b.ps1") == "Fa una cosa in PowerShell.")
        caso("dal primo commento per la shell", descrizione_strumento(t / "c.sh") == "Fa una cosa in shell.")
        caso("negativo: uno strumento muto resta senza descrizione", descrizione_strumento(t / "d.py") == "")
    skill = [{"nome": "prova", "descrizione": "Fa | prove", "manuale": True}]
    attrezzi = [{"nome": "a.py", "descrizione": "Prima riga."}]
    pieno = {"pacchetto:alfa": {"come": "c", "perche": "p", "quando_no": "n"},
             "pacchetto:beta-mcp": {"come": "c", "perche": "p", "quando_no": NON_DICHIARATO},
             "skill:prova": {"come": "c", "perche": "p", "quando_no": "n"}}
    caso("con tutte le voci complete non ci sono problemi", problemi(voci, skill, attrezzi, pieno) == [])
    monco = dict(pieno)
    del monco["pacchetto:alfa"]
    caso("negativo: un pacchetto senza voce ferma", any("pacchetto:alfa" in x for x in problemi(voci, skill, attrezzi, monco)))
    vuoto = dict(pieno, **{"skill:prova": {"come": "c", "perche": "", "quando_no": "n"}})
    caso("negativo: un campo vuoto ferma", any("perche" in x for x in problemi(voci, skill, attrezzi, vuoto)))
    orfano = dict(pieno, **{"pacchetto:sparito": {"come": "c", "perche": "p", "quando_no": "n"}})
    caso("negativo: una voce che sul disco non esiste piu' ferma", any("sparito" in x for x in problemi(voci, skill, attrezzi, orfano)))
    caso("negativo: uno strumento senza descrizione ferma", any("d.py" in x for x in problemi(voci, skill, [{"nome": "d.py", "descrizione": ""}], pieno)))
    registro = {"fonti": [{"id": "github" + ":a/b", "pacchetto": "alfa"}, {"id": "web" + ":https://esempio.dev/x", "pacchetto": "filone prova"}]}
    doc = genera(voci, skill, attrezzi, pieno, registro)
    caso("il documento porta ogni pacchetto con le sue fonti collegate", ("[a/b](https://github" + ".com/a/b)") in doc and "`beta-mcp` (MCP)" in doc, doc[:300])
    caso("una barra verticale in una descrizione non rompe la tabella", "Fa \\| prove" in doc)
    caso("le fonti senza pacchetto compaiono per appartenenza", "| filone prova | [esempio.dev/x](https://esempio.dev/x) |" in doc, doc[-300:])
    caso("i «quando no» non dichiarati si contano", "Per 1 voci" in doc)
    caso("generare due volte da' lo stesso testo", doc == genera(voci, skill, attrezzi, pieno, registro))
    print("%d prove, %d fallite" % (len(esiti), esiti.count(False)))
    return 1 if False in esiti else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--radice", default=".")
    ap.add_argument("--scrivi", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--autotest", action="store_true")
    a = ap.parse_args()
    if a.autotest:
        return autotest()
    radice = Path(a.radice).resolve()
    if not (radice / ".claude/PROMPT-nuovo-progetto.md").is_file():
        print("riferimento: vale per il repository del template; qui non ha oggetto.")
        return 0
    voci, skill, attrezzi, dati, registro = carica(radice)
    guai = problemi(voci, skill, attrezzi, dati)
    testo = genera(voci, skill, attrezzi, dati, registro)
    dest = radice / USCITA
    if a.scrivi:
        dest.write_bytes(testo.encode("utf-8"))
        print("scritto %s: %d skill, %d pacchetti, %d strumenti" % (USCITA, len(skill), len(voci), len(attrezzi)))
    else:
        attuale = dest.read_bytes().decode("utf-8").replace("\r\n", "\n") if dest.is_file() else ""
        if attuale != testo:
            guai.append("%s non corrisponde al disco: rigenerare con --scrivi" % USCITA)
    for g in guai:
        print("  " + g)
    print("riferimento: %d problemi" % len(guai))
    return 1 if guai else 0


if __name__ == "__main__":
    sys.exit(main())
