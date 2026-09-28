#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Segnala nel codice di un'interfaccia i tratti dell'estetica generica da modello.

Perché esiste
-------------
Un modello che genera un'interfaccia senza indicazioni converge su scelte "in distribuzione",
cioè le più frequenti nel materiale da cui ha imparato, e il risultato è riconoscibile: sfondo
crema con accento caldo, una parola del titolo in corsivo, un'etichetta maiuscola sopra ogni
titolo, card dentro card, le stesse icone, la sezione "come funziona" in tre passi. Il catalogo
dei tratti, con le fonti, sta in `GUIDA.md` del pacchetto `anti-slop`. Questo programma li cerca
nei sorgenti, perché si notano meglio sul codice che sul rendering, dove sembrano scelte.

Che cosa cerca
--------------
U1  palette crema e accento caldo: uno sfondo chiaro e caldo insieme a un accento ambra,
    arancio o terracotta, nei valori esadecimali o nelle classi di utilità.
U2  la sezione in tre passi: "come funziona" o "how it works" con i marcatori 01, 02, 03.
U3  una parola del titolo in corsivo: un h1 o h2 che contiene em, i o una classe italic.
U4  etichette sopra i titoli: elementi maiuscoli spaziati, più di uno ogni tre titoli.
U5  card annidate: tre o più contenitori a card uno dentro l'altro.
U6  icone scontate: quattro o più icone del gruppo fulmine, scudo, grafico, puzzle, cuffia,
    spunta, scintille, razzo importate nello stesso file.
U7  decorazione estranea: una finta finestra di terminale, con i tre pallini colorati.
U8  sezioni gemelle: tre o più sezioni con la stessa identica classe.
U9  contrasto insufficiente: una regola CSS con colore del testo e dello sfondo espliciti il
    cui rapporto di contrasto è sotto 4.5:1, la soglia WCAG 1.4.3 per il testo normale.
U10 caratteri predefiniti: Inter, Roboto, Arial, Space Grotesk come carattere principale, o i
    serif da titolo che le fonti indicano come preferiti dai modelli.

Che cosa non può sapere
-----------------------
Legge i sorgenti, non il rendering: non vede ciò che un componente produce a runtime, non
risolve i temi e non conosce la palette di un framework di utilità, di cui riconosce solo i nomi
delle classi. Un tratto segnalato non è un errore ma una scelta da motivare: uno sfondo crema può
essere l'identità del marchio, e allora la sua ragione va scritta. Il contrasto U9 è l'unico
controllo normativo, e vale solo dove testo e sfondo sono dichiarati nella stessa regola.

Uso
---
    python tools/lint-ui.py <cartella del frontend> [...]
    python tools/lint-ui.py --gate <cartella>       esce 1 se trova qualcosa
    python tools/lint-ui.py --self-test
"""

import argparse
import colorsys
import io
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ESCLUSE = {".git", "node_modules", ".venv", "__pycache__", "dist", "build", "out", ".next",
           "target", "coverage", ".svelte-kit", ".nuxt"}
ESTENSIONI = (".html", ".htm", ".css", ".scss", ".sass", ".less", ".jsx", ".tsx", ".js", ".ts",
              ".vue", ".svelte", ".astro")

HEX = re.compile(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
SFONDO_CALDO_CLASSI = re.compile(r"\bbg-(amber|orange|stone|yellow)-(50|100)\b")
ACCENTO_CALDO_CLASSI = re.compile(r"\bbg-(amber|orange)-(300|400|500|600)\b")
PASSI = re.compile(r"(how it works|come funziona|in tre passi|three steps|3 steps)", re.I)
MARCATORI = [re.compile(r">\s*0?%d\s*<|['\"]0?%d['\"]" % (n, n)) for n in (1, 2, 3)]
TITOLO = re.compile(r"<(h[12])\b[^>]*>(.*?)</\1>", re.I | re.S)
CORSIVO = re.compile(r"<(em|i)\b|class(Name)?=[\"'][^\"']*\bitalic\b", re.I)
ETICHETTA = re.compile(r"class(Name)?=[\"'][^\"']*\buppercase\b[^\"']*\btracking-[\w\[\].-]+"
                       r"|class(Name)?=[\"'][^\"']*\btracking-[\w\[\].-]+[^\"']*\buppercase\b", re.I)
TITOLI = re.compile(r"<h[1-3]\b", re.I)
TAG = re.compile(r"<(/?)(div|section|article|aside|li)\b([^>]*)>", re.I)
CARD = re.compile(r"\bcard\b|(?=[^\"']*\brounded[\w-]*)(?=[^\"']*\b(shadow|border)\b)", re.I)
ICONE = {"Zap", "Bolt", "Shield", "ShieldCheck", "BarChart", "BarChart2", "BarChart3", "ChartBar",
         "TrendingUp", "Puzzle", "PuzzlePiece", "Headphones", "Headset", "CheckCircle",
         "CheckCircle2", "CircleCheck", "Sparkles", "Rocket"}
IMPORT_ICONE = re.compile(r"import\s*\{([^}]*)\}\s*from\s*['\"](lucide-react|lucide-vue-next|"
                          r"@heroicons/react[^'\"]*|react-icons[^'\"]*|@phosphor-icons/react)['\"]")
SEMAFORO = [re.compile(p, re.I) for p in (r"#ff5f56|#ff5f57|bg-red-(400|500)",
                                          r"#ffbd2e|#febc2e|bg-yellow-(400|500)",
                                          r"#27c93f|#28c840|bg-green-(400|500)")]
SEZIONE_INTERA = re.compile(r"<section\b[^>]*>(.*?)</section>", re.I | re.S)
APERTURA = re.compile(r"<([a-zA-Z][\w-]*)\b")
REGOLA_CSS = re.compile(r"([^{}]+)\{([^{}]*)\}")
FONT = re.compile(r"font-family\s*:\s*['\"]?(Inter|Roboto|Arial|Space Grotesk|Fraunces|Instrument Serif)\b"
                  r"|\bfont-\[?['\"]?(Inter|Fraunces)\b", re.I)
FONT_NEXT = re.compile(r"import\s*\{[^}]*\b(Inter|Roboto|Space_Grotesk|Fraunces|Instrument_Serif)\b[^}]*\}"
                       r"\s*from\s*['\"]next/font/google['\"]")


def rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def luminanza(c):
    def canale(v):
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (canale(v) for v in c)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrasto(a, b):
    la, lb = sorted((luminanza(a), luminanza(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def caldo_chiaro(c):
    h, l, s = colorsys.rgb_to_hls(*c)
    return l >= 0.88 and 0.02 <= s <= 0.75 and 20 / 360 <= h <= 60 / 360


def accento_caldo(c):
    h, l, s = colorsys.rgb_to_hls(*c)
    return 0.35 <= l <= 0.75 and s >= 0.5 and 8 / 360 <= h <= 48 / 360


def cammina(radice):
    if os.path.isfile(radice):
        yield radice
        return
    for dirpath, dirnames, filenames in os.walk(radice):
        dirnames[:] = [d for d in dirnames if d not in ESCLUSE]
        for nome in sorted(filenames):
            if nome.lower().endswith(ESTENSIONI) and not nome.endswith((".min.js", ".min.css")):
                yield os.path.join(dirpath, nome)


def esamina_file(testo):
    """Ritorna (esiti del file, fatti per il progetto)."""
    esiti, fatti = [], {"sfondo_caldo": False, "accento_caldo": False}
    colori = [rgb(m.group(0)) for m in HEX.finditer(testo)]
    if any(caldo_chiaro(c) for c in colori) or SFONDO_CALDO_CLASSI.search(testo):
        fatti["sfondo_caldo"] = True
    if any(accento_caldo(c) for c in colori) or ACCENTO_CALDO_CLASSI.search(testo):
        fatti["accento_caldo"] = True

    if PASSI.search(testo) and all(m.search(testo) for m in MARCATORI):
        esiti.append(("U2", "sezione in tre passi numerati"))

    for m in TITOLO.finditer(testo):
        if CORSIVO.search(m.group(0)):
            esiti.append(("U3", "una parola del titolo %s in corsivo" % m.group(1).lower()))
            break
        # La stessa enfasi fatta con un colore: uno span che isola una parte breve del titolo,
        # "Accenting just a single word or phrase in a headline" nella fonte (FONTI.md, F06).
        interno = re.search(r"<span\b[^>]*>([^<]{1,60})</span>", m.group(2), re.I)
        if interno and len(re.sub(r"<[^>]+>", "", m.group(2)).split()) > len(interno.group(1).split()):
            esiti.append(("U3", "una parte del titolo %s isolata e accentata: «%s»"
                          % (m.group(1).lower(), interno.group(1).strip()[:40])))
            break

    # Le etichette si riconoscono anche quando lo stile sta in una classe CSS del file: una regola
    # con maiuscolo e spaziatura delle lettere definisce una classe di etichetta, e si contano gli
    # elementi che la usano.
    classi_etichetta = set()
    for r in REGOLA_CSS.finditer(testo):
        if re.search(r"text-transform\s*:\s*uppercase", r.group(2), re.I) and \
                re.search(r"letter-spacing\s*:\s*[.\d]", r.group(2), re.I):
            classi_etichetta |= set(re.findall(r"\.([\w-]+)\s*$", r.group(1).strip()))
    # Conta solo gli elementi seguiti subito da un titolo: un badge o una didascalia maiuscola non
    # è un'etichetta sopra un titolo, che è il segno descritto dalla fonte.
    uso_css = sum(len(re.findall(r"class=[\"'](?:[^\"']*\s)?%s(?:\s[^\"']*)?[\"'][^>]*>[^<]{0,120}"
                                 r"</[\w-]+>\s*<h[1-3]\b" % re.escape(c), testo, re.I))
                  for c in classi_etichetta)
    etichette, titoli = len(ETICHETTA.findall(testo)) + uso_css, len(TITOLI.findall(testo))
    if etichette >= 2 and etichette * 3 > max(titoli, 1):
        esiti.append(("U4", "%d etichette maiuscole spaziate per %d titoli" % (etichette, titoli)))

    pila, massimo = [], 0
    for m in TAG.finditer(testo):
        if m.group(1):
            if pila:
                pila.pop()
        elif not m.group(3).rstrip().endswith("/"):
            pila.append(bool(CARD.search(m.group(3))))
            massimo = max(massimo, sum(pila))
    if massimo >= 3:
        esiti.append(("U5", "%d card annidate una dentro l'altra" % massimo))

    icone = set()
    for m in IMPORT_ICONE.finditer(testo):
        icone |= {n.strip().split(" as ")[0].replace("Icon", "") for n in m.group(1).split(",")} & ICONE
    if len(icone) >= 4:
        esiti.append(("U6", "icone scontate: " + ", ".join(sorted(icone))))

    if all(p.search(testo) for p in SEMAFORO):
        esiti.append(("U7", "finta finestra con i tre pallini: verificare che serva al prodotto"))

    # Il segno non è la classe comune, che è normale pratica CSS, ma la stessa struttura interna
    # ripetuta: si confronta lo scheletro dei primi tag di ogni sezione, ignorando testo e classi.
    scheletri = []
    for m in SEZIONE_INTERA.finditer(testo):
        tag = APERTURA.findall(m.group(1))[:10]
        if len(tag) >= 3:
            scheletri.append(" ".join(t.lower() for t in tag))
    for sk in set(scheletri):
        if scheletri.count(sk) >= 3:
            esiti.append(("U8", "%d sezioni con la stessa struttura interna (%s)"
                          % (scheletri.count(sk), sk[:50])))

    for m in REGOLA_CSS.finditer(testo):
        corpo = m.group(2)
        testo_c = re.search(r"(?<![\w-])color\s*:\s*(#[0-9a-fA-F]{3,6})\b", corpo)
        sfondo_c = re.search(r"background(-color)?\s*:\s*(#[0-9a-fA-F]{3,6})\b", corpo)
        if testo_c and sfondo_c:
            r = contrasto(rgb(testo_c.group(1)), rgb(sfondo_c.group(2)))
            if r < 4.5:
                esiti.append(("U9", "contrasto %.2f:1 sotto 4.5:1 in «%s»" % (r, m.group(1).strip()[:40])))

    f = FONT.search(testo) or FONT_NEXT.search(testo)
    if f:
        nome = next((g for g in f.groups() if g), "")
        if nome:
            esiti.append(("U10", "carattere predefinito o preferito dai modelli: " + nome.replace("_", " ")))
    return esiti, fatti


def esamina(radici):
    esiti, sfondo, accento = [], [], []
    for radice in radici:
        for percorso in cammina(radice):
            try:
                testo = io.open(percorso, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            trovati, fatti = esamina_file(testo)
            esiti.extend((percorso, u, d) for u, d in trovati)
            if fatti["sfondo_caldo"]:
                sfondo.append(percorso)
            if fatti["accento_caldo"]:
                accento.append(percorso)
    if sfondo and accento:
        esiti.insert(0, ("(progetto)", "U1", "sfondo chiaro caldo (%s) con accento ambra o terracotta "
                         "(%s)" % (os.path.basename(sfondo[0]), os.path.basename(accento[0]))))
    return esiti


def self_test():
    import shutil
    import tempfile
    esiti = []

    def prova(nome, condizione, dettaglio=""):
        esiti.append((nome, bool(condizione), dettaglio))

    def codici(testo, nome="pagina.html"):
        d = tempfile.mkdtemp(prefix="lint-ui-")
        try:
            io.open(os.path.join(d, nome), "w", encoding="utf-8").write(testo)
            return {u for _, u, _ in esamina([d])}
        finally:
            shutil.rmtree(d, ignore_errors=True)

    prova("U1: crema con accento terracotta si segnala",
          "U1" in codici("body{background:#F4F1EA} .btn{background:#D97757}"))
    prova("negativo U1: crema senza accento caldo non basta",
          "U1" not in codici("body{background:#F4F1EA} .btn{background:#1d4ed8}"))
    prova("U2: tre passi numerati si segnalano",
          "U2" in codici("<h2>How it works</h2><b>01</b><b>02</b><b>03</b>"))
    prova("U3: una parola del titolo in corsivo si segnala",
          "U3" in codici("<h1>Build the future of <em>work</em></h1>"))
    prova("negativo U3: un corsivo fuori dal titolo non si segnala",
          "U3" not in codici("<h1>Build the future</h1><p><em>work</em></p>"))
    prova("U4: un'etichetta maiuscola per ogni titolo si segnala",
          "U4" in codici('<p class="uppercase tracking-widest">A</p><h2>x</h2>'
                         '<p class="uppercase tracking-widest">B</p><h2>y</h2>'))
    prova("U3: una frase del titolo isolata in uno span si segnala",
          "U3" in codici("<h1>Potenzialità e fonti<br><span>in un flusso reale</span></h1>"))
    prova("negativo U3: un titolo tutto dentro uno span non si segnala",
          "U3" not in codici("<h1><span>Potenzialità e fonti</span></h1>"))
    prova("U4: etichette definite da una classe CSS maiuscola e spaziata si segnalano",
          "U4" in codici("<style>.eye{text-transform:uppercase;letter-spacing:.2em}</style>"
                         '<div class="eye">A</div><h2>x</h2><div class="eye">B</div><h2>y</h2>'))
    prova("negativo U4: badge maiuscoli spaziati lontani dai titoli non si segnalano",
          "U4" not in codici("<style>.tag{text-transform:uppercase;letter-spacing:.1em}</style>"
                             '<h2>x</h2><p>t</p><span class="tag">A</span><span class="tag">B</span>'
                             '<span class="tag">C</span>'))
    prova("U5: tre card annidate si segnalano",
          "U5" in codici('<div class="card"><div class="card"><div class="card">x</div></div></div>'))
    prova("negativo U5: tre card affiancate non si segnalano",
          "U5" not in codici('<div class="card">a</div><div class="card">b</div><div class="card">c</div>'))
    prova("U6: quattro icone scontate si segnalano",
          "U6" in codici("import { Zap, Shield, BarChart3, Puzzle } from 'lucide-react'", "a.tsx"))
    prova("U7: la finta finestra di terminale si segnala",
          "U7" in codici('<span class="bg-red-500"></span><span class="bg-yellow-500"></span>'
                         '<span class="bg-green-500"></span>'))
    gemella = '<section class="s"><h2>T</h2><p>t</p><img src="x"><a href="#">L</a></section>'
    prova("U8: tre sezioni con la stessa struttura interna si segnalano",
          "U8" in codici(gemella * 3))
    prova("negativo U8: la stessa classe su sezioni di struttura diversa non si segnala",
          "U8" not in codici('<section class="s"><h2>A</h2><p>a</p><ul><li>x</li></ul></section>'
                             '<section class="s"><h2>B</h2><table><tr><td>b</td></tr></table></section>'
                             '<section class="s"><blockquote><p>c</p></blockquote><a>d</a></section>'))
    prova("U9: testo bianco su ambra sotto 4.5:1 si segnala",
          "U9" in codici(".btn{color:#ffffff;background:#f59e0b}", "a.css"))
    prova("negativo U9: testo nero su ambra non si segnala",
          "U9" not in codici(".btn{color:#000000;background:#f59e0b}", "a.css"))
    r = contrasto(rgb("#ffffff"), rgb("#000000"))
    prova("il contrasto bianco su nero vale 21:1 come da definizione WCAG", abs(r - 21.0) < 0.01, "%.2f" % r)
    prova("U10: Inter importato da next/font si segnala",
          "U10" in codici("import { Inter } from 'next/font/google'", "layout.tsx"))

    larghezza = max(len(n) for n, _, _ in esiti)
    falliti = 0
    for nome, ok, dettaglio in esiti:
        if not ok:
            falliti += 1
        print("  %s  %s%s" % (nome.ljust(larghezza), "ok" if ok else "FALLITO",
                              ("  " + dettaglio[:120]) if (dettaglio and not ok) else ""))
    print("")
    print("%d prove, %d fallite." % (len(esiti), falliti))
    return 1 if falliti else 0


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("percorsi", nargs="*", default=["."])
    p.add_argument("--gate", action="store_true", help="esce 1 se trova qualcosa")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args()
    if a.self_test:
        return self_test()
    esiti = esamina(a.percorsi)
    per = {}
    for percorso, u, d in esiti:
        per[u] = per.get(u, 0) + 1
        print("%s  %s  %s" % (percorso, u, d))
    print("")
    print("%d segnalazioni: %s" % (len(esiti), ", ".join("%s %d" % (k, per[k]) for k in sorted(per)) or "nessuna"))
    print("Sono scelte da motivare, non errori, salvo U9 che misura una soglia WCAG. Il perché di "
          "ciascuna sta in GUIDA.md del pacchetto anti-slop.")
    return 1 if (a.gate and esiti) else 0


if __name__ == "__main__":
    sys.exit(main())
