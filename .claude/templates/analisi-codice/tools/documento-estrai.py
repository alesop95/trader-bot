"""Estrae da una pagina gia' prodotta il suo contenuto, come Markdown, separandolo dalla grafica.

Primo passo della pipeline di produzione. Le pagine di governance esistenti tengono incollate due
cose: il testo del documento e il design system incorporato. Misurato il 04/11/2026 su sei pagine,
5.399.995 byte in tutto, il testo e' fra l'1,0 e il 3,9 per cento del file; il resto e' la stessa
copia della grafica ripetuta sei volte. Finche' restano incollate, ogni modifica e' chirurgia su
marcatura, nessun documento si puo' consegnare in un altro formato senza rifarlo, e un cambio di
marchio costa la riscrittura di tutti i file.

Questo strumento scioglie l'incollatura nella sola direzione che si puo' fare senza perdere
niente: dalla pagina al contenuto. La direzione opposta, dal contenuto alla pagina, e' il
generatore, e la prova che la separazione e' corretta sara' il confronto fra la pagina rigenerata
e quella di partenza.

La convenzione del Markdown prodotto e' Markdown normale piu' attributi in stile Pandoc, che sono
leggibili a occhio e non richiedono di imparare niente di nuovo. Un occhiello di sezione diventa
un attributo del titolo, `## Titolo {occhiello="Titolarita'"}`. Un sommario diventa una citazione
subito dopo il titolo. Un riquadro diventa un richiamo `> [!riquadro]`. Un'etichetta come lacuna
dichiarata diventa `[testo]{.vuoto}`. Le tabelle restano tabelle.

La decorazione non entra nel contenuto. Le forme e i colori dei segni accanto agli occhielli sono
scelte del design system e il generatore le assegna da se': tenerle qui significherebbe chiedere a
chi scrive un documento di decidere il colore di un quadratino.

Lo strumento non legge niente dalla knowledge base e non scrive mai dentro il repository
tracciato: lavora sul file che gli si indica e scrive accanto, o dove gli si dice.

    python tools/documento-estrai.py _notes/pagine/registro-trattamenti.html
    python tools/documento-estrai.py <pagina> --uscita _notes/documenti/registro.md
    python tools/documento-estrai.py --autotest
"""

import argparse
import html as _html
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

BLOCCHI = ("p", "h1", "h2", "h3", "h4", "table", "div", "section", "ul", "ol", "li", "tr")


def testo(frammento):
    """Riduce un frammento di marcatura al suo testo, conservando i corsivi, i codici e i segni."""
    s = frammento
    s = re.sub(r"(?s)<svg.*?</svg>", "", s)
    s = re.sub(r"(?s)<br\s*/?>", " ", s)
    s = re.sub(r'(?s)<span class="vuoto">(.*?)</span>', r"[\1]{.vuoto}", s)
    s = re.sub(r"(?s)<span class=\"cod\">(.*?)</span>", r"`\1`", s)
    s = re.sub(r"(?s)<code>(.*?)</code>", r"`\1`", s)
    s = re.sub(r"(?s)<em>(.*?)</em>", r"*\1*", s)
    s = re.sub(r"(?s)<strong>(.*?)</strong>", r"**\1**", s)
    s = re.sub(r"(?s)<a [^>]*href=\"(.*?)\"[^>]*>(.*?)</a>", r"[\2](\1)", s)
    s = re.sub(r"(?s)<[^>]+>", "", s)
    s = _html.unescape(s)
    s = re.sub(r"[ \t\r\n]+", " ", s)
    return s.strip()


def attributi(occhiello):
    """Rende l'occhiello come attributo di titolo, o stringa vuota se non c'e'."""
    if not occhiello:
        return ""
    return ' {occhiello="%s"}' % occhiello.replace('"', "'")


def tabella(frammento):
    """Converte una tabella in tabella Markdown. Una cella sta su una riga sola, sempre."""
    intestazioni = [testo(c) for c in re.findall(r"(?s)<th[^>]*>(.*?)</th>", frammento)]
    righe = []
    corpo = re.search(r"(?s)<tbody[^>]*>(.*?)</tbody>", frammento)
    sorgente = corpo.group(1) if corpo else frammento
    for tr in re.findall(r"(?s)<tr[^>]*>(.*?)</tr>", sorgente):
        celle = [testo(c) for c in re.findall(r"(?s)<td[^>]*>(.*?)</td>", tr)]
        if celle:
            righe.append(celle)
    if not intestazioni and not righe:
        return []
    larghezza = max([len(intestazioni)] + [len(r) for r in righe]) if righe or intestazioni else 0
    if not intestazioni:
        intestazioni = [""] * larghezza
    intestazioni += [""] * (larghezza - len(intestazioni))
    intestazioni = [c if c else "Campo %d" % (i + 1) for i, c in enumerate(intestazioni)]

    fuori = ["::: schede"]
    for n, r in enumerate(righe):
        if n:
            fuori.append("---")
        r = r + [""] * (larghezza - len(r))
        for colonna, valore in zip(intestazioni, r):
            # Un'etichetta come lacuna dichiarata sta dentro la cella della descrizione ma non e'
            # descrizione: e' lo stato della voce. Diventa percio' un campo suo, e il generatore
            # la rimette davanti al campo che segue.
            m = re.match(r"^\[(.*?)\]\{\.vuoto\}\s*(.*)$", valore, re.S)
            if m:
                fuori.append("Stato: " + m.group(1).strip())
                valore = m.group(2).strip()
            fuori.append("%s: %s" % (colonna, valore))
    fuori.append(":::")
    return fuori


def riquadro(frammento):
    """Converte un riquadro in richiamo, con il titolo interno come prima riga."""
    fuori = ["> [!riquadro]"]
    for tag, contenuto in re.findall(r"(?s)<(h3|h4|p)[^>]*>(.*?)</\1>", frammento):
        t = testo(contenuto)
        if not t:
            continue
        fuori.append("> " + ("**%s**" % t if tag in ("h3", "h4") else t))
        fuori.append(">")
    while fuori and fuori[-1] == ">":
        fuori.pop()
    return fuori


def sezione(frammento, prima):
    """Converte una sezione: occhiello sul titolo, sommario come citazione, poi il resto in ordine."""
    fuori = []
    m = re.search(r'(?s)<div class="(?:eyebrow|occhiello)">(.*?)</div>', frammento)
    occhiello = testo(m.group(1)) if m else ""

    # I segni grafici degli occhielli sono SVG, e un SVG contiene elementi i cui nomi cominciano
    # come quelli del testo: `path` comincia come `p`. Senza questa rimozione, e senza il confine
    # di parola imposto sotto, un `<path>` apre un finto paragrafo che si richiude al primo `</p>`
    # vero, cioe' centinaia di righe piu' avanti, inghiottendo titolo e tabella senza un errore.
    # Misurato il 04/11/2026 sul registro: una sezione su sei, la sola con una stella al posto di
    # un rettangolo, e' uscita come un unico paragrafo di prosa concatenata.
    frammento = re.sub(r"(?s)<svg.*?</svg>", "", frammento)

    for pezzo in re.finditer(
            r'(?s)<(h1|h2|h3)(?=[\s>])[^>]*>(.*?)</\1>'
            r'|<p(?=[\s>])[^>]*class="(?:standfirst|sommario)"[^>]*>(.*?)</p>'
            r'|<div(?=[\s>])[^>]*class="riquadro"[^>]*>(.*?)</div>'
            r'|<table(?=[\s>])[^>]*>(.*?)</table>'
            r'|<p(?=[\s>])(?![^>]*class="(?:standfirst|sommario)")[^>]*>(.*?)</p>', frammento):
        tag, titolo, sommario, box, tab, par = pezzo.groups()
        if titolo is not None:
            livello = "#" if (tag == "h1" or prima) and tag != "h3" else "##"
            if tag == "h3":
                livello = "###"
            t = testo(titolo)
            if t:
                fuori += ["", livello + " " + t + attributi(occhiello), ""]
                occhiello = ""
        elif sommario is not None:
            t = testo(sommario)
            if t:
                fuori += ["> " + t, ""]
        elif box is not None:
            fuori += riquadro(box) + [""]
        elif tab is not None:
            fuori += tabella("<table>" + tab + "</table>") + [""]
        elif par is not None:
            t = testo(par)
            if t:
                fuori += [t, ""]
    return fuori


def converti(pagina):
    """Dalla pagina intera al Markdown. Torna (testo, numero di sezioni trovate)."""
    # Il corpo comincia dopo la testa. Si taglia all'ultimo </style> perche' un foglio di
    # stile incorporato contiene testo che somiglia a marcatura, ma una pagina che al foglio
    # si collega invece di incorporarlo non ha nessuno </style>: senza il ripiego su </head>
    # il taglio andrebbe a -1 e il corpo si ridurrebbe all'ultimo carattere della pagina.
    # Difetto trovato il 09/11/2026 dal giro chiuso di documento-genera.py, alla sua prima corsa.
    taglio = max(pagina.rfind("</style>"), pagina.rfind("</head>"))
    corpo = pagina[taglio:] if taglio >= 0 else pagina
    titolo = re.search(r"(?s)<title>(.*?)</title>", pagina)
    revisione = re.search(r'(?s)<div class="nav">(.*?)</div>', corpo)

    testa = ["---"]
    if titolo:
        testa.append("titolo: %s" % testo(titolo.group(1)))
    if revisione:
        etichette = [testo(x) for x in re.findall(r"(?s)<span[^>]*>(.*?)</span>", revisione.group(1))]
        etichette = [e for e in etichette if e]
        if etichette:
            testa.append("intestazione: %s" % " | ".join(etichette))
    utility = re.search(r'(?s)<div class="utility">(.*?)</div>', corpo)
    if utility:
        etichette = [testo(x) for x in re.findall(r"(?s)<span[^>]*>(.*?)</span>", utility.group(1))]
        etichette = [e for e in etichette if e]
        if etichette:
            testa.append("etichette: %s" % " | ".join(etichette))

    # La testata e' l'occhiello, il titolo e il sommario del documento, non di una sezione,
    # e vive fuori dalle sezioni. Senza questa lettura spariva in silenzio: il 09/11/2026 la
    # pagina che descrive questo impianto l'aveva e il contenuto estratto no, e nessuno se
    # n'era accorto perche' il risultato sembrava completo.
    testata = re.search(r'(?s)<(?:header|div)[^>]*class="testata"[^>]*>(.*?)</(?:header|div)>',
                        corpo)
    if testata:
        # Gli SVG dei segni vanno via prima, altrimenti la ricerca del testo dell'occhiello
        # si ferma al primo tag chiuso, che e' il </svg>, e l'occhiello risulta vuoto.
        dentro = re.sub(r'(?s)<svg.*?</svg>', '', testata.group(1))
        occhiello = re.search(
            r'(?s)class="(?:eyebrow|occhiello)"[^>]*>(.*?)</(?:span|div|p)>', dentro)
        sommario = re.search(r'(?s)class="(?:standfirst|sommario)"[^>]*>(.*?)</p>', dentro)
        if occhiello and testo(occhiello.group(1)):
            testa.append("occhiello: %s" % testo(occhiello.group(1)))
        if sommario and testo(sommario.group(1)):
            testa.append("sommario: %s" % testo(sommario.group(1)))

    testa.append("---")

    sezioni = re.findall(r"(?s)<section[^>]*>(.*?)</section>", corpo)
    righe = list(testa)
    for i, s in enumerate(sezioni):
        righe += sezione(s, prima=(i == 0))

    fuori = []
    for r in righe:
        if r == "" and fuori and fuori[-1] == "":
            continue
        fuori.append(r)
    return "\n".join(fuori).strip() + "\n", len(sezioni)


PROVA = """<html><head><title>Documento di prova</title><style>x</style></head><body>
<div class="utility"><span class="label muta">Etichetta</span></div>
<div class="nav"><span class="marchio">Prova</span><span class="label muta">Revisione 0</span></div>
<main><section>
<div class="eyebrow"><svg class="pin" viewBox="0 0 11 11"><path d="M5.5 0l1.6 3.4L11 4z" fill="#AFD100"/></svg><span class="label">Occhiello</span></div>
<h1>Titolo<br>spezzato</h1>
<p class="standfirst">Sommario della prova.</p>
<div class="riquadro"><h3>Titolo del riquadro</h3><p>Corpo del riquadro.</p></div>
<p>Un paragrafo con <em>corsivo</em> e <span class="cod">codice</span>.</p>
<table><thead><tr><th>A</th><th>B</th></tr></thead>
<tbody><tr><td>uno</td><td><span class="vuoto">Lacuna dichiarata</span> due</td></tr></tbody></table>
</section></main></body></html>"""


def autotest():
    """Verifica che ogni costrutto sopravviva alla conversione, perche' una perdita e' silenziosa."""
    md, n = converti(PROVA)
    attese = [
        ("titolo del documento", "titolo: Documento di prova"),
        ("etichette di testata", "etichette: Etichetta"),
        ("titolo con a capo sciolto", "# Titolo spezzato"),
        ("occhiello come attributo", 'occhiello="Occhiello"'),
        ("sommario come citazione", "> Sommario della prova."),
        ("riquadro come richiamo", "> [!riquadro]"),
        ("titolo del riquadro", "> **Titolo del riquadro**"),
        ("corsivo", "*corsivo*"),
        ("codice in linea", "`codice`"),
        ("apertura del blocco a schede", "::: schede"),
        ("chiusura del blocco a schede", "\n:::"),
        ("campo dalla prima colonna", "A: uno"),
        ("stato estratto dalla cella", "Stato: Lacuna dichiarata"),
        ("resto della cella dopo lo stato", "B: due"),
        ("titolo non inghiottito da un path di SVG", "# Titolo spezzato"),
    ]
    mancanti = [nome for nome, atteso in attese if atteso not in md]
    if n != 1:
        print("autotest fallito: sezioni trovate %d invece di 1" % n)
        return 1
    if mancanti:
        print("autotest fallito: %d costrutti persi nella conversione" % len(mancanti))
        for x in mancanti:
            print("   " + x)
        print("--- prodotto ---")
        print(md)
        return 1
    if "<" in md or "&nbsp;" in md:
        print("autotest fallito: marcatura residua nel Markdown prodotto")
        return 1
    print("autotest: %d costrutti su %d sopravvivono alla conversione" % (len(attese), len(attese)))
    return 0


def copertura(pagina):
    """Che cosa la conversione NON ha convertito, invece di saltarlo in silenzio.

    Il giro chiuso fra generatore ed estrattore dimostra che i due sono inversi fra loro, non
    che l'estrattore veda tutto cio' che la pagina contiene: sono due proprieta' diverse, e la
    seconda e' quella che e' mancata. Il 09/11/2026 una pagina scritta a mano usava un
    vocabolario di classi diverso da quello noto, e l'occhiello, il sommario e la testata sono
    stati scartati senza che nessuno strumento lo dicesse; il contenuto sembrava completo perche'
    cio' che manca non si vede. Questo controllo conta gli elementi di blocco dentro le sezioni e
    li confronta con quelli che la conversione ha davvero raccolto, ed elenca le classi incontrate
    che nessuna regola riconosce.

    Non e' una prova di correttezza: e' una prova che niente e' stato ignorato. Un elemento
    decorativo puo' legittimamente non essere convertito, e per questo le classi si elencano
    invece di far fallire il controllo, perche' solo una persona sa se una classe sia contenuto.
    """
    corpo_inizio = max(pagina.rfind("</style>"), pagina.rfind("</head>"))
    corpo = pagina[corpo_inizio:] if corpo_inizio >= 0 else pagina
    sezioni = re.findall(r"(?s)<section[^>]*>(.*?)</section>", corpo)

    presenti = raccolti = 0
    for frammento in sezioni:
        senza_svg = re.sub(r"(?s)<svg.*?</svg>", "", frammento)
        presenti += len(re.findall(r"<(?:h1|h2|h3|p|table|ul|ol)(?=[\s>])", senza_svg))
        raccolti += len([r for r in sezione(frammento, prima=False) if r.strip()])

    note = {"eyebrow", "occhiello", "standfirst", "sommario", "riquadro", "vuoto", "cod",
            "nav", "utility", "testata", "label", "muta", "marchio", "pin"}
    viste = set()
    for valore in re.findall(r'class="([^"]+)"', corpo):
        viste.update(valore.split())
    ignote = sorted(v for v in viste - note if not v.startswith("riga-"))

    return {"sezioni": len(sezioni), "blocchi": presenti, "raccolti": raccolti,
            "classi_ignote": ignote,
            "testata": bool(re.search(r'class="testata"', corpo)),
            "occhielli": len(re.findall(r'class="(?:eyebrow|occhiello)"', corpo))}


def main(argv=None):
    p = argparse.ArgumentParser(description="Estrae il contenuto di una pagina prodotta, come Markdown.")
    p.add_argument("pagina", nargs="?", help="pagina HTML da cui estrarre")
    p.add_argument("--uscita", help="file Markdown da scrivere; senza, stampa a video")
    p.add_argument("--autotest", action="store_true", help="prova la conversione su un documento finto")
    p.add_argument("--copertura", action="store_true",
                   help="dice che cosa la conversione non ha convertito, e non scrive niente")
    a = p.parse_args(argv)

    if a.autotest:
        return autotest()
    if not a.pagina:
        p.error("serve una pagina, oppure --autotest")

    if a.copertura:
        f = Path(a.pagina)
        if not f.is_file():
            print("pagina inesistente: %s" % f)
            return 2
        c = copertura(f.read_text(encoding="utf-8", errors="replace"))
        print("%s: %d sezioni, %d elementi di blocco, %d righe raccolte%s%s"
              % (f.name, c["sezioni"], c["blocchi"], c["raccolti"],
                 ", testata" if c["testata"] else ", NESSUNA TESTATA",
                 ", %d occhielli" % c["occhielli"] if c["occhielli"] else ""))
        if c["classi_ignote"]:
            print("  classi che nessuna regola riconosce: %s" % ", ".join(c["classi_ignote"]))
        return 1 if c["classi_ignote"] else 0

    f = Path(a.pagina)
    if not f.is_file():
        print("pagina inesistente: %s" % f)
        return 2
    md, n = converti(f.read_text(encoding="utf-8"))
    if n == 0:
        print("nessuna sezione riconosciuta in %s: la pagina non ha la forma attesa" % f)
        return 2
    if a.uscita:
        u = Path(a.uscita)
        u.parent.mkdir(parents=True, exist_ok=True)
        u.write_text(md, encoding="utf-8", newline="\n")
        print("%s: %d sezioni, %d byte di contenuto su %d di pagina, scritti in %s"
              % (f.name, n, len(md), f.stat().st_size, u))
    else:
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
