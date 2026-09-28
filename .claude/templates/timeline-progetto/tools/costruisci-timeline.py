#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Costruisce la linea temporale del progetto, un microstep per voce, con la sua ragione.

Perché esiste, e perché è generata invece che scritta
-----------------------------------------------------
Un progetto lungo accumula centinaia di microstep, e di ciascuno restano due cose separate: il
fatto, che sta nel work-log e nei commit, e la ragione per cui quel fatto è stato fatto così e non
altrimenti, che sta nel registro delle decisioni o da nessuna parte. Le due cose non si leggono
insieme, quindi in pratica non si leggono: per sapere perché a marzo si è scelta una certa
tecnologia bisogna incrociare a mano un work-log in ordine inverso e un registro numerato che non
segue le stesse date.

Questo programma le mette in una linea sola. Non aggiunge informazione: la raccoglie. La regola del
sistema è che ciò che si può derivare non si scrive, e questo è il caso da manuale, perché una
linea temporale tenuta a mano diverge dal work-log entro la settimana e diventa una seconda fonte
di verità che nessuno sa più quale delle due sia.

Il vincolo che governa tutto: l'artefatto è del progetto
---------------------------------------------------------
La linea temporale e tutto ciò da cui deriva vivono dentro la cartella del progetto, tracciati da
git se il progetto lo vuole. Nulla viene scritto nella directory di configurazione dell'account
Claude, nella memoria automatica nativa o in qualunque magazzino fuori dal repository: è lo stesso
principio della sezione sull'auto-memory dello standard, cioè che tutto ciò che persiste deve
vivere dentro la cartella di progetto ed essere recuperabile da un clone. Una cronologia del
progetto che vivesse nell'account sarebbe invisibile a chiunque altro e sparirebbe con il primo
wipe, che è il modo peggiore di perdere proprio la cosa che serviva a ricordare.

Perché l'uscita è deterministica
---------------------------------
Nessuna data di generazione, nessun ordine che dipenda dal filesystem, tutto ordinato. Un file
generato che cambia a ogni corsa produce un diff a ogni commit, e un diff sempre rumoroso non si
guarda: il valore della linea temporale non è solo leggerla, è vederne il diff, perché un
intervento che aggiunge tre microstep mostra tre righe nuove e uno che ne toglie uno lo dichiara
invece di nasconderlo.

Da dove legge
-------------
Da due registri, perché un progetto può tenere i propri microstep in entrambi. Il work-log
`.claude/memory/progress.md` dà il passo con la sua data, i file toccati e il motivo; il registro
operativo `docs/OPERATIONS-LOG.md`, quando il pacchetto `operations-log` è attivo, dà il microstep
numerato con il perimetro, il legame con lo scopo del progetto e l'esito verificato. Leggere il solo
work-log su un progetto che ha anche il registro mostrerebbe meno di quanto il progetto sa di sé, e
il difetto sarebbe invisibile perché il documento prodotto resterebbe plausibile.

Del registro operativo il legame con lo scopo vale come ragione nella sua forma più propria, perché
dice a quale fase serve quell'intervento e che cosa ne dipende: è precisamente la domanda a cui una
linea temporale deve rispondere.

A entrambi si somma il registro delle decisioni `.claude/memory/decisions.md`, che dà la ragione
tecnologica per esteso quando un passo cita una delle sue voci.

L'aggancio fra un microstep e la sua ragione non si indovina: si dichiara. Una voce di work-log che
nomina `ADR-007` è agganciata a quella decisione; una che porta un campo `Ratio:` dichiara la
ragione sul posto, per i casi in cui la scelta tecnologica non merita una decisione architetturale
ma non è nemmeno ovvia. Un microstep senza né l'uno né l'altro finisce nella linea temporale con la
ragione dichiarata mancante, ed è la segnalazione più utile che questo programma produca: un fatto
senza il suo perché è esattamente ciò che il sistema esiste per non perdere.

Uso
---
    python tools/costruisci-timeline.py
    python tools/costruisci-timeline.py --out docs/TIMELINE.html
    python tools/costruisci-timeline.py --senza-ragione
    python tools/costruisci-timeline.py --self-test
"""

import argparse
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROGRESSO = os.path.join(".claude", "memory", "progress.md")
REGISTRO = os.path.join("docs", "OPERATIONS-LOG.md")
DECISIONI = os.path.join(".claude", "memory", "decisions.md")
CONTESTO = os.path.join(".claude", "context")
USCITA = os.path.join("docs", "TIMELINE.html")

RE_VOCE = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})\s*[-–]\s*(.+?)\s*$", re.M)
# Il registro dei microstep del pacchetto `operations-log`, che numera invece di
# datare nell'intestazione: la data sta fra i campi del corpo.
RE_MS = re.compile(r"^###\s+MS-(\d+)\s*[-–]\s*(.+?)\s*$", re.M)
RE_ADR = re.compile(r"^##\s+ADR-(\d+)\s*[-–]\s*(.+?)\s*$", re.M)
RE_RIF_ADR = re.compile(r"ADR-(\d+)")
RE_CAMPO = re.compile(r"(Commit|File toccati|Motivo|Ratio|Area|Data|Perimetro|Legame con il progetto|Verificato con|Esito)\s*:\s*(.*?)(?=\s+(?:Commit|File toccati|Motivo|Ratio|Area|Data|Perimetro|Legame con il progetto|Verificato con|Esito)\s*:|$)", re.S)
RE_SCHEDA = re.compile(r"^([a-z]+)-(\d+)-(.+)\.md$")

# Le aree di competenza, con il loro colore. L'identita' di un'area non e' mai affidata al solo
# colore: accanto compare sempre l'etichetta testuale, perche' un colore non si legge a voce, non
# sopravvive a una stampa in bianco e nero e non esiste per chi non lo distingue.
AREE = [
    ("architettura", "#4C6EF5"),
    ("dati", "#12B886"),
    ("interfaccia", "#F59F00"),
    ("sicurezza", "#E03131"),
    ("infrastruttura", "#7048E8"),
    ("documentazione", "#1098AD"),
    ("prove", "#2F9E44"),
    ("altro", "#868E96"),
]
COLORE = dict(AREE)


def leggi(percorso):
    if not os.path.isfile(percorso):
        return ""
    return io.open(percorso, encoding="utf-8", errors="replace").read()


def campi(blocco):
    """I campi dichiarati dentro il corpo di una voce, nella forma `Nome: valore`."""
    d = {}
    for nome, valore in RE_CAMPO.findall(blocco):
        d[nome.lower().replace(" ", "_")] = " ".join(valore.split())
    return d


def blocchi(testo, regex):
    """Spezza un documento nelle sue voci, ciascuna con il testo che la segue."""
    trovate = list(regex.finditer(testo))
    fuori = []
    for i, m in enumerate(trovate):
        fine = trovate[i + 1].start() if i + 1 < len(trovate) else len(testo)
        fuori.append((m, testo[m.end():fine].strip()))
    return fuori


def decisioni(radice=None):
    """Le decisioni architetturali per numero, con la loro motivazione."""
    testo = leggi(os.path.join(radice or ".", DECISIONI))
    fuori = {}
    for m, corpo in blocchi(testo, RE_ADR):
        numero = int(m.group(1))
        motivazione = ""
        mm = re.search(r"Motivazione\s*:\s*(.*?)(?=\s+Conseguenze\s*:|$)", corpo, re.S)
        if mm:
            motivazione = " ".join(mm.group(1).split())
        fuori[numero] = {"numero": numero, "titolo": m.group(2), "motivazione": motivazione}
    return fuori


def schede(radice=None):
    """Le schede didattiche presenti, per numero, quando il pacchetto e' attivo."""
    cartella = os.path.join(radice or ".", CONTESTO)
    fuori = {}
    if not os.path.isdir(cartella):
        return fuori
    for nome in sorted(os.listdir(cartella)):
        m = RE_SCHEDA.match(nome)
        if not m:
            continue
        fuori.setdefault(m.group(1), {})[int(m.group(2))] = nome
    return fuori


def dal_registro(radice=None, adr=None):
    """I microstep del registro operativo, quando il progetto ha quel pacchetto attivo.

    Il legame con lo scopo del progetto e' la ragione nella sua forma piu' propria: dice a quale
    fase serve quell'intervento e che cosa ne dipende, che e' precisamente la domanda a cui una
    linea temporale deve rispondere. Dove manchi vale il campo `Ratio:` come nel work-log, e dove
    manchino entrambi il passo resta dichiarato scoperto.
    """
    testo = leggi(os.path.join(radice or ".", REGISTRO))
    adr = adr if adr is not None else decisioni(radice)
    fuori = []
    for m, corpo in blocchi(testo, RE_MS):
        # Il modello del pacchetto porta una voce di esempio con i segnaposto fra parentesi
        # angolari: non e' un microstep e non deve comparire nella linea temporale.
        if "&lt;" in corpo or "<titolo" in corpo:
            continue
        c = campi(corpo)
        data = c.get("data", "")
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", data):
            continue
        riferite = sorted(set(int(x) for x in RE_RIF_ADR.findall(corpo)))
        ragione, fonte = "", ""
        if c.get("legame_con_il_progetto"):
            ragione, fonte = c["legame_con_il_progetto"], "legame dichiarato nel registro"
        elif c.get("ratio"):
            ragione, fonte = c["ratio"], "dichiarata nel registro"
        elif riferite:
            prime = [adr[n]["motivazione"] for n in riferite if n in adr and adr[n]["motivazione"]]
            if prime:
                ragione, fonte = prime[0], "ADR-%03d" % riferite[0]
        area = (c.get("area") or "altro").lower()
        if area not in COLORE:
            area = "altro"
        fuori.append({
            "data": data,
            "titolo": "MS-%s - %s" % (m.group(1), m.group(2)),
            "commit": (c.get("commit") or "").split()[0] if c.get("commit") else "",
            "file": c.get("perimetro", ""),
            "motivo": c.get("esito", ""),
            "ragione": ragione,
            "fonte": fonte,
            "adr": riferite,
            "area": area,
        })
    return fuori


def microstep(radice=None):
    """Le voci del work-log, ciascuna con la sua ragione quando e' dichiarata."""
    testo = leggi(os.path.join(radice or ".", PROGRESSO))
    adr = decisioni(radice)
    fuori = []
    for m, corpo in blocchi(testo, RE_VOCE):
        c = campi(corpo)
        riferite = sorted(set(int(x) for x in RE_RIF_ADR.findall(corpo)))
        ragione, fonte = "", ""
        if c.get("ratio"):
            ragione, fonte = c["ratio"], "dichiarata nel work-log"
        elif riferite:
            prime = [adr[n]["motivazione"] for n in riferite if n in adr and adr[n]["motivazione"]]
            if prime:
                ragione = prime[0]
                fonte = "ADR-%03d" % riferite[0]
        area = (c.get("area") or "altro").lower()
        if area not in COLORE:
            area = "altro"
        fuori.append({
            "data": m.group(1),
            "titolo": m.group(2),
            "commit": (c.get("commit") or "").split()[0] if c.get("commit") else "",
            "file": c.get("file_toccati", ""),
            "motivo": c.get("motivo", ""),
            "ragione": ragione,
            "fonte": fonte,
            "adr": riferite,
            "area": area,
        })
    fuori += dal_registro(radice, adr)
    # L'ordine e' cronologico crescente e a parita' di data segue il titolo: deterministico, e
    # indipendente dall'ordine in cui le due fonti sono scritte, che nel work-log e' inverso.
    fuori.sort(key=lambda v: (v["data"], v["titolo"]))
    return fuori


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def html(voci, nome_progetto):
    """La linea temporale come file unico e autosufficiente, senza data di generazione."""
    senza = [v for v in voci if not v["ragione"]]
    per_area = {}
    for v in voci:
        per_area[v["area"]] = per_area.get(v["area"], 0) + 1

    r = []
    r.append("<!DOCTYPE html>")
    r.append('<html lang="it"><head><meta charset="utf-8">')
    r.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
    r.append("<title>" + esc(nome_progetto) + " &mdash; linea temporale</title>")
    r.append("<style>")
    r.append(":root{--fg:#1A1D21;--bg:#FBFBFD;--muted:#6B7280;--line:#E5E7EB;--card:#FFFFFF}")
    r.append("@media(prefers-color-scheme:dark){:root{--fg:#E8EAED;--bg:#15171A;"
             "--muted:#9AA3AE;--line:#2A2E34;--card:#1C1F24}}")
    r.append("*{box-sizing:border-box}body{margin:0;padding:2rem 1rem;background:var(--bg);"
             "color:var(--fg);font:15px/1.65 -apple-system,Segoe UI,Roboto,sans-serif}")
    r.append(".wrap{max-width:900px;margin:0 auto}")
    r.append("h1{font-family:Georgia,serif;font-size:1.6rem;margin:0 0 .3rem}")
    r.append(".sub{color:var(--muted);font-size:13px;margin:0 0 2rem;max-width:62ch}")
    r.append(".legenda{display:flex;flex-wrap:wrap;gap:.4rem;margin-bottom:2rem}")
    r.append(".tag{display:inline-flex;align-items:center;gap:.35rem;font-size:11px;"
             "padding:.15rem .5rem;border:1px solid var(--line);border-radius:999px;"
             "background:var(--card)}")
    r.append(".pallino{width:9px;height:9px;border-radius:50%;flex:0 0 auto}")
    r.append(".step{position:relative;padding:0 0 1.6rem 1.6rem;border-left:2px solid var(--line)}")
    r.append(".step:last-child{border-left-color:transparent}")
    r.append(".dot{position:absolute;left:-6px;top:6px;width:10px;height:10px;border-radius:50%;"
             "border:2px solid var(--bg)}")
    r.append(".data{font:11px/1 ui-monospace,Consolas,monospace;color:var(--muted);"
             "letter-spacing:.06em}")
    r.append(".tit{font-weight:600;margin:.25rem 0 .4rem}")
    r.append(".why{background:var(--card);border:1px solid var(--line);border-radius:8px;"
             "padding:.6rem .8rem;font-size:13.5px}")
    r.append(".why b{font-weight:600}")
    r.append(".manca{border-style:dashed;color:var(--muted)}")
    r.append(".meta{font:11px/1.5 ui-monospace,Consolas,monospace;color:var(--muted);"
             "margin-top:.4rem;word-break:break-word}")
    r.append(".nota{margin-top:2.5rem;padding-top:1rem;border-top:1px solid var(--line);"
             "color:var(--muted);font-size:12.5px}")
    r.append("</style></head><body><div class=\"wrap\">")
    r.append("<h1>" + esc(nome_progetto) + "</h1>")
    r.append('<p class="sub">Linea temporale del progetto, un microstep per voce, con la ragione '
             "tecnologica adottata per quel passo. Documento generato dal work-log e dal registro "
             "delle decisioni: non si scrive a mano e non si corregge a mano, si rigenera. "
             "Vive nel repository del progetto e da nessun'altra parte.</p>")

    r.append('<div class="legenda">')
    for area, colore in AREE:
        if per_area.get(area):
            r.append('<span class="tag"><span class="pallino" style="background:%s"></span>%s (%d)'
                     "</span>" % (colore, esc(area), per_area[area]))
    r.append("</div>")

    for v in voci:
        colore = COLORE[v["area"]]
        r.append('<div class="step">')
        r.append('<span class="dot" style="background:%s"></span>' % colore)
        r.append('<div class="data">%s &middot; %s</div>' % (esc(v["data"]), esc(v["area"])))
        r.append('<div class="tit">%s</div>' % esc(v["titolo"]))
        if v["ragione"]:
            r.append('<div class="why"><b>Perché così:</b> %s <span class="meta">fonte: %s</span>'
                     "</div>" % (esc(v["ragione"]), esc(v["fonte"])))
        else:
            r.append('<div class="why manca"><b>Ragione non dichiarata.</b> Il fatto è registrato, '
                     "il perché no: si dichiara con un campo <code>Ratio:</code> nella voce del "
                     "work-log, oppure citando la decisione che lo motiva.</div>")
        meta = []
        if v["motivo"]:
            meta.append("motivo: " + esc(v["motivo"]))
        if v["file"]:
            meta.append("file: " + esc(v["file"]))
        if v["commit"]:
            meta.append("commit: " + esc(v["commit"]))
        if meta:
            r.append('<div class="meta">' + " &middot; ".join(meta) + "</div>")
        r.append("</div>")

    r.append('<p class="nota">%d microstep, di cui %d senza una ragione dichiarata. '
             "L'area di ciascuno si dichiara con un campo <code>Area:</code> nella voce del "
             "work-log; senza, il passo resta classificato come altro. Il colore non porta mai "
             "l'informazione da solo: accanto c'è sempre l'etichetta.</p>"
             % (len(voci), len(senza)))
    r.append("</div></body></html>")
    return "\n".join(r) + "\n"


# ------------------------------------------------------------------------------------------
# Le prove, su un albero sintetico.
# ------------------------------------------------------------------------------------------

def self_test():
    import shutil
    import tempfile
    esiti = []

    def prova(nome, condizione, dettaglio=""):
        esiti.append((nome, bool(condizione), dettaglio))

    tmp = tempfile.mkdtemp(prefix="timeline-")
    try:
        def scrivi(rel, testo):
            p = os.path.join(tmp, rel)
            d = os.path.dirname(p)
            if d and not os.path.isdir(d):
                os.makedirs(d)
            io.open(p, "w", encoding="utf-8", newline="\n").write(testo)

        scrivi(PROGRESSO, "\n".join([
            "# Work-log", "",
            "## 2026-03-02 - Secondo passo",
            "Commit: bbb2222 Area: dati Motivo: serviva leggere il formato nuovo. "
            "Scelta motivata in ADR-002.", "",
            "## 2026-03-01 - Primo passo",
            "Commit: aaa1111 Area: architettura File toccati: src/uno.py "
            "Motivo: separare il calcolo dalla resa. Ratio: la resa cambia ogni mese e il "
            "calcolo no, quindi separarli rende il pezzo stabile indipendente da quello volatile.",
            "",
            "## 2026-03-03 - Terzo passo senza perche'",
            "Commit: ccc3333 Motivo: richiesto.", ""]))
        scrivi(DECISIONI, "\n".join([
            "# Registro", "",
            "## ADR-002 - Formato di scambio",
            "Data: 2026-03-02 Stato: accettata Contesto: due sistemi devono parlarsi. "
            "Decisione: adottare il formato colonnare. "
            "Motivazione: il volume rende il costo di lettura dominante, e il colonnare lo abbatte "
            "sulle query che il progetto fa davvero. Conseguenze: serve una conversione una tantum.",
            ""]))

        voci = microstep(tmp)
        prova("legge tutti i microstep", len(voci) == 3, str(len(voci)))
        prova("l'ordine e' cronologico crescente e non quello del file",
              [v["data"] for v in voci] == ["2026-03-01", "2026-03-02", "2026-03-03"],
              str([v["data"] for v in voci]))
        prova("una ragione dichiarata sul posto si prende da li'",
              voci[0]["ragione"].startswith("la resa cambia ogni mese")
              and voci[0]["fonte"] == "dichiarata nel work-log", str(voci[0]))
        prova("una decisione citata porta la propria motivazione",
              "colonnare lo abbatte" in voci[1]["ragione"] and voci[1]["fonte"] == "ADR-002",
              str(voci[1]))
        prova("un microstep senza perche' resta senza, e non se ne inventa uno",
              voci[2]["ragione"] == "", str(voci[2]))
        prova("l'area dichiarata si conserva", voci[0]["area"] == "architettura", voci[0]["area"])
        prova("un'area non dichiarata cade su altro", voci[2]["area"] == "altro", voci[2]["area"])
        prova("i campi si separano senza mangiarsi a vicenda",
              voci[0]["file"] == "src/uno.py"
              and voci[0]["motivo"].startswith("separare il calcolo"), str(voci[0]))

        pagina = html(voci, "Progetto di prova")
        prova("la pagina nomina il microstep senza ragione come tale",
              "Ragione non dichiarata" in pagina, "")
        prova("la pagina conta i microstep senza ragione", "di cui 1 senza" in pagina, "")
        prova("la pagina non porta una data di generazione, quindi il diff e' leggibile",
              "generato il" not in pagina.lower(), "")
        prova("la pagina e' autosufficiente e non chiama la rete",
              "http://" not in pagina and "https://" not in pagina, "")
        prova("l'area non e' affidata al solo colore",
              "architettura</div>" in pagina or "&middot; architettura" in pagina, "")
        prova("due corse identiche producono lo stesso byte",
              html(microstep(tmp), "Progetto di prova") == pagina, "")

        # La seconda fonte: il registro dei microstep, quando il pacchetto e' attivo.
        scrivi(REGISTRO, "\n".join([
            "# Registro", "",
            "### MS-001 - Allestito il collettore",
            "Data: 2026-03-01 Area: infrastruttura Perimetro: il servizio di raccolta. "
            "Legame con il progetto: senza il collettore la fase di analisi non ha dati, quindi "
            "ogni passo successivo dipende da questo. Verificato con: una lettura di prova. "
            "Esito: fatto.", "",
            "### MS-002 - Ruotate le credenziali",
            "Data: 2026-03-05 Perimetro: il deposito segreti. Verificato con: un accesso. "
            "Esito: fatto.", "",
            "### MS-009 - Voce senza data",
            "Perimetro: qualcosa. Esito: fatto.", "",
            "### MS-00N - <titolo che dichiara il fatto>",
            "Perimetro: &lt;segnaposto&gt;. Esito: &lt;fatto&gt;.", ""]))
        unite = microstep(tmp)
        titoli = [v["titolo"] for v in unite]
        prova("le due fonti confluiscono in una linea sola",
              any(x.startswith("MS-001") for x in titoli) and "Primo passo" in titoli, str(titoli))
        prova("il legame con lo scopo vale come ragione del microstep",
              any(v["fonte"] == "legame dichiarato nel registro" for v in unite),
              str([(v["titolo"], v["fonte"]) for v in unite]))
        prova("negativo: la voce di esempio del modello non entra nella linea",
              not any("MS-00N" in x for x in titoli), str(titoli))
        prova("negativo: una voce del registro senza data non entra",
              not any("MS-009" in x for x in titoli), str(titoli))
        prova("un microstep del registro senza legame resta scoperto",
              any(v["titolo"].startswith("MS-002") and not v["ragione"] for v in unite),
              str([(v["titolo"], v["ragione"]) for v in unite]))
        prova("l'ordine resta cronologico attraverso le due fonti",
              [v["data"] for v in unite] == sorted(v["data"] for v in unite),
              str([v["data"] for v in unite]))

        # Il caso che rompe una pagina senza farlo notare.
        scrivi(PROGRESSO, "# Work-log\n\n## 2026-03-04 - Un titolo con <script> dentro\n"
                          "Commit: ddd4444 Motivo: prova. Ratio: <b>grassetto</b> non voluto.\n")
        pagina2 = html(microstep(tmp), "X")
        prova("il testo di una voce non puo' iniettare marcatura",
              "<script>" not in pagina2 and "&lt;script&gt;" in pagina2, "")

        # Un progetto che non ha ancora niente non deve rompersi.
        vuoto = tempfile.mkdtemp(prefix="timeline-vuoto-")
        try:
            prova("un progetto senza work-log non fa cadere il programma",
                  microstep(vuoto) == [], "")
            prova("e produce comunque una pagina valida",
                  html([], "Vuoto").startswith("<!DOCTYPE html>"), "")
        finally:
            shutil.rmtree(vuoto, ignore_errors=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    larghezza = max(len(n) for n, _, _ in esiti)
    falliti = 0
    for nome, ok, dettaglio in esiti:
        if not ok:
            falliti += 1
        print("  %s  %s%s" % (nome.ljust(larghezza), "ok" if ok else "FALLITO",
                              ("  " + dettaglio[:150]) if (dettaglio and not ok) else ""))
    print("")
    print("%d prove, %d fallite." % (len(esiti), falliti))
    return 1 if falliti else 0


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--out", default=USCITA, help="dove scrivere la linea temporale")
    p.add_argument("--nome", help="nome del progetto mostrato in testata")
    p.add_argument("--radice", help="radice del progetto; per difetto la cartella corrente")
    p.add_argument("--senza-ragione", action="store_true",
                   help="elenca a schermo i soli microstep senza ragione dichiarata, e basta")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args()

    if a.self_test:
        return self_test()

    base = a.radice or "."
    voci = microstep(a.radice)
    if not voci:
        sys.stderr.write("nessun microstep: serve un work-log in " + PROGRESSO
                         + " con voci nella forma `## AAAA-MM-GG - titolo`\n")
        return 1

    if a.senza_ragione:
        senza = [v for v in voci if not v["ragione"]]
        for v in senza:
            print("%s  %s" % (v["data"], v["titolo"]))
        print("")
        print("%d microstep su %d senza una ragione dichiarata" % (len(senza), len(voci)))
        return 1 if senza else 0

    nome = a.nome or os.path.basename(os.path.abspath(base))
    destinazione = os.path.join(base, a.out) if not os.path.isabs(a.out) else a.out
    cartella = os.path.dirname(destinazione)
    if cartella and not os.path.isdir(cartella):
        os.makedirs(cartella)
    io.open(destinazione, "w", encoding="utf-8", newline="\n").write(html(voci, nome))
    senza = len([v for v in voci if not v["ragione"]])
    print("%d microstep scritti in %s" % (len(voci), destinazione))
    if senza:
        print("%d senza una ragione dichiarata: si vedono con --senza-ragione" % senza)
    return 0


if __name__ == "__main__":
    sys.exit(main())
