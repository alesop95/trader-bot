#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Dal contenuto alla pagina: il pezzo mancante della pipeline documentale (ADR-010).

Perché esiste
-------------
`documento-estrai.py` scioglie l'incollatura fra testo e grafica nella sola direzione che si può
fare senza perdere niente, cioè dalla pagina al contenuto. Questo strumento fa la direzione
opposta, ed è il pezzo che mancava: finché c'era solo l'estrattore, un documento si poteva
leggere ma non riprodurre, quindi la separazione restava dichiarata e non dimostrata.

La prova della separazione
--------------------------
ADR-010 dice che la prova di correttezza è il confronto fra la pagina rigenerata e quella di
partenza. Confrontare due file HTML byte per byte però non prova quasi niente: due pagine
possono differire per uno spazio e dire la stessa cosa, o coincidere per caso su un documento
povero. La prova che questo strumento adotta è più forte ed è un giro chiuso: si genera la
pagina dal contenuto, si riestrae il contenuto dalla pagina generata, e i due contenuti devono
coincidere carattere per carattere. Se il giro chiude, nessuna informazione del contenuto è
andata persa nella grafica e nessuna grafica si è travestita da contenuto. L'autotest lo esegue
su un contenuto costruito che usa tutte le convenzioni, e il comando `--giro` lo esegue su un
contenuto vero.

La grafica non sta qui dentro
-----------------------------
Il generatore non contiene il design system e non ne contiene nemmeno un pezzo: lo riceve come
cartella e vi si collega. È il vincolo che tutta questa pipeline esiste per attuare, e il modo
più facile di violarlo è incollare qualche regola di stile "solo per far vedere il risultato".
Per difetto la pagina rimanda al foglio di stile del tema, e pesa pochi kilobyte; con
`--incorpora` il foglio e i caratteri finiscono dentro il file, e quella è la forma da
consegnare a chi non ha la cartella del tema. Le forme e i colori dei segni accanto agli
occhielli li assegna il generatore, prendendoli dal tema, perché sono decorazione e non
contenuto: chi scrive un documento non decide il colore di un quadratino.

Il tema non si cabla
--------------------
Il percorso del tema è un percorso reale di questa macchina, quindi non sta in un file
tracciato, come vuole `data-separation.md`. Si dichiara in `_notes/.tema.txt`, ignorato da git,
oppure si passa con `--tema`. Senza tema il generatore produce lo stesso la pagina, segnalando
che è senza grafica: una pagina senza stile è un esito, una pagina con lo stile inventato no.

    python tools/documento-genera.py _notes/documenti/registro-trattamenti.md
    python tools/documento-genera.py <contenuto> --uscita <pagina.html> --incorpora
    python tools/documento-genera.py <contenuto> --giro      prova il giro chiuso e non scrive
    python tools/documento-genera.py --autotest
"""

from __future__ import annotations

import argparse
import base64
import html as _html
import importlib.util
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

PROGETTO = Path(__file__).resolve().parent.parent
# Il tema lo dichiara il progetto da cui si lancia, anche quando lo strumento vive in un pacchetto
# del template; se la cartella corrente non lo dichiara vale quello accanto allo strumento.
DICHIARAZIONE_TEMA = next((p for p in (Path.cwd() / "_notes" / ".tema.txt", PROGETTO / "_notes" / ".tema.txt")
                           if p.exists()), PROGETTO / "_notes" / ".tema.txt")


def tema_dichiarato(dichiarazione=DICHIARAZIONE_TEMA):
    """Il percorso del tema, dal file che lo dichiara. None se non è dichiarato."""
    try:
        for riga in dichiarazione.read_text(encoding="utf-8-sig").splitlines():
            riga = riga.strip()
            if riga and not riga.startswith("#"):
                return Path(riga)
    except OSError:
        pass
    return None


def frontmatter(contenuto):
    """Separa il frontmatter dal corpo. Torna (campi, righe del corpo)."""
    righe = contenuto.splitlines()
    campi = {}
    if righe and righe[0].strip() == "---":
        for n, riga in enumerate(righe[1:], 1):
            if riga.strip() == "---":
                return campi, righe[n + 1:]
            chiave, _, valore = riga.partition(":")
            if valore:
                campi[chiave.strip()] = valore.strip()
    return campi, righe


def inline(s):
    """I segni di riga: prima si protegge la marcatura HTML, poi si applicano i nostri."""
    s = _html.escape(s, quote=False)
    # Il codice inline si mette da parte prima dei link e dell'enfasi: un `[...]` o un `*` dentro
    # il codice, frequenti nei domini Odoo, verrebbe altrimenti preso per un link o un corsivo.
    codici = []

    def accantona(m):
        codici.append(m.group(1))
        return "\x00%d\x00" % (len(codici) - 1)

    s = re.sub(r"`(.+?)`", accantona, s)
    s = re.sub(r"\[([^\]]+?)\]\(([^)\s]+?)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\[(.+?)\]\{\.vuoto\}", r'<span class="vuoto">\1</span>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"\x00(\d+)\x00", lambda m: '<span class="cod">%s</span>' % codici[int(m.group(1))], s)
    return s


def blocchi(righe):
    """Il corpo come elenco di blocchi, nell'ordine in cui compaiono."""
    fuori = []
    i = 0
    while i < len(righe):
        riga = righe[i]
        nudo = riga.strip()
        if not nudo:
            i += 1
            continue

        titolo = re.match(r"^(#{1,3})\s+(.*?)(?:\s*\{occhiello=\"(.*?)\"\})?$", nudo)
        if titolo:
            fuori.append({"tipo": "titolo", "livello": len(titolo.group(1)),
                          "testo": titolo.group(2).strip(), "occhiello": titolo.group(3) or ""})
            i += 1
            continue

        if nudo.startswith("> [!riquadro]"):
            dentro, i = [], i + 1
            while i < len(righe) and righe[i].lstrip().startswith(">"):
                pezzo = righe[i].lstrip()[1:].strip()
                if pezzo:
                    dentro.append(pezzo)
                i += 1
            fuori.append({"tipo": "riquadro", "righe": dentro})
            continue

        if nudo.startswith(">"):
            fuori.append({"tipo": "sommario", "testo": nudo[1:].strip()})
            i += 1
            continue

        if nudo == "::: schede":
            schede, corrente, i = [], [], i + 1
            while i < len(righe) and righe[i].strip() != ":::":
                voce = righe[i].strip()
                if voce == "---":
                    if corrente:
                        schede.append(corrente)
                    corrente = []
                elif voce:
                    chiave, _, valore = voce.partition(":")
                    corrente.append((chiave.strip(), valore.strip()))
                i += 1
            if corrente:
                schede.append(corrente)
            fuori.append({"tipo": "schede", "schede": schede})
            i += 1
            continue

        fuori.append({"tipo": "paragrafo", "testo": nudo})
        i += 1
    return fuori


def tabella_html(schede):
    """Le schede tornano tabella. Uno Stato precede il campo che segue, dentro la sua cella."""
    colonne = []
    for scheda in schede:
        for chiave, _ in scheda:
            if chiave != "Stato" and chiave not in colonne:
                colonne.append(chiave)
    if not colonne:
        return ""

    fuori = ["<table>", "<thead><tr>"]
    fuori += ["<th>%s</th>" % inline(c) for c in colonne]
    fuori += ["</tr></thead>", "<tbody>"]
    for scheda in schede:
        celle, sospeso = {}, None
        for chiave, valore in scheda:
            if chiave == "Stato":
                sospeso = valore
                continue
            testo = inline(valore)
            if sospeso:
                marca = '<span class="vuoto">%s</span>' % inline(sospeso)
                testo = (marca + " " + testo).strip()
                sospeso = None
            celle[chiave] = testo
        fuori.append("<tr>" + "".join("<td>%s</td>" % celle.get(c, "") for c in colonne) + "</tr>")
    fuori += ["</tbody>", "</table>"]
    return "\n".join(fuori)


def forme_del_tema(tema):
    """I nomi delle forme dei segni, letti dal tema. Elenco vuoto se il tema non le dichiara."""
    if not tema:
        return []
    dati = Path(tema) / "assets" / "pin" / "pin-data.js"
    try:
        testo = dati.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return re.findall(r'"([a-z0-9-]+)":\s*\{\s*viewBox', testo)


def segno(tema, forme, n):
    """Il segno accanto a un occhiello: decorazione, assegnata qui e non da chi scrive."""
    if not forme:
        return ""
    nome = forme[n % len(forme)]
    dati = (Path(tema) / "assets" / "pin" / "pin-data.js").read_text(
        encoding="utf-8", errors="replace")
    pezzo = re.search(r'"%s":\s*\{\s*viewBox:\s*"(.*?)",\s*body:\s*"(.*?)"\s*\}'
                      % re.escape(nome), dati, re.S)
    if not pezzo:
        return ""
    corpo = pezzo.group(2).replace('\\"', '"')
    return '<svg class="pin" viewBox="%s" aria-hidden="true">%s</svg>' % (pezzo.group(1), corpo)


def foglio_unito(radice):
    """Il foglio del tema con i suoi import risolti, come un testo solo."""
    pezzi = []
    for riga in (radice / "styles.css").read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r'@import\s+"(.*?)";', riga.strip())
        if m:
            try:
                pezzi.append((radice / m.group(1)).read_text(encoding="utf-8", errors="replace"))
            except OSError:
                pass
        else:
            pezzi.append(riga)
    return "\n".join(pezzi)


def famiglie_in_uso(css):
    """Le famiglie di caratteri che il foglio usa davvero, risolvendo le variabili.

    Serve perché incorporare tutto è la scelta sbagliata che sembra prudente. Il tema dichiara
    quindici file per 2,2 MB, che in base64 diventano oltre tre; la pagina di partenza, scritta a
    mano, ne portava tre. Le famiglie però non compaiono per nome nelle dichiarazioni d'uso ma
    attraverso variabili, quindi un confronto per nome non trova niente e farebbe concludere che
    nessun carattere serve: le variabili si risolvono prima di confrontare.
    """
    variabili = dict(re.findall(r"(--[\w-]+)\s*:\s*([^;}]+)", css))
    senza_facce = re.sub(r"@font-face\s*\{.*?\}", "", css, flags=re.S)
    usate = set()
    for dichiarazione in re.findall(r"font-family\s*:\s*([^;}]+)", senza_facce):
        for _ in range(4):  # una variabile puo' puntare a un'altra variabile
            dichiarazione = re.sub(r"var\(\s*(--[\w-]+)\s*\)",
                                   lambda m: variabili.get(m.group(1), ""), dichiarazione)
        # Solo la famiglia primaria, cioe' la prima della pila: le successive sono ripieghi, ed
        # esistono precisamente per non doverle spedire. Tenerle raddoppiava il peso, perche' il
        # ripiego dichiarato per la famiglia variabile e' un'altra famiglia del tema, con cinque
        # pesi statici propri.
        for nome in dichiarazione.split(","):
            nome = nome.strip().strip("\"'")
            if nome and not nome.startswith("var("):
                usate.add(nome)
                break
    return usate


def facce_da_tenere(css, usate):
    """I file dei caratteri da incorporare: solo le famiglie in uso, e la variabile batte le statiche."""
    facce = []
    for blocco in re.findall(r"@font-face\s*\{(.*?)\}", css, flags=re.S):
        famiglia = re.search(r'font-family\s*:\s*["\']?([^;"\']+)', blocco)
        file = re.findall(r'url\(["\']?([^"\')]+\.ttf)', blocco)
        if famiglia and file and famiglia.group(1).strip() in usate:
            facce.append((famiglia.group(1).strip(), file[0]))
    con_variabile = {f for f, n in facce if "Variable" in n}
    return [(f, n) for f, n in facce if "Variable" in n or f not in con_variabile]


def foglio_documento():
    """Il foglio che disegna un documento, se il progetto ne ha uno."""
    try:
        return (PROGETTO / "assets" / "documento.css").read_text(
            encoding="utf-8", errors="replace")
    except OSError:
        return ""


def stile(tema, incorpora, con_caratteri=False):
    """Il collegamento al foglio di stile, oppure il foglio incorporato.

    I caratteri restano fuori anche dalla pagina autonoma, se non li si chiede: il tema ne
    dichiara 2,2 MB e la pagina deve restare un documento, non un pacchetto di caratteri. Senza
    di essi valgono i ripieghi che il tema stesso dichiara accanto a ogni famiglia, quindi la
    pagina resta corretta di colori, spaziature e geometria e cambia solo il disegno delle
    lettere. Chi deve consegnare la resa tipografica esatta chiede i caratteri e ne paga il peso,
    che il comando dichiara.
    """
    # Il foglio del documento e quello del tema sono due cose diverse e servono entrambe. Il tema
    # porta i token, cioe' i valori di marca, e i componenti; non ha e non deve avere regole per
    # gli elementi nudi di un documento, perche' un documento non e' un'interfaccia. Il foglio del
    # documento mappa titoli, paragrafi, occhielli, sommari, riquadri e tabelle su quei token, e
    # tiene il valore come ripiego: senza tema la pagina resta corretta, con il tema i valori di
    # marca prevalgono. Il 09/11/2026 la prima pagina generata e' uscita con gli stili di difetto
    # del navigatore proprio perche' questo foglio mancava e il solo tema non disegna niente.
    documento = PROGETTO / "assets" / "documento.css"
    if not tema:
        if documento.is_file():
            return ("<!-- nessun tema dichiarato: valgono i ripieghi del foglio documento. -->\n"
                    + ('<link rel="stylesheet" href="%s">' % documento.as_uri()
                       if not incorpora
                       else "<style>\n%s\n</style>"
                            % documento.read_text(encoding="utf-8", errors="replace")))
        return ("<!-- nessun tema dichiarato e nessun foglio documento: pagina senza grafica. "
                "Si dichiara in _notes/.tema.txt oppure con --tema. -->")
    radice = Path(tema)
    if not incorpora:
        collegamenti = ['<link rel="stylesheet" href="%s">' % (radice / "styles.css").as_uri()]
        if documento.is_file():
            collegamenti.append('<link rel="stylesheet" href="%s">' % documento.as_uri())
        return "\n".join(collegamenti)

    css = foglio_unito(radice)
    if not con_caratteri:
        css = re.sub(r"@font-face\s*\{.*?\}", "", css, flags=re.S)
        return "<style>\n%s\n%s\n</style>" % (css, foglio_documento())

    # Lo stesso file compare due volte nello stesso src, con due dichiarazioni di formato, perche'
    # un carattere variabile offre al navigatore la via con le variazioni e quella senza. Finche'
    # sono riferimenti costa due righe; incorporati costano due volte il carattere, ed e' il
    # milione di byte che separava la misura attesa da quella osservata. Si tiene il primo.
    css = re.sub(r'url\((["\']?)([^"\')]+\.ttf)\1\)(\s*format\([^)]*\))\s*,\s*'
                 r'url\((["\']?)\2\4\)\s*format\([^)]*\)',
                 lambda m: 'url(%s%s%s)%s' % (m.group(1), m.group(2), m.group(1), m.group(3)), css)

    tenuti = {n for _, n in facce_da_tenere(css, famiglie_in_uso(css))}

    def sostituisci(m):
        riferimento = m.group(1)
        if riferimento not in tenuti:
            return "url()"
        percorso = radice / "tokens" / riferimento
        if not percorso.is_file():
            percorso = radice / riferimento.replace("../", "")
        try:
            dati = base64.b64encode(percorso.read_bytes()).decode("ascii")
        except OSError:
            return m.group(0)
        return 'url("data:font/ttf;base64,%s")' % dati

    css = re.sub(r'url\(["\']?([^"\')]+\.ttf)["\']?\)', sostituisci, css)
    return "<style>\n%s\n%s\n</style>" % (css, foglio_documento())


# Sezioni e sottosezioni comprimibili. Il DOM generato resta quello statico, che l'estrattore
# legge per il giro chiuso: lo script sta nella testa, che l'estrattore taglia, e raggruppa a
# runtime il contenuto sotto ogni h2 e ogni h3 figli diretti di una sezione. L'occhiello che
# precede un titolo resta fuori dal corpo del titolo precedente, perche' appartiene al successivo.
# Lo stile entra dallo script e non da un <style>, perche' una pagina senza tema non ne ha.
# Il disegno e' quello del componente Accordion del design system aziendale: interruttore piu'/meno a
# destra del titolo, mai una freccia, icona di 24px, filo #D0D4E3 fra le righe, apertura animata
# sulle righe della griglia in 420ms con cubic-bezier(.2,.6,.2,1). I pulsanti seguono la regola
# del sistema per le etichette: maiuscolo con spaziatura .2em, raggio zero, nessuna ombra.
PIEGHE = r"""<script>
document.addEventListener('DOMContentLoaded',function(){
var main=document.querySelector('main');if(!main)return;
var css=document.createElement('style');css.textContent=
'.piega{cursor:pointer;display:flex;align-items:center;justify-content:space-between;gap:24px}'+
'.piega::after{content:"";flex:0 0 24px;height:24px;background:linear-gradient(currentColor,currentColor) center/16px 2px no-repeat,linear-gradient(currentColor,currentColor) center/2px 16px no-repeat}'+
'.piega[aria-expanded="true"]::after{background:linear-gradient(currentColor,currentColor) center/16px 2px no-repeat}'+
'.piega:focus-visible{outline:2px solid currentColor;outline-offset:4px}'+
'h3.piega{border-top:1px solid #D0D4E3;padding-top:24px}'+
'main>section{transition:padding 420ms cubic-bezier(.2,.6,.2,1)}'+
'td{overflow-wrap:anywhere}'+
'main>section:has(>.piega-corpo.chiuso){padding:20px 0}'+
'main>section:has(>.piega-corpo.chiuso)>.eyebrow{margin-bottom:4px}'+
'main>section:has(>.piega-corpo.chiuso)>.eyebrow .label{font-size:12px}'+
'main>section:has(>.piega-corpo.chiuso)>h2{font-size:28px}'+
'.piega-dentro h3.piega+.piega-corpo.chiuso{margin-bottom:0}.piega-dentro>h3.piega{padding-top:16px;margin-top:16px}'+
'.piega-corpo{display:grid;grid-template-rows:1fr;transition:grid-template-rows 420ms cubic-bezier(.2,.6,.2,1)}'+
'.piega-corpo.chiuso{grid-template-rows:0fr}.piega-dentro{overflow:hidden;min-height:0}'+
'.piega-dentro>:first-child{margin-top:24px}.piega-dentro>p+p{margin-top:16px}'+
'.piega-dentro>h3{margin-top:40px}.piega-dentro>table+p{margin-top:24px}'+
'.pieghe-comandi{display:flex;gap:16px;padding:24px var(--gutter,24px) 0}'+
'.pieghe-comandi button{font:inherit;font-size:12px;font-weight:500;text-transform:uppercase;letter-spacing:.2em;background:none;border:1px solid currentColor;border-radius:0;padding:12px 24px;cursor:pointer;color:inherit}'+
'@media (prefers-reduced-motion:reduce){.piega-corpo{transition:none}}'+
'@media print{.piega-corpo.chiuso{grid-template-rows:1fr}.piega::after,.pieghe-comandi{display:none}}';
document.head.appendChild(css);
var titoli=[];
function imposta(t,aperto){t[1].classList.toggle('chiuso',!aperto);t[0].setAttribute('aria-expanded',aperto?'true':'false')}
function piega(h,nodi){if(!nodi.length)return null;var c=document.createElement('div');c.className='piega-corpo';
var d=document.createElement('div');d.className='piega-dentro';c.appendChild(d);
h.parentNode.insertBefore(c,nodi[0]);nodi.forEach(function(n){d.appendChild(n)});
var testo=document.createElement('span');while(h.firstChild)testo.appendChild(h.firstChild);h.appendChild(testo);
h.classList.add('piega');h.setAttribute('role','button');h.setAttribute('tabindex','0');h.setAttribute('aria-expanded','true');
var t=[h,c];function cambia(){imposta(t,c.classList.contains('chiuso'))}
h.addEventListener('click',cambia);
h.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();cambia()}});
titoli.push(t);return d}
function eyebrowDi(n){return n&&n.classList&&n.classList.contains('eyebrow')}
function figliDopo(h,stop){var out=[],n=h.nextElementSibling;
while(n&&!stop(n)){if(eyebrowDi(n)&&n.nextElementSibling&&stop(n.nextElementSibling))break;out.push(n);n=n.nextElementSibling}return out}
function sottolivelli(cont){Array.prototype.slice.call(cont.children).forEach(function(h){
if(h.tagName==='H3')piega(h,figliDopo(h,function(n){return n.tagName==='H3'||n.tagName==='H2'}))})}
main.querySelectorAll(':scope > section').forEach(function(s){
var h2=s.querySelector(':scope > h2');
if(h2){var c=piega(h2,figliDopo(h2,function(){return false}));if(c)sottolivelli(c)}else sottolivelli(s)});
if(!titoli.length)return;
titoli.forEach(function(t){t[1].style.transition='none';imposta(t,false)});
requestAnimationFrame(function(){requestAnimationFrame(function(){titoli.forEach(function(t){t[1].style.transition=''})})});
var bar=document.createElement('div');bar.className='pieghe-comandi';
[['Espandi tutto',false],['Comprimi tutto',true]].forEach(function(v){var b=document.createElement('button');b.type='button';b.textContent=v[0];
b.addEventListener('click',function(){titoli.forEach(function(t){imposta(t,!v[1])})});bar.appendChild(b)});
main.parentNode.insertBefore(bar,main)});
</script>"""


def genera(contenuto, tema=None, incorpora=False, con_caratteri=False):
    """Dal contenuto alla pagina. Deterministico: stesso ingresso, stessa uscita."""
    campi, righe = frontmatter(contenuto)
    forme = forme_del_tema(tema)

    testa = ["<!doctype html>", '<html lang="it">', "<head>", '<meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width, initial-scale=1">',
             "<title>%s</title>" % _html.escape(campi.get("titolo", "Documento")),
             stile(tema, incorpora, con_caratteri), PIEGHE, "</head>", "<body>"]

    if campi.get("etichette"):
        testa.append('<div class="utility">' + "".join(
            '<span class="label muta">%s</span>' % inline(e.strip())
            for e in campi["etichette"].split("|")) + "</div>")
    if campi.get("intestazione"):
        pezzi = [p.strip() for p in campi["intestazione"].split("|")]
        testa.append('<div class="nav">' + "".join(
            '<span class="%s">%s</span>' % ("marchio" if n == 0 else "label muta", inline(p))
            for n, p in enumerate(pezzi)) + "</div>")

    # La testata: occhiello, titolo e sommario del documento, non di una sezione. Sta fuori da
    # <main> perche' l'estrattore legge le sezioni e la testata separatamente, e perche' non e'
    # contenuto di una sezione. Il titolo del documento vive qui come h1, quindi i titoli di
    # sezione sono h2, esattamente come nella pagina scritta a mano.
    testata = []
    if campi.get("occhiello") or campi.get("sommario"):
        testata.append('<header class="testata">')
        if campi.get("occhiello"):
            testata.append('<span class="eyebrow">%s<span class="label">%s</span></span>'
                           % (segno(tema, forme, 0), inline(campi["occhiello"])))
        testata.append("<h1>%s</h1>" % _html.escape(campi.get("titolo", "")))
        if campi.get("sommario"):
            testata.append('<p class="standfirst">%s</p>' % inline(campi["sommario"]))
        testata.append("</header>")

    corpo = testata + ["<main>"]
    aperta = False
    quante = 0
    for blocco in blocchi(righe):
        if blocco["tipo"] == "titolo" and blocco["livello"] <= 2:
            if aperta:
                corpo.append("</section>")
            corpo.append("<section>")
            aperta = True
            if blocco["occhiello"]:
                corpo.append('<div class="eyebrow">%s<span class="label">%s</span></div>'
                             % (segno(tema, forme, quante), inline(blocco["occhiello"])))
            quante += 1
            # Sempre h2: il titolo del documento e' nella testata, i titoli di sezione gli
            # stanno sotto. L'estrattore rende h2 come primo livello nella prima sezione e come
            # secondo nelle altre, quindi il giro chiude per entrambi.
            corpo.append("<h2>%s</h2>" % inline(blocco["testo"]))
            continue
        if not aperta:
            corpo.append("<section>")
            aperta = True
        if blocco["tipo"] == "titolo":
            if blocco["occhiello"]:
                corpo.append('<div class="eyebrow">%s<span class="label">%s</span></div>'
                             % (segno(tema, forme, quante), inline(blocco["occhiello"])))
                quante += 1
            corpo.append("<h3>%s</h3>" % inline(blocco["testo"]))
        elif blocco["tipo"] == "sommario":
            corpo.append('<p class="standfirst">%s</p>' % inline(blocco["testo"]))
        elif blocco["tipo"] == "riquadro":
            dentro = []
            for n, riga in enumerate(blocco["righe"]):
                forte = re.match(r"^\*\*(.*)\*\*$", riga)
                if forte and n == 0:
                    dentro.append("<h3>%s</h3>" % inline(forte.group(1)))
                else:
                    dentro.append("<p>%s</p>" % inline(riga))
            corpo.append('<div class="riquadro">%s</div>' % "".join(dentro))
        elif blocco["tipo"] == "schede":
            corpo.append(tabella_html(blocco["schede"]))
        else:
            corpo.append("<p>%s</p>" % inline(blocco["testo"]))

    if aperta:
        corpo.append("</section>")
    corpo.append("</main>")
    return "\n".join(testa + corpo + ["</body>", "</html>", ""])


def estrattore():
    """L'estrattore, caricato per percorso perché il suo nome contiene un trattino."""
    percorso = PROGETTO / "tools" / "documento-estrai.py"
    spec = importlib.util.spec_from_file_location("documento_estrai", percorso)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def giro(contenuto, tema=None):
    """Il giro chiuso: contenuto, pagina, contenuto. Torna (chiude, riestratto)."""
    pagina = genera(contenuto, tema=tema)
    riestratto, _ = estrattore().converti(pagina)
    return riestratto.strip() == contenuto.strip(), riestratto


PROVA = """---
titolo: Documento di prova
intestazione: Marchio | Revisione 0
etichette: Etichetta
---

# Titolo primo {occhiello="Occhiello"}

> Sommario della prova.

Un paragrafo con *corsivo*, `codice` e **grassetto**.

## Titolo secondo

> [!riquadro]
> **Titolo del riquadro**
>
> Corpo del riquadro.

::: schede
Stato: Lacuna dichiarata
Campo A: uno
Campo B: due
---
Campo A: tre
Campo B: quattro
:::
"""


def autotest():
    """Prove del giro chiuso e dei singoli segni. Nessun file reale, nessuna scrittura."""
    prove = fallite = 0

    def prova(nome, condizione):
        nonlocal prove, fallite
        prove += 1
        if not condizione:
            fallite += 1
            print(f"  FALLITA: {nome}")

    pagina = genera(PROVA)
    prova("la pagina comincia con il tipo di documento", pagina.startswith("<!doctype html>"))
    prova("il titolo del frontmatter diventa il titolo della pagina",
          "<title>Documento di prova</title>" in pagina)
    prova("senza tema la pagina lo dichiara invece di inventare lo stile",
          "nessun tema dichiarato" in pagina and "<style>" not in pagina)
    prova("due titoli di primo livello aprono due sezioni", pagina.count("<section>") == 2)
    prova("l'occhiello precede il titolo di sezione",
          pagina.index('class="eyebrow"') < pagina.index("<h2>"))
    prova("senza testata non si emette un h1 vuoto", "<h1>" not in pagina)
    prova("il sommario e' uno standfirst", 'class="standfirst"' in pagina)
    prova("il riquadro diventa un riquadro", 'class="riquadro"' in pagina)
    prova("le schede tornano tabella", "<table>" in pagina and pagina.count("<tr>") == 3)
    prova("lo stato precede il campo che segue dentro la sua cella",
          '<td><span class="vuoto">Lacuna dichiarata</span> uno</td>' in pagina)
    prova("il corsivo e' corsivo", "<em>corsivo</em>" in pagina)
    prova("il codice e' codice", '<span class="cod">codice</span>' in pagina)
    prova("il grassetto non diventa due corsivi", "<strong>grassetto</strong>" in pagina)
    prova("lo script delle pieghe sta nella testa, fuori dal corpo",
          pagina.index("piega-corpo") < pagina.index("</head>") < pagina.index("<main>"))
    prova("l'interruttore e' piu'/meno come nel componente Accordion, non una freccia",
          "rotate(" not in PIEGHE and "420ms" in PIEGHE)
    prova("all'apertura le sezioni sono chiuse, senza animazione",
          "imposta(t,false)})" in PIEGHE)

    chiude, riestratto = giro(PROVA)
    prova("IL GIRO CHIUDE: contenuto, pagina, contenuto", chiude)
    if not chiude:
        for a, b in zip(PROVA.strip().splitlines(), riestratto.strip().splitlines()):
            if a != b:
                print("    atteso:  %r" % a)
                print("    ottenuto: %r" % b)
                break

    prova("la generazione e' deterministica", genera(PROVA) == genera(PROVA))
    prova("un contenuto senza frontmatter non fa cadere nulla",
          genera("# Solo un titolo\n\nUn paragrafo.\n").count("<section>") == 1)
    prova("un ampersand nel testo non rompe la pagina",
          "&amp;" in genera("# T\n\nUno &amp; due.\n") or "&amp;" in genera("# T\n\nUno & due.\n"))

    print(f"documento-genera: {prove} prove, {fallite} fallite.")
    return 1 if fallite else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("contenuto", nargs="?", help="il file Markdown da cui generare la pagina")
    ap.add_argument("--uscita", help="dove scrivere la pagina; per difetto accanto al contenuto")
    ap.add_argument("--tema", help="la cartella del design system")
    ap.add_argument("--incorpora", action="store_true",
                    help="mette il foglio di stile dentro la pagina, senza i caratteri")
    ap.add_argument("--con-caratteri", action="store_true", dest="con_caratteri",
                    help="con --incorpora, incorpora anche i caratteri delle famiglie in uso")
    ap.add_argument("--giro", action="store_true",
                    help="prova il giro chiuso su questo contenuto e non scrive niente")
    ap.add_argument("--autotest", action="store_true")
    argomenti = ap.parse_args(argv)

    if argomenti.autotest:
        return autotest()
    if not argomenti.contenuto:
        ap.error("serve il file del contenuto, oppure --autotest")

    sorgente = Path(argomenti.contenuto)
    try:
        contenuto = sorgente.read_text(encoding="utf-8-sig")
    except OSError as errore:
        print("documento-genera: contenuto illeggibile: %s" % errore)
        return 2

    tema = Path(argomenti.tema) if argomenti.tema else tema_dichiarato()
    if tema and not Path(tema).is_dir():
        print("documento-genera: tema dichiarato ma non raggiungibile: %s" % tema)
        return 2

    if argomenti.giro:
        chiude, riestratto = giro(contenuto, tema=tema)
        if chiude:
            print("documento-genera: il giro chiude, il contenuto torna identico.")
            return 0
        print("documento-genera: il giro NON chiude. Prima differenza:")
        atteso = contenuto.strip().splitlines()
        ottenuto = riestratto.strip().splitlines()
        for n in range(max(len(atteso), len(ottenuto))):
            a = atteso[n] if n < len(atteso) else "(manca)"
            b = ottenuto[n] if n < len(ottenuto) else "(manca)"
            if a != b:
                print("  riga %d" % (n + 1))
                print("    atteso:   %s" % a[:160])
                print("    ottenuto: %s" % b[:160])
                break
        return 1

    pagina = genera(contenuto, tema=tema, incorpora=argomenti.incorpora,
                    con_caratteri=argomenti.con_caratteri)
    destinazione = Path(argomenti.uscita) if argomenti.uscita else sorgente.with_suffix(".html")
    destinazione.parent.mkdir(parents=True, exist_ok=True)
    destinazione.write_text(pagina, encoding="utf-8")
    print("documento-genera: scritta %s (%d byte, tema %s)"
          % (destinazione, len(pagina.encode("utf-8")), tema or "nessuno"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
