#!/usr/bin/env python3
"""Genera la guida grafica del template: come lo si usa, per fasi e per filoni, e come gli strumenti si intrecciano.

Perche' esiste. Il proprietario ha chiesto il 2026-11-12 un grafico di come si usa il template
da affiancare alla guida d'uso, separato per filoni e con l'intreccio degli strumenti. Una
pagina disegnata a mano invecchia al primo pacchetto nuovo: questa si genera. Settori e
pacchetti vengono dal catalogo, le skill dalla loro cartella, i filoni da `docs/FILONI.md`;
soltanto le fasi d'uso e gli archi dell'intreccio sono autorati, in
`.claude/templates/guida-grafica.json`, perche' sono un giudizio e non un inventario.

La pagina e' autonoma: nessuno script, nessuna risorsa esterna, il grafo e' SVG in linea.
L'aspetto e' quello delle altre pagine di `docs/` del template, che e' un progetto privato;
un progetto dell'organizzazione rigenera la propria con il design system dell'organizzazione.

Uso:
    python tools/guida-grafica.py --scrivi     genera docs/guida-grafica.html
    python tools/guida-grafica.py --check      esce con 1 se la pagina non e' allineata ai dati
    python tools/guida-grafica.py --autotest
"""

from __future__ import annotations

import argparse
import html
import importlib.util
import json
import re
import sys
from pathlib import Path

DATI = ".claude/templates/guida-grafica.json"
CATALOGO = ".claude/templates/PACKAGES.md"
FILONI = "docs/FILONI.md"
USCITA = "docs/guida-grafica.html"
COLORI = {"fonti": "#92400E", "catalogo": "#4338CA", "progetto": "#14532D", "consumo": "#7C3AED"}
NOMI_GRUPPO = {"fonti": "Fonti e scouting", "catalogo": "Catalogo e documentazione", "progetto": "Progetto e memoria", "consumo": "Agenti e consumo"}
LARGO, ALTO, PASSO_X, PASSO_Y, MARGINE = 176, 56, 272, 128, 28


def e(testo) -> str:
    return html.escape(str(testo), quote=True)


def modulo_riferimento():
    spec = importlib.util.spec_from_file_location("riferimento", Path(__file__).with_name("riferimento.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def filoni(testo: str) -> list:
    """Le righe della tabella dei filoni: nome, stato, settore di destinazione, documento."""
    # Le colonne si riconoscono dall'intestazione e non dalla posizione: la prima si chiama
    # «Tema» nell'indice di oggi, e una colonna aggiunta domani non deve spostare le altre.
    esito, colonne = [], None
    for r in testo.splitlines():
        celle = [x.strip() for x in r.strip().strip("|").split(" | ")] if r.startswith("|") else None
        if celle and colonne is None and "Stato" in celle and "Settore di destinazione" in celle:
            colonne = {nome: i for i, nome in enumerate(celle)}
            continue
        if colonne is None:
            continue
        if not r.strip():
            colonne = None
            continue
        if r.startswith("|---") or not celle or len(celle) < len(colonne):
            continue
        esito.append({"nome": celle[0], "stato": celle[colonne["Stato"]], "settore": celle[colonne["Settore di destinazione"]],
                      "documento": celle[colonne.get("Documento", len(celle) - 1)].strip("`")})
    return esito


def prima_frase(testo: str, tetto: int = 150) -> str:
    testo = re.sub(r"[`*]", "", testo)
    m = re.search(r"[.;:](\s|$)", testo)
    frase = testo[:m.start()] if m and m.start() > 30 else testo
    return frase if len(frase) <= tetto else frase[:tetto].rsplit(" ", 1)[0] + "…"


def bordo(cx, cy, tx, ty):
    """Il punto in cui il segmento dal centro (cx, cy) verso (tx, ty) esce dal rettangolo del nodo."""
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    sx = (LARGO / 2) / abs(dx) if dx else float("inf")
    sy = (ALTO / 2) / abs(dy) if dy else float("inf")
    s = min(sx, sy)
    return cx + dx * s, cy + dy * s


def grafo(nodi: list, archi: list) -> str:
    centri = {n["id"]: (MARGINE + n["col"] * PASSO_X + LARGO / 2, MARGINE + n["riga"] * PASSO_Y + ALTO / 2) for n in nodi}
    larghezza = MARGINE * 2 + max(n["col"] for n in nodi) * PASSO_X + LARGO
    altezza = MARGINE * 2 + max(n["riga"] for n in nodi) * PASSO_Y + ALTO
    p = ['<svg viewBox="0 0 %d %d" role="img" aria-label="Intreccio degli strumenti del template" xmlns="http://www.w3.org/2000/svg">' % (larghezza, altezza),
         '<defs><marker id="punta" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#6B7280"/></marker></defs>']
    etichette = []
    for a in archi:
        (x1, y1), (x2, y2) = centri[a["da"]], centri[a["a"]]
        ax, ay = bordo(x1, y1, x2, y2)
        bx, by = bordo(x2, y2, x1, y1)
        p.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#6B7280" stroke-width="1.3" marker-end="url(#punta)"/>' % (ax, ay, bx, by))
        mx, my = (ax + bx) / 2, (ay + by) / 2
        largo = len(a["etichetta"]) * 5.6 + 10
        etichette.append('<rect x="%.1f" y="%.1f" width="%.1f" height="16" rx="3" fill="#F1F2F6"/><text x="%.1f" y="%.1f" text-anchor="middle" font-size="10" fill="#374151">%s</text>'
                         % (mx - largo / 2, my - 8, largo, mx, my + 3.5, e(a["etichetta"])))
    for n in nodi:
        cx, cy = centri[n["id"]]
        colore = COLORI.get(n.get("gruppo"), "#111827")
        p.append('<rect x="%.1f" y="%.1f" width="%d" height="%d" rx="7" fill="#fff" stroke="%s" stroke-width="1.6"/>' % (cx - LARGO / 2, cy - ALTO / 2, LARGO, ALTO, colore))
        p.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="13" font-weight="600" fill="#111827">%s</text>' % (cx, cy - 3, e(n["etichetta"])))
        p.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="10.5" font-family="Consolas,monospace" fill="%s">%s</text>' % (cx, cy + 14, colore, e(n.get("sotto", ""))))
    return "\n".join(p + etichette + ["</svg>"])


def problemi(dati: dict) -> list:
    esito = []
    ident = [n.get("id") for n in dati.get("nodi", [])]
    if len(ident) != len(set(ident)):
        esito.append("due nodi hanno lo stesso identificativo")
    posti = [(n.get("col"), n.get("riga")) for n in dati.get("nodi", [])]
    if len(posti) != len(set(posti)):
        esito.append("due nodi occupano la stessa cella della griglia")
    for a in dati.get("archi", []):
        for capo in ("da", "a"):
            if a.get(capo) not in ident:
                esito.append("un arco nomina il nodo %r, che non esiste" % a.get(capo))
    if not dati.get("fasi"):
        esito.append("nessuna fase d'uso")
    return esito


STILE = """:root{--ground:#F1F2F6;--surface:#fff;--text:#111827;--muted:#6B7280;--accent:#4338CA;--border:#DDE0E8}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--ground);color:var(--text);font-family:'Segoe UI',system-ui,-apple-system,sans-serif;font-size:14px;line-height:1.6}
main{max-width:1000px;margin:0 auto;padding:3rem 1.5rem}
.eye{font-size:10px;letter-spacing:.15em;text-transform:uppercase;color:var(--muted);font-family:Consolas,monospace}
h1{font-family:Georgia,serif;font-size:2.3rem;line-height:1.1;letter-spacing:-.02em;margin:.4rem 0 .6rem}
h2{font-family:Georgia,serif;font-size:1.35rem;margin:3rem 0 .4rem;padding-top:1.5rem;border-top:2px solid var(--text)}
h3{font-size:13px;letter-spacing:.06em;text-transform:uppercase;margin:0 0 .5rem}
p.sub{color:var(--muted);max-width:680px;margin-bottom:1.1rem}
.conti{display:flex;gap:2rem;flex-wrap:wrap;margin-top:1rem}
.conti b{display:block;font-family:Georgia,serif;font-size:1.8rem;color:var(--accent);line-height:1;font-weight:normal}
.conti span{font-size:10px;text-transform:uppercase;letter-spacing:.1em;color:var(--muted)}
.fasi{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:.8rem;counter-reset:fase}
.fase{background:var(--surface);border:1px solid var(--border);border-radius:7px;padding:1rem;counter-increment:fase}
.fase h3::before{content:counter(fase) " ";font-family:Georgia,serif;color:var(--accent);font-size:1.3rem;margin-right:.3rem}
.fase .quando{color:var(--muted);font-size:12.5px;margin-bottom:.5rem}
.fase .esito{font-size:12.5px;margin-top:.6rem;padding-top:.5rem;border-top:1px solid var(--border)}
code{font-family:Consolas,monospace;font-size:11.5px;background:var(--ground);padding:1px 5px;border-radius:3px;color:var(--accent);display:inline-block;margin:1px 2px 1px 0}
.grafo{background:var(--surface);border:1px solid var(--border);border-radius:7px;padding:.5rem;overflow-x:auto}
.grafo svg{min-width:860px;width:100%;height:auto;display:block}
.legenda{display:flex;gap:1.2rem;flex-wrap:wrap;font-size:12px;color:var(--muted);margin:.6rem 0 0}
.legenda i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px;vertical-align:-1px}
.settore{background:var(--surface);border:1px solid var(--border);border-radius:7px;padding:1rem;margin-bottom:.7rem}
.settore h3 small{color:var(--muted);font-weight:normal;letter-spacing:0;text-transform:none;margin-left:.4rem}
.settore .aperti{font-size:12.5px;color:#92400E;margin-top:.5rem}
table{width:100%;border-collapse:collapse;font-size:12.5px;background:var(--surface);border:1px solid var(--border)}
th,td{text-align:left;padding:.45rem .7rem;border-bottom:1px solid var(--border);vertical-align:top}
th{font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}
footer{margin-top:3rem;font-size:12px;color:var(--muted)}
"""


def genera(dati: dict, voci: list, skill: list, righe_filoni: list) -> str:
    settori = []
    for v in voci:
        if v["settore"] not in settori:
            settori.append(v["settore"])
    p = ['<!DOCTYPE html>', '<html lang="it">', '<head>', '<meta charset="utf-8">', '<meta name="viewport" content="width=device-width, initial-scale=1">',
         '<title>Guida grafica del template</title>', '<style>', STILE.rstrip(), '</style>', '</head>', '<body>', '<main>',
         '<div class="eye">Generata da tools/guida-grafica.py, non si modifica a mano</div>',
         '<h1>Come si usa il template</h1>',
         '<p class="sub">Tre viste dello stesso sistema: le fasi in cui lo si usa, il modo in cui gli strumenti si passano il lavoro, e che cosa offre settore per settore. Affianca la guida d\'uso, che spiega; il dettaglio di ogni voce sta nel riferimento.</p>',
         '<div class="conti"><div><b>%d</b><span>Fasi</span></div><div><b>%d</b><span>Skill di sistema</span></div><div><b>%d</b><span>Pacchetti</span></div><div><b>%d</b><span>Settori</span></div><div><b>%d</b><span>Filoni</span></div></div>'
         % (len(dati["fasi"]), len(skill), len(voci), len(settori), len(righe_filoni)),
         '<h2>1. Le fasi d\'uso</h2>',
         '<p class="sub">Dalla nascita del progetto alla passata che riporta le correzioni a tutti gli altri. Ogni fase nomina gli strumenti che la attuano e ciò che deve risultare.</p>',
         '<div class="fasi">']
    for f in dati["fasi"]:
        p.append('<div class="fase"><h3>%s</h3><div class="quando">%s</div><div>%s</div><div class="esito">%s</div></div>'
                 % (e(f["titolo"]), e(f["quando"]), "".join("<code>%s</code>" % e(s) for s in f["strumenti"]), e(f["esito"])))
    p += ['</div>', '<h2>2. Come gli strumenti si intrecciano</h2>',
          '<p class="sub">Una freccia va da chi produce a chi consuma. Il giro in basso è quello che tiene vivo il sistema: un progetto registra una lezione, il template la recepisce, la passata la riporta a tutti.</p>',
          '<div class="grafo">', grafo(dati["nodi"], dati["archi"]), '</div>',
          '<div class="legenda">' + "".join('<span><i style="background:%s"></i>%s</span>' % (COLORI[g], e(NOMI_GRUPPO[g])) for g in COLORI) + '</div>',
          '<h2>3. Per settore, con i filoni aperti</h2>',
          '<p class="sub">Un progetto appartiene a due o tre settori. Sotto ciascuno, i pacchetti pronti e i filoni che vi confluiranno.</p>']
    for s in settori:
        del_settore = [v for v in voci if v["settore"] == s]
        aperti = [f["nome"] for f in righe_filoni if s.lower() in f["settore"].lower()]
        p.append('<div class="settore"><h3>%s<small>%d pacchetti</small></h3><div>%s</div>%s</div>'
                 % (e(s), len(del_settore), "".join('<code title="%s">%s</code>' % (e(prima_frase(v["cosa_fa"])), e(v["nome"])) for v in del_settore),
                    ('<div class="aperti">Filoni aperti: %s</div>' % e(", ".join(aperti))) if aperti else ""))
    p += ['<h2>4. Le skill di sistema</h2>', '<p class="sub">Arrivano in ogni progetto con l\'allineamento. Quelle a invocazione manuale non pesano all\'avvio.</p>', '<table><tr><th>Skill</th><th>Che cosa fa</th></tr>']
    for sk in skill:
        p.append('<tr><td><code>%s</code></td><td>%s</td></tr>' % (e(sk["nome"]), e(prima_frase(sk.get("descrizione", ""), 220))))
    p += ['</table>', '<h2>5. I filoni</h2>', '<p class="sub">Linee di indagine non ancora a catalogo, con lo stato dichiarato nell\'indice.</p>', '<table><tr><th>Filone</th><th>Stato</th><th>Documento</th></tr>']
    for f in righe_filoni:
        p.append('<tr><td>%s</td><td>%s</td><td><code>%s</code></td></tr>' % (e(f["nome"]), e(prima_frase(f["stato"], 200)), e(f["documento"])))
    p += ['</table>', '<footer>Fonti dei dati: .claude/templates/PACKAGES.md, .claude/skills/, docs/FILONI.md e .claude/templates/guida-grafica.json. Dettaglio di ogni voce in docs/RIFERIMENTO.md; spiegazione in GUIDA-USO.md.</footer>',
          '</main>', '</body>', '</html>']
    return "\n".join(p) + "\n"


def carica(radice: Path):
    rif = modulo_riferimento()
    dati = json.loads((radice / DATI).read_text(encoding="utf-8"))
    voci = rif.catalogo((radice / CATALOGO).read_text(encoding="utf-8"))
    skill = rif.skill_di_sistema(radice)
    righe = filoni((radice / FILONI).read_text(encoding="utf-8")) if (radice / FILONI).is_file() else []
    return dati, voci, skill, righe


def autotest() -> int:
    esiti = []

    def caso(nome, ok, dettaglio=""):
        esiti.append(bool(ok))
        print(("ok    " if ok else "ROSSO ") + nome + ("" if ok else "  " + str(dettaglio)))

    dati = {"fasi": [{"titolo": "Aprire", "quando": "sempre", "strumenti": ["riprendi"], "esito": "si sa"}],
            "nodi": [{"id": "a", "etichetta": "A <uno>", "sotto": "a.py", "col": 0, "riga": 0, "gruppo": "fonti"},
                     {"id": "b", "etichetta": "B", "sotto": "b.py", "col": 1, "riga": 1, "gruppo": "catalogo"}],
            "archi": [{"da": "a", "a": "b", "etichetta": "passa"}]}
    voci = [{"nome": "uno", "settore": "Primo settore", "cosa_fa": "Fa una cosa lunga abbastanza da avere una frase. E poi altro", "quando": ""},
            {"nome": "due", "settore": "Secondo", "cosa_fa": "Altro", "quando": ""}]
    skill = [{"nome": "riprendi", "descrizione": "Riprende il lavoro."}]
    tabella = "| Tema | Filone | Stato | Settore di destinazione | Documento |\n|---|---|---|---|---|\n| Uno | m | aperto | Primo settore | `docs/x.md` |\n\n| altra | tabella |\n"
    righe = filoni(tabella)
    caso("i filoni si leggono dalla tabella e la tabella finisce alla riga vuota", righe == [{"nome": "Uno", "stato": "aperto", "settore": "Primo settore", "documento": "docs/x.md"}], righe)
    caso("dati coerenti non hanno problemi", problemi(dati) == [])
    rotto = dict(dati, archi=[{"da": "a", "a": "z", "etichetta": "x"}])
    caso("un arco verso un nodo che non esiste viene segnalato", any("'z'" in x for x in problemi(rotto)), problemi(rotto))
    doppio = dict(dati, nodi=dati["nodi"] + [{"id": "c", "etichetta": "C", "col": 0, "riga": 0}])
    caso("due nodi nella stessa cella vengono segnalati", any("stessa cella" in x for x in problemi(doppio)))
    pagina = genera(dati, voci, skill, righe)
    caso("la pagina contiene fasi, grafo, settori, skill e filoni", all(x in pagina for x in ("Aprire", "<svg", "Primo settore", "riprendi", "docs/x.md")))
    caso("il testo dei dati viene protetto", "A &lt;uno&gt;" in pagina and "A <uno>" not in pagina)
    caso("un filone compare sotto il settore a cui confluisce, e solo lì", pagina.count("Filoni aperti: Uno") == 1)
    caso("la pagina non carica niente da fuori", "<script" not in pagina and "http://www.w3.org" in pagina and pagina.count("http") == 1, pagina.count("http"))
    x, y = bordo(100, 100, 300, 100)
    caso("una freccia esce dal bordo del nodo e non dal centro", (x, y) == (100 + LARGO / 2, 100))
    caso("la stessa generazione dà la stessa pagina", pagina == genera(dati, voci, skill, righe))
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
    if not (radice / DATI).is_file():
        print("guida-grafica: qui non ci sono i dati del template; niente da fare.")
        return 0
    dati, voci, skill, righe = carica(radice)
    guasti = problemi(dati)
    for g in guasti:
        print("guida-grafica: " + g)
    if guasti:
        return 1
    pagina = genera(dati, voci, skill, righe)
    dest = radice / USCITA
    if a.scrivi:
        dest.write_bytes(pagina.encode("utf-8"))
        print("scritto %s: %d fasi, %d nodi, %d pacchetti, %d filoni" % (USCITA, len(dati["fasi"]), len(dati["nodi"]), len(voci), len(righe)))
        return 0
    attuale = dest.read_bytes().decode("utf-8").replace("\r\n", "\n") if dest.is_file() else ""
    if attuale != pagina:
        print("guida-grafica: %s non e' allineata ai dati; rigenerare con --scrivi" % USCITA)
        return 1 if a.check else 0
    print("guida-grafica: allineata")
    return 0


if __name__ == "__main__":
    sys.exit(main())
