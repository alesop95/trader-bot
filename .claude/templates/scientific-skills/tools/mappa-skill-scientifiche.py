#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera la mappa delle skill scientifiche di K-Dense, con autore, licenza e rischio.

Perché esiste, e perché non è un installatore
----------------------------------------------
La raccolta `K-Dense-AI/scientific-agent-skills` contiene centosessantasei skill e si installa
già benissimo da sola: `gh skill install <repo> <nome>` ne prende una per volta, la mette nella
cartella giusta per l'host che si usa e registra la provenienza, e `--pin` la blocca a un tag o
a un commit. Riscrivere quel meccanismo qui sarebbe duplicare una funzione che esiste, che è
precisamente ciò che il catalogo di questo sistema si vieta.

Ciò che non esiste a monte è la vista che serve per decidere quale prendere. Il README della
raccolta elenca le categorie in prosa, e le prime righe del suo avviso di sicurezza dicono la
cosa che conta: non installarle tutte, leggere il file di ciascuna prima di prenderla, e sapere
che le skill scritte da terzi non hanno avuto la stessa revisione di quelle della casa. Tutti e
tre quei criteri sono verificabili meccanicamente, perché stanno nel frontmatter e nella forma
della cartella, e nessuno li ha mai messi in una tabella. Questo programma li mette.

Le tre proprietà che decide, e perché sono quelle
--------------------------------------------------
La prima è chi ha scritto la skill. Il campo `skill-author` del frontmatter distingue la casa
dagli altri, e la distinzione è dichiarata dalla raccolta stessa come differenza di profondità
della revisione, non come giudizio di qualità.

La seconda è la licenza. Nella raccolta convivono licenze permissive e alcune proprietarie, e
una licenza proprietaria dentro un insieme presentato come MIT è esattamente il genere di cosa
che nessuno guarda finché non serve.

La terza è se la skill porti con sé programmi eseguibili, cioè una cartella `scripts/`. Una
skill di sola documentazione e una che porta codice sono due classi di rischio diverse, e la
seconda è quella per cui l'avviso di sicurezza della raccolta suggerisce di passare uno
scanner prima di installare.

Da dove legge
-------------
Da una copia locale della raccolta, non dalla rete, perché la copia serve comunque per leggere
il file di una skill prima di prenderla e perché un programma che scarica duecento megabyte per
produrre una tabella è il genere di comodità che si paga due volte. La copia si fa una volta
con un clone parziale, che prende i testi e non gli allegati.

    git clone --depth 1 --filter=blob:none --sparse https://github.com/K-Dense-AI/scientific-agent-skills.git .tmp-skills
    git -C .tmp-skills sparse-checkout set skills

La cartella `.tmp-skills` è esclusa da git dal blocco di questo pacchetto nel `.gitignore`.
Per aggiornarla si esegue `git -C .tmp-skills pull`, e rigenerando la mappa si vede che cosa è
cambiato a monte, che è la stessa strategia a costo zero del pacchetto `claude-code-handoff`.

Uso
---
    python tools/mappa-skill-scientifiche.py --da .tmp-skills
    python tools/mappa-skill-scientifiche.py --da .tmp-skills --out docs/MAPPA-SKILL-SCIENTIFICHE.md
    python tools/mappa-skill-scientifiche.py --da .tmp-skills --settore "Bioinformatics"
    python tools/mappa-skill-scientifiche.py --self-test
"""

import argparse
import collections
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CASA = "K-Dense"

# Le skill che coprono una capacità già presente nel catalogo di questo sistema. La tabella è
# piccola e scritta a mano di proposito: è conoscenza del catalogo, non della raccolta a monte,
# quindi non si può ricavare dai file di là e va aggiornata qui quando il catalogo cambia. Una
# voce dice quale pacchetto di questo sistema copre già quel terreno, perché al gate la domanda
# non è se la skill sia buona ma se aggiunga qualcosa a ciò che il progetto ha già.
SOVRAPPOSIZIONI = {
    "literature-review": "academic-researcher, notebooklm-bridge",
    "paper-lookup": "academic-researcher, arxiv-cli, academix",
    "research-lookup": "academic-researcher, academix",
    "bgpt-paper-search": "academic-researcher, semantic-scholar-mcp",
    "paperclip": "academic-researcher, paperqa2",
    "paperzilla": "academic-researcher, paperqa2",
    "scholar-evaluation": "academic-researcher",
    "peer-review": "academic-researcher",
    "citation-management": "book-bib-extract, zotero-mcp, refchecker-mcp",
    "pyzotero": "zotero-mcp",
    "exa-search": "notebooklm-bridge",
    "docx": "doc-ingest, docx-to-docs",
    "pdf": "doc-ingest, book-to-skill",
    "pptx": "doc-ingest",
    "xlsx": "doc-ingest",
    "markitdown": "doc-ingest",
    "liteparse": "doc-ingest",
    "latex-posters": "latex",
    "venue-templates": "latex",
    "markdown-mermaid-writing": "diagrams",
    "scientific-schematics": "diagrams",
    "scientific-visualization": "la skill nativa dataviz",
    "matplotlib": "la skill nativa dataviz",
    "seaborn": "la skill nativa dataviz",
    "infographics": "la skill nativa dataviz",
    "scientific-writing": "interaction-style.md, humanizer",
    "open-notebook": "knowledge-wiki, operations-log",
}


def frontmatter(testo):
    """Il blocco YAML iniziale come dizionario piatto, senza una libreria per farlo.

    Si legge a mano perché il frontmatter di una skill è piatto per contratto, tranne il blocco
    `metadata`, di cui interessa una chiave sola. Una dipendenza per leggere sei campi non si
    giustifica in un pacchetto che per il resto non ne ha.
    """
    if not testo.startswith("---"):
        return {}
    fine = testo.find("\n---", 3)
    if fine < 0:
        return {}
    d = {}
    for riga in testo[3:fine].splitlines():
        m = re.match(r"^\s{0,4}([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$", riga)
        if not m:
            continue
        chiave, valore = m.group(1), m.group(2).strip()
        # Le virgolette compaiono in una parte delle voci e non in tutte: senza toglierle lo
        # stesso autore risulterebbe due autori diversi, che e' un difetto che si vede solo
        # contando e che falserebbe il conteggio su cui poggia il gate.
        if len(valore) >= 2 and valore[0] == valore[-1] and valore[0] in "\"'":
            valore = valore[1:-1]
        if chiave not in d or not d[chiave]:
            d[chiave] = valore
    return d


def leggi(radice):
    """Legge le skill dalla copia locale e ritorna una riga per ciascuna."""
    cartella = os.path.join(radice, "skills")
    if not os.path.isdir(cartella):
        raise SystemExit("non trovo " + cartella + ": serve una copia locale della raccolta, e "
                         "il comando per farla sta nella documentazione di questo programma")
    righe = []
    for nome in sorted(os.listdir(cartella)):
        percorso = os.path.join(cartella, nome, "SKILL.md")
        if not os.path.isfile(percorso):
            continue
        with io.open(percorso, encoding="utf-8", errors="replace") as fh:
            testo = fh.read()
        fm = frontmatter(testo)
        autore = fm.get("skill-author", "") or "(non dichiarato)"
        licenza = normalizza_licenza(fm.get("license", ""))
        righe.append({
            "nome": fm.get("name", nome),
            "cartella": nome,
            "autore": autore,
            "della_casa": CASA.lower() in autore.lower(),
            "licenza": licenza,
            "proprietaria": "propriet" in licenza.lower(),
            "scripts": os.path.isdir(os.path.join(cartella, nome, "scripts")),
            "descrizione": " ".join((fm.get("description", "") or "").split()),
            "copre_gia": SOVRAPPOSIZIONI.get(nome, ""),
        })
    return righe


def normalizza_licenza(valore):
    """Riduce alla stessa forma le grafie diverse della stessa licenza.

    Nella raccolta la stessa licenza compare scritta in tre modi, per esempio con e senza la
    parola che la segue. Senza questa riduzione il conteggio per licenza produce tre righe dove
    ce n'e' una, e chi guarda la tabella conclude che la raccolta sia piu' eterogenea di quanto
    sia. La riduzione tocca la sola forma e mai la sostanza: due licenze diverse restano due.
    """
    v = (valore or "").strip().strip("\"'")
    if not v:
        return "(non dichiarata)"
    v = re.sub(r"\s+license$", "", v, flags=re.I)
    if v.lower().startswith("propriet"):
        return "Proprietaria"
    return v


def conteggi(righe):
    return {
        "totale": len(righe),
        "della_casa": sum(1 for r in righe if r["della_casa"]),
        "di_terzi": sum(1 for r in righe if not r["della_casa"]),
        "con_scripts": sum(1 for r in righe if r["scripts"]),
        "proprietarie": sum(1 for r in righe if r["proprietaria"]),
        "sovrapposte": sum(1 for r in righe if r["copre_gia"]),
        "licenze": collections.Counter(r["licenza"] for r in righe),
        "autori_terzi": collections.Counter(r["autore"] for r in righe if not r["della_casa"]),
    }


def settori(radice):
    """Le categorie dichiarate dal README a monte, con il numero che ciascuna dichiara.

    Si leggono di la' invece di inventarle qui per la stessa ragione per cui il censimento delle
    fonti del pacchetto `community-sources` eredita le intestazioni della fonte: una tassonomia
    scritta da chi conosce il dominio e' quasi sempre migliore di una inventata da chi lo sta
    imparando, e resta confrontabile con l'originale quando l'originale cambia.
    """
    percorso = os.path.join(radice, "README.md")
    if not os.path.isfile(percorso):
        return []
    with io.open(percorso, encoding="utf-8", errors="replace") as fh:
        testo = fh.read()
    fuori = []
    for m in re.finditer(r"^####\s+\S*\s*\*\*(.+?)\*\*\s*\((\d+)\s+skills?\)", testo, re.M):
        fuori.append((m.group(1).strip(), int(m.group(2))))
    return fuori


def markdown(righe, elenco_settori, radice):
    c = conteggi(righe)
    r = []
    r.append("# Mappa delle skill scientifiche")
    r.append("")
    r.append("> Documento generato da `tools/mappa-skill-scientifiche.py` leggendo una copia locale di `K-Dense-AI/scientific-agent-skills`. Non si scrive a mano: si rigenera. Le tre colonne che contano sono l'autore, la licenza e la presenza di programmi eseguibili, perché sono i tre criteri che l'avviso di sicurezza della raccolta chiede di guardare prima di installare.")
    r.append("")
    r.append("## In breve")
    r.append("")
    r.append("Sono %d skill. Ne ha scritte %d la casa che mantiene la raccolta e %d altri autori, e la differenza è dichiarata a monte come differenza di profondità della revisione. Ne portano programmi eseguibili %d, cioè la maggioranza, ed è la classe per cui vale passare uno scanner prima di installare. Ne hanno licenza proprietaria %d, dentro una raccolta che si presenta come MIT. E %d coprono un terreno che un pacchetto di questo sistema già copre."
             % (c["totale"], c["della_casa"], c["di_terzi"], c["con_scripts"],
                c["proprietarie"], c["sovrapposte"]))
    r.append("")
    r.append("| Licenza | Skill |")
    r.append("|---|---|")
    for licenza, n in c["licenze"].most_common():
        r.append("| %s | %d |" % (licenza, n))
    r.append("")
    if c["autori_terzi"]:
        r.append("Gli autori diversi dalla casa, con quante skill ciascuno: "
                 + ", ".join("%s (%d)" % (a, n) for a, n in c["autori_terzi"].most_common())
                 + ".")
        r.append("")

    if elenco_settori:
        r.append("## I settori, come li dichiara la raccolta")
        r.append("")
        r.append("Sono la tassonomia di chi la mantiene, letta dal suo README e non inventata qui. Servono al gate dei pacchetti per capire quale porzione della raccolta riguardi un progetto: quasi sempre è una sola riga di questa tabella.")
        r.append("")
        r.append("| Settore | Skill dichiarate |")
        r.append("|---|---|")
        for nome, n in elenco_settori:
            r.append("| %s | %d |" % (nome, n))
        r.append("")
        somma = sum(n for _, n in elenco_settori)
        if somma != c["totale"]:
            r.append("Le categorie dichiarano %d skill in totale contro le %d presenti sul disco. Lo scarto non è un errore di questo programma: le categorie del README si sovrappongono e alcune skill vi compaiono due volte o nessuna. Va letto come indicazione della grandezza di un settore, non come conteggio." % (somma, c["totale"]))
            r.append("")

    r.append("## Le skill che questo sistema copre già")
    r.append("")
    r.append("Righe da non prendere senza avere deciso quale delle due capacità resta in uso, e da registrare come decisione quando si prende comunque quella di là.")
    r.append("")
    r.append("| Skill | Che cosa in questo sistema copre già lo stesso terreno |")
    r.append("|---|---|")
    for x in righe:
        if x["copre_gia"]:
            r.append("| `%s` | %s |" % (x["cartella"], x["copre_gia"]))
    r.append("")

    r.append("## Tutte le skill")
    r.append("")
    r.append("La colonna del codice dice se la skill porta una cartella `scripts/` con programmi eseguibili. La colonna dell'autore dice soltanto se sia della casa: e lo fa secondo il criterio che la raccolta stessa indica per sapere quanta revisione quella skill abbia avuto.")
    r.append("")
    r.append("| Skill | Autore | Licenza | Codice | Che cosa fa |")
    r.append("|---|---|---|---|---|")
    for x in righe:
        descrizione = x["descrizione"]
        if len(descrizione) > 240:
            descrizione = descrizione[:237].rsplit(" ", 1)[0] + "..."
        r.append("| `%s` | %s | %s | %s | %s |"
                 % (x["cartella"], "casa" if x["della_casa"] else x["autore"].replace("|", "/"),
                    x["licenza"], "si" if x["scripts"] else "no",
                    descrizione.replace("|", "/")))
    r.append("")
    r.append("Copia letta in `%s`." % radice.replace("\\", "/"))
    return "\n".join(r) + "\n"


# ------------------------------------------------------------------------------------------
# Le prove, contro un albero sintetico e senza rete.
# ------------------------------------------------------------------------------------------

def self_test():
    import shutil
    import tempfile
    esiti = []

    def prova(nome, condizione, dettaglio=""):
        esiti.append((nome, bool(condizione), dettaglio))

    tmp = tempfile.mkdtemp(prefix="mappa-skill-")
    try:
        def skill(nome, autore, licenza, con_scripts, descrizione, virgolette=False):
            d = os.path.join(tmp, "skills", nome)
            os.makedirs(d)
            if con_scripts:
                os.makedirs(os.path.join(d, "scripts"))
            a = ('"%s"' % autore) if virgolette else autore
            testo = ("---\nname: %s\ndescription: %s\nlicense: %s\nmetadata:\n"
                     "  version: \"1.0\"\n  skill-author: %s\n---\n\n# %s\n"
                     % (nome, descrizione, licenza, a, nome))
            io.open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8").write(testo)

        skill("alfa", "K-Dense Inc.", "MIT", True, "fa una cosa")
        skill("beta", "K-Dense Inc.", "MIT license", False, "ne fa un'altra", virgolette=True)
        skill("pdf", "Anthropic, PBC", "Proprietary. LICENSE.txt has complete terms", True,
              "legge i PDF")
        skill("gamma", "Terzo Autore", "Apache-2.0", True, "fa una terza cosa")
        io.open(os.path.join(tmp, "README.md"), "w", encoding="utf-8").write(
            "#### x **Primo settore** (3 skills)\n- roba\n#### y **Secondo settore** (2 skills)\n")

        righe = leggi(tmp)
        c = conteggi(righe)
        prova("legge tutte le skill", c["totale"] == 4, str(c["totale"]))
        prova("le virgolette attorno all'autore non ne creano uno nuovo",
              c["della_casa"] == 2, str(c["della_casa"]))
        prova("un autore di terze parti si conta come tale", c["di_terzi"] == 2, str(c["di_terzi"]))
        prova("il codice eseguibile si rileva dalla cartella", c["con_scripts"] == 3,
              str(c["con_scripts"]))
        prova("una licenza proprietaria si riconosce nonostante la frase attorno",
              c["proprietarie"] == 1, str(c["proprietarie"]))
        prova("le grafie diverse della stessa licenza non fanno due licenze",
              c["licenze"]["MIT"] == 2, str(dict(c["licenze"])))
        prova("la sovrapposizione con il catalogo si segnala",
              [x for x in righe if x["cartella"] == "pdf"][0]["copre_gia"] != "", "")
        prova("negativo: una skill senza corrispondenza non ne inventa una",
              [x for x in righe if x["cartella"] == "alfa"][0]["copre_gia"] == "", "")

        s = settori(tmp)
        prova("i settori si leggono dal README a monte", s == [("Primo settore", 3),
                                                               ("Secondo settore", 2)], str(s))
        testo = markdown(righe, s, tmp)
        prova("la mappa dichiara lo scarto fra i settori e le skill presenti",
              "contro le 4 presenti" in testo, "")
        prova("la mappa porta tutte le skill", testo.count("| `") >= 4, "")
        prova("la mappa dice dove ha letto", tmp.replace("\\", "/") in testo, "")

        # Il caso che rompe una tabella Markdown senza farlo notare.
        skill("delta", "K-Dense Inc.", "MIT", False, "una descrizione con | dentro")
        testo2 = markdown(leggi(tmp), s, tmp)
        righe_tabella = [x for x in testo2.splitlines() if x.startswith("| `delta`")]
        prova("una barra verticale nella descrizione non spezza la tabella",
              righe_tabella and righe_tabella[0].count("|") == 6, str(righe_tabella))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    larghezza = max(len(n) for n, _, _ in esiti)
    falliti = 0
    for nome, ok, dettaglio in esiti:
        if not ok:
            falliti += 1
        print("  %s  %s%s" % (nome.ljust(larghezza), "ok" if ok else "FALLITO",
                              ("  " + dettaglio) if (dettaglio and not ok) else ""))
    print("")
    print("%d prove, %d fallite." % (len(esiti), falliti))
    return 1 if falliti else 0


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--da", help="cartella della copia locale della raccolta")
    p.add_argument("--out", default="MAPPA-SKILL-SCIENTIFICHE.md")
    p.add_argument("--settore", help="stampa a schermo le sole skill il cui testo nomina questo settore")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args()

    if a.self_test:
        return self_test()
    if not a.da:
        p.error("serve --da con la cartella della copia locale")

    righe = leggi(a.da)
    if a.settore:
        ago = a.settore.lower()
        trovate = [x for x in righe if ago in x["descrizione"].lower() or ago in x["cartella"]]
        for x in trovate:
            print("%-32s %-6s %s" % (x["cartella"], "codice" if x["scripts"] else "-",
                                     x["descrizione"][:110]))
        print("")
        print("%d skill su %d nominano %s" % (len(trovate), len(righe), a.settore))
        return 0

    testo = markdown(righe, settori(a.da), a.da)
    cartella = os.path.dirname(a.out)
    if cartella and not os.path.isdir(cartella):
        os.makedirs(cartella)
    io.open(a.out, "w", encoding="utf-8", newline="\n").write(testo)
    c = conteggi(righe)
    print("%d skill mappate in %s" % (c["totale"], a.out))
    print("%d della casa, %d di terzi, %d con codice eseguibile, %d proprietarie, %d gia' coperte"
          % (c["della_casa"], c["di_terzi"], c["con_scripts"], c["proprietarie"], c["sovrapposte"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
