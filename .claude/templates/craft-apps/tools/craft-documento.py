#!/usr/bin/env python3
"""Dal Markdown a un documento o a una presentazione, in locale, con le app Craft.

La ricetta è quella che il proprietario ha fissato il 2026-10-19: il contenuto si
scrive in Markdown, si converte con l'applicazione Craft installata sulla
macchina, e gli si applica il design di un design system. Tutto resta locale:
nessun servizio, nessun token, nessun account. WordCraft fa documenti (docx, pdf,
odt, rtf, html, tex), DeckCraft fa presentazioni (pptx, pdf).

    python craft-documento.py documento relazione.md --out relazione.docx --stile stile.json
    python craft-documento.py documento relazione.md --out relazione.pdf --riferimento modello.docx
    python craft-documento.py slide sintesi.md --out sintesi.pptx --stile stile.json
    python craft-documento.py riferimento --stile stile.json --out modello.docx
    python craft-documento.py --autotest
    python craft-documento.py --collaudo        # prova vera, se le app sono installate

Il file di stile è il ponte con il design system: un JSON di pochi valori, che si
ricavano dai token del design system scelto (colori, font, dimensioni) e si
scrivono una volta per progetto.

    {
      "font_titoli": "Georgia",          "font_testo": "Verdana",
      "colore_titoli": "C8102E",          "colore_testo": "1A1A1A",
      "dimensioni": {"Title": 32, "Heading 1": 24, "Heading 2": 18, "Normal": 11},
      "colori_slide": {"accent1": "#C8102E", "dk1": "#1A1A1A", "lt1": "#FFFFFF"}
    }

Perché lo strumento chiama le CLI da Python e non si lascia fare da PowerShell: i
comandi delle CLI Craft prendono parametri JSON, e Windows PowerShell 5.1 toglie
le virgolette doppie dagli argomenti di un eseguibile, quindi il JSON arriva rotto
("bad JSON params"). Misurato il 2026-10-19 su WordCraft 0.8.0.

Tre fatti di WordCraft 0.8.0, misurati lo stesso giorno, che decidono come si
applica lo stile. Il font di uno stile si imposta con la chiave `font` dei campi
di carattere: `fontFamily`, `family` e `name` sono accettate con uscita 0 e
ignorate, e lo si è visto solo aprendo `word/styles.xml`. `styles.copyFrom` copia
le definizioni degli stili ma non il tema, quindi il font del corpo non viaggia
con un documento di riferimento: per questo i valori del file di stile si
applicano sempre direttamente, anche quando si passa un riferimento. E un
documento nuovo nasce con una diapositiva vuota in DeckCraft, che qui si toglie.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
from craft_apps_comune import sistema, trova_cli  # noqa: E402

STILI_TITOLO = ["Title", "Heading 1", "Heading 2", "Heading 3"]
FORMATI_DOC = {".docx", ".pdf", ".odt", ".rtf", ".html", ".tex", ".txt", ".md"}
FORMATI_SLIDE = {".pptx", ".pdf", ".deckcraft"}
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


class Errore(Exception):
    pass


def cli(app: str) -> str:
    p = trova_cli(app, sistema())
    if not p:
        raise Errore(app + " non è installata su questa macchina: `python craft-apps.py rileva` dice che cosa c'è, "
                     "`python craft-apps.py installa " + app + "` la prende dai rilasci di GitHub, senza account")
    return str(p)


def esegui(binario: str, *argomenti: str) -> str:
    r = subprocess.run([binario, *argomenti], capture_output=True, text=True, encoding="utf-8", errors="replace")
    uscita = (r.stdout + r.stderr).strip()
    if r.returncode != 0:
        raise Errore(Path(binario).name + " " + " ".join(argomenti[:2]) + ": " + uscita[-600:])
    return uscita


def c(nome: str, parametri: dict) -> list[str]:
    return ["--cmd", nome + "=" + json.dumps(parametri, ensure_ascii=False)]


STILE_PRIVATO = Path(__file__).resolve().parent.parent / "stili" / "privato-tecnico-sobrio.json"
STILE_PROGETTO = Path(".claude") / "craft-stile.json"
# Fuori da ogni repository: quale design system aziendale vale per quale dominio di posta
# dell'identita' git. Esempio: {"azienda.example": "C:/Users/me/.design-systems/x/craft-stile.json"}.
# Sta sulla macchina perche' un design aziendale non va copiato in un template pubblico.
MAPPA_IDENTITA = Path.home() / ".craft-apps" / "stili-per-identita.json"


def stile_automatico(progetto: Path) -> tuple[Path, str]:
    """Quale file di stile vale qui, e perche'. Regola del proprietario, 2026-10-19: il design
    si sceglie dal repository e dalla sua identita', non dall'abitudine. Prima la scelta
    esplicita del progetto; poi l'identita' git: un dominio dichiarato aziendale prende il suo
    design system, ogni altra identita' prende quello privato."""
    proprio = progetto / STILE_PROGETTO
    if proprio.is_file():
        return proprio, "scelto dal progetto in " + str(STILE_PROGETTO)
    r = subprocess.run(["git", "-C", str(progetto), "config", "user.email"], capture_output=True, text=True)
    email = r.stdout.strip().lower()
    dominio = email.rsplit("@", 1)[-1] if "@" in email else ""
    if MAPPA_IDENTITA.is_file() and dominio:
        mappa = json.loads(MAPPA_IDENTITA.read_text(encoding="utf-8"))
        if dominio in mappa:
            return Path(mappa[dominio]), "identita' " + email + ", design aziendale per " + dominio
    return STILE_PRIVATO, "identita' " + (email or "assente") + ", design privato"


def leggi_stile(percorso: str | None) -> dict:
    if not percorso:
        return {}
    if percorso == "auto":
        file, perche = stile_automatico(Path.cwd())
        print("stile: " + str(file) + " (" + perche + ")", file=sys.stderr)
        if not file.is_file():
            raise Errore("il file di stile indicato per questa identita' non esiste: " + str(file))
        percorso = str(file)
    dati = json.loads(Path(percorso).read_text(encoding="utf-8"))
    if not isinstance(dati, dict):
        raise Errore("il file di stile deve essere un oggetto JSON")
    return dati


def colore(v: str | None) -> str | None:
    return v.lstrip("#").upper() if v else None


def stili_presenti(docx: Path) -> set[str]:
    """I nomi degli stili definiti nel documento, in minuscolo. WordCraft rifiuta di modificare
    uno stile che il documento non ha, e quali stili abbia dipende dal Markdown: un testo senza
    blocchi di codice non ha lo stile Code. Misurato il 2026-10-19."""
    import re
    with zipfile.ZipFile(docx) as z:
        xml = z.read("word/styles.xml").decode("utf-8", "replace")
    return {n.lower() for n in re.findall(r'<w:name w:val="([^"]+)"', xml)}


def spazio_dopo_tabelle(docx: Path, punti: int | float) -> int:
    """Aggiunge spazio prima della prosa che segue una tabella nel DOCX generato.

    WordCraft produce tabelle e paragrafi adiacenti; la spaziatura del corpo non
    crea da sola un distacco dal bordo inferiore. I titoli conservano la propria
    spaziatura di stile. Il pacchetto DOCX rimane un file WordCraft: si modifica
    solo `word/document.xml`, senza dipendere da python-docx.
    """
    if isinstance(punti, bool) or not isinstance(punti, (int, float)) or not 0 <= punti <= 72:
        raise Errore("spazio_dopo_tabelle_pt deve essere un numero fra 0 e 72")
    if punti == 0:
        return 0
    before = str(round(punti * 20))
    with zipfile.ZipFile(docx) as source:
        original = source.read("word/document.xml")
        # Mantiene i prefissi WordCraft, compresi quelli non usati dall'elemento
        # modificato. ET senza registrazione rinominerebbe w: in ns0:.
        from io import BytesIO
        for _, (prefix, uri) in ET.iterparse(BytesIO(original), events=("start-ns",)):
            if prefix not in {"xml", "xmlns"}:
                ET.register_namespace(prefix or "", uri)
        root = ET.fromstring(original)
        body = root.find(W + "body")
        if body is None:
            raise Errore("DOCX senza word/body")
        children = list(body)
        changed = 0
        for index, node in enumerate(children[:-1]):
            following = children[index + 1]
            if node.tag != W + "tbl" or following.tag != W + "p":
                continue
            props = following.find(W + "pPr")
            style = props.find(W + "pStyle") if props is not None else None
            if style is not None and style.get(W + "val", "").lower().startswith(("heading", "title")):
                continue
            if props is None:
                props = ET.Element(W + "pPr")
                following.insert(0, props)
            spacing = props.find(W + "spacing")
            if spacing is None:
                spacing = ET.Element(W + "spacing")
                props.append(spacing)
            previous = spacing.get(W + "before")
            if previous is None or int(previous) < int(before):
                spacing.set(W + "before", before)
                changed += 1
        if not changed:
            return 0
        updated = ET.tostring(root, encoding="utf-8", xml_declaration=True)
        temp = docx.with_name(docx.name + ".spazio.tmp")
        try:
            with zipfile.ZipFile(temp, "w") as target:
                for item in source.infolist():
                    target.writestr(item, updated if item.filename == "word/document.xml" else source.read(item))
        except Exception:
            temp.unlink(missing_ok=True)
            raise
    temp.replace(docx)
    return changed


def comandi_stile_documento(stile: dict, presenti: set[str] | None = None) -> list[str]:
    """I comandi WordCraft che applicano un file di stile. Funzione pura, provata da --autotest.
    Con `presenti` si tralasciano gli stili che il documento non definisce."""
    out: list[str] = []
    if not stile:
        return out
    if presenti is not None:
        filtrati = comandi_stile_documento(stile, None)
        tenuti: list[str] = []
        for i in range(0, len(filtrati), 2):
            nome, par = filtrati[i + 1].split("=", 1)
            dati = json.loads(par)
            if nome == "styles.modify" and dati["style"].lower() not in presenti:
                continue
            tenuti += filtrati[i:i + 2]
        return tenuti
    if stile.get("font_titoli") or stile.get("font_testo"):
        tf = {"heading": stile.get("font_titoli") or stile.get("font_testo")}
        if stile.get("font_testo"):
            tf["body"] = stile["font_testo"]
        out += c("design.themeFonts", tf)
    dim = stile.get("dimensioni", {})
    for nome in STILI_TITOLO:
        chr_: dict = {}
        if stile.get("font_titoli"):
            chr_["font"] = stile["font_titoli"]
        if stile.get("colore_titoli"):
            chr_["color"] = colore(stile["colore_titoli"])
        if nome in dim:
            chr_["size"] = dim[nome]
        if chr_:
            out += c("styles.modify", {"style": nome, "chr": chr_})
    chr_ = {}
    if stile.get("font_testo"):
        chr_["font"] = stile["font_testo"]
    if stile.get("colore_testo"):
        chr_["color"] = colore(stile["colore_testo"])
    if "Normal" in dim:
        chr_["size"] = dim["Normal"]
    if chr_:
        out += c("styles.modify", {"style": "Normal", "chr": chr_})
    # I blocchi di codice del Markdown diventano lo stile di paragrafo Code. Il codice in linea
    # no: WordCraft 0.8.0 gli assegna Courier New come font diretto, che nessuno stile cambia.
    chr_ = {}
    if stile.get("font_codice"):
        chr_["font"] = stile["font_codice"]
    if "Code" in dim:
        chr_["size"] = dim["Code"]
    if chr_:
        out += c("styles.modify", {"style": "Code", "chr": chr_})
    return out


def comandi_stile_slide(stile: dict) -> list[str]:
    out: list[str] = []
    if stile.get("font_titoli") or stile.get("font_testo"):
        out += c("design.fonts", {"major": stile.get("font_titoli") or stile.get("font_testo"),
                                  "minor": stile.get("font_testo") or stile.get("font_titoli")})
    colori = stile.get("colori_slide")
    if colori:
        out += c("design.colors", {"colors": {k: "#" + colore(v) for k, v in colori.items()}})
    return out


def documento(sorgente: Path, uscita: Path, stile: dict, riferimento: Path | None) -> Path:
    if uscita.suffix.lower() not in FORMATI_DOC:
        raise Errore("formato non previsto per un documento: " + uscita.suffix)
    w = cli("wordcraft")
    with tempfile.TemporaryDirectory() as d:
        intermedio = Path(d) / "intermedio.docx"
        esegui(w, "convert", str(sorgente), str(intermedio))
        cmd: list[str] = []
        if riferimento:
            cmd += c("styles.copyFrom", {"path": str(riferimento.resolve()), "styles": STILI_TITOLO + ["Normal"]})
        cmd += comandi_stile_documento(stile, stili_presenti(intermedio))
        stilato = Path(d) / "stilato.docx"
        if cmd:
            esegui(w, "run", "--file", str(intermedio), *cmd, "--save", str(stilato))
        else:
            stilato = intermedio
        if "spazio_dopo_tabelle_pt" in stile:
            spazio_dopo_tabelle(stilato, stile["spazio_dopo_tabelle_pt"])
        uscita.parent.mkdir(parents=True, exist_ok=True)
        if uscita.suffix.lower() == ".docx":
            uscita.write_bytes(stilato.read_bytes())
        else:
            esegui(w, "convert", str(stilato), str(uscita))
    return uscita


def riferimento(stile: dict, uscita: Path) -> Path:
    """Un docx di riferimento con il design applicato, da tenere nel progetto o da passare a chi usa Word."""
    with tempfile.TemporaryDirectory() as d:
        md = Path(d) / "modello.md"
        md.write_text("# Titolo\n\nTesto di esempio.\n\n## Sottotitolo\n\nAltro testo.\n", encoding="utf-8")
        return documento(md, uscita, stile, None)


def slide(sorgente: Path, uscita: Path, stile: dict) -> Path:
    if uscita.suffix.lower() not in FORMATI_SLIDE:
        raise Errore("formato non previsto per una presentazione: " + uscita.suffix)
    dk = cli("deckcraft")
    testo = sorgente.read_text(encoding="utf-8")
    cmd = c("slide.fromOutline", {"text": testo, "markdown": True}) + c("slide.delete", {"index": 0})
    cmd += comandi_stile_slide(stile)
    with tempfile.TemporaryDirectory() as d:
        pptx = Path(d) / "slide.pptx"
        esegui(dk, "run", *cmd, "--save", str(pptx))
        uscita.parent.mkdir(parents=True, exist_ok=True)
        if uscita.suffix.lower() == ".pptx":
            uscita.write_bytes(pptx.read_bytes())
        else:
            esegui(dk, "convert", str(pptx), str(uscita))
    return uscita


def autotest() -> int:
    casi = rossi = 0

    def caso(nome: str, ok: bool) -> None:
        nonlocal casi, rossi
        casi += 1
        rossi += 0 if ok else 1
        print(("ok   " if ok else "ROSSO ") + nome)

    stile = {"font_titoli": "Georgia", "font_testo": "Verdana", "colore_titoli": "#c8102e",
             "dimensioni": {"Heading 1": 24, "Normal": 11}, "colori_slide": {"accent1": "c8102e"}}
    cmd = comandi_stile_documento(stile)
    pares = [(cmd[i + 1].split("=", 1)[0], json.loads(cmd[i + 1].split("=", 1)[1])) for i in range(0, len(cmd), 2)]
    caso("ogni comando è una coppia --cmd nome=json", all(cmd[i] == "--cmd" for i in range(0, len(cmd), 2)))
    normale = [p for n, p in pares if n == "styles.modify" and p["style"] == "Normal"]
    caso("il font del testo usa la chiave `font`, l'unica che WordCraft applica", normale and normale[0]["chr"].get("font") == "Verdana")
    h1 = [p for n, p in pares if n == "styles.modify" and p["style"] == "Heading 1"][0]["chr"]
    caso("il colore perde il cancelletto e diventa maiuscolo", h1.get("color") == "C8102E")
    caso("la dimensione arriva solo allo stile che la dichiara", h1.get("size") == 24 and "size" not in
         [p for n, p in pares if n == "styles.modify" and p["style"] == "Heading 2"][0]["chr"])
    caso("senza file di stile non si manda nessun comando", comandi_stile_documento({}) == [])
    st = dict(stile, font_codice="Consolas")
    senza_code = " ".join(comandi_stile_documento(st, {"normal", "heading 1", "heading 2"}))
    caso("uno stile assente dal documento non si modifica, perché WordCraft rifiuterebbe il comando",
         '"Code"' not in senza_code and '"Heading 3"' not in senza_code and '"Heading 1"' in senza_code)
    caso("i comandi di tema restano anche filtrando gli stili", "design.themeFonts" in senza_code)
    sl = comandi_stile_slide(stile)
    caso("le slide ricevono font e colori del tema", any("design.fonts" in x for x in sl) and '"accent1": "#C8102E"' in " ".join(sl))
    caso("le virgolette restano nel JSON, che è la ragione per non passare da PowerShell", all('"' in x for x in cmd[1::2]))
    print(f"\n{casi - rossi} casi superati su {casi}")
    return 1 if rossi else 0


def collaudo() -> int:
    """Prova vera sulle app installate: produce e poi verifica sui byte, non sull'uscita dei comandi."""
    ok = True
    stile = {"font_titoli": "Georgia", "font_testo": "Verdana", "colore_titoli": "C8102E",
             "dimensioni": {"Heading 1": 24}, "spazio_dopo_tabelle_pt": 12}
    with tempfile.TemporaryDirectory() as d:
        md = Path(d) / "prova.md"
        md.write_text("# Prova\n\nTesto con *corsivo*.\n\n| Campo | Valore |\n|---|---|\n| A | B |\n\nProsa dopo tabella.\n\n# Seconda\n\n- tre\n", encoding="utf-8")
        try:
            docx = documento(md, Path(d) / "prova.docx", stile, None)
            with zipfile.ZipFile(docx) as z:
                stili = z.read("word/styles.xml").decode("utf-8", "replace")
            for atteso in ("Verdana", "Georgia", "C8102E"):
                presente = atteso in stili
                ok &= presente
                print(("ok   " if presente else "ROSSO ") + "documento: " + atteso + " in word/styles.xml")
            with zipfile.ZipFile(docx) as z:
                body = ET.fromstring(z.read("word/document.xml")).find(W + "body")
            children = list(body) if body is not None else []
            gaps = []
            for index, node in enumerate(children[:-1]):
                if node.tag == W + "tbl" and children[index + 1].tag == W + "p":
                    spacing = children[index + 1].find(W + "pPr/" + W + "spacing")
                    gaps.append(int(spacing.get(W + "before", "0")) if spacing is not None else 0)
            spazio = bool(gaps) and min(gaps) >= 240
            ok &= spazio
            print(("ok   " if spazio else "ROSSO ") + "documento: prosa dopo tabella distanziata di 12 pt")
            pdf = documento(md, Path(d) / "prova.pdf", stile, None)
            buono = pdf.read_bytes()[:5] == b"%PDF-"
            ok &= buono
            print(("ok   " if buono else "ROSSO ") + "documento: il pdf è un pdf")
        except Errore as e:
            print("saltato documento: " + str(e))
        try:
            pptx = slide(md, Path(d) / "prova.pptx", stile)
            # Gli zip si chiudono subito: su Windows un file aperto impedisce di cancellare la cartella temporanea.
            with zipfile.ZipFile(pptx) as z:
                nomi = [n for n in z.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml")]
                tema = " ".join(z.read(n).decode("utf-8", "replace") for n in z.namelist() if n.startswith("ppt/theme/"))
            giusto = len(nomi) == 2
            ok &= giusto
            print(("ok   " if giusto else "ROSSO ") + f"slide: {len(nomi)} diapositive per due titoli, senza la vuota iniziale")
            for atteso in ("Georgia", "Verdana"):
                presente = atteso in tema
                ok &= presente
                print(("ok   " if presente else "ROSSO ") + "slide: " + atteso + " nel tema")
        except Errore as e:
            print("saltato slide: " + str(e))
    print("collaudo " + ("verde" if ok else "ROSSO"))
    return 0 if ok else 1


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Dal Markdown a documenti e presentazioni con le app Craft, in locale.")
    p.add_argument("--autotest", action="store_true")
    p.add_argument("--collaudo", action="store_true")
    sub = p.add_subparsers(dest="comando")
    pd = sub.add_parser("documento", help="Markdown -> docx, pdf, odt, rtf, html, tex con WordCraft")
    pd.add_argument("sorgente")
    pd.add_argument("--out", required=True)
    pd.add_argument("--stile")
    pd.add_argument("--riferimento", help="docx di cui copiare gli stili")
    ps = sub.add_parser("slide", help="Markdown -> pptx o pdf con DeckCraft: un titolo per diapositiva")
    ps.add_argument("sorgente")
    ps.add_argument("--out", required=True)
    ps.add_argument("--stile")
    pr = sub.add_parser("riferimento", help="crea un docx di riferimento dal file di stile")
    pr.add_argument("--stile", required=True)
    pr.add_argument("--out", required=True)
    a = p.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    if a.autotest:
        return autotest()
    if a.collaudo:
        return collaudo()
    if not a.comando:
        p.print_help()
        return 2
    try:
        if a.comando == "documento":
            out = documento(Path(a.sorgente), Path(a.out), leggi_stile(a.stile), Path(a.riferimento) if a.riferimento else None)
        elif a.comando == "slide":
            out = slide(Path(a.sorgente), Path(a.out), leggi_stile(a.stile))
        else:
            out = riferimento(leggi_stile(a.stile), Path(a.out))
    except Errore as e:
        print("craft-documento: " + str(e), file=sys.stderr)
        return 1
    print("scritto " + str(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
